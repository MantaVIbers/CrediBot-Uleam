import httpx

from app.core.config import settings


class WhatsAppServiceError(Exception):
    pass


def _get_messages_url() -> str:
    if not settings.whatsapp_phone_number_id:
        raise WhatsAppServiceError("WHATSAPP_PHONE_NUMBER_ID no está configurado.")
    return (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
        f"{settings.whatsapp_phone_number_id}/messages"
    )


def send_text_message(to_phone: str, message: str) -> dict:
    if not settings.whatsapp_access_token:
        raise WhatsAppServiceError("WHATSAPP_ACCESS_TOKEN no está configurado.")

    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message},
    }

    try:
        response = httpx.post(
            _get_messages_url(),
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise WhatsAppServiceError(
            f"Error de WhatsApp API ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except httpx.RequestError as exc:
        raise WhatsAppServiceError(f"Error de conexión con WhatsApp API: {exc}") from exc
