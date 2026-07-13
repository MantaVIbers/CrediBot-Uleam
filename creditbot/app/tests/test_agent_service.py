"""Pruebas del agente OpenAI con function calling."""
import json
from unittest.mock import MagicMock, patch

from app.services import agent_service


# Verifica fallback cuando no hay API key configurada
def test_answer_without_openai_key_returns_fallback(monkeypatch):
    monkeypatch.setattr(agent_service.settings, "openai_api_key", "")
    reply = agent_service.answer_question("¿Qué es el score?")
    assert "precalificar" in reply.lower()


@patch("app.services.agent_service.audit_repository.log_tool_call")
@patch("app.services.agent_service.rag_service.retrieve_context", return_value=["contexto"])
@patch("app.services.agent_service.rag_service.build_context_block", return_value="contexto")
@patch("app.services.agent_service.rag_service.is_rag_available", return_value=True)
# Verifica que el agente ejecute tool calls de OpenAI y registre auditoría
def test_agent_executes_tool_calls(mock_rag_ok, mock_context, mock_retrieve, mock_audit, monkeypatch):
    monkeypatch.setattr(agent_service.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(agent_service.settings, "openai_model", "gpt-4o-mini")

    # Simula tool call de OpenAI para consultar política de crédito
    tool_call = MagicMock()
    tool_call.id = "call-1"
    tool_call.function.name = "consultar_politica_credito"
    tool_call.function.arguments = json.dumps({"pregunta": "¿Qué es el score?"})

    first_message = MagicMock()
    first_message.content = None
    first_message.tool_calls = [tool_call]
    first_message.model_dump.return_value = {"role": "assistant", "tool_calls": []}

    final_message = MagicMock()
    final_message.content = "El score mide tu historial crediticio simulado."
    final_message.tool_calls = None

    # Primera llamada retorna tool call, segunda retorna respuesta final
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=first_message)]),
        MagicMock(choices=[MagicMock(message=final_message)]),
    ]

    with patch("openai.OpenAI", return_value=mock_client):
        reply = agent_service.answer_question("¿Qué es el score?", "conv-1")

    assert "score" in reply.lower()
    assert mock_audit.call_count >= 2  # Al menos tool call + respuesta final
    tool_names = [call.args[0] for call in mock_audit.call_args_list]
    assert "consultar_politica_credito" in tool_names       # Tool de consulta de política
    assert agent_service.AGENT_TOOL_NAME in tool_names      # Tool del agente


@patch("app.services.agent_service.audit_repository.log_tool_call")
# Verifica que la validación de cédula enmascare los datos sensibles
def test_validar_cedula_tool_masks_input(mock_audit):
    result = agent_service._tool_validar_cedula("0912345675", "conv-2")

    assert result["valida"] is True
    assert "09" in result["cedula_masked"]  # Solo visible primeros 2 y últimos 2
    mock_audit.assert_called_once()
    assert mock_audit.call_args.args[0] == "validar_cedula"
    # La cédula enmascarada se registra en auditoría, no la original
    assert mock_audit.call_args.kwargs["input_payload"]["cedula"] == "09******75"


@patch("app.services.agent_service.audit_repository.log_tool_call")
# Verifica que la explicación de reglas retorne categorías de score
def test_explicar_reglas_credito_returns_categories(mock_audit):
    result = agent_service._tool_explicar_reglas_credito("score", "conv-3")

    assert result["tema"] == "score"
    assert "categorias_score" in result["reglas"]  # Contiene clasificación de scores
    mock_audit.assert_called_once()
