"""Rutas del webhook de WhatsApp (Twilio)."""
import logging

from fastapi import APIRouter, Form, HTTPException, Request, Response

from app.core.config import settings
from app.schemas.whatsapp import extract_twilio_message
from app.services.conversation_service import process_message
from app.services.whatsapp_service import WhatsAppServiceError, send_text_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["whatsapp"])


def _validate_twilio_signature(request: Request, form_data: dict[str, str]) -> None:
    """Valida la firma X-Twilio-Signature si la configuración lo requiere."""
    if not settings.twilio_validate_signature:
        return

    if not settings.app_public_url:
        raise HTTPException(
            status_code=500,
            detail="APP_PUBLIC_URL es requerido para validar la firma de Twilio.",
        )

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        raise HTTPException(status_code=403, detail="Falta la firma de Twilio.")

    try:
        from twilio.request_validator import RequestValidator
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="Instala el paquete twilio para validar firmas.",
        ) from exc

    url = f"{settings.app_public_url.rstrip('/')}{request.url.path}"
    validator = RequestValidator(settings.twilio_auth_token)
    if not validator.validate(url, form_data, signature):
        raise HTTPException(status_code=403, detail="Firma de Twilio inválida.")


@router.get("/whatsapp")
def whatsapp_webhook_status():
    """Endpoint GET de verificación del webhook de Twilio."""
    return {
        "status": "ok",
        "provider": "twilio",
        "message": "Configura esta URL en Twilio Console como webhook entrante.",
    }


@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(default=""),
    MessageSid: str = Form(default=""),
):
    """Recibe mensajes entrantes de Twilio, los procesa y responde."""
    form_data = {
        "From": From,
        "Body": Body,
        "MessageSid": MessageSid,
    }
    _validate_twilio_signature(request, form_data)

    incoming = extract_twilio_message(From, Body, MessageSid or None)
    if not incoming:
        return Response(content="", media_type="text/plain")

    phone = incoming["phone"]
    message = incoming["message"]
    raw_payload = incoming["raw_payload"]

    reply = process_message(phone, message, raw_payload=raw_payload)

    try:
        send_text_message(phone, reply)
    except WhatsAppServiceError as exc:
        logger.error("No se pudo enviar mensaje a %s: %s", phone, exc)

    return Response(content="", media_type="text/plain")
