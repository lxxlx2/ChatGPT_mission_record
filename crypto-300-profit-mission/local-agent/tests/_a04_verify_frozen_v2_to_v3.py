"""CI-only consumer: validate upgraded PR #52 V2 -> new V3, byte for byte.

Run only after _a04_build_frozen_v2_sidecar.py generated the old database with
the actual fixed parent SHA source in a separate worktree.
"""
import json
import os
from pathlib import Path

from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_history_replay import HistoryJournal

path = Path(os.environ["FRANK_A04_TEST_OLD_V2_SIDECAR"])
manifest = json.loads(path.with_suffix(".manifest.json").read_text(encoding="utf-8"))
wallet, sig, slot = manifest["wallet"], manifest["signature"], manifest["slot"]
store = WalletEvidenceStore(path)
try:
    journal = HistoryJournal(store)
    before = journal.state(wallet)
    assert before["captured"] == 1 and before["pending"] == 0
    assert before["legacy_v2_document_count"] == 1
    assert before["v3_missing_count"] == 1
    assert before["coverage"] == "PARTIAL_ECONOMIC_EVIDENCE"
    assert before["normalizer_version"] == "SOL_TOKEN_VIEW_V3"
    assert before["source_pagination_coverage"] == "AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
    first = journal.rebuild_versioned_views(wallet)
    assert first["new"] == 1 and first["already_present"] == 0
    assert first["blocked"] == 0
    second = journal.rebuild_versioned_views(wallet)
    assert second["new"] == 0 and second["already_present"] == 1
    assert second["blocked"] == 0
    assert first["normalizer_version"] == "SOL_TOKEN_VIEW_V3"
    assert store.count("WALLET_TX_VIEW_V2") == 1
    assert store.count("WALLET_TX_VIEW_V3") == 1

    current = store.db.execute(
        "SELECT source_sha256,payload_json FROM evidence_documents "
        "WHERE kind='WALLET_TX_VIEW_V3' AND identity=?",
        (wallet + ":" + sig + ":" + str(slot) + ":v3",),
    ).fetchone()
    doc = json.loads(current["payload_json"])
    assert doc["normalizer_version"] == "SOL_TOKEN_VIEW_V3"
    assert doc["schema_version"] == 3
    assert doc["native_sol_coverage_status"] == "NO_NATIVE_SOL_FLOW_OBSERVED"
    after = journal.state(wallet)
    assert after["v3_missing_count"] == 0 and after["v3_blocked_count"] == 0
    assert after["coverage"] == "AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
    assert after["legacy_v2_document_count"] == 1
    assert after["native_sol_unclassified_count"] == 0

    unchanged = store.db.execute(
        "SELECT source_sha256,payload_json FROM evidence_documents "
        "WHERE kind='WALLET_TX_VIEW_V2' AND identity=?",
        (wallet + ":" + sig + ":" + str(slot) + ":v2",),
    ).fetchone()
    assert unchanged["source_sha256"] == manifest["v2_hash"]
    assert unchanged["payload_json"] == manifest["v2_payload"]
    assert store.db.execute(
        "SELECT payload_json FROM evidence_documents "
        "WHERE kind='RAW_TX' AND identity=?",
        (sig + ":" + str(slot),),
    ).fetchone()["payload_json"] == manifest["source_raw"]
    assert dict(store.db.execute(
        "SELECT * FROM wallet_history_cursor WHERE wallet=?", (wallet,),
    ).fetchone()) == manifest["cursor"]
    print("REAL_PARENT_SHA_V2_TO_V3_UPGRADE=PASS")
    print("LEGACY_RAW_AND_V2_BYTE_IDENTICAL=PASS")
    print("CURRENT_V3_IDEMPOTENT_AND_COVERAGE=PASS")
finally:
    store.close()
