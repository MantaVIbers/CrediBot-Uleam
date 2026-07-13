"""Lógica principal del flujo conversacional del bot."""
import re
from typing import Any

from app.core.constants import (
    ASK_AMOUNT,
    ASK_CEDULA,
    ASK_INCOME,
    ASK_NAME,
    ASK_TERM,
    CONFIRM_DATA,
    CONSENT,
    CREDIT_RESULT_OBSERVED,
    CREDIT_RESULT_PREAPPROVED,
    FINISHED,
    HANDOFF_REQUESTED,
    MENU,
    SHOW_RESULT,
    START,
)
from app.domain.cedula_validator import mask_cedula
from app.repositories import conversation_repository, credit_repository, message_repository, user_repository
from app.services import handoff_service, message_service, precalificacion_service, validation_service

# Palabras clave que el usuario puede escribir para solicitar un asesor humano
HANDOFF_KEYWORDS = {"asesor", "humano", "persona", "agente"}
# Cantidad máxima de fallos de validación antes de derivar a asesor
MAX_VALIDATION_FAILURES = 3

# Contador de fallos de validación por conversación (en memoria)
_validation_failures: dict[str, int] = {}


def _parse_amount(value: str) -> float:
    """Convierte el texto del monto a float."""
    return validation_service.parse_numeric_value(value)


def _parse_term(value: str) -> int:
    """Convierte el texto del plazo a entero."""
    return int(value.strip())


def _parse_income(value: str) -> float:
    """Convierte el texto del ingreso a float."""
    return validation_service.parse_numeric_value(value)


def _clean_cedula(value: str) -> str:
    """Normaliza la cédula quitando espacios y guiones."""
    return value.strip().replace("-", "").replace(" ", "")


def _build_summary_data(user: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Construye un dict con los datos resumidos para confirmación del usuario."""
    cedula = request.get("cedula") or user.get("cedula")
    return {
        "name": user.get("full_name") or "Cliente",
        "cedula": mask_cedula(cedula) if cedula else None,
        "amount": float(request["requested_amount"]),
        "term": int(request["term_months"]),
        "income": float(request["monthly_income"]),
    }


def _build_result_data(evaluation: dict[str, Any]) -> dict[str, Any]:
    """Construye un dict con los datos del resultado de la precalificación v2."""
    return {
        "result": evaluation["result"],
        "categoria": evaluation.get("categoria"),
        "motivo": evaluation.get("motivo"),
        "tea": float(evaluation.get("tea", 0.0)),
        "capacidad_pago": float(evaluation.get("capacidad_pago", 0.0)),
        "monto_maximo": float(evaluation.get("monto_maximo", 0.0)),
        "cuota_estimada": float(evaluation.get("cuota_estimada", 0.0)),
        "plazo_meses": int(evaluation.get("plazo_meses", 0)),
    }


def _contains_handoff_keyword(text: str) -> bool:
    """Detecta palabras clave de derivación como palabras completas."""
    return any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in HANDOFF_KEYWORDS)


def _reset_validation_failures(conversation_id: str) -> None:
    """Reinicia el contador de fallos de validación para una conversación."""
    _validation_failures.pop(conversation_id, None)


def _track_validation_failure(conversation_id: str) -> bool:
    """Incrementa el contador de fallos y retorna True si se superó el límite."""
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
    """Deriva la conversación a un asesor humano y finaliza la conversación activa."""
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
    """Maneja un fallo de validación; si se supera el límite, deriva a asesor."""
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
    if state not in {HANDOFF_REQUESTED, FINISHED} and _contains_handoff_keyword(
        normalized_text
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
            response = message_service.ask_cedula_message()
            next_state = ASK_CEDULA

    elif state == ASK_CEDULA:
        is_valid, reason = validation_service.validate_cedula(text)
        if not is_valid:
            handoff_response = _handle_validation_failure(
                conversation_id, user_id, message_service.invalid_cedula_message(reason)
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_cedula_message(reason)
            next_state = ASK_CEDULA
        else:
            _reset_validation_failures(conversation_id)
            cedula = _clean_cedula(text)
            request = credit_repository.get_draft_request(conversation_id)
            if request:
                credit_repository.update_cedula(request["id"], cedula)
            user["cedula"] = cedula
            response = message_service.ask_consent_message()
            next_state = CONSENT

    elif state == CONSENT:
        is_valid, _ = validation_service.validate_confirmation(text)
        if not is_valid:
            handoff_response = _handle_validation_failure(
                conversation_id, user_id, message_service.invalid_confirmation_message()
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_confirmation_message()
            next_state = CONSENT
        elif text.strip() == "1":
            _reset_validation_failures(conversation_id)
            request = credit_repository.get_draft_request(conversation_id)
            cedula = (request or {}).get("cedula") or user.get("cedula")
            if cedula:
                user_repository.update_cedula_consent(user_id, cedula)
            response = message_service.ask_amount_message(user.get("full_name"))
            next_state = ASK_AMOUNT
        else:
            _reset_validation_failures(conversation_id)
            response = message_service.consent_declined_message()
            next_state = FINISHED
            conversation_repository.finish_conversation(conversation_id)

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
            else:
                response = message_service.welcome_message()
                next_state = MENU

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
                cedula = request.get("cedula") or user.get("cedula") or ""
                evaluation = precalificacion_service.precalificar_por_cedula(
                    cedula,
                    float(request["monthly_income"]),
                    int(request["term_months"]),
                    monto_solicitado=float(request["requested_amount"]),
                    conversation_id=conversation_id,
                )
                credit_repository.save_result_v2(
                    request["id"],
                    credit_score=evaluation.get("credit_score"),
                    score_category=str(evaluation.get("categoria")),
                    max_amount=float(evaluation.get("monto_maximo", 0.0)),
                    annual_rate=float(evaluation.get("tea", 0.0)),
                    estimated_payment=float(evaluation.get("cuota_estimada", 0.0)),
                    payment_capacity=float(evaluation.get("capacidad_pago", 0.0)),
                    result=str(evaluation["result"]),
                )
                result_data = _build_result_data(evaluation)
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
