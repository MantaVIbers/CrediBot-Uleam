"""Página del dashboard para visualizar casos derivados a asesor humano."""
import pandas as pd
import streamlit as st

from components.auth import require_auth
from services.supabase_dashboard import (
    DashboardConfigError,
    obtener_casos_derivados,
    obtener_solicitudes,
    obtener_usuarios,
)


def _safe_value(value: object, default: str = "No registrado") -> object:
    """Retorna el valor o un texto por defecto si es nulo."""
    if value is None or pd.isna(value):
        return default
    return value


def _money_text(value: object) -> str:
    """Formatea un valor numérico como texto monetario."""
    if value is None or pd.isna(value):
        return "No registrado"
    return f"${float(value):.2f}"


def _term_text(value: object) -> str:
    """Formatea un número de meses como texto."""
    if value is None or pd.isna(value):
        return "No registrado"
    return f"{int(value)} meses"


st.set_page_config(
    page_title="Casos Derivados - CrediBot",
    page_icon="CB",
    layout="wide",
)

require_auth()

st.title("Casos Derivados")

try:
    casos_derivados = obtener_casos_derivados()
    solicitudes = obtener_solicitudes()
    usuarios = obtener_usuarios()
except DashboardConfigError as exc:
    st.warning(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"No se pudo consultar Supabase: {exc}")
    st.stop()

df_casos = pd.DataFrame(casos_derivados)
df_solicitudes = pd.DataFrame(solicitudes)
df_usuarios = pd.DataFrame(usuarios)

if df_casos.empty:
    st.success("No existen casos derivados pendientes.")
    st.stop()

df = df_casos.copy()

# Combina con datos de solicitudes y usuarios
if not df_solicitudes.empty and "credit_request_id" in df.columns:
    df = df.merge(
        df_solicitudes.add_prefix("solicitud_"),
        how="left",
        left_on="credit_request_id",
        right_on="solicitud_id",
    )

if not df_usuarios.empty and "user_id" in df.columns:
    df = df.merge(
        df_usuarios.add_prefix("usuario_"),
        how="left",
        left_on="user_id",
        right_on="usuario_id",
    )

preferred_columns = [
    "id",
    "status",
    "reason",
    "usuario_full_name",
    "usuario_phone",
    "solicitud_requested_amount",
    "solicitud_term_months",
    "solicitud_monthly_income",
    "solicitud_result",
    "created_at",
]
visible_columns = [column for column in preferred_columns if column in df.columns]

st.dataframe(df[visible_columns], use_container_width=True, hide_index=True)

case_ids = df["id"].astype(str).tolist()
selected_case_id = st.selectbox("Seleccionar caso", case_ids)
selected_case = df[df["id"].astype(str) == selected_case_id].iloc[0]

st.subheader("Detalle del caso")

col1, col2 = st.columns(2)

col1.write(f"**Cliente:** {_safe_value(selected_case.get('usuario_full_name'))}")
col1.write(f"**Telefono:** {_safe_value(selected_case.get('usuario_phone'))}")
col1.write(f"**Motivo:** {_safe_value(selected_case.get('reason'))}")
col1.write(f"**Estado:** {_safe_value(selected_case.get('status'))}")

col2.write(
    f"**Monto solicitado:** {_money_text(selected_case.get('solicitud_requested_amount'))}"
)
col2.write(f"**Plazo:** {_term_text(selected_case.get('solicitud_term_months'))}")
col2.write(
    f"**Ingreso mensual:** {_money_text(selected_case.get('solicitud_monthly_income'))}"
)
col2.write(f"**Resultado:** {_safe_value(selected_case.get('solicitud_result'))}")
