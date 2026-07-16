"""Página del dashboard que lista y filtra solicitudes de crédito."""
import pandas as pd
import streamlit as st

from components.auth import require_auth
from components.navigation import render_sidebar
from services.supabase_dashboard import (
    DashboardConfigError,
    obtener_casos_derivados,
    obtener_solicitudes,
)
from styles import apply_dashboard_styles


st.set_page_config(
    page_title="Solicitudes - CrediBot",
    page_icon="CB",
    layout="wide",
)

apply_dashboard_styles()
require_auth()
render_sidebar()

st.markdown(
    """
    <div class="cb-hero">
      <div class="cb-eyebrow">Gestión crediticia</div>
      <div class="cb-hero-title">Solicitudes de Crédito</div>
      <p class="cb-hero-subtitle">
        Seguimiento de precalificaciones, resultados y derivaciones al asesor.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    solicitudes = obtener_solicitudes()
    casos_derivados = obtener_casos_derivados()
except DashboardConfigError as exc:
    st.warning(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"No se pudo consultar Supabase: {exc}")
    st.stop()

df = pd.DataFrame(solicitudes)
df_casos = pd.DataFrame(casos_derivados)

if df.empty:
    st.info("No existen solicitudes registradas.")
    st.stop()

# Identifica qué solicitudes tienen un caso derivado asociado
derived_request_ids: set[str] = set()
if not df_casos.empty and "credit_request_id" in df_casos.columns:
    derived_request_ids = set(df_casos["credit_request_id"].dropna().astype(str))

if "id" in df.columns:
    df["derivado_asesor"] = df["id"].astype(str).isin(derived_request_ids)
else:
    df["derivado_asesor"] = False

st.markdown('<div class="cb-section-title">Filtros</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

resultado = col1.selectbox(
    "Resultado",
    ["Todos", "preaprobado", "observado", "no_cumple"],
)

derivacion = col2.selectbox(
    "Derivacion",
    ["Todos", "Derivados", "No derivados"],
)

filtered_df = df.copy()

if resultado != "Todos" and "result" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["result"] == resultado]

if derivacion == "Derivados":
    filtered_df = filtered_df[filtered_df["derivado_asesor"]]
elif derivacion == "No derivados":
    filtered_df = filtered_df[~filtered_df["derivado_asesor"]]

metric_cols = st.columns(4)
metric_cols[0].metric("Solicitudes mostradas", len(filtered_df))
metric_cols[1].metric(
    "Preaprobadas",
    int((filtered_df["result"] == "preaprobado").sum()) if "result" in filtered_df else 0,
)
metric_cols[2].metric(
    "Observadas",
    int((filtered_df["result"] == "observado").sum()) if "result" in filtered_df else 0,
)
metric_cols[3].metric(
    "Derivadas",
    int(filtered_df["derivado_asesor"].sum()) if "derivado_asesor" in filtered_df else 0,
)

preferred_columns = [
    "id",
    "user_id",
    "requested_amount",
    "term_months",
    "monthly_income",
    "estimated_payment",
    "payment_capacity",
    "result",
    "status",
    "derivado_asesor",
    "created_at",
    "updated_at",
]
visible_columns = [column for column in preferred_columns if column in filtered_df.columns]
extra_columns = [column for column in filtered_df.columns if column not in visible_columns]
display_df = filtered_df[visible_columns + extra_columns]

st.markdown('<div class="cb-section-title">Listado</div>', unsafe_allow_html=True)
st.dataframe(display_df, width="stretch", hide_index=True)

# Botón para descargar CSV
csv = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Descargar CSV",
    data=csv,
    file_name="solicitudes_creditbot.csv",
    mime="text/csv",
)
