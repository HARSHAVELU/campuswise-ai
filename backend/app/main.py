import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.error_handlers import unhandled_exception_handler
from app.core.logging import configure_logging
from app.core.metrics import instrument_app
from app.core.rate_limit import limiter
from app.core.request_logging import RequestLoggingMiddleware
from app.core.tracing import configure_tracing
from app.database.session import engine

configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("%s starting in %s mode", settings.app_name, settings.environment)
    yield


app = FastAPI(
    title=settings.app_name,
    description="AI-powered university course, professor, and semester planning assistant.",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)

instrument_app(app)  # GET /metrics -- always on, no external dependency
configure_tracing(app, engine)  # no-op unless OTEL_ENABLED=true
