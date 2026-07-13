"""Detección simple de intención para mantener el flujo guiado."""
import re
import unicodedata


def _normalize(value: str) -> str:
    """Normaliza texto para comparar intención sin depender de tildes."""
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.lower().strip()


def _has_any(text: str, words: set[str]) -> bool:
    """Verifica si el texto contiene alguna de las palabras como palabra completa."""
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def menu_option_from_text(value: str) -> str | None:
    """Convierte mensajes naturales del menú a una opción válida."""
    text = _normalize(value)
    if text in {"1", "2", "3"}:
        return text
    # "persona" sola no cuenta (falso positivo con "persona natural")
    if _has_any(text, {"asesor", "humano", "agente", "ejecutivo"}):
        return "3"
    if re.search(r"\b(?:hablar con|quiero|necesito|pasar a).{0,30}\bpersona\b", text):
        return "3"
    if _has_any(text, {"credito", "prestamo", "precalificar", "solicitar", "cotizar"}):
        return "1"
    if _has_any(text, {"informacion", "info", "requisitos", "tasas", "plazos"}):
        return "2"
    return None


def confirmation_from_text(value: str) -> str | None:
    """Convierte confirmaciones naturales a 1 (sí) o 2 (no)."""
    text = _normalize(value)
    if text in {"1", "2"}:
        return text
    if _has_any(text, {"si", "acepto", "autorizo", "confirmo", "correcto", "ok"}):
        return "1"
    if _has_any(text, {"no", "rechazo", "cancelar", "corregir", "editar"}):
        return "2"
    return None


def looks_like_numeric_answer(value: str) -> bool:
    """Detecta respuestas de monto/plazo/ingreso para no confundirlas con RAG."""
    if "?" in value:
        return False
    text = _normalize(value)
    if not re.search(r"\d", text):
        return False
    # "12", "12 meses", "en 12 plazos", "$1.200", "1500 dolares"
    # Detectar patrones numéricos: "12", "12 meses", "$1.200", "1500 dolares"
    return bool(
        re.search(
            r"(?:^|[\s$])\d[\d.,]*\s*(?:meses|mes|plazos|plazo|dolares|usd|\$)?\b",
            text,
        )
    )


def is_policy_question(value: str) -> bool:
    """Detecta preguntas informativas que deben responderse con RAG."""
    if looks_like_numeric_answer(value):
        return False
    text = _normalize(value)
    if "?" in value:
        return _has_any(
            text,
            {
                "documentos",
                "requisitos",
                "tasa",
                "tasas",
                "plazo",
                "plazos",
                "monto",
                "montos",
                "cuota",
                "score",
            },
        )
    return _has_any(
        text,
        {
            "documentos",
            "requisitos",
            "tasas",
            "plazos",
            "politica",
            "condiciones",
        },
    )
