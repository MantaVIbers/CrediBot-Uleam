"""Pruebas de la capa de redaccion con OpenAI."""
import openai

from app.agent import openai_agent


def test_render_reply_devuelve_base_sin_api_key(monkeypatch):
    monkeypatch.setattr(openai_agent.settings, "openai_enable_ai", True)
    monkeypatch.setattr(openai_agent.settings, "openai_api_key", "")

    reply = openai_agent.render_reply(
        base_reply="Selecciona una opcion: 1. Si 2. No",
        state="CONSENT",
        user_message="hola",
    )

    assert reply == "Selecciona una opcion: 1. Si 2. No"
    assert openai_agent.runtime_status()["last_request_status"] == "not_configured"


def test_render_reply_respeta_flag_desactivado(monkeypatch):
    monkeypatch.setattr(openai_agent.settings, "openai_enable_ai", False)
    monkeypatch.setattr(openai_agent.settings, "openai_api_key", "sk-test")

    reply = openai_agent.render_reply(
        base_reply="Texto base",
        state="MENU",
        user_message="hola",
    )

    assert reply == "Texto base"


def test_render_reply_invoca_openai_si_esta_configurado(monkeypatch):
    llamadas = []

    class _FakeResponse:
        output_text = "Respuesta redactada por IA"

    class _FakeResponses:
        def create(self, **kwargs):
            llamadas.append(kwargs)
            return _FakeResponse()

    class _FakeClient:
        def __init__(self, api_key, **kwargs):
            self.api_key = api_key
            self.options = kwargs
            self.responses = _FakeResponses()

    monkeypatch.setattr(openai_agent.settings, "openai_enable_ai", True)
    monkeypatch.setattr(openai_agent.settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(openai_agent.settings, "openai_model", "gpt-test")
    monkeypatch.setattr(openai, "OpenAI", _FakeClient)

    reply = openai_agent.render_reply(
        base_reply="Texto base con opcion 1",
        state="MENU",
        user_message="hola",
        context={
            "state_before": "ASK_AMOUNT",
            "state_after": "ASK_AMOUNT",
            "pending_step": "indica el monto que deseas solicitar.",
            "rag_context": [
                {
                    "title": "Requisitos básicos",
                    "source": "credito_mvp.md",
                    "content": "Debe entregar nombre, cédula y monto.",
                }
            ],
        },
    )

    assert reply == "Respuesta redactada por IA"
    assert openai_agent.runtime_status()["last_request_status"] == "success"
    assert openai_agent.runtime_status()["last_error_type"] is None
    assert llamadas[0]["model"] == "gpt-test"
    assert "Texto base con opcion 1" in llamadas[0]["input"]
    assert "Estado anterior: ASK_AMOUNT" in llamadas[0]["input"]
    assert "Paso pendiente para continuar" in llamadas[0]["input"]
    assert "Debe entregar nombre, cédula y monto." in llamadas[0]["input"]
