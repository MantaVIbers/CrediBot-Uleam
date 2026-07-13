"""Pruebas del repositorio de perfiles crediticios.

Se mockea el cliente de Supabase para no depender de una base real; se verifica
que la cédula se normalice y que la respuesta se mapee correctamente.
"""
from types import SimpleNamespace

from app.repositories import credit_profile_repository as repo


class _FakeQuery:
    """Query encadenable que imita la API fluida de supabase-py."""

    def __init__(self, recorder, rows):
        self._recorder = recorder
        self._rows = rows

    def select(self, *args, **kwargs):
        return self

    def eq(self, column, value):
        self._recorder["eq"] = (column, value)
        return self

    def limit(self, *args, **kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self._rows)


class _FakeClient:
    def __init__(self, recorder, rows):
        self._recorder = recorder
        self._rows = rows

    def table(self, name):
        self._recorder["table"] = name
        return _FakeQuery(self._recorder, self._rows)


def _patch_client(monkeypatch, rows):
    recorder: dict = {}
    monkeypatch.setattr(
        repo, "get_supabase_client", lambda: _FakeClient(recorder, rows)
    )
    return recorder


def test_get_profile_by_cedula_found(monkeypatch):
    """Devuelve el primer registro y consulta la tabla credit_profiles por cédula."""
    row = {"cedula": "0912345675", "credit_score": 720, "score_category": "aceptable"}
    recorder = _patch_client(monkeypatch, [row])

    result = repo.get_profile_by_cedula("0912345675")

    assert result == row
    assert recorder["table"] == "credit_profiles"
    assert recorder["eq"] == ("cedula", "0912345675")


def test_get_profile_by_cedula_normalizes_separators(monkeypatch):
    """Los separadores se eliminan antes de consultar."""
    recorder = _patch_client(monkeypatch, [{"cedula": "0912345675"}])

    repo.get_profile_by_cedula(" 091-234 5675 ")

    assert recorder["eq"] == ("cedula", "0912345675")


def test_get_profile_by_cedula_not_found(monkeypatch):
    """Sin filas retorna None."""
    _patch_client(monkeypatch, [])

    assert repo.get_profile_by_cedula("0912345675") is None


def test_get_profile_by_cedula_empty_returns_none(monkeypatch):
    """Una cédula vacía no golpea la base y retorna None."""
    called = {"hit": False}

    def _boom():
        called["hit"] = True
        raise AssertionError("no debería consultar la base con cédula vacía")

    monkeypatch.setattr(repo, "get_supabase_client", _boom)

    assert repo.get_profile_by_cedula("   ") is None
    assert called["hit"] is False
