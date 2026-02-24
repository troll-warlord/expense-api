import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.routers.health import router as health_router
from app.routers.router import v1_router

configure_logging(debug=settings.APP_DEBUG)

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from app.core.database import engine

    try:
        async with engine.connect():
            log.info("database connection ok")
    except Exception as exc:
        log.warning("database not reachable on startup", error=str(exc))

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Expense Tracker API",
        version="1.0.0",
        description="Production-ready Expense Tracker Backend",
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # HTTP middleware — binds request context for ALL log lines in request
    # ------------------------------------------------------------------
    access_log = structlog.get_logger("app.access")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        # Clear any context left over from a previous request on this worker
        structlog.contextvars.clear_contextvars()

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Resolve client source from header; default to "api" for unknown callers
        _VALID_SOURCES = {"web", "android", "ios", "api"}
        client_source = request.headers.get("X-Client-Source", "api").lower().strip()
        if client_source not in _VALID_SOURCES:
            client_source = "api"
        request.state.source = client_source

        # Soft-decode user ID from Bearer token — never raises
        user_id: str | None = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.core.security import decode_access_token

                claims = decode_access_token(auth_header[7:])
                if claims:
                    user_id = str(claims.get("sub"))
            except Exception:
                pass

        # Client IP — respects X-Forwarded-For for reverse-proxy setups
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (request.client.host if request.client else "-")

        # Bind context — these keys appear automatically in EVERY log line
        # emitted anywhere in the app during this request
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            user_id=user_id,
            ip=client_ip,
            source=client_source,
        )

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        response.headers["X-Request-ID"] = request_id

        status_code = response.status_code
        msg = f"{request.method} {request.url.path} → {status_code} ({duration_ms}ms)"
        extra = {"query": request.url.query} if request.url.query else {}
        if status_code >= 500:
            access_log.error(msg, **extra)
        elif status_code >= 400:
            access_log.warning(msg, **extra)
        else:
            access_log.info(msg, **extra)

        return response

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Rate limiter state
    # ------------------------------------------------------------------
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    app.include_router(health_router)
    app.include_router(v1_router)

    # ------------------------------------------------------------------
    # Global exception handlers
    # ------------------------------------------------------------------

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [f"{' → '.join(str(loc) for loc in e['loc'] if loc != 'body')}: {e['msg']}" for e in exc.errors()]
        # Bind to context — appears in the consolidated access line emitted by middleware
        structlog.contextvars.bind_contextvars(validation_errors=errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Validation error",
                "data": errors,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Emit a dedicated ERROR line that includes the full traceback
        log.exception("Unhandled exception", exc_info=exc)
        # Bind error type so it also appears in the consolidated access line
        structlog.contextvars.bind_contextvars(error=type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected error occurred",
                "data": None,
            },
        )

    return app


app: FastAPI = create_app()
