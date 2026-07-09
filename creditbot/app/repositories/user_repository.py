from typing import Any

from app.repositories.supabase_client import get_supabase_client


def get_user_by_phone(phone: str) -> dict[str, Any] | None:
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
    payload: dict[str, Any] = {"phone": phone}
    if full_name:
        payload["full_name"] = full_name

    response = get_supabase_client().table("users").insert(payload).execute()
    return response.data[0]


def get_or_create_user(phone: str) -> dict[str, Any]:
    user = get_user_by_phone(phone)
    if user:
        return user
    return create_user(phone)


def update_user_name(user_id: str, full_name: str) -> dict[str, Any]:
    response = (
        get_supabase_client()
        .table("users")
        .update({"full_name": full_name})
        .eq("id", user_id)
        .execute()
    )
    return response.data[0]
