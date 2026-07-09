"""Esquemas Pydantic para el simulador de mensajes."""
from pydantic import BaseModel, Field


class SimulateMessageRequest(BaseModel):
    """Cuerpo de la petición para simular un mensaje entrante."""

    phone: str = Field(..., examples=["593999999999"])
    message: str = Field(..., examples=["Hola"])


class SimulateMessageResponse(BaseModel):
    """Respuesta del simulador con el mensaje de réplica del bot."""

    phone: str
    reply: str
