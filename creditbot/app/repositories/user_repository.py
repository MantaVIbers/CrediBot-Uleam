"""Operaciones de base de datos para la tabla users."""
from datetime import datetime, timezone
from typing import Any

from app.repositories.supabase_client import get_supabase_client


def get_user_by_phone(phone: str) -> dict[str, Any] | None:
    """Busca un usuario por su número de teléfono."""
    response = (
        get_supabase_client()
        .table("users")
        .select("*")
        .eq("phone", phone)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def create_user(phone: str, full_name: str | None = None) -> dict[str, Any]:
    """Crea un nuevo usuario con el teléfono dado."""
    payload: dict[str, Any] = {"phone": phone}
    if full_name:
        payload["full_name"] = full_name

    response = get_supabase_client().table("users").insert(payload).execute()
    return response.data[0]


def get_or_create_user(phone: str) -> dict[str, Any]:
    """Retorna el usuario si existe, o lo crea si no."""
    user = get_user_by_phone(phone)
    if user:
        return user
    return create_user(phone)


def update_user_name(user_id: str, full_name: str) -> dict[str, Any]:
    """Actualiza el nombre completo de un usuario."""
    response = (
        get_supabase_client()
        .table("users")
        .update({"full_name": full_name})
        .eq("id", user_id)
        .execute()
    )
    return response.data[0]


def update_cedula_consent(user_id: str, cedula: str) -> dict[str, Any]:
    """Registra la cédula y el consentimiento del usuario (RF-08).

    La cédula solo se almacena tras el consentimiento explícito, junto con la
    marca de tiempo en que fue otorgado.
    """
    response = (
        get_supabase_client()
        .table("users")
        .update(
            {
                "cedula": cedula,
                "consent_given": True,
                "consent_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", user_id)
        .execute()
    )
    return response.data[0]
