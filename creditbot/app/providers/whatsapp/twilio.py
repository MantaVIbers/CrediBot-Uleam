"""Proveedor Twilio WhatsApp."""
from typing import Any

import httpx

from app.core.config import settings
from app.providers.whatsapp.base import WhatsAppProvider, WhatsAppProviderError


def format_twilio_whatsapp_number(phone: str) -> str:
    """Formatea un número al formato 'whatsapp:+XXXXXXXX' requerido por Twilio."""
    # Limpia prefijos existentes y reconstruye en formato Twilio
    cleaned = phone.replace("whatsapp:", "").replace("+", "").strip()
    return f"whatsapp:+{cleaned}"


def normalize_twilio_phone(from_field: str) -> str:
    """Limpia el campo 'From' de Twilio y retorna solo el número sin prefijos."""
    return from_field.replace("whatsapp:", "").replace("+", "").strip()


class TwilioWhatsAppProvider(WhatsAppProvider):
    name = "twilio"

    def send_text_message(self, to_phone: str, message: str) -> dict[str, Any]:
        if not settings.twilio_account_sid:
            raise WhatsAppProviderError("TWILIO_ACCOUNT_SID no está configurado.")
        if not settings.twilio_auth_token:
            raise WhatsAppProviderError("TWILIO_AUTH_TOKEN no está configurado.")
        if not settings.twilio_whatsapp_from:
            raise WhatsAppProviderError("TWILIO_WHATSAPP_FROM no está configurado.")

        # Construye la URL del API de Twilio y el cuerpo del mensaje
        url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{settings.twilio_account_sid}/Messages.json"
        )
        payload = {
            "From": settings.twilio_whatsapp_from,
            "To": format_twilio_whatsapp_number(to_phone),
            "Body": message,
        }

        try:
            response = httpx.post(
                url,
                data=payload,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise WhatsAppProviderError(
                f"Error de Twilio API ({exc.response.status_code}): {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise WhatsAppProviderError(f"Error de conexión con Twilio API: {exc}") from exc
