"""Componente de autenticación para el dashboard de Streamlit."""
import os
import hmac
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _get_admin_password() -> str:
    """Lee la contraseña desde .env local o secretos de Streamlit Cloud."""
    env_value = os.getenv("ADMIN_DASHBOARD_PASSWORD", "").strip()
    if env_value:
        return env_value

    try:
        return str(st.secrets.get("ADMIN_DASHBOARD_PASSWORD", "")).strip()
    except Exception:
        return ""


def require_auth() -> None:
    """Verifica que el usuario esté autenticado; si no, muestra el formulario de login."""
    if "dashboard_authenticated" not in st.session_state:
        st.session_state["dashboard_authenticated"] = False

    if st.session_state["dashboard_authenticated"]:
        return

    expected_password = _get_admin_password()

    if not expected_password:
        st.warning("Configura ADMIN_DASHBOARD_PASSWORD en .env o en Secrets.")
        st.stop()

    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
        [data-testid="stAppViewContainer"] {
            margin-left: 0 !important;
            background: #ffffff !important;
        }
        .stApp { background: #ffffff !important; }
        .block-container {
            max-width: 460px !important;
            padding-top: 12vh !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <section class="cb-login-card">
          <div class="cb-login-mark">$</div>
          <div class="cb-login-eyebrow">CREDIBOT · ULEAM</div>
          <h1>Bienvenido de vuelta</h1>
          <p>
            Ingresa al panel para gestionar solicitudes, conversaciones y casos
            de atención humana.
          </p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    with st.form("admin_login_form", border=False):
        password = st.text_input(
            "Contraseña de acceso",
            type="password",
            placeholder="Escribe tu contraseña",
        )
        submitted = st.form_submit_button(
            "Ingresar al panel", type="primary", width="stretch"
        )

    if submitted:
        if hmac.compare_digest(password, expected_password):
            st.session_state["dashboard_authenticated"] = True
            st.rerun()
        else:
            st.error("La contraseña no es correcta. Inténtalo nuevamente.")

    st.stop()
