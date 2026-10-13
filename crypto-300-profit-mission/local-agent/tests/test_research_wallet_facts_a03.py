"""A03 evidence-backed research scoping and frozen-live non-interference tests."""
import json
from pathlib import Path

import pytest

from mission_agent.mission_control.person_registry import PersonRegistry
from mission_agent.mission_control.research_wallet_facts import PersonResearchReader


ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def key(value):
    value = int.from_bytes(bytes([value]) * 32, "big")
    digits = ""
    while value:
        value, idx = divmod(value, 58)
        digits = ALPHABET[idx] + digits
    return digits


A, B, C = key(2), key(3), key(4)
MINT, ACCOUNT = key(5), key(6)


def person(pid, *addresses, enabled=False, research=True):
    return {"person_id": pid, "display_name": pid,
            "enabled": enabled, "research_enabled": research,
            "wallets": [
                {"chain": "solana", "address": address,
                 "role": "PRIMARY", "valid_from_slot": 100}
                for address in addresses
            ]}


def registry(*people):
    return PersonRegistry.from_mapping({"schema_version": 2, "persons": list(people)})


def observation(wallet, raw, slot=130):
    return {"chain": "solana", "wallet": wallet, "mint": MINT,
            "slot": slot, "commitment": "finalized", "raw_amount": raw,
            "decimals": 6, "source": "ARCHIVED_FINALIZED_ACCOUNT_CAPTURE",
            "token_account": ACCOUNT}


class StubFacts:
    def __init__(self, facts=None):
        self.facts = facts or {}
        self.calls = []

    def observed_mint(self, *, chain, wallet, mint, as_of_slot):
        self.calls.append((chain, wallet, mint, as_of_slot))
        return self.facts.get((wallet, mint))


def test_two_people_same_mint_are_separate_research_scopes():
    source = StubFacts({(A, MINT): observation(A, "1000000"),
                        (B, MINT): observation(B, "9000000")})
    reader = PersonResearchReader(registry(person("frank", A, enabled=True),
                                           person("person_b", B)), source)
    first = reader.mint_observations(person_id="frank", mint=MINT, as_of_slot=140)
    second = reader.mint_observations(person_id="person_b", mint=MINT, as_of_slot=140)
    assert first["wallets"][0]["inventory"]["balance"]["quantity"] == "1"
    assert second["wallets"][0]["inventory"]["balance"]["quantity"] == "9"
    assert first["wallets"][0]["wallet"] != second["wallets"][0]["wallet"]
    assert first["person_balance"] is second["person_balance"] is None
    assert first["portfolio_verified"] is second["portfolio_verified"] is False
    assert [c[1] for c in source.calls] == [A, B]


def test_one_person_two_wallets_never_double_counts_as_verified_person_balance():
    source = StubFacts({(A, MINT): observation(A, "1000000"),
                        (B, MINT): observation(B, "2000000")})
    reader = PersonResearchReader(registry(person("frank", A, B, enabled=True)), source)
    result = reader.mint_observations(person_id="frank", mint=MINT, as_of_slot=140)
    assert result["queried_wallets"] == result["observed_wallets"] == 2
    assert sorted(x["inventory"]["balance"]["quantity"] for x in result["wallets"]) == ["1", "2"]
    assert result["person_balance"] is None
    assert result["person_pnl_usd"] is None
    assert all(not x["inventory"]["chain_complete"] for x in result["wallets"])


def test_missing_evidence_is_not_zero():
    reader = PersonResearchReader(registry(person("frank", A, enabled=True)), StubFacts())
    record = reader.mint_observations(person_id="frank", mint=MINT, as_of_slot=140)
    assert record["wallets"][0]["inventory"]["balance"] is None
    assert record["wallets"][0]["inventory"]["status"] == "NOT_CAPTURED"
    assert not record["wallets"][0]["inventory"]["current_balance_verified"]


def test_disabled_person_does_not_call_source():
    src = StubFacts({(B, MINT): observation(B, "1")})
    reader = PersonResearchReader(registry(person("frank", A, enabled=True),
                                           person("person_b", B, research=False)), src)
    with pytest.raises(KeyError, match="RESEARCH_PERSON_NOT_ENABLED"):
        reader.mint_observations(person_id="person_b", mint=MINT, as_of_slot=140)
    assert src.calls == []


def test_unregistered_person_not_accepted():
    src = StubFacts()
    reader = PersonResearchReader(registry(person("frank", A, enabled=True)), src)
    with pytest.raises(KeyError, match="RESEARCH_PERSON_NOT_ENABLED"):
        reader.mint_observations(person_id="spoofed", mint=MINT, as_of_slot=140)
    assert src.calls == []


@pytest.mark.parametrize("slot", [None, True, 10.5, -1])
def test_time_must_be_explicit_valid_slot(slot):
    reader = PersonResearchReader(registry(person("frank", A, enabled=True)), StubFacts())
    with pytest.raises(ValueError, match="INVALID_RESEARCH_AS_OF_SLOT"):
        reader.mint_observations(person_id="frank", mint=MINT, as_of_slot=slot)


def test_wallet_binding_not_backdated_into_before_approval_interval():
    src = StubFacts({(A, MINT): observation(A, "2")})
    reader = PersonResearchReader(registry(person("frank", A, enabled=True)), src)
    result = reader.mint_observations(person_id="frank", mint=MINT, as_of_slot=50)
    assert result["queried_wallets"] == 0
    assert result["status"] == "NO_BOUND_WALLETS_AT_SLOT"
    assert not src.calls


@pytest.mark.parametrize("change", [
    {"wallet": B}, {"chain": "ethereum"}, {"mint": A},
    {"commitment": "processed"}, {"slot": 90}, {"slot": 150},
    {"raw_amount": "-100"}, {"raw_amount": 10}, {"decimals": True},
    {"token_account": "1" * 33}, {"source": ""},
])
def test_wrong_owner_mint_interval_or_units_fail_closed(change):
    raw = observation(A, "20")
    raw.update(change)
    reader = PersonResearchReader(registry(person("frank", A, enabled=True)),
                                  StubFacts({(A, MINT): raw}))
    with pytest.raises(ValueError):
        reader.mint_observations(person_id="frank", mint=MINT, as_of_slot=140)


def test_person_research_list_contains_no_production_capabilities():
    reader = PersonResearchReader(registry(person("frank", A, enabled=True),
                                           person("person_b", B)), StubFacts())
    people = reader.people()
    assert {p["person_id"] for p in people} == {"frank", "person_b"}
    assert all(p["research_only"] and not p["signal_allowed"]
               and not p["delivery_allowed"] for p in people)


def test_legacy_production_registry_is_read_unchanged_and_no_live_access():
    path = Path(__file__).resolve().parents[1] / "config/frank_local_registry.json"
    original = path.read_text(encoding="utf-8")
    reader = PersonResearchReader(PersonRegistry.from_file(path), StubFacts())
    assert [p["person_id"] for p in reader.people()] == ["frank"]
    response = reader.mint_observations(person_id="frank", mint=MINT,
                                        as_of_slot=140)
    assert response["status"] == "PARTIAL_RESEARCH_EVIDENCE"
    assert response["person_pnl_usd"] is None
    assert response["signal_allowed"] is False
    assert response["delivery_allowed"] is False
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(original)
