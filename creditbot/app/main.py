"""Punto de entrada de la aplicación FastAPI."""
from fastapi import FastAPI

from app.api.routes_admin import router as admin_router
from app.api.routes_health import router as health_router
from app.api.routes_simulator import router as simulator_router
from app.api.routes_webhook import router as webhook_router

app = FastAPI(title="CrediBot", version="0.1.0")

# Registro de routers
app.include_router(health_router)
app.include_router(simulator_router)
app.include_router(webhook_router)
app.include_router(admin_router)
