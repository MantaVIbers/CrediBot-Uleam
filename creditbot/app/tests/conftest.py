"""Fixtures compartidas para pruebas del backend."""
import pytest


@pytest.fixture(autouse=True)
def no_open_handoff_by_default(monkeypatch):
    """Evita consultas reales a Supabase al iniciar process_message."""
    monkeypatch.setattr(
        "app.services.conversation_service.handoff_service.get_open_handoff_case_for_user",
        lambda user_id: None,
    )
