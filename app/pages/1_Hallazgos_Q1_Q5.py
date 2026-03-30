from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Rectangle
import streamlit as st


# =========================================================
# 1. Project root and imports
# =========================================================
def find_project_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "src").exists() and (candidate / "data").exists():
            return candidate
    raise RuntimeError("No fue posible ubicar la raíz del proyecto.")


PROJECT_ROOT = find_project_root(Path(__file__).resolve())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.data.loaders import load_all_datasets
from src.analysis.site_selection import (
    build_city_sales_summary,
    add_city_priority_score,
)


# =========================================================
# 2. Page config
# =========================================================
st.set_page_config(
    page_title="Hallazgos clave Q1-Q5",
    page_icon="📈",
    layout="wide",
)

TP_COLORS = {
    "blue_primary": "#2448A8",
    "blue_secondary": "#4C78E6",
    "blue_soft": "#6EC1E4",
    "yellow_accent": "#F2D22E",
    "gray_bg": "#F7F8FA",
    "gray_card": "#FFFFFF",
    "gray_text": "#4B5563",
    "gray_muted": "#D1D5DB",
    "gray_dark": "#1F2937",
    "white": "#FFFFFF",
}


# =========================================================
# 3. Global styles
# =========================================================
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {TP_COLORS["gray_bg"]};
        }}

        .block-container {{
            padding-top: 1.8rem;
            padding-bottom: 2rem;
            max-width: 1280px;
        }}

        section[data-testid="stSidebar"] {{
            background-color: #F1F4FA;
            border-right: 1px solid {TP_COLORS["gray_muted"]};
        }}

        .hero-card {{
            background: linear-gradient(180deg, {TP_COLORS["white"]} 0%, #FBFCFE 100%);
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 18px;
            padding: 1.55rem 1.7rem;
            box-shadow: 0 8px 24px rgba(31, 41, 55, 0.06);
            margin-bottom: 1rem;
        }}

        .hero-badge {{
            display: inline-block;
            background: {TP_COLORS["yellow_accent"]};
            color: {TP_COLORS["gray_dark"]};
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.24rem 0.58rem;
            border-radius: 999px;
            margin-bottom: 0.75rem;
        }}

        .hero-title {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 2rem;
            font-weight: 760;
            line-height: 1.2;
            margin-bottom: 0.2rem;
        }}

        .hero-subtitle {{
            color: {TP_COLORS["gray_dark"]};
            font-size: 1.02rem;
            font-weight: 600;
            margin-bottom: 0.85rem;
        }}

        .hero-note {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.97rem;
            line-height: 1.7;
            margin-bottom: 0;
        }}

        .story-strip {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.85rem;
            margin-bottom: 1.1rem;
        }}

        .story-card {{
            background: {TP_COLORS["gray_card"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 14px;
            padding: 0.95rem 1rem;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
        }}

        .story-card .label {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.8rem;
            margin-bottom: 0.25rem;
        }}

        .story-card .value {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 1.08rem;
            font-weight: 720;
            line-height: 1.35;
        }}

        .summary-card {{
            background: {TP_COLORS["gray_card"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 16px;
            padding: 1rem 1.1rem;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
            margin-bottom: 1.1rem;
        }}

        .summary-title {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 1.05rem;
            font-weight: 720;
            margin-bottom: 0.45rem;
        }}

        .summary-list {{
            margin: 0;
            padding-left: 1.15rem;
            color: {TP_COLORS["gray_text"]};
            font-size: 0.94rem;
            line-height: 1.65;
        }}

        .summary-list li {{
            margin-bottom: 0.25rem;
        }}

        .section-card {{
            background: {TP_COLORS["gray_card"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 16px;
            padding: 1.1rem 1.15rem;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
            margin-bottom: 1rem;
        }}

        .section-title {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 1.2rem;
            font-weight: 750;
            margin-bottom: 0.35rem;
        }}

        .section-text {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.95rem;
            line-height: 1.65;
            margin-bottom: 0.2rem;
        }}

        .chart-caption {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.88rem;
            line-height: 1.55;
            margin-top: 0.25rem;
            margin-bottom: 0.8rem;
        }}

        .callout {{
            background: {TP_COLORS["white"]};
            border-left: 5px solid {TP_COLORS["blue_secondary"]};
            border-radius: 10px;
            padding: 0.8rem 0.95rem;
            color: {TP_COLORS["gray_text"]};
            font-size: 0.93rem;
            line-height: 1.6;
            margin-top: 0.65rem;
            margin-bottom: 0.3rem;
        }}

        .decision-box {{
            background: #FBFCFE;
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 12px;
            padding: 0.85rem 0.95rem;
            margin-top: 0.75rem;
            color: {TP_COLORS["gray_dark"]};
            font-size: 0.93rem;
            line-height: 1.6;
        }}

        .mini-card {{
            background: {TP_COLORS["white"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 12px;
            padding: 0.9rem 0.95rem;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.03);
            height: 100%;
        }}

        .mini-card h4 {{
            color: {TP_COLORS["gray_dark"]};
            font-size: 1rem;
            margin-bottom: 0.45rem;
            margin-top: 0;
        }}

        .mini-card p {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.92rem;
            line-height: 1.6;
            margin-bottom: 0;
        }}

        .glossary-note {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.9rem;
            line-height: 1.6;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 4. Helpers
# =========================================================
def fmt_int(x, pos=None):
    return f"{x:,.0f}"


def fmt_pct(x, pos=None):
    return f"{x:.0%}"


def fmt_currency(x, pos=None):
    return f"${x:,.0f}"


def prettify_label(value: str) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("_", " ").title()


def apply_plot_style():
    plt.rcParams.update({
        "figure.facecolor": TP_COLORS["white"],
        "axes.facecolor": TP_COLORS["white"],
        "axes.edgecolor": TP_COLORS["gray_dark"],
        "axes.labelcolor": TP_COLORS["gray_dark"],
        "xtick.color": TP_COLORS["gray_dark"],
        "ytick.color": TP_COLORS["gray_dark"],
        "text.color": TP_COLORS["gray_dark"],
        "font.size": 10,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


# =========================================================
# 5. Data builders
# =========================================================
@st.cache_data(show_spinner=False)
def build_q1_q2_assets():
    bundle = load_all_datasets()

    customers = bundle.customers.copy()
    order_items = bundle.order_items.copy()
    order_reviews = bundle.order_reviews.copy()
    orders = bundle.orders.copy()
    products = bundle.products.copy()
    translation = bundle.product_category_translation.copy()

    reviews_agg = (
        order_reviews
        .sort_values(["order_id", "review_creation_date"], ascending=[True, False], na_position="last")
        .groupby("order_id", as_index=False)
        .agg(
            review_score=("review_score", "mean"),
            review_comment_message=("review_comment_message", "first"),
        )
    )

    delivered_orders = orders.loc[orders["order_status"] == "delivered"].copy()

    item_base = (
        order_items
        .merge(delivered_orders, on="order_id", how="inner", validate="many_to_one")
        .merge(products, on="product_id", how="left", validate="many_to_one")
        .merge(translation, on="product_category_name", how="left", validate="many_to_one")
        .merge(customers, on="customer_id", how="left", validate="many_to_one")
        .merge(reviews_agg, on="order_id", how="left", validate="many_to_one")
    )

    item_base["product_category"] = (
        item_base["product_category_name_english"]
        .fillna(item_base["product_category_name"])
        .fillna("unknown")
    )

    item_base["quantity"] = 1
    item_base["item_revenue"] = item_base["price"].fillna(0)
    item_base["gross_revenue"] = item_base["price"].fillna(0) + item_base["freight_value"].fillna(0)

    item_base["delivery_delay_days"] = (
        item_base["order_delivered_customer_date"] - item_base["order_estimated_delivery_date"]
    ).dt.days

    item_base["is_late_delivery"] = item_base["delivery_delay_days"] > 0
    item_base["is_bad_review"] = item_base["review_score"].fillna(5) <= 2
    item_base["is_neutral_or_worse_review"] = item_base["review_score"].fillna(5) <= 3

    category_sales = (
        item_base.groupby("product_category", as_index=False)
        .agg(
            total_volume=("quantity", "sum"),
            total_revenue=("item_revenue", "sum"),
            total_gross_revenue=("gross_revenue", "sum"),
            n_orders=("order_id", "nunique"),
            n_products=("product_id", "nunique"),
            avg_price=("price", "mean"),
        )
    )

    top_categories_volume = (
        category_sales.sort_values(["total_volume", "total_revenue"], ascending=[False, False])
        .head(5)
        .reset_index(drop=True)
    )

    top_categories_revenue = (
        category_sales.sort_values(["total_revenue", "total_volume"], ascending=[False, False])
        .head(5)
        .reset_index(drop=True)
    )

    delay_review_summary = (
        item_base.groupby("is_late_delivery", as_index=False)
        .agg(
            n_items=("quantity", "sum"),
            avg_review_score=("review_score", "mean"),
            bad_review_rate=("is_bad_review", "mean"),
            neutral_or_worse_rate=("is_neutral_or_worse_review", "mean"),
        )
    )

    delay_view = delay_review_summary.copy()
    delay_view["scenario"] = delay_view["is_late_delivery"].map({
        False: "Entrega puntual",
        True: "Entrega tardía"
    })

    category_diagnostics = (
        item_base.groupby("product_category", as_index=False)
        .agg(
            n_items=("quantity", "sum"),
            n_orders=("order_id", "nunique"),
            total_revenue=("item_revenue", "sum"),
            avg_review_score=("review_score", "mean"),
            bad_review_rate=("is_bad_review", "mean"),
            late_delivery_rate=("is_late_delivery", "mean"),
        )
    )

    priority_categories = (
        category_diagnostics
        .query("n_orders >= 30")
        .assign(
            pain_index=lambda df: df["bad_review_rate"] * np.log1p(df["n_items"])
        )
        .sort_values(["pain_index", "total_revenue"], ascending=[False, False])
        .reset_index(drop=True)
    )

    return {
        "item_base": item_base,
        "category_sales": category_sales,
        "top_categories_volume": top_categories_volume,
        "top_categories_revenue": top_categories_revenue,
        "delay_view": delay_view,
        "priority_categories": priority_categories,
    }


@st.cache_data(show_spinner=False)
def build_q3_q5_assets():
    processed_dir = PROJECT_ROOT / "data" / "processed"

    customer_360_path = processed_dir / "customer_360_features.csv"
    segment_summary_path = processed_dir / "customer_primary_segment_summary.csv"
    flag_summary_path = processed_dir / "customer_flag_summary.csv"

    if not customer_360_path.exists():
        raise FileNotFoundError(
            "No se encontró customer_360_features.csv en data/processed. "
            "Ejecuta primero el notebook 04b_customer_segmentation_enriched."
        )

    customer_360 = pd.read_csv(customer_360_path)

    if segment_summary_path.exists():
        customer_primary_segment_summary = pd.read_csv(segment_summary_path)
    else:
        customer_primary_segment_summary = (
            customer_360.groupby(
                ["segment_code", "customer_segment_primary", "segment_alias"],
                as_index=False
            )
            .agg(
                n_customers=("customer_unique_id", "nunique"),
                avg_recency_days=("recency_days", "mean"),
                avg_frequency=("frequency", "mean"),
                avg_monetary=("monetary", "mean"),
                avg_order_value=("avg_order_value", "mean"),
            )
            .sort_values(["segment_code"])
            .reset_index(drop=True)
        )
        customer_primary_segment_summary["share_pct"] = (
            customer_primary_segment_summary["n_customers"] /
            customer_primary_segment_summary["n_customers"].sum()
        )

    if flag_summary_path.exists():
        customer_flag_summary = pd.read_csv(flag_summary_path)
    else:
        customer_flag_summary = pd.DataFrame({
            "flag_name": ["HIGH_VALUE", "FRICTION_RISK", "CHURN_SIGNAL"],
            "n_customers": [
                customer_360["customer_flags_text"].fillna("").str.contains("HIGH_VALUE", regex=False).sum(),
                customer_360["customer_flags_text"].fillna("").str.contains("FRICTION_RISK", regex=False).sum(),
                customer_360["customer_flags_text"].fillna("").str.contains("CHURN_SIGNAL", regex=False).sum(),
            ]
        })
        customer_flag_summary["share_pct"] = (
            customer_flag_summary["n_customers"] / len(customer_360)
        )

    bundle = load_all_datasets()
    customers = bundle.customers.copy()
    orders = bundle.orders.copy()
    order_items = bundle.order_items.copy()

    delivered_orders = orders.loc[orders["order_status"] == "delivered"].copy()

    order_value = (
        order_items.groupby("order_id", as_index=False)
        .agg(
            order_revenue=("price", "sum"),
            freight_total=("freight_value", "sum"),
            n_items=("order_item_id", "count"),
        )
    )

    order_base = (
        delivered_orders
        .merge(order_value, on="order_id", how="inner", validate="one_to_one")
        .merge(customers, on="customer_id", how="left", validate="many_to_one")
    )

    city_summary = build_city_sales_summary(order_base)
    city_priority = add_city_priority_score(city_summary)
    top_city = city_priority.iloc[0].copy()

    return {
        "customer_primary_segment_summary": customer_primary_segment_summary,
        "customer_flag_summary": customer_flag_summary,
        "city_priority": city_priority,
        "top_city": top_city,
    }


# =========================================================
# 6. Plot builders
# =========================================================
def plot_q1_volume(top_categories_volume: pd.DataFrame, category_sales: pd.DataFrame):
    apply_plot_style()

    plot_df = top_categories_volume.copy().sort_values("total_volume", ascending=True)
    plot_df["product_category_label"] = plot_df["product_category"].apply(prettify_label)

    total_volume_all = category_sales["total_volume"].sum()
    plot_df["share_pct"] = plot_df["total_volume"] / total_volume_all

    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=TP_COLORS["white"])
    ax.barh(
        plot_df["product_category_label"],
        plot_df["total_volume"],
        color=TP_COLORS["blue_secondary"],
        edgecolor="none",
        height=0.72,
    )

    ax.set_title(
        "Categorías líderes por volumen de ventas",
        fontsize=14,
        fontweight="bold",
        color=TP_COLORS["blue_primary"],
        pad=14,
    )
    ax.set_xlabel("Ítems vendidos", color=TP_COLORS["gray_dark"], fontsize=11)
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(FuncFormatter(fmt_int))
    ax.spines["left"].set_color(TP_COLORS["gray_dark"])
    ax.spines["bottom"].set_color(TP_COLORS["gray_dark"])
    ax.tick_params(axis="x", colors=TP_COLORS["gray_dark"], labelsize=10)
    ax.tick_params(axis="y", colors=TP_COLORS["gray_dark"], labelsize=10)
    ax.xaxis.grid(True, linestyle="-", linewidth=0.7, color=TP_COLORS["gray_muted"], alpha=0.75)
    ax.set_axisbelow(True)

    max_val = plot_df["total_volume"].max()

    for i, (_, row) in enumerate(plot_df.iterrows()):
        value = row["total_volume"]
        pct = row["share_pct"]
        ax.text(
            value * 0.89,
            i,
            f"{pct:.1%}",
            va="center",
            ha="center",
            color=TP_COLORS["white"],
            fontsize=9,
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.22",
                facecolor=TP_COLORS["blue_secondary"],
                edgecolor="none",
            )
        )
        ax.text(
            value + max_val * 0.006,
            i,
            f"{value:,.0f}",
            va="center",
            ha="left",
            color=TP_COLORS["gray_text"],
            fontsize=10,
        )

    ax.set_xlim(0, max_val * 1.14)
    plt.tight_layout()
    return fig


def plot_q1_revenue(top_categories_revenue: pd.DataFrame, category_sales: pd.DataFrame):
    apply_plot_style()

    plot_df = top_categories_revenue.copy().sort_values("total_revenue", ascending=True)
    plot_df["product_category_label"] = plot_df["product_category"].apply(prettify_label)

    total_revenue_all = category_sales["total_revenue"].sum()
    plot_df["share_pct"] = plot_df["total_revenue"] / total_revenue_all

    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=TP_COLORS["white"])
    ax.barh(
        plot_df["product_category_label"],
        plot_df["total_revenue"],
        color=TP_COLORS["blue_secondary"],
        edgecolor="none",
        height=0.72,
    )

    ax.set_title(
        "Categorías líderes por ingresos",
        fontsize=14,
        fontweight="bold",
        color=TP_COLORS["blue_primary"],
        pad=14,
    )
    ax.set_xlabel("Ingresos", color=TP_COLORS["gray_dark"], fontsize=11)
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(FuncFormatter(fmt_currency))
    ax.spines["left"].set_color(TP_COLORS["gray_dark"])
    ax.spines["bottom"].set_color(TP_COLORS["gray_dark"])
    ax.tick_params(axis="x", colors=TP_COLORS["gray_dark"], labelsize=10)
    ax.tick_params(axis="y", colors=TP_COLORS["gray_dark"], labelsize=10)
    ax.xaxis.grid(True, linestyle="-", linewidth=0.7, color=TP_COLORS["gray_muted"], alpha=0.75)
    ax.set_axisbelow(True)

    max_val = plot_df["total_revenue"].max()
    top_two_idx = plot_df.index[-2:]

    for i, (idx, row) in enumerate(plot_df.iterrows()):
        value = row["total_revenue"]
        pct = row["share_pct"]
        ax.text(
            value * 0.88,
            i,
            f"{pct:.1%}",
            va="center",
            ha="center",
            color=TP_COLORS["white"],
            fontsize=9,
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.22",
                facecolor=TP_COLORS["blue_secondary"],
                edgecolor="none",
            )
        )
        if idx in top_two_idx:
            ax.text(
                value + max_val * 0.008,
                i,
                f"${value:,.0f}",
                va="center",
                ha="left",
                color=TP_COLORS["gray_text"],
                fontsize=10,
            )

    ax.set_xlim(0, max_val * 1.16)
    plt.tight_layout()
    return fig


