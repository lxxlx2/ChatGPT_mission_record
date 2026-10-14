"""Claude A04 E1/E2 and immutable-view repair adversarial cases.

These tests use synthetic owner-missing records as fault injection. They are
not assertions that real Frank transactions have these exact gaps.
"""
import json

import pytest

from mission_agent.mission_control.wallet_economic_ledger import (
    LedgerEvidenceError, normalize_transaction,
)
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_history_replay import (
    HistoryJournal, SourceEvidenceError, WalletHistoryCollector,
)
from test_frank_a04_a05_chain_capture import (
    OWNER_A, OWNER_B, MINT, ATA_A, ATA_B, balances, tx,
)
from test_frank_a04_history_resume import receipt, signature


def test_E1a_post_missing_owner_does_not_create_false_outflow():
    raw = tx([balances(0, OWNER_A, MINT, "100")],
             [balances(0, OWNER_A, MINT, "100")])
    del raw["meta"]["postTokenBalances"][0]["owner"]
    result = normalize_transaction(raw, tracked_wallets={OWNER_A})
    assert result["token_legs"] == []
    assert "TOKEN_OWNER_UNRESOLVED" in result["coverage_gaps"]
    assert not result["token_owner_coverage_complete"]
    assert result["realized_pnl_usd"] is None if "realized_pnl_usd" in result else result["person_pnl_usd"] is None


def test_E1b_pre_missing_owner_does_not_create_false_inflow():
    raw = tx([balances(0, OWNER_A, MINT, "100")],
             [balances(0, OWNER_A, MINT, "100")])
    del raw["meta"]["preTokenBalances"][0]["owner"]
    result = normalize_transaction(raw, tracked_wallets={OWNER_A})
    assert result["token_legs"] == []
    assert "TOKEN_OWNER_UNRESOLVED" in result["coverage_gaps"]


def test_E1c_both_owners_unknown_are_not_silently_filled():
    raw = tx([balances(0, OWNER_A, MINT, "100")],
             [balances(0, OWNER_A, MINT, "200")])
    raw["meta"]["postTokenBalances"][0]["uiTokenAmount"]["amount"] = "100"
    del raw["meta"]["preTokenBalances"][0]["owner"]
    del raw["meta"]["postTokenBalances"][0]["owner"]
    result = normalize_transaction(raw, tracked_wallets={OWNER_A})
    assert result["token_legs"] == []
    assert result["coverage_gaps"] == ["TOKEN_OWNER_UNRESOLVED"]
    assert result["person_pnl_usd"] is None


@pytest.mark.parametrize("pre_missing", [False, True])
def test_changed_quantity_with_one_missing_owner_blocks_immutable_capture(pre_missing):
    raw = tx([balances(0, OWNER_A, MINT, "100")],
             [balances(0, OWNER_A, MINT, "200")])
    del raw["meta"]["preTokenBalances" if pre_missing else "postTokenBalances"][0]["owner"]
    with pytest.raises(LedgerEvidenceError, match="TOKEN_OWNER_UNRESOLVED_DELTA"):
        normalize_transaction(raw, tracked_wallets={OWNER_A})


def test_unobserved_native_sol_flow_is_explicit_never_zero():
    raw = tx([], [])
    raw["transaction"]["message"]["accountKeys"].append({"pubkey": OWNER_A})
    raw["transaction"]["message"]["instructions"] = []
    raw["meta"]["preBalances"] = [1000000, 0, 900000]
    raw["meta"]["postBalances"] = [1000000, 0, 500000]
    result = normalize_transaction(raw, tracked_wallets={OWNER_A})
    assert result["token_legs"] == []
    assert result["native_sol_coverage_status"] == "NATIVE_SOL_FLOW_UNCLASSIFIED"
    assert result["native_sol_flow_lamports"] is None
    assert result["person_pnl_usd"] is None
    assert result["normalizer_version"] == "SOL_TOKEN_VIEW_V2"


def test_wallet_view_cannot_claim_wrong_research_owner_and_old_raw_remains(tmp_path):
    store = WalletEvidenceStore(tmp_path / "research-sidecar.sqlite")
    try:
        journal = HistoryJournal(store)
        sig = signature(800)
        raw = receipt(sig, 900, OWNER_A, other=OWNER_B)
        journal.record_page(OWNER_A, None, [
            {"signature": sig, "slot": 900, "confirmationStatus": "finalized"}
        ])
        from mission_agent.mission_control.wallet_history_replay import _wallet_projection
        view = _wallet_projection(raw, OWNER_B)
        with pytest.raises(SourceEvidenceError, match="WALLET_VIEW_OWNER_MISMATCH"):
            journal.record_transaction(OWNER_A, sig, raw, view)
        assert journal.state(OWNER_A)["pending"] == 1
        assert store.count("RAW_TX") == 0
    finally:
        store.close()


