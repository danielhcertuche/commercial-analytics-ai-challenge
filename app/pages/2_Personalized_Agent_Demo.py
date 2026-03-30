from pathlib import Path
import sys
import streamlit as st
import pandas as pd


# =========================================================
# 1. Project root and imports (VERSIÓN FLEXIBLE)
# =========================================================
def find_project_root(current_path: Path) -> Path:
    """
    Busca la raíz del proyecto de forma flexible para evitar RuntimeError.
    """
    root_markers = ["src", "requirements.txt", ".gitignore", "app"]
    for candidate in [current_path] + list(current_path.parents):
        if any((candidate / marker).exists() for marker in root_markers):
            return candidate
    return Path.cwd()

PROJECT_ROOT = find_project_root(Path(__file__).resolve())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Intentar importar módulos locales con manejo de errores
try:
    from src.data.loaders import load_all_datasets
    from src.analysis.site_selection import (
        build_city_sales_summary,
        add_city_priority_score,
    )
except ImportError:
    st.error("No se pudieron cargar los módulos de 'src'. Verifica la estructura de carpetas.")


from src.data.loaders import load_all_datasets
from src.analysis.knowledge_base import (
    build_item_level_sales_base,
    compute_product_sales,
    select_reference_products,
    build_knowledge_base_dict,
    build_prompt_ready_knowledge_base,
)
from src.prompts.system_prompts import (
    SYSTEM_PROMPTS,
    build_purchase_history_summary,
    render_system_prompt_structured,
)
from src.demo.agent_demo import local_mock_response

