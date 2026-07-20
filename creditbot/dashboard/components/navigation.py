"""Navegación e identidad visual del panel administrativo."""
import streamlit as st

from services.supabase_dashboard import obtener_contadores_navegacion


def _safe_navigation_counts() -> dict[str, int]:
    try:
        return obtener_contadores_navegacion()
    except Exception:
        return {}


def render_sidebar(counts: dict[str, int] | None = None) -> None:
    """Dibuja la marca y el menú común de todas las pantallas."""
    navigation_counts = counts if counts is not None else _safe_navigation_counts()
    requests_label = "Solicitudes"
    cases_label = "Casos derivados"
    if "solicitudes" in navigation_counts:
        requests_label += f" · {navigation_counts['solicitudes']}"
    if "casos_pendientes" in navigation_counts:
        cases_label += f" · {navigation_counts['casos_pendientes']}"

    with st.sidebar:
        st.markdown(
            """
            <div class="cb-brand">
              <div class="cb-brand-mark">$</div>
              <div>
                <div class="cb-brand-name">CrediBot</div>
                <div class="cb-brand-tagline">CRÉDITOS CONVERSACIONALES</div>
              </div>
            </div>
            <div class="cb-nav-label">NAVEGACIÓN</div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link("app.py", label="Panel general", icon="🏠")
        st.page_link("pages/1_Simulador.py", label="Simulador de chat", icon="💬")
        st.page_link("pages/2_Solicitudes.py", label=requests_label, icon="📄")
        st.page_link("pages/3_Casos_Derivados.py", label=cases_label, icon="🎧")
        st.page_link("pages/4_Usuarios.py", label="Usuarios", icon="👥")
        st.page_link("pages/5_Auditoria_IA.py", label="Auditoría IA", icon="🛡️")
        st.page_link("pages/6_Conversaciones.py", label="Conversaciones", icon="💬")
        st.markdown(
            """
            <div class="cb-sidebar-footer">
              <span class="cb-sidebar-live"></span>Sistema operativo<br>
              Entorno académico · ULEAM
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Cerrar sesión", width="stretch"):
            st.session_state["dashboard_authenticated"] = False
            st.rerun()
