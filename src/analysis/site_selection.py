from __future__ import annotations

import pandas as pd


def build_city_sales_summary(order_base: pd.DataFrame) -> pd.DataFrame:
    city_summary = (
        order_base.groupby(["customer_state", "customer_city"], as_index=False)
        .agg(
            n_orders=("order_id", "nunique"),
            n_customers=("customer_unique_id", "nunique"),
            total_revenue=("order_revenue", "sum"),
            avg_order_value=("order_revenue", "mean"),
            total_items=("n_items", "sum"),
        )
    )
    return city_summary


def add_city_priority_score(city_summary: pd.DataFrame) -> pd.DataFrame:
    df = city_summary.copy()

    def minmax(s: pd.Series) -> pd.Series:
        rng = s.max() - s.min()
        if rng == 0:
            return pd.Series(0.0, index=s.index)
        return (s - s.min()) / rng

    df["revenue_norm"] = minmax(df["total_revenue"])
    df["orders_norm"] = minmax(df["n_orders"])
    df["customers_norm"] = minmax(df["n_customers"])
    df["aov_norm"] = minmax(df["avg_order_value"])

    df["city_priority_score"] = (
        0.45 * df["revenue_norm"]
        + 0.25 * df["orders_norm"]
        + 0.20 * df["customers_norm"]
        + 0.10 * df["aov_norm"]
    )

    return df.sort_values("city_priority_score", ascending=False).reset_index(drop=True)