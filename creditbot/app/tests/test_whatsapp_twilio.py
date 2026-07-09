"""Pruebas de normalización de teléfonos y extracción de mensajes de Twilio."""
from app.schemas.whatsapp import extract_twilio_message
from app.services.whatsapp_service import format_twilio_whatsapp_number, normalize_twilio_phone


def test_normalize_twilio_phone():
    """Verifica que se limpie el prefijo 'whatsapp:+' del número."""
    assert normalize_twilio_phone("whatsapp:+593999999999") == "593999999999"


def test_format_twilio_whatsapp_number():
    """Verifica que se agregue el prefijo 'whatsapp:+' al número."""
    assert format_twilio_whatsapp_number("593999999999") == "whatsapp:+593999999999"


def test_extract_twilio_message():
    """Verifica la extracción correcta de datos desde parámetros de Twilio."""
    result = extract_twilio_message(
        "whatsapp:+593999999999",
        "Hola",
        "SM123",
    )

    assert result is not None
    assert result["phone"] == "593999999999"
    assert result["message"] == "Hola"
    assert result["raw_payload"]["MessageSid"] == "SM123"
