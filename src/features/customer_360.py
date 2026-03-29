from __future__ import annotations

from typing import Iterable
import numpy as np
import pandas as pd


def _safe_mode(series: pd.Series, default: str = "unknown") -> str:
    s = series.dropna()
    if s.empty:
        return default
    mode = s.mode()
    return str(mode.iloc[0]) if not mode.empty else str(s.iloc[0])


def _minmax(series: pd.Series) -> pd.Series:
    s = series.astype(float).copy()
    min_v = s.min()
    max_v = s.max()
    if pd.isna(min_v) or pd.isna(max_v) or max_v == min_v:
        return pd.Series(0.0, index=s.index)
    return (s - min_v) / (max_v - min_v)


def build_item_level_customer_base(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    order_reviews: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    translation: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construye una base a nivel ítem entregado con:
    - customer_unique_id
    - categoría
    - revenue por ítem
    - score de review
    - señal de retraso
    """
    delivered_orders = orders.loc[orders["order_status"] == "delivered"].copy()

    reviews_agg = (
        order_reviews
        .sort_values(["order_id", "review_creation_date"], ascending=[True, False], na_position="last")
        .groupby("order_id", as_index=False)
        .agg(
            review_score=("review_score", "mean"),
            review_comment_title=("review_comment_title", "first"),
            review_comment_message=("review_comment_message", "first"),
        )
    )

    item_base = (
        order_items
        .merge(
            delivered_orders[[
                "order_id",
                "customer_id",
                "order_status",
                "order_purchase_timestamp",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ]],
            on="order_id",
            how="inner",
            validate="many_to_one",
        )
        .merge(
            customers[[
                "customer_id",
                "customer_unique_id",
                "customer_city",
                "customer_state",
            ]],
            on="customer_id",
            how="left",
            validate="many_to_one",
        )
        .merge(
            products[["product_id", "product_category_name"]],
            on="product_id",
            how="left",
            validate="many_to_one",
        )
        .merge(
            translation,
            on="product_category_name",
            how="left",
            validate="many_to_one",
        )
        .merge(
            reviews_agg,
            on="order_id",
            how="left",
            validate="many_to_one",
        )
    )

    item_base["product_category"] = (
        item_base["product_category_name_english"]
        .fillna(item_base["product_category_name"])
        .fillna("unknown")
    )

    item_base["item_revenue"] = item_base["price"].fillna(0.0)
    item_base["gross_revenue"] = (
        item_base["price"].fillna(0.0) + item_base["freight_value"].fillna(0.0)
    )

    item_base["delivery_delay_days"] = (
        item_base["order_delivered_customer_date"] - item_base["order_estimated_delivery_date"]
    ).dt.days

    item_base["is_late_delivery"] = item_base["delivery_delay_days"].fillna(0).gt(0)
    item_base["is_bad_review"] = item_base["review_score"].fillna(5).le(2)
    item_base["is_neutral_or_worse_review"] = item_base["review_score"].fillna(5).le(3)

    return item_base


def build_customer_behavior_features(item_base: pd.DataFrame) -> pd.DataFrame:
    """
    Features de comportamiento y afinidad:
    - categoría favorita
    - diversidad de categorías
    - span de compra
    - frecuencia mensual
    - concentración de gasto en categoría favorita
    """
    df = item_base.copy()

    customer_base = (
        df.groupby("customer_unique_id", as_index=False)
        .agg(
            first_purchase_date=("order_purchase_timestamp", "min"),
            last_purchase_date=("order_purchase_timestamp", "max"),
            total_orders=("order_id", "nunique"),
            total_items=("order_item_id", "count"),
            total_revenue=("item_revenue", "sum"),
            avg_order_value=("item_revenue", "mean"),
            category_diversity=("product_category", "nunique"),
            main_state=("customer_state", lambda s: _safe_mode(s, "unknown")),
            main_city=("customer_city", lambda s: _safe_mode(s, "unknown")),
            favorite_category=("product_category", lambda s: _safe_mode(s, "unknown")),
        )
    )

    customer_base["purchase_span_days"] = (
        customer_base["last_purchase_date"] - customer_base["first_purchase_date"]
    ).dt.days.clip(lower=0)

    customer_base["months_active"] = np.maximum(
        1.0,
        customer_base["purchase_span_days"] / 30.4
    )

    customer_base["purchase_frequency_per_month"] = (
        customer_base["total_orders"] / customer_base["months_active"]
    )

    category_spend = (
        df.groupby(["customer_unique_id", "product_category"], as_index=False)
        .agg(category_revenue=("item_revenue", "sum"))
    )

    top_category_spend = (
        category_spend
        .sort_values(["customer_unique_id", "category_revenue"], ascending=[True, False])
        .groupby("customer_unique_id", as_index=False)
        .first()
        .rename(columns={"category_revenue": "favorite_category_revenue"})
    )

    customer_base = customer_base.merge(
        top_category_spend[["customer_unique_id", "favorite_category_revenue"]],
        on="customer_unique_id",
        how="left",
    )

    customer_base["favorite_category_revenue"] = customer_base["favorite_category_revenue"].fillna(0.0)
    customer_base["top_category_share"] = np.where(
        customer_base["total_revenue"] > 0,
        customer_base["favorite_category_revenue"] / customer_base["total_revenue"],
        0.0
    )

    return customer_base


def build_customer_experience_features(item_base: pd.DataFrame) -> pd.DataFrame:
    """
    Features de fricción / experiencia:
    - bad_review_rate_customer
    - late_delivery_rate_customer
    - neutral_or_worse_review_rate_customer
    - avg_review_score_customer
    """
    df = item_base.copy()

    exp = (
        df.groupby("customer_unique_id", as_index=False)
        .agg(
            avg_review_score_customer=("review_score", "mean"),
            bad_review_rate_customer=("is_bad_review", "mean"),
            neutral_or_worse_review_rate_customer=("is_neutral_or_worse_review", "mean"),
            late_delivery_rate_customer=("is_late_delivery", "mean"),
            avg_delay_days_customer=("delivery_delay_days", "mean"),
        )
    )

    exp["avg_review_score_customer"] = exp["avg_review_score_customer"].fillna(5.0)
    exp["bad_review_rate_customer"] = exp["bad_review_rate_customer"].fillna(0.0)
    exp["neutral_or_worse_review_rate_customer"] = exp["neutral_or_worse_review_rate_customer"].fillna(0.0)
    exp["late_delivery_rate_customer"] = exp["late_delivery_rate_customer"].fillna(0.0)
    exp["avg_delay_days_customer"] = exp["avg_delay_days_customer"].fillna(0.0)

    return exp


def build_customer_history_summary(item_base: pd.DataFrame, top_n_categories: int = 3) -> pd.DataFrame:
    """
    Resumen textual corto del comportamiento del cliente.
    Sirve para punto 4 y punto 7.
    """
    category_pref = (
        item_base.groupby(["customer_unique_id", "product_category"], as_index=False)
        .agg(
            total_orders=("order_id", "nunique"),
            total_spend=("item_revenue", "sum"),
        )
        .sort_values(["customer_unique_id", "total_spend", "total_orders"], ascending=[True, False, False])
    )

    rows = []
    for customer_id, grp in category_pref.groupby("customer_unique_id"):
        top_categories = grp.head(top_n_categories)["product_category"].tolist()
        categories_text = ", ".join(top_categories) if top_categories else "unknown"
        rows.append(
            {
                "customer_unique_id": customer_id,
                "purchase_history_summary": f"Top categories: {categories_text}"
            }
        )

    return pd.DataFrame(rows)


def build_customer_360_features(
    customer_rfm: pd.DataFrame,
    item_base: pd.DataFrame,
) -> pd.DataFrame:
    """
    Une RFM + comportamiento + fricción y calcula scores enriquecidos.
    """
    behavior = build_customer_behavior_features(item_base)
    experience = build_customer_experience_features(item_base)
    history = build_customer_history_summary(item_base)

    customer_360 = (
        customer_rfm
        .merge(behavior, on="customer_unique_id", how="left", suffixes=("", "_behavior"))
        .merge(experience, on="customer_unique_id", how="left")
        .merge(history, on="customer_unique_id", how="left")
    )

    # columnas base útiles
    customer_360["days_since_first_purchase"] = (
        customer_360["last_purchase_date"] - customer_360["first_purchase_date"]
    ).dt.days.clip(lower=0)

    customer_360["customer_lifetime_days"] = customer_360["days_since_first_purchase"]

    # scores enriquecidos
    customer_360["value_score"] = (
        0.45 * _minmax(customer_360["monetary"]) +
        0.25 * _minmax(customer_360["frequency"]) +
        0.20 * _minmax(customer_360["avg_order_value"]) +
        0.10 * _minmax(customer_360["total_items"])
    )

    customer_360["engagement_score"] = (
        0.45 * _minmax(customer_360["R_score"]) +
        0.35 * _minmax(customer_360["purchase_frequency_per_month"]) +
        0.20 * _minmax(customer_360["category_diversity"])
    )

    customer_360["friction_score"] = (
        0.45 * customer_360["bad_review_rate_customer"].fillna(0.0) +
        0.30 * customer_360["late_delivery_rate_customer"].fillna(0.0) +
        0.25 * customer_360["neutral_or_worse_review_rate_customer"].fillna(0.0)
    )

    customer_360["inactivity_risk_score"] = (
        0.65 * _minmax(customer_360["recency_days"]) +
        0.35 * (1 - _minmax(customer_360["frequency"]))
    )

    customer_360["customer_health_score"] = (
        0.50 * customer_360["engagement_score"] +
        0.35 * customer_360["value_score"] -
        0.15 * customer_360["friction_score"]
    )

    customer_360["purchase_history_summary"] = customer_360["purchase_history_summary"].fillna("Top categories: unknown")

    return customer_360


def assign_enriched_customer_segment(customer_360: pd.DataFrame) -> pd.DataFrame:
    """
    Segmentación híbrida:
    - Loyal high-value
    - Loyal
    - Growth potential
    - Occasional
    - At risk
    - At risk high-value
    - Friction-sensitive
    """
    df = customer_360.copy()

    value_q75 = df["value_score"].quantile(0.75)
    value_q60 = df["value_score"].quantile(0.60)
    friction_q75 = df["friction_score"].quantile(0.75)
    recency_q75 = df["recency_days"].quantile(0.75)

    def classify(row: pd.Series) -> str:
        recency = row["recency_days"]
        frequency = row["frequency"]
        value_score = row["value_score"]
        friction_score = row["friction_score"]
        engagement = row["engagement_score"]

        if value_score >= value_q75 and recency <= 120 and frequency >= 2:
            return "Loyal high-value"

        if engagement >= 0.60 and recency <= 150 and frequency >= 2:
            return "Loyal"

        if recency <= 120 and frequency == 1 and value_score >= 0.40:
            return "Growth potential"

        if friction_score >= friction_q75 and recency <= 180:
            return "Friction-sensitive"

        if recency >= recency_q75 and value_score >= value_q60:
            return "At risk high-value"

        if recency >= recency_q75:
            return "At risk"

        return "Occasional"

    df["customer_segment_enriched"] = df.apply(classify, axis=1)
    return df