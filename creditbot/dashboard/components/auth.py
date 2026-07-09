import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _get_admin_password() -> str:
    return os.getenv("ADMIN_DASHBOARD_PASSWORD", "").strip()


def _logout() -> None:
    st.session_state["dashboard_authenticated"] = False
    st.rerun()


def require_auth() -> None:
    if "dashboard_authenticated" not in st.session_state:
        st.session_state["dashboard_authenticated"] = False

    if st.session_state["dashboard_authenticated"]:
        with st.sidebar:
            st.button("Cerrar sesion", on_click=_logout)
        return

    expected_password = _get_admin_password()
    st.title("Acceso administrativo")

    if not expected_password:
        st.warning("Configura ADMIN_DASHBOARD_PASSWORD en creditbot/.env.")
        st.stop()

    with st.form("admin_login_form"):
        password = st.text_input("Contrasena", type="password")
        submitted = st.form_submit_button("Ingresar")

    if submitted:
        if password == expected_password:
            st.session_state["dashboard_authenticated"] = True
            st.rerun()
        else:
            st.error("Contrasena incorrecta.")

    st.stop()

