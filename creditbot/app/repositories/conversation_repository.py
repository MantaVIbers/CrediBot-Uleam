"""Operaciones de base de datos para la tabla conversations."""
from datetime import datetime, timezone
from typing import Any

from app.core.constants import START
from app.repositories.supabase_client import get_supabase_client


def get_active_conversation(user_id: str) -> dict[str, Any] | None:
    """Retorna la conversación activa más reciente de un usuario, o None."""
    response = (
        get_supabase_client()
        .table("conversations")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def create_conversation(user_id: str) -> dict[str, Any]:
    """Crea una nueva conversación en estado START para el usuario."""
    response = (
        get_supabase_client()
        .table("conversations")
        .insert({"user_id": user_id, "current_state": START})
        .execute()
    )
    return response.data[0]


def get_or_create_active_conversation(user_id: str) -> dict[str, Any]:
    """Recupera la conversación activa o crea una nueva si no existe."""
    conversation = get_active_conversation(user_id)
    if conversation:
        return conversation
    return create_conversation(user_id)


def get_conversation_by_id(conversation_id: str) -> dict[str, Any] | None:
    """Busca una conversación por ID."""
    response = (
        get_supabase_client()
        .table("conversations")
        .select("*")
        .eq("id", conversation_id)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def reactivate_conversation(conversation_id: str, new_state: str) -> dict[str, Any]:
    """Reactiva una conversación finalizada para continuar atención humana."""
    response = (
        get_supabase_client()
        .table("conversations")
        .update(
            {
                "is_active": True,
                "current_state": new_state,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", conversation_id)
        .execute()
    )
    return response.data[0]


def update_state(conversation_id: str, new_state: str) -> dict[str, Any]:
    """Actualiza el estado actual de una conversación."""
    response = (
        get_supabase_client()
        .table("conversations")
        .update(
            {
                "current_state": new_state,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", conversation_id)
        .execute()
    )
    return response.data[0]


def update_last_message(conversation_id: str, message: str) -> dict[str, Any]:
    """Guarda el último mensaje enviado en la conversación."""
    response = (
        get_supabase_client()
        .table("conversations")
        .update(
            {
                "last_message": message,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", conversation_id)
        .execute()
    )
    return response.data[0]


def finish_conversation(conversation_id: str) -> dict[str, Any]:
    """Marca la conversación como inactiva (finalizada)."""
    response = (
        get_supabase_client()
        .table("conversations")
        .update(
            {
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", conversation_id)
        .execute()
    )
    return response.data[0]
