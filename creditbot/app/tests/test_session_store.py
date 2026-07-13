"""Pruebas del almacén de sesión (Redis/memoria)."""
from app.services.session_store import (
    InMemorySessionStore,
    get_session_store,
    reset_session_store,
    validation_failure_key,
)


# Verifica incremento y reinicio de contadores en almacenamiento en memoria
def test_in_memory_incr_and_reset():
    store = InMemorySessionStore()
    key = validation_failure_key("conv-1")
    assert store.get_int(key) == 0
    assert store.incr(key) == 1  # Primera incrementación
    assert store.incr(key) == 2  # Segunda incrementación
    store.delete(key)
    assert store.get_int(key) == 0  # Después de eliminar, vuelve a 0


# Verifica que sin URL de Redis se usa memoria como fallback
def test_get_session_store_defaults_to_memory(monkeypatch):
    reset_session_store()
    monkeypatch.setattr("app.services.session_store.settings.redis_url", "")
    store = get_session_store()
    assert isinstance(store, InMemorySessionStore)
    reset_session_store()
