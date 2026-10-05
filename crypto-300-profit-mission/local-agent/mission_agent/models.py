from dataclasses import dataclass
from .clock import parse_utc, stamp
from .hashing import normalize, digest

EVENT_TYPES = frozenset({"RAW_PRICE_CANDIDATE", "RAW_FRANK_CANDIDATE", "RAW_MONSTER_CANDIDATE",
                         "RAW_NFT_CANDIDATE", "TEST_ACTION_CANDIDATE"})
DECISIONS = frozenset({"IGNORE", "WATCH", "ACTIONABLE_RISK", "ACTIONABLE_OPPORTUNITY"})
DELIVERY_STATES = frozenset({"PENDING_DECISION", "DECIDED_IGNORE", "DECIDED_WATCH",
                           "DELIVERY_PENDING", "DELIVERY_SENDING", "DELIVERY_UNCERTAIN",
                           "DELIVERED", "FAILED_MANUAL_REVIEW"})


@dataclass(frozen=True)
class Event:
    event_id: str
    event_type: str
    asset: str | None
    observed_at_utc: str
    priority: int
    payload: dict
    source: str = "synthetic"

    @classmethod
    def synthetic(cls, event_type, asset, observed_at, priority, payload, seed="0"):
        if event_type not in EVENT_TYPES or type(priority) is not int or priority not in (0, 1):
            raise ValueError("invalid synthetic type/priority")
        if asset is not None and (not isinstance(asset, str) or len(asset) > 80):
            raise ValueError("invalid asset")
        if not isinstance(payload, dict):
            raise ValueError("object payload required")
        observed_at = stamp(parse_utc(observed_at))
        data = normalize({"event_type": event_type, "asset": asset, "observed_at_utc": observed_at,
                          "priority": priority, "payload": payload, "seed": str(seed)})
        return cls("synthetic:v1:" + digest(data), event_type, data["asset"], observed_at,
                   priority, data["payload"])
