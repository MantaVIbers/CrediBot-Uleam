"""Capa de servicio para la derivación de casos a asesor humano."""
from typing import Any

from app.repositories import handoff_repository, message_repository

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


def close_handoff_case(case_id: str) -> dict[str, Any]:
    """Cierra un caso de derivación."""
    return handoff_repository.close_handoff_case(case_id)


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
