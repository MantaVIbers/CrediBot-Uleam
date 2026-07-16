"""Simulador visual del flujo conversacional de CrediBot."""
from datetime import datetime
from html import escape
import secrets

import streamlit as st

from components.auth import require_auth
from components.navigation import render_sidebar
from services.supabase_dashboard import (
    DashboardConfigError,
    obtener_estado_backend,
    simular_mensaje,
)
from styles import apply_dashboard_styles


def _new_demo_phone() -> str:
    """Genera un identificador telefónico numérico aislado para una nueva prueba."""
    return f"59399{secrets.randbelow(100_000_000):08d}"


def _render_history(messages: list[dict[str, str]]) -> str:
    if not messages:
        body = (
            '<div class="cb-chat-empty"><strong>Inicia una conversación</strong><br>'
            'Escribe “Hola” para abrir el menú de CrediBot.</div>'
        )
    else:
        rows: list[str] = []
        for item in messages:
            is_user = item["role"] == "user"
            row_class = "cb-message-out" if is_user else "cb-message-in"
            bubble_class = "cb-bubble-out" if is_user else "cb-bubble-in"
            author = "Tú" if is_user else "CrediBot"
            content = escape(item["content"])
            timestamp = escape(item["time"])
            rows.append(
                f'<div class="cb-message-row {row_class}">'
                f'<div class="cb-bubble {bubble_class}">'
                f'<div class="cb-message-author">{author}</div>'
                f'{content}<div class="cb-message-time">{timestamp}</div>'
                '</div></div>'
            )
        body = "".join(rows)

    return (
        '<div class="cb-simulator-shell">'
        '<div class="cb-sim-header">'
        '<div class="cb-avatar">$</div><div>'
        '<div class="cb-sim-name">CrediBot</div>'
        '<div class="cb-sim-status">en línea · simulación segura</div>'
        '</div></div>'
        '<div class="cb-sim-window">'
        '<div class="cb-date-chip">HOY</div>'
        f'{body}</div></div>'
    )


st.set_page_config(
    page_title="Simulador - CrediBot",
    page_icon="💬",
    layout="wide",
)

apply_dashboard_styles()
require_auth()
render_sidebar()

if "sim_phone" not in st.session_state:
    st.session_state["sim_phone"] = _new_demo_phone()
if "sim_messages" not in st.session_state:
    st.session_state["sim_messages"] = []

st.markdown(
    """
    <div class="cb-hero">
      <div class="cb-eyebrow">Laboratorio conversacional</div>
      <div class="cb-hero-title">Simulador de chat</div>
      <p class="cb-hero-subtitle">
        Prueba la conversación completa contra el backend real, sin consumir créditos
        de Twilio, Meta o Kapso.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

backend = obtener_estado_backend()
status_col, phone_col, action_col = st.columns([1.15, 2.3, 1.15], vertical_alignment="bottom")
with status_col:
    if backend["online"]:
        st.success("Backend conectado")
    else:
        st.error("Backend sin conexión")
with phone_col:
    st.text_input(
        "Identificador de prueba",
        key="sim_phone",
        help="Cada identificador conserva su propio estado en Supabase.",
    )
with action_col:
    if st.button("Nueva conversación", width="stretch"):
        st.session_state["sim_phone"] = _new_demo_phone()
        st.session_state["sim_messages"] = []
        st.session_state.pop("sim_error", None)
        st.rerun()

st.markdown(_render_history(st.session_state["sim_messages"]), unsafe_allow_html=True)

if st.session_state.get("sim_error"):
    st.error(st.session_state.pop("sim_error"))

with st.form("simulator_message_form", clear_on_submit=True, border=False):
    input_col, send_col = st.columns([5.4, 1], vertical_alignment="bottom")
    with input_col:
        message = st.text_input(
            "Mensaje",
            placeholder="Escribe un mensaje…",
            label_visibility="collapsed",
        )
    with send_col:
        submitted = st.form_submit_button(
            "Enviar",
            type="primary",
            width="stretch",
        )

if submitted and message.strip():
    now = datetime.now().strftime("%H:%M")
    st.session_state["sim_messages"].append(
        {"role": "user", "content": message.strip(), "time": now}
    )
    try:
        reply = simular_mensaje(st.session_state["sim_phone"], message)
    except DashboardConfigError as exc:
        st.session_state["sim_error"] = str(exc)
    else:
        st.session_state["sim_messages"].append(
            {
                "role": "assistant",
                "content": reply,
                "time": datetime.now().strftime("%H:%M"),
            }
        )
    st.rerun()

st.caption(f"Conectado a: {backend['url']}")
