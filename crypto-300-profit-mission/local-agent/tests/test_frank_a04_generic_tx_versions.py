"""P2 generic TX source invariant: V2 and V3 projections coexist immutably.

Synthetic regression uses precisely the same slot/signature/RAW token receipt;
an independent workflow also runs both frozen parent and current SHA code.
"""
import hashlib
import json

import pytest

from mission_agent.mission_control.wallet_economic_ledger import normalize_transaction
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from test_frank_a04_a05_chain_capture import OWNER_A
from test_frank_a04_claude_fourth_review import fee_only_receipt
from test_frank_a04_history_resume import signature


def _normalized(version, raw):
    current = normalize_transaction(raw, tracked_wallets={OWNER_A})
    if version == 3:
        return current
    legacy = dict(current)
    legacy["schema_version"] = 2
    legacy["normalizer_version"] = "SOL_TOKEN_VIEW_V2"
    legacy["native_sol_coverage_status"] = "NATIVE_SOL_FLOW_UNCLASSIFIED"
    legacy.pop("native_sol_observation_reason")
    legacy.pop("canonical_event_sha256")
    legacy["canonical_event_sha256"] = hashlib.sha256(
        json.dumps(legacy, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode()).hexdigest()
    return legacy


@pytest.mark.parametrize("reverse", [False, True])
def test_preexisting_v2_and_v3_generic_tx_coexist_in_both_orders(tmp_path, reverse):
    path = tmp_path / "research.sqlite"
    sig, slot = signature(7301), 5001
    raw = fee_only_receipt(sig, slot)
    legacy, current = _normalized(2, raw), _normalized(3, raw)
    assert legacy["canonical_event_sha256"] != current["canonical_event_sha256"]
    rows = [legacy, current]
    if reverse:
        rows.reverse()
    store = WalletEvidenceStore(path)
    try:
        for row in rows:
            assert store.record_transaction(row) is True
            assert store.record_transaction(row) is False
        assert store.count("TX") == 2
        keys = ["solana:" + sig + ":" + str(slot),
                "solana:" + sig + ":" + str(slot) + ":v3"]
        archived = store.db.execute(
            "SELECT identity,payload_json,source_sha256 FROM evidence_documents "
            "WHERE kind='TX' ORDER BY identity"
        ).fetchall()
        assert {row["identity"] for row in archived} == set(keys)
        values = {row["identity"]: json.loads(row["payload_json"])
                  for row in archived}
        assert values[keys[0]] == legacy
        assert values[keys[1]] == current
        assert all(
            hashlib.sha256(row["payload_json"].encode()).hexdigest()
            == row["source_sha256"] for row in archived
        )
        source_before = {
            row["identity"]: (row["source_sha256"], row["payload_json"])
            for row in archived
        }
        # An independently hashed, semantically changed same-version
        # projection must conflict, not mutate history or allocate a third TX.
        changed = dict(current)
        changed["fees_lamports"] += 1
        changed.pop("canonical_event_sha256")
        changed["canonical_event_sha256"] = hashlib.sha256(
            json.dumps(changed, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False).encode()).hexdigest()
        with pytest.raises(ValueError, match="IMMUTABLE_EVIDENCE_CONFLICT"):
            store.record_transaction(changed)
        assert store.count("TX") == 2
        assert {row["identity"]: (row["source_sha256"], row["payload_json"])
                for row in store.db.execute(
                    "SELECT identity,payload_json,source_sha256 FROM evidence_documents "
                    "WHERE kind='TX'"
                ).fetchall()} == source_before
    finally:
        store.close()
    reader = WalletEvidenceStore(path, read_only=True)
    try:
        assert reader.count("TX") == 2
    finally:
        reader.close()


@pytest.mark.parametrize(("schema", "version"), [
    (3, "SOL_TOKEN_VIEW_V2"), (2, "SOL_TOKEN_VIEW_V3"),
    (4, "SOL_TOKEN_VIEW_V4"), (True, "SOL_TOKEN_VIEW_V3"),
    (3, "SOL_TOKEN_VIEW_V3:malicious"), (3, None),
])
def test_generic_tx_rejects_unapproved_or_mismatched_version_identity(
    tmp_path, schema, version
):
    raw = fee_only_receipt(signature(7302), 5002)
    doc = _normalized(3, raw)
    doc["schema_version"] = schema
    doc["normalizer_version"] = version
    doc.pop("canonical_event_sha256")
    doc["canonical_event_sha256"] = hashlib.sha256(
        json.dumps(doc, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode()).hexdigest()
    store = WalletEvidenceStore(tmp_path / "research.sqlite")
    try:
        with pytest.raises(ValueError, match="UNSUPPORTED_TRANSACTION_NORMALIZER_VERSION"):
            store.record_transaction(doc)
        assert store.count("TX") == 0
    finally:
        store.close()
