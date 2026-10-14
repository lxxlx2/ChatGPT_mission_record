"""CI script: V3 generic TX import must coexist with true old PR52 TX."""
import hashlib
import json
import os
from pathlib import Path

from mission_agent.mission_control.wallet_economic_ledger import normalize_transaction
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from test_frank_a04_a05_chain_capture import OWNER_A
from test_frank_a04_claude_fourth_review import fee_only_receipt

path = Path(os.environ["FRANK_A04_LEGACY_GENERIC_TX_PATH"])
manifest = json.loads(path.with_suffix(".manifest.json").read_text("utf-8"))
sig, slot = manifest["signature"], manifest["slot"]
raw = fee_only_receipt(sig, slot)
current = normalize_transaction(raw, tracked_wallets={OWNER_A})
assert current["normalizer_version"] == "SOL_TOKEN_VIEW_V3"
assert current["schema_version"] == 3
base = "solana:" + sig + ":" + str(slot)

store = WalletEvidenceStore(path)
try:
    prior = store.db.execute(
        "SELECT source_sha256,payload_json FROM evidence_documents "
        "WHERE kind='TX' AND identity=?", (base,)
    ).fetchone()
    assert prior["source_sha256"] == manifest["legacy_hash"]
    assert prior["payload_json"] == manifest["legacy_payload"]
    assert store.record_transaction(current) is True
    assert store.record_transaction(current) is False
    assert store.count("TX") == 2
    updated = store.db.execute(
        "SELECT identity,source_sha256,payload_json FROM evidence_documents "
        "WHERE kind='TX' ORDER BY identity"
    ).fetchall()
    assert {r["identity"] for r in updated} == {base, base + ":v3"}
    for row in updated:
        assert row["source_sha256"] == hashlib.sha256(
            row["payload_json"].encode("utf-8")
        ).hexdigest()
    again_old = store.db.execute(
        "SELECT source_sha256,payload_json FROM evidence_documents "
        "WHERE kind='TX' AND identity=?", (base,)
    ).fetchone()
    assert again_old["source_sha256"] == manifest["legacy_hash"]
    assert again_old["payload_json"] == manifest["legacy_payload"]
    modern = json.loads(store.db.execute(
        "SELECT payload_json FROM evidence_documents "
        "WHERE kind='TX' AND identity=?", (base + ":v3",)
    ).fetchone()["payload_json"])
    assert modern == current
    # Same-version changes are correctly refused, rather than silent copies.
    altered = dict(current)
    altered["fees_lamports"] += 1
    altered.pop("canonical_event_sha256")
    altered["canonical_event_sha256"] = hashlib.sha256(
        json.dumps(altered, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode()
    ).hexdigest()
    try:
        store.record_transaction(altered)
    except ValueError as exc:
        assert str(exc) == "IMMUTABLE_EVIDENCE_CONFLICT"
    else:
        raise AssertionError("SAME_VERSION_CONFLICT_NOT_BLOCKED")
    assert store.count("TX") == 2
finally:
    store.close()
print("ACTUAL_PARENT_V2_PLUS_CURRENT_V3_GENERIC_TX_PASS")
print("GENERIC_TX_VERSION_REIMPORT_IDEMPOTENCE_PASS")
print("ORIGINAL_UNVERSIONED_TX_V2_BYTES_AND_HASH_PRESERVED_PASS")
