"""Pruebas del webhook firmado de Kapso."""
import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app


def _signature(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_webhook_kapso_procesa_mensaje_firmado(monkeypatch):
    from app.api import routes_webhook

    secret = "kapso-webhook-test"
    monkeypatch.setattr(routes_webhook.settings, "kapso_webhook_secret", secret)
    monkeypatch.setattr(
        routes_webhook.settings, "kapso_validate_webhook_signature", True
    )
    monkeypatch.setattr(
        routes_webhook,
        "process_message",
        lambda phone, message, raw_payload: f"Respuesta para {message}",
    )
    sent = []
    monkeypatch.setattr(
        routes_webhook,
        "send_text_message",
        lambda phone, message: sent.append((phone, message)),
    )
    payload = {
        "message": {
            "id": "wamid.1",
            "from": "593999000111",
            "type": "text",
            "text": {"body": "Hola"},
        },
        "conversation": {"id": "conv-1"},
    }
    raw_body = json.dumps(payload).encode("utf-8")

    response = TestClient(app).post(
        "/webhook/whatsapp",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Event": "whatsapp.message.received",
            "X-Webhook-Signature": _signature(secret, raw_body),
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert sent == [("593999000111", "Respuesta para Hola")]


def test_webhook_kapso_rechaza_firma_invalida(monkeypatch):
    from app.api import routes_webhook

    monkeypatch.setattr(routes_webhook.settings, "kapso_webhook_secret", "secret")
    monkeypatch.setattr(
        routes_webhook.settings, "kapso_validate_webhook_signature", True
    )

    response = TestClient(app).post(
        "/webhook/whatsapp",
        json={"message": {"type": "text"}},
        headers={
            "X-Webhook-Event": "whatsapp.message.received",
            "X-Webhook-Signature": "invalid",
        },
    )

    assert response.status_code == 403


def test_webhook_kapso_responde_a_audio_sin_alterar_el_flujo(monkeypatch):
    from app.api import routes_webhook

    secret = "kapso-webhook-test"
    monkeypatch.setattr(routes_webhook.settings, "kapso_webhook_secret", secret)
    monkeypatch.setattr(routes_webhook.settings, "kapso_validate_webhook_signature", True)
    process_calls = []
    monkeypatch.setattr(
        routes_webhook,
        "process_message",
        lambda *args, **kwargs: process_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        routes_webhook,
        "restart_after_non_text",
        lambda phone: "Hola, soy CrediBot. ¿Qué deseas hacer?\n1. Precalificar crédito\n2. Información general\n3. Hablar con asesor",
    )
    sent = []
    monkeypatch.setattr(routes_webhook, "send_text_message", lambda phone, message: sent.append((phone, message)))
    payload = {"message": {"id": "wamid.audio", "from": "593999000111", "type": "audio"}}
    raw_body = json.dumps(payload).encode("utf-8")

    response = TestClient(app).post(
        "/webhook/whatsapp",
        content=raw_body,
        headers={"X-Webhook-Event": "whatsapp.message.received", "X-Webhook-Signature": _signature(secret, raw_body)},
    )

    assert response.status_code == 200
    assert process_calls == []
    assert sent == [
        ("593999000111", "Por favor, envíame tu mensaje como texto. Puedo entenderte mejor cuando escribes."),
        ("593999000111", "Hola, soy CrediBot. ¿Qué deseas hacer?\n1. Precalificar crédito\n2. Información general\n3. Hablar con asesor"),
    ]
