from __future__ import annotations

import json
from typing import Any

import pandas as pd


CATEGORY_COPY = {
    "bed_bath_table": {
        "headline": "Funcionalidad y confort para el hogar",
        "description": (
            "Producto destacado para el hogar, pensado para clientes que valoran "
            "practicidad, orden y una mejora tangible en su rutina diaria."
        ),
    },
    "health_beauty": {
        "headline": "Bienestar con alta tracción comercial",
        "description": (
            "Referencia muy atractiva dentro del portafolio de cuidado personal, "
            "ideal para campañas de recompra, rutina y autocuidado."
        ),
    },
    "sports_leisure": {
        "headline": "Movimiento, ocio y estilo de vida activo",
        "description": (
            "Producto con buena demanda para clientes que buscan dinamismo, bienestar "
            "y experiencias asociadas a actividad física o tiempo libre."
        ),
    },
    "furniture_decor": {
        "headline": "Estética y renovación de espacios",
        "description": (
            "Opción con potencial comercial para clientes interesados en transformar "
            "sus espacios con soluciones funcionales y visualmente atractivas."
        ),
    },
    "computers_accessories": {
        "headline": "Practicidad digital y uso cotidiano",
        "description": (
            "Producto orientado a clientes con hábitos digitales, útil para propuestas "
            "de conveniencia, productividad y compra complementaria."
        ),
    },
    "watches_gifts": {
        "headline": "Compra aspiracional y de obsequio",
        "description": (
            "Referencia muy útil para campañas de regalo, ocasión especial y consumo "
            "emocional de ticket medio o alto."
        ),
    },
    "default": {
        "headline": "Producto destacado del portafolio",
        "description": (
            "Producto con desempeño comercial relevante dentro del catálogo, adecuado "
            "para campañas de conversión, visibilidad y recomendación."
        ),
    },
}


def build_item_level_sales_base(bundle: Any) -> pd.DataFrame:
    """
    Construye una base a nivel ítem vendido y entregado.
    """
    orders = bundle.orders.copy()
    order_items = bundle.order_items.copy()
    products = bundle.products.copy()
    translation = bundle.product_category_translation.copy()

    delivered_orders = orders.loc[orders["order_status"] == "delivered"].copy()

    item_base = (
        order_items
        .merge(
            delivered_orders[["order_id", "order_status", "order_purchase_timestamp"]],
            on="order_id",
            how="inner",
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

    return item_base


def compute_product_sales(item_base: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega métricas por producto.
    """
    product_sales = (
        item_base.groupby("product_id", as_index=False)
        .agg(
            product_category=("product_category", lambda s: s.mode().iloc[0] if not s.mode().empty else "unknown"),
            total_volume=("order_item_id", "count"),
            total_revenue=("item_revenue", "sum"),
            avg_price=("price", "mean"),
            n_orders=("order_id", "nunique"),
        )
    )

    return product_sales


def compute_top_products(
    product_sales: pd.DataFrame,
    *,
    top_k: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    top_products_volume = (
        product_sales
        .sort_values(["total_volume", "total_revenue"], ascending=[False, False])
        .head(top_k)
        .reset_index(drop=True)
    )

    top_products_revenue = (
        product_sales
        .sort_values(["total_revenue", "total_volume"], ascending=[False, False])
        .head(top_k)
        .reset_index(drop=True)
    )

    return top_products_volume, top_products_revenue


def select_reference_products(
    product_sales: pd.DataFrame,
    *,
    top_k: int = 5,
    n_products: int = 3,
) -> pd.DataFrame:
    """
    Selecciona 3 productos de referencia a partir de la unión de:
    - top productos por volumen
    - top productos por ingresos
    """
    top_volume, top_revenue = compute_top_products(product_sales, top_k=top_k)

    top_volume = top_volume.copy()
    top_revenue = top_revenue.copy()

    top_volume["rank_volume"] = range(1, len(top_volume) + 1)
    top_revenue["rank_revenue"] = range(1, len(top_revenue) + 1)

    ref = (
        product_sales
        .merge(
            top_volume[["product_id", "rank_volume"]],
            on="product_id",
            how="left",
        )
        .merge(
            top_revenue[["product_id", "rank_revenue"]],
            on="product_id",
            how="left",
        )
    )

    default_rank = top_k + 2
    ref["rank_volume"] = ref["rank_volume"].fillna(default_rank)
    ref["rank_revenue"] = ref["rank_revenue"].fillna(default_rank)

    ref = ref.loc[
        (ref["rank_volume"] <= top_k) | (ref["rank_revenue"] <= top_k)
    ].copy()

    ref["selection_score"] = (
        (1 / ref["rank_volume"]) +
        (1 / ref["rank_revenue"])
    )

    ref = (
        ref.sort_values(
            ["selection_score", "total_revenue", "total_volume"],
            ascending=[False, False, False],
        )
        .head(n_products)
        .reset_index(drop=True)
    )

    return ref


def _build_marketing_description(row: pd.Series) -> str:
    category = row["product_category"]
    avg_price = row["avg_price"]
    total_volume = row["total_volume"]
    n_orders = row["n_orders"]

    copy_pack = CATEGORY_COPY.get(category, CATEGORY_COPY["default"])
    headline = copy_pack["headline"]
    base_desc = copy_pack["description"]

    return (
        f"{headline}. {base_desc} "
        f"En el dataset mostró una tracción destacada con {int(total_volume):,} ítems vendidos "
        f"y {int(n_orders):,} órdenes asociadas. "
        f"Su precio real promedio fue de ${avg_price:,.2f}, lo que lo convierte en una referencia "
        f"atractiva para campañas de recomendación y personalización."
    )


def build_knowledge_base_dict(reference_products: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """
    Construye una base de conocimiento pequeña, honesta y reusable.
    """
    kb: dict[str, dict[str, Any]] = {}

    for _, row in reference_products.iterrows():
        product_id = row["product_id"]
        kb[product_id] = {
            "product_id": product_id,
            "product_category": row["product_category"],
            "avg_real_price": round(float(row["avg_price"]), 2),
            "sales_signals": {
                "total_volume": int(row["total_volume"]),
                "total_revenue": round(float(row["total_revenue"]), 2),
                "n_orders": int(row["n_orders"]),
            },
            "marketing_description": _build_marketing_description(row),
        }

    return kb


def knowledge_base_to_json(knowledge_base: dict[str, dict[str, Any]]) -> str:
    return json.dumps(knowledge_base, ensure_ascii=False, indent=2)


def save_knowledge_base_json(
    knowledge_base: dict[str, dict[str, Any]],
    output_path: str,
) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
        
def build_prompt_ready_knowledge_base(knowledge_base: dict[str, dict]) -> str:
    lines = []
    for _, item in knowledge_base.items():
        lines.append(
            f"- {item['product_id']} | categoría: {item['product_category']} | "
            f"precio promedio: ${item['avg_real_price']:,.2f} | "
            f"mensaje comercial: {item['marketing_description']}"
        )
    return "\n".join(lines)