from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings


@lru_cache
def get_supabase_client() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise ValueError(
            "SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY deben estar configurados en .env"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def test_connection() -> bool:
    client = get_supabase_client()
    client.table("users").select("id").limit(1).execute()
    return True
