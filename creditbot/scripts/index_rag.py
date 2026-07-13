#!/usr/bin/env python3
"""Indexa chunks RAG en Supabase generando embeddings con OpenAI.

Uso (desde creditbot/):
    python scripts/index_rag.py

Requisitos: OPENAI_API_KEY, SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY en .env
Ejecutar seed_rag_documents.sql antes si la tabla está vacía.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

# Configurar la ruta del proyecto para importaciones
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.repositories.rag_repository import list_all_chunks  # noqa: E402
from app.repositories.supabase_client import get_supabase_client  # noqa: E402


def main() -> None:
    if not settings.openai_api_key:
        raise SystemExit("Configura OPENAI_API_KEY en .env")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    chunks = list_all_chunks()
    # Filtrar chunks que aún no tienen embedding generado
    pending = [c for c in chunks if not c.get("embedding")]
    if not pending:
        print("No hay chunks pendientes de indexar.")
        return

    texts = [c["content"] for c in pending]
    response = client.embeddings.create(model="text-embedding-3-small", input=texts)
    vectors = [item.embedding for item in response.data]

    supabase = get_supabase_client()
    for chunk, vector in zip(pending, vectors, strict=True):
        supabase.table("rag_chunks").update({"embedding": vector}).eq("id", chunk["id"]).execute()
        print(f"Indexado chunk {chunk['id']} ({len(vector)} dims)")

    print(f"Listo. {len(pending)} chunks indexados.")


if __name__ == "__main__":
    main()
