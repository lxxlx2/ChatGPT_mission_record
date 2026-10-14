"""Claude exact-head P2/P4/P5/P6/P7 stop-the-line regressions.

This test set deliberately creates *synthetic*, adversarial Solana receipts;
it must not be presented as real Frank wallet source history.
"""
import json

import pytest

from mission_agent.mission_control.wallet_economic_ledger import (
    LedgerEvidenceError, normalize_transaction,
)
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_history_replay import (
    HistoryJournal, WalletHistoryCollector,
)
from mission_agent.mission_control.wallet_instruction_evidence import transfer_instructions
from mission_agent.mission_control.wallet_chain_capture import SPL_TOKEN_PROGRAM
from test_frank_a04_a05_chain_capture import (
    OWNER_A, OWNER_B, MINT, ATA_A, ATA_B, balances,
)
from test_frank_a04_history_resume import receipt, signature


def data(sig, slot=1000, *, tracked=OWNER_A, post_raw="100", unknown=False):
    result = receipt(sig, slot, tracked)
    result["transaction"]["message"]["accountKeys"] = [{"pubkey": ATA_A}]
    result["meta"]["preTokenBalances"] = [balances(0, tracked, MINT, "0")]
    result["meta"]["postTokenBalances"] = [balances(0, tracked, MINT, post_raw)]
    if unknown:
        del result["meta"]["preTokenBalances"][0]["owner"]
        del result["meta"]["postTokenBalances"][0]["owner"]
    return result


def source(wallet, sig, raw):
    calls = []
    def rpc(method, params):
        calls.append(method)
        if method == "getSignaturesForAddress":
            if "before" in params[1]:
                return {"result": []}
            return {"result": [{"signature": sig, "slot": raw["slot"],
                                "confirmationStatus": "finalized"}]}
        assert method == "getTransaction"
        return {"result": raw}
    return rpc, calls


def test_P2_unknown_owner_nonzero_never_closes_gap_or_marks_capture(tmp_path):
    sig = signature(1701)
    raw = data(sig, unknown=True)
    with pytest.raises(LedgerEvidenceError, match="TOKEN_OWNER_UNRESOLVED_DELTA"):
        normalize_transaction(raw, tracked_wallets={OWNER_A})
    store = WalletEvidenceStore(tmp_path / "history.sqlite")
    try:
        journal = HistoryJournal(store)
        rpc, _ = source(OWNER_A, sig, raw)
        observed = WalletHistoryCollector(journal, rpc, wallet=OWNER_A).collect(
            max_pages=2, tx_budget=5)
        assert observed["pending"] == 1
        assert observed["captured"] == 0
        assert observed["status"] == "SOURCE_LIMITED"
        assert observed["missing_detail_counts"]["TOKEN_OWNER_UNRESOLVED_DELTA"] == 1
        assert store.count("RAW_TX") == 0
        assert store.count("WALLET_TX_VIEW_V2") == 0
        assert observed["history_complete"] is False
    finally:
        store.close()


def test_P6_old_v1_repair_block_persists_and_state_is_not_available(tmp_path):
    sig = signature(1702)
    raw = data(sig, unknown=True)
    store = WalletEvidenceStore(tmp_path / "history.sqlite")
    try:
        journal = HistoryJournal(store)
        journal.record_page(OWNER_A, None, [
            {"signature": sig, "slot": 1000, "confirmationStatus": "finalized"}
        ])
        journal.record_page(OWNER_A, sig, [])
        old_identity = OWNER_A + ":" + sig + ":1000"
        raw_identity = sig + ":1000"
        with store.db:
            for kind, identity, value in (
                ("RAW_TX", raw_identity, raw),
                ("WALLET_TX_VIEW", old_identity, {"schema_version": 1,
                                                 "false_outflow": "-100"}),
            ):
                import hashlib
                payload = json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"))
                checksum = hashlib.sha256(payload.encode()).hexdigest()
                store.db.execute(
                    "INSERT INTO evidence_documents(kind,identity,source_sha256,payload_json)"
                    " VALUES(?,?,?,?)", (kind, identity, checksum, payload),
                )
            store.db.execute(
                "UPDATE wallet_history_signature SET state='CAPTURED' "
                "WHERE wallet=? AND signature=?", (OWNER_A, sig),
            )
        before = store.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='WALLET_TX_VIEW'"
        ).fetchone()[0]
        assert journal.state(OWNER_A)["v2_missing_count"] == 1
        repair = journal.rebuild_versioned_views(OWNER_A)
        assert repair["blocked"] == 1
        state = journal.state(OWNER_A)
        assert state["captured"] == 1 and state["pending"] == 0
        assert state["v2_blocked_count"] == 1
        assert state["v2_missing_count"] == 1
        assert state["coverage"] == "PARTIAL_ECONOMIC_EVIDENCE"
        assert state["missing_detail_counts"]["V2_REBUILD_BLOCKED"] == 1
        assert journal.rebuild_versioned_views(OWNER_A)["blocked"] == 1
        assert store.count("WALLET_TX_VIEW_V2") == 0
        assert store.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='WALLET_TX_VIEW'"
        ).fetchone()[0] == before
    finally:
        store.close()


