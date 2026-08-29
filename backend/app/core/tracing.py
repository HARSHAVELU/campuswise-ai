"""Distributed tracing (OpenTelemetry -> OTLP -> Jaeger).

Auto-instruments FastAPI (one span per request) and SQLAlchemy (one child
span per query), so a slow request's trace shows the real breakdown --
"800ms total, of which 40ms was three Postgres queries and 720ms was the
Claude call" -- instead of just a single opaque duration. The Claude/Voyage
spans themselves come from app.core.llm_telemetry, which every LLM-primary
call site already goes through.

A no-op if OTEL_ENABLED is unset (see app.core.config) -- most local/test
runs don't have a collector running, and there's no reason to configure the
SDK at all in that case.
"""

import logging

logger = logging.getLogger(__name__)

_tracer = None


def configure_tracing(app, engine) -> None:
    global _tracer

    from app.core.config import get_settings

    settings = get_settings()
    if not settings.otel_enabled:
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({SERVICE_NAME: settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
    RedisInstrumentor().instrument()

    _tracer = trace.get_tracer(settings.otel_service_name)
    logger.info("OpenTelemetry tracing enabled, exporting to %s", settings.otel_exporter_endpoint)


def get_tracer():
    """Returns the configured tracer, or None if tracing is disabled.

    Callers (app.core.llm_telemetry) must handle None -- span creation is
    skipped entirely rather than using a no-op tracer, to avoid importing
    the OpenTelemetry API in processes that never enabled it.
    """
    return _tracer
