"""Pruebas del flujo conversacional completo del bot."""
from unittest.mock import patch

from app.core.constants import (
    ASK_AMOUNT,
    ASK_INCOME,
    ASK_NAME,
    ASK_TERM,
    CONFIRM_DATA,
    MENU,
    SHOW_RESULT,
    START,
)
from app.services.conversation_service import process_message

# IDs ficticios para las pruebas
USER_ID = "user-1"
CONVERSATION_ID = "conv-1"
REQUEST_ID = "req-1"


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
        "requested_amount": None,
        "term_months": None,
        "monthly_income": None,
        "status": "draft",
    }
    data.update(overrides)
    return data


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
):
    """Prueba el flujo completo desde START hasta SHOW_RESULT con datos válidos."""
    user = _base_user()
    mock_get_user.return_value = user

    states = [
        START,
        MENU,
        ASK_NAME,
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
        _draft_request(),
        _draft_request(requested_amount=500),
        _draft_request(requested_amount=500, term_months=12),
        _draft_request(requested_amount=500, term_months=12, monthly_income=700),
        _draft_request(requested_amount=500, term_months=12, monthly_income=700),
    ]

    with patch(
        "app.services.conversation_service.user_repository.update_user_name",
        return_value={**user, "full_name": "Carlos Ortiz"},
    ), patch(
        "app.services.conversation_service.credit_repository.update_amount",
        return_value=_draft_request(requested_amount=500),
    ), patch(
        "app.services.conversation_service.credit_repository.update_term",
        return_value=_draft_request(requested_amount=500, term_months=12),
    ), patch(
        "app.services.conversation_service.credit_repository.update_income",
        return_value=_draft_request(
            requested_amount=500, term_months=12, monthly_income=700
        ),
    ), patch(
        "app.services.conversation_service.credit_repository.save_result",
        return_value=_draft_request(
            requested_amount=500,
            term_months=12,
            monthly_income=700,
            result="preaprobado",
        ),
    ):
        reply_start = process_message("593999999999", "Hola")
        assert "CrediBot" in reply_start

        reply_menu = process_message("593999999999", "1")
        assert "nombre completo" in reply_menu.lower()
        mock_create_draft.assert_called_once()

        reply_name = process_message("593999999999", "Carlos Ortiz")
        assert "monto" in reply_name.lower()

        reply_amount = process_message("593999999999", "500")
        assert "meses" in reply_amount.lower()

        reply_term = process_message("593999999999", "12")
        assert "ingreso" in reply_term.lower()

        reply_income = process_message("593999999999", "700")
        assert "Resumen" in reply_income
        assert "Carlos Ortiz" in reply_income

        reply_confirm = process_message("593999999999", "1")
        assert "Preaprobado" in reply_confirm

    assert mock_save_inbound.call_count == 7
    assert mock_save_outbound.call_count == 7
