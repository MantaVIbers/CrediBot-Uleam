"""Pruebas del servicio de dashboard para casos derivados."""
from types import SimpleNamespace

from dashboard.services import supabase_dashboard


class _FakeQuery:
    def __init__(self, recorder):
        self._recorder = recorder

    def update(self, payload):
        self._recorder["payload"] = payload
        return self

    def eq(self, column, value):
        self._recorder["eq"] = (column, value)
        return self

    def execute(self):
        return SimpleNamespace(data=[{"id": self._recorder["eq"][1], "status": "closed"}])


class _FakeClient:
    def __init__(self, recorder):
        self._recorder = recorder

    def table(self, name):
        self._recorder["table"] = name
        return _FakeQuery(self._recorder)


def test_cerrar_caso_derivado_actualiza_estado(monkeypatch):
    recorder = {}
    monkeypatch.setattr(
        supabase_dashboard,
        "get_supabase_client",
        lambda: _FakeClient(recorder),
    )

    result = supabase_dashboard.cerrar_caso_derivado("case-1")

    assert result == {"id": "case-1", "status": "closed"}
    assert recorder["table"] == "handoff_cases"
    assert recorder["payload"]["status"] == "closed"
    assert "updated_at" in recorder["payload"]
    assert recorder["eq"] == ("id", "case-1")
