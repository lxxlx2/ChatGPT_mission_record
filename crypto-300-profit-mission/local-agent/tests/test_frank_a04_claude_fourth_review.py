"""Claude review #4: native SOL fee-only and research source availability.

All owner-gap/fee-only tests are synthetic by design. Full real Solana RPC
receipts, when obtained, are separately preserved with explicit source proof.
"""
import hashlib
import json

from mission_agent.mission_control.wallet_economic_ledger import normalize_transaction
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_history_replay import (
    HistoryJournal, WalletHistoryCollector, _HISTORY_SCHEMA,
)
from test_frank_a04_a05_chain_capture import (
    OWNER_A, OWNER_B, MINT, ATA_A, balances,
)
from test_frank_a04_history_resume import receipt, signature


def fee_only_receipt(sig, slot):
    raw = receipt(sig, slot, OWNER_A)
    raw["transaction"]["message"]["accountKeys"] = [
        {"pubkey": OWNER_A}, {"pubkey": ATA_A},
    ]
    raw["meta"]["fee"] = 5000
    raw["meta"]["preBalances"] = [10000000, 2039280]
    raw["meta"]["postBalances"] = [9995000, 2039280]
    raw["meta"]["preTokenBalances"] = [balances(1, OWNER_A, MINT, "100")]
    raw["meta"]["postTokenBalances"] = [balances(1, OWNER_A, MINT, "80")]
    return raw


def test_fee_only_token_transfer_has_no_native_sol_flow_or_unknown_coverage(tmp_path):
    sig = signature(2401)
    tx = fee_only_receipt(sig, 900)
    view = normalize_transaction(tx, tracked_wallets={OWNER_A})
    assert view["native_sol_coverage_status"] == "NO_NATIVE_SOL_FLOW_OBSERVED"
    assert view["native_sol_observation_reason"] == "TRACKED_BALANCES_FEE_ONLY"
    assert view["fees_lamports"] == 5000
    assert len(view["token_legs"]) == 1
    assert view["token_legs"][0]["delta_raw"] == "-20"
    assert view["person_pnl_usd"] is None
    sidecar = WalletEvidenceStore(tmp_path / "research.sqlite")
    try:
        journal = HistoryJournal(sidecar)
        def rpc(method, params):
            if method == "getTransaction":
                return {"result": tx}
            if "before" in params[1]:
                return {"result": []}
            return {"result": [{"signature": sig, "slot": 900,
                                "confirmationStatus": "finalized"}]}
        summary = WalletHistoryCollector(journal, rpc, wallet=OWNER_A).collect(
            max_pages=2, tx_budget=4)
        assert summary["captured"] == 1
        assert summary["pending"] == 0
        assert summary["native_sol_unclassified_count"] == 0
        assert summary["native_sol_balance_evidence_missing_count"] == 0
        assert summary["coverage"] == "AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
        assert summary["history_complete"] is False
    finally:
        sidecar.close()


def test_real_non_fee_balance_delta_is_not_silently_called_fee_only():
    raw = fee_only_receipt(signature(2402), 901)
    raw["meta"]["postBalances"][0] -= 100000
    view = normalize_transaction(raw, tracked_wallets={OWNER_A})
    assert view["native_sol_coverage_status"] == "NATIVE_SOL_FLOW_UNCLASSIFIED"
    assert view["native_sol_observation_reason"] == "NON_FEE_NATIVE_BALANCE_CHANGE"
    assert view["native_sol_flow_lamports"] is None


def test_system_transfer_without_sol_delta_is_conservatively_unclassified():
    raw = fee_only_receipt(signature(2403), 902)
    raw["transaction"]["message"]["instructions"] = [{
        "programId": "11111111111111111111111111111111",
        "parsed": {"type": "transfer", "info": {
            "source": OWNER_A, "destination": OWNER_B, "lamports": 100,
        }},
    }]
    view = normalize_transaction(raw, tracked_wallets={OWNER_A})
    assert view["native_sol_coverage_status"] == "NATIVE_SOL_FLOW_UNCLASSIFIED"
    assert view["native_sol_observation_reason"] == "SYSTEM_VALUE_INSTRUCTION"


def test_missing_sol_balances_must_be_unknown_but_not_claim_native_flow():
    raw = receipt(signature(2404), 903, OWNER_A)
    view = normalize_transaction(raw, tracked_wallets={OWNER_A})
    assert view["native_sol_coverage_status"] == "NATIVE_SOL_BALANCE_EVIDENCE_MISSING"
    assert view["native_sol_observation_reason"] == "BALANCE_DATA_MISSING"
    assert view["native_sol_flow_lamports"] is None


