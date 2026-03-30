from pathlib import Path
import sys
import streamlit as st


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "src").exists() and (candidate / "data").exists():
            return candidate
    raise RuntimeError("No fue posible ubicar la raíz del proyecto.")


PROJECT_ROOT = find_project_root(Path(__file__).resolve())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

st.set_page_config(
    page_title="Commercial Analytics AI Challenge",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
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

GITHUB_URL = "https://github.com/danielhcertuche/commercial-analytics-ai-challenge/tree/main"

st.markdown(
    f"""
    <style>
        .stApp {{
            background:
                radial-gradient(circle at top right, rgba(110, 193, 228, 0.08), transparent 18%),
                linear-gradient(180deg, #FAFBFD 0%, {TP_COLORS["gray_bg"]} 100%);
        }}

        .block-container {{
            padding-top: 1.6rem;
            padding-bottom: 2.2rem;
            max-width: 1220px;
        }}

        section[data-testid="stSidebar"] {{
            background-color: #F2F5FB;
            border-right: 1px solid {TP_COLORS["gray_muted"]};
        }}

        .hero-card {{
            background: linear-gradient(180deg, {TP_COLORS["white"]} 0%, #FBFCFE 100%);
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 22px;
            padding: 2rem 2rem 1.5rem 2rem;
            box-shadow: 0 10px 28px rgba(31, 41, 55, 0.05);
            margin-bottom: 1.1rem;
        }}

        .tag {{
            display: inline-block;
            background: {TP_COLORS["yellow_accent"]};
            color: {TP_COLORS["gray_dark"]};
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.28rem 0.68rem;
            border-radius: 999px;
            margin-bottom: 0.85rem;
        }}

        .hero-title {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 2.25rem;
            font-weight: 780;
            line-height: 1.1;
            margin-bottom: 0.32rem;
        }}

        .hero-subtitle {{
            color: {TP_COLORS["gray_dark"]};
            font-size: 1.06rem;
            font-weight: 600;
            margin-bottom: 0.9rem;
        }}

        .hero-note {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.98rem;
            line-height: 1.78;
            max-width: 960px;
            margin-bottom: 0;
        }}

        .metric-card {{
            background: {TP_COLORS["gray_card"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 14px;
            padding: 0.95rem 1rem;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
        }}

        .metric-label {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.82rem;
            margin-bottom: 0.2rem;
        }}

        .metric-value {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 1.24rem;
            font-weight: 760;
            line-height: 1.2;
        }}

        .section-title {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 1.18rem;
            font-weight: 730;
            margin-top: 0.35rem;
            margin-bottom: 0.8rem;
        }}

        .panel {{
            background: {TP_COLORS["white"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 18px;
            padding: 1.15rem 1.2rem;
            box-shadow: 0 6px 18px rgba(31, 41, 55, 0.04);
            height: 100%;
        }}

        .panel h3 {{
            color: {TP_COLORS["gray_dark"]};
            font-size: 1rem;
            margin-top: 0;
            margin-bottom: 0.5rem;
        }}

        .panel p {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.94rem;
            line-height: 1.7;
            margin-bottom: 0.55rem;
        }}

        .panel ul {{
            margin: 0.35rem 0 0 0;
            padding-left: 1.2rem;
        }}

        .panel li {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.93rem;
            line-height: 1.7;
            margin-bottom: 0.22rem;
        }}

        .nav-card {{
            background: linear-gradient(180deg, {TP_COLORS["white"]} 0%, #FBFCFE 100%);
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 16px;
            padding: 1rem 1rem 0.95rem 1rem;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
            min-height: 185px;
        }}

        .nav-step {{
            color: {TP_COLORS["blue_secondary"]};
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }}

        .nav-card h4 {{
            color: {TP_COLORS["gray_dark"]};
            font-size: 1rem;
            margin-top: 0;
            margin-bottom: 0.45rem;
        }}

        .nav-card p {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.93rem;
            line-height: 1.65;
            margin-bottom: 0;
        }}

        .repo-card {{
            background: linear-gradient(180deg, {TP_COLORS["white"]} 0%, #FBFCFE 100%);
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 18px;
            padding: 1.1rem 1.2rem;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
            margin-top: 1rem;
        }}

        .repo-title {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 1rem;
            font-weight: 720;
            margin-bottom: 0.45rem;
        }}

        .repo-note {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.94rem;
            line-height: 1.68;
            margin-bottom: 0.8rem;
        }}

        .repo-links {{
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }}

        .repo-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            text-decoration: none;
            background: {TP_COLORS["blue_primary"]};
            color: {TP_COLORS["white"]} !important;
            font-weight: 600;
            font-size: 0.92rem;
            padding: 0.64rem 0.95rem;
            border-radius: 10px;
        }}

        .repo-btn-alt {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            text-decoration: none;
            background: {TP_COLORS["white"]};
            color: {TP_COLORS["gray_dark"]} !important;
            font-weight: 600;
            font-size: 0.92rem;
            padding: 0.64rem 0.95rem;
            border-radius: 10px;
            border: 1px solid {TP_COLORS["gray_muted"]};
        }}

        .footer-box {{
            background: {TP_COLORS["white"]};
            border-left: 5px solid {TP_COLORS["blue_secondary"]};
            border-radius: 14px;
            padding: 0.95rem 1rem;
            margin-top: 1rem;
            color: {TP_COLORS["gray_text"]};
            font-size: 0.94rem;
            line-height: 1.7;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# HERO
st.markdown(
    """
    <div class="hero-card">
        <div class="tag">DEMO DE PRUEBA TÉCNICA</div>
        <div class="hero-title">Commercial Analytics AI Challenge</div>
        <div class="hero-subtitle">Aplicación ejecutiva y demo funcional del proyecto desarrollado</div>
        <p class="hero-note">
            Esta aplicación fue diseñada como una entrada, clara y agradable al proyecto.
            Reúne en un mismo lugar la historia analítica del reto, la lógica de negocio derivada de los datos
            y una demostración local del agente personalizado. La intención es facilitar una lectura ordenada
            de cómo cada hallazgo se traduce en una decisión posible.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# MÉTRICAS
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Cobertura del reto</div>
            <div class="metric-value">Q1–Q7</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Modo de demostración</div>
            <div class="metric-value">Local · sin API</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Criterio de desarrollo</div>
            <div class="metric-value">Reproducible</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# INTRO
st.markdown('<div class="section-title">Antes de navegar</div>', unsafe_allow_html=True)

c1, c2 = st.columns([1.2, 1], gap="large")

with c1:
    st.markdown(
        """
        <div class="panel">
            <h3>Qué encontrará aquí</h3>
            <p>
                El recorrido se concentra en tres frentes. Primero, una lectura ejecutiva de los hallazgos
                comerciales más relevantes del reto. Después, una demo local del agente personalizado,
                construida para mostrar el comportamiento esperado sin depender de una API externa.
                Finalmente, una página de presentación que resume la solución propuesta, los criterios de diseño
                y los supuestos adoptados.
            </p>
            <ul>
                <li>Hallazgos Q1–Q5: resultados de negocio y decisiones sugeridas.</li>
                <li>Personalized Agent Demo: simulación funcional del caso Q6–Q7.</li>
                <li>Presentación: cierre ejecutivo de la propuesta completa.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
        <div class="panel">
            <h3>Base de datos y supuestos</h3>
            <p>
                El proyecto usa exclusivamente los datasets entregados en la prueba como evidencia principal.
                A partir de ellos se construyeron métricas, estadisticos, experiencia del cliente, segmentación,
                recomendación y priorización geográfica.
            </p>
            <ul>
                <li>Edad y género se asumieron disponibles desde CRM, como lo permite el enunciado.</li>
                <li>La base de conocimiento se apoya en productos líderes identificados desde el dataset.</li>
                <li>La demo del agente se dejó en modo "local" para priorizar estabilidad, bajo costo y trazabilidad.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# NAVEGACIÓN
st.markdown('<div class="section-title">Rutas disponibles en esta app</div>', unsafe_allow_html=True)

n1, n2, n3 = st.columns(3, gap="large")

with n1:
    st.markdown(
        """
        <div class="nav-card">
            <div class="nav-step">Ruta 1</div>
            <h4>Hallazgos Q1–Q5</h4>
            <p>
                Presenta los hallazgos principales del reto: qué mueve el negocio, qué afecta la experiencia,
                cómo conviene segmentar la base de clientes y qué criterio sostiene la expansión física.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with n2:
    st.markdown(
        """
        <div class="nav-card">
            <div class="nav-step">Ruta 2</div>
            <h4>Personalized Agent Demo</h4>
            <p>
                Muestra una "simulación local" del agente con escenarios representativos de cliente.
                El objetivo es evidenciar la lógica de personalización y el tono esperado de la respuesta.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with n3:
    st.markdown(
        """
        <div class="nav-card">
            <div class="nav-step">Ruta 3</div>
            <h4>Presentación</h4>
            <p>
                Resume la propuesta de forma ejecutiva: enfoque, componentes desarrollados,
                supuestos adoptados y lectura general del valor que aporta la solución.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# REPO
st.markdown(
    f"""
    <div class="repo-card">
        <div class="repo-title">Repositorio y material de entrega</div>
        <div class="repo-note">
            El análisis, los notebooks y la implementación usada para esta app se encuentran organizados
            en el repositorio del proyecto. Si para revisión resulta más práctico, el mismo contenido
            puede compartirse también en formato ZIP como alternativa.
        </div>
        <div class="repo-links">
            <a class="repo-btn" href="{GITHUB_URL}" target="_blank">🐙 Ver repositorio en GitHub</a>
            <a class="repo-btn-alt" href="{GITHUB_URL}" target="_blank">📦 Alternativa: entrega en ZIP</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# CIERRE
st.markdown(
    """
    <div class="footer-box">
        <strong>Nota metodológica:</strong> esta app no busca reemplazar la documentación técnica del proyecto,
        sino ofrecer una lectura más accesible, ordenada y presentable de la solución.
    </div>
    """,
    unsafe_allow_html=True,
)