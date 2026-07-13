"""Factory del proveedor de WhatsApp activo."""
from functools import lru_cache

from app.core.config import settings
from app.providers.whatsapp.base import WhatsAppProvider, WhatsAppProviderError
from app.providers.whatsapp.meta import MetaWhatsAppProvider
from app.providers.whatsapp.twilio import TwilioWhatsAppProvider


# Cachea la instancia del proveedor para evitar recrearla en cada llamada
@lru_cache
def get_whatsapp_provider() -> WhatsAppProvider:
    """Retorna el proveedor configurado en WHATSAPP_PROVIDER."""
    # Normaliza el valor de configuración; por defecto usa Twilio
    provider = (settings.whatsapp_provider or "twilio").strip().lower()
    if provider == "meta":
        return MetaWhatsAppProvider()
    if provider == "twilio":
        return TwilioWhatsAppProvider()
    # Si el proveedor no es válido, lanza error con opciones disponibles
    raise WhatsAppProviderError(
        f"Proveedor de WhatsApp desconocido: {provider}. Usa 'twilio' o 'meta'."
    )


def send_text_message(to_phone: str, message: str) -> dict:
    """Envía texto usando el proveedor activo."""
    return get_whatsapp_provider().send_text_message(to_phone, message)
