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
    assert calculate_estimated_payment(500, 12) == 41.67


def test_calculate_payment_capacity():
    assert calculate_payment_capacity(700) == 210.0


def test_evaluate_credit_request_preapproved():
    result = evaluate_credit_request(500, 12, 700)

    assert result["estimated_payment"] == 41.67
    assert result["payment_capacity"] == 210.0
    assert result["result"] == CREDIT_RESULT_PREAPPROVED


def test_evaluate_credit_request_observed():
    result = evaluate_credit_request(780, 12, 200)

    assert result["estimated_payment"] == 65.0
    assert result["payment_capacity"] == 60.0
    assert result["result"] == CREDIT_RESULT_OBSERVED


def test_evaluate_credit_request_not_qualified():
    result = evaluate_credit_request(4000, 12, 700)

    assert result["estimated_payment"] == 333.33
    assert result["payment_capacity"] == 210.0
    assert result["result"] == CREDIT_RESULT_NOT_QUALIFIED
