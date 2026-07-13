"""Pruebas del flujo conversacional v2 alineado al documento de requisitos.

Orden: START → MENU → CONSENT → ASK_CEDULA → VERIFY → PURPOSE → AMOUNT → TERM → INCOME → CONFIRM → RESULT
"""
from unittest.mock import patch

from app.core.constants import (
    ASK_AMOUNT,
    ASK_CEDULA,
    ASK_INCOME,
    ASK_PURPOSE,
    ASK_TERM,
    CONFIRM_DATA,
    CONSENT,
    CREDIT_RESULT_PREAPPROVED,
    FINISHED,
    MENU,
    NOT_ELIGIBLE,
    SHOW_RESULT,
    START,
)
from app.services.conversation_service import _contains_handoff_keyword, process_message

# Constantes de prueba para el flujo conversacional
USER_ID = "user-1"
CONVERSATION_ID = "conv-1"
REQUEST_ID = "req-1"
CEDULA = "0912345675"


# Funciones auxiliares para crear datos de prueba
def _base_user():
    return {"id": USER_ID, "phone": "593999999999", "full_name": None}


def _base_conversation(state: str = START):
    """Crea una conversación base en el estado indicado."""
    return {
        "id": CONVERSATION_ID,
        "user_id": USER_ID,
        "current_state": state,
        "is_active": True,
    }


def _draft_request(**overrides):
    """Crea una solicitud de crédito en borrador con valores por defecto."""
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


def _eligible_profile():
    """Perfil crediticio elegible (score 720, sin mora)."""
    return {
        "cedula": CEDULA,
        "full_name": "María González López",
        "credit_score": 720,
        "score_category": "aceptable",
        "has_delinquency": False,
        "delinquency_days": 0,
        "blacklisted": False,
        "thin_file": False,
        "monthly_installments": 150.0,
    }


def _preapproved_evaluation():
    """Resultado de precalificación preaprobado."""
    return {
        "ok": True,
        "result": CREDIT_RESULT_PREAPPROVED,
        "categoria": "aceptable",
        "motivo": None,
        "tea": 0.16,
        "capacidad_pago": 525.0,
        "monto_maximo": 2800.0,
        "cuota_estimada": 270.0,
        "plazo_meses": 12,
        "credit_score": 720,
    }


