from typing import Any

from app.repositories import handoff_repository


def create_handoff_case(
    user_id: str,
    conversation_id: str,
    reason: str,
    credit_request_id: str | None = None,
) -> dict[str, Any]:
    return handoff_repository.create_handoff_case(
        user_id=user_id,
        conversation_id=conversation_id,
        reason=reason,
        credit_request_id=credit_request_id,
    )


def get_pending_handoff_cases() -> list[dict[str, Any]]:
    return handoff_repository.get_pending_handoff_cases()


def close_handoff_case(case_id: str) -> dict[str, Any]:
    return handoff_repository.close_handoff_case(case_id)


def register_handoff(
    user_id: str,
    conversation_id: str,
    reason: str,
    credit_request_id: str | None = None,
) -> dict[str, Any]:
    return create_handoff_case(
        user_id=user_id,
        conversation_id=conversation_id,
        reason=reason,
        credit_request_id=credit_request_id,
    )
