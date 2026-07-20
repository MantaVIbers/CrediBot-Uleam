"""Agente OpenAI para redactar respuestas del bot.

La maquina de estados y las reglas siguen viviendo en el backend. Este modulo
solo toma una respuesta base ya validada y la redacta con tono natural.
"""
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_last_request_status = "not_attempted"
_last_error_type: str | None = None


SYSTEM_PROMPT = """
Eres CrediBot, asistente de precalificacion de credito por WhatsApp.
Responde en espanol claro, cercano y profesional.

Reglas obligatorias:
- No cambies montos, plazos, score, categoria, resultado ni opciones numericas.
- No inventes aprobaciones, requisitos, tasas ni datos de buro.
- Si hay contexto RAG, responde solo con esa informacion y no agregues condiciones nuevas.
- Si hay paso pendiente, conserva esa instruccion para que el usuario sepa como continuar.
- Mantén la respuesta corta, apta para WhatsApp.
- Si hay opciones numeradas, conserva exactamente su significado.
- Si el texto base deriva a asesor, no ofrezcas continuar automaticamente.
- Si el estado anterior es ASK_PURPOSE y el objetivo es ASK_AMOUNT, responde de
  forma cálida y natural: menciona el nombre y el propósito expresado, sin
  prometer una aprobación, y termina preguntando el monto de forma cercana.
- No copies literalmente la respuesta base: reescríbela como un mensaje breve,
  humano y empático, manteniendo exactamente los datos y la pregunta final.
""".strip()


def _is_configured() -> bool:
    """Indica si la IA puede usarse en este entorno."""
    return bool(settings.openai_enable_ai and settings.openai_api_key)


def runtime_status() -> dict[str, str | None]:
    """Expone diagnóstico mínimo de IA sin revelar claves ni mensajes privados."""
    return {
        "last_request_status": _last_request_status,
        "last_error_type": _last_error_type,
    }


def _format_context(context: dict[str, Any] | None) -> str:
    """Convierte el contexto seguro a texto explícito para el modelo."""
    if not context:
        return "Sin contexto adicional."

    lines = []
    if context.get("state_before"):
        lines.append(f"Estado anterior: {context['state_before']}")
    if context.get("state_after"):
        lines.append(f"Estado objetivo: {context['state_after']}")
    if context.get("pending_step"):
        lines.append(f"Paso pendiente para continuar: {context['pending_step']}")

    rag_context = context.get("rag_context") or []
    if rag_context:
        lines.append("Contexto RAG permitido:")
        for item in rag_context:
            lines.append(
                "- "
                f"{item.get('title', 'Sin titulo')} "
                f"({item.get('source', 'sin fuente')}): "
                f"{item.get('content', '')}"
            )

    rag_sources = context.get("rag_sources") or []
    if rag_sources:
        lines.append(f"Fuentes RAG: {rag_sources}")

    if context.get("conversation_id"):
        lines.append(f"conversation_id: {context['conversation_id']}")

    return "\n".join(lines) if lines else "Sin contexto adicional."


def render_reply(
    *,
    base_reply: str,
    state: str,
    user_message: str,
    context: dict[str, Any] | None = None,
) -> str:
    """Redacta una respuesta con OpenAI, o devuelve la base si no aplica.

    La respuesta base es siempre la fuente de verdad. Si OpenAI no esta
    configurado o falla, el flujo sigue funcionando con el texto determinista.
    """
    global _last_request_status, _last_error_type

    if not base_reply:
        return base_reply
    if not _is_configured():
        _last_request_status = "not_configured"
        _last_error_type = None
        return base_reply

    try:
        from openai import OpenAI

        # El webhook no debe quedar bloqueado si la IA tarda o no está disponible.
        client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_request_timeout_seconds,
            max_retries=0,
        )
        response = client.responses.create(
            model=settings.openai_model,
            instructions=SYSTEM_PROMPT,
            input=(
                f"Estado actual: {state}\n"
                f"Mensaje del usuario: {user_message}\n"
                f"{_format_context(context)}\n\n"
                "Redacta esta respuesta base sin cambiar su informacion:\n"
                f"{base_reply}"
            ),
            max_output_tokens=220,
        )
        rendered = (getattr(response, "output_text", "") or "").strip()
        if rendered:
            _last_request_status = "success"
            _last_error_type = None
            return rendered
        _last_request_status = "empty_response"
        _last_error_type = None
        return base_reply
    except Exception as exc:  # pragma: no cover - defensa para no tumbar WhatsApp
        logger.warning("No se pudo generar respuesta con OpenAI: %s", exc)
        _last_request_status = "failed"
        _last_error_type = type(exc).__name__
        return base_reply
