"""Lectura de chunks RAG almacenados en Supabase (pgvector)."""
from typing import Any

from app.repositories.supabase_client import get_supabase_client


def list_chunks_with_embeddings(limit: int = 200) -> list[dict[str, Any]]:
    """Lista chunks que ya tienen embedding (para búsqueda local por similitud)."""
    response = (
        get_supabase_client()
        .table("rag_chunks")
        .select("id, content, embedding, metadata")
        # Filtra solo chunks que tengan embedding generado (no nulo)
        .not_.is_("embedding", "null")
        .limit(limit)
        .execute()
    )
    return response.data or []


def list_all_chunks(limit: int = 200) -> list[dict[str, Any]]:
    """Lista chunks de texto (con o sin embedding)."""
    response = (
        get_supabase_client()
        .table("rag_chunks")
        .select("id, content, embedding, metadata")
        .limit(limit)
        .execute()
    )
    return response.data or []
