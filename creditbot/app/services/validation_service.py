"""Funciones de validación de entrada del usuario."""


def parse_numeric_value(value: str) -> float:
    """Convierte texto numérico a float, soportando coma decimal y separador de miles."""
    cleaned = value.strip().replace(" ", "")
    if "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            cleaned = parts[0].replace(".", "") + "." + parts[1]
        else:
            cleaned = cleaned.replace(",", "")
    elif "." in cleaned:
        integer_part, fractional_part = cleaned.rsplit(".", 1)
        if len(fractional_part) == 3 and integer_part.replace(".", "").isdigit():
            cleaned = cleaned.replace(".", "")
    return float(cleaned)


def validate_name(value: str) -> tuple[bool, str | None]:
    """Valida que el nombre tenga al menos 2 palabras o 5 caracteres."""
    cleaned = value.strip()
    if len(cleaned) < 5 and len(cleaned.split()) < 2:
        return False, "El nombre debe tener al menos 2 palabras o 5 caracteres."
    return True, None


def validate_amount(value: str) -> tuple[bool, str | None]:
    """Valida que el monto sea un número positivo."""
    try:
        amount = parse_numeric_value(value)
    except ValueError:
        return False, "El monto debe ser un número válido."

    if amount <= 0:
        return False, "El monto debe ser mayor a 0."

    return True, None


def validate_term(value: str) -> tuple[bool, str | None]:
    """Valida que el plazo sea un entero entre 3 y 36 meses."""
    try:
        term = int(value.strip())
    except ValueError:
        return False, "El plazo debe ser un número entero."

    if term < 3 or term > 36:
        return False, "El plazo debe estar entre 3 y 36 meses."

    return True, None


def validate_income(value: str) -> tuple[bool, str | None]:
    """Valida que el ingreso sea un número positivo."""
    try:
        income = parse_numeric_value(value)
    except ValueError:
        return False, "El ingreso debe ser un número válido."

    if income <= 0:
        return False, "El ingreso debe ser mayor a 0."

    return True, None


def validate_menu_option(value: str) -> tuple[bool, str | None]:
    """Valida que la opción del menú sea 1, 2 o 3."""
    cleaned = value.strip()
    if cleaned not in {"1", "2", "3"}:
        return False, "Selecciona una opción válida: 1, 2 o 3."
    return True, None


def validate_confirmation(value: str) -> tuple[bool, str | None]:
    """Valida que la confirmación sea 1 (Sí) o 2 (No)."""
    cleaned = value.strip()
    if cleaned not in {"1", "2"}:
        return False, "Selecciona una opción válida: 1 (Sí) o 2 (No)."
    return True, None
