"""Gunicorn configuration.

Loaded automatically when gunicorn is started from the project root
(gunicorn looks for gunicorn.conf.py in the current directory).
To use explicitly: gunicorn -c gunicorn.conf.py ...
"""

import multiprocessing

# ── Server socket ──────────────────────────────────────────────────────────
bind = "0.0.0.0:8000"

# ── Workers ────────────────────────────────────────────────────────────────
worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2 + 1

# ── Timeouts ───────────────────────────────────────────────────────────────
timeout = 30
keepalive = 5

# ── Logging ────────────────────────────────────────────────────────────────
# Let our configure_logging() own ALL log output — master process included.
# Gunicorn will forward its own records through the root logger that
# configure_logging() sets up, so every line shares the same format.
accesslog = None  # disable gunicorn's own access log (we log in middleware)
errorlog = "-"  # stderr → stdout redirect handled by structlog StreamHandler


def on_starting(server):  # noqa: ARG001
    """Called once in the master process before workers are forked."""
    from app.core.config import settings
    from app.core.logging import configure_logging

    configure_logging(debug=settings.APP_DEBUG)


def post_fork(server, worker):  # noqa: ARG001
    """Called in each worker after forking — re-initialise logging so
    cache_logger_on_first_use works correctly per-worker."""
    from app.core.config import settings
    from app.core.logging import configure_logging

    configure_logging(debug=settings.APP_DEBUG)
