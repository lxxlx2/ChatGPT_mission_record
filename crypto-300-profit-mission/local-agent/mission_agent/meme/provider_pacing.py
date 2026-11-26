"""In-process, per-host dispatch pacing for isolated CA scope workers."""
from threading import Lock
import time
from urllib.parse import urlsplit


class SharedProviderPacing:
    """Share request starts and backoff, never wait while holding the lock."""

    def __init__(self, *, monotonic=time.monotonic):
        self._clock = monotonic
        self._lock = Lock()
        self._last = {}
        self._cooldown = {}

    @staticmethod
    def _key(endpoint):
        # Different credentials/paths on the same host share the same quota.
        return urlsplit(endpoint).hostname

    def cooldown_until(self, endpoint):
        with self._lock:
            return self._cooldown.get(self._key(endpoint), 0.0)

    def cool_down(self, endpoint, seconds):
        key = self._key(endpoint)
        with self._lock:
            self._cooldown[key] = max(self._cooldown.get(key, 0.0), self._clock() + seconds)

    def reserve(self, endpoint, interval, *, sleep, check):
        key = self._key(endpoint)
        while True:
            check()
            with self._lock:
                now = self._clock()
                ready = max(self._last.get(key, -interval) + interval, self._cooldown.get(key, 0.0))
                if ready <= now:
                    self._last[key] = now
                    return
            sleep(ready - now)
