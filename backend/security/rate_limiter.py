import time
from collections import defaultdict
from threading import Lock


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str) -> bool:
        if not key:
            return True
        now = time.time()
        normalized_key = key.strip().lower()

        with self._lock:
            timestamps = self._requests[normalized_key]
            cutoff = now - self.window_seconds
            # Retain only timestamps within the active window
            active_timestamps = [t for t in timestamps if t > cutoff]
            if len(active_timestamps) >= self.max_requests:
                self._requests[normalized_key] = active_timestamps
                return False
            active_timestamps.append(now)
            self._requests[normalized_key] = active_timestamps
            return True

    def reset(self):
        """Clears all tracked requests."""
        with self._lock:
            self._requests.clear()


# Default policies:
# - Max 5 reset requests per 15 minutes per IP address
# - Max 3 reset requests per 15 minutes per email address
ip_rate_limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=900)
email_rate_limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=900)


def reset_rate_limiters():
    """Resets all rate limiter stores (primarily for testing)."""
    ip_rate_limiter.reset()
    email_rate_limiter.reset()
