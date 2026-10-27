"""Candidate BSC physical HTTPS source for the ORIGINAL D1 shared coordinator.

SOURCE CODE ONLY: no public runner or authorization.  This exact source type
allows the existing bounded http.client HTTPS code to be reviewed in the one
shared RID/RAW/3-slot path. It MUST NOT be dispatched outside a future
independently reviewed, one-owner, one-time foreground child. The module seal
only prevents accidental construction; it is NOT authentication or permission.
No real JSON-RPC is sent by importing or constructing this source.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from f0_l1_http_wire import MAX_BODY_BYTES
from f0_l2_d1_concrete_https import (
    _REVIEW_TEST_ONLY_CAPABILITY, _review_concrete_https_once,
)
from f0_l2_d1_preflight import parse_utc_timestamp

# This internal seal is NOT a cryptographic/user authorization boundary.
# The future physical child MUST independently consume a one-shot user grant.
_UNRELEASED_SOURCE_CODE_SEAL = object()


class BoundedPhysicalReadOnlySource:
    """Exactly one fixed-host HTTP source; no URL, keys or transport callback."""

    __slots__ = ("_start", "_end", "_last")

    def __init__(self, start_utc: str, end_utc: str, *,
                 _unreleased_review_seal=None):
        if (_unreleased_review_seal is not _UNRELEASED_SOURCE_CODE_SEAL
                or type(start_utc) is not str
                or type(end_utc) is not str):
            raise ValueError("F0_REAL_SOURCE_FOREGROUND_RELEASE_NOT_REVIEWED")
        start = parse_utc_timestamp(start_utc)
        end = parse_utc_timestamp(end_utc)
        if not timedelta(0) < end - start <= timedelta(seconds=60):
            raise ValueError("F0_REAL_SOURCE_UTC_WINDOW_INVALID")
        self._start = start
        self._end = end
        self._last = None

    def check_at_actual_post(self):
        """UTC is checked AFTER TLS connect and shared start-gap wait."""
        now = datetime.now(timezone.utc)
        if self._last is not None and now < self._last:
            raise ValueError("F0_REAL_SOURCE_UTC_ROLLBACK")
        self._last = now
        if not self._start <= now <= self._end:
            raise ValueError("F0_REAL_SOURCE_POST_UTC_OUTSIDE_WINDOW")
        return now

    def reply_transport_evidence_physical_candidate(
            self, request, begin_at_real_post, timeout_s, *,
            reservation_guard=None):
        """Invoke the EXISTING HTTPS primitive, not a new sender.

        This method is reachable only from the private coordinator candidate
        integration. The end-to-end source is NOT released here: independent
        foreground child/one-use-grant integration is still missing.
        """
        from f0_l2_d1_coordinator import _StagedOnlyReservationGuard
        if (type(self) is not BoundedPhysicalReadOnlySource
                or type(reservation_guard) is not _StagedOnlyReservationGuard
                or not callable(begin_at_real_post)):
            raise ValueError("F0_REAL_SOURCE_DURABLE_RID_REQUIRED")
        reservation_guard(request)
        denied = [None]

        def pre_connect(payload):
            if payload != request:
                raise ValueError("F0_REAL_SOURCE_PRECONNECT_PAYLOAD_CHANGED")
            reservation_guard(payload)

        def final_post(payload):
            if payload != request:
                raise ValueError("F0_REAL_SOURCE_PREPOST_PAYLOAD_CHANGED")
            try:
                begin_at_real_post()
            except Exception as exc:
                denied[0] = exc
                raise

        # The actual HTTP implementation is the original reviewed primitive:
        # TLS hostname validation, fixed :443 host, 2MB max body, no redirect,
        # no proxy, no retry and exact full-block JSON-RPC whitelist.
        # Its historical name/capability are TEST labels, not run authority.
        result = _review_concrete_https_once(
            request, final_post_guard=final_post,
            pre_connect_guard=pre_connect,
            _test_capability=_REVIEW_TEST_ONLY_CAPABILITY,
            timeout_s=timeout_s, max_bytes=MAX_BODY_BYTES)
        if denied[0] is not None:
            raise denied[0]
        raw = result["raw_frame"]
        if result["state"] == "RAW" and raw is not None:
            return {"state": "RAW", "frame": raw, "failure": None}
        if raw is not None:
            return {"state": "REJECTED_RAW", "frame": raw,
                    "failure": result["failure"]}
        return {"state": "FAILED_NO_RAW", "frame": None,
                "failure": result["failure"]}


def send_live(*_args, **_kwargs):
    """No released physical CLI/one-shot authority in this code-only PR."""
    raise ValueError("F0_REAL_SOURCE_ONE_SHOT_FOREGROUND_NOT_RELEASED")
