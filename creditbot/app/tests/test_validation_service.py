"""Pruebas del servicio de validación de entrada del usuario."""
from app.services.validation_service import (
    validate_amount,
    validate_confirmation,
    validate_income,
    validate_menu_option,
    validate_name,
    validate_purpose,
    validate_term,
)


def test_validate_amount_correct():
    """Monto válido."""
    is_valid, error = validate_amount("500")
    assert is_valid is True
    assert error is None


def test_validate_amount_invalid():
    """Monto no numérico y monto cero."""
    is_valid, error = validate_amount("abc")
    assert is_valid is False
    assert error is not None

    is_valid, error = validate_amount("0")
    assert is_valid is False
    assert error is not None


def test_validate_term_correct():
    """Plazo válido."""
    is_valid, error = validate_term("12")
    assert is_valid is True
    assert error is None


def test_validate_term_natural_language():
    """Plazo en frases naturales."""
    from app.services.validation_service import parse_term_value

    assert parse_term_value("12 meses") == 12
    assert parse_term_value("en 12 plazos") == 12
    is_valid, error = validate_term("en 12 plazos")
    assert is_valid is True
    assert error is None


def test_validate_term_invalid():
    """Plazo fuera de rango y no numérico."""
    is_valid, error = validate_term("2")
    assert is_valid is False
    assert error is not None

    is_valid, error = validate_term("abc")
    assert is_valid is False
    assert error is not None


def test_validate_name_correct():
    """Nombre con al menos 2 palabras."""
    is_valid, error = validate_name("Carlos Ortiz")
    assert is_valid is True
    assert error is None


def test_validate_income_correct():
    """Ingreso válido."""
    is_valid, error = validate_income("700")
    assert is_valid is True
    assert error is None


def test_validate_purpose_correct():
    """Destino del crédito válido."""
    is_valid, error = validate_purpose("estudios")
    assert is_valid is True
    assert error is None


def test_validate_purpose_invalid():
    """Destino del crédito demasiado corto."""
    is_valid, error = validate_purpose("x")
    assert is_valid is False
    assert error is not None


def test_validate_menu_option_correct():
    """Opción de menú 1."""
    is_valid, error = validate_menu_option("1")
    assert is_valid is True
    assert error is None


def test_validate_confirmation_correct():
    """Confirmación 1."""
    is_valid, error = validate_confirmation("1")
    assert is_valid is True
    assert error is None


def test_validate_amount_with_thousands_separator():
    """Monto con separador de miles (coma)."""
    is_valid, error = validate_amount("1,000")
    assert is_valid is True
    assert error is None


def test_parse_numeric_value_thousands():
    """Verifica el parseo correcto de valores con separador de miles."""
    from app.services.validation_service import parse_numeric_value

    assert parse_numeric_value("1,000") == 1000.0
    assert parse_numeric_value("1.500") == 1500.0
    assert parse_numeric_value("500,50") == 500.5