@patch("app.services.conversation_service.precalificacion_service.precalificar_por_cedula")
@patch("app.services.conversation_service.credit_repository.save_result_v2")
@patch("app.services.conversation_service.user_repository.update_user_name")
@patch("app.services.conversation_service.user_repository.update_cedula_consent")
@patch("app.services.conversation_service.credit_profile_repository.get_profile_by_cedula")
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
    mock_get_profile,
    mock_update_cedula_consent,
    mock_update_user_name,
    mock_save_result_v2,
    mock_precalificar,
):
    """Flujo completo alineado: consentimiento → cédula → verificación → precalificación."""
    user = _base_user()
    mock_get_user.return_value = user
    mock_get_profile.return_value = _eligible_profile()
    mock_update_user_name.side_effect = lambda uid, name: {**user, "full_name": name}

    states = [
        START,
        MENU,
        CONSENT,
        ASK_CEDULA,
        ASK_PURPOSE,
        ASK_AMOUNT,
        ASK_TERM,
        ASK_INCOME,
        CONFIRM_DATA,
        SHOW_RESULT,
    ]
    state_index = {"value": 0}  # Índice mutable para simular cambio de estado

    def conversation_side_effect(_user_id):
        return _base_conversation(states[state_index["value"]])

    def update_state_side_effect(_conversation_id, new_state):
        state_index["value"] = states.index(new_state)

    mock_get_conversation.side_effect = conversation_side_effect
    mock_update_state.side_effect = update_state_side_effect
    mock_get_draft.side_effect = [
        _draft_request(),                                    # Sin datos aún
        _draft_request(cedula=CEDULA),                       # Después de ingresar cédula
        _draft_request(cedula=CEDULA, loan_purpose="estudios"),  # Después de propósito
        _draft_request(cedula=CEDULA, loan_purpose="estudios", requested_amount=500),  # Después de monto
        _draft_request(
            cedula=CEDULA, loan_purpose="estudios", requested_amount=500, term_months=12
        ),
        _draft_request(
            cedula=CEDULA,
            loan_purpose="estudios",
            requested_amount=500,
            term_months=12,
            monthly_income=700,
        ),
        _draft_request(
            cedula=CEDULA,
            loan_purpose="estudios",
            requested_amount=500,
            term_months=12,
            monthly_income=700,
        ),
    ]
    mock_precalificar.return_value = _preapproved_evaluation()

    with patch(
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
        assert "CrediBot" in reply_start  # Saludo inicial del bot

        reply_menu = process_message("593999999999", "1")
        assert "autoriz" in reply_menu.lower()  # Solicita autorización de datos
        mock_create_draft.assert_called_once()  # Se crea borrador de solicitud

        reply_consent = process_message("593999999999", "1")
        assert "cédula" in reply_consent.lower()  # Pide número de cédula

        reply_cedula = process_message("593999999999", CEDULA)
        assert "María González López" in reply_cedula or "perfil crediticio" in reply_cedula.lower()
        assert "para qué" in reply_cedula.lower()  # Pide propósito del crédito
        mock_update_cedula.assert_called_once()
        mock_update_cedula_consent.assert_called_once()
        mock_get_profile.assert_called_once()  # Consulta perfil crediticio

        reply_purpose = process_message("593999999999", "estudios")
        assert "monto" in reply_purpose.lower()  # Pide monto solicitado

        reply_amount = process_message("593999999999", "500")
        assert "meses" in reply_amount.lower()  # Pide plazo en meses

        reply_term = process_message("593999999999", "12")
        assert "ingreso" in reply_term.lower()  # Pide ingreso mensual

        reply_income = process_message("593999999999", "700")
        assert "Resumen" in reply_income  # Muestra resumen de solicitud

        reply_confirm = process_message("593999999999", "1")
        assert "Preaprobado" in reply_confirm  # Resultado de precalificación
        mock_precalificar.assert_called_once()
        mock_save_result_v2.assert_called_once()

    # Verifica que se guarden 9 mensajes entrantes y 9 salientes
    assert mock_save_inbound.call_count == 9
    assert mock_save_outbound.call_count == 9


# Verifica detección de palabras clave para derivación a asesor humano
def test_contains_handoff_keyword():
    assert _contains_handoff_keyword("quiero hablar con un asesor") is True
    assert _contains_handoff_keyword("impersonal") is False
    assert _contains_handoff_keyword("necesito un agente") is True
    assert _contains_handoff_keyword("credito para persona natural") is False  # No activa handoff
    assert _contains_handoff_keyword("hablar con una persona") is True


@patch(
    "app.services.conversation_service.openai_agent.render_reply",
    side_effect=lambda **kwargs: kwargs["base_reply"],
)
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
    mock_get_user.return_value = {**_base_user(), "full_name": "María González López"}
    mock_get_conversation.return_value = _base_conversation(ASK_AMOUNT)  # Estado pidiendo monto

    reply = process_message("593999999999", "qué requisitos necesito?")

    assert "políticas internas" in reply    # Respuesta de políticas
    assert "Para continuar" in reply         # Indica cómo continuar
    assert "monto" in reply.lower()          # Recuerda el paso pendiente
    mock_update_state.assert_not_called()    # No cambia de estado


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
    mock_get_user.return_value = _base_user()
    mock_get_conversation.return_value = _base_conversation(ASK_CEDULA)

    reply = process_message("593999999999", "1234567890")

    assert "no es válida" in reply.lower()  # Mensaje de error de cédula


@patch("app.services.conversation_service.credit_profile_repository.get_profile_by_cedula")
@patch("app.services.conversation_service.user_repository.update_cedula_consent")
@patch("app.services.conversation_service.credit_repository.update_cedula")
@patch("app.services.conversation_service.credit_repository.get_draft_request")
@patch("app.services.conversation_service.message_repository.save_outbound_message")
@patch("app.services.conversation_service.message_repository.save_inbound_message")
@patch("app.services.conversation_service.conversation_repository.update_last_message")
@patch("app.services.conversation_service.conversation_repository.get_or_create_active_conversation")
@patch("app.services.conversation_service.user_repository.get_or_create_user")
def test_cedula_not_found_stays_in_ask_cedula(
    mock_get_user,
    mock_get_conversation,
    mock_update_last_message,
    mock_save_inbound,
    mock_save_outbound,
    mock_get_draft,
    mock_update_cedula,
    mock_update_consent,
    mock_get_profile,
):
    mock_get_user.return_value = _base_user()
    mock_get_conversation.return_value = _base_conversation(ASK_CEDULA)
    mock_get_draft.return_value = _draft_request()
    mock_get_profile.return_value = None

    reply = process_message("593999999999", CEDULA)

    assert "no encontramos" in reply.lower()  # Mensaje de cédula no encontrada


@patch("app.services.conversation_service.conversation_repository.finish_conversation")
@patch("app.services.conversation_service.user_repository.update_user_name")
@patch("app.services.conversation_service.credit_profile_repository.get_profile_by_cedula")
@patch("app.services.conversation_service.user_repository.update_cedula_consent")
@patch("app.services.conversation_service.credit_repository.update_cedula")
@patch("app.services.conversation_service.credit_repository.get_draft_request")
@patch("app.services.conversation_service.message_repository.save_outbound_message")
@patch("app.services.conversation_service.message_repository.save_inbound_message")
@patch("app.services.conversation_service.conversation_repository.update_last_message")
@patch("app.services.conversation_service.conversation_repository.update_state")
@patch("app.services.conversation_service.conversation_repository.get_or_create_active_conversation")
@patch("app.services.conversation_service.user_repository.get_or_create_user")
def test_high_risk_score_marks_not_eligible(
    mock_get_user,
    mock_get_conversation,
    mock_update_state,
    mock_update_last_message,
    mock_save_inbound,
    mock_save_outbound,
    mock_get_draft,
    mock_update_cedula,
    mock_update_consent,
    mock_get_profile,
    mock_update_name,
    mock_finish,
):
    mock_get_user.return_value = _base_user()
    mock_get_conversation.return_value = _base_conversation(ASK_CEDULA)
    mock_get_draft.return_value = _draft_request()
    mock_get_profile.return_value = {
        "cedula": CEDULA,
        "full_name": "Usuario Riesgo",
        "credit_score": 280,              # Score de alto riesgo
        "has_delinquency": False,
        "delinquency_days": 0,
        "blacklisted": False,
        "thin_file": False,
    }

    reply = process_message("593999999999", CEDULA)

    assert "no podemos continuar" in reply.lower() or "alto riesgo" in reply.lower()
    mock_update_state.assert_called_with(CONVERSATION_ID, NOT_ELIGIBLE)  # Estado de no elegible
    mock_finish.assert_called_once()  # Conversación finalizada


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
    mock_get_user.return_value = _base_user()
    mock_get_conversation.return_value = _base_conversation(CONSENT)

    reply = process_message("593999999999", "2")

    assert "autorización" in reply.lower()  # Confirma rechazo de autorización
    mock_update_state.assert_called_once_with(CONVERSATION_ID, FINISHED)
    mock_finish.assert_called_once_with(CONVERSATION_ID)  # Conversación finalizada


@patch("app.services.conversation_service.openai_agent.render_reply", side_effect=lambda base_reply, **kwargs: base_reply)
@patch("app.services.conversation_service.message_repository.save_outbound_message")
@patch("app.services.conversation_service.message_repository.save_inbound_message")
@patch("app.services.conversation_service.conversation_repository.update_last_message")
@patch("app.services.conversation_service.conversation_repository.update_state")
@patch("app.services.conversation_service.conversation_repository.get_or_create_active_conversation")
@patch("app.services.conversation_service.user_repository.get_or_create_user")
def test_menu_option_2_returns_policy_info(
    mock_get_user,
    mock_get_conversation,
    mock_update_state,
    mock_update_last_message,
    mock_save_inbound,
    mock_save_outbound,
    _mock_render,
):
    """La opción 2 responde con políticas y permanece en el menú."""
    mock_get_user.return_value = _base_user()
    mock_get_conversation.return_value = _base_conversation(MENU)

    reply_menu = process_message("593999999999", "2")

    assert "política" in reply_menu.lower() or "información" in reply_menu.lower()
    mock_update_state.assert_not_called()  # Permanece en menú


@patch("app.services.conversation_service.openai_agent.render_reply", side_effect=lambda base_reply, **kwargs: base_reply)
@patch("app.services.conversation_service.credit_repository.update_term")
@patch("app.services.conversation_service.credit_repository.update_amount")
@patch("app.services.conversation_service.credit_repository.get_draft_request")
@patch("app.services.conversation_service.message_repository.save_outbound_message")
@patch("app.services.conversation_service.message_repository.save_inbound_message")
@patch("app.services.conversation_service.conversation_repository.update_last_message")
@patch("app.services.conversation_service.conversation_repository.update_state")
@patch("app.services.conversation_service.conversation_repository.get_or_create_active_conversation")
@patch("app.services.conversation_service.user_repository.get_or_create_user")
def test_ask_term_accepts_un_ano_as_12_months(
    mock_get_user,
    mock_get_conversation,
    mock_update_state,
    mock_update_last_message,
    mock_save_inbound,
    mock_save_outbound,
    mock_get_draft,
    mock_update_amount,
    mock_update_term,
    mock_update_income,
):
    """El flujo interpreta 'un año' como 12 meses en el paso de plazo."""
    user = {**_base_user(), "full_name": "Carlos Ortiz"}
    mock_get_user.return_value = user
    mock_get_conversation.return_value = _base_conversation(ASK_TERM)
    mock_get_draft.return_value = _draft_request(cedula=CEDULA, requested_amount=5000)
    mock_update_term.return_value = _draft_request(cedula=CEDULA, requested_amount=5000, term_months=12)

    reply = process_message("593999999999", "un año")

    assert "ingreso" in reply.lower()  # Avanza al paso de ingreso
    mock_update_term.assert_called_once()
    assert mock_update_term.call_args[0][1] == 12  # "un año" = 12 meses
