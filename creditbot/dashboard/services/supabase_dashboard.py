"""Servicio de conexión a Supabase específico para el dashboard de Streamlit."""
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import httpx
import streamlit as st
from supabase import Client, create_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class DashboardConfigError(RuntimeError):
    """Error de configuración del dashboard (variables de entorno faltantes)."""
    pass


def _get_env_value(name: str) -> str:
    """Obtiene un valor desde .env local o secretos de Streamlit Cloud."""
    import os

    env_value = os.getenv(name, "").strip()
    if env_value:
        return env_value

    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


@lru_cache
def get_supabase_client() -> Client:
    """Retorna el cliente de Supabase (cacheado) para el dashboard."""
    supabase_url = _get_env_value("SUPABASE_URL")
    supabase_key = _get_env_value("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise DashboardConfigError(
            "Configura SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en .env o en Secrets."
        )

    return create_client(supabase_url, supabase_key)


def obtener_usuarios() -> list[dict[str, Any]]:
    """Obtiene todos los usuarios desde Supabase."""
    response = (
        get_supabase_client()
        .table("users")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def obtener_solicitudes() -> list[dict[str, Any]]:
    """Obtiene todas las solicitudes de crédito desde Supabase."""
    response = (
        get_supabase_client()
        .table("credit_requests")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def obtener_casos_derivados() -> list[dict[str, Any]]:
    """Obtiene los casos derivados abiertos desde Supabase."""
    response = (
        get_supabase_client()
        .table("handoff_cases")
        .select("*")
        .neq("status", "closed")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def obtener_mensajes_conversacion(conversation_id: str) -> list[dict[str, Any]]:
    """Obtiene el historial completo de mensajes de una conversación."""
    response = (
        get_supabase_client()
        .table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data or []


def _format_twilio_whatsapp_number(phone: str) -> str:
    """Formatea un número al formato requerido por Twilio WhatsApp."""
    cleaned = phone.replace("whatsapp:", "").replace("+", "").strip()
    return f"whatsapp:+{cleaned}"


def _send_dashboard_whatsapp_message(to_phone: str, message: str) -> dict[str, Any]:
    """Envía WhatsApp desde el dashboard usando .env o Secrets de Streamlit."""
    account_sid = _get_env_value("TWILIO_ACCOUNT_SID")
    auth_token = _get_env_value("TWILIO_AUTH_TOKEN")
    whatsapp_from = _get_env_value("TWILIO_WHATSAPP_FROM")

    if not account_sid:
        raise DashboardConfigError("TWILIO_ACCOUNT_SID no está configurado.")
    if not auth_token:
        raise DashboardConfigError("TWILIO_AUTH_TOKEN no está configurado.")
    if not whatsapp_from:
        raise DashboardConfigError("TWILIO_WHATSAPP_FROM no está configurado.")

    response = httpx.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
        data={
            "From": whatsapp_from,
            "To": _format_twilio_whatsapp_number(to_phone),
            "Body": message,
        },
        auth=(account_sid, auth_token),
        timeout=30.0,
    )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise DashboardConfigError(
            f"Error de Twilio API ({exc.response.status_code}): {exc.response.text}"
        ) from exc

    return response.json()


def enviar_respuesta_humana(
    *,
    case_id: str,
    conversation_id: str,
    user_id: str,
    phone: str,
    content: str,
) -> dict[str, Any]:
    """Envía una respuesta humana por WhatsApp y la registra en el historial."""
    from datetime import datetime, timezone

    message = content.strip()
    if not message:
        raise DashboardConfigError("Escribe un mensaje antes de enviar.")
    if not phone:
        raise DashboardConfigError("El caso no tiene teléfono asociado.")

    twilio_response = _send_dashboard_whatsapp_message(phone, message)

    raw_payload = {
        "source": "dashboard_human",
        "twilio_sid": twilio_response.get("sid"),
        "twilio_status": twilio_response.get("status"),
    }

    response = (
        get_supabase_client()
        .table("messages")
        .insert(
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "direction": "outbound",
                "content": message,
                "raw_payload": raw_payload,
            }
        )
        .execute()
    )

    get_supabase_client().table("handoff_cases").update(
        {
            "status": "assigned",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", case_id).execute()

    return response.data[0]


def cerrar_caso_derivado(case_id: str) -> dict[str, Any]:
    """Marca un caso derivado como cerrado."""
    from datetime import datetime, timezone

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
    return (response.data or [{}])[0]


def probar_conexion() -> bool:
    """Prueba la conexión a Supabase consultando la tabla users."""
    get_supabase_client().table("users").select("id").limit(1).execute()
    return True
