"""Servicio de precalificación crediticia v2.

Orquesta las tres piezas del flujo v2 sin acoplarse al canal (WhatsApp) ni al LLM:
1. Valida la cédula ecuatoriana (app.domain.cedula_validator).
2. Consulta el perfil crediticio en el buró simulado (credit_profile_repository).
3. Aplica las reglas de negocio deterministas (app.domain.credit_rules).

Devuelve siempre un dict con la clave ``ok``. Si ``ok`` es False, ``error`` indica
el motivo (cedula_invalida). Si es True, incluye el resultado de la precalificación
y datos de presentación (cédula enmascarada, nombre, si tiene historial, etc.).
"""
import time
from typing import Any

from app.domain import credit_rules
from app.domain.cedula_validator import mask_cedula, validate_cedula
from app.repositories import audit_repository, credit_profile_repository

TOOL_NAME = "precalificar_por_cedula"


def _profile_flags(profile: dict[str, Any] | None) -> dict[str, Any]:
    """Extrae, con valores por defecto seguros, los campos del perfil que usan las reglas."""
    # Si no hay perfil (thin_file), retorna valores por defecto seguros
    if not profile:
        return {
            "score": 0,
            "cuotas_actuales": 0.0,
            "has_delinquency": False,
            "delinquency_days": 0,
            "lista_negra": False,
            "sin_historial": True,
            "full_name": None,
        }
    return {
        "score": int(profile.get("credit_score") or 0),
        "cuotas_actuales": float(profile.get("monthly_installments") or 0.0),
        "has_delinquency": bool(profile.get("has_delinquency")),
        "delinquency_days": int(profile.get("delinquency_days") or 0),
        "lista_negra": bool(profile.get("blacklisted")),
        "sin_historial": bool(profile.get("thin_file")),
        "full_name": profile.get("full_name"),
    }


def _audit(
    cedula: str,
    ingreso_neto: float,
    plazo_meses: int,
    monto_solicitado: float | None,
    resultado: dict[str, Any],
    started_at: float,
    conversation_id: str | None,
) -> None:
    """Registra la invocación en tool_audit_logs con la cédula enmascarada."""
    latency_ms = int((time.perf_counter() - started_at) * 1000)
    audit_repository.log_tool_call(
        TOOL_NAME,
        input_payload={
            "cedula": mask_cedula(cedula),
            "ingreso_neto": ingreso_neto,
            "plazo_meses": plazo_meses,
            "monto_solicitado": monto_solicitado,
        },
        output_payload={
            "ok": resultado.get("ok"),
            "result": resultado.get("result"),
            "categoria": resultado.get("categoria"),
            "monto_maximo": resultado.get("monto_maximo"),
            "error": resultado.get("error"),
        },
        success=bool(resultado.get("ok")),
        latency_ms=latency_ms,
        conversation_id=conversation_id,
    )


def precalificar_por_cedula(
    cedula: str,
    ingreso_neto: float,
    plazo_meses: int,
    monto_solicitado: float | None = None,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Ejecuta la precalificación completa a partir de una cédula.

    No lanza excepciones por datos del usuario: retorna siempre un dict con ``ok``.
    Cada invocación se audita en tool_audit_logs (cédula enmascarada).
    """
    started_at = time.perf_counter()

    # Paso 1: Valida la cédula ecuatoriana (algoritmo módulo 10)
    es_valida, motivo = validate_cedula(cedula)
    if not es_valida:
        resultado = {
            "ok": False,
            "error": "cedula_invalida",
            "motivo": motivo,
            "cedula_masked": mask_cedula(cedula),
        }
        _audit(cedula, ingreso_neto, plazo_meses, monto_solicitado, resultado, started_at, conversation_id)
        return resultado

    # Paso 2: Consulta el perfil crediticio en el buró simulado
    profile = credit_profile_repository.get_profile_by_cedula(cedula)
    flags = _profile_flags(profile)

    # Paso 3: Aplica las reglas de negocio deterministas
    calculo = credit_rules.precalificar(
        flags["score"],
        ingreso_neto,
        plazo_meses,
        cuotas_actuales=flags["cuotas_actuales"],
        has_delinquency=flags["has_delinquency"],
        delinquency_days=flags["delinquency_days"],
        lista_negra=flags["lista_negra"],
        sin_historial=flags["sin_historial"],
        monto_solicitado=monto_solicitado,
    )

    # Construye el resultado final con datos de presentación
    resultado = {
        "ok": True,
        "cedula_masked": mask_cedula(cedula),
        "full_name": flags["full_name"],
        "tiene_perfil": profile is not None,
        "sin_historial": flags["sin_historial"],
        "credit_score": flags["score"] if profile is not None else None,
        **calculo,
    }
    _audit(cedula, ingreso_neto, plazo_meses, monto_solicitado, resultado, started_at, conversation_id)
    return resultado
