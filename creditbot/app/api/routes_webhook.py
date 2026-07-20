"""Ruta del webhook nativo de Kapso WhatsApp."""
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.providers.whatsapp.kapso import extract_kapso_messages
from app.services.conversation_service import process_message, restart_after_non_text
from app.services.whatsapp_service import WhatsAppServiceError, send_text_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["whatsapp"])


def _validate_kapso_signature(raw_body: bytes, signature_header: str | None) -> None:
    """Valida el HMAC SHA-256 enviado por Kapso en X-Webhook-Signature."""
    if not settings.kapso_validate_webhook_signature:
        return

    secret = (settings.kapso_webhook_secret or "").strip()
    if not secret:
        raise HTTPException(
            status_code=500,
            detail="KAPSO_WEBHOOK_SECRET es requerido para validar el webhook.",
        )
    if not signature_header:
        raise HTTPException(status_code=403, detail="Falta la firma de Kapso.")

    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header.strip()):
        raise HTTPException(status_code=403, detail="Firma de Kapso inválida.")


def _send_reply(phone: str, reply: str) -> None:
    try:
        send_text_message(phone, reply)
    except WhatsAppServiceError as exc:
        logger.error("No se pudo enviar mensaje a %s: %s", phone, exc)


@router.get("/whatsapp")
async def whatsapp_webhook_get():
    """Devuelve el estado de la ruta que debe registrarse en Kapso."""
    return {
        "status": "ok",
        "provider": "kapso",
        "message": "Registra esta URL en Kapso para whatsapp.message.received.",
    }


@router.post("/whatsapp")
async def receive_whatsapp_webhook(request: Request):
    """Recibe eventos JSON de Kapso, procesa mensajes entrantes y responde."""
    raw_body = await request.body()
    _validate_kapso_signature(raw_body, request.headers.get("X-Webhook-Signature"))
    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="JSON inválido.") from exc

    event = request.headers.get("X-Webhook-Event") or payload.get("type")
    if event != "whatsapp.message.received":
        return {"status": "ignored"}

    for incoming in extract_kapso_messages(payload):
        reply = incoming.get("reply")
        if reply:
            _send_reply(incoming["phone"], reply)
            _send_reply(incoming["phone"], restart_after_non_text(incoming["phone"]))
            continue
        else:
            reply = process_message(
                incoming["phone"],
                incoming["message"],
                raw_payload=incoming["raw_payload"],
            )
        _send_reply(incoming["phone"], reply)
    return {"status": "ok"}
