"""Prometheus metrics: request-level (via the instrumentator library) and
AI-call-level (hand-defined, since no library knows about our LLM/embedding
calls).

Metrics are always-on and purely in-process -- unlike tracing, there's no
external collector to be unreachable, so there's no reason to gate this
behind a feature flag. `/metrics` is safe to scrape whether or not anything
is actually scraping it.
"""

from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# ---- AI call metrics --------------------------------------------------
# `provider` is "anthropic" | "voyage"; `purpose` identifies which of the
# four LLM-primary/deterministic-fallback call sites this is (see
# app.core.llm_telemetry and docs/architecture-proposal.md, "AI Architecture").

LLM_CALLS_TOTAL = Counter(
    "campuswise_ai_calls_total",
    "Total AI provider calls (Claude, Voyage), by outcome.",
    ["provider", "purpose", "outcome"],  # outcome: success | error
)

LLM_CALL_DURATION_SECONDS = Histogram(
    "campuswise_ai_call_duration_seconds",
    "AI provider call latency in seconds.",
    ["provider", "purpose"],
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30),
)

LLM_TOKENS_TOTAL = Counter(
    "campuswise_ai_tokens_total",
    "Tokens consumed by AI provider calls.",
    ["provider", "purpose", "direction"],  # direction: input | output
)

FALLBACK_TOTAL = Counter(
    "campuswise_fallback_total",
    "Times a deterministic fallback ran instead of (or after a failed) LLM call.",
    ["purpose", "reason"],  # reason: no_api_key | llm_error
)


def instrument_app(app) -> None:
    """Wires up request-level metrics (count, latency, in-progress) and
    exposes them at GET /metrics in Prometheus text format."""
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
