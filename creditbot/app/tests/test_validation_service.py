from app.services.validation_service import (
    validate_amount,
    validate_confirmation,
    validate_income,
    validate_menu_option,
    validate_name,
    validate_term,
)


def test_validate_amount_correct():
    is_valid, error = validate_amount("500")
    assert is_valid is True
    assert error is None


def test_validate_amount_invalid():
    is_valid, error = validate_amount("abc")
    assert is_valid is False
    assert error is not None

    is_valid, error = validate_amount("0")
    assert is_valid is False
    assert error is not None


def test_validate_term_correct():
    is_valid, error = validate_term("12")
    assert is_valid is True
    assert error is None


def test_validate_term_invalid():
    is_valid, error = validate_term("2")
    assert is_valid is False
    assert error is not None

    is_valid, error = validate_term("abc")
    assert is_valid is False
    assert error is not None


def test_validate_name_correct():
    is_valid, error = validate_name("Carlos Ortiz")
    assert is_valid is True
    assert error is None


def test_validate_income_correct():
    is_valid, error = validate_income("700")
    assert is_valid is True
    assert error is None


def test_validate_menu_option_correct():
    is_valid, error = validate_menu_option("1")
    assert is_valid is True
    assert error is None


def test_validate_confirmation_correct():
    is_valid, error = validate_confirmation("1")
    assert is_valid is True
    assert error is None
