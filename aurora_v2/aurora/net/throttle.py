"""Twelve Data throttling and retry: a 429 is a queue position, not a failure.

The free plan allows eight requests a minute. Without a client-side pacing layer
every ninth request died as HTTP 429 and a universe silently lost half its names -
which is exactly how the 40-symbol test shrank to 20 symbols while reporting
success. This module-level policy spaces calls out, honours Retry-After, and gives
up only after a bounded number of attempts.
"""
import time

MIN_INTERVAL = 7.6      # seconds between calls; 8/min is 7.5s, plus margin
MAX_ATTEMPTS = 4
BASE_BACKOFF = 8.0

_last_call = [float("-inf")]   # the first call is never made to wait
_sleep = time.sleep        # injectable so tests do not actually wait
_clock = time.monotonic


def throttle(min_interval: float | None = None) -> float:
    """Sleep so the gap between calls is at least min_interval. Returns the wait."""
    gap = MIN_INTERVAL if min_interval is None else min_interval
    now = _clock()
    wait = _last_call[0] + gap - now
    if wait > 0:
        _sleep(wait)
    _last_call[0] = _clock()
    return max(0.0, wait)


def retry_delay(attempt: int, retry_after: float | None = None) -> float:
    """Delay before attempt+1. A server that names its wait is obeyed."""
    if retry_after is not None and retry_after > 0:
        return retry_after
    return BASE_BACKOFF * (2 ** attempt)
