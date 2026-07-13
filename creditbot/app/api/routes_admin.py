"""Rutas administrativas para consultar datos y responder handoffs."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import require_admin_password
from app.repositories import conversation_repository, message_repository, user_repository
from app.repositories.supabase_client import get_supabase_client
from app.services.handoff_service import (
    close_handoff_case,
    get_open_handoff_cases,
    get_pending_handoff_cases,
    reply_as_advisor,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class HandoffReplyRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


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
    """Retorna los casos de derivación abiertos (pending/assigned)."""
    return {"items": get_open_handoff_cases()}


@router.get("/handoff/pending")
def list_pending_handoff_cases():
    """Retorna solo casos pendientes (compatibilidad)."""
    return {"items": get_pending_handoff_cases()}


@router.post("/handoff/{case_id}/reply")
def reply_handoff_case(
    case_id: str,
    body: HandoffReplyRequest,
    _: None = Depends(require_admin_password),
):
    """Envía una respuesta humana por WhatsApp (Meta/Twilio según proveedor)."""
    try:
        result = reply_as_advisor(case_id, body.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "status": "ok",
        "phone": result["phone"],
        "case": result["case"],
        "message": result["message"],
    }


@router.post("/handoff/{case_id}/close")
def close_handoff(
    case_id: str,
    _: None = Depends(require_admin_password),
):
    """Cierra un caso de derivación."""
    try:
        case = close_handoff_case(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok", "case": case}


@router.get("/conversations/{phone}")
def get_conversation_by_phone(phone: str):
    """Retorna usuario, conversación y mensajes dado un número de teléfono."""
    user = user_repository.get_user_by_phone(phone)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Buscar conversación activa; si no existe, obtener la más reciente
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
