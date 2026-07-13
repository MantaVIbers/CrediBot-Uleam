"""Auditoría de invocaciones de tools del agente (tabla tool_audit_logs, RNF-04).

La auditoría es best-effort: si el registro falla no debe interrumpir la
conversación, por lo que las excepciones se capturan y se registran en el log.
IMPORTANTE: los payloads deben llegar ya enmascarados (sin cédula en claro).
"""
import logging
from typing import Any

from app.repositories.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def log_tool_call(
    tool_name: str,
    *,
    input_payload: dict[str, Any] | None = None,
    output_payload: dict[str, Any] | None = None,
    success: bool = True,
    latency_ms: int | None = None,
    conversation_id: str | None = None,
) -> dict[str, Any] | None:
    """Registra la invocación de una tool. Retorna la fila creada o None si falla."""
    # Construye el payload base de auditoría
    payload: dict[str, Any] = {
        "tool_name": tool_name,
        "input_payload": input_payload,
        "output_payload": output_payload,
        "success": success,
    }
    # Agrega campos opcionales solo si se proporcionaron
    if latency_ms is not None:
        payload["latency_ms"] = latency_ms
    if conversation_id is not None:
        payload["conversation_id"] = conversation_id

    try:
        response = (
            get_supabase_client().table("tool_audit_logs").insert(payload).execute()
        )
        return response.data[0] if response.data else None
    except Exception:  # noqa: BLE001 - la auditoría nunca debe romper el flujo
        # Registra el error pero no interrumpe la conversación (best-effort)
        logger.warning("No se pudo registrar la auditoría de la tool '%s'", tool_name)
        return None
