from typing import Any


def extract_incoming_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []

    if payload.get("object") != "whatsapp_business_account":
        return messages

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue

                text_body = message.get("text", {}).get("body")
                phone = message.get("from")
                if not phone or not text_body:
                    continue

                messages.append(
                    {
                        "phone": phone,
                        "message": text_body,
                        "raw_payload": message,
                    }
                )

    return messages
