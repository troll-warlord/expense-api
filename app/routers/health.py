"""Health-check endpoint.

Used by load balancers, container orchestrators (k8s liveness/readiness probes),
and deployment scripts to verify the app and its dependencies are reachable.

Route: GET /health  (no /v1 prefix — infrastructure tooling expects a fixed path)
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.database import get_async_session

router = APIRouter(tags=["Health"])


@router.get("/health", include_in_schema=True)
async def health() -> JSONResponse:
    """Return 200 if the app and database are reachable, 503 otherwise."""
    db_ok = False
    try:
        async for session in get_async_session():
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    if db_ok:
        return JSONResponse(status_code=200, content={"status": "ok", "db": "ok"})
    return JSONResponse(status_code=503, content={"status": "degraded", "db": "unreachable"})
