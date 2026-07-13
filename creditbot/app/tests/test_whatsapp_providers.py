"""Pruebas de proveedores WhatsApp (Meta + factory)."""
import pytest

from app.providers.whatsapp.factory import get_whatsapp_provider
from app.providers.whatsapp.meta import (
    extract_meta_messages,
    format_meta_phone,
    normalize_meta_phone,
)
from app.providers.whatsapp.twilio import TwilioWhatsAppProvider


# Verifica la normalización y formato de números de teléfono de Meta
def test_normalize_and_format_meta_phone():
    assert normalize_meta_phone("+593 99 999 9999") == "593999999999"
    assert format_meta_phone("whatsapp:+593999999999") == "593999999999"


# Verifica la extracción de mensajes de texto del payload de Meta (filtra imágenes)
def test_extract_meta_messages():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "593999999999",
                                    "id": "wamid.1",
                                    "timestamp": "123",
                                    "type": "text",
                                    "text": {"body": "Hola"},
                                },
                                {
                                    "from": "593111111111",
                                    "type": "image",
                                },
                            ]
                        }
                    }
                ]
            }
        ]
    }
    messages = extract_meta_messages(payload)
    # Solo se extrae el mensaje de texto, no la imagen
    assert len(messages) == 1
    assert messages[0]["phone"] == "593999999999"
    assert messages[0]["message"] == "Hola"
    assert messages[0]["raw_payload"]["provider"] == "meta"


# Verifica que el factory retorne Twilio cuando la configuración lo indica
def test_factory_defaults_to_twilio(monkeypatch):
    get_whatsapp_provider.cache_clear()
    monkeypatch.setattr(
        "app.providers.whatsapp.factory.settings.whatsapp_provider",
        "twilio",
    )
    provider = get_whatsapp_provider()
    assert isinstance(provider, TwilioWhatsAppProvider)
    assert provider.name == "twilio"
    get_whatsapp_provider.cache_clear()


# Verifica que el factory lance error con proveedores desconocidos
def test_factory_rejects_unknown(monkeypatch):
    get_whatsapp_provider.cache_clear()
    monkeypatch.setattr(
        "app.providers.whatsapp.factory.settings.whatsapp_provider",
        "telegram",
    )
    with pytest.raises(Exception, match="desconocido"):
        get_whatsapp_provider()
    get_whatsapp_provider.cache_clear()
