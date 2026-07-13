"""Bandeja de atención humana para casos derivados."""
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from components.auth import require_auth
from services.supabase_dashboard import (
    DashboardConfigError,
    cerrar_caso_derivado,
    enviar_respuesta_humana,
    obtener_casos_derivados,
    obtener_estado_configuracion,
    obtener_mensajes_conversacion,
    obtener_solicitudes,
    obtener_usuarios,
)
from styles import apply_dashboard_styles


def _safe_value(value: object, default: str = "No registrado") -> str:
    """Retorna un texto seguro para mostrar en UI."""
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def _money_text(value: object) -> str:
    """Formatea un valor monetario."""
    if value is None or pd.isna(value):
        return "No registrado"
    return f"${float(value):,.2f}"


def _term_text(value: object) -> str:
    """Formatea un plazo en meses."""
    if value is None or pd.isna(value):
        return "No registrado"
    return f"{int(value)} meses"


def _reason_text(reason: object) -> str:
    """Traduce motivos técnicos a texto de operación."""
    labels = {
        "user_requested_advisor": "Solicitó asesor",
        "menu_option_3": "Eligió hablar con asesor",
        "observed_result": "Resultado observado",
        "repeated_invalid_input": "Fallos de validación",
    }
    return labels.get(str(reason), _safe_value(reason))


def _format_datetime(value: object) -> str:
    """Devuelve fecha corta para listas y burbujas."""
    if value is None or pd.isna(value):
        return ""
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return str(value)
    return parsed.strftime("%d/%m %H:%M")


def _short_text(value: object, limit: int = 92) -> str:
    """Acorta texto largo sin romper la lista de contactos."""
    text = _safe_value(value, "")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _raw_payload(value: object) -> dict[str, Any]:
    """Normaliza el payload crudo del mensaje."""
    return value if isinstance(value, dict) else {}


def _message_author(item: dict[str, Any]) -> str:
    """Identifica el autor visible del mensaje."""
    if item.get("direction") == "inbound":
        return "Cliente"
    raw_payload = _raw_payload(item.get("raw_payload"))
    if raw_payload.get("source") == "dashboard_human":
        return "Asesor"
    return "CrediBot"


def _message_html(item: dict[str, Any]) -> str:
    """Construye una burbuja de chat tipo WhatsApp."""
    direction = item.get("direction")
    outbound = direction == "outbound"
    row_class = "cb-message-out" if outbound else "cb-message-in"
    bubble_class = "cb-bubble-out" if outbound else "cb-bubble-in"
    content = escape(str(item.get("content") or ""))
    author = escape(_message_author(item))
    timestamp = escape(_format_datetime(item.get("created_at")))
    return f"""
    <div class="cb-message-row {row_class}">
      <div class="cb-bubble {bubble_class}">
        <div class="cb-message-author">{author}</div>
        <div>{content}</div>
        <div class="cb-message-time">{timestamp}</div>
      </div>
    </div>
    """


def _case_context(selected_case: pd.Series) -> dict[str, str]:
    """Extrae ids necesarios para responder el caso."""
    return {
        "case_id": _safe_value(selected_case.get("id"), ""),
        "conversation_id": _safe_value(selected_case.get("conversation_id"), ""),
        "user_id": _safe_value(selected_case.get("user_id"), ""),
        "phone": _safe_value(selected_case.get("usuario_phone"), ""),
    }


def _client_name(selected_case: pd.Series) -> str:
    """Nombre visible del contacto."""
    name = _safe_value(selected_case.get("usuario_full_name"), "")
    if name:
        return name
    phone = _safe_value(selected_case.get("usuario_phone"), "")
    return phone or "Cliente sin nombre"


def _status_class(status: object) -> str:
    """Devuelve clase visual para estado del caso."""
    if status == "assigned":
        return "cb-pill-green"
    if status == "pending":
        return "cb-pill-yellow"
    return "cb-pill-red"


