"""Rutas de health check para monitoreo."""
from fastapi import APIRouter

from app.agent.openai_agent import runtime_status
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {"status": "ok", "app": "CrediBot"}


@router.get("/health/ai")
def ai_health_check():
    """Indica si la capa de IA está activa sin exponer secretos."""
    return {
        "status": "ok",
        "enabled": settings.openai_enable_ai,
        "configured": bool(settings.openai_api_key),
        "model": settings.openai_model,
        **runtime_status(),
    }


@router.get("/health/whatsapp")
def whatsapp_health_check():
    """Indica si Kapso está listo sin exponer secretos."""
    configured = bool(
        settings.kapso_api_key
        and settings.kapso_phone_number_id
        and (
            settings.kapso_webhook_secret
            or not settings.kapso_validate_webhook_signature
        )
    )
    missing = [
        name
        for name, ok in (
            ("KAPSO_API_KEY", bool(settings.kapso_api_key)),
            ("KAPSO_PHONE_NUMBER_ID", bool(settings.kapso_phone_number_id)),
            (
                "KAPSO_WEBHOOK_SECRET",
                bool(settings.kapso_webhook_secret)
                or not settings.kapso_validate_webhook_signature,
            ),
        )
        if not ok
    ]
    return {
        "status": "ok" if configured else "incomplete",
        "provider": "kapso",
        "configured": configured,
        "missing_env": missing,
        "app_public_url_set": bool(settings.app_public_url),
        "admin_password_set": bool(settings.admin_dashboard_password),
        "kapso_validate_webhook_signature": settings.kapso_validate_webhook_signature,
        "redis_configured": bool(settings.redis_url),
        "webhook_path": "/webhook/whatsapp",
    }
