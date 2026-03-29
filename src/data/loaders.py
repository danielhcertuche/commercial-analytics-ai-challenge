from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


RAW_FILENAMES = {
    "customers": "customers_dataset.csv",
    "geolocation": "geolocation_dataset.csv",
    "order_items": "order_items_dataset.csv",
    "order_payments": "order_payments_dataset.csv",
    "order_reviews": "order_reviews_dataset.csv",
    "orders": "orders_dataset.csv",
    "product_category_translation": "product_category_name_translation.csv",
    "products": "products_dataset.csv",
    "sellers": "sellers_dataset.csv",
}

DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
}


@dataclass
class DatasetBundle:
    customers: pd.DataFrame
    geolocation: pd.DataFrame
    order_items: pd.DataFrame
    order_payments: pd.DataFrame
    order_reviews: pd.DataFrame
    orders: pd.DataFrame
    product_category_translation: pd.DataFrame
    products: pd.DataFrame
    sellers: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        return {
            "customers": self.customers,
            "geolocation": self.geolocation,
            "order_items": self.order_items,
            "order_payments": self.order_payments,
            "order_reviews": self.order_reviews,
            "orders": self.orders,
            "product_category_translation": self.product_category_translation,
            "products": self.products,
            "sellers": self.sellers,
        }