def plot_delay_impact(delay_view: pd.DataFrame):
    apply_plot_style()

    plot_df = delay_view.copy()
    colors = [TP_COLORS["blue_secondary"], TP_COLORS["yellow_accent"]]

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.7), facecolor=TP_COLORS["white"])

    fig.suptitle(
        "Impacto del cumplimiento de entrega en la experiencia del cliente",
        fontsize=15,
        fontweight="bold",
        color=TP_COLORS["blue_primary"],
        y=1.02,
    )

    ax = axes[0]
    ax.bar(plot_df["scenario"], plot_df["avg_review_score"], color=colors, width=0.58, edgecolor="none")
    ax.set_title("Calificación promedio", fontsize=12, color=TP_COLORS["gray_dark"])
    ax.set_ylabel("Puntaje de reseña", fontsize=10)
    ax.set_xlabel("")
    ax.set_ylim(0, 5.1)
    ax.yaxis.grid(True, linestyle="-", linewidth=0.7, color=TP_COLORS["gray_muted"], alpha=0.75)
    ax.set_axisbelow(True)

    for i, v in enumerate(plot_df["avg_review_score"]):
        ax.text(
            i,
            v + 0.12,
            f"{v:.2f}",
            ha="center",
            va="bottom",
            color=TP_COLORS["gray_dark"],
            fontsize=10,
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.18",
                facecolor=colors[i],
                edgecolor="none",
                alpha=0.95,
            )
        )

    ax = axes[1]
    ax.bar(plot_df["scenario"], plot_df["bad_review_rate"], color=colors, width=0.58, edgecolor="none")
    ax.set_title("Tasa de mala reseña", fontsize=12, color=TP_COLORS["gray_dark"])
    ax.set_ylabel("Proporción", fontsize=10)
    ax.set_xlabel("")
    ax.set_ylim(0, max(plot_df["bad_review_rate"].max() * 1.28, 0.75))
    ax.yaxis.set_major_formatter(FuncFormatter(fmt_pct))
    ax.yaxis.grid(True, linestyle="-", linewidth=0.7, color=TP_COLORS["gray_muted"], alpha=0.75)
    ax.set_axisbelow(True)

    for i, v in enumerate(plot_df["bad_review_rate"]):
        ax.text(
            i,
            v + 0.018,
            f"{v:.0%}",
            ha="center",
            va="bottom",
            color=TP_COLORS["gray_dark"],
            fontsize=10,
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.18",
                facecolor=colors[i],
                edgecolor="none",
                alpha=0.95,
            )
        )

    plt.tight_layout()
    return fig


