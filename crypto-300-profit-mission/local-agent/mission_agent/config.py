from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    runtime_root: Path
    runtime_repo: str = "lxxlx2/crypto-monitor-runtime"
    delivery_policy: str = "at_least_once"
    disk_budget_bytes: int = 5_000_000_000
    max_batch_bytes: int = 100_000
    max_item_bytes: int = 2_000
    normal_limit: int = 40
    urgent_limit: int = 8
    batch_ttl_seconds: int = 7200
    cooldown_seconds: int = 60
    lease_seconds: int = 120

    @property
    def transport_mode(self):
        return "LOCAL_FILE"

    @property
    def real_send_enabled(self):
        return False

    def __post_init__(self):
        if self.delivery_policy not in ("at_least_once", "at_most_once"):
            raise ValueError("unsupported policy")
        if not 1 <= self.max_batch_bytes <= 100_000 or not 1 <= self.max_item_bytes <= 2_000:
            raise ValueError("size limit outside contract")
        if not 1 <= self.normal_limit <= 40 or not 1 <= self.urgent_limit <= 8:
            raise ValueError("count limit outside contract")
        if min(self.disk_budget_bytes, self.batch_ttl_seconds, self.cooldown_seconds, self.lease_seconds) <= 0:
            raise ValueError("positive budgets required")
