"""Agente OpenAI con function calling para el modo INFO_AI (RF-07).

El agente puede invocar tools de negocio auditables; no calcula montos ni scores
por sí mismo: delega en reglas deterministas y RAG documentado.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.core.config import settings
from app.core.constants import (
    SCORE_ACCEPTABLE,
    SCORE_EXCELLENT,
    SCORE_HIGH_RISK,
    SCORE_REGULAR,
)
from app.domain import credit_rules
from app.domain.cedula_validator import mask_cedula, validate_cedula
from app.repositories import audit_repository
from app.services import rag_service

logger = logging.getLogger(__name__)

AGENT_TOOL_NAME = "agente_openai_tools"
# Número máximo de iteraciones tool-calling antes de forzar respuesta final
MAX_TOOL_ROUNDS = 5

AGENT_SYSTEM_PROMPT = """Eres CrediBot, asistente de precalificación crediticia de ULEAM (demo académica).
Responde en español, claro y breve (máximo 6 oraciones).
Usa las tools disponibles cuando necesites validar cédulas, consultar política o explicar reglas.
No inventes montos, tasas ni scores: apóyate en los resultados de las tools.
Recuerda: esto es precalificación simulada, no una aprobación final.
Si preguntan cómo precalificar, indica que en el menú principal pueden elegir la opción 1."""

# Definición de tools disponibles para el agente OpenAI
OPENAI_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "consultar_politica_credito",
            "description": "Recupera fragmentos de la política de crédito relevantes a una pregunta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pregunta": {
                        "type": "string",
                        "description": "Pregunta o tema sobre políticas de crédito o precalificación.",
                    }
                },
                "required": ["pregunta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validar_cedula",
            "description": "Valida una cédula ecuatoriana de persona natural (algoritmo módulo 10).",
            "parameters": {
                "type": "object",
                "properties": {
                    "cedula": {
                        "type": "string",
                        "description": "Número de cédula de 10 dígitos.",
                    }
                },
                "required": ["cedula"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explicar_reglas_credito",
            "description": "Explica las reglas deterministas de precalificación (score, tasas, capacidad).",
            "parameters": {
                "type": "object",
                "properties": {
                    "tema": {
                        "type": "string",
                        "description": "Tema opcional: score, tasas, capacidad, elegibilidad o general.",
                    }
                },
            },
        },
    },
]


def is_agent_enabled() -> bool:
    """True si hay API key de OpenAI para el agente."""
    return bool(settings.openai_api_key.strip())


def _fallback_answer() -> str:
    return (
        "CrediBot te ayuda a precalificar crédito por WhatsApp con reglas claras y un buró simulado. "
        "En el menú elige 1 para iniciar la precalificación, 2 para preguntar sobre políticas "
        "(requiere OpenAI configurado) o 3 para hablar con un asesor."
    )


def _audit_subtool(
    tool_name: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    *,
    success: bool,
    latency_ms: int,
    conversation_id: str | None,
) -> None:
    audit_repository.log_tool_call(
        tool_name,
        input_payload=input_payload,
        output_payload=output_payload,
        success=success,
        latency_ms=latency_ms,
        conversation_id=conversation_id,
    )


def _tool_consultar_politica_credito(pregunta: str, conversation_id: str | None) -> dict[str, Any]:
    started = time.perf_counter()
    cleaned = pregunta.strip()
    chunks: list[str] = []
    try:
        if rag_service.is_rag_available():
            chunks = rag_service.retrieve_context(cleaned)
        context = rag_service.build_context_block(chunks)
        result = {
            "fragmentos_encontrados": len(chunks),
            "contexto": context[:2500] if context else "Sin contexto disponible.",
        }
        latency_ms = int((time.perf_counter() - started) * 1000)
        _audit_subtool(
            "consultar_politica_credito",
            {"pregunta": cleaned[:500]},
            {"fragmentos": len(chunks), "contexto_chars": len(context)},
            success=True,
            latency_ms=latency_ms,
            conversation_id=conversation_id,
        )
        return result
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((time.perf_counter() - started) * 1000)
        _audit_subtool(
            "consultar_politica_credito",
            {"pregunta": cleaned[:500]},
            {"error": str(exc)},
            success=False,
            latency_ms=latency_ms,
            conversation_id=conversation_id,
        )
        return {"error": str(exc), "fragmentos_encontrados": 0, "contexto": ""}


def _tool_validar_cedula(cedula: str, conversation_id: str | None) -> dict[str, Any]:
    started = time.perf_counter()
    es_valida, motivo = validate_cedula(cedula)
    result = {
        "valida": es_valida,
        "motivo": motivo,
        "cedula_masked": mask_cedula(cedula),
    }
    latency_ms = int((time.perf_counter() - started) * 1000)
    _audit_subtool(
        "validar_cedula",
        {"cedula": mask_cedula(cedula)},
        {"valida": es_valida, "motivo": motivo},
        success=True,
        latency_ms=latency_ms,
        conversation_id=conversation_id,
    )
    return result


def _tool_explicar_reglas_credito(tema: str | None, conversation_id: str | None) -> dict[str, Any]:
    started = time.perf_counter()
    # Normaliza el tema: si no se especifica, usa "general"
    normalized = (tema or "general").strip().lower()
    # Construye el diccionario completo de reglas de negocio
    reglas: dict[str, Any] = {
        "categorias_score": {
            SCORE_EXCELLENT: "750-999",
            SCORE_ACCEPTABLE: "550-749",
            SCORE_REGULAR: "349-549",
            SCORE_HIGH_RISK: "1-348",
        },
        "tasas_tea_referenciales": credit_rules.TASA_POR_CATEGORIA,
        "multiplicador_monto_por_categoria": credit_rules.MULTIPLICADOR_MONTO,
        "capacidad_pago": f"Hasta {int(credit_rules.CAPACITY_RATIO * 100)}% del ingreso neto menos cuotas vigentes.",
        "mora_maxima_dias": credit_rules.MAX_DELINQUENCY_DAYS,
        "plazos_validos_meses": "3 a 36",
        "resultados_posibles": ["preaprobado", "observado", "no_cumple"],
    }
    # Mapeo de temas del usuario a claves del diccionario de reglas
    tema_keys = {
        "score": "categorias_score",
        "tasas": "tasas_tea_referenciales",
        "capacidad": "capacidad_pago",
        "elegibilidad": "mora_maxima_dias",
    }
    # Filtra las reglas según el tema solicitado
    if normalized != "general":
        key = tema_keys.get(normalized)
        if key:
            payload = {"tema": normalized, "reglas": {key: reglas[key]}}
        else:
            payload = {"tema": normalized, "reglas": {"mensaje": "Tema no reconocido; usa general."}}
    else:
        # Tema "general": retorna todas las reglas disponibles
        payload = {"tema": "general", "reglas": reglas}

    latency_ms = int((time.perf_counter() - started) * 1000)
    _audit_subtool(
        "explicar_reglas_credito",
        {"tema": normalized},
        {"keys": list(payload["reglas"].keys()) if isinstance(payload["reglas"], dict) else []},
        success=True,
        latency_ms=latency_ms,
        conversation_id=conversation_id,
    )
    return payload


# Despacha la llamada a la tool correspondiente según el nombre
def _dispatch_tool(name: str, arguments: dict[str, Any], conversation_id: str | None) -> dict[str, Any]:
    if name == "consultar_politica_credito":
        return _tool_consultar_politica_credito(arguments.get("pregunta", ""), conversation_id)
    if name == "validar_cedula":
        return _tool_validar_cedula(arguments.get("cedula", ""), conversation_id)
    if name == "explicar_reglas_credito":
        return _tool_explicar_reglas_credito(arguments.get("tema"), conversation_id)
    return {"error": f"Tool desconocida: {name}"}


def _audit_agent_run(
    question: str,
    answer: str,
    *,
    tools_used: list[str],
    success: bool,
    latency_ms: int,
    conversation_id: str | None,
    error: str | None = None,
) -> None:
    audit_repository.log_tool_call(
        AGENT_TOOL_NAME,
        input_payload={"pregunta": question[:500]},
        output_payload={
            "respuesta": answer[:1000],
            "tools_invocadas": tools_used,
            "error": error,
        },
        success=success,
        latency_ms=latency_ms,
        conversation_id=conversation_id,
    )


def answer_question(question: str, conversation_id: str | None = None) -> str:
    """Responde en modo INFO_AI usando agente OpenAI con function calling."""
    cleaned = question.strip()
    if not cleaned:
        return "Escribe tu pregunta sobre crédito o precalificación."

    if not is_agent_enabled():
        return _fallback_answer()

    started = time.perf_counter()
    tools_used: list[str] = []
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": cleaned},
        ]

        # Loop principal de function calling: el agente puede llamar tools hasta MAX_TOOL_ROUNDS veces
        answer = _fallback_answer()
        for _ in range(MAX_TOOL_ROUNDS):
            response = client.chat.completions.create(
                model=settings.openai_model,
                temperature=0.2,
                max_tokens=400,
                messages=messages,
                tools=OPENAI_TOOLS,
            )
            message = response.choices[0].message
            # Si no hay tool_calls, el agente dio la respuesta final
            if not message.tool_calls:
                answer = (message.content or "").strip() or _fallback_answer()
                break

            # Agrega la respuesta del asistente al historial de mensajes
            messages.append(message.model_dump(exclude_none=True))
            # Ejecuta cada tool invocada y agrega el resultado al historial
            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                try:
                    fn_args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    fn_args = {}
                tools_used.append(fn_name)
                tool_result = _dispatch_tool(fn_name, fn_args, conversation_id)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                )

        latency_ms = int((time.perf_counter() - started) * 1000)
        _audit_agent_run(
            cleaned,
            answer,
            tools_used=tools_used,
            success=True,
            latency_ms=latency_ms,
            conversation_id=conversation_id,
        )
        return answer
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fallo el agente OpenAI")
        latency_ms = int((time.perf_counter() - started) * 1000)
        fallback = (
            "No pude consultar la IA en este momento. "
            "Puedes elegir 1 en el menú para precalificar o 3 para un asesor."
        )
        _audit_agent_run(
            cleaned,
            fallback,
            tools_used=tools_used,
            success=False,
            latency_ms=latency_ms,
            conversation_id=conversation_id,
            error=str(exc),
        )
        return fallback