def plot_pain_matrix(priority_categories: pd.DataFrame):
    apply_plot_style()

    plot_df = priority_categories.head(10).copy()
    plot_df["product_category_label"] = plot_df["product_category"].apply(prettify_label)

    x_ref = plot_df["n_items"].median()
    y_ref = plot_df["bad_review_rate"].median()

    x_left = x_ref - plot_df["n_items"].min()
    x_right = plot_df["n_items"].max() - x_ref
    x_half_range = max(x_left, x_right) * 1.08

    y_down = y_ref - plot_df["bad_review_rate"].min()
    y_up = plot_df["bad_review_rate"].max() - y_ref
    y_half_range = max(y_down, y_up) * 1.10

    x_min = max(0, x_ref - x_half_range)
    x_max = x_ref + x_half_range
    y_min = max(0, y_ref - y_half_range)
    y_max = y_ref + y_half_range

    fig, ax = plt.subplots(figsize=(10.5, 6), facecolor=TP_COLORS["white"])

    quadrant_blue = TP_COLORS["blue_soft"]
    quadrant_alpha = 0.08

    ax.add_patch(Rectangle((x_min, y_ref), x_ref - x_min, y_max - y_ref,
                           facecolor=quadrant_blue, alpha=quadrant_alpha, edgecolor="none", zorder=0))
    ax.add_patch(Rectangle((x_min, y_min), x_ref - x_min, y_ref - y_min,
                           facecolor=quadrant_blue, alpha=quadrant_alpha, edgecolor="none", zorder=0))
    ax.add_patch(Rectangle((x_ref, y_min), x_max - x_ref, y_ref - y_min,
                           facecolor=quadrant_blue, alpha=quadrant_alpha, edgecolor="none", zorder=0))
    ax.add_patch(Rectangle((x_ref, y_ref), x_max - x_ref, y_max - y_ref,
                           facecolor=TP_COLORS["yellow_accent"], alpha=0.12, edgecolor="none", zorder=0))

    sizes = plot_df["total_revenue"] / 3500.0

    ax.scatter(
        plot_df["n_items"],
        plot_df["bad_review_rate"],
        s=sizes,
        color=TP_COLORS["blue_secondary"],
        alpha=0.85,
        edgecolors=TP_COLORS["white"],
        linewidths=1.2,
        zorder=3,
    )

    for _, row in plot_df.iterrows():
        ax.annotate(
            row["product_category_label"],
            (row["n_items"], row["bad_review_rate"]),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
            color=TP_COLORS["gray_dark"],
        )

    ax.axvline(x_ref, color=TP_COLORS["gray_muted"], linestyle="--", linewidth=1.3, zorder=1)
    ax.axhline(y_ref, color=TP_COLORS["gray_muted"], linestyle="--", linewidth=1.3, zorder=1)

    ax.set_title(
        "Matriz de priorización: escala comercial vs mala experiencia",
        fontsize=14,
        fontweight="bold",
        color=TP_COLORS["blue_primary"],
        pad=14,
    )

    ax.set_xlabel("Ítems vendidos", fontsize=11, color=TP_COLORS["gray_dark"])
    ax.set_ylabel("Tasa de mala reseña", fontsize=11, color=TP_COLORS["gray_dark"])
    ax.xaxis.set_major_formatter(FuncFormatter(fmt_int))
    ax.yaxis.set_major_formatter(FuncFormatter(fmt_pct))
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color(TP_COLORS["gray_dark"])

    ax.grid(True, linestyle="-", linewidth=0.7, color=TP_COLORS["gray_muted"], alpha=0.55)
    ax.set_axisbelow(True)

    ax.text(
        0.98, 0.96, "Mayor prioridad",
        transform=ax.transAxes,
        fontsize=9,
        ha="right",
        va="top",
        color=TP_COLORS["gray_dark"],
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.25", facecolor=TP_COLORS["yellow_accent"], edgecolor="none")
    )

    ax.text(0.02, 0.96, "Escala menor,\nfricción mayor", transform=ax.transAxes,
            fontsize=8.7, ha="left", va="top", color=TP_COLORS["gray_text"])
    ax.text(0.02, 0.05, "Escala menor,\nfricción menor", transform=ax.transAxes,
            fontsize=8.7, ha="left", va="bottom", color=TP_COLORS["gray_text"])
    ax.text(0.98, 0.05, "Escala mayor,\nfricción menor", transform=ax.transAxes,
            fontsize=8.7, ha="right", va="bottom", color=TP_COLORS["gray_text"])

    plt.tight_layout()
    return fig


