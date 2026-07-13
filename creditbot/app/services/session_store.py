"""Almacén de sesión activa: Redis si está configurado, memoria como fallback."""
from __future__ import annotations

import logging
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


class SessionStore(Protocol):
    def get_int(self, key: str, default: int = 0) -> int: ...

    def set_int(self, key: str, value: int) -> None: ...

    def delete(self, key: str) -> None: ...

    def incr(self, key: str) -> int: ...


class InMemorySessionStore:
    """Fallback local (un proceso). Útil en tests y desarrollo sin Redis."""

    def __init__(self) -> None:
        self._data: dict[str, int] = {}

    def get_int(self, key: str, default: int = 0) -> int:
        return self._data.get(key, default)

    def set_int(self, key: str, value: int) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def incr(self, key: str) -> int:
        value = self._data.get(key, 0) + 1
        self._data[key] = value
        return value


class RedisSessionStore:
    """Sesión en Redis (compatible con Upstash vía REDIS_URL)."""

    def __init__(self, redis_client, ttl_seconds: int) -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds

    def get_int(self, key: str, default: int = 0) -> int:
        raw = self._redis.get(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    def set_int(self, key: str, value: int) -> None:
        self._redis.set(key, value, ex=self._ttl)

    def delete(self, key: str) -> None:
        self._redis.delete(key)

    def incr(self, key: str) -> int:
        value = int(self._redis.incr(key))
        self._redis.expire(key, self._ttl)
        return value


_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    """Retorna el almacén de sesión (singleton)."""
    global _store
    if _store is not None:
        return _store

    if settings.redis_url:
        try:
            from redis import Redis

            client = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            client.ping()
            _store = RedisSessionStore(client, settings.redis_session_ttl_seconds)
            logger.info("Sesión activa usando Redis.")
            return _store
        except Exception as exc:
            logger.warning("No se pudo conectar a Redis (%s). Usando memoria.", exc)

    _store = InMemorySessionStore()
    logger.info("Sesión activa usando memoria local.")
    return _store


def reset_session_store() -> None:
    """Reinicia el singleton (solo para tests)."""
    global _store
    _store = None


def validation_failure_key(conversation_id: str) -> str:
    return f"session:{conversation_id}:failures"
