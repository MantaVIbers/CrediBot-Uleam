"""Operaciones de base de datos para la tabla handoff_cases (derivación a asesor)."""
from datetime import datetime, timezone
from typing import Any

from app.repositories.supabase_client import get_supabase_client


def create_handoff_case(
    user_id: str,
    conversation_id: str,
    reason: str,
    credit_request_id: str | None = None,
) -> dict[str, Any]:
    """Crea un caso de derivación a asesor humano."""
    payload: dict[str, Any] = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "reason": reason,
        "status": "pending",
    }
    if credit_request_id:
        payload["credit_request_id"] = credit_request_id

    response = get_supabase_client().table("handoff_cases").insert(payload).execute()
    return response.data[0]


def get_pending_handoff_cases() -> list[dict[str, Any]]:
    """Retorna todos los casos de derivación pendientes."""
    response = (
        get_supabase_client()
        .table("handoff_cases")
        .select("*")
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def close_handoff_case(case_id: str) -> dict[str, Any]:
    """Cierra un caso de derivación cambiando su estado a 'closed'."""
    response = (
        get_supabase_client()
        .table("handoff_cases")
        .update(
            {
                "status": "closed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", case_id)
        .execute()
    )
    return response.data[0]
