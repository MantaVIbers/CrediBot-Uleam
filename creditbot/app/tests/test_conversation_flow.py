"""Pruebas del flujo conversacional completo del bot (v2 con cédula + consentimiento)."""
from unittest.mock import patch

from app.core.constants import (
    ASK_AMOUNT,
    ASK_CEDULA,
    ASK_INCOME,
    ASK_NAME,
    ASK_PURPOSE,
    ASK_TERM,
    CONFIRM_DATA,
    CONSENT,
    CREDIT_RESULT_PREAPPROVED,
    FINISHED,
    MENU,
    SHOW_RESULT,
    START,
)
from app.services.conversation_service import _contains_handoff_keyword, process_message

# IDs ficticios para las pruebas
USER_ID = "user-1"
CONVERSATION_ID = "conv-1"
REQUEST_ID = "req-1"

# Cédula ficticia pero válida (algoritmo módulo 10)
CEDULA = "0912345675"


def _base_user():
    """Retorna un usuario base de prueba."""
    return {"id": USER_ID, "phone": "593999999999", "full_name": None}


def _base_conversation(state: str = START):
    """Retorna una conversación base de prueba en un estado dado."""
    return {
        "id": CONVERSATION_ID,
        "user_id": USER_ID,
        "current_state": state,
        "is_active": True,
    }


def _draft_request(**overrides):
    """Retorna una solicitud draft base de prueba con valores opcionales."""
    data = {
        "id": REQUEST_ID,
        "user_id": USER_ID,
        "conversation_id": CONVERSATION_ID,
        "cedula": None,
        "loan_purpose": None,
        "requested_amount": None,
        "term_months": None,
        "monthly_income": None,
        "status": "draft",
    }
    data.update(overrides)
    return data


def _preapproved_evaluation():
    """Resultado de precalificación v2 preaprobado para las pruebas."""
    return {
        "ok": True,
        "result": CREDIT_RESULT_PREAPPROVED,
        "categoria": "excelente",
        "motivo": None,
        "tea": 0.145,
        "capacidad_pago": 525.0,
        "monto_maximo": 3000.0,
        "cuota_estimada": 270.0,
        "plazo_meses": 12,
        "credit_score": 820,
    }


@patch("app.services.conversation_service.precalificacion_service.precalificar_por_cedula")
@patch("app.services.conversation_service.credit_repository.save_result_v2")
@patch("app.services.conversation_service.user_repository.update_cedula_consent")
@patch("app.services.conversation_service.credit_repository.update_purpose")
@patch("app.services.conversation_service.credit_repository.update_cedula")
@patch("app.services.conversation_service.message_repository.save_outbound_message")
@patch("app.services.conversation_service.message_repository.save_inbound_message")
@patch("app.services.conversation_service.conversation_repository.update_last_message")
@patch("app.services.conversation_service.conversation_repository.update_state")
@patch("app.services.conversation_service.credit_repository.get_draft_request")
@patch("app.services.conversation_service.credit_repository.create_draft_request")
@patch("app.services.conversation_service.conversation_repository.get_or_create_active_conversation")
@patch("app.services.conversation_service.user_repository.get_or_create_user")
def test_conversation_flow_basic(
    mock_get_user,
    mock_get_conversation,
    mock_create_draft,
    mock_get_draft,
    mock_update_state,
    mock_update_last_message,
    mock_save_inbound,
    mock_save_outbound,
    mock_update_cedula,
    mock_update_purpose,
    mock_update_cedula_consent,
    mock_save_result_v2,
    mock_precalificar,
):
    """Prueba el flujo completo desde START hasta SHOW_RESULT con datos válidos."""
    user = _base_user()
    mock_get_user.return_value = user

    states = [
        START,
        MENU,
        ASK_NAME,
        ASK_CEDULA,
        CONSENT,
        ASK_PURPOSE,
        ASK_AMOUNT,
        ASK_TERM,
        ASK_INCOME,
        CONFIRM_DATA,
        SHOW_RESULT,
    ]
    state_index = {"value": 0}

    def conversation_side_effect(_user_id):
        return _base_conversation(states[state_index["value"]])

    def update_state_side_effect(_conversation_id, new_state):
        state_index["value"] = states.index(new_state)

    mock_get_conversation.side_effect = conversation_side_effect
    mock_update_state.side_effect = update_state_side_effect
    mock_get_draft.side_effect = [
        _draft_request(),                                                        # ASK_CEDULA
        _draft_request(cedula=CEDULA),                                           # CONSENT (lee cédula persistida)
        _draft_request(cedula=CEDULA),                                           # ASK_PURPOSE
        _draft_request(cedula=CEDULA, loan_purpose="estudios"),                  # ASK_AMOUNT
        _draft_request(cedula=CEDULA, loan_purpose="estudios", requested_amount=500),  # ASK_TERM
        _draft_request(cedula=CEDULA, loan_purpose="estudios", requested_amount=500, term_months=12),  # ASK_INCOME (lectura)
        _draft_request(cedula=CEDULA, loan_purpose="estudios", requested_amount=500, term_months=12, monthly_income=700),  # ASK_INCOME (relectura)
        _draft_request(cedula=CEDULA, loan_purpose="estudios", requested_amount=500, term_months=12, monthly_income=700),  # CONFIRM_DATA
    ]
    mock_precalificar.return_value = _preapproved_evaluation()

    with patch(
        "app.services.conversation_service.user_repository.update_user_name",
        return_value={**user, "full_name": "Carlos Ortiz"},
    ), patch(
        "app.services.conversation_service.credit_repository.update_amount",
        return_value=_draft_request(cedula=CEDULA, requested_amount=500),
    ), patch(
        "app.services.conversation_service.credit_repository.update_term",
        return_value=_draft_request(cedula=CEDULA, requested_amount=500, term_months=12),
    ), patch(
        "app.services.conversation_service.credit_repository.update_income",
        return_value=_draft_request(
            cedula=CEDULA, requested_amount=500, term_months=12, monthly_income=700
        ),
    ):
        reply_start = process_message("593999999999", "Hola")
        assert "CrediBot" in reply_start

        reply_menu = process_message("593999999999", "1")
        assert "nombre completo" in reply_menu.lower()
        mock_create_draft.assert_called_once()

        reply_name = process_message("593999999999", "Carlos Ortiz")
        assert "cédula" in reply_name.lower()

        reply_cedula = process_message("593999999999", CEDULA)
        assert "autoriz" in reply_cedula.lower()
        mock_update_cedula.assert_called_once()

        reply_consent = process_message("593999999999", "1")
        assert "para qué" in reply_consent.lower()
        mock_update_cedula_consent.assert_called_once()

        reply_purpose = process_message("593999999999", "estudios")
        assert "monto" in reply_purpose.lower()
        mock_update_purpose.assert_called_once()

        reply_amount = process_message("593999999999", "500")
        assert "meses" in reply_amount.lower()

        reply_term = process_message("593999999999", "12")
        assert "ingreso" in reply_term.lower()

        reply_income = process_message("593999999999", "700")
        assert "Resumen" in reply_income
        assert "Carlos Ortiz" in reply_income

        reply_confirm = process_message("593999999999", "1")
        assert "Preaprobado" in reply_confirm
        mock_precalificar.assert_called_once()
        mock_save_result_v2.assert_called_once()

    assert mock_save_inbound.call_count == 10
    assert mock_save_outbound.call_count == 10


