"""Lógica de evaluación crediticia (precalificación)."""
from app.core.constants import (
    CREDIT_RESULT_NOT_QUALIFIED,
    CREDIT_RESULT_OBSERVED,
    CREDIT_RESULT_PREAPPROVED,
)


def calculate_estimated_payment(amount: float, term_months: int) -> float:
    """Calcula la cuota estimada dividiendo el monto entre el plazo."""
    return round(amount / term_months, 2)


def calculate_payment_capacity(monthly_income: float) -> float:
    """Calcula el 30% del ingreso mensual como capacidad de pago."""
    return round(monthly_income * 0.30, 2)


def evaluate_credit_request(
    amount: float, term_months: int, monthly_income: float
) -> dict[str, float | str]:
    """Evalúa la solicitud y retorna cuota estimada, capacidad y resultado."""
    estimated_payment = calculate_estimated_payment(amount, term_months)
    payment_capacity = calculate_payment_capacity(monthly_income)

    if estimated_payment <= payment_capacity:
        result = CREDIT_RESULT_PREAPPROVED
    elif estimated_payment <= payment_capacity * 1.20:
        result = CREDIT_RESULT_OBSERVED
    else:
        result = CREDIT_RESULT_NOT_QUALIFIED

    return {
        "estimated_payment": estimated_payment,
        "payment_capacity": payment_capacity,
        "result": result,
    }
