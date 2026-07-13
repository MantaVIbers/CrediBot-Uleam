"""Página del dashboard para visualizar casos derivados a asesor humano."""
from typing import Any

import pandas as pd
import streamlit as st

from components.auth import require_auth
from services.supabase_dashboard import (
    DashboardConfigError,
    cerrar_caso_derivado,
    enviar_respuesta_humana,
    obtener_mensajes_conversacion,
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


def _reason_text(reason: object) -> str:
    """Traduce motivos técnicos a texto para el asesor."""
    labels = {
        "user_requested_advisor": "Cliente solicitó asesor",
        "menu_option_3": "Cliente eligió hablar con asesor",
        "observed_result": "Resultado observado",
        "repeated_invalid_input": "Fallos repetidos de validación",
    }
    return labels.get(str(reason), str(_safe_value(reason)))


def _raw_payload(value: object) -> dict[str, Any]:
    """Normaliza el payload crudo de un mensaje."""
    return value if isinstance(value, dict) else {}


def _message_author(item: dict[str, Any]) -> str:
    """Identifica si el mensaje saliente fue del bot o de un asesor."""
    direction = item.get("direction")
    if direction == "inbound":
        return "Cliente"

    raw_payload = _raw_payload(item.get("raw_payload"))
    if raw_payload.get("source") == "dashboard_human":
        return "Asesor"
    return "CrediBot"


def _render_live_chat(messages: list[dict[str, Any]]) -> None:
    """Muestra los mensajes guardados en Supabase como conversación."""
    if not messages:
        st.info("Todavía no hay mensajes guardados para esta conversación.")
        return

    for item in messages:
        direction = item.get("direction")
        author = _message_author(item)
        content = item.get("content") or ""
        timestamp = item.get("created_at") or ""
        avatar = "user" if direction == "inbound" else "assistant"
        with st.chat_message(avatar):
            st.markdown(f"**{author}**")
            st.write(content)
            if timestamp:
                st.caption(str(timestamp))


def _case_context(selected_case: pd.Series) -> dict[str, str]:
    """Extrae los identificadores necesarios para operar el caso."""
    return {
        "case_id": str(selected_case.get("id") or ""),
        "conversation_id": str(selected_case.get("conversation_id") or ""),
        "user_id": str(selected_case.get("user_id") or ""),
        "phone": str(_safe_value(selected_case.get("usuario_phone"), "") or ""),
    }


def _render_chat_messages(selected_case: pd.Series) -> None:
    """Renderiza solo el historial para permitir refresco periódico."""
    conversation_id = str(selected_case.get("conversation_id") or "")

    if not conversation_id:
        st.warning("El caso no tiene conversación asociada.")
        return

    try:
        messages = obtener_mensajes_conversacion(conversation_id)
    except Exception as exc:
        st.error(f"No se pudo cargar el chat: {exc}")
        return

    st.caption("El chat consulta Supabase periódicamente mientras esta página esté abierta.")
    _render_live_chat(messages)


def _render_reply_form(selected_case: pd.Series) -> None:
    """Renderiza el formulario estable para responder como asesor."""
    context = _case_context(selected_case)

    if not context["conversation_id"] or not context["user_id"]:
        st.warning("El caso no tiene conversación o usuario asociado.")
        return

    with st.form(f"human_reply_form_{context['case_id']}", clear_on_submit=True):
        reply = st.text_area(
            "Responder como asesor",
            placeholder="Escribe la respuesta para enviarla por WhatsApp...",
            height=110,
        )
        submitted = st.form_submit_button("Enviar respuesta", type="primary")

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


st.set_page_config(
    page_title="Casos Derivados - CrediBot",
    page_icon="CB",
    layout="wide",
)

require_auth()

st.title("Casos Derivados")
st.caption("Bandeja de atención humana con resumen y últimos mensajes del cliente.")

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

summary_cols = st.columns(4)
summary_cols[0].metric("Pendientes", len(df))
summary_cols[1].metric(
    "Solicitan asesor",
    int((df["reason"] == "user_requested_advisor").sum()) if "reason" in df else 0,
)
summary_cols[2].metric(
    "Observados",
    int((df["reason"] == "observed_result").sum()) if "reason" in df else 0,
)
summary_cols[3].metric(
    "Fallos de datos",
    int((df["reason"] == "repeated_invalid_input").sum()) if "reason" in df else 0,
)

st.dataframe(df[visible_columns], use_container_width=True, hide_index=True)

case_ids = df["id"].astype(str).tolist()
selected_case_id = st.selectbox("Seleccionar caso", case_ids)
selected_case = df[df["id"].astype(str) == selected_case_id].iloc[0]

st.subheader("Detalle del caso")

col1, col2 = st.columns(2)

col1.write(f"**Cliente:** {_safe_value(selected_case.get('usuario_full_name'))}")
col1.write(f"**Telefono:** {_safe_value(selected_case.get('usuario_phone'))}")
col1.write(f"**Motivo:** {_reason_text(selected_case.get('reason'))}")
col1.write(f"**Estado:** {_safe_value(selected_case.get('status'))}")

col2.write(
    f"**Monto solicitado:** {_money_text(selected_case.get('solicitud_requested_amount'))}"
)
col2.write(f"**Plazo:** {_term_text(selected_case.get('solicitud_term_months'))}")
col2.write(
    f"**Ingreso mensual:** {_money_text(selected_case.get('solicitud_monthly_income'))}"
)
col2.write(f"**Resultado:** {_safe_value(selected_case.get('solicitud_result'))}")

st.markdown("### Resumen para asesor")
st.info(str(_safe_value(selected_case.get("handoff_summary"), "Sin resumen guardado.")))

st.markdown("### Chat en vivo")

auto_refresh = st.toggle("Actualizar chat automaticamente", value=True)

if auto_refresh and hasattr(st, "fragment"):

    @st.fragment(run_every="5s")
    def _live_chat_fragment() -> None:
        _render_chat_messages(selected_case)

    _live_chat_fragment()
else:
    if st.button("Actualizar chat"):
        st.rerun()
    _render_chat_messages(selected_case)

_render_reply_form(selected_case)

st.markdown("### Gestión")
if st.button("Cerrar caso", type="primary"):
    try:
        cerrar_caso_derivado(str(selected_case_id))
    except Exception as exc:
        st.error(f"No se pudo cerrar el caso: {exc}")
    else:
        st.success("Caso cerrado correctamente.")
        st.rerun()