def test_contains_handoff_keyword():
    """Verifica que las palabras clave de derivación coincidan solo como palabras completas."""
    assert _contains_handoff_keyword("quiero hablar con un asesor") is True
    assert _contains_handoff_keyword("impersonal") is False
    assert _contains_handoff_keyword("necesito un agente") is True
    assert _contains_handoff_keyword("credito para persona natural") is False
    assert _contains_handoff_keyword("hablar con una persona") is True


@patch("app.services.conversation_service.openai_agent.render_reply", side_effect=lambda **kwargs: kwargs["base_reply"])
@patch("app.services.conversation_service.message_repository.save_outbound_message")
@patch("app.services.conversation_service.message_repository.save_inbound_message")
@patch("app.services.conversation_service.conversation_repository.update_last_message")
@patch("app.services.conversation_service.conversation_repository.update_state")
@patch("app.services.conversation_service.conversation_repository.get_or_create_active_conversation")
@patch("app.services.conversation_service.user_repository.get_or_create_user")
def test_policy_question_keeps_current_state(
    mock_get_user,
    mock_get_conversation,
    mock_update_state,
    mock_update_last_message,
    mock_save_inbound,
    mock_save_outbound,
    mock_render,
):
    """Una duda informativa usa RAG y no rompe el paso actual."""
    mock_get_user.return_value = {**_base_user(), "full_name": "Carlos Ortiz"}
    mock_get_conversation.return_value = _base_conversation(ASK_AMOUNT)

    reply = process_message("593999999999", "qué requisitos necesito?")

    assert "políticas internas" in reply
    assert "Requisitos básicos" in reply
    assert "Para continuar" in reply
    assert "monto" in reply.lower()
    mock_update_state.assert_not_called()


@patch("app.services.conversation_service.message_repository.save_outbound_message")
@patch("app.services.conversation_service.message_repository.save_inbound_message")
@patch("app.services.conversation_service.conversation_repository.update_last_message")
@patch("app.services.conversation_service.conversation_repository.get_or_create_active_conversation")
@patch("app.services.conversation_service.user_repository.get_or_create_user")
def test_invalid_cedula_stays_in_ask_cedula(
    mock_get_user,
    mock_get_conversation,
    mock_update_last_message,
    mock_save_inbound,
    mock_save_outbound,
):
    """Una cédula inválida no avanza el flujo y pide reintentar."""
    mock_get_user.return_value = {**_base_user(), "full_name": "Carlos Ortiz"}
    mock_get_conversation.return_value = _base_conversation(ASK_CEDULA)

    reply = process_message("593999999999", "1234567890")

    assert "no es válida" in reply.lower()


@patch("app.services.conversation_service.conversation_repository.finish_conversation")
@patch("app.services.conversation_service.message_repository.save_outbound_message")
@patch("app.services.conversation_service.message_repository.save_inbound_message")
@patch("app.services.conversation_service.conversation_repository.update_last_message")
@patch("app.services.conversation_service.conversation_repository.update_state")
@patch("app.services.conversation_service.conversation_repository.get_or_create_active_conversation")
@patch("app.services.conversation_service.user_repository.get_or_create_user")
def test_consent_declined_finishes_conversation(
    mock_get_user,
    mock_get_conversation,
    mock_update_state,
    mock_update_last_message,
    mock_save_inbound,
    mock_save_outbound,
    mock_finish,
):
    """Si el usuario no autoriza la consulta del buró, la conversación termina."""
    mock_get_user.return_value = {**_base_user(), "full_name": "Carlos Ortiz", "cedula": CEDULA}
    mock_get_conversation.return_value = _base_conversation(CONSENT)

    reply = process_message("593999999999", "2")

    assert "autorización" in reply.lower()
    mock_update_state.assert_called_once_with(CONVERSATION_ID, FINISHED)
    mock_finish.assert_called_once_with(CONVERSATION_ID)
