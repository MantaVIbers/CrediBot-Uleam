"""Seguimiento de todas las conversaciones de CrediBot."""
from html import escape

import pandas as pd
import streamlit as st

from components.auth import require_auth
from components.navigation import render_sidebar
from components.presentation import format_datetime, format_money, safe_value
from components.ui import render_empty_state, render_page_header
from services.supabase_dashboard import (
    DashboardConfigError,
    obtener_casos_de_conversaciones,
    obtener_conversaciones,
    obtener_mensajes_conversacion,
    obtener_solicitudes,
    obtener_usuarios,
)
from styles import apply_dashboard_styles


def _index_by(rows: list[dict], key: str) -> dict[str, dict]:
    return {str(row.get(key)): row for row in rows if row.get(key)}


def _bubble(message: dict) -> str:
    outbound = message.get("direction") == "outbound"
    source = (message.get("raw_payload") or {}).get("source")
    author = "Cliente" if not outbound else ("Asesor" if source == "dashboard_human" else "CrediBot")
    row_class = "cb-message-out" if outbound else "cb-message-in"
    bubble_class = "cb-bubble-out" if outbound else "cb-bubble-in"
    return (
        f'<div class="cb-message-row {row_class}"><div class="cb-bubble {bubble_class}">'
        f'<div class="cb-message-author">{escape(author)}</div>'
        f'<div>{escape(str(message.get("content") or ""))}</div>'
        f'<div class="cb-message-time">{escape(format_datetime(message.get("created_at")))}</div>'
        "</div></div>"
    )


st.set_page_config(page_title="Conversaciones - CrediBot", page_icon="CB", layout="wide")
apply_dashboard_styles()
require_auth()
render_sidebar()
render_page_header(
    "Seguimiento de conversaciones",
    "Conversaciones",
    "Consulta el historial, estado del flujo y contexto de cada atención.",
)

try:
    conversations = obtener_conversaciones()
    users = _index_by(obtener_usuarios(), "id")
    requests = _index_by(obtener_solicitudes(), "conversation_id")
    cases = _index_by(obtener_casos_de_conversaciones(), "conversation_id")
except DashboardConfigError as exc:
    st.warning(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"No se pudo consultar las conversaciones: {exc}")
    st.stop()

if not conversations:
    render_empty_state("Aún no hay conversaciones registradas.")
    st.stop()

rows = []
for conversation in conversations:
    user = users.get(str(conversation.get("user_id")), {})
    case = cases.get(str(conversation.get("id")), {})
    rows.append(
        {
            **conversation,
            "cliente": safe_value(user.get("full_name"), safe_value(user.get("phone"), "Cliente")),
            "telefono": safe_value(user.get("phone"), "Sin teléfono"),
            "caso_estado": safe_value(case.get("status"), "—"),
            "caso_motivo": safe_value(case.get("reason"), "—"),
        }
    )

df = pd.DataFrame(rows)
metrics = st.columns(3)
metrics[0].metric("Conversaciones", len(df))
metrics[1].metric("Activas", int(df["is_active"].fillna(False).sum()))
metrics[2].metric("Con derivación", int((df["caso_estado"] != "—").sum()))

query = st.text_input("Buscar", placeholder="Nombre, teléfono, estado o motivo")
if query.strip():
    needle = query.strip().lower()
    mask = pd.Series(False, index=df.index)
    for column in ("cliente", "telefono", "current_state", "caso_estado", "caso_motivo"):
        mask = mask | df[column].fillna("").astype(str).str.lower().str.contains(needle, na=False)
    df = df[mask]

if df.empty:
    st.info("No hay conversaciones que coincidan con la búsqueda.")
    st.stop()

options = {
    f"{row.cliente} · {row.telefono} · {row.current_state}": str(row.id)
    for row in df.itertuples()
}
label = st.selectbox("Seleccionar conversación", list(options))
conversation_id = options[label]
selected = next(row for row in rows if str(row["id"]) == conversation_id)
request = requests.get(conversation_id, {})
case = cases.get(conversation_id, {})

left, right = st.columns([1.7, 0.9], gap="large")
with left:
    st.subheader("Historial")
    try:
        messages = obtener_mensajes_conversacion(conversation_id)
    except Exception as exc:
        st.error(f"No se pudo cargar el historial: {exc}")
        messages = []
    if messages:
        st.markdown(
            f'<div class="cb-chat-window">{"".join(_bubble(message) for message in messages)}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("No hay mensajes guardados para esta conversación.")

with right:
    st.subheader("Estado y contexto")
    st.write(f"**Cliente:** {selected['cliente']}")
    st.write(f"**Teléfono:** {selected['telefono']}")
    st.write(f"**Estado actual:** {safe_value(selected.get('current_state'))}")
    st.write(f"**Activa:** {'Sí' if selected.get('is_active') else 'No'}")
    st.write(f"**Última actualización:** {format_datetime(selected.get('updated_at'))}")
    st.divider()
    st.write(f"**Derivación:** {safe_value(case.get('status'), 'Sin derivación')}")
    if case:
        st.write(f"**Motivo:** {safe_value(case.get('reason'))}")
        st.write(f"**Resumen:** {safe_value(case.get('handoff_summary'), 'Sin resumen')}")
    st.divider()
    st.write("**Solicitud de crédito**")
    if request:
        st.write(f"Monto: {format_money(request.get('requested_amount'), 'No registrado')}")
        st.write(f"Plazo: {safe_value(request.get('term_months'), 'No registrado')} meses")
        st.write(f"Ingreso: {format_money(request.get('monthly_income'), 'No registrado')}")
        st.write(f"Resultado: {safe_value(request.get('result'), 'Pendiente')}")
    else:
        st.caption("No hay solicitud asociada.")
