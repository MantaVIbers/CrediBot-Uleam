import logging

from fastapi import APIRouter, HTTPException, Query, Response

from app.core.config import settings
from app.schemas.whatsapp import extract_incoming_messages
from app.services.conversation_service import process_message
from app.services.whatsapp_service import WhatsAppServiceError, send_text_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["whatsapp"])


@router.get("/whatsapp")
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
):
    if (
        hub_mode == "subscribe"
        and hub_verify_token == settings.whatsapp_verify_token
        and hub_challenge
    ):
        return Response(content=hub_challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Token de verificación inválido.")


@router.post("/whatsapp")
def receive_whatsapp_webhook(payload: dict):
    incoming_messages = extract_incoming_messages(payload)

    for item in incoming_messages:
        phone = item["phone"]
        message = item["message"]
        raw_payload = item["raw_payload"]

        reply = process_message(phone, message, raw_payload=raw_payload)

        try:
            send_text_message(phone, reply)
        except WhatsAppServiceError as exc:
            logger.error("No se pudo enviar mensaje a %s: %s", phone, exc)

    return {"status": "ok"}