def plot_segment_distribution(customer_primary_segment_summary: pd.DataFrame):
    apply_plot_style()

    plot_df = customer_primary_segment_summary.sort_values("n_customers", ascending=True).copy()

    fig, ax = plt.subplots(figsize=(9.2, 4.9), facecolor=TP_COLORS["white"])
    ax.barh(
        plot_df["segment_alias"],
        plot_df["n_customers"],
        color=TP_COLORS["blue_secondary"],
        edgecolor="none",
        height=0.72,
    )

    ax.set_title(
        "Distribución de clientes por segmento primario",
        fontsize=14,
        fontweight="bold",
        color=TP_COLORS["blue_primary"],
        pad=14,
    )
    ax.set_xlabel("Clientes", color=TP_COLORS["gray_dark"], fontsize=11)
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(FuncFormatter(fmt_int))
    ax.xaxis.grid(True, linestyle="-", linewidth=0.7, color=TP_COLORS["gray_muted"], alpha=0.75)
    ax.set_axisbelow(True)
    ax.spines["left"].set_color(TP_COLORS["gray_dark"])
    ax.spines["bottom"].set_color(TP_COLORS["gray_dark"])

    max_val = plot_df["n_customers"].max()
    for i, (_, row) in enumerate(plot_df.iterrows()):
        share = row["share_pct"] if "share_pct" in row else 0
        ax.text(
            row["n_customers"] + max_val * 0.01,
            i,
            f'{row["n_customers"]:,.0f} ({share:.1%})',
            va="center",
            ha="left",
            color=TP_COLORS["gray_text"],
            fontsize=10,
        )

    ax.set_xlim(0, max_val * 1.18)
    plt.tight_layout()
    return fig


