def validate_name(value: str) -> tuple[bool, str | None]:
    cleaned = value.strip()
    if len(cleaned) < 5 and len(cleaned.split()) < 2:
        return False, "El nombre debe tener al menos 2 palabras o 5 caracteres."
    return True, None


def validate_amount(value: str) -> tuple[bool, str | None]:
    try:
        amount = float(value.replace(",", ".").strip())
    except ValueError:
        return False, "El monto debe ser un número válido."

    if amount <= 0:
        return False, "El monto debe ser mayor a 0."

    return True, None


def validate_term(value: str) -> tuple[bool, str | None]:
    try:
        term = int(value.strip())
    except ValueError:
        return False, "El plazo debe ser un número entero."

    if term < 3 or term > 36:
        return False, "El plazo debe estar entre 3 y 36 meses."

    return True, None


def validate_income(value: str) -> tuple[bool, str | None]:
    try:
        income = float(value.replace(",", ".").strip())
    except ValueError:
        return False, "El ingreso debe ser un número válido."

    if income <= 0:
        return False, "El ingreso debe ser mayor a 0."

    return True, None


def validate_menu_option(value: str) -> tuple[bool, str | None]:
    cleaned = value.strip()
    if cleaned not in {"1", "2", "3"}:
        return False, "Selecciona una opción válida: 1, 2 o 3."
    return True, None


def validate_confirmation(value: str) -> tuple[bool, str | None]:
    cleaned = value.strip()
    if cleaned not in {"1", "2"}:
        return False, "Selecciona una opción válida: 1 (Sí) o 2 (No)."
    return True, None
