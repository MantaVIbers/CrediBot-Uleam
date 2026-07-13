"""Pruebas del RAG local de políticas."""
from app.services import rag_service


# Verifica que la búsqueda de políticas recupere requisitos relevantes
def test_search_policies_recupera_requisitos():
    chunks = rag_service.search_policies("qué requisitos necesito")

    assert chunks
    assert chunks[0].title == "Requisitos básicos"
    assert "nombre completo" in chunks[0].content


# Verifica que la respuesta incluya fuentes de políticas internas
def test_build_policy_answer_incluye_fuente_relevante():
    answer, chunks = rag_service.build_policy_answer("documentos para el crédito")

    assert "Según las políticas internas" in answer
    assert chunks
    assert any(chunk.title == "Documentos referenciales" for chunk in chunks)


# Verifica que tokens inválidos retornen lista vacía
def test_search_policies_sin_tokens_devuelve_vacio():
    assert rag_service.search_policies("??") == []
