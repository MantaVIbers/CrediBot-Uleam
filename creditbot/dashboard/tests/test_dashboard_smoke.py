from pathlib import Path

from streamlit.testing.v1 import AppTest

import components.navigation as navigation
import components.ui as ui
import services.supabase_dashboard as dashboard_service


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]

USERS = [
    {
        "id": "user-1",
        "full_name": "Cliente Demo",
        "phone": "593991234567",
        "cedula": "0912345675",
        "consent_given": True,
        "consent_at": "2026-07-13T10:00:00Z",
        "created_at": "2026-07-13T09:00:00Z",
    }
]
REQUESTS = [
    {
        "id": "request-1",
        "user_id": "user-1",
        "conversation_id": "conversation-1",
        "cedula": "0912345675",
        "requested_amount": 3000,
        "term_months": 12,
        "monthly_income": 1500,
        "estimated_payment": 250,
        "result": "preaprobado",
        "status": "completed",
        "created_at": "2026-07-13T10:00:00Z",
    }
]
CASES = [
    {
        "id": "case-1",
        "user_id": "user-1",
        "credit_request_id": "request-1",
        "conversation_id": "conversation-1",
        "reason": "user_requested_advisor",
        "status": "pending",
        "created_at": "2026-07-13T10:05:00Z",
    }
]
AUDIT = [
    {
        "id": "audit-1",
        "conversation_id": "conversation-1",
        "tool_name": "precalificar_credito",
        "success": True,
        "latency_ms": 120,
        "input_payload": {"cedula": "0912345675"},
        "output_payload": {"result": "preaprobado"},
        "created_at": "2026-07-13T10:06:00Z",
    }
]


def _patch_dashboard(monkeypatch) -> None:
    monkeypatch.setattr(navigation, "render_sidebar", lambda *args, **kwargs: None)
    monkeypatch.setattr(ui, "render_data_toolbar", lambda *args, **kwargs: False)
    monkeypatch.setattr(dashboard_service, "obtener_usuarios", lambda: USERS)
    monkeypatch.setattr(dashboard_service, "obtener_solicitudes", lambda: REQUESTS)
    monkeypatch.setattr(dashboard_service, "obtener_casos_derivados", lambda: CASES)
    monkeypatch.setattr(dashboard_service, "obtener_auditoria_ia", lambda: AUDIT)
    monkeypatch.setattr(dashboard_service, "obtener_mensajes_conversacion", lambda _id: [])
    monkeypatch.setattr(
        dashboard_service,
        "obtener_estado_backend",
        lambda: {"online": True, "url": "http://localhost:8000", "detail": {}},
    )
    monkeypatch.setattr(
        dashboard_service,
        "obtener_estado_configuracion",
        lambda: {
            "supabase": True,
            "backend_api": True,
            "can_reply": True,
            "reply_mode": "backend_api",
            "backend_url": "http://localhost:8000",
        },
    )


def test_all_dashboard_pages_render_with_demo_data(monkeypatch) -> None:
    _patch_dashboard(monkeypatch)
    pages = [
        "app.py",
        "pages/1_Simulador.py",
        "pages/2_Solicitudes.py",
        "pages/3_Casos_Derivados.py",
            "pages/4_Usuarios.py",
            "pages/5_Auditoria_IA.py",
            "pages/6_Conversaciones.py",
        ]
    for relative_path in pages:
        app = AppTest.from_file(str(DASHBOARD_ROOT / relative_path), default_timeout=20)
        app.session_state["dashboard_authenticated"] = True
        app.run()
        assert not app.exception, f"{relative_path}: {app.exception}"


def test_summary_case_opens_selected_handoff(monkeypatch) -> None:
    _patch_dashboard(monkeypatch)
    app = AppTest.from_file(str(DASHBOARD_ROOT / "app.py"), default_timeout=20)
    app.session_state["dashboard_authenticated"] = True
    app.run()
    open_button = next(button for button in app.button if button.label == "Abrir caso")
    open_button.click()
    app.run()
    assert not app.exception
    assert app.session_state["selected_handoff_case_id"] == "case-1"