def _render_contact_card(case: pd.Series, active: bool) -> None:
    """Renderiza una tarjeta compacta de contacto."""
    name = escape(_client_name(case))
    phone = escape(_safe_value(case.get("usuario_phone")))
    reason = escape(_reason_text(case.get("reason")))
    status = escape(_safe_value(case.get("status"), "pending"))
    created_at = escape(_format_datetime(case.get("created_at")))
    summary = escape(_short_text(case.get("handoff_summary"), 88))
    active_class = "cb-contact-active" if active else ""
    pill_class = _status_class(case.get("status"))

    st.markdown(
        f"""
        <div class="cb-contact {active_class}">
          <div class="cb-contact-name">{name}</div>
          <div class="cb-contact-meta">{phone}</div>
          <div style="margin:8px 0 6px;">
            <span class="cb-pill {pill_class}">{status}</span>
            <span class="cb-pill">{reason}</span>
          </div>
          <div class="cb-contact-meta">{summary}</div>
          <div class="cb-contact-meta" style="margin-top:6px;">{created_at}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _load_messages(conversation_id: str) -> list[dict[str, Any]]:
    """Carga mensajes de una conversación."""
    if not conversation_id:
        return []
    return obtener_mensajes_conversacion(conversation_id)


def _render_chat_messages(selected_case: pd.Series) -> None:
    """Renderiza el panel central con mensajes actualizables."""
    conversation_id = _safe_value(selected_case.get("conversation_id"), "")
    if not conversation_id:
        st.warning("Este caso no tiene conversación asociada.")
        return

    try:
        messages = _load_messages(conversation_id)
    except Exception as exc:
        st.error(f"No se pudo cargar el chat: {exc}")
        return

    if not messages:
        st.markdown(
            """
            <div class="cb-chat-window">
              <div class="cb-muted">Todavía no hay mensajes guardados para esta conversación.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    messages_html = "\n".join(_message_html(item) for item in messages)
    st.markdown(
        f"""
        <div class="cb-chat-window">
          {messages_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_reply_form(selected_case: pd.Series) -> None:
    """Formulario estable para responder al cliente."""
    context = _case_context(selected_case)
    if not context["conversation_id"] or not context["user_id"]:
        st.warning("El caso no tiene conversación o usuario asociado.")
        return

    st.markdown('<div class="cb-chat-compose">', unsafe_allow_html=True)
    with st.form(f"human_reply_form_{context['case_id']}", clear_on_submit=True):
        reply = st.text_area(
            "Mensaje al cliente",
            placeholder="Escribe como asesor y envía por WhatsApp...",
            height=92,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Enviar por WhatsApp", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        try:
            enviar_respuesta_humana(
                case_id=context["case_id"],
                conversation_id=context["conversation_id"],
                user_id=context["user_id"],
                phone=context["phone"],
                content=reply,
            )
        except DashboardConfigError as exc:
            st.warning(str(exc))
        except Exception as exc:
            st.error(f"No se pudo enviar la respuesta: {exc}")
        else:
            st.success("Respuesta enviada por WhatsApp.")
            st.rerun()


def _render_detail_item(label: str, value: str) -> None:
    """Muestra un dato en la ficha derecha."""
    st.markdown(
        f"""
        <div class="cb-detail-item">
          <div class="cb-detail-label">{escape(label)}</div>
          <div class="cb-detail-value">{escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_config_status() -> None:
    """Muestra si Twilio/Supabase están listos para responder."""
    config = obtener_estado_configuracion()
    if config["can_reply"]:
        mode = "Twilio directo" if config["reply_mode"] == "twilio_direct" else "Backend API"
        st.success(f"Listo para responder por WhatsApp ({mode}).")
        return

    missing: list[str] = []
    if not config["supabase"]:
        missing.append("Supabase (SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY)")
    if not config["twilio"]:
        missing.append(
            "Twilio en el panel (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM)"
        )
    if not config["backend_api"]:
        missing.append(
            "o backend con Twilio (BACKEND_API_URL + ADMIN_DASHBOARD_PASSWORD en Render)"
        )
    st.warning(
        "Aún no puedes enviar WhatsApp desde el panel. Configura: "
        + "; ".join(missing)
    )


def _merge_case_data(
    casos: list[dict[str, Any]],
    solicitudes: list[dict[str, Any]],
    usuarios: list[dict[str, Any]],
) -> pd.DataFrame:
    """Une casos con usuarios y solicitudes para la bandeja."""
    df = pd.DataFrame(casos)
    if df.empty:
        return df

    df_solicitudes = pd.DataFrame(solicitudes)
    df_usuarios = pd.DataFrame(usuarios)

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

    return df


st.set_page_config(
    page_title="Atención Humana - CrediBot",
    page_icon="CB",
    layout="wide",
)

require_auth()
apply_dashboard_styles()

st.markdown(
    """
    <div class="cb-hero">
      <div class="cb-hero-title">Atención Humana</div>
      <p class="cb-hero-subtitle">
        Bandeja tipo WhatsApp para revisar contactos derivados y responder en vivo
        con Twilio desde este panel.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

_render_config_status()

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

df = _merge_case_data(casos_derivados, solicitudes, usuarios)

if df.empty:
    st.success("No existen casos derivados abiertos.")
    st.stop()

pending_count = int((df["status"] == "pending").sum()) if "status" in df else 0
assigned_count = int((df["status"] == "assigned").sum()) if "status" in df else 0
observed_count = int((df["reason"] == "observed_result").sum()) if "reason" in df else 0

metrics = st.columns(4)
metrics[0].metric("Conversaciones abiertas", len(df))
metrics[1].metric("Pendientes", pending_count)
metrics[2].metric("En atención", assigned_count)
metrics[3].metric("Observados", observed_count)

if "selected_handoff_case_id" not in st.session_state:
    st.session_state["selected_handoff_case_id"] = str(df.iloc[0]["id"])

left_col, chat_col, detail_col = st.columns([0.9, 1.55, 0.85], gap="medium")

with left_col:
    st.markdown('<div class="cb-section-title">Contactos</div>', unsafe_allow_html=True)
    search = st.text_input("Buscar contacto", placeholder="Nombre, teléfono o motivo")
    status_filter = st.segmented_control(
        "Estado",
        options=["Todos", "Pendientes", "En atención"],
        default="Todos",
    )

    filtered = df.copy()
    if search.strip():
        query = search.strip().lower()
        name = filtered.get("usuario_full_name", pd.Series("", index=filtered.index))
        phone = filtered.get("usuario_phone", pd.Series("", index=filtered.index))
        reason = filtered.get("reason", pd.Series("", index=filtered.index))
        summary = filtered.get("handoff_summary", pd.Series("", index=filtered.index))
        mask = name.fillna("").astype(str).str.lower().str.contains(query, na=False)
        mask = mask | phone.fillna("").astype(str).str.lower().str.contains(query, na=False)
        mask = mask | reason.fillna("").astype(str).str.lower().str.contains(query, na=False)
        mask = mask | summary.fillna("").astype(str).str.lower().str.contains(query, na=False)
        filtered = filtered[mask]

    if status_filter == "Pendientes" and "status" in filtered:
        filtered = filtered[filtered["status"] == "pending"]
    elif status_filter == "En atención" and "status" in filtered:
        filtered = filtered[filtered["status"] == "assigned"]

    if filtered.empty:
        st.info("No hay contactos con esos filtros.")
    else:
        labels = {
            str(row["id"]): f"{_client_name(row)} · {_safe_value(row.get('usuario_phone'))}"
            for _, row in filtered.iterrows()
        }
        options = list(labels.keys())
        current = st.session_state.get("selected_handoff_case_id")
        if current not in options:
            current = options[0]
        picked = st.selectbox(
            "Seleccionar por nombre o teléfono",
            options=options,
            format_func=lambda case_id: labels.get(case_id, case_id),
            index=options.index(current),
        )
        if picked != st.session_state["selected_handoff_case_id"]:
            st.session_state["selected_handoff_case_id"] = picked
            st.rerun()

        for _, case in filtered.iterrows():
            case_id = str(case["id"])
            active = case_id == st.session_state["selected_handoff_case_id"]
            _render_contact_card(case, active)
            if st.button("Abrir chat", key=f"open_{case_id}", use_container_width=True):
                st.session_state["selected_handoff_case_id"] = case_id
                st.rerun()

selected_id = st.session_state["selected_handoff_case_id"]
if selected_id not in set(df["id"].astype(str)):
    selected_id = str(df.iloc[0]["id"])
    st.session_state["selected_handoff_case_id"] = selected_id

selected_case = df[df["id"].astype(str) == selected_id].iloc[0]
client_name = _client_name(selected_case)
phone = _safe_value(selected_case.get("usuario_phone"))
status = _safe_value(selected_case.get("status"), "pending")
reason = _reason_text(selected_case.get("reason"))

with chat_col:
    st.markdown(
        f"""
        <div class="cb-chat-header">
          <div>
            <p class="cb-chat-name">{escape(client_name)}</p>
            <p class="cb-chat-phone">{escape(phone)} · {escape(reason)}</p>
          </div>
          <span class="cb-pill {_status_class(status)}">{escape(status)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    auto_refresh = st.toggle("Actualizar en vivo", value=True)
    if auto_refresh and hasattr(st, "fragment"):

        @st.fragment(run_every="5s")
        def _live_chat_fragment() -> None:
            _render_chat_messages(selected_case)

        _live_chat_fragment()
    else:
        if st.button("Actualizar conversación", use_container_width=True):
            st.rerun()
        _render_chat_messages(selected_case)

    _render_reply_form(selected_case)

with detail_col:
    st.markdown('<div class="cb-section-title">Ficha del caso</div>', unsafe_allow_html=True)
    st.markdown('<div class="cb-panel"><div class="cb-panel-pad">', unsafe_allow_html=True)
    _render_detail_item("Cliente", client_name)
    _render_detail_item("Teléfono", phone)
    _render_detail_item("Motivo", reason)
    _render_detail_item("Estado", status)
    _render_detail_item("Creado", _format_datetime(selected_case.get("created_at")))
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('<div class="cb-section-title">Solicitud</div>', unsafe_allow_html=True)
    st.markdown('<div class="cb-panel"><div class="cb-panel-pad">', unsafe_allow_html=True)
    _render_detail_item(
        "Monto solicitado",
        _money_text(selected_case.get("solicitud_requested_amount")),
    )
    _render_detail_item("Plazo", _term_text(selected_case.get("solicitud_term_months")))
    _render_detail_item(
        "Ingreso mensual",
        _money_text(selected_case.get("solicitud_monthly_income")),
    )
    _render_detail_item("Resultado", _safe_value(selected_case.get("solicitud_result")))
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown('<div class="cb-section-title">Resumen</div>', unsafe_allow_html=True)
    st.info(_safe_value(selected_case.get("handoff_summary"), "Sin resumen guardado."))

    st.markdown('<div class="cb-section-title">Gestión</div>', unsafe_allow_html=True)
    if st.button("Cerrar caso", type="primary", use_container_width=True):
        try:
            cerrar_caso_derivado(selected_id)
        except Exception as exc:
            st.error(f"No se pudo cerrar el caso: {exc}")
        else:
            st.success("Caso cerrado correctamente.")
            st.session_state.pop("selected_handoff_case_id", None)
            st.rerun()
