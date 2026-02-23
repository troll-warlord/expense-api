"""Logging configuration using structlog.

Two rendering modes — chosen automatically:
  • TTY (terminal / dev)  → colourised logfmt
  • Non-TTY (container, pipe, CI) → plain logfmt, machine-parseable by Loki / Datadog

Architecture — ONE consolidated log line per request:
  The HTTP middleware binds all request context (request_id, ip, user_id, status,
  duration_ms) and any context bound by services (transaction_id, etc.) via
  structlog.contextvars, then emits a SINGLE line at request completion.

PII scrubbing:
  scrub_pii() masks values for known-sensitive keys in 4xx/5xx request payloads.
  Imported and used by the HTTP middleware in app/main.py.

Usage in services — bind, don't log for operational context:
    from structlog.contextvars import bind_contextvars
    bind_contextvars(transaction_id=str(tx.id))   # appears in the access line

Usage for true business events (login, register, … — deserve their own line):
    import structlog
    log = structlog.get_logger(__name__)
    log.info("User logged in", user_id=str(user.id))
"""

import logging
import sys
from typing import Any

import structlog

# ── PII scrubbing ─────────────────────────────────────────────────────────────

_SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "amount",
        "description",
        "password",
        "email",
        "note",
        "otp",
        "token",
        "phone_number",
    }
)


def scrub_pii(data: Any) -> Any:
    """Recursively mask values whose keys match the sensitive-key list.

    Safe to call on any JSON-decoded structure (dict, list, or scalar).

    Example::

        scrub_pii({"amount": "500", "date": "2026-01-01"})
        # → {"amount": "REDACTED", "date": "2026-01-01"}
    """
    if isinstance(data, dict):
        return {k: "REDACTED" if k.lower() in _SENSITIVE_KEYS else scrub_pii(v) for k, v in data.items()}
    if isinstance(data, list):
        return [scrub_pii(item) for item in data]
    return data


# ── Logfmt renderer ───────────────────────────────────────────────────────────

# Preferred key order after the event — any unlisted key appears at the end.
_KEY_ORDER: tuple[str, ...] = ("status", "duration_ms", "ip", "user_id", "request_id")


def _build_logfmt_renderer(colors: bool):  # noqa: C901
    """Return a logfmt renderer for use in the structlog processor chain.

    TTY output (colors=True)::

        2026-02-24T15:22:45  level=INFO  event="POST /v1/transactions"  status=201  duration_ms=18.2  ip=127.0.0.1  user_id=c1000001  request_id=abc  transaction_id=def

    Production output (colors=False) — same fields, no ANSI codes.
    """
    SEP = "  " if colors else " "
    RST = "\033[0m" if colors else ""
    DIM = "\033[2m" if colors else ""
    LEVEL_COLORS: dict[str, str] = (
        {
            "debug": "\033[36m",
            "info": "\033[32m",
            "warning": "\033[33m",
            "error": "\033[31m",
            "critical": "\033[1;31m",
        }
        if colors
        else {}
    )

    def _quote(v: Any) -> str:
        s = str(v)
        if any(c in s for c in (" ", "=", '"', "\n", "\r")):
            return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return s

    def renderer(_logger: Any, _method: str, event_dict: dict) -> str:
        ts = event_dict.pop("timestamp", "")
        ts_str = ts[:19] if len(ts) >= 19 else ts

        level = event_dict.pop("level", "info").lower()
        event_dict.pop("logger", None)
        event = event_dict.pop("event", "")

        lc = LEVEL_COLORS.get(level, "")
        ts_part = f"{DIM}{ts_str}{RST}" if colors else ts_str
        level_part = f"{lc}level={level.upper():<8}{RST}" if colors else f"level={level.upper():<8}"
        event_part = f"{lc}event={_quote(event)}{RST}" if colors else f"event={_quote(event)}"

        parts = [ts_part, level_part, event_part]

        for key in _KEY_ORDER:
            if key in event_dict:
                val = event_dict.pop(key)
                if val is not None:
                    parts.append(f"{key}={_quote(val)}")

        for k, v in event_dict.items():
            if v is not None:
                parts.append(f"{k}={_quote(v)}")

        return SEP.join(parts)

    return renderer


# ── Bootstrap ─────────────────────────────────────────────────────────────────


def configure_logging(debug: bool = False) -> None:
    """Call once at startup (from app/main.py)."""
    level = logging.DEBUG if debug else logging.INFO

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=False),
        structlog.processors.ExceptionRenderer(),
    ]

    renderer = _build_logfmt_renderer(colors=sys.stdout.isatty())

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    for noisy in ("sqlalchemy", "uvicorn.access", "gunicorn.access", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    for important in ("uvicorn.error", "gunicorn.error"):
        logging.getLogger(important).setLevel(logging.INFO)

    for name in ("gunicorn", "gunicorn.error", "gunicorn.access", "uvicorn", "uvicorn.error", "uvicorn.access"):
        lgr = logging.getLogger(name)
        lgr.handlers = []
        lgr.propagate = True
