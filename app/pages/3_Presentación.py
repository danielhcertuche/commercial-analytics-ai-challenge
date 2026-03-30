from pathlib import Path
import sys
import base64
import streamlit as st


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "app").exists() and (candidate / "src").exists():
            return candidate
    raise RuntimeError("No fue posible ubicar la raíz del proyecto.")


def find_presentation_files(project_root: Path):
    """
    Busca la presentación en rutas de proyecto y también en /mnt/data
    para facilitar pruebas locales y ejecución en entornos temporales.
    """
    pdf_candidates = [
        project_root / "outputs" / "reports" / "commercial_analytics_executive_presentation.pdf",
        project_root / "commercial_analytics_executive_presentation.pdf",
        Path("/mnt/data/pdfout/commercial_analytics_executive_presentation.pdf"),
        Path("/mnt/data/commercial_analytics_executive_presentation.pdf"),
    ]

    pptx_candidates = [
        project_root / "outputs" / "reports" / "commercial_analytics_executive_presentation.pptx",
        project_root / "commercial_analytics_executive_presentation.pptx",
        Path("/mnt/data/commercial_analytics_executive_presentation.pptx"),
    ]

    pdf_path = next((p for p in pdf_candidates if p.exists()), None)
    pptx_path = next((p for p in pptx_candidates if p.exists()), None)

    return pdf_path, pptx_path


PROJECT_ROOT = find_project_root(Path(__file__).resolve())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

pdf_path, pptx_path = find_presentation_files(PROJECT_ROOT)

st.set_page_config(
    page_title="Presentación ejecutiva",
    page_icon="🧾",
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
            max-width: 1260px;
            padding-top: 1.6rem;
            padding-bottom: 2rem;
        }}

        .hero-card {{
            background: {TP_COLORS["gray_card"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 18px;
            padding: 1.45rem 1.55rem;
            box-shadow: 0 6px 18px rgba(31, 41, 55, 0.05);
            margin-bottom: 1rem;
        }}

        .tag {{
            display: inline-block;
            background: {TP_COLORS["yellow_accent"]};
            color: {TP_COLORS["gray_dark"]};
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.24rem 0.6rem;
            border-radius: 999px;
            margin-bottom: 0.75rem;
        }}

        .title {{
            color: {TP_COLORS["blue_primary"]};
            font-size: 2rem;
            font-weight: 760;
            margin-bottom: 0.15rem;
        }}

        .subtitle {{
            color: {TP_COLORS["gray_dark"]};
            font-size: 1.02rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }}

        .note {{
            color: {TP_COLORS["gray_text"]};
            font-size: 0.96rem;
            line-height: 1.7;
        }}

        .embed-card {{
            background: {TP_COLORS["gray_card"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 18px;
            padding: 0.8rem;
            box-shadow: 0 6px 18px rgba(31, 41, 55, 0.05);
        }}

        .status-card {{
            background: {TP_COLORS["white"]};
            border: 1px solid {TP_COLORS["gray_muted"]};
            border-radius: 14px;
            padding: 0.9rem 1rem;
            margin-top: 0.8rem;
            color: {TP_COLORS["gray_text"]};
            line-height: 1.6;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
        <div class="tag">PRESENTACIÓN EJECUTIVA</div>
        <div class="title">Resumen visual del proyecto</div>
        <div class="subtitle">Versión descargable en PPTX y PDF</div>
        <div class="note">
            Esta sección reúne la presentación ejecutiva del reto con una narrativa breve de Q1 a Q7.
            Se entrega en formato PowerPoint y PDF para facilitar revisión, descarga y exposición.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    if pdf_path and pdf_path.exists():
        st.download_button(
            label="Descargar PDF",
            data=pdf_path.read_bytes(),
            file_name=pdf_path.name,
            mime="application/pdf",
            width="stretch",
        )
    else:
        st.button("PDF no disponible", disabled=True, width="stretch")

with col2:
    if pptx_path and pptx_path.exists():
        st.download_button(
            label="Descargar PPTX",
            data=pptx_path.read_bytes(),
            file_name=pptx_path.name,
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            width="stretch",
        )
    else:
        st.button("PPTX no disponible", disabled=True, width="stretch")

status_lines = []
status_lines.append(f"PDF: {'✅ encontrado' if pdf_path else '⚠️ no encontrado'}")
status_lines.append(f"PPTX: {'✅ encontrado' if pptx_path else '⚠️ no encontrado'}")

if pdf_path:
    status_lines.append(f"Ruta PDF: `{pdf_path}`")
if pptx_path:
    status_lines.append(f"Ruta PPTX: `{pptx_path}`")

st.markdown(
    "<div class='status-card'>" + "<br>".join(status_lines) + "</div>",
    unsafe_allow_html=True,
)

if pdf_path and pdf_path.exists():
    pdf_bytes = pdf_path.read_bytes()
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    st.markdown("<div class='embed-card'>", unsafe_allow_html=True)
    st.components.v1.html(
        f"""
        <iframe
            src="data:application/pdf;base64,{b64_pdf}"
            width="100%"
            height="920"
            style="border:none; border-radius:12px; background:white;">
        </iframe>
        """,
        height=940,
        scrolling=False,
    )
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning(
        "No se encontró el PDF de la presentación. "
        "Ubícalo en `outputs/reports/` o conserva el archivo en `/mnt/data` durante la prueba."
    )

# with st.expander("Notas de uso"):
#     st.markdown(
#         "- El PDF se muestra embebido para lectura directa dentro de la app.\n"
#         "- El PPTX se mantiene como versión editable para exposición o ajustes finales.\n"
#         "- Para uso estable en tu repo, guarda ambos archivos en `outputs/reports/`.\n"
#         "- Nombres esperados:\n"
#         "  - `commercial_analytics_executive_presentation.pdf`\n"
#         "  - `commercial_analytics_executive_presentation.pptx`"
#     )