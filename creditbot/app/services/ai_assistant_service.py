"""Asistente IA con RAG para preguntas generales sobre crédito (RF-07).

El LLM **no calcula** montos ni scores: solo explica políticas usando contexto
recuperado. La precalificación sigue siendo determinista vía `precalificacion_service`.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.core.config import settings
from app.repositories import audit_repository
from app.services import rag_service

logger = logging.getLogger(__name__)

TOOL_NAME = "consultar_politica_credito"

# Prompt del sistema que define el comportamiento del asistente IA
SYSTEM_PROMPT = """Eres CrediBot, asistente de precalificación crediticia de ULEAM (demo académica).
Responde en español, claro y breve (máximo 6 oraciones).
Usa SOLO la información del contexto de política. Si no está en el contexto, dilo honestamente.
No inventes montos, tasas ni scores concretos para el usuario.
Recuerda: esto es precalificación simulada, no una aprobación final.
Si preguntan cómo precalificar, indica que en el menú principal pueden elegir la opción 1."""


def is_ai_enabled() -> bool:
    """True si hay API key de OpenAI configurada."""
    return bool(settings.openai_api_key.strip())


def _fallback_answer() -> str:
    return (
        "CrediBot te ayuda a precalificar crédito por WhatsApp con reglas claras y un buró simulado. "
        "En el menú elige 1 para iniciar la precalificación, 2 para preguntar sobre políticas "
        "(requiere OpenAI configurado) o 3 para hablar con un asesor."
    )


def _audit(
    question: str,
    answer: str,
    *,
    chunks: list[str],
    success: bool,
    latency_ms: int,
    conversation_id: str | None,
    error: str | None = None,
) -> None:
    audit_repository.log_tool_call(
        TOOL_NAME,
        input_payload={"pregunta": question[:500]},
        output_payload={
            "respuesta": answer[:1000],
            "chunks_usados": len(chunks),
            "error": error,
        },
        success=success,
        latency_ms=latency_ms,
        conversation_id=conversation_id,
    )


def answer_credit_question(question: str, conversation_id: str | None = None) -> str:
    """Responde una pregunta general usando RAG + OpenAI Chat Completions."""
    cleaned = question.strip()
    if not cleaned:
        return "Escribe tu pregunta sobre crédito o precalificación."

    if not is_ai_enabled():
        return _fallback_answer()

    started = time.perf_counter()
    chunks: list[str] = []
    try:
        # Recupera fragmentos relevantes de la política de crédito
        if rag_service.is_rag_available():
            chunks = rag_service.retrieve_context(cleaned)
        context = rag_service.build_context_block(chunks)

        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        user_content = cleaned
        # Inyecta el contexto de política si está disponible
        if context:
            user_content = f"Contexto de política:\n{context}\n\nPregunta del usuario:\n{cleaned}"

        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.2,
            max_tokens=350,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        # Extrae la respuesta y usa fallback si viene vacía
        answer = (response.choices[0].message.content or "").strip() or _fallback_answer()
        latency_ms = int((time.perf_counter() - started) * 1000)
        _audit(cleaned, answer, chunks=chunks, success=True, latency_ms=latency_ms, conversation_id=conversation_id)
        return answer
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fallo el asistente IA")
        latency_ms = int((time.perf_counter() - started) * 1000)
        fallback = (
            "No pude consultar la IA en este momento. "
            "Puedes elegir 1 en el menú para precalificar o 3 para un asesor."
        )
        _audit(
            cleaned,
            fallback,
            chunks=chunks,
            success=False,
            latency_ms=latency_ms,
            conversation_id=conversation_id,
            error=str(exc),
        )
        return fallback
