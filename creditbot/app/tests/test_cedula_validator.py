"""Pruebas del validador de cédula ecuatoriana (módulo 10)."""
from app.domain.cedula_validator import (
    is_valid_cedula,
    mask_cedula,
    validate_cedula,
)

# Cédulas ficticias que cumplen el algoritmo módulo 10 (generadas para pruebas).
VALID_CEDULA_GUAYAS = "0912345675"
VALID_CEDULA_PICHINCHA = "1710034560"


def test_valid_cedula_guayas():
    """Una cédula válida de Guayas pasa la validación."""
    assert is_valid_cedula(VALID_CEDULA_GUAYAS) is True


def test_valid_cedula_pichincha():
    """Una cédula válida de Pichincha pasa la validación."""
    valid, error = validate_cedula(VALID_CEDULA_PICHINCHA)
    assert valid is True
    assert error is None


def test_valid_cedula_with_separators():
    """La validación ignora espacios y guiones."""
    assert is_valid_cedula(" 0912345675 ") is True


def test_invalid_check_digit():
    """Un dígito verificador incorrecto se rechaza."""
    valid, error = validate_cedula("0912345671")
    assert valid is False
    assert "verificador" in error


def test_invalid_length():
    """Una cédula con menos de 10 dígitos se rechaza."""
    valid, error = validate_cedula("091234567")
    assert valid is False
    assert "10 dígitos" in error


def test_non_numeric_cedula():
    """Una cédula con letras se rechaza."""
    valid, error = validate_cedula("09123A5675")
    assert valid is False
    assert "solo números" in error


def test_invalid_province_code():
    """Un código de provincia fuera de rango se rechaza."""
    valid, error = validate_cedula("2512345678")
    assert valid is False
    assert "provincia" in error


def test_invalid_third_digit():
    """Un tercer dígito >= 6 (no persona natural) se rechaza."""
    valid, error = validate_cedula("0962345675")
    assert valid is False
    assert "tercer dígito" in error


def test_empty_cedula():
    """Una cédula vacía se rechaza."""
    valid, _ = validate_cedula("")
    assert valid is False


def test_mask_cedula():
    """La cédula se enmascara dejando visibles los extremos."""
    assert mask_cedula("0912345675") == "09******75"


def test_mask_short_value():
    """Valores muy cortos se enmascaran por completo."""
    assert mask_cedula("091") == "***"
