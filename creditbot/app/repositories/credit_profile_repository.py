"""Operaciones de lectura para la tabla credit_profiles (perfiles crediticios).

En producción estos datos vendrían de un buró (Equifax). Aquí provienen del seed
FICTICIO cargado en Supabase (supabase/seed_credit_profiles.sql). El repositorio
solo lee: la precalificación nunca modifica el buró.
"""
from typing import Any

from app.repositories.supabase_client import get_supabase_client


def _clean_cedula(cedula: str) -> str:
    """Normaliza la cédula quitando separadores para consultar la tabla."""
    # Elimina espacios, guiones y otros separadores comunes en cédulas
    return (cedula or "").strip().replace("-", "").replace(" ", "")


def get_profile_by_cedula(cedula: str) -> dict[str, Any] | None:
    """Busca el perfil crediticio por cédula. Retorna el dict o None si no existe."""
    cleaned = _clean_cedula(cedula)
    # Si la cédula está vacía después de limpiar, retorna None
    if not cleaned:
        return None

    response = (
        get_supabase_client()
        .table("credit_profiles")
        .select("*")
        .eq("cedula", cleaned)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None
