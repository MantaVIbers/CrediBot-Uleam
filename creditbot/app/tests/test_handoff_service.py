"""Pruebas del servicio de derivación humana."""
from app.services import handoff_service


# Verifica que la creación de un caso de handoff incluya resumen y transcripción
def test_create_handoff_case_incluye_resumen_y_transcript(monkeypatch):
    # Simula historial de mensajes de la conversación
    messages = [
        {"direction": "inbound", "content": "Hola", "created_at": "2026-07-13T10:00:00Z"},
        {"direction": "outbound", "content": "Menú", "created_at": "2026-07-13T10:00:01Z"},
        {
            "direction": "inbound",
            "content": "quiero hablar con un asesor",
            "created_at": "2026-07-13T10:00:02Z",
        },
    ]
    recorder = {}

    monkeypatch.setattr(
        handoff_service.message_repository,
        "get_messages_by_conversation",
        lambda conversation_id: messages,
    )
    monkeypatch.setattr(
        handoff_service.handoff_repository,
        "create_handoff_case",
        lambda **kwargs: recorder.setdefault("payload", kwargs) or {"id": "case-1"},
    )

    result = handoff_service.create_handoff_case(
        user_id="user-1",
        conversation_id="conv-1",
        reason="user_requested_advisor",       # Razón de la derivación
        credit_request_id="req-1",
    )

    assert result == recorder["payload"]
    assert recorder["payload"]["credit_request_id"] == "req-1"
    # El resumen debe contener la solicitud de asesor
    assert "solicitó hablar con un asesor" in recorder["payload"]["handoff_summary"]
    assert "quiero hablar con un asesor" in recorder["payload"]["handoff_summary"]
    # La transcripción debe incluir todos los mensajes
    assert recorder["payload"]["transcript"][-1]["direction"] == "inbound"
    assert recorder["payload"]["transcript"][-1]["content"] == "quiero hablar con un asesor"

