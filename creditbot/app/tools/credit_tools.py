"""Tools de negocio seguras para CrediBot.

Las operaciones que cambian datos son ejecutadas por la máquina de estados,
nunca por texto libre del modelo. Estas funciones entregan contexto auditable.
"""
from time import perf_counter
from typing import Any

from app.domain.cedula_validator import mask_cedula, validate_cedula
from app.repositories import audit_repository, credit_profile_repository
from app.services import rag_service


def _audit(
    name: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    conversation_id: str | None = None,
) -> None:
    audit_repository.log_tool_call(
        name,
        input_payload=input_payload,
        output_payload=output_payload,
        conversation_id=conversation_id,
    )


def validar_cedula(cedula: str, conversation_id: str | None = None) -> dict[str, Any]:
    """Valida formato y dígito verificador sin guardar la cédula."""
    start = perf_counter()
    valid, reason = validate_cedula(cedula)
    result = {"valid": valid, "reason": reason}
    audit_repository.log_tool_call(
        "validar_cedula",
        input_payload={"cedula": mask_cedula(cedula)},
        output_payload=result,
        latency_ms=int((perf_counter() - start) * 1000),
        conversation_id=conversation_id,
    )
    return result


def consultar_perfil_crediticio(cedula: str, conversation_id: str | None = None) -> dict[str, Any]:
    """Consulta el perfil simulado y devuelve solo datos mínimos del flujo."""
    profile = credit_profile_repository.get_profile_by_cedula(cedula)
    result = {
        "found": bool(profile),
        "score_category": profile.get("score_category") if profile else None,
    }
    _audit(
        "consultar_perfil_crediticio",
        {"cedula": mask_cedula(cedula)},
        result,
        conversation_id,
    )
    return result


def calcular_monto_maximo(income: float, monthly_installments: float = 0) -> dict[str, Any]:
    """Calcula capacidad estimada; no constituye una aprobación."""
    amount = max(0.0, (float(income) * 0.35 - float(monthly_installments)) * 12)
    result = {"estimated_max_amount": round(amount, 2), "informative": True}
    _audit("calcular_monto_maximo", {"income": income}, result)
    return result


def registrar_solicitud() -> dict[str, str]:
    """Indica que registrar datos es responsabilidad del flujo validado."""
    result = {"status": "requires_state_machine"}
    _audit("registrar_solicitud", {}, result)
    return result


def derivar_a_asesor() -> dict[str, str]:
    """Indica que la derivación requiere petición explícita o regla backend."""
    result = {"status": "requires_explicit_request_or_backend_rule"}
    _audit("derivar_a_asesor", {}, result)
    return result


def obtener_politica_credito(question: str, conversation_id: str | None = None) -> dict[str, Any]:
    """Recupera información desde las políticas internas RAG."""
    answer, chunks = rag_service.build_policy_answer(question)
    result = {"answer": answer, "sources": [chunk.source for chunk in chunks]}
    _audit("obtener_politica_credito", {"question": question[:300]}, result, conversation_id)
    return result


def tools_for_agent(safe_only: bool = False) -> list[Any]:
    """Lista de tools expuesta a Agno para consultas controladas.

    En texto libre se omite la consulta de perfil: así ninguna llamada del
    modelo puede revelar datos crediticios antes de la validación del backend.
    """
    tools: list[Any] = [
        validar_cedula,
        calcular_monto_maximo,
        registrar_solicitud,
        derivar_a_asesor,
        obtener_politica_credito,
    ]
    if not safe_only:
        tools.insert(1, consultar_perfil_crediticio)
    return tools
