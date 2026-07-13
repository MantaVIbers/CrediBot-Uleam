"""Servicio de conexión a Supabase y API backend para el dashboard."""
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import httpx
import streamlit as st
from supabase import Client, create_client


# Obtener la ruta raíz del proyecto y cargar variables de entorno
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


def _backend_api_url() -> str:
    return _get_env_value("BACKEND_API_URL").rstrip("/")


def _admin_password() -> str:
    return _get_env_value("ADMIN_DASHBOARD_PASSWORD")


def _call_backend(method: str, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Llama al backend FastAPI con autenticación de admin."""
    base = _backend_api_url()
    password = _admin_password()
    if not base:
        raise DashboardConfigError(
            "Configura BACKEND_API_URL (ej. https://credibot-uleam-gjj2.onrender.com)."
        )
    if not password:
        raise DashboardConfigError(
            "Configura ADMIN_DASHBOARD_PASSWORD (debe coincidir con el backend)."
        )

    url = f"{base}{path}"
    headers = {"X-Admin-Password": password}
    try:
        response = httpx.request(
            method,
            url,
            json=json_body,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        try:
            detail = exc.response.json().get("detail", detail)
        except Exception:
            pass
        raise DashboardConfigError(
            f"Error del backend ({exc.response.status_code}): {detail}"
        ) from exc
    except httpx.RequestError as exc:
        raise DashboardConfigError(f"No se pudo conectar al backend: {exc}") from exc

    if not response.content:
        return {}
    return response.json()


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


def enviar_respuesta_humana(
    *,
    case_id: str,
    conversation_id: str,
    user_id: str,
    phone: str,
    content: str,
) -> dict[str, Any]:
    """Envía respuesta humana vía backend (Meta/Twilio) y refresca el caso."""
    del conversation_id, user_id, phone  # el backend resuelve teléfono desde el caso
    message = content.strip()
    if not message:
        raise DashboardConfigError("Escribe un mensaje antes de enviar.")

    result = _call_backend(
        "POST",
        f"/admin/handoff/{case_id}/reply",
        {"message": message},
    )
    return result.get("message") or result


def cerrar_caso_derivado(case_id: str) -> dict[str, Any]:
    """Cierra el caso vía backend (fallback local a Supabase si no hay API)."""
    if _backend_api_url() and _admin_password():
        result = _call_backend("POST", f"/admin/handoff/{case_id}/close")
        return result.get("case") or result

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


def obtener_auditoria_tools(limit: int = 100) -> list[dict[str, Any]]:
    """Obtiene registros de auditoría de tools del agente IA."""
    response = (
        get_supabase_client()
        .table("tool_audit_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def probar_conexion() -> bool:
    """Prueba la conexión a Supabase consultando la tabla users."""
    get_supabase_client().table("users").select("id").limit(1).execute()
    return True
