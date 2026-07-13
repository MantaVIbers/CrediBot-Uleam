"""Pruebas del servicio de derivación humana."""
from app.services import handoff_service


def test_create_handoff_case_incluye_resumen_y_transcript(monkeypatch):
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
        reason="user_requested_advisor",
        credit_request_id="req-1",
    )

    assert result == recorder["payload"]
    assert recorder["payload"]["credit_request_id"] == "req-1"
    assert "solicitó hablar con un asesor" in recorder["payload"]["handoff_summary"]
    assert "quiero hablar con un asesor" in recorder["payload"]["handoff_summary"]
    assert recorder["payload"]["transcript"][-1]["direction"] == "inbound"
    assert recorder["payload"]["transcript"][-1]["content"] == "quiero hablar con un asesor"

