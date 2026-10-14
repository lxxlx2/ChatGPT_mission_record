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
from test_frank_a04_claude_fourth_review import fee_only_receipt
from test_frank_a04_history_resume import signature
from test_frank_a04_a05_chain_capture import OWNER_A

path = Path(os.environ["FRANK_A04_TEST_OLD_V2_SIDECAR"])
sig = signature(6501)
raw = fee_only_receipt(sig, 6500)
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
    assert original_doc["native_sol_coverage_status"] == "NATIVE_SOL_FLOW_UNCLASSIFIED"
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
    }
    path.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8")
finally:
    sidecar.close()
print("FROZEN_PR52_V2_SIDECAR_BUILT", path)
