"""Contrato común para proveedores de WhatsApp."""
from abc import ABC, abstractmethod
from typing import Any


class WhatsAppProviderError(Exception):
    """Error al enviar o procesar mensajes de WhatsApp."""


class WhatsAppProvider(ABC):
    """Interfaz mínima para enviar texto por WhatsApp."""

    # Nombre identificador del proveedor (sobrescrito por subclases)
    name: str = "base"

    @abstractmethod
    def send_text_message(self, to_phone: str, message: str) -> dict[str, Any]:
        """Envía un mensaje de texto al número indicado."""