def plot_flags(customer_flag_summary: pd.DataFrame):
    apply_plot_style()

    plot_df = customer_flag_summary.sort_values("n_customers", ascending=True).copy()
    plot_df["flag_label"] = plot_df["flag_name"].map({
        "HIGH_VALUE": "Valor alto",
        "FRICTION_RISK": "Riesgo de fricción",
        "CHURN_SIGNAL": "Señal de abandono",
    }).fillna(plot_df["flag_name"])

    fig, ax = plt.subplots(figsize=(8.8, 4.2), facecolor=TP_COLORS["white"])
    ax.barh(
        plot_df["flag_label"],
        plot_df["n_customers"],
        color=TP_COLORS["blue_soft"],
        edgecolor="none",
        height=0.72,
    )

    ax.set_title(
        "Incidencia de flags de valor y riesgo",
        fontsize=13,
        fontweight="bold",
        color=TP_COLORS["blue_primary"],
        pad=14,
    )
    ax.set_xlabel("Clientes", color=TP_COLORS["gray_dark"], fontsize=11)
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(FuncFormatter(fmt_int))
    ax.xaxis.grid(True, linestyle="-", linewidth=0.7, color=TP_COLORS["gray_muted"], alpha=0.75)
    ax.set_axisbelow(True)
    ax.spines["left"].set_color(TP_COLORS["gray_dark"])
    ax.spines["bottom"].set_color(TP_COLORS["gray_dark"])

    max_val = plot_df["n_customers"].max()
    for i, (_, row) in enumerate(plot_df.iterrows()):
        share = row["share_pct"] if "share_pct" in row else 0
        ax.text(
            row["n_customers"] + max_val * 0.01,
            i,
            f'{row["n_customers"]:,.0f} ({share:.1%})',
            va="center",
            ha="left",
            color=TP_COLORS["gray_text"],
            fontsize=10,
        )

    ax.set_xlim(0, max_val * 1.18)
    plt.tight_layout()
    return fig


