import pandas as pd
import streamlit as st

from components.auth import require_auth
from services.supabase_dashboard import (
    DashboardConfigError,
    obtener_casos_derivados,
    obtener_solicitudes,
)


st.set_page_config(
    page_title="Solicitudes - CrediBot",
    page_icon="CB",
    layout="wide",
)

require_auth()

st.title("Solicitudes de Credito")

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

derived_request_ids: set[str] = set()
if not df_casos.empty and "credit_request_id" in df_casos.columns:
    derived_request_ids = set(df_casos["credit_request_id"].dropna().astype(str))

if "id" in df.columns:
    df["derivado_asesor"] = df["id"].astype(str).isin(derived_request_ids)
else:
    df["derivado_asesor"] = False

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

st.metric("Solicitudes mostradas", len(filtered_df))

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

st.dataframe(display_df, use_container_width=True, hide_index=True)

csv = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Descargar CSV",
    data=csv,
    file_name="solicitudes_creditbot.csv",
    mime="text/csv",
)
