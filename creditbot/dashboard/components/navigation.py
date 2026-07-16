"""Navegación e identidad visual del panel administrativo."""
import streamlit as st


def _logout() -> None:
    st.session_state["dashboard_authenticated"] = False
    st.rerun()


def render_sidebar() -> None:
    """Dibuja la marca y el menú común de todas las pantallas."""
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
        st.page_link("pages/2_Solicitudes.py", label="Solicitudes", icon="📄")
        st.page_link("pages/3_Casos_Derivados.py", label="Casos derivados", icon="🎧")
        st.page_link("pages/4_Usuarios.py", label="Usuarios", icon="👥")
        st.page_link("pages/5_Auditoria_IA.py", label="Auditoría IA", icon="🛡️")
        st.markdown(
            """
            <div class="cb-sidebar-footer">
              <span class="cb-sidebar-live"></span>Sistema operativo<br>
              Entorno académico · ULEAM
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button("Cerrar sesión", on_click=_logout, width="stretch")
