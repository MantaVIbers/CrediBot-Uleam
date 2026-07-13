"""Operaciones de base de datos para la tabla handoff_cases (derivación a asesor)."""
from datetime import datetime, timezone
from typing import Any

from app.repositories.supabase_client import get_supabase_client


def create_handoff_case(
    user_id: str,
    conversation_id: str,
    reason: str,
    credit_request_id: str | None = None,
    handoff_summary: str | None = None,
    transcript: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Crea un caso de derivación a asesor humano."""
    # Construye el payload base con los campos requeridos
    payload: dict[str, Any] = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "reason": reason,
        "status": "pending",
    }
    # Agrega campos opcionales solo si se proporcionaron
    if credit_request_id:
        payload["credit_request_id"] = credit_request_id
    if handoff_summary:
        payload["handoff_summary"] = handoff_summary
    if transcript is not None:
        payload["transcript"] = transcript

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


def get_open_handoff_cases() -> list[dict[str, Any]]:
    """Retorna casos abiertos (pending o assigned)."""
    response = (
        get_supabase_client()
        .table("handoff_cases")
        .select("*")
        .neq("status", "closed")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def get_handoff_case_by_id(case_id: str) -> dict[str, Any] | None:
    """Busca un caso de derivación por ID."""
    response = (
        get_supabase_client()
        .table("handoff_cases")
        .select("*")
        .eq("id", case_id)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def update_handoff_case(
    case_id: str,
    *,
    status: str | None = None,
    transcript: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Actualiza estado y/o transcript de un caso."""
    # Siempre actualiza la marca de tiempo
    payload: dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    # Agrega campos opcionales solo si se proporcionaron
    if status is not None:
        payload["status"] = status
    if transcript is not None:
        payload["transcript"] = transcript

    response = (
        get_supabase_client()
        .table("handoff_cases")
        .update(payload)
        .eq("id", case_id)
        .execute()
    )
    return response.data[0]


def close_handoff_case(case_id: str) -> dict[str, Any]:
    """Cierra un caso de derivación cambiando su estado a 'closed'."""
    return update_handoff_case(case_id, status="closed")
