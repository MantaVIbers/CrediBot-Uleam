from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class DashboardConfigError(RuntimeError):
    pass


def _get_env_value(name: str) -> str:
    import os

    return os.getenv(name, "").strip()


@lru_cache
def get_supabase_client() -> Client:
    supabase_url = _get_env_value("SUPABASE_URL")
    supabase_key = _get_env_value("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise DashboardConfigError(
            "Configura SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en creditbot/.env."
        )

    return create_client(supabase_url, supabase_key)


def obtener_usuarios() -> list[dict[str, Any]]:
    response = (
        get_supabase_client()
        .table("users")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def obtener_solicitudes() -> list[dict[str, Any]]:
    response = (
        get_supabase_client()
        .table("credit_requests")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def obtener_casos_derivados() -> list[dict[str, Any]]:
    response = (
        get_supabase_client()
        .table("handoff_cases")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def probar_conexion() -> bool:
    get_supabase_client().table("users").select("id").limit(1).execute()
    return True