def test_P4_failed_transaction_parsed_transfer_is_not_executed():
    sig = signature(1703)
    raw = receipt(sig, 1000, OWNER_A, other=OWNER_B)
    raw["meta"]["err"] = {"InstructionError": [0, "Custom"]}
    raw["transaction"]["message"]["accountKeys"] = [
        {"pubkey": ATA_A}, {"pubkey": ATA_B},
    ]
    raw["meta"]["preTokenBalances"] = [
        balances(0, OWNER_A, MINT, "10"), balances(1, OWNER_B, MINT, "0")
    ]
    raw["meta"]["postTokenBalances"] = [
        balances(0, OWNER_A, MINT, "10"), balances(1, OWNER_B, MINT, "0")
    ]
    raw["transaction"]["message"]["instructions"] = [{
        "programId": SPL_TOKEN_PROGRAM,
        "parsed": {"type": "transfer", "info": {
            "source": ATA_A, "destination": ATA_B, "amount": "10",
        }},
    }]
    view = normalize_transaction(raw, tracked_wallets={OWNER_A, OWNER_B})
    out = transfer_instructions(raw, view)
    assert out["transfer_count"] == 1
    assert out["executed_transfer_count"] == 0
    assert out["transaction_executed"] is False
    assert out["transfers"][0]["executed"] is False
    assert out["transfers"][0]["source_status"] == "FAILED_TRANSACTION_INSTRUCTION_NOT_EXECUTED"
    assert out["transfers"][0]["classification"] == "FAILED_TRANSACTION_INSTRUCTION_NOT_EXECUTED"
    assert out["active_market_trades_verified"] is False
    assert out["person_pnl_usd"] is None


def test_P5_native_sol_unclassified_is_visible_in_wallet_state_and_status(tmp_path):
    sig = signature(1704)
    raw = receipt(sig, 1000, OWNER_A)
    raw["meta"]["preBalances"] = [40000000]
    raw["meta"]["postBalances"] = [10000000]
    store = WalletEvidenceStore(tmp_path / "history.sqlite")
    try:
        journal = HistoryJournal(store)
        rpc, _ = source(OWNER_A, sig, raw)
        result = WalletHistoryCollector(journal, rpc, wallet=OWNER_A).collect(
            max_pages=2, tx_budget=5)
        assert result["captured"] == 1
        assert result["pending"] == 0
        assert result["pagination_end_observed"]
        assert result["source_pagination_coverage"] == "AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
        assert result["native_sol_unclassified_count"] == 1
        assert result["coverage"] == "PARTIAL_ECONOMIC_EVIDENCE"
        assert result["status"] == "PARTIAL_ECONOMIC_EVIDENCE"
        assert store.count("WALLET_TX_VIEW_V2") == 1
    finally:
        store.close()


def test_P7_old_and_new_wallet_views_are_isolated_by_evidence_kind(tmp_path):
    sig = signature(1705)
    raw = receipt(sig, 1000, OWNER_A)
    store = WalletEvidenceStore(tmp_path / "history.sqlite")
    try:
        journal = HistoryJournal(store)
        journal.record_page(OWNER_A, None, [
            {"signature": sig, "slot": 1000, "confirmationStatus": "finalized"}
        ])
        rpc, _ = source(OWNER_A, sig, raw)
        current = WalletHistoryCollector(journal, rpc, wallet=OWNER_A).collect(
            max_pages=0, tx_budget=1)
        assert current["captured"] == 1
        assert store.count("WALLET_TX_VIEW") == 0
        assert store.count("WALLET_TX_VIEW_V2") == 1
        first = store.db.execute(
            "SELECT payload_json FROM evidence_documents "
            "WHERE kind='WALLET_TX_VIEW_V2'"
        ).fetchone()[0]
        with store.db:
            store.db.execute(
                "INSERT INTO evidence_documents(kind,identity,source_sha256,payload_json)"
                " VALUES(?,?,?,?)",
                ("WALLET_TX_VIEW", "old-record", "legacy", '{"schema_version":1}'),
            )
        assert store.count("WALLET_TX_VIEW") == 1
        assert store.count("WALLET_TX_VIEW_V2") == 1
        assert store.db.execute(
            "SELECT payload_json FROM evidence_documents "
            "WHERE kind='WALLET_TX_VIEW_V2'"
        ).fetchone()[0] == first
        assert journal.rebuild_versioned_views(OWNER_A)["already_present"] == 1
    finally:
        store.close()
