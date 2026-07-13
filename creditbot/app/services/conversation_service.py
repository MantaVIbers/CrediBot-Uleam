"""Lógica principal del flujo conversacional del bot."""
import re
from datetime import datetime, timezone
from typing import Any

from app.core.constants import (
    ASK_AMOUNT,
    ASK_CEDULA,
    ASK_INCOME,
    ASK_PURPOSE,
    ASK_TERM,
    CONFIRM_DATA,
    CONSENT,
    CREDIT_RESULT_OBSERVED,
    CREDIT_RESULT_PREAPPROVED,
    FINISHED,
    HANDOFF_REQUESTED,
    MENU,
    NOT_ELIGIBLE,
    SHOW_RESULT,
    START,
    VERIFY_IDENTITY,
)
from app.agent import openai_agent
from app.domain import credit_rules
from app.domain.cedula_validator import mask_cedula
from app.repositories import (
    conversation_repository,
    credit_profile_repository,
    credit_repository,
    handoff_repository,
    message_repository,
    user_repository,
)
from app.services import (
    handoff_service,
    intent_service,
    message_service,
    precalificacion_service,
    rag_service,
    validation_service,
)
from app.services.session_store import get_session_store, validation_failure_key

# Palabras clave que el usuario puede escribir para solicitar un asesor humano.
# "persona" no se usa sola: provoca falsos positivos ("persona natural", etc.).
HANDOFF_KEYWORDS = {"asesor", "humano", "agente"}
# Cantidad máxima de fallos de validación antes de derivar a asesor
MAX_VALIDATION_FAILURES = 3
# Frases que sí activan handoff cuando incluyen "persona"
_HANDOFF_PERSONA_PATTERN = re.compile(
    r"\b(?:hablar con|quiero|necesito|pasar a|derivar(?:me)? a?).{0,30}\bpersona\b",
    re.IGNORECASE,
)

def _parse_amount(value: str) -> float:
    """Convierte el texto del monto a float."""
    return validation_service.parse_numeric_value(value)


def _parse_term(value: str) -> int:
    """Convierte el texto del plazo a entero (acepta '12 meses', 'en 12 plazos')."""
    return validation_service.parse_term_value(value)


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
        "purpose": request.get("loan_purpose") or "No indicado",
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
    """Detecta solicitud de asesor como palabras/frases completas."""
    if any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in HANDOFF_KEYWORDS):
        return True
    return bool(_HANDOFF_PERSONA_PATTERN.search(text))


def _reset_validation_failures(conversation_id: str) -> None:
    """Reinicia el contador de fallos de validación para una conversación."""
    get_session_store().delete(validation_failure_key(conversation_id))


def _track_validation_failure(conversation_id: str) -> bool:
    """Incrementa el contador de fallos y retorna True si se superó el límite."""
    count = get_session_store().incr(validation_failure_key(conversation_id))
    return count >= MAX_VALIDATION_FAILURES


def _request_handoff(
    conversation_id: str,
    user_id: str,
    response: str,
    reason: str,
    credit_request_id: str | None = None,
) -> str:
    """Deriva la conversación a un asesor humano manteniendo el chat activo."""
    handoff_service.register_handoff(
        user_id=user_id,
        conversation_id=conversation_id,
        reason=reason,
        credit_request_id=credit_request_id,
    )
    _reset_validation_failures(conversation_id)
    conversation_repository.update_state(conversation_id, HANDOFF_REQUESTED)
    conversation_repository.update_last_message(conversation_id, response)
    message_repository.save_outbound_message(conversation_id, user_id, response)
    return response


