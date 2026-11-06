"""Rolled-back instructions cannot prove transfers, funding or consolidation."""
from copy import deepcopy

import pytest

from mission_agent.meme import cluster
from mission_agent.meme.cluster import Holder, WalletClusterAnalyzer


def transaction():
    def transfer(source, destination, **amount):
        return {"parsed": {"type": "transfer", "info": {
            "source": source, "destination": destination, **amount,
        }}}

    balances = [
        {"accountIndex": index, "owner": owner, "mint": "Mint",
         "uiTokenAmount": {"amount": "100", "decimals": 0}}
        for index, owner in enumerate(("A", "B", "OUTSIDE"))
    ]
    return {
        "slot": 100, "blockTime": 100,
        "transaction": {"signatures": ["transfer"], "message": {
            "accountKeys": ["ta", "tb", "tc"],
            "instructions": [
                transfer("A", "B", lamports=5),
                transfer("FUNDER", "A", lamports=7),
                transfer("ta", "tb", amount="11"),
                transfer("ta", "tc", amount="13"),
            ],
        }},
        "meta": {"err": None, "preTokenBalances": balances,
                 "postTokenBalances": deepcopy(balances), "innerInstructions": []},
    }


class TransferRPC:
    endpoint = "fixture"
    calls = 0
    cache_hits = 0

    def __init__(self, tx):
        self.tx = tx

    def call(self, method, params, ttl=0):
        if method == "getSignaturesForAddress":
            return [{"signature": "transfer", "slot": 100, "blockTime": 100}]
        if method == "getTransaction":
            return self.tx
        raise AssertionError(method)


@pytest.mark.parametrize("success_state", ["failed", "missing_err", "missing_meta", "null_meta", "false_err"])
def test_unverified_success_cannot_create_transfer_relations_or_funding(monkeypatch, success_state):
    tx = transaction()
    if success_state == "failed":
        tx["meta"]["err"] = {"InstructionError": [3, {"Custom": 6001}]}
    elif success_state == "missing_err":
        del tx["meta"]["err"]
    elif success_state == "missing_meta":
        del tx["meta"]
    elif success_state == "null_meta":
        tx["meta"] = None
    else:
        tx["meta"]["err"] = False

    # Classification has its own failed-tx guard. Transfer evidence must be
    # protected independently, before the classifier runs.
    monkeypatch.setattr(cluster, "classify", lambda *args: {})
    a = WalletClusterAnalyzer("Mint", rpc=TransferRPC(tx), enumerate_holder_ranks=True)
    h = Holder("ta", "A", 100, 0, "ORDINARY", "fixture")
    assert a._scan_holder(h, {"ta": "A", "tb": "B"}, {"A", "B"}, 1) is None
    a._scan_funding(h, {"signature": "buy", "block_time": 110}, {"A", "B"}, 1)
    assert a.edges == []
    assert a.consolidations == []
    assert a.funding == []
    # Rejected economic evidence must not stall the source cursor or hide the
    # existing historical-account success diagnostic.
    assert all(w["next_before"] == "transfer" and w["signature_count"] == 1
               for w in a.history_coverage.values())
    assert a._historical_errors["TRANSACTION_SUCCESS_UNVERIFIED"] == 1


def test_successful_transfer_still_creates_relations_consolidation_and_funding(monkeypatch):
    monkeypatch.setattr(cluster, "classify", lambda *args: {})
    a = WalletClusterAnalyzer("Mint", rpc=TransferRPC(transaction()))
    h = Holder("ta", "A", 100, 0, "ORDINARY", "fixture")
    a._scan_holder(h, {"ta": "A", "tb": "B"}, {"A", "B"}, 1)
    a._scan_funding(h, {"signature": "buy", "block_time": 110}, {"A", "B"}, 1)
    assert {e["type"] for e in a.edges} == {"DIRECT_QUOTE_TRANSFER", "DIRECT_TOKEN_TRANSFER"}
    assert len(a.consolidations) == 1
    assert a.consolidations[0]["amount_raw"] == "13"
    assert len(a.funding) == 1
    assert a.funding[0]["lamports"] == "7"


