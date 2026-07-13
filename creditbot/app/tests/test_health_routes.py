"""Pruebas de endpoints de salud."""
from fastapi.testclient import TestClient

from app.main import app


def test_root_muestra_inicio_credibot():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "CrediBot" in response.text
    assert "Consola de demo" in response.text
    assert "/docs" in response.text
    assert "/simulate/message" in response.text
    assert "/admin/handoff" in response.text
    assert "593999000111" in response.text


def test_ai_health_no_expone_api_key(monkeypatch):
    from app.api import routes_health

    monkeypatch.setattr(routes_health.settings, "openai_enable_ai", True)
    monkeypatch.setattr(routes_health.settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(routes_health.settings, "openai_model", "gpt-test")

    client = TestClient(app)
    response = client.get("/health/ai")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "ok",
        "enabled": True,
        "configured": True,
        "model": "gpt-test",
    }
    assert "sk-test" not in response.text


def test_whatsapp_health_sin_secretos(monkeypatch):
    from app.api import routes_health

    monkeypatch.setattr(routes_health.settings, "whatsapp_provider", "twilio")
    monkeypatch.setattr(routes_health.settings, "twilio_account_sid", "ACtest")
    monkeypatch.setattr(routes_health.settings, "twilio_auth_token", "token")
    monkeypatch.setattr(routes_health.settings, "twilio_whatsapp_from", "whatsapp:+14155238886")
    monkeypatch.setattr(routes_health.settings, "app_public_url", "https://example.com")
    monkeypatch.setattr(routes_health.settings, "twilio_validate_signature", True)
    monkeypatch.setattr(routes_health.settings, "redis_url", "")

    client = TestClient(app)
    response = client.get("/health/whatsapp")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "twilio"
    assert body["configured"] is True
    assert body["missing_env"] == []
    assert body["webhook_path"] == "/webhook/whatsapp"
    assert "token" not in response.text
