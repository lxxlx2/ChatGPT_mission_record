"""Research-only person/wallet registry; never an authority for signals or mail.

Loads the existing Frank v1 JSON without changing the frozen live path. New
persons and wallets are *data scopes*, not permission to subscribe, notify or
trade. Live Frank permissions remain in their existing approved policy.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re


_PERSON_ID = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
_SOL_ADDRESS = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}\Z")
_ROLES = frozenset({"PRIMARY", "SECONDARY", "RESEARCH_ONLY"})
_APPROVAL_STATUSES = frozenset({"UNREVIEWED", "RESEARCH_APPROVED"})
_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _solana_pubkey_32_bytes(address: str) -> bool:
    """Validate the encoded public-key width, not just the base58 text length.

    This is format validation only. Whether the address is a wallet owner,
    mint, token account, or PDA must be established from chain evidence in A05.
    """
    if not _SOL_ADDRESS.fullmatch(address):
        return False
    value = 0
    for character in address:
        value = value * 58 + _BASE58_ALPHABET.index(character)
    zeros = len(address) - len(address.lstrip("1"))
    byte_count = (value.bit_length() + 7) // 8
    return zeros + byte_count == 32


def _optional_reference(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("INVALID_" + field)
    return value.strip()


@dataclass(frozen=True)
class WalletBinding:
    wallet_id: str
    person_id: str
    chain: str
    address: str
    role: str
    valid_from_slot: int
    valid_to_slot: int | None
    ownership_evidence: str | None
    evidence_state: str
    binding_source: str | None
    approval_status: str
    funding_source_evidence: str | None
    controller_evidence: str | None

    @property
    def signal_allowed(self) -> bool:
        return False

    @property
    def delivery_allowed(self) -> bool:
        return False

    @property
    def trading_allowed(self) -> bool:
        return False


@dataclass(frozen=True)
class PersonRecord:
    person_id: str
    display_name: str
    research_enabled: bool
    wallets: tuple[WalletBinding, ...]

    @property
    def signal_allowed(self) -> bool:
        return False

    @property
    def delivery_allowed(self) -> bool:
        return False


def _slot(value: object, name: str, *, default: int | None = None) -> int | None:
    if value is None:
        return default
    if type(value) is not int or value < 0:
        raise ValueError("INVALID_" + name)
    return value


class PersonRegistry:
    """Explicit, strict research identity binding with half-open slot ranges.

    schema v1 is the current frank_local_registry.json and is read compatibly.
    Optional v2 bindings can be historical; overlapping binding assignments
    for any chain/address are rejected even when they name the same person.

    This registry *never* confers signal, delivery, or trading authority.
    """

    def __init__(self, persons: tuple[PersonRecord, ...], schema_version: int):
        self.schema_version = schema_version
        self._people = {person.person_id: person for person in persons}
        self._wallets: dict[tuple[str, str], list[WalletBinding]] = {}
        for person in persons:
            for wallet in person.wallets:
                self._wallets.setdefault((wallet.chain, wallet.address), []).append(wallet)

    @classmethod
    def from_file(cls, path: str | Path) -> "PersonRegistry":
        return cls.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))

    @classmethod
    def from_mapping(cls, data: object) -> "PersonRegistry":
        if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] not in (1, 2):
            raise ValueError("PERSON_REGISTRY_SCHEMA_UNSUPPORTED")
        version = data["schema_version"]
        source = data.get("persons")
        if not isinstance(source, list) or not source:
            raise ValueError("PERSON_REGISTRY_EMPTY")
        persons: list[PersonRecord] = []
        seen_people: set[str] = set()
        seen_ranges: dict[tuple[str, str], list[tuple[int, int | None]]] = {}
        for raw in source:
            if not isinstance(raw, dict):
                raise ValueError("INVALID_PERSON")
            pid = raw.get("person_id")
            if not isinstance(pid, str) or not _PERSON_ID.fullmatch(pid):
                raise ValueError("INVALID_PERSON_ID")
            if pid in seen_people:
                raise ValueError("DUPLICATE_PERSON_ID")
            seen_people.add(pid)
            display = raw.get("display_name", pid)
            if not isinstance(display, str) or not display.strip():
                raise ValueError("INVALID_DISPLAY_NAME")
            enabled = raw.get("enabled", False)
            if type(enabled) is not bool:
                raise ValueError("INVALID_LEGACY_ENABLED")
            if pid != "frank" and enabled:
                raise ValueError("NEW_PERSON_CANNOT_ENABLE_LEGACY_SIGNAL")
            research = raw.get("research_enabled", enabled if pid == "frank" else False)
            if type(research) is not bool:
                raise ValueError("INVALID_RESEARCH_ENABLED")
            permissions = raw.get("permissions", {})
            if not isinstance(permissions, dict) or any(
                permissions.get(field) is not False and permissions.get(field) is not None
                for field in ("signal_evaluation", "delivery", "trading")
            ):
                raise ValueError("RESEARCH_REGISTRY_CANNOT_AUTHORIZE_LIVE_ACTIONS")
            wallets = raw.get("wallets")
            if not isinstance(wallets, list) or (not wallets and enabled):
                raise ValueError("PERSON_WALLETS_EMPTY")
            bindings: list[WalletBinding] = []
            for item in wallets:
                if not isinstance(item, dict):
                    raise ValueError("INVALID_WALLET")
                chain = item.get("chain")
                address = item.get("address")
                if chain != "solana" or not isinstance(address, str) or not _solana_pubkey_32_bytes(address):
                    raise ValueError("UNSUPPORTED_OR_INVALID_WALLET")
                role = item.get("role", "RESEARCH_ONLY")
                if role not in _ROLES:
                    raise ValueError("INVALID_WALLET_ROLE")
                wperm = item.get("permissions", {})
                if not isinstance(wperm, dict) or any(
                    wperm.get(field) is not False and wperm.get(field) is not None
                    for field in ("signal_evaluation", "delivery", "trading")
                ):
                    raise ValueError("WALLET_CANNOT_AUTHORIZE_LIVE_ACTIONS")
                if version == 1 and any(k in item for k in ("valid_from_slot", "valid_to_slot")):
                    raise ValueError("TEMPORAL_BINDINGS_REQUIRE_V2")
                if version == 2 and item.get("valid_from_slot") is None:
                    raise ValueError("TEMPORAL_VALID_FROM_REQUIRED")
                start = _slot(item.get("valid_from_slot"), "VALID_FROM_SLOT", default=0)
                stop = _slot(item.get("valid_to_slot"), "VALID_TO_SLOT")
                if stop is not None and stop <= start:
                    raise ValueError("INVALID_WALLET_INTERVAL")
                key = (chain, address)
                for existing_start, existing_stop in seen_ranges.get(key, ()):
                    if start < (existing_stop if existing_stop is not None else float("inf")) and (
                        existing_start < (stop if stop is not None else float("inf"))
                    ):
                        raise ValueError("WALLET_BINDING_OVERLAP")
                seen_ranges.setdefault(key, []).append((start, stop))
                evidence = _optional_reference(item.get("ownership_evidence"), "OWNERSHIP_EVIDENCE")
                binding_source = _optional_reference(item.get("source"), "BINDING_SOURCE")
                funding_source = _optional_reference(item.get("funding_source_evidence"), "FUNDING_SOURCE_EVIDENCE")
                controller = _optional_reference(item.get("controller_evidence"), "CONTROLLER_EVIDENCE")
                approval_status = item.get("approval_status", "UNREVIEWED")
                if type(approval_status) is not str or approval_status not in _APPROVAL_STATUSES:
                    raise ValueError("INVALID_BINDING_APPROVAL_STATUS")
                # A registered reference or research approval never proves beneficial
                # control, on-chain inventory, cost basis, or live authorization.
                evidence_state = "CLAIMED_WITH_REFERENCE" if evidence else "REGISTERED_UNVERIFIED"
                binding_id = chain + ":" + address
                if version == 2:
                    binding_id += "@" + str(start)
                bindings.append(WalletBinding(
                    wallet_id=binding_id, person_id=pid, chain=chain,
                    address=address, role=role, valid_from_slot=start,
                    valid_to_slot=stop, ownership_evidence=evidence,
                    evidence_state=evidence_state, binding_source=binding_source,
                    approval_status=approval_status,
                    funding_source_evidence=funding_source,
                    controller_evidence=controller,
                ))
            persons.append(PersonRecord(
                person_id=pid, display_name=display.strip(),
                research_enabled=research, wallets=tuple(bindings),
            ))
        return cls(tuple(persons), version)

    def research_people(self) -> tuple[PersonRecord, ...]:
        return tuple(person for person in self._people.values() if person.research_enabled)

    def person(self, person_id: str) -> PersonRecord:
        person = self._people.get(person_id)
        if person is None or not person.research_enabled:
            raise KeyError("RESEARCH_PERSON_NOT_ENABLED")
        return person

    def wallets_for(self, person_id: str, *, slot: int | None = None) -> tuple[WalletBinding, ...]:
        person = self.person(person_id)
        if slot is None:
            return tuple(w for w in person.wallets if w.valid_to_slot is None)
        requested = _slot(slot, "LOOKUP_SLOT")
        return tuple(w for w in person.wallets
                     if w.valid_from_slot <= requested and (
                         w.valid_to_slot is None or requested < w.valid_to_slot
                     ))

    def wallet_at(self, chain: str, address: str, *, slot: int | None = None) -> WalletBinding:
        if slot is None:
            found = [w for w in self._wallets.get((chain, address), ())
                     if w.valid_to_slot is None]
        else:
            requested = _slot(slot, "LOOKUP_SLOT")
            found = [w for w in self._wallets.get((chain, address), ())
                     if w.valid_from_slot <= requested and (
                         w.valid_to_slot is None or requested < w.valid_to_slot
                     )]
        if len(found) != 1 or not self.person(found[0].person_id):
            raise KeyError("RESEARCH_WALLET_NOT_BOUND")
        return found[0]
