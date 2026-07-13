"""Pruebas del asistente IA."""
from unittest.mock import MagicMock, patch

from app.services import ai_assistant_service


# Verifica que sin API key se retorne respuesta de respaldo
def test_answer_without_openai_key_returns_fallback(monkeypatch):
    monkeypatch.setattr(ai_assistant_service.settings, "openai_api_key", "")
    reply = ai_assistant_service.answer_credit_question("¿Qué es el score?")
    assert "precalificar" in reply.lower()


@patch("app.services.ai_assistant_service.audit_repository.log_tool_call")
@patch("app.services.ai_assistant_service.rag_service.retrieve_context", return_value=["contexto"])
@patch("app.services.ai_assistant_service.rag_service.build_context_block", return_value="contexto")
# Verifica que con API key mockeada se invoque a OpenAI y se registre auditoría
def test_answer_with_openai_mock(mock_context, mock_retrieve, mock_audit, monkeypatch):
    monkeypatch.setattr(ai_assistant_service.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(ai_assistant_service.settings, "openai_model", "gpt-4o-mini")

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "El score mide tu historial crediticio simulado."
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    with patch("openai.OpenAI", return_value=mock_client):
        reply = ai_assistant_service.answer_credit_question("¿Qué es el score?", "conv-1")

    assert "score" in reply.lower()
    mock_audit.assert_called_once()  # Se registró la llamada en auditoría
