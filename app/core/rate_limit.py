"""Application-wide rate limiter (slowapi / limits).

The limiter uses in-memory storage by default.  In production with multiple
workers, each worker has its own counter — so the effective limit across all
workers is limit × num_workers.  For stricter enforcement, swap the storage
backend for a shared Redis instance:

    from limits.storage import RedisStorage
    limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],  # no global limit; apply per-endpoint
)