@pytest.mark.parametrize("phase", ["holder", "funding"])
@pytest.mark.parametrize("conflict", ["slot", "primary_signature"])
@pytest.mark.parametrize("enumerate_history", [True, False])
def test_conflicting_transaction_context_cannot_create_economic_evidence(monkeypatch, phase, conflict, enumerate_history):
    tx = transaction()
    if conflict == "slot":
        tx["slot"] = 101
        code = "TRANSACTION_SLOT_CONFLICT"
    else:
        tx["transaction"]["signatures"] = ["another-transaction"]
        code = "TRANSACTION_IDENTITY_MISMATCH"
    classified = []
    def classify(signature, value, owner):
        classified.append(signature)
        return {"classification": "ACTIVE_TRADE", "trade": {
            "mint": "Mint", "direction": "BUY", "token_amount_raw": "11", "token_decimals": 0,
        }}
    monkeypatch.setattr(cluster, "classify", classify)
    a = WalletClusterAnalyzer("Mint", rpc=TransferRPC(tx), enumerate_holder_ranks=enumerate_history)
    h = Holder("ta", "A", 100, 0, "ORDINARY", "fixture")
    if phase == "holder":
        assert a._scan_holder(h, {"ta": "A", "tb": "B"}, {"A", "B"}, 1) is None
    else:
        a._scan_funding(h, {"signature": "buy", "block_time": 110}, {"A", "B"}, 1)
    assert classified == []
    assert a.trades == a.edges == a.consolidations == a.funding == []
    assert a._historical_errors[code] == int(enumerate_history)
    assert a.tx_errors == [{"signature": "transfer", "phase": phase + "_context", "error": code}]
    window = next(iter(a.history_coverage.values()))
    assert window["next_before"] == "transfer" and window["signature_count"] == 1
    assert window["stop_reason"] == "PAGE_LIMIT" and window["history_complete"] is False


@pytest.mark.parametrize("enumerate_history", [True, False])
def test_matching_context_keeps_economic_evidence_with_or_without_account_discovery(monkeypatch, enumerate_history):
    monkeypatch.setattr(cluster, "classify", lambda *args: {
        "classification": "ACTIVE_TRADE", "trade": {"mint": "Mint", "direction": "BUY"},
    })
    a = WalletClusterAnalyzer("Mint", rpc=TransferRPC(transaction()), enumerate_holder_ranks=enumerate_history)
    h = Holder("ta", "A", 100, 0, "ORDINARY", "fixture")
    first = a._scan_holder(h, {"ta": "A", "tb": "B"}, {"A", "B"}, 1)
    a._scan_funding(h, {"signature": "buy", "block_time": 110}, {"A", "B"}, 1)
    assert first["signature"] == "transfer"
    assert len(a.trades) == len(a.consolidations) == len(a.funding) == 1
    assert {edge["type"] for edge in a.edges} == {"DIRECT_QUOTE_TRANSFER", "DIRECT_TOKEN_TRANSFER"}
    assert a.tx_errors == []


def test_legacy_missing_context_remains_unverified_without_changing_existing_economics(monkeypatch):
    # Older synthetic/input adapters omit slot/signatures. This narrow repair
    # rejects contradictions; it does not convert absence into a verified match
    # or broaden the existing historical-account evidence acceptance contract.
    tx = transaction()
    del tx["slot"]
    del tx["transaction"]["signatures"]
    monkeypatch.setattr(cluster, "classify", lambda *args: {})
    a = WalletClusterAnalyzer("Mint", rpc=TransferRPC(tx), enumerate_holder_ranks=True)
    h = Holder("ta", "A", 100, 0, "ORDINARY", "fixture")
    a._scan_holder(h, {"ta": "A", "tb": "B"}, {"A", "B"}, 1)
    a._scan_funding(h, {"signature": "buy", "block_time": 110}, {"A", "B"}, 1)
    assert len(a.consolidations) == len(a.funding) == 1
    assert a.historical_accounts == []
    assert a._historical_errors["TRANSACTION_CONTEXT_UNAVAILABLE"] == 1
    assert a.tx_errors == []


@pytest.mark.parametrize("conflicting_slot", [False, True])
def test_classified_cache_rechecks_context_across_owner_accounts_without_new_rpc(monkeypatch, conflicting_slot):
    class RepeatedTransactionRPC(TransferRPC):
        transaction_reads = 0
        def call(self, method, params, ttl=0):
            if method == "getTransaction":
                self.transaction_reads += 1
            value = super().call(method, params, ttl)
            if method == "getSignaturesForAddress" and params[0] == "second" and conflicting_slot:
                value[0]["slot"] += 1
            return value

    classified = []
    def classify(signature, value, owner):
        classified.append(signature)
        return {"classification": "ACTIVE_TRADE", "trade": {"mint": "Mint", "direction": "BUY"}}
    monkeypatch.setattr(cluster, "classify", classify)
    rpc = RepeatedTransactionRPC(transaction())
    a = WalletClusterAnalyzer("Mint", rpc=rpc, enumerate_holder_ranks=True)
    first = a._scan_holder(Holder("ta", "A", 100, 0, "ORDINARY", "fixture"), {}, {"A", "B"}, 1)
    second = a._scan_holder(Holder("second", "A", 100, 0, "ORDINARY", "fixture"), {}, {"A", "B"}, 1)
    assert first["signature"] == "transfer"
    assert second is None if conflicting_slot else second == first
    assert rpc.transaction_reads == 1 and classified == ["transfer"]
    assert len(a.trades) == 1  # Preserve the first valid evidence, without duplication.
    assert a.tx_errors == ([{"signature": "transfer", "phase": "holder_context",
                             "error": "TRANSACTION_SLOT_CONFLICT"}] if conflicting_slot else [])
    second_window = list(a.history_coverage.values())[-1]
    assert second_window["next_before"] == "transfer" and second_window["signature_count"] == 1
