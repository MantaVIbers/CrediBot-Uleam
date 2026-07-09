"""Página principal del panel de administración de CrediBot."""
import pandas as pd
import streamlit as st

from components.auth import require_auth
from services.supabase_dashboard import (
    DashboardConfigError,
    obtener_casos_derivados,
    obtener_solicitudes,
    obtener_usuarios,
)


st.set_page_config(
    page_title="CrediBot Dashboard",
    page_icon="CB",
    layout="wide",
)

require_auth()

st.title("Panel Administrativo CrediBot")
st.caption("Resumen general de usuarios, solicitudes y casos derivados.")

try:
    usuarios = obtener_usuarios()
    solicitudes = obtener_solicitudes()
    casos_derivados = obtener_casos_derivados()
except DashboardConfigError as exc:
    st.warning(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"No se pudo consultar Supabase: {exc}")
    st.stop()

df_usuarios = pd.DataFrame(usuarios)
df_solicitudes = pd.DataFrame(solicitudes)
df_casos_derivados = pd.DataFrame(casos_derivados)

total_usuarios = len(df_usuarios)
total_solicitudes = len(df_solicitudes)
total_casos_derivados = len(df_casos_derivados)

if df_solicitudes.empty or "result" not in df_solicitudes:
    preaprobadas = 0
    observadas = 0
    no_cumplen = 0
else:
    preaprobadas = int((df_solicitudes["result"] == "preaprobado").sum())
    observadas = int((df_solicitudes["result"] == "observado").sum())
    no_cumplen = int((df_solicitudes["result"] == "no_cumple").sum())

# Métricas principales
col1, col2, col3 = st.columns(3)
col1.metric("Usuarios registrados", total_usuarios)
col2.metric("Solicitudes totales", total_solicitudes)
col3.metric("Casos derivados", total_casos_derivados)

col4, col5, col6 = st.columns(3)
col4.metric("Preaprobadas", preaprobadas)
col5.metric("Observadas", observadas)
col6.metric("No cumplen", no_cumplen)

st.subheader("Solicitudes recientes")

if df_solicitudes.empty:
    st.info("No existen solicitudes registradas.")
else:
    visible_columns = [
        column
        for column in [
            "id",
            "user_id",
            "requested_amount",
            "term_months",
            "monthly_income",
            "estimated_payment",
            "payment_capacity",
            "result",
            "status",
            "created_at",
        ]
        if column in df_solicitudes.columns
    ]
    st.dataframe(
        df_solicitudes[visible_columns].head(10),
        use_container_width=True,
        hide_index=True,
    )
