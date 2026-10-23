"""D1 OFFLINE real-thread fake-POST UTC send-time gate; never a live permit.

The verification clock is supplied by the isolated test caller. Its readings
cannot authenticate external time and must never enable send_live(). The gate
is called AFTER the simulated HTTPS/TLS setup, at the final memory POST point.
"""
from datetime import datetime, timedelta
from hashlib import sha256

from f0_l2_d1_bundle import _strict_permit
from f0_l2_d1_preflight import parse_utc_timestamp
from f0_l1_http_wire import valid_rpc_payload


class OfflinePostUTCWindow:
    def __init__(self, raw_permit, expected_sha, test_only_utc_clock):
        permit=_strict_permit(raw_permit)
        if (permit["approved_commit_sha"] != expected_sha
                or not callable(test_only_utc_clock)):
            raise ValueError("D1_POST_UTC_SCOPE_UNBOUND")
        start=parse_utc_timestamp(permit["window_start_utc"])
        end=parse_utc_timestamp(permit["window_end_utc"])
        if not timedelta(0) < end-start <= timedelta(minutes=10):
            raise ValueError("D1_POST_UTC_SCOPE_INVALID")
        self.start=start
        self.end=end
        self._clock=test_only_utc_clock
        self._last=None
        self.source_sha=expected_sha
        self.permit_sha256=sha256(raw_permit).hexdigest()
        self.checked_fake_posts=0

    def check_at_fake_post(self, payload):
        valid_rpc_payload(payload)
        now=self._clock()
        if (type(now) is not datetime or now.tzinfo is None
                or now.utcoffset() != timedelta(0)):
            raise ValueError("D1_POST_UTC_CLOCK_NOT_TRUSTWORTHY")
        if self._last is not None and now < self._last:
            raise ValueError("D1_POST_UTC_CLOCK_ROLLBACK")
        self._last=now
        if not self.start <= now <= self.end:
            raise ValueError("D1_POST_UTC_WINDOW_EXPIRED")
        self.checked_fake_posts+=1
        return "OFFLINE_FAKE_POST_UTC_CHECKED_NOT_LIVE"
