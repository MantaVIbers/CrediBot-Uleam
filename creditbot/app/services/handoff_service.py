"""Capa de servicio para la derivación de casos a asesor humano."""
from datetime import datetime, timezone
from typing import Any

from app.repositories import (
    conversation_repository,
    handoff_repository,
    message_repository,
    user_repository,
)
from app.services.whatsapp_service import WhatsAppServiceError, send_text_message

REASON_LABELS = {
    "user_requested_advisor": "El cliente solicitó hablar con un asesor.",
    "menu_option_3": "El cliente eligió la opción de hablar con asesor.",
    "observed_result": "La precalificación quedó observada y requiere revisión.",
    "repeated_invalid_input": "El cliente falló varias veces al ingresar datos.",
}


def _compact_transcript(messages: list[dict[str, Any]], limit: int = 12) -> list[dict[str, str]]:
    """Prepara los últimos mensajes para que el asesor retome el caso."""
    compact: list[dict[str, str]] = []
    for message in messages[-limit:]:
        compact.append(
            {
                "direction": str(message.get("direction", "")),
                "content": str(message.get("content", "")),
                "created_at": str(message.get("created_at", "")),
            }
        )
    return compact


def _build_handoff_summary(reason: str, transcript: list[dict[str, str]]) -> str:
    """Construye un resumen breve y estable para el asesor humano."""
    reason_text = REASON_LABELS.get(reason, f"Motivo de derivación: {reason}.")
    last_user_message = next(
        (
            item["content"]
            for item in reversed(transcript)
            if item.get("direction") == "inbound" and item.get("content")
        ),
        "Sin último mensaje del cliente.",
    )
    return f"{reason_text} Último mensaje del cliente: {last_user_message}"


def create_handoff_case(
    user_id: str,
    conversation_id: str,
    reason: str,
    credit_request_id: str | None = None,
) -> dict[str, Any]:
    """Crea un caso de derivación a través del repositorio."""
    messages = message_repository.get_messages_by_conversation(conversation_id)
    transcript = _compact_transcript(messages)
    return handoff_repository.create_handoff_case(
        user_id=user_id,
        conversation_id=conversation_id,
        reason=reason,
        credit_request_id=credit_request_id,
        handoff_summary=_build_handoff_summary(reason, transcript),
        transcript=transcript,
    )


def get_pending_handoff_cases() -> list[dict[str, Any]]:
    """Retorna todos los casos de derivación pendientes."""
    return handoff_repository.get_pending_handoff_cases()


def get_open_handoff_cases() -> list[dict[str, Any]]:
    """Retorna casos abiertos (pending o assigned)."""
    return handoff_repository.get_open_handoff_cases()


def get_open_handoff_case_for_user(user_id: str) -> dict[str, Any] | None:
    """Retorna el caso abierto más reciente de un usuario, si existe."""
    return handoff_repository.get_open_handoff_case_by_user(user_id)


def close_handoff_case(case_id: str) -> dict[str, Any]:
    """Cierra un caso de derivación."""
    case = handoff_repository.get_handoff_case_by_id(case_id)
    if not case:
        raise ValueError("Caso de derivación no encontrado.")
    if case.get("status") == "closed":
        return case
    closed = handoff_repository.close_handoff_case(case_id)
    conversation_id = case.get("conversation_id")
    if conversation_id:
        conversation_repository.finish_conversation(str(conversation_id))
    return closed


def reply_as_advisor(case_id: str, content: str) -> dict[str, Any]:
    """Envía la respuesta del asesor por WhatsApp y la registra en el historial."""
    message = (content or "").strip()
    if not message:
        raise ValueError("Escribe un mensaje antes de enviar.")

    case = handoff_repository.get_handoff_case_by_id(case_id)
    if not case:
        raise ValueError("Caso de derivación no encontrado.")
    if case.get("status") == "closed":
        raise ValueError("El caso ya está cerrado.")

    user = user_repository.get_user_by_id(str(case["user_id"]))
    if not user or not user.get("phone"):
        raise ValueError("El caso no tiene un teléfono de cliente asociado.")

    phone = str(user["phone"])
    conversation_id = str(case["conversation_id"])
    user_id = str(case["user_id"])

    try:
        provider_response = send_text_message(phone, message)
    except WhatsAppServiceError as exc:
        raise RuntimeError(str(exc)) from exc

    raw_payload = {
        "source": "dashboard_human",
        "provider_response": provider_response,
    }
    saved = message_repository.save_outbound_message(
        conversation_id=conversation_id,
        user_id=user_id,
        content=message,
        raw_payload=raw_payload,
    )

    transcript = case.get("transcript") if isinstance(case.get("transcript"), list) else []
    transcript = list(transcript)
    transcript.append(
        {
            "direction": "outbound",
            "content": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "dashboard_human",
        }
    )
    updated_case = handoff_repository.update_handoff_case(
        case_id,
        status="assigned",
        transcript=transcript[-20:],
    )

    return {
        "case": updated_case,
        "message": saved,
        "phone": phone,
    }


def register_handoff(
    user_id: str,
    conversation_id: str,
    reason: str,
    credit_request_id: str | None = None,
) -> dict[str, Any]:
    """Alias para crear un caso de derivación (usado desde conversation_service)."""
    return create_handoff_case(
        user_id=user_id,
        conversation_id=conversation_id,
        reason=reason,
        credit_request_id=credit_request_id,
    )
