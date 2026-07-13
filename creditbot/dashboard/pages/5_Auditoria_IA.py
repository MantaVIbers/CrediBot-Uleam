"""Página del dashboard con auditoría de tools IA (tool_audit_logs)."""
import json

import pandas as pd
import streamlit as st

from components.auth import require_auth
from services.supabase_dashboard import DashboardConfigError, obtener_auditoria_tools


st.set_page_config(
    page_title="Auditoria IA - CrediBot",
    page_icon="CB",
    layout="wide",
)

require_auth()

st.title("Auditoria IA / Tools")
st.caption(
    "Registro documentado de invocaciones: precalificacion, normalizacion de entrada, "
    "consultas RAG y agente OpenAI."
)

try:
    registros = obtener_auditoria_tools(limit=200)
except DashboardConfigError as exc:
    st.warning(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"No se pudo consultar Supabase: {exc}")
    st.stop()

if not registros:
    st.info(
        "No hay registros aun. Usa el bot (precalificacion o modo informacion) "
        "y vuelve a cargar esta pagina."
    )
    st.stop()

df = pd.DataFrame(registros)

if "tool_name" in df.columns:
    tools = ["Todos"] + sorted(df["tool_name"].dropna().unique().tolist())
    tool_filter = st.selectbox("Tool", tools)
    if tool_filter != "Todos":
        df = df[df["tool_name"] == tool_filter]

if "success" in df.columns:
    ok_filter = st.selectbox("Resultado", ["Todos", "Exitosos", "Fallidos"])
    if ok_filter == "Exitosos":
        df = df[df["success"] == True]  # noqa: E712
    elif ok_filter == "Fallidos":
        df = df[df["success"] == False]  # noqa: E712

col1, col2, col3 = st.columns(3)
col1.metric("Registros", len(df))
if "latency_ms" in df.columns and not df.empty:
    col2.metric("Latencia promedio (ms)", int(df["latency_ms"].fillna(0).mean()))
if "tool_name" in df.columns and not df.empty:
    col3.metric("Tools distintas", df["tool_name"].nunique())

preferred_columns = [
    "id",
    "tool_name",
    "success",
    "latency_ms",
    "conversation_id",
    "input_payload",
    "output_payload",
    "created_at",
]
visible = [c for c in preferred_columns if c in df.columns]
display = df[visible].copy()

for col in ("input_payload", "output_payload"):
    if col in display.columns:
        display[col] = display[col].apply(
            lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
        )

st.dataframe(display, use_container_width=True, hide_index=True)

csv = display.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Descargar CSV",
    data=csv,
    file_name="auditoria_tools_creditbot.csv",
    mime="text/csv",
)
