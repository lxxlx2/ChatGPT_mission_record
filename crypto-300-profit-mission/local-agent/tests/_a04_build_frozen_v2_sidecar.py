"""CI-only producer: run with exact immutable PR #52 source via PYTHONPATH.

Writes a genuine pre-V3 research Sidecar using OLD native-flow normalization.
This script is executed from the separate parent worktree, never production.
"""
import json
import os
from pathlib import Path

from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_history_replay import (
    HistoryJournal, _wallet_projection,
)
from test_frank_a04_history_resume import receipt, signature
from test_frank_a04_a05_chain_capture import OWNER_A, ATA_A, MINT, balances
import mission_agent.mission_control.wallet_economic_ledger as economic_ledger

path = Path(os.environ["FRANK_A04_TEST_OLD_V2_SIDECAR"])
sig = signature(6501)
raw = receipt(sig, 6500, OWNER_A)
raw["transaction"]["message"]["accountKeys"] = [
    {"pubkey": OWNER_A}, {"pubkey": ATA_A},
]
raw["transaction"]["message"]["instructions"] = []
raw["meta"]["fee"] = 5000
raw["meta"]["preBalances"] = [10000000, 2039280]
raw["meta"]["postBalances"] = [9995000, 2039280]
raw["meta"]["preTokenBalances"] = [balances(1, OWNER_A, MINT, "100")]
raw["meta"]["postTokenBalances"] = [balances(1, OWNER_A, MINT, "80")]
assert "frank-v2-parent-" in str(economic_ledger.__file__), (
    "TEST_IS_NOT_USING_PARENT_SHA_MODULE:" + str(economic_ledger.__file__))
print("PARENT_NORMALIZER_MODULE=" + str(economic_ledger.__file__))
sidecar = WalletEvidenceStore(path)
try:
    journal = HistoryJournal(sidecar)
    journal.record_page(OWNER_A, None, [
        {"signature": sig, "slot": 6500, "confirmationStatus": "finalized"},
    ])
    journal.record_transaction(OWNER_A, sig, raw, _wallet_projection(raw, OWNER_A))
    journal.record_page(OWNER_A, sig, [])
    assert sidecar.count("RAW_TX") == 1
    assert sidecar.count("WALLET_TX_VIEW_V2") == 1
    original = sidecar.db.execute(
        "SELECT source_sha256,payload_json FROM evidence_documents "
        "WHERE kind='WALLET_TX_VIEW_V2'"
    ).fetchone()
    original_doc = json.loads(original["payload_json"])
    assert original_doc["normalizer_version"] == "SOL_TOKEN_VIEW_V2"
    assert original_doc["native_sol_coverage_status"] == (
        os.environ["FRANK_A04_TEST_EXPECTED_OLD_NATIVE_STATUS"])
    manifest = {
        "wallet": OWNER_A, "signature": sig, "slot": 6500,
        "v2_hash": original["source_sha256"],
        "v2_payload": original["payload_json"],
        "source_raw": sidecar.db.execute(
            "SELECT payload_json FROM evidence_documents WHERE kind='RAW_TX'"
        ).fetchone()["payload_json"],
        "cursor": dict(sidecar.db.execute(
            "SELECT * FROM wallet_history_cursor WHERE wallet=?",
            (OWNER_A,),
        ).fetchone()),
        "origin_normalizer_version": original_doc["normalizer_version"],
        "origin_native_sol_status": original_doc["native_sol_coverage_status"],
    }
    path.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8")
finally:
    sidecar.close()
print("FROZEN_PR52_V2_SIDECAR_BUILT", path)
