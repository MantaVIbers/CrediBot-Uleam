"""Función para extraer y normalizar los datos de un mensaje entrante de Twilio."""
from typing import Any

from app.services.whatsapp_service import normalize_twilio_phone


def extract_twilio_message(
    from_phone: str,
    body: str,
    message_sid: str | None = None,
) -> dict[str, Any] | None:
    """Extrae teléfono, mensaje y payload crudo desde los parámetros de Twilio."""
    # Normalizar el número de teléfono al formato estándar
    phone = normalize_twilio_phone(from_phone)
    # Eliminar espacios en blanco del mensaje
    message = body.strip()

    if not phone or not message:
        return None

    raw_payload: dict[str, Any] = {
        "From": from_phone,
        "Body": body,
    }
    if message_sid:
        raw_payload["MessageSid"] = message_sid

    return {
        "phone": phone,
        "message": message,
        "raw_payload": raw_payload,
    }
