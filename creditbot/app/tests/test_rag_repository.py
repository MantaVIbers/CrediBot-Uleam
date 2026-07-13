"""Pruebas del repositorio RAG."""
from app.repositories import rag_repository


# Verifica que el repositorio maneje correctamente una tabla vacía de chunks
def test_list_all_chunks_empty(monkeypatch):
    class FakeResponse:
        data = []

    class FakeTable:
        def select(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        def execute(self):
            return FakeResponse()

    class FakeClient:
        def table(self, _name):
            return FakeTable()

    monkeypatch.setattr(rag_repository, "get_supabase_client", lambda: FakeClient())
    assert rag_repository.list_all_chunks() == []
