"""Conservative admission guard; preserves accepted work instead of evicting it."""
from pathlib import Path


class DiskBudgetExceeded(RuntimeError):
    pass


def used_bytes(root):
    return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file() and not p.is_symlink())


def admit(root,extra_bytes,budget=5_000_000_000):
    if used_bytes(root)+extra_bytes>budget*95//100:
        raise DiskBudgetExceeded('UNHEALTHY_DISK: preserve backlog; stop new writes')