def find_project_root(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / "src").exists() and (candidate / "data").exists():
            return candidate
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = find_project_root()
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def _read_csv(path: Path, parse_dates: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")

    return pd.read_csv(
        path,
        parse_dates=parse_dates or [],
        low_memory=False,
    )


def load_dataset(name: str, raw_dir: str | Path | None = None) -> pd.DataFrame:
    if name not in RAW_FILENAMES:
        raise ValueError(f"Dataset no soportado: {name}. Opciones: {list(RAW_FILENAMES)}")

    raw_path = Path(raw_dir) if raw_dir else RAW_DATA_DIR
    file_path = raw_path / RAW_FILENAMES[name]
    parse_dates = DATE_COLUMNS.get(name, [])
    return _read_csv(file_path, parse_dates=parse_dates)


def load_all_datasets(raw_dir: str | Path | None = None) -> DatasetBundle:
    raw_path = Path(raw_dir) if raw_dir else RAW_DATA_DIR

    return DatasetBundle(
        customers=load_dataset("customers", raw_path),
        geolocation=load_dataset("geolocation", raw_path),
        order_items=load_dataset("order_items", raw_path),
        order_payments=load_dataset("order_payments", raw_path),
        order_reviews=load_dataset("order_reviews", raw_path),
        orders=load_dataset("orders", raw_path),
        product_category_translation=load_dataset("product_category_translation", raw_path),
        products=load_dataset("products", raw_path),
        sellers=load_dataset("sellers", raw_path),
    )


def table_profile(df: pd.DataFrame, name: str) -> dict[str, Any]:
    return {
        "table": name,
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "duplicates": int(df.duplicated().sum()),
        "null_cells": int(df.isna().sum().sum()),
        "null_pct": round(float(df.isna().mean().mean() * 100), 2),
    }


def build_inventory_report(bundle: DatasetBundle) -> pd.DataFrame:
    rows = [table_profile(df, name) for name, df in bundle.as_dict().items()]
    return pd.DataFrame(rows).sort_values(["rows", "cols"], ascending=False).reset_index(drop=True)


def build_key_quality_report(bundle: DatasetBundle) -> pd.DataFrame:
    checks = []

    def add_check(table: str, column: str, df: pd.DataFrame) -> None:
        checks.append(
            {
                "table": table,
                "column": column,
                "rows": len(df),
                "nulls": int(df[column].isna().sum()) if column in df.columns else None,
                "distinct": int(df[column].nunique(dropna=True)) if column in df.columns else None,
                "is_unique": bool(df[column].is_unique) if column in df.columns else None,
            }
        )

    add_check("customers", "customer_id", bundle.customers)
    add_check("customers", "customer_unique_id", bundle.customers)
    add_check("orders", "order_id", bundle.orders)
    add_check("orders", "customer_id", bundle.orders)
    add_check("order_items", "order_id", bundle.order_items)
    add_check("order_items", "product_id", bundle.order_items)
    add_check("order_items", "seller_id", bundle.order_items)
    add_check("order_reviews", "review_id", bundle.order_reviews)
    add_check("order_reviews", "order_id", bundle.order_reviews)
    add_check("products", "product_id", bundle.products)
    add_check("sellers", "seller_id", bundle.sellers)

    return pd.DataFrame(checks)


def _aggregate_reviews(order_reviews: pd.DataFrame) -> pd.DataFrame:
    review_cols = [c for c in order_reviews.columns if c in {
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    }]
    reviews = order_reviews[review_cols].copy()

    reviews["review_comment_title"] = reviews.get("review_comment_title", pd.Series(dtype="object")).fillna("")
    reviews["review_comment_message"] = reviews.get("review_comment_message", pd.Series(dtype="object")).fillna("")

    reviews_agg = (
        reviews.sort_values(
            ["order_id", "review_creation_date"],
            ascending=[True, False],
            na_position="last",
        )
        .groupby("order_id", as_index=False)
        .agg(
            review_score=("review_score", "mean"),
            review_comment_title=("review_comment_title", "first"),
            review_comment_message=("review_comment_message", "first"),
        )
    )

    return reviews_agg


def _aggregate_payments(order_payments: pd.DataFrame) -> pd.DataFrame:
    payments_agg = (
        order_payments.groupby("order_id", as_index=False)
        .agg(
            payment_value_total=("payment_value", "sum"),
            payment_installments_max=("payment_installments", "max"),
            payment_type_nunique=("payment_type", "nunique"),
        )
    )
    return payments_agg


def build_item_level_base(
    bundle: DatasetBundle,
    delivered_only: bool = True,
) -> pd.DataFrame:
    orders = bundle.orders.copy()
    items = bundle.order_items.copy()
    products = bundle.products.copy()
    translation = bundle.product_category_translation.copy()
    customers = bundle.customers.copy()

    reviews_agg = _aggregate_reviews(bundle.order_reviews)
    payments_agg = _aggregate_payments(bundle.order_payments)

    if delivered_only:
        orders = orders.loc[orders["order_status"] == "delivered"].copy()

    df = (
        items.merge(orders, on="order_id", how="inner", validate="many_to_one")
        .merge(products, on="product_id", how="left", validate="many_to_one")
        .merge(
            translation,
            on="product_category_name",
            how="left",
            validate="many_to_one",
        )
        .merge(customers, on="customer_id", how="left", validate="many_to_one")
        .merge(reviews_agg, on="order_id", how="left", validate="many_to_one")
        .merge(payments_agg, on="order_id", how="left", validate="many_to_one")
    )

    if "product_category_name_english" in df.columns:
        df["product_category"] = df["product_category_name_english"].fillna(df["product_category_name"])
    else:
        df["product_category"] = df["product_category_name"]

    df["product_category"] = df["product_category"].fillna("unknown")
    df["quantity"] = 1
    df["item_revenue"] = df["price"].fillna(0.0)
    df["gross_revenue"] = df["price"].fillna(0.0) + df["freight_value"].fillna(0.0)

    df["delivery_delay_days"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.days

    df["is_late_delivery"] = df["delivery_delay_days"].fillna(0).gt(0)
    df["is_bad_review"] = df["review_score"].fillna(5).le(2)
    df["is_neutral_or_worse_review"] = df["review_score"].fillna(5).le(3)

    df["review_comment_title"] = df["review_comment_title"].fillna("")
    df["review_comment_message"] = df["review_comment_message"].fillna("")

    return df


def top_n_products(
    item_base: pd.DataFrame,
    metric: str = "volume",
    top_n: int = 5,
) -> pd.DataFrame:
    metric_map = {
        "volume": ("quantity", "sum"),
        "revenue": ("item_revenue", "sum"),
        "gross_revenue": ("gross_revenue", "sum"),
    }
    if metric not in metric_map:
        raise ValueError(f"Métrica no soportada: {metric}")

    target_col, agg_fn = metric_map[metric]

    result = (
        item_base.groupby("product_id", as_index=False)
        .agg(
            total_volume=("quantity", "sum"),
            total_revenue=("item_revenue", "sum"),
            total_gross_revenue=("gross_revenue", "sum"),
            n_orders=("order_id", "nunique"),
            category=("product_category", lambda s: s.mode().iloc[0] if not s.mode().empty else "unknown"),
        )
        .sort_values(
            "total_volume" if metric == "volume" else (
                "total_revenue" if metric == "revenue" else "total_gross_revenue"
            ),
            ascending=False,
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    return result


def top_n_categories(
    item_base: pd.DataFrame,
    metric: str = "volume",
    top_n: int = 5,
) -> pd.DataFrame:
    if metric == "volume":
        sort_col = "total_volume"
    elif metric == "revenue":
        sort_col = "total_revenue"
    elif metric == "gross_revenue":
        sort_col = "total_gross_revenue"
    else:
        raise ValueError(f"Métrica no soportada: {metric}")

    result = (
        item_base.groupby("product_category", as_index=False)
        .agg(
            total_volume=("quantity", "sum"),
            total_revenue=("item_revenue", "sum"),
            total_gross_revenue=("gross_revenue", "sum"),
            n_orders=("order_id", "nunique"),
            n_products=("product_id", "nunique"),
        )
        .sort_values(sort_col, ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    return result


def pain_point_summary(item_base: pd.DataFrame) -> pd.DataFrame:
    summary = pd.DataFrame(
        {
            "metric": [
                "avg_review_score",
                "bad_review_rate",
                "neutral_or_worse_review_rate",
                "late_delivery_rate",
                "avg_delivery_delay_days",
            ],
            "value": [
                item_base["review_score"].mean(),
                item_base["is_bad_review"].mean(),
                item_base["is_neutral_or_worse_review"].mean(),
                item_base["is_late_delivery"].mean(),
                item_base["delivery_delay_days"].mean(),
            ],
        }
    )
    return summary


def worst_categories_by_experience(
    item_base: pd.DataFrame,
    min_orders: int = 30,
    top_n: int = 10,
) -> pd.DataFrame:
    result = (
        item_base.groupby("product_category", as_index=False)
        .agg(
            n_orders=("order_id", "nunique"),
            n_items=("quantity", "sum"),
            avg_review_score=("review_score", "mean"),
            bad_review_rate=("is_bad_review", "mean"),
            late_delivery_rate=("is_late_delivery", "mean"),
            avg_delay_days=("delivery_delay_days", "mean"),
            total_revenue=("item_revenue", "sum"),
        )
        .query("n_orders >= @min_orders")
        .sort_values(
            ["bad_review_rate", "late_delivery_rate", "avg_review_score"],
            ascending=[False, False, True],
        )
        .head(top_n)
        .reset_index(drop=True)
    )
    return result