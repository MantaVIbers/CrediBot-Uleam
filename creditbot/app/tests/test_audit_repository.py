"""Pruebas del repositorio de auditoría de tools (tool_audit_logs).

Verifica el mapeo del payload y que el registro sea best-effort: un fallo del
cliente no debe propagar la excepción.
"""
from types import SimpleNamespace

from app.repositories import audit_repository as repo


class _FakeInsert:
    def __init__(self, recorder, rows):
        self._recorder = recorder
        self._rows = rows

    def insert(self, payload):
        self._recorder["payload"] = payload
        return self

    def execute(self):
        return SimpleNamespace(data=self._rows)


class _FakeClient:
    def __init__(self, recorder, rows):
        self._recorder = recorder
        self._rows = rows

    def table(self, name):
        self._recorder["table"] = name
        return _FakeInsert(self._recorder, self._rows)


def test_log_tool_call_inserta_payload(monkeypatch):
    """Registra la tool con los campos esperados en tool_audit_logs."""
    recorder: dict = {}
    monkeypatch.setattr(
        repo,
        "get_supabase_client",
        lambda: _FakeClient(recorder, [{"id": "log-1"}]),
    )

    result = repo.log_tool_call(
        "precalificar_por_cedula",
        input_payload={"cedula": "09******75"},
        output_payload={"result": "preaprobado"},
        success=True,
        latency_ms=12,
        conversation_id="conv-1",
    )

    assert result == {"id": "log-1"}
    assert recorder["table"] == "tool_audit_logs"
    assert recorder["payload"]["tool_name"] == "precalificar_por_cedula"
    assert recorder["payload"]["success"] is True
    assert recorder["payload"]["latency_ms"] == 12
    assert recorder["payload"]["conversation_id"] == "conv-1"


def test_log_tool_call_es_best_effort(monkeypatch):
    """Si el cliente falla, retorna None sin propagar la excepción."""
    def _boom():
        raise RuntimeError("db caída")

    monkeypatch.setattr(repo, "get_supabase_client", _boom)

    assert repo.log_tool_call("precalificar_por_cedula") is None
