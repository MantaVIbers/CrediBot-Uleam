import httpx

from app.core.config import settings


class WhatsAppServiceError(Exception):
    pass


def format_twilio_whatsapp_number(phone: str) -> str:
    cleaned = phone.replace("whatsapp:", "").replace("+", "").strip()
    return f"whatsapp:+{cleaned}"


def normalize_twilio_phone(from_field: str) -> str:
    return from_field.replace("whatsapp:", "").replace("+", "").strip()


def _get_twilio_messages_url() -> str:
    if not settings.twilio_account_sid:
        raise WhatsAppServiceError("TWILIO_ACCOUNT_SID no está configurado.")
    return (
        "https://api.twilio.com/2010-04-01/Accounts/"
        f"{settings.twilio_account_sid}/Messages.json"
    )


def send_text_message(to_phone: str, message: str) -> dict:
    if not settings.twilio_auth_token:
        raise WhatsAppServiceError("TWILIO_AUTH_TOKEN no está configurado.")
    if not settings.twilio_whatsapp_from:
        raise WhatsAppServiceError("TWILIO_WHATSAPP_FROM no está configurado.")

    payload = {
        "From": settings.twilio_whatsapp_from,
        "To": format_twilio_whatsapp_number(to_phone),
        "Body": message,
    }

    try:
        response = httpx.post(
            _get_twilio_messages_url(),
            data=payload,
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise WhatsAppServiceError(
            f"Error de Twilio API ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise WhatsAppServiceError(f"Error de conexión con Twilio API: {exc}") from exc
