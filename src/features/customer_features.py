from __future__ import annotations

import pandas as pd


def build_order_level_base(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    delivered_orders = orders.loc[orders["order_status"] == "delivered"].copy()

    order_value = (
        order_items.groupby("order_id", as_index=False)
        .agg(
            order_revenue=("price", "sum"),
            freight_total=("freight_value", "sum"),
            n_items=("order_item_id", "count"),
            n_distinct_products=("product_id", "nunique"),
        )
    )

    order_base = (
        delivered_orders
        .merge(order_value, on="order_id", how="inner", validate="one_to_one")
        .merge(customers, on="customer_id", how="left", validate="many_to_one")
    )

    return order_base


def build_customer_rfm(
    order_base: pd.DataFrame,
    snapshot_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    df = order_base.copy()

    if snapshot_date is None:
        snapshot_date = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    customer_rfm = (
        df.groupby("customer_unique_id", as_index=False)
        .agg(
            last_purchase_date=("order_purchase_timestamp", "max"),
            frequency=("order_id", "nunique"),
            monetary=("order_revenue", "sum"),
            avg_order_value=("order_revenue", "mean"),
            total_items=("n_items", "sum"),
            n_cities=("customer_city", "nunique"),
            main_state=("customer_state", lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]),
            main_city=("customer_city", lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]),
        )
    )

    customer_rfm["recency_days"] = (snapshot_date - customer_rfm["last_purchase_date"]).dt.days

    return customer_rfm


def add_rfm_scores(customer_rfm: pd.DataFrame) -> pd.DataFrame:
    df = customer_rfm.copy()

    # menor recency es mejor
    df["R_score"] = pd.qcut(df["recency_days"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
    df["F_score"] = pd.qcut(df["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
    df["M_score"] = pd.qcut(df["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)

    df["RFM_score"] = (
        df["R_score"].astype(str)
        + df["F_score"].astype(str)
        + df["M_score"].astype(str)
    )

    df["rfm_numeric_score"] = df["R_score"] + df["F_score"] + df["M_score"]

    return df


def assign_customer_segment(customer_rfm: pd.DataFrame) -> pd.DataFrame:
    df = customer_rfm.copy()

    def classify(row: pd.Series) -> str:
        r, f, m = row["R_score"], row["F_score"], row["M_score"]

        if r >= 4 and f >= 4 and m >= 4:
            return "Loyal high-value"
        if r >= 4 and f >= 3 and m >= 3:
            return "Loyal"
        if r >= 4 and f <= 2:
            return "Recent occasional"
        if r <= 2 and f >= 3 and m >= 3:
            return "At risk high-value"
        if r <= 2 and f <= 2:
            return "At risk / churn"
        if f >= 3 and m >= 3:
            return "Frequent valuable"
        return "Occasional"

    df["customer_segment"] = df.apply(classify, axis=1)
    return df