def test_N1_owner_gap_opt_in_archives_raw_and_continues_older_pages(tmp_path):
    recent, blocked, older = [signature(2410+i) for i in range(3)]
    good0 = fee_only_receipt(recent, 1002)
    bad = fee_only_receipt(blocked, 1001)
    # An unrelated third-party token account with missing owner and an
    # unverified nonzero delta. It must NOT be attributed to OWNER_A.
    bad["transaction"]["message"]["accountKeys"].append({"pubkey": OWNER_B})
    bad["meta"]["preBalances"].append(100000)
    bad["meta"]["postBalances"].append(100000)
    bad["meta"]["preTokenBalances"].append(balances(2, OWNER_B, MINT, "0"))
    bad["meta"]["postTokenBalances"].append(balances(2, OWNER_B, MINT, "100"))
    del bad["meta"]["preTokenBalances"][-1]["owner"]
    del bad["meta"]["postTokenBalances"][-1]["owner"]
    good2 = fee_only_receipt(older, 1000)
    txs = {recent: good0, blocked: bad, older: good2}
    ordered = [(recent, 1002), (blocked, 1001), (older, 1000)]

    def source(method, params):
        if method == "getTransaction":
            return {"result": txs[params[0]]}
        before = params[1].get("before")
        pos = next((i+1 for i, (sig, _) in enumerate(ordered)
                    if sig == before), 0) if before else 0
        return {"result": [
            {"signature": sig, "slot": slot, "confirmationStatus": "finalized"}
            for sig, slot in ordered[pos:pos+params[1]["limit"]]
        ]}

    sidecar = WalletEvidenceStore(tmp_path / "research.sqlite")
    try:
        journal = HistoryJournal(sidecar)
        default = WalletHistoryCollector(
            journal, source, wallet=OWNER_A, page_size=2,
        ).collect(max_pages=4, tx_budget=10)
        assert default["captured"] == 1 and default["pending"] == 1
        assert default["missing_detail_counts"]["TOKEN_OWNER_UNRESOLVED_DELTA"] == 1
        assert default["pagination_end_observed"] is False
        # Explicit recovery path never invents a v2 economic leg, yet
        # permits older signatures to be enumerated normally.
        allowed = WalletHistoryCollector(
            journal, source, wallet=OWNER_A, page_size=2,
            continue_on_owner_gaps=True,
        ).collect(max_pages=4, tx_budget=10)
        assert allowed["captured"] == 3 and allowed["pending"] == 0
        assert allowed["pagination_end_observed"]
        assert allowed["source_pagination_coverage"] == "AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
        assert allowed["coverage"] == "PARTIAL_ECONOMIC_EVIDENCE"
        assert allowed["v2_blocked_count"] == 1
        assert allowed["v2_missing_count"] == 1
        assert allowed["missing_detail_counts"]["TOKEN_OWNER_UNRESOLVED_DELTA"] == 1
        assert allowed["unresolved_owner_continuation_opt_in"] is True
        assert sidecar.count("RAW_TX") == 3
        assert sidecar.count("WALLET_TX_VIEW_V2") == 2
        assert sidecar.count("WALLET_TX_VIEW") == 0
        # A retry/rebuild preserves the untrusted economic gap explicitly.
        repair = journal.rebuild_versioned_views(OWNER_A)
        assert repair["blocked"] == 1
        assert journal.state(OWNER_A)["coverage"] == "PARTIAL_ECONOMIC_EVIDENCE"
    finally:
        sidecar.close()


def test_old_sidecar_is_migrated_without_rewriting_raw_v1_or_cursor(tmp_path):
    path = tmp_path / "legacy.sqlite"
    sidecar = WalletEvidenceStore(path)
    sig = signature(2500)
    old_raw = receipt(sig, 999, OWNER_A)
    payload = json.dumps(old_raw, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False)
    archive = '{"schema_version":1,"discredited_outflow":"-100"}'
    try:
        sidecar.db.executescript(_HISTORY_SCHEMA)
        assert "v2_error_code" not in {
            row["name"] for row in sidecar.db.execute(
                "PRAGMA table_info(wallet_history_signature)")
        }
        with sidecar.db:
            sidecar.db.execute(
                "INSERT INTO wallet_history_cursor(wallet,next_before,"
                "pagination_end_observed,page_count,last_error_code) "
                "VALUES(?,?,?,?,NULL)", (OWNER_A, sig, 1, 2),
            )
            sidecar.db.execute(
                "INSERT INTO wallet_history_signature(wallet,signature,slot,state) "
                "VALUES(?,?,?,'CAPTURED')", (OWNER_A, sig, 999),
            )
            for kind, identity, text in (
                ("RAW_TX", sig + ":999", payload),
                ("WALLET_TX_VIEW", OWNER_A + ":" + sig + ":999", archive),
            ):
                sidecar.db.execute(
                    "INSERT INTO evidence_documents(kind,identity,source_sha256,"
                    "payload_json) VALUES(?,?,?,?)",
                    (kind, identity, hashlib.sha256(text.encode()).hexdigest(), text),
                )
    finally:
        sidecar.close()
    upgraded = WalletEvidenceStore(path)
    try:
        journal = HistoryJournal(upgraded)
        assert "v2_error_code" in {
            row["name"] for row in upgraded.db.execute(
                "PRAGMA table_info(wallet_history_signature)")
        }
        saved = upgraded.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='RAW_TX'"
        ).fetchone()[0]
        assert saved == payload
        saved_v1 = upgraded.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='WALLET_TX_VIEW'"
        ).fetchone()[0]
        assert saved_v1 == archive
        state = journal.state(OWNER_A)
        assert state["page_count"] == 2
        assert state["captured"] == 1
        assert state["v2_missing_count"] == 1
        assert state["coverage"] == "PARTIAL_ECONOMIC_EVIDENCE"
        assert journal.state(OWNER_A) == state
    finally:
        upgraded.close()
