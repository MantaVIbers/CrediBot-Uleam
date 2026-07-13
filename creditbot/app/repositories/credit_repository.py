"""Operaciones de base de datos para la tabla credit_requests."""
from datetime import datetime, timezone
from typing import Any

from app.repositories.supabase_client import get_supabase_client


def create_draft_request(user_id: str, conversation_id: str) -> dict[str, Any]:
    """Crea una solicitud de crédito en estado 'draft'."""
    response = (
        get_supabase_client()
        .table("credit_requests")
        .insert(
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "status": "draft",
            }
        )
        .execute()
    )
    return response.data[0]


def get_draft_request(conversation_id: str) -> dict[str, Any] | None:
    """Retorna la solicitud en estado draft asociada a una conversación."""
    response = (
        get_supabase_client()
        .table("credit_requests")
        .select("*")
        .eq("conversation_id", conversation_id)
        .eq("status", "draft")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def update_amount(request_id: str, amount: float) -> dict[str, Any]:
    """Actualiza el monto solicitado en una solicitud."""
    response = (
        get_supabase_client()
        .table("credit_requests")
        .update(
            {
                "requested_amount": amount,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", request_id)
        .execute()
    )
    return response.data[0]


def update_term(request_id: str, term_months: int) -> dict[str, Any]:
    """Actualiza el plazo en meses de una solicitud."""
    response = (
        get_supabase_client()
        .table("credit_requests")
        .update(
            {
                "term_months": term_months,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", request_id)
        .execute()
    )
    return response.data[0]


def update_income(request_id: str, monthly_income: float) -> dict[str, Any]:
    """Actualiza el ingreso mensual registrado en una solicitud."""
    response = (
        get_supabase_client()
        .table("credit_requests")
        .update(
            {
                "monthly_income": monthly_income,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", request_id)
        .execute()
    )
    return response.data[0]


def update_cedula(request_id: str, cedula: str) -> dict[str, Any]:
    """Guarda la cédula asociada a la solicitud (flujo v2)."""
    response = (
        get_supabase_client()
        .table("credit_requests")
        .update(
            {
                "cedula": cedula,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", request_id)
        .execute()
    )
    return response.data[0]


def save_result(
    request_id: str,
    estimated_payment: float,
    payment_capacity: float,
    result: str,
) -> dict[str, Any]:
    """Guarda el resultado de la evaluación y marca la solicitud como completada."""
    response = (
        get_supabase_client()
        .table("credit_requests")
        .update(
            {
                "estimated_payment": estimated_payment,
                "payment_capacity": payment_capacity,
                "result": result,
                "status": "completed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", request_id)
        .execute()
    )
    return response.data[0]


def save_result_v2(
    request_id: str,
    *,
    credit_score: int | None,
    score_category: str,
    max_amount: float,
    annual_rate: float,
    estimated_payment: float,
    payment_capacity: float,
    result: str,
) -> dict[str, Any]:
    """Guarda el resultado de la precalificación v2 (score, categoría, monto y tasa)."""
    response = (
        get_supabase_client()
        .table("credit_requests")
        .update(
            {
                "credit_score": credit_score,
                "score_category": score_category,
                "max_amount": max_amount,
                "annual_rate": annual_rate,
                "estimated_payment": estimated_payment,
                "payment_capacity": payment_capacity,
                "result": result,
                "status": "completed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", request_id)
        .execute()
    )
    return response.data[0]