st.set_page_config(
    page_title="Personalized Agent Demo",
    page_icon="🤖",
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

        .page-card {{
            background: linear-gradient(180deg, {TP_COLORS["white"]} 0%, #FBFCFE 100%);
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 18px;
            padding: 1.4rem 1.55rem;
            box-shadow: 0 8px 24px rgba(31, 41, 55, 0.06);
            margin-bottom: 1rem;
        }}

        .demo-badge {{
            display: inline-block;
            background: {TP_COLORS["yellow_accent"]};
            color: {TP_COLORS["gray_dark"]};
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.24rem 0.58rem;
            border-radius: 999px;
            margin-bottom: 0.75rem;
        }}

        .page-title {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 1.95rem;
            font-weight: 750;
            margin-bottom: 0.25rem;
        }}

        .page-subtitle {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.98rem;
            line-height: 1.7;
            margin-bottom: 0;
        }}

        .section-card {{
            background: {TP_COLORS["gray_card"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 15px;
            padding: 1rem 1.1rem;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
            margin-bottom: 1rem;
        }}

        .section-title {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 1.08rem;
            font-weight: 700;
            margin-bottom: 0.6rem;
        }}

        .small-note {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.91rem;
            line-height: 1.6;
        }}

        .response-box {{
            background: #F9FAFB;
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 12px;
            padding: 1rem;
            color: {TP_COLORS["gray_dark"]};
            font-size: 0.95rem;
            line-height: 1.7;
            white-space: pre-wrap;
        }}

        .kpi-box {{
            background: {TP_COLORS["white"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 12px;
            padding: 0.8rem 0.9rem;
            margin-top: 0.3rem;
        }}

        .kpi-label {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.8rem;
            margin-bottom: 0.15rem;
        }}

        .kpi-value {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 1.15rem;
            font-weight: 700;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_demo_assets():
    processed_dir = PROJECT_ROOT / "data" / "processed"
    required_files = [
        processed_dir / "customer_360_features.csv",
    ]

    missing = [str(p.name) for p in required_files if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Faltan archivos en data/processed: " + ", ".join(missing)
        )

    customer_360_features = pd.read_csv(processed_dir / "customer_360_features.csv")
    bundle = load_all_datasets()

    item_base = build_item_level_sales_base(bundle)
    product_sales = compute_product_sales(item_base)
    reference_products = select_reference_products(
        product_sales,
        top_k=5,
        n_products=3,
    )
    knowledge_base = build_knowledge_base_dict(reference_products)
    knowledge_base_prompt = build_prompt_ready_knowledge_base(knowledge_base)

    return customer_360_features, reference_products, knowledge_base, knowledge_base_prompt


def build_profile_table(profile: dict) -> pd.DataFrame:
    rows = [
        {"atributo": "Edad", "valor": str(profile["edad"])},
        {"atributo": "Género", "valor": str(profile["genero"])},
        {"atributo": "Perfil principal", "valor": str(profile["perfil_de_cliente"])},
        {"atributo": "Flags activos", "valor": str(profile["flags"])},
    ]
    return pd.DataFrame(rows).astype(str)


def build_knowledge_base_table(knowledge_base: dict) -> pd.DataFrame:
    rows = []
    for item in knowledge_base.values():
        rows.append(
            {
                "product_id": str(item.get("product_id", "")),
                "category": str(item.get("product_category", "")),
                "avg_price": f"${float(item.get('avg_real_price', 0)):,.2f}",
                "commercial_message": str(item.get("marketing_description", "")),
            }
        )
    return pd.DataFrame(rows).astype(str)


def select_demo_scenario(customer_360_features: pd.DataFrame, scenario_name: str):
    if scenario_name == "young_digital_frequent":
        row = (
            customer_360_features
            .query("customer_segment_primary == 'CORE_LOYAL'")
            .sort_values(["frequency", "monetary"], ascending=[False, False])
            .iloc[0]
        )
        edad = 24
        justification = (
            "Se selecciona un cliente fiel y recurrente para representar un perfil digital, "
            "activo y con alta probabilidad de conversión."
        )

    elif scenario_name == "older_conservative_friction":
        row = (
            customer_360_features.loc[
                customer_360_features["customer_flags_text"]
                .fillna("")
                .str.contains("FRICTION_RISK", regex=False)
            ]
            .query("customer_segment_primary in ['CHURN_RISK', 'HIGH_VALUE_RISK']")
            .sort_values(["recency_days", "inactivity_risk_score"], ascending=[False, False])
            .iloc[0]
        )
        edad = 63
        justification = (
            "Se selecciona un cliente con señales de fricción o enfriamiento para probar "
            "una comunicación más conservadora y orientada a recuperar confianza."
        )

    else:
        row = (
            customer_360_features
            .query("customer_segment_primary == 'VIP'")
            .sort_values(["monetary", "avg_order_value"], ascending=[False, False])
            .iloc[0]
        )
        edad = 42
        justification = (
            "Se selecciona un cliente premium para representar una recomendación más curada, "
            "de mayor valor y con tono de atención diferenciada."
        )

    return row, edad, justification


try:
    customer_360_features, reference_products, knowledge_base, knowledge_base_prompt = load_demo_assets()
except Exception as exc:
    st.error(f"No fue posible cargar los activos del demo: {exc}")
    st.stop()

st.markdown(
    """
    <div class="page-card">
        <div class="demo-badge">DEMO LOCAL · Q6–Q7</div>
        <div class="page-title">Demo del agente hiper-personalizado</div>
        <p class="page-subtitle">
            Esta vista demuestra, de forma controlada y reproducible, cómo el sistema ajusta el tono,
            el encuadre comercial y la recomendación según el perfil del cliente. La ejecución actual
            opera en modo local para priorizar estabilidad, bajo costo y claridad en la presentación.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

scenario_options = {
    "young_digital_frequent": "Escenario 1 · Cliente joven, digital y frecuente",
    "older_conservative_friction": "Escenario 2 · Cliente mayor con fricción o riesgo",
    "vip_high_spend": "Escenario 3 · Cliente VIP o de alto valor",
}

scenario_name = st.selectbox(
    "Selecciona el escenario de demostración",
    options=list(scenario_options.keys()),
    format_func=lambda x: scenario_options[x],
)

row, edad, justification = select_demo_scenario(customer_360_features, scenario_name)

profile = {
    "edad": edad,
    "genero": "No especificado",
    "perfil_de_cliente": row["customer_segment_primary"],
    "historial_compras": build_purchase_history_summary(row.to_dict()),
    "flags": row["customer_flags_text"],
}

profile_df = build_profile_table(profile)
kb_df = build_knowledge_base_table(knowledge_base)

col_left, col_right = st.columns([1.05, 1.25], gap="large")

with col_left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Perfil de cliente utilizado en la demo</div>', unsafe_allow_html=True)
    st.dataframe(profile_df, width="stretch", hide_index=True)
    st.markdown(
        f"""
        <div class="small-note">
            <strong>Justificación del escenario:</strong><br>
            {justification}
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.markdown(
            f"""
            <div class="kpi-box">
                <div class="kpi-label">Recency days</div>
                <div class="kpi-value">{int(row["recency_days"]):,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with metric_col2:
        st.markdown(
            f"""
            <div class="kpi-box">
                <div class="kpi-label">Monetary</div>
                <div class="kpi-value">${float(row["monetary"]):,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Resumen de historial de compras</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="small-note">
            {profile["historial_compras"]}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Base de conocimiento empleada</div>', unsafe_allow_html=True)
    st.dataframe(kb_df, width="stretch", hide_index=True)
    st.markdown(
        """
        <div class="small-note">
            La base es deliberadamente pequeña para la demo: contiene productos líderes,
            precio promedio real y una descripción comercial breve, suficiente para condicionar
            el comportamiento del agente sin inflar contexto innecesariamente.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    prompt_text = render_system_prompt_structured(
        SYSTEM_PROMPTS[scenario_name],
        edad=profile["edad"],
        genero=profile["genero"],
        perfil_de_cliente=profile["perfil_de_cliente"],
        historial_compras=profile["historial_compras"],
        base_conocimiento=knowledge_base_prompt,
    )

    with st.expander("Ver prompt renderizado"):
        st.code(prompt_text, language="text")

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Respuesta simulada del agente</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="small-note">
        Esta respuesta se genera con una lógica local de demostración. El objetivo no es competir
        con un motor generativo en producción, sino evidenciar cómo cambia el mensaje cuando
        varía el contexto del cliente, el historial resumido y la base de conocimiento.
    </div>
    """,
    unsafe_allow_html=True,
)

if st.button("Generar recomendación personalizada", type="primary"):
    profile_payload = {
        "edad": profile["edad"],
        "genero": profile["genero"],
        "perfil_de_cliente": profile["perfil_de_cliente"],
        "historial_compras": profile["historial_compras"],
        "flags": profile["flags"],
    }

    response_text = local_mock_response(
        scenario_name=scenario_name,
        profile=profile_payload,
        knowledge_base=knowledge_base,
    )

    safe_response = (
        response_text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )

    st.markdown(
        f'<div class="response-box">{safe_response}</div>',
        unsafe_allow_html=True,
    )
else:
    st.info(
        "Selecciona un escenario y ejecuta la demostración para visualizar la respuesta personalizada del agente."
    )

st.markdown("</div>", unsafe_allow_html=True)