"""Redis cache-aside helpers for expensive, frequently-repeated reads.

Deliberately not a blanket cache-everything layer -- only endpoints that are
read-heavy and expensive relative to their staleness tolerance use this
(course search, grade distributions; see docs/architecture-proposal.md,
"Caching"). No active invalidation on writes: TTLs are short enough that
this is acceptable for the seeded/demo dataset, which changes rarely. A
production deployment ingesting real per-term data would add explicit
invalidation on ingestion.
"""

import json
import logging
from functools import wraps
from typing import Callable

import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None
_client_unavailable = False


def get_redis_client() -> redis.Redis | None:
    """Returns a Redis client, or None if Redis is unreachable.

    Caching is an optimization, not a dependency -- if Redis is down, every
    cached function just falls through to computing the real result.
    """
    global _client, _client_unavailable
    if _client_unavailable:
        return None
    if _client is None:
        settings = get_settings()
        _client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=0.5)
    try:
        _client.ping()
    except redis.RedisError:
        logger.warning("Redis unavailable, caching disabled for this process")
        _client_unavailable = True
        return None
    return _client


def cached(prefix: str, ttl_seconds: int):
    """Decorator: cache a function's JSON-serializable return value in Redis.

    The cache key is built from `prefix` plus the function's positional and
    keyword arguments (excluding any SQLAlchemy Session, which isn't a
    meaningful or serializable part of the key).
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            client = get_redis_client()
            cache_key_parts = [
                repr(a) for a in args if not hasattr(a, "execute")
            ] + [f"{k}={v!r}" for k, v in sorted(kwargs.items()) if not hasattr(v, "execute")]
            cache_key = f"{prefix}:" + "|".join(cache_key_parts)

            if client is not None:
                try:
                    cached_value = client.get(cache_key)
                    if cached_value is not None:
                        return json.loads(cached_value)
                except redis.RedisError:
                    pass

            result = fn(*args, **kwargs)

            if client is not None:
                try:
                    client.setex(cache_key, ttl_seconds, json.dumps(result))
                except (redis.RedisError, TypeError):
                    pass  # non-JSON-serializable result or Redis hiccup: skip caching silently

            return result

        return wrapper

    return decorator
