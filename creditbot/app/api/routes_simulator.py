"""Rutas del simulador para probar el bot sin Twilio."""
from fastapi import APIRouter

from app.schemas.conversation import SimulateMessageRequest, SimulateMessageResponse
from app.services.conversation_service import process_message

router = APIRouter(prefix="/simulate", tags=["simulator"])


@router.post("/message", response_model=SimulateMessageResponse)
def simulate_message(payload: SimulateMessageRequest):
    """Endpoint para simular un mensaje entrante y obtener la respuesta del bot."""
    reply = process_message(payload.phone, payload.message)
    return SimulateMessageResponse(phone=payload.phone, reply=reply)
