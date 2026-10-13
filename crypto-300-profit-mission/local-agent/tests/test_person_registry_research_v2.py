"""First A02 acceptance gates: registry identity ≠ wallet ownership ≠ live authority.

All tests are offline/readonly, deliberately do not import the frozen signal
engine, create delivery state, or access users' production wallets.
"""
from __future__ import annotations

from pathlib import Path
import json

import pytest

from mission_agent.mission_control.person_registry import PersonRegistry


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "config/frank_local_registry.json"
FRANK = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
WALLET_B = "BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp"
WALLET_C = "So11111111111111111111111111111111111111112"


def _person(pid, *wallets, research=True, enabled=False):
    return {
        "person_id": pid, "display_name": pid.upper(),
        "research_enabled": research, "enabled": enabled,
        "wallets": [
            {"chain": "solana", "address": address,
             "role": "PRIMARY" if i == 0 else "SECONDARY"}
            for i, address in enumerate(wallets)
        ],
    }


def _v2(*persons):
    return {"schema_version": 2, "persons": list(persons)}


def test_legacy_existing_frank_file_is_compatible_without_owning_wallet_proof():
    raw = json.loads(LEGACY.read_text())
    registry = PersonRegistry.from_file(LEGACY)
    assert raw["schema_version"] == registry.schema_version == 1
    assert len(registry.research_people()) == 1
    person = registry.person("frank")
    assert person.display_name == "Frank"
    assert registry.wallet_at("solana", FRANK).person_id == "frank"
    assert person.wallets[0].evidence_state == "REGISTERED_UNVERIFIED"
    assert person.signal_allowed is False
    assert person.delivery_allowed is False
    assert person.wallets[0].trading_allowed is False
    assert raw == json.loads(LEGACY.read_text())


def test_two_wallets_one_person_are_research_only_and_not_distinct_persons():
    p = _person("frank", FRANK, WALLET_B, enabled=True)
    reg = PersonRegistry.from_mapping(_v2(p))
    assert [w.address for w in reg.wallets_for("frank")] == [FRANK, WALLET_B]
    assert len(reg.research_people()) == 1
    assert len({w.wallet_id for w in reg.wallets_for("frank")}) == 2
    assert all(not w.delivery_allowed and not w.signal_allowed
               and not w.trading_allowed for w in reg.wallets_for("frank"))


def test_two_people_same_token_still_have_separate_wallet_scopes():
    p = _person("frank", FRANK, enabled=True)
    q = _person("person_b", WALLET_B)
    reg = PersonRegistry.from_mapping(_v2(p, q))
    assert reg.wallet_at("solana", FRANK).person_id == "frank"
    assert reg.wallet_at("solana", WALLET_B).person_id == "person_b"
    assert len(reg.wallets_for("person_b")) == 1
    assert not reg.person("person_b").signal_allowed


def test_unapproved_research_person_cannot_be_selected():
    reg = PersonRegistry.from_mapping(_v2(
        _person("frank", FRANK, enabled=True),
        _person("person_b", WALLET_B, research=False),
    ))
    with pytest.raises(KeyError, match="RESEARCH_PERSON_NOT_ENABLED"):
        reg.person("person_b")
    with pytest.raises(KeyError, match="RESEARCH_PERSON_NOT_ENABLED"):
        reg.wallet_at("solana", WALLET_B)


@pytest.mark.parametrize("capabilities", [
    {"signal_evaluation": True},
    {"delivery": True},
    {"trading": True},
])
def test_registry_cannot_grant_production_authority(capabilities):
    p = _person("person_b", WALLET_B)
    p["permissions"] = capabilities
    with pytest.raises(ValueError, match="RESEARCH_REGISTRY_CANNOT_AUTHORIZE"):
        PersonRegistry.from_mapping(_v2(p))


def test_new_person_legacy_enabled_must_fail_even_without_signal_flag():
    p = _person("person_b", WALLET_B, enabled=True)
    with pytest.raises(ValueError, match="NEW_PERSON_CANNOT_ENABLE_LEGACY_SIGNAL"):
        PersonRegistry.from_mapping(_v2(p))


def test_wallet_cannot_grant_delivery_or_trade():
    p = _person("frank", FRANK, enabled=True)
    p["wallets"][0]["permissions"] = {"delivery": True}
    with pytest.raises(ValueError, match="WALLET_CANNOT_AUTHORIZE"):
        PersonRegistry.from_mapping(_v2(p))


def test_duplicate_person_or_overlapping_wallet_assignments_are_rejected():
    p = _person("frank", FRANK, enabled=True)
    with pytest.raises(ValueError, match="DUPLICATE_PERSON_ID"):
        PersonRegistry.from_mapping(_v2(p, p))
    with pytest.raises(ValueError, match="WALLET_BINDING_OVERLAP"):
        PersonRegistry.from_mapping(_v2(
            p, _person("person_b", FRANK)))


def test_nonoverlapping_historical_reassignment_reconciles_by_slot():
    a = _person("frank", FRANK, enabled=True)
    b = _person("person_b", FRANK)
    a["wallets"][0].update(valid_from_slot=1, valid_to_slot=100)
    b["wallets"][0].update(valid_from_slot=100)
    reg = PersonRegistry.from_mapping(_v2(a, b))
    assert reg.wallet_at("solana", FRANK, slot=99).person_id == "frank"
    assert reg.wallet_at("solana", FRANK, slot=100).person_id == "person_b"
    assert reg.wallet_at("solana", FRANK).person_id == "person_b"
    assert reg.wallets_for("frank", slot=100) == ()
    assert len(reg.wallets_for("person_b", slot=100)) == 1
    with pytest.raises(KeyError, match="RESEARCH_WALLET_NOT_BOUND"):
        reg.wallet_at("solana", FRANK, slot=0)


def test_invalid_interval_and_unsupported_chain_fail_closed():
    a = _person("frank", FRANK)
    a["wallets"][0].update(valid_from_slot=100, valid_to_slot=100)
    with pytest.raises(ValueError, match="INVALID_WALLET_INTERVAL"):
        PersonRegistry.from_mapping(_v2(a))
    a["wallets"][0].update(valid_from_slot=1, valid_to_slot=None, chain="evm")
    with pytest.raises(ValueError, match="UNSUPPORTED_OR_INVALID_WALLET"):
        PersonRegistry.from_mapping(_v2(a))


def test_registry_from_mapping_does_not_mutate_input():
    doc = _v2(_person("frank", FRANK, enabled=True),
              _person("person_b", WALLET_C))
    before = json.dumps(doc, sort_keys=True)
    registry = PersonRegistry.from_mapping(doc)
    assert json.dumps(doc, sort_keys=True) == before
    assert len(registry.research_people()) == 2
