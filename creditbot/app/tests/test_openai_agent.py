"""Pruebas de la capa de redaccion con OpenAI."""
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


def test_render_reply_respeta_flag_desactivado(monkeypatch):
    monkeypatch.setattr(openai_agent.settings, "openai_enable_ai", False)
    monkeypatch.setattr(openai_agent.settings, "openai_api_key", "sk-test")

    reply = openai_agent.render_reply(
        base_reply="Texto base",
        state="MENU",
        user_message="hola",
    )

    assert reply == "Texto base"
