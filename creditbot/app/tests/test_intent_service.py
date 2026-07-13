"""Pruebas de detección de intención."""
from app.services import intent_service
from app.services import message_service


def test_menu_detecta_credito_en_lenguaje_natural():
    assert intent_service.menu_option_from_text("Quiero solicitar un crédito") == "1"
    assert intent_service.menu_option_from_text("necesito un prestamo") == "1"


def test_menu_detecta_info_y_asesor():
    assert intent_service.menu_option_from_text("quiero información de requisitos") == "2"
    assert intent_service.menu_option_from_text("hablar con una persona") == "3"


def test_confirmacion_detecta_si_y_no():
    assert intent_service.confirmation_from_text("sí autorizo") == "1"
    assert intent_service.confirmation_from_text("confirmo") == "1"
    assert intent_service.confirmation_from_text("no, quiero corregir") == "2"


def test_handoff_hint_no_se_duplica():
    message = message_service.with_handoff_hint("Indica tu ingreso mensual")
    assert "asesor" in message.lower()
    assert message_service.with_handoff_hint(message) == message
