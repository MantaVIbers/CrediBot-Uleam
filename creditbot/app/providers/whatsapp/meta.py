"""Proveedor Meta WhatsApp Cloud API."""
from typing import Any

import httpx

from app.core.config import settings
from app.providers.whatsapp.base import WhatsAppProvider, WhatsAppProviderError


def normalize_meta_phone(from_field: str) -> str:
    """Normaliza el wa_id / from de Meta a dígitos sin '+'."""
    return (
        (from_field or "")
        .replace("whatsapp:", "")
        .replace("+", "")
        .replace(" ", "")
        .strip()
    )


def format_meta_phone(phone: str) -> str:
    """Meta espera el número en formato internacional sin '+' (ej. 59399...)."""
    return normalize_meta_phone(phone)


class MetaWhatsAppProvider(WhatsAppProvider):
    name = "meta"

    def send_text_message(self, to_phone: str, message: str) -> dict[str, Any]:
        if not settings.meta_whatsapp_token:
            raise WhatsAppProviderError("META_WHATSAPP_TOKEN no está configurado.")
        if not settings.meta_whatsapp_phone_number_id:
            raise WhatsAppProviderError(
                "META_WHATSAPP_PHONE_NUMBER_ID no está configurado."
            )

        # Construye la URL del Graph API con la versión configurada
        version = settings.meta_graph_api_version.strip("/") or "v21.0"
        phone_number_id = settings.meta_whatsapp_phone_number_id
        url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"

        # Cuerpo del mensaje en formato Meta Cloud API
        payload = {
            "messaging_product": "whatsapp",
            "to": format_meta_phone(to_phone),
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }
        headers = {
            "Authorization": f"Bearer {settings.meta_whatsapp_token}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise WhatsAppProviderError(
                f"Error de Meta Cloud API ({exc.response.status_code}): {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            raise WhatsAppProviderError(
                f"Error de conexión con Meta Cloud API: {exc}"
            ) from exc


def extract_meta_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrae mensajes de texto entrantes del webhook JSON de Meta."""
    # Lista de mensajes normalizados que se retornarán
    messages: list[dict[str, Any]] = []

    # Recorre la estructura anidada del webhook: entry -> changes -> messages
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for item in value.get("messages") or []:
                # Solo procesa mensajes de tipo texto
                if item.get("type") != "text":
                    continue
                phone = normalize_meta_phone(item.get("from", ""))
                body = ((item.get("text") or {}).get("body") or "").strip()
                # Omite mensajes vacíos o sin número válido
                if not phone or not body:
                    continue
                messages.append(
                    {
                        "phone": phone,
                        "message": body,
                        # Guarda datos originales para auditoría
                        "raw_payload": {
                            "provider": "meta",
                            "from": item.get("from"),
                            "id": item.get("id"),
                            "timestamp": item.get("timestamp"),
                            "text": item.get("text"),
                        },
                    }
                )
    return messages