def test_versioned_rebuild_keeps_original_immutable_evidence_and_is_repeatable(tmp_path):
    store = WalletEvidenceStore(tmp_path / "research-sidecar.sqlite")
    sig = signature(801)
    raw = receipt(sig, 901, OWNER_A)
    try:
        journal = HistoryJournal(store)
        journal.record_page(OWNER_A, None, [
            {"signature": sig, "slot": 901, "confirmationStatus": "finalized"}
        ])
        class FakeRPC:
            def __call__(self, method, args):
                if method == "getTransaction":
                    return {"result": raw}
                return {"result": []}
        result = WalletHistoryCollector(journal, FakeRPC(), wallet=OWNER_A).collect(
            max_pages=0, tx_budget=1)
        assert result["captured"] == 1
        # Existing newly captured V2 is already verified. Insert a separate
        # historical V1 artifact; an explicit V2 rebuild must not mutate it.
        legacy = '{"schema_version":1,"old_economic_attribution":"UNVERIFIED"}'
        with store.db:
            store.db.execute(
                "INSERT INTO evidence_documents(kind,identity,source_sha256,payload_json)"
                "VALUES('WALLET_TX_VIEW',?,?,?)",
                (OWNER_A + ":" + sig + ":901", "legacy-archive", legacy),
            )
        original = store.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='WALLET_TX_VIEW'"
        ).fetchone()[0]
        raw_original = store.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='RAW_TX'"
        ).fetchone()[0]
        rebuilt = journal.rebuild_versioned_views(OWNER_A)
        assert rebuilt["new"] == 0 and rebuilt["already_present"] == 1
        assert rebuilt["blocked"] == 0
        repeated = journal.rebuild_versioned_views(OWNER_A)
        assert repeated["new"] == 0 and repeated["already_present"] == 1
        assert store.count("WALLET_TX_VIEW_V2") == 1
        modern = json.loads(store.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='WALLET_TX_VIEW_V2'"
        ).fetchone()[0])
        assert modern["normalizer_version"] == "SOL_TOKEN_VIEW_V2"
        assert modern["instruction_evidence"]["transfer_count"] == 0
        assert store.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='WALLET_TX_VIEW'"
        ).fetchone()[0] == original
        assert store.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='RAW_TX'"
        ).fetchone()[0] == raw_original
    finally:
        store.close()


def test_historical_collector_captures_parsed_instruction_evidence(tmp_path):
    from mission_agent.mission_control.wallet_history_replay import _wallet_projection
    from mission_agent.mission_control.wallet_chain_capture import SPL_TOKEN_PROGRAM
    raw = receipt(signature(803), 903, OWNER_A, other=OWNER_B)
    raw["transaction"]["message"]["accountKeys"] = [
        {"pubkey": ATA_A}, {"pubkey": ATA_B}
    ]
    raw["meta"]["preTokenBalances"] = [
        balances(0, OWNER_A, MINT, "90"),
        balances(1, OWNER_B, MINT, "0"),
    ]
    raw["meta"]["postTokenBalances"] = [
        balances(0, OWNER_A, MINT, "0"),
        balances(1, OWNER_B, MINT, "90"),
    ]
    raw["transaction"]["message"]["instructions"] = [
        {"programId": SPL_TOKEN_PROGRAM, "parsed": {"type": "transfer", "info": {
            "source": ATA_A, "destination": ATA_B, "amount": "90",
        }}},
    ]
    owner_a = _wallet_projection(raw, OWNER_A)
    owner_b = _wallet_projection(raw, OWNER_B)
    for view in (owner_a, owner_b):
        assert view["instruction_evidence"]["transfer_count"] == 1
        assert view["instruction_evidence"]["active_market_trades_verified"] is False
        assert view["active_market_buys_confirmed"] == 0
        assert view["person_pnl_usd"] is None
    assert owner_a["instruction_evidence"]["transfers"][0]["classification"] == "ONE_TRACKED_ENDPOINT_TRANSFER"
