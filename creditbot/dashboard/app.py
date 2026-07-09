import streamlit as st

from services.supabase_dashboard import DashboardConfigError, probar_conexion


st.set_page_config(
    page_title="CrediBot Dashboard",
    page_icon="CB",
    layout="wide",
)

st.title("Panel Administrativo CrediBot")
st.caption("Modulo inicial del dashboard administrativo.")

st.info(
    "El panel esta listo para conectar metricas, solicitudes, casos derivados y usuarios."
)

st.subheader("Conexion a Supabase")

try:
    probar_conexion()
    st.success("Conexion con Supabase disponible.")
except DashboardConfigError as exc:
    st.warning(str(exc))
except Exception as exc:
    st.error(f"No se pudo consultar Supabase: {exc}")
