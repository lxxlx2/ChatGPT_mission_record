"""Read-only, opt-in local ledger partitions. No production registry or sender wiring."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat

from ..meme.holder_ranks import valid_pubkey


def _person_id(value):
    return isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", value) is not None


def _unique_object(pairs):
    found = {}
    for key, value in pairs:
        if key in found:
            raise ValueError("DUPLICATE_PERSON_REGISTRY_KEY")
        found[key] = value
    return found


@dataclass(frozen=True)
class PersonWalletScope:
    person_id: str
    wallets: tuple[str, ...]

    def __post_init__(self):
        if (not _person_id(self.person_id) or not isinstance(self.wallets, tuple)
                or not (1 <= len(self.wallets) <= 32) or not all(valid_pubkey(w) for w in self.wallets)
                or len(set(self.wallets)) != len(self.wallets)):
            raise ValueError("INVALID_PERSON_WALLET_SCOPE")
        object.__setattr__(self, "wallets", tuple(sorted(self.wallets)))

    def for_wallet(self, wallet):
        if wallet not in self.wallets:
            raise ValueError("WALLET_OUTSIDE_PERSON_SCOPE")
        return PersonWalletScope(self.person_id, (wallet,))


def load_staged_person_scopes(path: Path, *, allowed_person_ids: frozenset[str]) -> dict[str, PersonWalletScope]:
    """Require a trusted local registry and explicit allow-list; never enable a scanner."""
    if (not isinstance(allowed_person_ids, frozenset) or not (1 <= len(allowed_person_ids) <= 32)
            or not all(_person_id(p) for p in allowed_person_ids)):
        raise ValueError("EXPLICIT_STAGED_PERSONS_REQUIRED")
    def open_registry(name, flags):
        fd = os.open(name, flags | os.O_NONBLOCK | os.O_NOFOLLOW)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise ValueError("PERSON_REGISTRY_FILE_REQUIRED")
        return fd

    with open(Path(path), "rb", opener=open_registry) as source:
        raw = source.read(262145)
    if len(raw) > 262144:
        raise ValueError("PERSON_REGISTRY_TOO_LARGE")
    data = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(data, dict) or not isinstance(data.get("persons"), list):
        raise ValueError("INVALID_PERSON_REGISTRY")
    known, scopes, assigned_wallets = set(), {}, set()
    for entry in data["persons"]:
        if (not isinstance(entry, dict) or not _person_id(entry.get("person_id"))
                or type(entry.get("enabled")) is not bool):
            raise ValueError("INVALID_PERSON_REGISTRY")
        person = entry["person_id"]
        if person in known:
            raise ValueError("DUPLICATE_PERSON_ID")
        known.add(person)
        if not entry["enabled"]:
            continue
        if person not in allowed_person_ids:
            raise ValueError("UNAPPROVED_STAGED_PERSON")
        wallets = entry.get("wallets")
        if not isinstance(wallets, list) or not all(
            isinstance(w, dict) and w.get("chain") == "solana" and valid_pubkey(w.get("address")) for w in wallets
        ):
            raise ValueError("INVALID_PERSON_WALLETS")
        scope = PersonWalletScope(person, tuple(w["address"] for w in wallets))
        if assigned_wallets.intersection(scope.wallets):
            raise ValueError("WALLET_IN_MULTIPLE_PERSON_SCOPES")
        assigned_wallets.update(scope.wallets)
        scopes[person] = scope
    if set(scopes) != allowed_person_ids:
        raise ValueError("STAGED_PERSON_NOT_ENABLED")
    return scopes
