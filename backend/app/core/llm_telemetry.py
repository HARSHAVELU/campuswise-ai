"""Unified telemetry for every AI provider call (Claude, Voyage).

One context manager records all three signals from a single call site: a
Prometheus counter + latency histogram + token counters (app.core.metrics),
an OpenTelemetry span if tracing is enabled (app.core.tracing), and one
structured log line -- so instrumenting a new provider call is a two-line
change, not four separate ones repeated at every call site.

This is the platform's answer to "no LLM-specific observability": every one
of the four LLM-primary/deterministic-fallback call sites (requirement
parsing, syllabus Q&A synthesis, assessment extraction, chat replies) and
both Voyage call sites (embeddings, reranking) goes through this.
"""

import logging
import time
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass

from app.core.metrics import (
    FALLBACK_TOTAL,
    LLM_CALL_DURATION_SECONDS,
    LLM_CALLS_TOTAL,
    LLM_TOKENS_TOTAL,
)
from app.core.tracing import get_tracer

logger = logging.getLogger("app.ai_calls")


@dataclass
class LLMCallRecorder:
    """Filled in by the caller once the provider response is available
    (token counts aren't known until after the call returns)."""

    input_tokens: int | None = None
    output_tokens: int | None = None


@contextmanager
def track_llm_call(provider: str, purpose: str, model: str):
    """Wraps a single AI provider call.

    Usage:
        with track_llm_call("anthropic", "requirement_parsing", model) as rec:
            response = client.messages.create(...)
            rec.input_tokens = response.usage.input_tokens
            rec.output_tokens = response.usage.output_tokens
    """
    recorder = LLMCallRecorder()
    start = time.perf_counter()
    outcome = "success"

    tracer = get_tracer()
    span_cm = tracer.start_as_current_span(f"ai.{provider}.{purpose}") if tracer else nullcontext()

    try:
        with span_cm as span:
            yield recorder
            if span is not None:
                span.set_attribute("ai.provider", provider)
                span.set_attribute("ai.purpose", purpose)
                span.set_attribute("ai.model", model)
                if recorder.input_tokens is not None:
                    span.set_attribute("ai.input_tokens", recorder.input_tokens)
                if recorder.output_tokens is not None:
                    span.set_attribute("ai.output_tokens", recorder.output_tokens)
    except Exception:
        outcome = "error"
        raise
    finally:
        duration = time.perf_counter() - start
        LLM_CALLS_TOTAL.labels(provider=provider, purpose=purpose, outcome=outcome).inc()
        LLM_CALL_DURATION_SECONDS.labels(provider=provider, purpose=purpose).observe(duration)
        if recorder.input_tokens is not None:
            LLM_TOKENS_TOTAL.labels(provider=provider, purpose=purpose, direction="input").inc(
                recorder.input_tokens
            )
        if recorder.output_tokens is not None:
            LLM_TOKENS_TOTAL.labels(provider=provider, purpose=purpose, direction="output").inc(
                recorder.output_tokens
            )
        logger.info(
            "ai_call provider=%s purpose=%s model=%s outcome=%s duration_ms=%s "
            "input_tokens=%s output_tokens=%s",
            provider,
            purpose,
            model,
            outcome,
            round(duration * 1000, 1),
            recorder.input_tokens,
            recorder.output_tokens,
        )


def record_fallback(purpose: str, reason: str) -> None:
    """Call when a deterministic fallback ran instead of (or after a failed) LLM call.

    reason: "no_api_key" | "llm_error"
    """
    FALLBACK_TOTAL.labels(purpose=purpose, reason=reason).inc()
    logger.info("ai_fallback purpose=%s reason=%s", purpose, reason)
