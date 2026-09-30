from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    runtime_root: Path
    transport_backend: str = "LOCAL_FILE"
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

    @classmethod
    def for_remote(cls, runtime_root, **kwargs):
        if "max_batch_bytes" in kwargs or "transport_backend" in kwargs:
            raise ValueError("remote ceiling is fixed by connector verification")
        return cls(runtime_root, max_batch_bytes=75_000, transport_backend="GITHUB_PRIVATE", **kwargs)

    @property
    def transport_mode(self):
        return self.transport_backend

    @property
    def real_send_enabled(self):
        return False

    def __post_init__(self):
        if self.transport_backend not in ("LOCAL_FILE", "GITHUB_PRIVATE"):
            raise ValueError("unsupported transport")
        if self.transport_backend == "GITHUB_PRIVATE" and self.max_batch_bytes > 75_000:
            raise ValueError("remote batch exceeds connector-verified ceiling")
        if self.delivery_policy not in ("at_least_once", "at_most_once"):
            raise ValueError("unsupported policy")
        if not 1 <= self.max_batch_bytes <= 100_000 or not 1 <= self.max_item_bytes <= 2_000:
            raise ValueError("size limit outside contract")
        if not 1 <= self.normal_limit <= 40 or not 1 <= self.urgent_limit <= 8:
            raise ValueError("count limit outside contract")
        if min(self.disk_budget_bytes, self.batch_ttl_seconds, self.cooldown_seconds, self.lease_seconds) <= 0:
            raise ValueError("positive budgets required")
