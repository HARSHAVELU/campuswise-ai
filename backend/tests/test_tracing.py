from unittest.mock import patch

from fastapi import FastAPI

from app.core.tracing import configure_tracing, get_tracer


def test_configure_tracing_is_noop_when_disabled():
    with patch("app.core.config.get_settings") as mock_settings:
        mock_settings.return_value.otel_enabled = False
        app = FastAPI()
        configure_tracing(app, engine=None)
    # No exception, and nothing about disabled tracing should require a real engine.


def test_configure_tracing_enabled_does_not_raise_without_a_real_collector():
    """The OTel SDK is designed to degrade gracefully when its collector is
    unreachable (export failures are swallowed in a background thread) --
    this exercises the actual instrumentation wiring path, which our test
    suite otherwise never runs since OTEL_ENABLED defaults to False."""
    from sqlalchemy import create_engine

    engine = create_engine("sqlite://")

    with patch("app.core.config.get_settings") as mock_settings:
        mock_settings.return_value.otel_enabled = True
        mock_settings.return_value.otel_exporter_endpoint = "localhost:4317"
        mock_settings.return_value.otel_service_name = "test-service"
        app = FastAPI()

        configure_tracing(app, engine)

    assert get_tracer() is not None
