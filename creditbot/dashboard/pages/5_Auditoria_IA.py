"""Trazabilidad de invocaciones de herramientas y decisiones automatizadas."""
import json

import pandas as pd
import streamlit as st

from components.auth import require_auth
from components.navigation import render_sidebar
from services.supabase_dashboard import DashboardConfigError, obtener_auditoria_ia
from styles import apply_dashboard_styles


st.set_page_config(
    page_title="Auditoría IA - CrediBot",
    page_icon="🛡️",
    layout="wide",
)

apply_dashboard_styles()
require_auth()
render_sidebar()

st.markdown(
    """
    <div class="cb-hero">
      <div class="cb-eyebrow">Control y trazabilidad</div>
      <div class="cb-hero-title">Auditoría IA</div>
      <p class="cb-hero-subtitle">
        Revisa las herramientas ejecutadas, su resultado y tiempo de respuesta sin
        exponer credenciales ni cédulas completas.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    logs = obtener_auditoria_ia()
except DashboardConfigError as exc:
    st.warning(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"No se pudo consultar la auditoría: {exc}")
    st.stop()

df = pd.DataFrame(logs)
if df.empty:
    st.info("Todavía no existen eventos de auditoría.")
    st.stop()

metric_cols = st.columns(4)
metric_cols[0].metric("Invocaciones", len(df))
metric_cols[1].metric(
    "Correctas",
    int(df["success"].fillna(False).sum()) if "success" in df else 0,
)
metric_cols[2].metric(
    "Con error",
    int((~df["success"].fillna(False)).sum()) if "success" in df else 0,
)
metric_cols[3].metric(
    "Latencia promedio",
    f"{df['latency_ms'].dropna().mean():.0f} ms"
    if "latency_ms" in df and not df["latency_ms"].dropna().empty
    else "—",
)

filter_left, filter_right = st.columns(2)
tools = sorted(df["tool_name"].dropna().astype(str).unique()) if "tool_name" in df else []
selected_tool = filter_left.selectbox("Herramienta", ["Todas", *tools])
selected_status = filter_right.selectbox("Resultado", ["Todos", "Correctos", "Con error"])

filtered = df.copy()
if selected_tool != "Todas":
    filtered = filtered[filtered["tool_name"] == selected_tool]
if selected_status == "Correctos":
    filtered = filtered[filtered["success"].fillna(False)]
elif selected_status == "Con error":
    filtered = filtered[~filtered["success"].fillna(False)]

for column in ("input_payload", "output_payload"):
    if column in filtered:
        filtered[column] = filtered[column].apply(
            lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value
        )

visible = [
    column
    for column in (
        "created_at",
        "tool_name",
        "success",
        "latency_ms",
        "conversation_id",
        "input_payload",
        "output_payload",
    )
    if column in filtered.columns
]
st.markdown('<div class="cb-section-title">Registro de actividad</div>', unsafe_allow_html=True)
st.dataframe(filtered[visible], width="stretch", hide_index=True)