def _append_handoff_transcript(case_id: str, case: dict[str, Any], text: str) -> None:
    """Agrega un mensaje entrante al transcript del caso para el panel."""
    transcript = case.get("transcript") if isinstance(case.get("transcript"), list) else []
    transcript = list(transcript)
    transcript.append(
        {
            "direction": "inbound",
            "content": text,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    handoff_repository.update_handoff_case(case_id, transcript=transcript[-20:])


def _process_open_handoff_message(
    *,
    conversation_id: str,
    user_id: str,
    text: str,
    open_handoff: dict[str, Any],
    raw_payload: dict[str, Any] | None,
) -> str:
    """Registra mensajes del cliente mientras un caso humano sigue abierto."""
    message_repository.save_inbound_message(
        conversation_id,
        user_id,
        text,
        raw_payload=raw_payload,
    )

    if intent_service.is_restart_command(text):
        handoff_service.close_handoff_case(str(open_handoff["id"]))
        conversation_repository.finish_conversation(conversation_id)
        _reset_validation_failures(conversation_id)
        new_conversation = conversation_repository.get_or_create_active_conversation(user_id)
        new_id = new_conversation["id"]
        response = message_service.restart_message()
        conversation_repository.update_state(new_id, MENU)
        response = message_service.with_handoff_hint(response)
        conversation_repository.update_last_message(new_id, response)
        message_repository.save_outbound_message(new_id, user_id, response)
        return response

    _append_handoff_transcript(str(open_handoff["id"]), open_handoff, text)
    response = message_service.handoff_waiting_message()
    conversation_repository.update_state(conversation_id, HANDOFF_REQUESTED)
    conversation_repository.update_last_message(conversation_id, response)
    message_repository.save_outbound_message(conversation_id, user_id, response)
    return response


def _resolve_open_handoff_conversation(user_id: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Retorna conversación y caso abiertos si el usuario tiene handoff activo."""
    open_handoff = handoff_service.get_open_handoff_case_for_user(user_id)
    if not open_handoff:
        return None

    conversation = conversation_repository.get_conversation_by_id(
        str(open_handoff["conversation_id"])
    )
    if not conversation:
        return None

    if not conversation.get("is_active"):
        conversation = conversation_repository.reactivate_conversation(
            str(conversation["id"]),
            HANDOFF_REQUESTED,
        )
    return conversation, open_handoff


def _handle_validation_failure(
    conversation_id: str,
    user_id: str,
    response: str,
) -> str | None:
    """Si se supera el límite de fallos, deriva a asesor; si no, retorna None."""
    if _track_validation_failure(conversation_id):
        return _request_handoff(
            conversation_id,
            user_id,
            message_service.handoff_message(),
            reason="repeated_invalid_input",
        )
    return None


def _verify_identity(cedula: str) -> dict[str, Any]:
    """Consulta el buró simulado y evalúa elegibilidad temprana (RF-02/03/04)."""
    profile = credit_profile_repository.get_profile_by_cedula(cedula)
    if not profile:
        return {
            "ok": False,
            "motivo": "sin_perfil",
            "full_name": None,
            "categoria": None,
            "credit_score": None,
        }

    elegibilidad = credit_rules.verificar_elegibilidad(
        int(profile.get("credit_score") or 0),
        has_delinquency=bool(profile.get("has_delinquency")),
        delinquency_days=int(profile.get("delinquency_days") or 0),
        lista_negra=bool(profile.get("blacklisted")),
        sin_historial=bool(profile.get("thin_file")),
    )
    return {
        "ok": bool(elegibilidad["elegible"]),
        "motivo": elegibilidad.get("motivo"),
        "categoria": elegibilidad.get("categoria"),
        "full_name": profile.get("full_name"),
        "credit_score": int(profile.get("credit_score") or 0),
        "profile": profile,
    }


def _continuation_prompt(state: str) -> str | None:
    """Indica cómo retomar el flujo después de responder una duda informativa."""
    prompts = {
        MENU: "elige 1 para precalificar, 2 para información o 3 para asesor.",
        CONSENT: "responde 1 para autorizar o 2 para no autorizar.",
        ASK_CEDULA: "envíame tu número de cédula de 10 dígitos.",
        VERIFY_IDENTITY: "espera la verificación o escribe 'asesor'.",
        ASK_PURPOSE: "indica el destino del crédito, por ejemplo estudios o negocio.",
        ASK_AMOUNT: "indica el monto que deseas solicitar.",
        ASK_TERM: "indica el plazo en meses, entre 3 y 36.",
        ASK_INCOME: "indica tu ingreso mensual aproximado.",
        CONFIRM_DATA: "responde 1 para confirmar o 2 para corregir.",
    }
    return prompts.get(state)


def _policy_response_for_state(text: str, state: str) -> tuple[str, list[rag_service.RagChunk]]:
    """Responde dudas de políticas y conserva el flujo actual."""
    answer, chunks = rag_service.build_policy_answer(text)
    return message_service.policy_info_message(answer, _continuation_prompt(state)), chunks


def _build_ai_context(
    *,
    conversation_id: str,
    state_before: str,
    state_after: str,
    rag_chunks: list[rag_service.RagChunk],
) -> dict[str, Any]:
    """Arma el contexto permitido para que la IA redacte sin decidir el flujo."""
    return {
        "conversation_id": conversation_id,
        "state_before": state_before,
        "state_after": state_after,
        "pending_step": _continuation_prompt(state_after),
        "rag_context": [
            {
                "title": chunk.title,
                "source": chunk.source,
                "content": chunk.content,
            }
            for chunk in rag_chunks
        ],
        "rag_sources": [
            {"title": chunk.title, "source": chunk.source}
            for chunk in rag_chunks
        ],
    }


def process_message(phone: str, text: str, raw_payload: dict[str, Any] | None = None) -> str:
    user = user_repository.get_or_create_user(phone)
    user_id = user["id"]

    open_handoff_context = _resolve_open_handoff_conversation(user_id)
    if open_handoff_context:
        conversation, open_handoff = open_handoff_context
        return _process_open_handoff_message(
            conversation_id=str(conversation["id"]),
            user_id=user_id,
            text=text,
            open_handoff=open_handoff,
            raw_payload=raw_payload,
        )

    conversation = conversation_repository.get_or_create_active_conversation(user_id)
    conversation_id = conversation["id"]
    state = conversation["current_state"]

    message_repository.save_inbound_message(
        conversation_id, user_id, text, raw_payload=raw_payload
    )

    if intent_service.is_restart_command(text) and state not in {
        START,
        FINISHED,
        NOT_ELIGIBLE,
    }:
        conversation_repository.finish_conversation(conversation_id)
        _reset_validation_failures(conversation_id)
        new_conversation = conversation_repository.get_or_create_active_conversation(user_id)
        conversation_id = new_conversation["id"]
        response = message_service.restart_message()
        conversation_repository.update_state(conversation_id, MENU)
        response = message_service.with_handoff_hint(response)
        response = openai_agent.render_reply(
            base_reply=response,
            state=MENU,
            user_message=text,
            context=_build_ai_context(
                conversation_id=conversation_id,
                state_before=state,
                state_after=MENU,
                rag_chunks=[],
            ),
        )
        conversation_repository.update_last_message(conversation_id, response)
        message_repository.save_outbound_message(conversation_id, user_id, response)
        return response

    normalized_text = text.strip().lower()
    if state not in {HANDOFF_REQUESTED, FINISHED, NOT_ELIGIBLE} and _contains_handoff_keyword(
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
    rag_chunks: list[rag_service.RagChunk] = []

    if (
        state not in {START, HANDOFF_REQUESTED, FINISHED, NOT_ELIGIBLE}
        and intent_service.is_policy_question(text)
        and not intent_service.looks_like_numeric_answer(text)
    ):
        response, rag_chunks = _policy_response_for_state(text, state)
        next_state = state

    elif state == START:
        response = message_service.welcome_message()
        next_state = MENU

    elif state == MENU:
        menu_option = intent_service.menu_option_from_text(text)
        if menu_option is None:
            handoff_response = _handle_validation_failure(
                conversation_id,
                user_id,
                message_service.invalid_menu_message() + "\n\n" + message_service.welcome_message(),
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_menu_message() + "\n\n" + message_service.welcome_message()
            next_state = MENU
        elif menu_option == "1":
            _reset_validation_failures(conversation_id)
            credit_repository.create_draft_request(user_id, conversation_id)
            response = message_service.ask_consent_message()
            next_state = CONSENT
        elif menu_option == "2":
            _reset_validation_failures(conversation_id)
            # "2" no sirve como query RAG; usamos resumen + políticas generales.
            _, rag_chunks = rag_service.build_policy_answer(
                "requisitos tasas plazos montos documentos score"
            )
            response = message_service.general_info_message()
            if rag_chunks:
                bullets = []
                for chunk in rag_chunks[:2]:
                    summary = " ".join(chunk.content.split())
                    if len(summary) > 180:
                        summary = summary[:177].rstrip() + "..."
                    bullets.append(f"- {chunk.title}: {summary}")
                response = (
                    message_service.general_info_message()
                    + "\n\nDetalle de políticas:\n"
                    + "\n".join(bullets)
                )
            next_state = MENU
        elif menu_option == "3":
            return _request_handoff(
                conversation_id,
                user_id,
                message_service.handoff_message(),
                reason="menu_option_3",
            )

    elif state == CONSENT:
        confirmation = intent_service.confirmation_from_text(text)
        if confirmation is None:
            handoff_response = _handle_validation_failure(
                conversation_id, user_id, message_service.invalid_confirmation_message()
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_confirmation_message()
            next_state = CONSENT
        elif confirmation == "1":
            _reset_validation_failures(conversation_id)
            response = message_service.ask_cedula_message()
            next_state = ASK_CEDULA
        else:
            _reset_validation_failures(conversation_id)
            response = message_service.consent_declined_message()
            next_state = FINISHED
            conversation_repository.finish_conversation(conversation_id)

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
            user_repository.update_cedula_consent(user_id, cedula)
            user["cedula"] = cedula

            # VERIFY_IDENTITY: consulta buró + elegibilidad temprana
            verification = _verify_identity(cedula)
            if verification["motivo"] == "sin_perfil":
                response = message_service.cedula_not_found_message()
                next_state = ASK_CEDULA
            elif not verification["ok"]:
                name = verification.get("full_name")
                if name:
                    user_repository.update_user_name(user_id, name)
                    user["full_name"] = name
                response = message_service.not_eligible_message(
                    name,
                    verification.get("motivo"),
                    verification.get("categoria"),
                )
                next_state = NOT_ELIGIBLE
                conversation_repository.finish_conversation(conversation_id)
            else:
                name = verification.get("full_name") or "Cliente"
                user_repository.update_user_name(user_id, name)
                user["full_name"] = name
                response = (
                    message_service.identity_verified_message(
                        name,
                        str(verification.get("categoria")),
                        verification.get("credit_score"),
                    )
                    + "\n\n"
                    + message_service.ask_purpose_message()
                )
                next_state = ASK_PURPOSE

    elif state == ASK_PURPOSE:
        is_valid, _ = validation_service.validate_purpose(text)
        if not is_valid:
            handoff_response = _handle_validation_failure(
                conversation_id, user_id, message_service.invalid_purpose_message()
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_purpose_message()
            next_state = ASK_PURPOSE
        else:
            _reset_validation_failures(conversation_id)
            request = credit_repository.get_draft_request(conversation_id)
            if request:
                credit_repository.update_purpose(request["id"], text.strip())
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
            else:
                response = message_service.welcome_message()
                next_state = MENU

    elif state == CONFIRM_DATA:
        confirmation = intent_service.confirmation_from_text(text)
        if confirmation is None:
            handoff_response = _handle_validation_failure(
                conversation_id, user_id, message_service.invalid_confirmation_message()
            )
            if handoff_response:
                return handoff_response
            response = message_service.invalid_confirmation_message()
            next_state = CONFIRM_DATA
        elif confirmation == "1":
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
                if not evaluation.get("ok"):
                    response = (
                        f"No se pudo completar la precalificación: "
                        f"{evaluation.get('motivo') or 'datos incompletos'}. "
                        "Inténtalo de nuevo o escribe 'asesor'."
                    )
                    next_state = CONFIRM_DATA
                else:
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
        elif confirmation == "2":
            _reset_validation_failures(conversation_id)
            response = message_service.ask_purpose_message()
            next_state = ASK_PURPOSE

    elif state == SHOW_RESULT:
        response = message_service.finished_message()
        next_state = FINISHED
        conversation_repository.finish_conversation(conversation_id)

    elif state in {HANDOFF_REQUESTED, FINISHED, NOT_ELIGIBLE}:
        user = user_repository.get_or_create_user(phone)
        conversation = conversation_repository.get_or_create_active_conversation(user["id"])
        conversation_id = conversation["id"]
        state = conversation["current_state"]
        response = message_service.welcome_message()
        next_state = MENU

    if next_state != state:
        conversation_repository.update_state(conversation_id, next_state)

    if next_state not in {HANDOFF_REQUESTED, FINISHED, NOT_ELIGIBLE}:
        response = message_service.with_handoff_hint(response)

    response = openai_agent.render_reply(
        base_reply=response,
        state=next_state,
        user_message=text,
        context=_build_ai_context(
            conversation_id=conversation_id,
            state_before=state,
            state_after=next_state,
            rag_chunks=rag_chunks,
        ),
    )
    conversation_repository.update_last_message(conversation_id, response)
    message_repository.save_outbound_message(conversation_id, user_id, response)
    return response
