"""CI script: write V2 generic TX via actual frozen PR #52 Python modules."""
import json
import os
from pathlib import Path

from mission_agent.mission_control.wallet_economic_ledger import normalize_transaction
import mission_agent.mission_control.wallet_economic_ledger as economic_ledger
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from test_frank_a04_a05_chain_capture import OWNER_A
from test_frank_a04_claude_fourth_review import fee_only_receipt
from test_frank_a04_history_resume import signature

assert "/frank-old-v2-parent/" in str(economic_ledger.__file__), (
    "NOT_FROZEN_PR52_NORMALIZER:" + str(economic_ledger.__file__)
)
path = Path(os.environ["FRANK_A04_LEGACY_GENERIC_TX_PATH"])
sig, slot = signature(9401), 9400
raw = fee_only_receipt(sig, slot)
old = normalize_transaction(raw, tracked_wallets={OWNER_A})
assert old["schema_version"] == 2
assert old["normalizer_version"] == "SOL_TOKEN_VIEW_V2"
assert old["native_sol_coverage_status"] == "NO_NATIVE_SOL_FLOW_OBSERVED"
identity = "solana:" + sig + ":" + str(slot)
store = WalletEvidenceStore(path)
try:
    assert store.record_transaction(old) is True
    assert store.record_transaction(old) is False
    original = store.db.execute(
        "SELECT identity,source_sha256,payload_json FROM evidence_documents "
        "WHERE kind='TX'"
    ).fetchone()
    assert original["identity"] == identity
    assert json.loads(original["payload_json"]) == old
    assert store.count("TX") == 1
    manifest = {
        "signature": sig,
        "slot": slot,
        "legacy_hash": original["source_sha256"],
        "legacy_payload": original["payload_json"],
        "old_module": str(economic_ledger.__file__),
    }
    path.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8"
    )
finally:
    store.close()
print("FROZEN_PR52_UNVERSIONED_TX_V2_PASS")
