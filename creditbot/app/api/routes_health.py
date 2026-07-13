"""Ruta de health check para monitoreo."""
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Endpoint de verificación de estado del servicio."""
    return {"status": "ok", "app": "CrediBot"}


@router.get("/health/ai")
def ai_health_check():
    """Indica si la capa de IA esta activa sin exponer secretos."""
    return {
        "status": "ok",
        "enabled": settings.openai_enable_ai,
        "configured": bool(settings.openai_api_key),
        "model": settings.openai_model,
    }


@router.get("/health/whatsapp")
def whatsapp_health_check():
    """Indica si el proveedor WhatsApp está listo (sin exponer secretos)."""
    provider = (settings.whatsapp_provider or "twilio").strip().lower()
    if provider == "meta":
        configured = bool(
            settings.meta_whatsapp_token and settings.meta_whatsapp_phone_number_id
        )
        missing = [
            name
            for name, ok in (
                ("META_WHATSAPP_TOKEN", bool(settings.meta_whatsapp_token)),
                (
                    "META_WHATSAPP_PHONE_NUMBER_ID",
                    bool(settings.meta_whatsapp_phone_number_id),
                ),
                (
                    "META_WHATSAPP_VERIFY_TOKEN",
                    bool(settings.meta_whatsapp_verify_token),
                ),
            )
            if not ok
        ]
    else:
        configured = bool(
            settings.twilio_account_sid
            and settings.twilio_auth_token
            and settings.twilio_whatsapp_from
        )
        missing = [
            name
            for name, ok in (
                ("TWILIO_ACCOUNT_SID", bool(settings.twilio_account_sid)),
                ("TWILIO_AUTH_TOKEN", bool(settings.twilio_auth_token)),
                ("TWILIO_WHATSAPP_FROM", bool(settings.twilio_whatsapp_from)),
            )
            if not ok
        ]

    redis_configured = bool(settings.redis_url)
    return {
        "status": "ok" if configured else "incomplete",
        "provider": provider,
        "configured": configured,
        "missing_env": missing,
        "app_public_url_set": bool(settings.app_public_url),
        "twilio_validate_signature": settings.twilio_validate_signature,
        "redis_configured": redis_configured,
        "webhook_path": "/webhook/whatsapp",
    }
