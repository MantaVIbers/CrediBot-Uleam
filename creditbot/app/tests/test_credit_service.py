"""Pruebas del servicio de evaluación crediticia."""
from app.core.constants import (
    CREDIT_RESULT_NOT_QUALIFIED,
    CREDIT_RESULT_OBSERVED,
    CREDIT_RESULT_PREAPPROVED,
)
from app.services.credit_service import (
    calculate_estimated_payment,
    calculate_payment_capacity,
    evaluate_credit_request,
)


def test_calculate_estimated_payment():
    """Verifica el cálculo de la cuota estimada."""
    assert calculate_estimated_payment(500, 12) == 41.67


def test_calculate_payment_capacity():
    """Verifica el cálculo del 30% del ingreso como capacidad de pago."""
    assert calculate_payment_capacity(700) == 210.0


def test_evaluate_credit_request_preapproved():
    """Caso donde la cuota estimada es menor o igual a la capacidad de pago."""
    result = evaluate_credit_request(500, 12, 700)

    assert result["estimated_payment"] == 41.67
    assert result["payment_capacity"] == 210.0
    assert result["result"] == CREDIT_RESULT_PREAPPROVED


def test_evaluate_credit_request_observed():
    """Caso donde la cuota supera la capacidad pero está dentro del 20% adicional."""
    result = evaluate_credit_request(780, 12, 200)

    assert result["estimated_payment"] == 65.0
    assert result["payment_capacity"] == 60.0
    assert result["result"] == CREDIT_RESULT_OBSERVED


def test_evaluate_credit_request_not_qualified():
    """Caso donde la cuota supera la capacidad de pago en más del 20%."""
    result = evaluate_credit_request(4000, 12, 700)

    assert result["estimated_payment"] == 333.33
    assert result["payment_capacity"] == 210.0
    assert result["result"] == CREDIT_RESULT_NOT_QUALIFIED
