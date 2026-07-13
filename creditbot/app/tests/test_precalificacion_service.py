"""Pruebas del servicio de precalificación v2.

Se mockea el repositorio de perfiles para aislar la orquestación (validación de
cédula + reglas de negocio) de la base de datos.
"""
from app.core.constants import (
    CREDIT_RESULT_NOT_QUALIFIED,
    CREDIT_RESULT_OBSERVED,
    CREDIT_RESULT_PREAPPROVED,
    SCORE_ACCEPTABLE,
    SCORE_EXCELLENT,
    SCORE_REGULAR,
)
from app.services import precalificacion_service as service

# Cédula ficticia pero válida (módulo 10), presente en el seed como 'aceptable'.
CEDULA_VALIDA = "0912345675"


def _stub_audit(monkeypatch):
    """Neutraliza la auditoría para aislar la lógica del servicio."""
    monkeypatch.setattr(
        service.audit_repository, "log_tool_call", lambda *a, **k: None
    )


def _patch_profile(monkeypatch, profile):
    _stub_audit(monkeypatch)
    monkeypatch.setattr(
        service.credit_profile_repository,
        "get_profile_by_cedula",
        lambda cedula: profile,
    )


def test_cedula_invalida_no_consulta_perfil(monkeypatch):
    """Una cédula inválida corta el flujo antes de tocar el repositorio."""
    _stub_audit(monkeypatch)

    def _boom(cedula):
        raise AssertionError("no debería consultar perfil con cédula inválida")

    monkeypatch.setattr(
        service.credit_profile_repository, "get_profile_by_cedula", _boom
    )

    result = service.precalificar_por_cedula("1234567890", 1000, 12)

    assert result["ok"] is False
    assert result["error"] == "cedula_invalida"
    assert result["cedula_masked"] == "12******90"


def test_perfil_excelente_preaprobado(monkeypatch):
    """Perfil excelente sin mora y cuota dentro de capacidad → preaprobado."""
    _patch_profile(
        monkeypatch,
        {
            "credit_score": 820,
            "full_name": "Carlos Ortiz Vera",
            "monthly_installments": 0.0,
            "has_delinquency": False,
            "delinquency_days": 0,
            "blacklisted": False,
            "thin_file": False,
        },
    )

    result = service.precalificar_por_cedula(CEDULA_VALIDA, 1500, 12)

    assert result["ok"] is True
    assert result["tiene_perfil"] is True
    assert result["categoria"] == SCORE_EXCELLENT
    assert result["credit_score"] == 820
    assert result["result"] == CREDIT_RESULT_PREAPPROVED
    assert result["monto_maximo"] > 0
    assert result["cedula_masked"] == "09******75"


def test_perfil_aceptable_es_elegible(monkeypatch):
    """Perfil aceptable es elegible y calcula tasa y monto."""
    _patch_profile(
        monkeypatch,
        {
            "credit_score": 650,
            "full_name": "Luis Mero Andrade",
            "monthly_installments": 110.0,
            "has_delinquency": False,
            "delinquency_days": 0,
            "blacklisted": False,
            "thin_file": False,
        },
    )

    result = service.precalificar_por_cedula(CEDULA_VALIDA, 1200, 24)

    assert result["ok"] is True
    assert result["categoria"] == SCORE_ACCEPTABLE
    assert result["elegible"] is True
    assert result["tea"] > 0


def test_perfil_regular_observado(monkeypatch):
    """Perfil regular siempre queda observado."""
    _patch_profile(
        monkeypatch,
        {
            "credit_score": 420,
            "full_name": "Jorge Cedeño Loor",
            "monthly_installments": 320.0,
            "has_delinquency": False,
            "delinquency_days": 0,
            "blacklisted": False,
            "thin_file": False,
        },
    )

    result = service.precalificar_por_cedula(CEDULA_VALIDA, 1000, 12)

    assert result["categoria"] == SCORE_REGULAR
    assert result["result"] == CREDIT_RESULT_OBSERVED


def test_mora_activa_no_elegible(monkeypatch):
    """Score alto pero con mora activa → no elegible y no cumple."""
    _patch_profile(
        monkeypatch,
        {
            "credit_score": 800,
            "full_name": "Tomás Freire Santos",
            "monthly_installments": 220.0,
            "has_delinquency": True,
            "delinquency_days": 60,
            "blacklisted": False,
            "thin_file": False,
        },
    )

    result = service.precalificar_por_cedula(CEDULA_VALIDA, 2000, 12)

    assert result["elegible"] is False
    assert result["motivo"] == "mora_activa"
    assert result["result"] == CREDIT_RESULT_NOT_QUALIFIED
    assert result["monto_maximo"] == 0.0


def test_sin_perfil_se_trata_como_sin_historial(monkeypatch):
    """Sin perfil en el buró → sin_historial (categoría regular, observado)."""
    _patch_profile(monkeypatch, None)

    result = service.precalificar_por_cedula(CEDULA_VALIDA, 1000, 12)

    assert result["ok"] is True
    assert result["tiene_perfil"] is False
    assert result["sin_historial"] is True
    assert result["credit_score"] is None
    assert result["categoria"] == SCORE_REGULAR
    assert result["result"] == CREDIT_RESULT_OBSERVED


def test_auditoria_registra_cedula_enmascarada(monkeypatch):
    """Cada precalificación registra la tool con la cédula enmascarada."""
    monkeypatch.setattr(
        service.credit_profile_repository, "get_profile_by_cedula", lambda cedula: None
    )
    registros = []
    monkeypatch.setattr(
        service.audit_repository,
        "log_tool_call",
        lambda name, **kwargs: registros.append((name, kwargs)),
    )

    service.precalificar_por_cedula(CEDULA_VALIDA, 1000, 12, conversation_id="conv-9")

    assert len(registros) == 1
    name, kwargs = registros[0]
    assert name == "precalificar_por_cedula"
    assert kwargs["conversation_id"] == "conv-9"
    assert kwargs["input_payload"]["cedula"] == "09******75"
    assert "0912345675" not in str(kwargs["input_payload"])
    assert kwargs["success"] is True


def test_thin_file_perfil_marca_sin_historial(monkeypatch):
    """Perfil con thin_file=True se trata como sin historial pese a tener score."""
    _patch_profile(
        monkeypatch,
        {
            "credit_score": 780,
            "full_name": "Pedro Salas Ochoa",
            "monthly_installments": 0.0,
            "has_delinquency": False,
            "delinquency_days": 0,
            "blacklisted": False,
            "thin_file": True,
        },
    )

    result = service.precalificar_por_cedula(CEDULA_VALIDA, 1000, 12)

    assert result["sin_historial"] is True
    assert result["categoria"] == SCORE_REGULAR
