"""Memoria acotada de conversación para respuestas naturales."""
from app.repositories import message_repository


def recent_conversation_memory(conversation_id: str, limit: int = 8) -> str:
    """Devuelve últimos mensajes con roles; Supabase sigue siendo la fuente de verdad."""
    try:
        messages = message_repository.get_messages_by_conversation(conversation_id)
    except Exception:
        return "Sin historial disponible."

    lines: list[str] = []
    for item in messages[-limit:]:
        role = "Cliente" if item.get("direction") == "inbound" else "CrediBot"
        content = " ".join(str(item.get("content") or "").split())
        if content:
            lines.append(f"{role}: {content[:400]}")
    return "\n".join(lines) or "Sin historial disponible."
