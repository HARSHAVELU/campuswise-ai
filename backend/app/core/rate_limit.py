"""Per-IP rate limiting (slowapi / the `limits` library).

Uses in-memory storage rather than Redis: simpler, no extra failure mode to
reason about, and correct for a single backend instance. A multi-instance
deployment would need a shared store (Redis) so limits are enforced
consistently across instances -- a known scaling point, not done here.
"""

from typing import Callable

from slowapi import Limiter
from slowapi.util import get_remote_address

DEFAULT_LIMITS: list[str | Callable[..., str]] = ["120/minute"]
AUTH_LIMIT = "10/minute"
CHAT_LIMIT = "30/minute"

limiter = Limiter(key_func=get_remote_address, default_limits=DEFAULT_LIMITS)
