"""Normaliza respuestas en lenguaje natural del usuario usando OpenAI.

Se usa en cada paso del flujo (monto, plazo, ingreso, menú, sí/no, etc.)
antes de la validación determinista. El LLM solo traduce texto → valor
estructurado; las reglas de negocio siguen en validation_service y credit_rules.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from app.core.config import settings
from app.repositories import audit_repository

logger = logging.getLogger(__name__)

TOOL_NAME = "normalizar_entrada_usuario"

# Instrucciones específicas para cada campo que el LLM debe normalizar
FIELD_PROMPTS: dict[str, str] = {
    "menu_option": (
        "Opciones: 1=precalificar crédito, 2=información general, 3=hablar con asesor. "
        "Devuelve solo 1, 2 o 3."
    ),
    "confirmation": (
        "Opciones: 1=sí/autorizo/acepto/confirmo, 2=no/rechazo/cancelo. Devuelve solo 1 o 2."
    ),
    "name": "Extrae el nombre completo de la persona. Devuelve solo el nombre.",
    "cedula": (
        "Extrae la cédula ecuatoriana de 10 dígitos. Devuelve solo los 10 dígitos, sin guiones."
    ),
    "amount": (
        "Extrae el monto solicitado en dólares como número (sin símbolo). "
        "Ej: 'cinco mil' → 5000, 'USD 1.200' → 1200."
    ),
    "term_months": (
        "Extrae el plazo en MESES como entero. "
        "Ej: 'un año' → 12, 'dos años' → 24, '18 meses' → 18, 'medio año' → 6."
    ),
    "income": (
        "Extrae el ingreso mensual en dólares como número (sin símbolo). "
        "Ej: 'mil quinientos' → 1500."
    ),
}

# Atajos locales sin llamar a OpenAI (más rápido y barato).
_TERM_HINTS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"\bun\s+a[nñ]o\b|\b1\s+a[nñ]o\b|\bdoce\s+meses\b", re.I), 12),
    (re.compile(r"\bdos\s+a[nñ]os\b|\b2\s+a[nñ]os\b|\bveinticuatro\s+meses\b", re.I), 24),
    (re.compile(r"\btres\s+a[nñ]os\b|\b3\s+a[nñ]os\b|\btreinta\s+y\s+seis\s+meses\b", re.I), 36),
    (re.compile(r"\bseis\s+meses\b|\bmedio\s+a[nñ]o\b", re.I), 6),
    (re.compile(r"\bdieciocho\s+meses\b|\bun\s+a[nñ]o\s+y\s+medio\b", re.I), 18),
]

_CONFIRM_YES = re.compile(
    r"^(si|sí|yes|ok|dale|claro|autorizo|acepto|confirmo|de\s+acuerdo|1)$",
    re.I,
)
_CONFIRM_NO = re.compile(r"^(no|nop|negativo|rechazo|cancelo|2)$", re.I)

_MENU_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(1|precalif\w*|credito|crédito|solicitud)\b", re.I), "1"),
    (re.compile(r"\b(2|info\w*|informaci\w*)\b", re.I), "2"),
    (re.compile(r"\b(3|asesor|humano|persona)\b", re.I), "3"),
]


def is_enabled() -> bool:
    return bool(settings.openai_api_key.strip())


def _local_normalize(field: str, text: str) -> str | None:
    """Reglas rápidas sin IA."""
    cleaned = text.strip()
    if not cleaned:
        return None

    # Normalización de plazo: busca patrones como "un año", "dos años", etc.
    if field == "term_months":
        for pattern, months in _TERM_HINTS:
            if pattern.search(cleaned):
                return str(months)
        # Intenta extraer directamente un número seguido de "meses"
        match = re.search(r"(\d+)\s*meses?", cleaned, re.I)
        if match:
            return match.group(1)

    # Normalización de confirmación: acepta "sí", "ok", "autorizo", etc.
    if field == "confirmation":
        if _CONFIRM_YES.match(cleaned):
            return "1"
        if _CONFIRM_NO.match(cleaned):
            return "2"

    # Normalización de opción de menú: 1=precalificar, 2=info, 3=asesor
    if field == "menu_option":
        for pattern, option in _MENU_HINTS:
            if pattern.search(cleaned):
                return option

    # Normalización de cédula: extrae solo dígitos y valida longitud
    if field == "cedula":
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) == 10:
            return digits

    # Normalización de montos: elimina símbolos y formato de moneda
    if field in {"amount", "income"}:
        numeric = cleaned.replace("$", "").replace("USD", "").replace("usd", "")
        # Maneja formato europeo (1.200,50) vs formato US (1,200.50)
        numeric = numeric.replace(".", "").replace(",", ".") if re.search(r"\d,\d", numeric) else numeric
        match = re.search(r"(\d+(?:\.\d+)?)", numeric.replace(" ", ""))
        if match:
            return match.group(1)

    return None


def _audit(
    field: str,
    raw: str,
    normalized: str,
    *,
    success: bool,
    latency_ms: int,
    conversation_id: str | None,
    source: str,
    error: str | None = None,
) -> None:
    audit_repository.log_tool_call(
        TOOL_NAME,
        input_payload={"campo": field, "texto_original": raw[:500]},
        output_payload={
            "valor_normalizado": normalized[:200],
            "fuente": source,
            "error": error,
        },
        success=success,
        latency_ms=latency_ms,
        conversation_id=conversation_id,
    )


def _normalize_with_openai(field: str, text: str) -> str | None:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    instruction = FIELD_PROMPTS[field]
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        max_tokens=80,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un parser de formularios. Devuelve JSON: "
                    '{"value": "<valor normalizado>"} o {"value": null} si no puedes interpretar. '
                    f"Campo: {field}. {instruction}"
                ),
            },
            {"role": "user", "content": text.strip()},
        ],
    )
    content = (response.choices[0].message.content or "").strip()
    data = json.loads(content)
    value = data.get("value")
    if value is None:
        return None
    return str(value).strip()


def normalize_user_input(
    text: str,
    field: str,
    conversation_id: str | None = None,
) -> str:
    """Devuelve texto normalizado para validar; si no puede, retorna el original."""
    raw = text.strip()
    if not raw or field not in FIELD_PROMPTS:
        return text

    # Primero intenta normalizar con reglas locales (rápido y sin costo)
    local = _local_normalize(field, raw)
    if local:
        _audit(field, raw, local, success=True, latency_ms=0, conversation_id=conversation_id, source="local")
        return local

    # Si OpenAI no está configurado, retorna el texto original
    if not is_enabled():
        return text

    # Si las reglas locales fallaron, intenta con OpenAI
    started = time.perf_counter()
    try:
        ai_value = _normalize_with_openai(field, raw)
        latency_ms = int((time.perf_counter() - started) * 1000)
        if ai_value:
            _audit(
                field,
                raw,
                ai_value,
                success=True,
                latency_ms=latency_ms,
                conversation_id=conversation_id,
                source="openai",
            )
            return ai_value
        _audit(
            field,
            raw,
            raw,
            success=False,
            latency_ms=latency_ms,
            conversation_id=conversation_id,
            source="openai",
            error="sin_valor",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo normalizar con IA el campo %s: %s", field, exc)
        latency_ms = int((time.perf_counter() - started) * 1000)
        _audit(
            field,
            raw,
            raw,
            success=False,
            latency_ms=latency_ms,
            conversation_id=conversation_id,
            source="openai",
            error=str(exc),
        )
    return text
