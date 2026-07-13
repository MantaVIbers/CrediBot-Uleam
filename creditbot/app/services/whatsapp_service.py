"""Fachada de WhatsApp: proveedor activo (Twilio o Meta)."""
from app.providers.whatsapp.base import WhatsAppProviderError as WhatsAppServiceError
from app.providers.whatsapp.factory import send_text_message
from app.providers.whatsapp.twilio import (
    format_twilio_whatsapp_number,
    normalize_twilio_phone,
)

__all__ = [
    "WhatsAppServiceError",
    "format_twilio_whatsapp_number",
    "normalize_twilio_phone",
    "send_text_message",
]
