"""Servicio de conexión a Supabase y envío WhatsApp (Twilio) para el dashboard."""
from datetime import datetime, timezone
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


def obtener_estado_configuracion() -> dict[str, Any]:
    """Indica qué piezas están listas para responder desde el panel."""
    supabase_ok = bool(
        _get_env_value("SUPABASE_URL") and _get_env_value("SUPABASE_SERVICE_ROLE_KEY")
    )
    twilio_ok = bool(
        _get_env_value("TWILIO_ACCOUNT_SID")
        and _get_env_value("TWILIO_AUTH_TOKEN")
        and _get_env_value("TWILIO_WHATSAPP_FROM")
    )
    backend_url = _backend_api_url()
    backend_ok = bool(backend_url and _admin_password())
    return {
        "supabase": supabase_ok,
        "twilio": twilio_ok,
        "backend_api": backend_ok,
        "can_reply": supabase_ok and (twilio_ok or backend_ok),
        "reply_mode": "twilio_direct" if twilio_ok else ("backend_api" if backend_ok else "none"),
        "backend_url": backend_url,
    }


def _backend_api_url() -> str:
    return _get_env_value("BACKEND_API_URL").rstrip("/")


def _admin_password() -> str:
    return _get_env_value("ADMIN_DASHBOARD_PASSWORD")


def _simulator_backend_url() -> str:
    """URL del backend para el simulador, con fallback local."""
    return (
        _get_env_value("BACKEND_API_URL")
        or _get_env_value("APP_PUBLIC_URL")
        or "http://localhost:8000"
    ).rstrip("/")


@st.cache_data(ttl=20, show_spinner=False)
def obtener_estado_backend() -> dict[str, Any]:
    """Comprueba si el backend del simulador está disponible."""
    url = _simulator_backend_url()
    try:
        response = httpx.get(f"{url}/health", timeout=8.0, follow_redirects=True)
        response.raise_for_status()
        return {"online": True, "url": url, "detail": response.json()}
    except Exception as exc:
        return {"online": False, "url": url, "detail": str(exc)}


def simular_mensaje(phone: str, message: str) -> str:
    """Envía un turno al simulador FastAPI y retorna la respuesta de CrediBot."""
    phone_value = phone.strip()
    message_value = message.strip()
    if not phone_value or not message_value:
        raise DashboardConfigError("El teléfono y el mensaje son obligatorios.")

    url = _simulator_backend_url()
    try:
        response = httpx.post(
            f"{url}/simulate/message",
            json={"phone": phone_value, "message": message_value},
            timeout=45.0,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise DashboardConfigError(
            f"El simulador respondió {exc.response.status_code}: {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise DashboardConfigError(
            f"No se pudo conectar con el backend en {url}: {exc}"
        ) from exc

    return str(response.json().get("reply") or "Sin respuesta del bot.")


def _format_twilio_whatsapp_number(phone: str) -> str:
    """Formatea un número al formato requerido por Twilio WhatsApp."""
    cleaned = phone.replace("whatsapp:", "").replace("+", "").strip()
    return f"whatsapp:+{cleaned}"


def _send_twilio_whatsapp_message(to_phone: str, message: str) -> dict[str, Any]:
    """Envía WhatsApp desde el panel usando credenciales Twilio."""
    account_sid = _get_env_value("TWILIO_ACCOUNT_SID")
    auth_token = _get_env_value("TWILIO_AUTH_TOKEN")
    whatsapp_from = _get_env_value("TWILIO_WHATSAPP_FROM")

    missing = [
        name
        for name, ok in (
            ("TWILIO_ACCOUNT_SID", bool(account_sid)),
            ("TWILIO_AUTH_TOKEN", bool(auth_token)),
            ("TWILIO_WHATSAPP_FROM", bool(whatsapp_from)),
        )
        if not ok
    ]
    if missing:
        raise DashboardConfigError(
            "Faltan credenciales Twilio en el panel: "
            + ", ".join(missing)
            + ". Agrégalas en .env, Streamlit Secrets o Render (servicio dashboard)."
        )

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
            f"Twilio rechazó el envío ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise DashboardConfigError(f"No se pudo conectar con Twilio: {exc}") from exc

    return response.json()


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


def _persist_human_reply(
    *,
    case_id: str,
    conversation_id: str,
    user_id: str,
    content: str,
    provider_payload: dict[str, Any],
    channel: str,
) -> dict[str, Any]:
    """Guarda el mensaje saliente y marca el caso como assigned."""
    raw_payload = {
        "source": "dashboard_human",
        "channel": channel,
        **provider_payload,
    }
    response = (
        get_supabase_client()
        .table("messages")
        .insert(
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "direction": "outbound",
                "content": content,
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

    return (response.data or [{}])[0]


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


def obtener_auditoria_ia() -> list[dict[str, Any]]:
    """Obtiene las invocaciones auditadas de herramientas del agente."""
    response = (
        get_supabase_client()
        .table("tool_audit_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(500)
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
    """Envía respuesta humana por Twilio (preferido) o backend como respaldo."""
    message = content.strip()
    if not message:
        raise DashboardConfigError("Escribe un mensaje antes de enviar.")
    if not phone:
        raise DashboardConfigError("El caso no tiene teléfono asociado.")

    config = obtener_estado_configuracion()
    if not config["can_reply"]:
        raise DashboardConfigError(
            "No hay canal de envío configurado. Agrega TWILIO_ACCOUNT_SID, "
            "TWILIO_AUTH_TOKEN y TWILIO_WHATSAPP_FROM en el panel (o BACKEND_API_URL "
            "+ ADMIN_DASHBOARD_PASSWORD en el backend con Twilio en Render)."
        )

    if config["twilio"]:
        twilio_response = _send_twilio_whatsapp_message(phone, message)
        return _persist_human_reply(
            case_id=case_id,
            conversation_id=conversation_id,
            user_id=user_id,
            content=message,
            provider_payload={
                "twilio_sid": twilio_response.get("sid"),
                "twilio_status": twilio_response.get("status"),
            },
            channel="twilio_direct",
        )

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
