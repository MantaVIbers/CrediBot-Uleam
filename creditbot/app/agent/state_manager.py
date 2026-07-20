"""Utilidades de control para la capa de IA y la máquina de estados."""
from app.core.constants import ASK_AMOUNT, ASK_CEDULA, ASK_INCOME, ASK_PURPOSE, ASK_TERM


EXPECTED_INPUTS = {
    ASK_CEDULA: "tu número de cédula de 10 dígitos",
    ASK_PURPOSE: "el destino del crédito, por ejemplo estudios o negocio",
    ASK_AMOUNT: "el monto que deseas solicitar en dólares",
    ASK_TERM: "el plazo que deseas en meses, entre 3 y 36",
    ASK_INCOME: "tu ingreso mensual aproximado en dólares",
}


def expected_input_for_state(state: str) -> str | None:
    """Describe el único dato que el flujo espera en un estado."""
    return EXPECTED_INPUTS.get(state)


def is_free_text_out_of_context(state: str, text: str) -> bool:
    """Distingue una explicación humana de un dato mal formado."""
    if state not in EXPECTED_INPUTS:
        return False
    cleaned = (text or "").strip()
    return len(cleaned) >= 8 and any(character.isalpha() for character in cleaned)
