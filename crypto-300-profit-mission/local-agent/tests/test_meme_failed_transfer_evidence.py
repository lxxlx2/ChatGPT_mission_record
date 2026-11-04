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