def plot_city_priority(city_priority: pd.DataFrame):
    apply_plot_style()

    plot_df = city_priority.head(10).sort_values("city_priority_score", ascending=True).copy()
    plot_df["city_label"] = (
        plot_df["customer_city"].astype(str).str.title() + ", " + plot_df["customer_state"].astype(str)
    )

    fig, ax = plt.subplots(figsize=(9.2, 4.9), facecolor=TP_COLORS["white"])
    ax.barh(
        plot_df["city_label"],
        plot_df["city_priority_score"],
        color=TP_COLORS["blue_secondary"],
        edgecolor="none",
        height=0.72,
    )

    ax.set_title(
        "Ciudades con mayor prioridad para expansión física",
        fontsize=14,
        fontweight="bold",
        color=TP_COLORS["blue_primary"],
        pad=14,
    )
    ax.set_xlabel("Índice de prioridad comercial", color=TP_COLORS["gray_dark"], fontsize=11)
    ax.set_ylabel("")
    ax.xaxis.grid(True, linestyle="-", linewidth=0.7, color=TP_COLORS["gray_muted"], alpha=0.75)
    ax.set_axisbelow(True)
    ax.spines["left"].set_color(TP_COLORS["gray_dark"])
    ax.spines["bottom"].set_color(TP_COLORS["gray_dark"])

    plt.tight_layout()
    return fig


# =========================================================
# 7. Data loading
# =========================================================
try:
    q1q2 = build_q1_q2_assets()
    q3q5 = build_q3_q5_assets()
except Exception as exc:
    st.error(f"No fue posible cargar los datos necesarios para esta página: {exc}")
    st.stop()

top_categories_volume = q1q2["top_categories_volume"]
top_categories_revenue = q1q2["top_categories_revenue"]
category_sales = q1q2["category_sales"]
delay_view = q1q2["delay_view"]
priority_categories = q1q2["priority_categories"]

customer_primary_segment_summary = q3q5["customer_primary_segment_summary"]
customer_flag_summary = q3q5["customer_flag_summary"]
city_priority = q3q5["city_priority"]
top_city = q3q5["top_city"]


# =========================================================
# 8. Narrative values
# =========================================================
top_volume_category_raw = top_categories_volume.loc[0, "product_category"]
top_revenue_category_raw = top_categories_revenue.loc[0, "product_category"]

top_volume_category = prettify_label(top_volume_category_raw)
top_revenue_category = prettify_label(top_revenue_category_raw)

late_bad = delay_view.loc[delay_view["scenario"] == "Entrega tardía", "bad_review_rate"].iloc[0]
on_time_bad = delay_view.loc[delay_view["scenario"] == "Entrega puntual", "bad_review_rate"].iloc[0]
late_score = delay_view.loc[delay_view["scenario"] == "Entrega tardía", "avg_review_score"].iloc[0]
on_time_score = delay_view.loc[delay_view["scenario"] == "Entrega puntual", "avg_review_score"].iloc[0]

top_segment_alias = (
    customer_primary_segment_summary
    .sort_values("n_customers", ascending=False)
    .iloc[0]["segment_alias"]
)

top_city_label = f'{str(top_city["customer_city"]).title()}, {top_city["customer_state"]}'

priority_top = priority_categories.head(3)["product_category"].apply(prettify_label).tolist()
priority_text = ", ".join(priority_top)


# =========================================================
# 9. Page content
# =========================================================
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-badge">DEMO EJECUTIVA · Q1–Q5</div>
        <div class="hero-title">Hallazgos clave para la decisión comercial</div>
        <div class="hero-subtitle">Síntesis ejecutiva de ventas, experiencia del cliente, segmentación y expansión</div>
        <p class="hero-note">
            Esta página resume, en un solo recorrido, los principales resultados del análisis:
            qué categorías sostienen el negocio, qué factor explica la mayor parte del deterioro en la experiencia,
            cómo conviene organizar la base de clientes y qué ciudad presenta mejores condiciones
            para una expansión física con criterio comercial.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="story-strip">
        <div class="story-card">
            <div class="label">Lectura comercial</div>
            <div class="value">No hay una categoría dominante por sí sola; sí existe un grupo líder que explica una parte relevante del negocio.</div>
        </div>
        <div class="story-card">
            <div class="label">Lectura de experiencia</div>
            <div class="value">La entrega tardía es la señal más fuerte asociada al deterioro en reseñas y calificación del cliente.</div>
        </div>
        <div class="story-card">
            <div class="label">Implicación estratégica</div>
            <div class="value">La recomendación es actuar en tres frentes: segmentar mejor, personalizar la oferta y evaluar expansión con base comercial digital.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="summary-card">
        <div class="summary-title">Conclusiones ejecutivas</div>
        <ul class="summary-list">
            <li>El portafolio muestra liderazgo compartido: varias categorías tienen peso relevante, sin que una sola concentre el negocio.</li>
            <li>La entrega tardía presenta la asociación más fuerte con la caída en satisfacción, por lo que la mejora operativa debe ser prioritaria.</li>
            <li>Las decisiones de negocio ganan solidez cuando se combinan lectura comercial, segmentación de clientes y un criterio prudente de expansión.</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Q1
