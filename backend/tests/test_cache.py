from unittest.mock import MagicMock, patch

import redis

import app.core.cache as cache_module
from app.core.cache import cached, get_redis_client


def _reset_module_state():
    cache_module._client = None
    cache_module._client_unavailable = False


def test_get_redis_client_returns_none_when_unreachable():
    _reset_module_state()
    with patch("app.core.cache.redis.Redis.from_url") as mock_from_url:
        mock_client = MagicMock()
        mock_client.ping.side_effect = redis.ConnectionError("no redis here")
        mock_from_url.return_value = mock_client
        assert get_redis_client() is None
    _reset_module_state()


def test_cached_decorator_falls_through_when_redis_unavailable():
    _reset_module_state()
    calls = []

    @cached("test_prefix", ttl_seconds=30)
    def compute(x: int) -> dict:
        calls.append(x)
        return {"value": x * 2}

    with patch("app.core.cache.get_redis_client", return_value=None):
        assert compute(5) == {"value": 10}
        assert compute(5) == {"value": 10}
    assert calls == [5, 5]  # no caching happened, so the function ran both times
    _reset_module_state()


def test_cached_decorator_returns_cached_value_on_hit():
    _reset_module_state()
    calls = []
    store: dict[str, str] = {}

    mock_client = MagicMock()
    mock_client.get.side_effect = lambda key: store.get(key)
    mock_client.setex.side_effect = lambda key, ttl, value: store.__setitem__(key, value)

    @cached("test_prefix2", ttl_seconds=30)
    def compute(x: int) -> dict:
        calls.append(x)
        return {"value": x * 2}

    with patch("app.core.cache.get_redis_client", return_value=mock_client):
        assert compute(7) == {"value": 14}
        assert compute(7) == {"value": 14}
    assert calls == [7]  # second call was served from the cache
    _reset_module_state()


def test_cached_decorator_ignores_session_like_args_in_key():
    _reset_module_state()
    mock_session = MagicMock()
    mock_session.execute = MagicMock()  # marks it as "session-like" per the exclusion check

    @cached("test_prefix3", ttl_seconds=30)
    def compute(db, x: int) -> dict:
        return {"value": x}

    with patch("app.core.cache.get_redis_client", return_value=None):
        # Should not raise even though `db` isn't JSON-serializable / hashable in a normal way.
        assert compute(mock_session, 3) == {"value": 3}
    _reset_module_state()
