"""Fail-closed, offline Monster event as-of projection for P0 source evidence.

No network, wallet, live monitoring, future labels, or trading. This only filters
events by *declared* provenance: original timing/source proof still needs separate
independent verification before the production/P1 gate is passed.
"""
from datetime import datetime, timedelta, timezone
import re


class PITAsOfError(ValueError):
    pass


_PROVEN_BASIS = frozenset((
    "ACTUAL_HISTORICAL_PUBLICATION", "ACTUAL_LIVE_OBSERVER_RECEIPT"))
_POLICIES = frozenset((
    "LIVE_OBSERVED", "RECONSTRUCTED_CONSERVATIVE", "NO_VERIFIABLE_ASOF"))
_HASH = re.compile(r"^[0-9a-fA-F]{64}$")
_EVENTS = frozenset((
    "DEPLOYED", "POOL_CREATED", "LIQ_ADDED", "FIRST_SWAP", "SWAP",
    "ALPHA_ANNOUNCED", "ALPHA_LISTED", "USDM_ANNOUNCED", "USDM_LISTED",
    "SPOT_ANNOUNCED", "SPOT_LISTED", "LIQ_REMOVED", "POOL_MIGRATED",
    "DELISTED"))

_OFFCHAIN_EVENTS = frozenset((
    "ALPHA_ANNOUNCED", "ALPHA_LISTED",
    "USDM_ANNOUNCED", "USDM_LISTED",
    "SPOT_ANNOUNCED", "SPOT_LISTED"))


def _time(raw):
    if not isinstance(raw, str):
        raise PITAsOfError("OFFSET_AWARE_ISO_TIMESTAMP_REQUIRED")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("naive")
        return value.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise PITAsOfError("OFFSET_AWARE_ISO_TIMESTAMP_REQUIRED") from None


def asof(token_key, decision_at, information_policy, *, events,
         historical_delay_ms=None, historical_delay_policy_sha256=None):
    """Project only genuinely visible events from one exact chain+CA identity.

    'LIVE_OBSERVED' needs provenance-marked, externally attested available_at.
    'RECONSTRUCTED_CONSERVATIVE' additionally permits explicit delay-assumed
    chain timestamps; its result is never PIT_VERIFIED, regardless of inputs.
    NO_VERIFIABLE_ASOF always fails closed. A policy SHA is a *reference*, not
    automatic proof that the delay policy was actually approved and frozen.
    """
    if not isinstance(token_key, str) or not token_key.strip():
        raise PITAsOfError("TOKEN_KEY_REQUIRED")
    decision = _time(decision_at)
    if information_policy not in _POLICIES:
        raise PITAsOfError("INFORMATION_POLICY_INVALID")
    if not isinstance(events, list):
        raise PITAsOfError("EVENTS_ARRAY_REQUIRED")
    if information_policy == "RECONSTRUCTED_CONSERVATIVE":
        if (type(historical_delay_ms) is not int or historical_delay_ms <= 0
                or not isinstance(historical_delay_policy_sha256, str)
                or not _HASH.fullmatch(historical_delay_policy_sha256)):
            raise PITAsOfError("FROZEN_DELAY_POLICY_AND_POSITIVE_MS_REQUIRED")
    elif historical_delay_ms is not None or historical_delay_policy_sha256 is not None:
        raise PITAsOfError("DELAY_ONLY_FOR_RECONSTRUCTED_POLICY")
    if information_policy == "NO_VERIFIABLE_ASOF":
        return {"token_key": token_key, "decision_at": decision.isoformat(),
                "policy": information_policy, "pit_status": "NOT_SCORABLE",
                "events": [], "source_provenance_independently_verified": False,
                "p1_gate_passed": False}

    seen = {}
    for e in events:
        if not isinstance(e, dict):
            raise PITAsOfError("EVENT_OBJECT_REQUIRED")
        if e.get("token_key") != token_key:
            continue
        event_id = e.get("event_id")
        source_hash = e.get("source_sha256")
        if (not isinstance(event_id, str) or not event_id
                or not isinstance(source_hash, str)
                or not _HASH.fullmatch(source_hash)
                or e.get("event_type") not in _EVENTS
                or not isinstance(e.get("venue"), str)
                or not e["venue"]):
            raise PITAsOfError("EVENT_ID_TYPE_OR_SOURCE_INVALID")
        chain_raw = e.get("chain_event_at")
        chain_at = _time(chain_raw) if chain_raw is not None else None
        # Off-chain announcements and listings have no required chain clock
        # under the frozen schema. A *future* optional chain timestamp must
        # never be disclosed in a past as-of view.
        if chain_at is None and e["event_type"] not in _OFFCHAIN_EVENTS:
            continue
        basis = e.get("availability_basis")
        status = e.get("pit_status")
        effective = None
        grade = None
        if status == "PIT_VERIFIED" and basis in _PROVEN_BASIS:
            if e.get("available_at") is None:
                continue
            effective = _time(e["available_at"])
            if chain_at is not None and effective < chain_at and (
                    e["event_type"] not in _OFFCHAIN_EVENTS):
                raise PITAsOfError("AVAILABLE_BEFORE_CHAIN_EVENT")
            time_key = ("observed_at" if basis == "ACTUAL_LIVE_OBSERVER_RECEIPT"
                        else "published_at")
            if e.get(time_key) is None or _time(e[time_key]) > effective:
                raise PITAsOfError("PUBLICATION_OR_RECEIPT_PROOF_CLOCK_INVALID")
            grade = "PIT_VERIFIED"
        elif (information_policy == "RECONSTRUCTED_CONSERVATIVE"
              and status == "PIT_RECONSTRUCTED_ONLY"
              and basis == "RECONSTRUCTED_DELAY_ASSUMPTION"
              and e.get("available_at") is None
              and chain_at is not None):
            try:
                effective = chain_at + timedelta(milliseconds=historical_delay_ms)
            except OverflowError:
                raise PITAsOfError("DELAY_OVERFLOWS_CLOCK") from None
            grade = "PIT_RECONSTRUCTED_ONLY"
        else:
            continue
        if chain_at is not None and chain_at > decision:
            continue
        if effective > decision:
            continue
        # Explicit allowlist: never expose future labels, future holder data,
        # later liquidity snapshots, scoring features, or arbitrary payloads.
        row = {
            "event_id": event_id, "token_key": token_key,
            "event_type": e["event_type"], "venue": e["venue"],
            "chain_event_at": (
                chain_at.isoformat() if chain_at is not None else None),
            "effective_available_at": effective.isoformat(),
            "pit_status": grade, "source_sha256": source_hash.lower(),
            "origin_kind": e.get("origin_kind"),
        }
        if event_id in seen and seen[event_id] != row:
            raise PITAsOfError("CONFLICTING_SAME_EVENT_ID")
        seen[event_id] = row
    ordered = sorted(seen.values(), key=lambda r: (
        r["effective_available_at"], r["event_id"]))
    grade = ("PIT_RECONSTRUCTED_ONLY" if information_policy ==
             "RECONSTRUCTED_CONSERVATIVE" and ordered else
             "PIT_VERIFIED" if ordered else "NOT_SCORABLE")
    result = {"token_key": token_key, "decision_at": decision.isoformat(),
              "policy": information_policy, "pit_status": grade,
              "events": ordered, "source_provenance_independently_verified": False,
                "p1_gate_passed": False}
    if information_policy == "RECONSTRUCTED_CONSERVATIVE":
        result["assumption_ms"] = historical_delay_ms
        result["delay_policy_sha256"] = historical_delay_policy_sha256.lower()
    return result