# ---------------------------------------------------------
st.markdown(
    """
    <div class="section-card">
        <div class="section-title">1. Qué categorías sostienen el negocio</div>
        <div class="section-text">
            La primera conclusión es que el negocio no depende de una sola lógica comercial.
            Algunas categorías destacan por volumen y otras por capacidad de generar ingreso.
            Esta diferencia es importante porque cambia la forma en que se deben priorizar campañas,
            inventario y visibilidad comercial.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_q1a, col_q1b = st.columns(2, gap="large")

with col_q1a:
    st.pyplot(plot_q1_volume(top_categories_volume, category_sales), clear_figure=True)
    st.markdown(
        f"""
        <div class="chart-caption">
            Lectura: <strong>{top_volume_category}</strong> lidera en unidades vendidas.
            Esta vista ayuda a identificar categorías de alta rotación y peso operativo.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_q1b:
    st.pyplot(plot_q1_revenue(top_categories_revenue, category_sales), clear_figure=True)
    st.markdown(
        f"""
        <div class="chart-caption">
            Lectura: <strong>{top_revenue_category}</strong> lidera en ingresos.
            Esta vista resalta qué categorías aportan mayor valor económico al portafolio.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <div class="callout">
        <strong>Conclusión del punto:</strong> <em>{top_volume_category}</em> lidera por volumen y
        <em>{top_revenue_category}</em> lidera por ingresos. El dato sugiere un portafolio relativamente diversificado,
        con un grupo de categorías líderes más que con una sola categoría dominante. Por eso conviene evaluar el negocio
        con al menos dos lentes: rotación e ingreso.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Q2
# ---------------------------------------------------------
st.markdown(
    """
    <div class="section-card">
        <div class="section-title">2. Qué factor está deteriorando la experiencia del cliente</div>
        <div class="section-text">
            La evidencia apunta a una causa principal: cuando la entrega no se cumple, la satisfacción baja
            de forma visible. Esto sugiere que la experiencia del cliente está siendo afectada,
            sobre todo, por fricción logística y no únicamente por el producto.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.pyplot(plot_delay_impact(delay_view), clear_figure=True)
st.markdown(
    """
    <div class="chart-caption">
        Lectura: la comparación entre entregas puntuales y tardías permite medir cuánto cambia
        la experiencia cuando falla el cumplimiento prometido.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="callout">
        <strong>Conclusión del punto:</strong> con entrega puntual, la tasa de mala reseña es de {on_time_bad:.0%}
        y la calificación promedio es {on_time_score:.2f}. Con entrega tardía, la mala reseña sube a {late_bad:.0%}
        y la calificación promedio cae a {late_score:.2f}. La evidencia sugiere que la puntualidad de entrega
        es la señal más fuerte asociada al deterioro de la experiencia, por lo que debería tratarse como una prioridad operativa.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-card">
        <div class="section-title">3. Dónde conviene intervenir primero</div>
        <div class="section-text">
            No todas las categorías necesitan el mismo nivel de urgencia.
            La matriz siguiente combina tamaño comercial y severidad de la mala experiencia
            para identificar dónde una mejora operativa o comercial tendría mayor retorno.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.pyplot(plot_pain_matrix(priority_categories), clear_figure=True)
st.markdown(
    """
    <div class="chart-caption">
        Lectura: la zona superior derecha concentra categorías donde coinciden alta escala comercial
        y una experiencia más frágil; allí se ubican los focos de intervención prioritaria.
    </div>
    """,
    unsafe_allow_html=True,
)

priority_main_categories = ["Bed Bath Table", "Furniture Decor", "Computers Accessories"]
priority_secondary_categories = ["Office Furniture"]

priority_main_text = ", ".join(priority_main_categories)
priority_secondary_text = ", ".join(priority_secondary_categories)

st.markdown(
    f"""
    <div class="decision-box">
        <strong>Decisión sugerida:</strong> la prioridad principal debería concentrarse en {priority_main_text},
        donde coinciden una escala relevante y una experiencia más frágil. En cambio, {priority_secondary_text}
        muestra una señal de fricción importante, pero sobre una base comercial menor, por lo que conviene tratarla
        como un frente específico de revisión y no como el primer foco masivo de intervención.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Q3
# ---------------------------------------------------------
st.markdown(
    """
    <div class="section-card">
        <div class="section-title">4. Cómo ordenar la base de clientes para actuar mejor</div>
        <div class="section-text">
            La segmentación permite pasar de una base de clientes homogénea a una lectura más útil para negocio.
            En lugar de tratar a todos igual, conviene separar grupos con comportamientos distintos
            y complementar esa lectura con señales de valor o riesgo.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_q3a, col_q3b = st.columns(2, gap="large")

with col_q3a:
    st.pyplot(plot_segment_distribution(customer_primary_segment_summary), clear_figure=True)
    st.markdown(
        """
        <div class="chart-caption">
            Lectura: esta distribución muestra cómo se reparte la base de clientes entre segmentos principales
            pensados para operación, marketing y personalización.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_q3b:
    st.pyplot(plot_flags(customer_flag_summary), clear_figure=True)
    st.markdown(
        """
        <div class="chart-caption">
            Lectura: los flags complementan el segmento principal y ayudan a identificar clientes con valor alto,
            fricción o señales de abandono.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <div class="callout">
        <strong>Conclusión del punto:</strong> el segmento con mayor peso es <em>{top_segment_alias}</em>.
        Más que describir clientes, esta estructura permite ordenar decisiones comerciales: diferenciar acciones
        de fidelización, recuperación y seguimiento según el valor y el riesgo de cada grupo.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Q4
# ---------------------------------------------------------
st.markdown(
    """
    <div class="section-card">
        <div class="section-title">5. Cómo recomendar mejor en tiempo real</div>
        <div class="section-text">
            La recomendación propuesta se apoya en una lógica sencilla y explicable:
            entender el perfil del cliente, resumir su historial, generar opciones probables
            y mostrar pocas recomendaciones con sentido comercial.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4, gap="medium")

with c1:
    st.markdown(
        """
        <div class="mini-card">
            <h4>1. Leer el contexto</h4>
            <p>
                Se usa el segmento principal, las señales de riesgo y las preferencias del cliente
                para entender su situación comercial.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
        <div class="mini-card">
            <h4>2. Resumir el historial</h4>
            <p>
                Se identifica qué compra, con qué frecuencia y qué categorías son más relevantes
                para ese cliente.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div class="mini-card">
            <h4>3. Generar candidatos</h4>
            <p>
                Se combinan productos populares, afinidad por categoría y señales del segmento
                para construir opciones probables.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        """
        <div class="mini-card">
            <h4>4. Priorizar lo útil</h4>
            <p>
                Se seleccionan pocas recomendaciones, claras y coherentes con la necesidad
                del cliente en ese momento.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="decision-box">
        <strong>Decisión sugerida:</strong> avanzar con una recomendación híbrida y explicable como primera versión operativa.
        Este enfoque es suficiente para capturar valor comercial en el corto plazo y, al mismo tiempo, deja una base ordenada
        para evolucionar a experiencias más avanzadas de personalización.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Q5
# ---------------------------------------------------------
st.markdown(
    """
    <div class="section-card">
        <div class="section-title">6. Qué ciudad presenta la mejor base para expansión física</div>
        <div class="section-text">
            Como el dataset no incluye variables físicas como tráfico, arriendo o costos de ubicación,
            la recomendación se apoya en evidencia comercial digital: ingresos, número de órdenes,
            base activa de clientes y ticket promedio.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_q5a, col_q5b = st.columns([1.3, 0.95], gap="large")

with col_q5a:
    st.pyplot(plot_city_priority(city_priority), clear_figure=True)
    st.markdown(
        """
        <div class="chart-caption">
            Lectura: esta vista resume qué ciudades combinan mejor escala comercial,
            base de clientes y valor promedio por compra.
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_q5b:
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">Ciudad recomendada</div>
            <div class="section-text">
                La primera ciudad candidata para una evaluación de expansión física es <strong>{top_city_label}</strong>.
            </div>
            <div class="callout">
                <strong>Fundamento:</strong><br>
                esta ciudad combina una base comercial robusta, buen volumen de órdenes,
                una base activa de clientes y un ticket competitivo frente a otras ciudades líderes.
            </div>
            <div class="decision-box">
                <strong>Ingresos totales:</strong> ${float(top_city["total_revenue"]):,.0f}<br>
                <strong>Órdenes:</strong> {int(top_city["n_orders"]):,}<br>
                <strong>Clientes únicos:</strong> {int(top_city["n_customers"]):,}<br>
                <strong>Ticket promedio:</strong> ${float(top_city["avg_order_value"]):,.2f}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# Final synthesis
# ---------------------------------------------------------
st.markdown(
    """
    <div class="section-card">
        <div class="section-title">7. Cierre </div>
        <div class="section-text">
            En conjunto, los hallazgos muestran una ruta clara: cuidar la experiencia donde más se deteriora,
            ordenar mejor la gestión comercial por tipo de cliente y priorizar el crecimiento con criterios de negocio.
        </div>
        <div class="decision-box">
            <strong>Conclusión:</strong> la oportunidad no está en hacer más de todo, sino en intervenir mejor,
            personalizar con mayor criterio y crecer donde la evidencia comercial lo respalde.
        </div>
        <div class="section-text" style="margin-top: 0.8rem;">
            Gracias por revisar esta demostración. El análisis fue estructurado para traducir datos en decisiones, con una lógica clara, reusable y orientada a implementación.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Glossary
# ---------------------------------------------------------
with st.expander("Glosario breve de términos usados en esta página"):
    st.markdown(
        """
        <div class="glossary-note">
            <strong>Ingresos:</strong> dinero total generado por las ventas.<br><br>
            <strong>Volumen:</strong> cantidad de productos vendidos.<br><br>
            <strong>Mala reseña:</strong> evaluación negativa del cliente, usada aquí como señal de mala experiencia.<br><br>
            <strong>Segmentación:</strong> forma de agrupar clientes con comportamientos parecidos para tratarlos mejor.<br><br>
            <strong>Flag:</strong> alerta complementaria. No reemplaza el segmento; ayuda a resaltar riesgo o valor.<br><br>
            <strong>Ticket promedio:</strong> valor promedio de una compra.<br><br>
            <strong>Recomendador híbrido:</strong> sistema que combina varias señales, como historial, popularidad y afinidad, en lugar de depender de una sola regla.<br><br>
            <strong>Tienda insignia:</strong> punto físico principal o representativo de la marca.
        </div>
        """,
        unsafe_allow_html=True,
    )