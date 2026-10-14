"""A04: older V2 native-SOL economic view must survive immutable V3 upgrade.

The synthetic V2 model emulates the exact pre-native-reason schema. A
separate CI cross-SHA job builds a real V2 file using the frozen PR #52 code.
"""
import hashlib
import json

from mission_agent.mission_control.wallet_economic_ledger import normalize_transaction
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_history_replay import (
    HistoryJournal, _HISTORY_SCHEMA,
)
from test_frank_a04_claude_fourth_review import fee_only_receipt
from test_frank_a04_history_resume import signature
from test_frank_a04_a05_chain_capture import OWNER_A


def _serial(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _store(db, kind, identity, value):
    payload = _serial(value)
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    db.execute(
        "INSERT INTO evidence_documents(kind,identity,source_sha256,payload_json)"
        " VALUES(?,?,?,?)", (kind, identity, h, payload),
    )
    return (h, payload)


def _prior_v2_view(tx, wallet):
    from mission_agent.mission_control.wallet_instruction_evidence import (
        transfer_instructions,
    )
    current = normalize_transaction(tx, tracked_wallets={wallet})
    assert current["native_sol_coverage_status"] == "NO_NATIVE_SOL_FLOW_OBSERVED"
    legacy = dict(current)
    legacy["schema_version"] = 2
    legacy["normalizer_version"] = "SOL_TOKEN_VIEW_V2"
    legacy["native_sol_coverage_status"] = "NATIVE_SOL_FLOW_UNCLASSIFIED"
    legacy.pop("native_sol_observation_reason", None)
    def hashed(obj):
        payload = {k: v for k, v in obj.items()
                   if k != "canonical_event_sha256"}
        return hashlib.sha256(_serial(payload).encode("utf-8")).hexdigest()
    legacy["canonical_event_sha256"] = hashed(legacy)
    legacy["research_wallet"] = wallet
    legacy["instruction_evidence"] = transfer_instructions(tx, legacy)
    legacy["canonical_event_sha256"] = hashed(legacy)
    return legacy


def test_legacy_v2_with_old_sol_status_migrates_to_new_v3_without_rewrite(tmp_path):
    db_path = tmp_path / "prior-immutable-v2.sqlite"
    sig, slot = signature(3201), 2000
    raw = fee_only_receipt(sig, slot)
    old_v2 = _prior_v2_view(raw, OWNER_A)
    wallet = OWNER_A
    identity = wallet + ":" + sig + ":" + str(slot)
    previous = WalletEvidenceStore(db_path)
    try:
        previous.db.executescript(_HISTORY_SCHEMA)
        with previous.db:
            previous.db.execute(
                "ALTER TABLE wallet_history_signature ADD COLUMN v2_error_code TEXT"
            )
            previous.db.execute(
                "INSERT INTO wallet_history_cursor(wallet,next_before,"
                "pagination_end_observed,page_count) VALUES(?,?,1,2)",
                (wallet, sig),
            )
            previous.db.execute(
                "INSERT INTO wallet_history_signature"
                "(wallet,signature,slot,state) VALUES(?,?,?,'CAPTURED')",
                (wallet, sig, slot),
            )
            old_raw = _store(previous.db, "RAW_TX", sig + ":" + str(slot), raw)
            old_doc = _store(
                previous.db, "WALLET_TX_VIEW_V2", identity + ":v2", old_v2)
        assert previous.count("WALLET_TX_VIEW_V2") == 1
    finally:
        previous.close()

    upgraded = WalletEvidenceStore(db_path)
    try:
        journal = HistoryJournal(upgraded)
        assert "v3_error_code" in {
            r["name"] for r in upgraded.db.execute(
                "PRAGMA table_info(wallet_history_signature)"
            )
        }
        before = journal.state(wallet)
        assert before["captured"] == 1 and before["pending"] == 0
        assert before["legacy_v2_document_count"] == 1
        assert before["v3_missing_count"] == 1
        assert before["coverage"] == "PARTIAL_ECONOMIC_EVIDENCE"
        assert before["normalizer_version"] == "SOL_TOKEN_VIEW_V3"

        built = journal.rebuild_versioned_views(wallet)
        assert built["view_kind"] == "WALLET_TX_VIEW_V3"
        assert built["normalizer_version"] == "SOL_TOKEN_VIEW_V3"
        assert built["new"] == 1 and built["blocked"] == 0
        again = journal.rebuild_versioned_views(wallet)
        assert again["new"] == 0 and again["already_present"] == 1
        assert again["blocked"] == 0

        now = journal.state(wallet)
        assert now["v3_missing_count"] == 0 and now["v3_blocked_count"] == 0
        assert now["legacy_v2_document_count"] == 1
        assert now["native_sol_unclassified_count"] == 0
        assert now["coverage"] == "AVAILABLE_SOURCE_END_NOT_GENESIS_PROVEN"
        row = upgraded.db.execute(
            "SELECT payload_json FROM evidence_documents "
            "WHERE kind='WALLET_TX_VIEW_V3' AND identity=?",
            (identity + ":v3",),
        ).fetchone()
        modern = json.loads(row["payload_json"])
        assert modern["schema_version"] == 3
        assert modern["normalizer_version"] == "SOL_TOKEN_VIEW_V3"
        assert modern["native_sol_coverage_status"] == "NO_NATIVE_SOL_FLOW_OBSERVED"
        assert upgraded.count("WALLET_TX_VIEW_V2") == 1
        assert upgraded.count("WALLET_TX_VIEW_V3") == 1
        for kind, old_identity, expected in [
            ("RAW_TX", sig + ":" + str(slot), old_raw),
            ("WALLET_TX_VIEW_V2", identity + ":v2", old_doc),
        ]:
            archived = upgraded.db.execute(
                "SELECT source_sha256,payload_json FROM evidence_documents "
                "WHERE kind=? AND identity=?", (kind, old_identity),
            ).fetchone()
            assert tuple(archived) == expected
        assert journal.state(wallet) == now
    finally:
        upgraded.close()
