"""Servicio de conexión a Supabase específico para el dashboard de Streamlit."""
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
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
    """Obtiene los casos derivados pendientes de atención desde Supabase."""
    response = (
        get_supabase_client()
        .table("handoff_cases")
        .select("*")
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def cerrar_caso_derivado(case_id: str) -> dict[str, Any]:
    """Marca un caso derivado como cerrado."""
    response = (
        get_supabase_client()
        .table("handoff_cases")
        .update({"status": "closed"})
        .eq("id", case_id)
        .execute()
    )
    return (response.data or [{}])[0]


def probar_conexion() -> bool:
    """Prueba la conexión a Supabase consultando la tabla users."""
    get_supabase_client().table("users").select("id").limit(1).execute()
    return True
