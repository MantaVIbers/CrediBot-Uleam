"""Pruebas del servicio de dashboard y reply de handoff."""
from types import SimpleNamespace

import pytest

from app.services import handoff_service
from dashboard.services import supabase_dashboard


# Clase fake que simula consultas encadenable de Supabase
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
            return SimpleNamespace(data=[{"id": "msg-1", **payload}])  # Retorna con ID asignado
        if "payload" in self._recorder:
            return SimpleNamespace(
                data=[{"id": self._recorder["eq"][1], **self._recorder["payload"]}]
            )
        return SimpleNamespace(data=[{"id": "msg-1", "content": "Hola"}])  # Respuesta por defecto


class _FakeClient:
    def __init__(self, recorder):
        self._recorder = recorder

    def table(self, name):
        self._recorder["table"] = name
        return _FakeQuery(self._recorder)


# Verifica que cerrar un caso de derivación actualice su estado a "closed"
def test_cerrar_caso_derivado_actualiza_estado(monkeypatch):
    recorder = {}
    monkeypatch.setattr(supabase_dashboard, "_backend_api_url", lambda: "")
    monkeypatch.setattr(supabase_dashboard, "_admin_password", lambda: "")
    monkeypatch.setattr(
        supabase_dashboard,
        "get_supabase_client",
        lambda: _FakeClient(recorder),
    )

    result = supabase_dashboard.cerrar_caso_derivado("case-1")

    assert result["id"] == "case-1"
    assert result["status"] == "closed"
    assert recorder["table"] == "handoff_cases"
    assert recorder["payload"]["status"] == "closed"       # Estado actualizado
    assert "updated_at" in recorder["payload"]             # Timestamp de actualización
    assert recorder["eq"] == ("id", "case-1")              # Filtro por ID


# Verifica que la consulta de mensajes lea el historial correcto
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
    assert recorder["select"] == "*"              # Selecciona todas las columnas
    assert recorder["eq"] == ("conversation_id", "conv-1")  # Filtra por conversación
    assert recorder["order"] == ("created_at", False)        # Orden cronológico ascendente


# Verifica que la respuesta humana se envíe al backend correctamente
def test_enviar_respuesta_humana_llama_backend(monkeypatch):
    calls = {}

    def fake_call(method, path, json_body=None):
        calls["method"] = method
        calls["path"] = path
        calls["json"] = json_body
        return {
            "message": {
                "id": "msg-1",
                "direction": "outbound",
                "content": json_body["message"],
                "raw_payload": {"source": "dashboard_human"},
            }
        }

    monkeypatch.setattr(supabase_dashboard, "_call_backend", fake_call)

    result = supabase_dashboard.enviar_respuesta_humana(
        case_id="case-1",
        conversation_id="conv-1",
        user_id="user-1",
        phone="593999000111",
        content="Hola, soy el asesor.",
    )

    assert calls["method"] == "POST"
    assert calls["path"] == "/admin/handoff/case-1/reply"   # Ruta del endpoint
    assert calls["json"] == {"message": "Hola, soy el asesor."}  # Cuerpo del mensaje
    assert result["content"] == "Hola, soy el asesor."      # Contenido en la respuesta


# Verifica que la respuesta como asesor envíe WhatsApp y guarde el mensaje
def test_reply_as_advisor_envia_whatsapp_y_persiste(monkeypatch):
    monkeypatch.setattr(
        handoff_service.handoff_repository,
        "get_handoff_case_by_id",
        lambda case_id: {
            "id": case_id,
            "status": "pending",
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "transcript": [],
        },
    )
    monkeypatch.setattr(
        handoff_service.user_repository,
        "get_user_by_id",
        lambda user_id: {"id": user_id, "phone": "593999000111"},
    )
    monkeypatch.setattr(
        handoff_service,
        "send_text_message",
        lambda phone, message: {"messages": [{"id": "wamid.1"}]},
    )
    monkeypatch.setattr(
        handoff_service.message_repository,
        "save_outbound_message",
        lambda **kwargs: {"id": "msg-1", **kwargs},
    )
    monkeypatch.setattr(
        handoff_service.handoff_repository,
        "update_handoff_case",
        lambda case_id, **kwargs: {"id": case_id, "status": kwargs["status"]},
    )

    result = handoff_service.reply_as_advisor("case-1", "Respuesta del asesor")

    assert result["phone"] == "593999000111"
    assert result["message"]["content"] == "Respuesta del asesor"
    assert result["case"]["status"] == "assigned"  # Estado cambia a asignado


# Verifica que no se permita enviar mensajes vacíos como asesor
def test_reply_as_advisor_rechaza_vacio():
    with pytest.raises(ValueError, match="Escribe un mensaje"):
        handoff_service.reply_as_advisor("case-1", "   ")
