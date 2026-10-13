"""Independent-review regression cases for read-only research binding integrity.

Synthetic addresses are format fixtures, not on-chain wallet-control evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mission_agent.meme.registry import Registry as MemeRegistry
from mission_agent.mission_control.person_registry import PersonRegistry
from mission_agent.signals.registry import load as load_live_registry


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "config/frank_local_registry.json"
MEME = ROOT / "config/meme_person_registry.json"
SYNTHETIC_KEY = "1" * 32


def _document(*people, version=2):
    return {"schema_version": version, "persons": list(people)}


def _person(pid="frank", *, from_slot=0, to_slot=None, address=SYNTHETIC_KEY,
            enabled=False, research=True):
    wallet = {"chain": "solana", "address": address, "role": "PRIMARY"}
    if from_slot is not None:
        wallet["valid_from_slot"] = from_slot
    if to_slot is not None:
        wallet["valid_to_slot"] = to_slot
    return {"person_id": pid, "display_name": pid, "enabled": enabled,
            "research_enabled": research, "wallets": [wallet]}


@pytest.mark.parametrize("address", ["1" * 33, "z" * 44])
def test_rejects_base58_strings_that_do_not_decode_to_32_bytes(address):
    with pytest.raises(ValueError, match="UNSUPPORTED_OR_INVALID_WALLET"):
        PersonRegistry.from_mapping(_document(_person(address=address)))


def test_accepts_exact_width_key_only_as_unverified_registration():
    reg = PersonRegistry.from_mapping(_document(_person()))
    binding = reg.wallet_at("solana", SYNTHETIC_KEY, slot=0)
    assert binding.evidence_state == "REGISTERED_UNVERIFIED"
    assert binding.approval_status == "UNREVIEWED"
    assert not binding.signal_allowed and not binding.delivery_allowed
    assert not binding.trading_allowed


def test_v2_rejects_missing_historical_origin_instead_of_retroactive_assignment():
    with pytest.raises(ValueError, match="TEMPORAL_VALID_FROM_REQUIRED"):
        PersonRegistry.from_mapping(_document(_person(from_slot=None)))


@pytest.mark.parametrize("version", [True, 1.0, 2.0])
def test_schema_version_must_be_exact_integer(version):
    person = _person()
    del person["wallets"][0]["valid_from_slot"]
    with pytest.raises(ValueError, match="PERSON_REGISTRY_SCHEMA_UNSUPPORTED"):
        PersonRegistry.from_mapping(_document(person, version=version))


def test_reassignment_uses_unique_binding_ids_and_exact_half_open_intervals():
    older = _person("frank", from_slot=0, to_slot=100, enabled=True)
    newer = _person("person_b", from_slot=100)
    reg = PersonRegistry.from_mapping(_document(older, newer))
    previous = reg.wallet_at("solana", SYNTHETIC_KEY, slot=99)
    current = reg.wallet_at("solana", SYNTHETIC_KEY, slot=100)
    assert previous.person_id == "frank"
    assert current.person_id == "person_b"
    assert previous.wallet_id != current.wallet_id
    assert previous.wallet_id.endswith("@0")
    assert current.wallet_id.endswith("@100")


def test_disabled_person_with_no_wallet_matches_legacy_loader():
    active = _person(enabled=True)
    inactive = {"person_id": "person_b", "display_name": "B",
                "enabled": False, "research_enabled": False, "wallets": []}
    reg = PersonRegistry.from_mapping(_document(active, inactive))
    assert [p.person_id for p in reg.research_people()] == ["frank"]
    assert reg.wallets_for("frank", slot=0)
    assert not reg._people["person_b"].wallets


def test_binding_provenance_is_metadata_and_not_asset_or_mail_authorization():
    p = _person(enabled=True)
    p["wallets"][0].update({
        "source": "research:approved-record",
        "approval_status": "RESEARCH_APPROVED",
        "ownership_evidence": "candidate:public-link",
        "funding_source_evidence": "unverified:funder-reference",
        "controller_evidence": "unverified:controller-reference",
    })
    w = PersonRegistry.from_mapping(_document(p)).wallet_at("solana", SYNTHETIC_KEY)
    assert w.binding_source == "research:approved-record"
    assert w.approval_status == "RESEARCH_APPROVED"
    assert w.funding_source_evidence == "unverified:funder-reference"
    assert w.controller_evidence == "unverified:controller-reference"
    assert w.evidence_state == "CLAIMED_WITH_REFERENCE"
    assert not w.delivery_allowed and not w.signal_allowed and not w.trading_allowed


@pytest.mark.parametrize(("field", "value", "message"), [
    ("approval_status", "LIVE", "INVALID_BINDING_APPROVAL_STATUS"),
    ("source", [], "INVALID_BINDING_SOURCE"),
    ("funding_source_evidence", [], "INVALID_FUNDING_SOURCE_EVIDENCE"),
    ("controller_evidence", 1, "INVALID_CONTROLLER_EVIDENCE"),
])
def test_metadata_cannot_silently_claim_or_smuggle_authority(field, value, message):
    person = _person()
    person["wallets"][0][field] = value
    with pytest.raises(ValueError, match=message):
        PersonRegistry.from_mapping(_document(person))


def test_real_readers_agree_on_legacy_frank_identity_without_promoting_proof():
    live, live_wallets = load_live_registry(LOCAL)
    historical = MemeRegistry(json.loads(MEME.read_text()), namespace="LIVE")
    research = PersonRegistry.from_file(LOCAL)
    assert live["schema_version"] == research.schema_version == 1
    assert set(live_wallets) == {w.address for w in research.wallets_for("frank")}
    assert {(chain, address): pid
            for (chain, address), (pid, verified) in historical.wallets.items()
            if verified} == {("solana", address): pid for address, pid in live_wallets.items()}
    assert all(w.evidence_state == "REGISTERED_UNVERIFIED"
               for w in research.wallets_for("frank"))
    assert all(not w.delivery_allowed for w in research.wallets_for("frank"))
