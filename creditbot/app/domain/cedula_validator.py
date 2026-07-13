"""Validación de cédula ecuatoriana (algoritmo módulo 10).

La cédula de una persona natural en Ecuador tiene 10 dígitos:
- Dígitos 1-2: código de provincia (01–24, o 30 para casos especiales/consulados).
- Dígito 3: menor a 6 para personas naturales (0–5).
- Dígitos 1-9: entran al cálculo del dígito verificador.
- Dígito 10: dígito verificador calculado con coeficientes [2,1,2,1,2,1,2,1,2].
"""

# Coeficientes aplicados a los primeros 9 dígitos para el algoritmo módulo 10.
_COEFFICIENTS = (2, 1, 2, 1, 2, 1, 2, 1, 2)

# Códigos de provincia válidos: 1–24 más 30 (consulados / casos especiales).
_MIN_PROVINCE = 1
_MAX_PROVINCE = 24
_SPECIAL_PROVINCE = 30

CEDULA_LENGTH = 10


def _expected_check_digit(first_nine: str) -> int:
    """Calcula el dígito verificador esperado a partir de los primeros 9 dígitos."""
    total = 0
    for digit_char, coefficient in zip(first_nine, _COEFFICIENTS):
        product = int(digit_char) * coefficient
        if product >= 10:
            product -= 9
        total += product
    remainder = total % 10
    return 0 if remainder == 0 else 10 - remainder


def is_valid_cedula(cedula: str) -> bool:
    """Retorna True si la cédula ecuatoriana es válida (formato + dígito verificador)."""
    valid, _ = validate_cedula(cedula)
    return valid


def validate_cedula(cedula: str) -> tuple[bool, str | None]:
    """Valida una cédula ecuatoriana.

    Retorna (True, None) si es válida, o (False, motivo) si no lo es.
    """
    if cedula is None:
        return False, "La cédula es obligatoria."

    cleaned = cedula.strip().replace("-", "").replace(" ", "")

    if not cleaned.isdigit():
        return False, "La cédula debe contener solo números."

    if len(cleaned) != CEDULA_LENGTH:
        return False, "La cédula debe tener 10 dígitos."

    province = int(cleaned[:2])
    if not (_MIN_PROVINCE <= province <= _MAX_PROVINCE or province == _SPECIAL_PROVINCE):
        return False, "El código de provincia de la cédula no es válido."

    third_digit = int(cleaned[2])
    if third_digit >= 6:
        return False, "El tercer dígito de la cédula no corresponde a una persona natural."

    if _expected_check_digit(cleaned[:9]) != int(cleaned[9]):
        return False, "El dígito verificador de la cédula no es válido."

    return True, None


def mask_cedula(cedula: str) -> str:
    """Enmascara la cédula para logs y auditoría (ej. '09******78')."""
    cleaned = (cedula or "").strip()
    if len(cleaned) <= 4:
        return "*" * len(cleaned)
    return cleaned[:2] + "*" * (len(cleaned) - 4) + cleaned[-2:]
