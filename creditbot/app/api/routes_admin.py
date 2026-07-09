"""Rutas administrativas para consultar datos del sistema."""
from fastapi import APIRouter, HTTPException

from app.repositories import conversation_repository, message_repository, user_repository
from app.repositories.supabase_client import get_supabase_client
from app.services.handoff_service import get_pending_handoff_cases

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/requests")
def list_credit_requests():
    """Retorna todas las solicitudes de crédito."""
    response = (
        get_supabase_client()
        .table("credit_requests")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return {"items": response.data or []}


@router.get("/handoff")
def list_handoff_cases():
    """Retorna los casos de derivación pendientes."""
    return {"items": get_pending_handoff_cases()}


@router.get("/conversations/{phone}")
def get_conversation_by_phone(phone: str):
    """Retorna usuario, conversación y mensajes dado un número de teléfono."""
    user = user_repository.get_user_by_phone(phone)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    conversation = conversation_repository.get_active_conversation(user["id"])
    if not conversation:
        response = (
            get_supabase_client()
            .table("conversations")
            .select("*")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            conversation = response.data[0]

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    messages = message_repository.get_messages_by_conversation(conversation["id"])
    return {
        "user": user,
        "conversation": conversation,
        "messages": messages,
    }
