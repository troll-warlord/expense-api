"""Logging configuration using structlog.

Two rendering modes — chosen automatically:
  • TTY (terminal / dev)  → colored, aligned, human-readable
  • Non-TTY (container, file, pipe, CI) → one JSON object per line

Request context (request_id, user_id) is bound once in the HTTP middleware and
automatically included in EVERY log line emitted during that request — from any
service, repository, or utility — without passing anything explicitly.

Usage anywhere in the app:
    import structlog
    log = structlog.get_logger(__name__)
    log.info("transaction created", transaction_id=str(tx.id))
"""

import logging
import sys

import structlog


def configure_logging(debug: bool = False) -> None:
    """Call once at startup (from app/main.py)."""

    level = logging.DEBUG if debug else logging.INFO

    # ── Shared processors applied to every log record ────────────────
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,  # inject bound context (request_id, user_id, …)
        structlog.stdlib.add_logger_name,  # "logger" key
        structlog.stdlib.add_log_level,  # "level" key
        structlog.processors.TimeStamper(fmt="%Y-%m-%dT%H:%M:%S", utc=False),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.ExceptionRenderer(),
    ]

    # ── Key order processor ───────────────────────────────────────────
    # Reorders the event dict so every log line has a consistent,
    # human-friendly field sequence regardless of insertion order.
    _PREFERRED_KEY_ORDER = [
        "timestamp",
        "level",
        "logger",
        "event",
        "method",
        "path",
        "status",
        "ip",
        "user_id",
        "request_id",
    ]

    def _reorder_keys(_logger, _method, event_dict: dict) -> dict:
        reordered = {k: event_dict[k] for k in _PREFERRED_KEY_ORDER if k in event_dict}
        reordered.update({k: v for k, v in event_dict.items() if k not in reordered})
        return reordered

    # ── Auto-detect renderer ──────────────────────────────────────────
    # isatty() → True when running in a real terminal (dev / ssh)
    # isatty() → False when stdout is a pipe/file (container, systemd, CI)
    if sys.stdout.isatty():
        renderer = structlog.dev.ConsoleRenderer(colors=True, sort_keys=False)
    else:
        renderer = structlog.processors.JSONRenderer()

    # ── Configure structlog ───────────────────────────────────────────
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

    # ── Configure stdlib logging (so existing logging.getLogger() calls
    #    also go through structlog's formatting pipeline) ──────────────
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _reorder_keys,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Silence noisy third-party loggers
    for noisy in ("sqlalchemy", "uvicorn.access", "gunicorn.access", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    for important in ("uvicorn.error", "gunicorn.error"):
        logging.getLogger(important).setLevel(logging.INFO)

    # Gunicorn and uvicorn install their own handlers directly on their loggers
    # before our configure_logging() is called.  Clear those handlers so every
    # record propagates up to the single root handler above (our structlog one).
    for name in ("gunicorn", "gunicorn.error", "gunicorn.access", "uvicorn", "uvicorn.error", "uvicorn.access"):
        lgr = logging.getLogger(name)
        lgr.handlers = []
        lgr.propagate = True
