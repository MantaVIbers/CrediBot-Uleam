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
