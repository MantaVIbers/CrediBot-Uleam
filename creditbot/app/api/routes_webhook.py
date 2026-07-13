"""Rutas del webhook de WhatsApp (Twilio y Meta Cloud API)."""
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Request, Response

from app.core.config import settings
from app.providers.whatsapp.meta import extract_meta_messages
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


def _validate_meta_signature(raw_body: bytes, signature_header: str | None) -> None:
    """Valida X-Hub-Signature-256 si META_WHATSAPP_APP_SECRET está configurado."""
    secret = (settings.meta_whatsapp_app_secret or "").strip()
    if not secret:
        return
    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=403, detail="Falta la firma de Meta.")
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    received = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, received):
        raise HTTPException(status_code=403, detail="Firma de Meta inválida.")


def _send_reply(phone: str, reply: str) -> None:
    try:
        send_text_message(phone, reply)
    except WhatsAppServiceError as exc:
        logger.error("No se pudo enviar mensaje a %s: %s", phone, exc)


@router.get("/whatsapp")
async def whatsapp_webhook_get(request: Request):
    """Verificación Meta (hub.challenge) o status del webhook."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and challenge is not None:
        expected = (settings.meta_whatsapp_verify_token or "").strip()
        if not expected or token != expected:
            raise HTTPException(status_code=403, detail="Verify token inválido.")
        return Response(content=str(challenge), media_type="text/plain")

    provider = (settings.whatsapp_provider or "twilio").strip().lower()
    return {
        "status": "ok",
        "provider": provider,
        "message": (
            "Meta: usa esta URL en el webhook de WhatsApp Cloud API. "
            "Twilio: configúrala como webhook entrante en Twilio Console."
        ),
    }


@router.post("/whatsapp")
async def receive_whatsapp_webhook(request: Request):
    """Recibe mensajes entrantes (JSON Meta o form Twilio), procesa y responde."""
    content_type = (request.headers.get("content-type") or "").lower()

    # Meta Cloud API envía JSON; Twilio envía form-urlencoded
    if "application/json" in content_type:
        raw_body = await request.body()
        _validate_meta_signature(
            raw_body,
            request.headers.get("X-Hub-Signature-256"),
        )
        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail="JSON inválido.") from exc
        for incoming in extract_meta_messages(payload):
            reply = process_message(
                incoming["phone"],
                incoming["message"],
                raw_payload=incoming["raw_payload"],
            )
            _send_reply(incoming["phone"], reply)
        return {"status": "ok"}

    # Rama Twilio: procesar datos del formulario
    form = await request.form()
    form_data = {key: str(value) for key, value in form.items()}
    _validate_twilio_signature(request, form_data)

    incoming = extract_twilio_message(
        form_data.get("From", ""),
        form_data.get("Body", ""),
        form_data.get("MessageSid") or None,
    )
    if not incoming:
        return Response(content="", media_type="text/plain")

    reply = process_message(
        incoming["phone"],
        incoming["message"],
        raw_payload=incoming["raw_payload"],
    )
    _send_reply(incoming["phone"], reply)
    return Response(content="", media_type="text/plain")
