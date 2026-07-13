"""Recuperación básica de políticas para respuestas informativas.

Este RAG inicial usa documentos Markdown locales como fuente de verdad. Es
determinista y testeable; más adelante puede reemplazarse por pgvector/Supabase.
"""
from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata


POLICY_DIR = Path(__file__).resolve().parents[2] / "docs" / "policies"
STOPWORDS = {
    "a",
    "al",
    "con",
    "de",
    "del",
    "el",
    "en",
    "es",
    "la",
    "las",
    "lo",
    "los",
    "para",
    "por",
    "que",
    "se",
    "un",
    "una",
    "y",
}


@dataclass(frozen=True)
class RagChunk:
    title: str
    source: str
    content: str
    score: int


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.lower()


def _tokens(value: str) -> set[str]:
    words = set(re.findall(r"[a-z0-9]+", _normalize(value)))
    return {word for word in words if len(word) > 2 and word not in STOPWORDS}


def _iter_policy_sections() -> list[tuple[str, str, str]]:
    sections: list[tuple[str, str, str]] = []
    for path in sorted(POLICY_DIR.glob("*.md")):
        current_title = path.stem
        buffer: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                if buffer:
                    sections.append((current_title, path.name, "\n".join(buffer).strip()))
                current_title = line.replace("## ", "", 1).strip()
                buffer = []
            elif line.strip() and not line.startswith("# "):
                buffer.append(line.strip())
        if buffer:
            sections.append((current_title, path.name, "\n".join(buffer).strip()))
    return sections


def search_policies(query: str, limit: int = 2) -> list[RagChunk]:
    """Busca secciones relevantes de políticas usando coincidencia léxica."""
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    results: list[RagChunk] = []
    for title, source, content in _iter_policy_sections():
        section_tokens = _tokens(f"{title} {content}")
        score = len(query_tokens & section_tokens)
        if score > 0:
            results.append(RagChunk(title=title, source=source, content=content, score=score))

    return sorted(results, key=lambda chunk: (-chunk.score, chunk.title))[:limit]


def build_policy_answer(query: str) -> tuple[str, list[RagChunk]]:
    """Construye una respuesta breve a partir de las secciones recuperadas."""
    chunks = search_policies(query)
    if not chunks:
        return (
            "No encontré una política específica para esa consulta. "
            "Puedo darte información general o derivarte con un asesor.",
            [],
        )

    bullet_lines = []
    for chunk in chunks:
        summary = " ".join(chunk.content.split())
        bullet_lines.append(f"- {chunk.title}: {summary}")

    answer = "Según las políticas internas del MVP:\n" + "\n".join(bullet_lines)
    return answer, chunks


def is_rag_available() -> bool:
    """True si hay documentos de política locales cargados."""
    return bool(list(POLICY_DIR.glob("*.md")))


def retrieve_context(query: str, limit: int = 3) -> list[str]:
    """Compatibilidad con servicios IA: devuelve fragmentos como texto."""
    return [f"{chunk.title}: {chunk.content}" for chunk in search_policies(query, limit)]


def build_context_block(chunks: list[str]) -> str:
    """Une fragmentos recuperados en un bloque de contexto."""
    return "\n".join(chunks)

