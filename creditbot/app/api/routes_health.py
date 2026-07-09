"""Ruta de health check para monitoreo."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Endpoint de verificación de estado del servicio."""
    return {"status": "ok", "app": "CrediBot"}
