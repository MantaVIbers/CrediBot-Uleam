"""Pruebas del servicio de dashboard para casos derivados."""
from types import SimpleNamespace

from dashboard.services import supabase_dashboard


class _FakeQuery:
    def __init__(self, recorder):
        self._recorder = recorder

    def select(self, columns):
        self._recorder["select"] = columns
        return self

    def insert(self, payload):
        self._recorder["insert_payload"] = payload
        return self

    def update(self, payload):
        self._recorder["payload"] = payload
        return self

    def eq(self, column, value):
        self._recorder["eq"] = (column, value)
        return self

    def neq(self, column, value):
        self._recorder["neq"] = (column, value)
        return self

    def order(self, column, desc=False):
        self._recorder["order"] = (column, desc)
        return self

    def execute(self):
        if "insert_payload" in self._recorder:
            payload = self._recorder["insert_payload"]
            return SimpleNamespace(data=[{"id": "msg-1", **payload}])
        if "payload" in self._recorder:
            return SimpleNamespace(data=[{"id": self._recorder["eq"][1], **self._recorder["payload"]}])
        return SimpleNamespace(data=[{"id": "msg-1", "content": "Hola"}])


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

    assert result["id"] == "case-1"
    assert result["status"] == "closed"
    assert recorder["table"] == "handoff_cases"
    assert recorder["payload"]["status"] == "closed"
    assert "updated_at" in recorder["payload"]
    assert recorder["eq"] == ("id", "case-1")


def test_obtener_mensajes_conversacion_lee_historial(monkeypatch):
    recorder = {}
    monkeypatch.setattr(
        supabase_dashboard,
        "get_supabase_client",
        lambda: _FakeClient(recorder),
    )

    result = supabase_dashboard.obtener_mensajes_conversacion("conv-1")

    assert result == [{"id": "msg-1", "content": "Hola"}]
    assert recorder["table"] == "messages"
    assert recorder["select"] == "*"
    assert recorder["eq"] == ("conversation_id", "conv-1")
    assert recorder["order"] == ("created_at", False)


def test_enviar_respuesta_humana_envia_y_guarda_mensaje(monkeypatch):
    recorder = {}
    monkeypatch.setattr(
        supabase_dashboard,
        "get_supabase_client",
        lambda: _FakeClient(recorder),
    )
    monkeypatch.setattr(
        supabase_dashboard,
        "_send_dashboard_whatsapp_message",
        lambda phone, message: {"sid": "SM123", "status": "queued"},
    )

    result = supabase_dashboard.enviar_respuesta_humana(
        case_id="case-1",
        conversation_id="conv-1",
        user_id="user-1",
        phone="593999000111",
        content="Hola, soy el asesor.",
    )

    assert result["id"] == "msg-1"
    assert result["direction"] == "outbound"
    assert result["content"] == "Hola, soy el asesor."
    assert result["raw_payload"]["source"] == "dashboard_human"
    assert recorder["table"] == "handoff_cases"
    assert recorder["payload"]["status"] == "assigned"
