from typing import Any

from app.repositories.supabase_client import get_supabase_client


def save_inbound_message(
    conversation_id: str,
    user_id: str,
    content: str,
    raw_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "direction": "inbound",
        "content": content,
    }
    if raw_payload is not None:
        payload["raw_payload"] = raw_payload

    response = get_supabase_client().table("messages").insert(payload).execute()
    return response.data[0]


def save_outbound_message(
    conversation_id: str,
    user_id: str,
    content: str,
    raw_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "direction": "outbound",
        "content": content,
    }
    if raw_payload is not None:
        payload["raw_payload"] = raw_payload

    response = get_supabase_client().table("messages").insert(payload).execute()
    return response.data[0]


def get_messages_by_conversation(conversation_id: str) -> list[dict[str, Any]]:
    response = (
        get_supabase_client()
        .table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data or []
