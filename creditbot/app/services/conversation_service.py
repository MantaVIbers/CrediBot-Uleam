from typing import Any

from app.core.constants import (
    ASK_AMOUNT,
    ASK_INCOME,
    ASK_NAME,
    ASK_TERM,
    CONFIRM_DATA,
    CREDIT_RESULT_OBSERVED,
    CREDIT_RESULT_PREAPPROVED,
    FINISHED,
    HANDOFF_REQUESTED,
    MENU,
    SHOW_RESULT,
    START,
)
from app.repositories import conversation_repository, credit_repository, message_repository, user_repository
from app.services import credit_service, handoff_service, message_service, validation_service

HANDOFF_KEYWORDS = {"asesor", "humano", "persona", "agente"}
MAX_VALIDATION_FAILURES = 3

_validation_failures: dict[str, int] = {}


def _parse_amount(value: str) -> float:
    return float(value.replace(",", ".").strip())


def _parse_term(value: str) -> int:
    return int(value.strip())


def _parse_income(value: str) -> float:
    return float(value.replace(",", ".").strip())


def _build_summary_data(user: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": user.get("full_name") or "Cliente",
        "amount": float(request["requested_amount"]),
        "term": int(request["term_months"]),
        "income": float(request["monthly_income"]),
    }


def _build_result_data(request: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    return {
        "estimated_payment": float(evaluation["estimated_payment"]),
        "payment_capacity": float(evaluation["payment_capacity"]),
        "result": evaluation["result"],
    }


def _reset_validation_failures(conversation_id: str) -> None:
    _validation_failures.pop(conversation_id, None)


def _track_validation_failure(conversation_id: str) -> bool:
    count = _validation_failures.get(conversation_id, 0) + 1
    _validation_failures[conversation_id] = count
    return count >= MAX_VALIDATION_FAILURES


def _request_handoff(
    conversation_id: str,
    user_id: str,
    response: str,
    reason: str,
    credit_request_id: str | None = None,
) -> str:
    handoff_service.register_handoff(
        user_id=user_id,
        conversation_id=conversation_id,
        reason=reason,
        credit_request_id=credit_request_id,
    )
    _reset_validation_failures(conversation_id)
    conversation_repository.update_state(conversation_id, HANDOFF_REQUESTED)
    conversation_repository.update_last_message(conversation_id, response)
    conversation_repository.finish_conversation(conversation_id)
    message_repository.save_outbound_message(conversation_id, user_id, response)
    return response


def _handle_validation_failure(
    conversation_id: str,
    user_id: str,
    response: str,
) -> str | None:
    if _track_validation_failure(conversation_id):
        return _request_handoff(
            conversation_id,
            user_id,
            message_service.handoff_message(),
            reason="repeated_invalid_input",
        )
    return response


def process_message(phone: str, text: str, raw_payload: dict[str, Any] | None = None) -> str:
    user = user_repository.get_or_create_user(phone)
    user_id = user["id"]

    conversation = conversation_repository.get_or_create_active_conversation(user_id)
    conversation_id = conversation["id"]
    state = conversation["current_state"]

    message_repository.save_inbound_message(
        conversation_id, user_id, text, raw_payload=raw_payload
    )

    normalized_text = text.strip().lower()
    if state not in {HANDOFF_REQUESTED, FINISHED} and any(
        keyword in normalized_text for keyword in HANDOFF_KEYWORDS
    ):
        return _request_handoff(
            conversation_id,
            user_id,
            message_service.handoff_message(),
            reason="user_requested_advisor",
        )

    response = ""
    next_state = state

    if state == START:
        response = message_service.welcome_message()
        next_state = MENU

    elif state == MENU:
        is_valid, _ = validation_service.validate_menu_option(text)
        if not is_valid:
            handoff_response = _handle_validation_failure(
                conversation_id,
                user_id,
                message_service.invalid_menu_message() + "\n\n" + message_service.welcome_message(),
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_menu_message() + "\n\n" + message_service.welcome_message()
            next_state = MENU
        elif text.strip() == "1":
            _reset_validation_failures(conversation_id)
            credit_repository.create_draft_request(user_id, conversation_id)
            response = message_service.ask_name_message()
            next_state = ASK_NAME
        elif text.strip() == "2":
            _reset_validation_failures(conversation_id)
            response = message_service.general_info_message()
            next_state = MENU
        elif text.strip() == "3":
            return _request_handoff(
                conversation_id,
                user_id,
                message_service.handoff_message(),
                reason="menu_option_3",
            )

    elif state == ASK_NAME:
        is_valid, _ = validation_service.validate_name(text)
        if not is_valid:
            handoff_response = _handle_validation_failure(
                conversation_id, user_id, message_service.invalid_name_message()
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_name_message()
            next_state = ASK_NAME
        else:
            _reset_validation_failures(conversation_id)
            user_repository.update_user_name(user_id, text.strip())
            user["full_name"] = text.strip()
            response = message_service.ask_amount_message(user.get("full_name"))
            next_state = ASK_AMOUNT

    elif state == ASK_AMOUNT:
        is_valid, _ = validation_service.validate_amount(text)
        if not is_valid:
            handoff_response = _handle_validation_failure(
                conversation_id, user_id, message_service.invalid_amount_message()
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_amount_message()
            next_state = ASK_AMOUNT
        else:
            _reset_validation_failures(conversation_id)
            request = credit_repository.get_draft_request(conversation_id)
            if request:
                credit_repository.update_amount(request["id"], _parse_amount(text))
            response = message_service.ask_term_message()
            next_state = ASK_TERM

    elif state == ASK_TERM:
        is_valid, _ = validation_service.validate_term(text)
        if not is_valid:
            handoff_response = _handle_validation_failure(
                conversation_id, user_id, message_service.invalid_term_message()
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_term_message()
            next_state = ASK_TERM
        else:
            _reset_validation_failures(conversation_id)
            request = credit_repository.get_draft_request(conversation_id)
            if request:
                credit_repository.update_term(request["id"], _parse_term(text))
            response = message_service.ask_income_message()
            next_state = ASK_INCOME

    elif state == ASK_INCOME:
        is_valid, _ = validation_service.validate_income(text)
        if not is_valid:
            handoff_response = _handle_validation_failure(
                conversation_id, user_id, message_service.invalid_income_message()
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_income_message()
            next_state = ASK_INCOME
        else:
            _reset_validation_failures(conversation_id)
            request = credit_repository.get_draft_request(conversation_id)
            if request:
                credit_repository.update_income(request["id"], _parse_income(text))
                request = credit_repository.get_draft_request(conversation_id)
            if request:
                summary = _build_summary_data(user, request)
                response = message_service.confirm_data_message(summary)
            next_state = CONFIRM_DATA

    elif state == CONFIRM_DATA:
        is_valid, _ = validation_service.validate_confirmation(text)
        if not is_valid:
            handoff_response = _handle_validation_failure(
                conversation_id, user_id, message_service.invalid_confirmation_message()
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_confirmation_message()
            next_state = CONFIRM_DATA
        elif text.strip() == "1":
            _reset_validation_failures(conversation_id)
            request = credit_repository.get_draft_request(conversation_id)
            if not request:
                response = message_service.welcome_message()
                next_state = MENU
            else:
                evaluation = credit_service.evaluate_credit_request(
                    float(request["requested_amount"]),
                    int(request["term_months"]),
                    float(request["monthly_income"]),
                )
                credit_repository.save_result(
                    request["id"],
                    float(evaluation["estimated_payment"]),
                    float(evaluation["payment_capacity"]),
                    str(evaluation["result"]),
                )
                result_data = _build_result_data(request, evaluation)
                if evaluation["result"] == CREDIT_RESULT_PREAPPROVED:
                    response = message_service.preapproved_message(result_data)
                elif evaluation["result"] == CREDIT_RESULT_OBSERVED:
                    response = message_service.observed_message(result_data)
                    handoff_service.register_handoff(
                        user_id=user_id,
                        conversation_id=conversation_id,
                        reason="observed_result",
                        credit_request_id=request["id"],
                    )
                else:
                    response = message_service.not_qualified_message(result_data)
                next_state = SHOW_RESULT
        elif text.strip() == "2":
            _reset_validation_failures(conversation_id)
            response = message_service.ask_name_message()
            next_state = ASK_NAME

    elif state == SHOW_RESULT:
        response = message_service.finished_message()
        next_state = FINISHED
        conversation_repository.finish_conversation(conversation_id)

    elif state in {HANDOFF_REQUESTED, FINISHED}:
        user = user_repository.get_or_create_user(phone)
        conversation = conversation_repository.get_or_create_active_conversation(user["id"])
        conversation_id = conversation["id"]
        state = conversation["current_state"]
        response = message_service.welcome_message()
        next_state = MENU

    if next_state != state:
        conversation_repository.update_state(conversation_id, next_state)

    conversation_repository.update_last_message(conversation_id, response)
    message_repository.save_outbound_message(conversation_id, user_id, response)
    return response
