"""Dated Frank wallet inventory reconciliation against actual Oct 11 RPC evidence."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import zipfile

import pytest

from mission_agent.mission_control.wallet_inventory import (
    InventoryEvidenceError, reconcile_watchlist, FRANK_WALLET,
)
from mission_agent.mission_control.wallet_watch import from_seed
from mission_agent.mission_control.server import DashboardState
from scripts.frank_evidence_bootstrap import main as mac_bootstrap

EVIDENCE = (Path(__file__).resolve().parents[2] / "meme" / "evidence" /
            "frank-v2-thirty-two-mint-finalized-2026-10-11.json")

OPEN = {
    "4mkNDiEALDutn8Py1GmJnvVuTdHVuL9y6AmcL9KTZx7F",
    "9bsHPggRK5Drw8sR7QBcx5pXrHH7Mc6haLmiR2d7aY2a",
    "9dSMwFfPezQ8WPcW1uZV7ns4rcviEj2LssSAg75WBLXd",
    "9fJAWKQpkY93hfuZxrHfh5wEh2AV9vjkWNQfzfbziHd2",
    "H7TuvDxEKygh27zGfGcjKG8JGWgrbyKpPtvJEpGosfas",
}
UNCERTAIN = {
    "CbcyNo7m1amFWqEQm2m4PLv1UNvpcL3C1Ujm6AkzpKoU",
    "GTBxUiw6wJdmmkCGZgRHLyYxqu1vG4KtRpeox6yDpump",
}
CLOSED_RETAINED = {
    "7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump",
    "BXoHJddsWJLHtAopeiSbKUSELsu8hSFMs8baGMDkpump",
    "F5WvFdG9sCfhv3bVYAMJNWiwpx5e3X2uvpXDtLtdsDJs",
}
UNKNOWN_RETAINED = "7KEPApdbBMByrmqihz3bht2uMhFQcatjfSFQCKq66kH3"


@pytest.fixture
def real_snapshot():
    return json.loads(EVIDENCE.read_text())


def make_watch(evidence):
    seed = []
    for record in evidence["records"]:
        mint = record["mint"]
        state = ("OPEN" if mint in OPEN else
                 "INVENTORY_UNDETERMINED" if mint in UNCERTAIN else
                 "CLOSED" if mint in CLOSED_RETAINED else "UNKNOWN")
        seed.append({"mint": mint, "local_state": state,
                     "local_recognized_buy_count": 1, "local_recognized_sell_count": 0})
    return from_seed(seed)


def test_real_32_mint_balance_source_matches_local_observation_contract(real_snapshot):
    assert real_snapshot["wallet"] == FRANK_WALLET
    assert len(real_snapshot["records"]) == 32
    result = reconcile_watchlist(make_watch(real_snapshot), real_snapshot)
    stats = result["snapshot_reconciliation"]
    assert stats["matched_mints"] == 32
    assert stats["nonzero_at_snapshot"] == 10
    assert stats["zero_at_snapshot"] == 22
    assert stats["unresolved_without_snapshot"] == 0
    assert stats["model_closed_with_remaining_tokens"] == 3
    assert stats["model_unknown_with_remaining_tokens"] == 1
    assert stats["model_open_with_zero_tokens"] == 0
    assert stats["model_uncertain_nonzero"] == 1
    assert result["wallet_total_nav_usd"] is None
    assert result["chain_completeness_verified"] is False
    assert result["snapshot_status"] == "DATED_POINT_IN_TIME_NOT_LIVE"
    assert all(x["current_chain_balance_verified"] is False for x in result["rows"])
    assert all(x["market_value_usd"] is None and x["pnl_usd"] is None for x in result["rows"])


def test_outdated_model_closed_but_positive_chain_balance_is_visible(real_snapshot):
    snap = reconcile_watchlist(make_watch(real_snapshot), real_snapshot)
    lookup = {x["mint"]: x for x in snap["rows"]}
    for mint in CLOSED_RETAINED:
        x = lookup[mint]
        assert x["watch_state"] == "HISTORICAL_EXIT"
        assert x["snapshot_inventory_state"] == "NONZERO_AT_SLOT"
        assert x["model_chain_disagreement"] == "MODEL_CLOSED_WITH_RESIDUAL_BALANCE"
        assert x["snapshot_token_quantity"] not in ("0", None)
        assert x["snapshot_source"] == "EXPORTED_FINALIZED_RPC_RECORD"
    assert lookup[UNKNOWN_RETAINED]["model_chain_disagreement"] == "MODEL_UNKNOWN_WITH_POSITIVE_BALANCE"


def test_unscanned_token_is_unresolved_not_zero(real_snapshot):
    reduced = deepcopy(real_snapshot)
    reduced["records"] = reduced["records"][:6]
    snap = reconcile_watchlist(make_watch(real_snapshot), reduced)
    assert snap["snapshot_reconciliation"]["matched_mints"] == 6
    assert snap["snapshot_reconciliation"]["unresolved_without_snapshot"] == 26
    absent = [r for r in snap["rows"] if r["mint"] not in {e["mint"] for e in reduced["records"]}]
    assert len(absent) == 26
    assert all(r["snapshot_inventory_state"] == "NOT_QUERIED_IN_SNAPSHOT" for r in absent)


@pytest.mark.parametrize("attribute,bad", [
    ("wallet", "unknown_wallet"),
    ("commitment", "processed"),
    ("network", "solana-devnet"),
    ("status", "INCOMPLETE"),
])
def test_bad_source_cannot_be_promoted_to_verified(real_snapshot, attribute, bad):
    cloned = deepcopy(real_snapshot)
    cloned[attribute] = bad
    with pytest.raises(InventoryEvidenceError):
        reconcile_watchlist(make_watch(real_snapshot), cloned)


@pytest.mark.parametrize("field,bad", [
    ("raw_amount", "-4"), ("raw_amount", "NaN"), ("raw_amount", 100),
    ("decimals", -1), ("decimals", 20), ("slot", 0), ("slot", None),
])
def test_bad_token_amount_and_slot_fail_closed(real_snapshot, field, bad):
    cloned = deepcopy(real_snapshot)
    cloned["records"][0][field] = bad
    with pytest.raises(InventoryEvidenceError):
        reconcile_watchlist(make_watch(real_snapshot), cloned)


def test_duplicate_record_does_not_count_twice(real_snapshot):
    cloned = deepcopy(real_snapshot)
    cloned["records"].append(deepcopy(cloned["records"][0]))
    with pytest.raises(InventoryEvidenceError, match="DUPLICATE"):
        reconcile_watchlist(make_watch(real_snapshot), cloned)


def test_dashboard_dated_source_fallback_and_explicit_precedence_are_safe(tmp_path, real_snapshot):
    db = tmp_path / "forward.sqlite"
    with sqlite3.connect(db) as conn:
        conn.executescript("""
            CREATE TABLE v1_states(person_id TEXT,mint TEXT,body TEXT);
            CREATE TABLE signatures(wallet TEXT,person_id TEXT,signature TEXT,block_time INTEGER,body TEXT);
            CREATE TABLE trades(wallet TEXT,signature TEXT,mint TEXT,episode_id TEXT,block_time INTEGER,side TEXT,body TEXT);
        """)
        for mint in OPEN:
            conn.execute("INSERT INTO v1_states VALUES(?,?,?)", ("frank",mint,'{"state":"OPEN"}'))
    state = DashboardState(tmp_path, tmp_path)
    without = state.frank_observed_watchlist()
    assert without["snapshot_status"] == "DATED_POINT_IN_TIME_NOT_LIVE"
    assert without["snapshot_origin"] == "REPO_DATED_2026_10_11_NOT_LIVE"
    assert without["summary"]["model_open"] == 5
    assert without["snapshot_reconciliation"]["matched_mints"] == 5
    assert without["wallet_total_nav_usd"] is None
    assert all(r["current_chain_balance_verified"] is False for r in without["rows"])
    (tmp_path / "frank-inventory-snapshot.json").write_text(json.dumps(real_snapshot))
    with_proof = state.frank_observed_watchlist()
    assert with_proof["snapshot_reconciliation"]["matched_mints"] == 5
    assert with_proof["snapshot_origin"] == "CONTROL_ROOT_EXPLICIT_IMPORT"
    assert with_proof["snapshot_reconciliation"]["nonzero_at_snapshot"] == 5
    assert with_proof["snapshot_status"] == "DATED_POINT_IN_TIME_NOT_LIVE"
    assert with_proof["wallet_total_nav_usd"] is None
    assert all(r["current_chain_balance_verified"] is False for r in with_proof["rows"])
    assert db.exists()


def test_mac_bootstrap_combines_local_model_and_explicit_dated_source_without_deployment(
        tmp_path, real_snapshot):
    prod = tmp_path / "production"
    prod.mkdir()
    with sqlite3.connect(prod / "forward.sqlite") as conn:
        conn.executescript("""
            CREATE TABLE v1_states(person_id TEXT,mint TEXT,body TEXT);
            CREATE TABLE signatures(wallet TEXT,person_id TEXT,signature TEXT,block_time INTEGER,body TEXT);
            CREATE TABLE trades(wallet TEXT,signature TEXT,mint TEXT,episode_id TEXT,block_time INTEGER,side TEXT,body TEXT);
        """)
        conn.execute("INSERT INTO v1_states VALUES(?,?,?)",
                     ("frank", sorted(OPEN)[0], '{"state":"OPEN","current_raw":"1"}'))
    evidence = tmp_path / "finalized.json"
    evidence.write_text(json.dumps(real_snapshot))
    output = tmp_path / "frank-evidence.zip"
    result = mac_bootstrap([
        "--production-root", str(prod),
        "--control-root", str(tmp_path / "control"),
        "--output", str(output),
        "--inventory-evidence", str(evidence),
    ])
    assert result == 0
    with zipfile.ZipFile(output) as z:
        names = z.namelist()
        assert "frank-inventory-dated-reconciliation.json" in names
        assert "frank-local-trade-inventory-gap-audit.json" in names
        audit = json.loads(z.read("frank-local-trade-inventory-gap-audit.json"))
        assert audit["wallet_pnl_usd"] is None
        assert audit["chain_complete"] is False
        assert audit["history_records"] == 0
        report = json.loads(z.read("frank-inventory-dated-reconciliation.json"))
        assert report["snapshot_reconciliation"]["matched_mints"] == 1
        assert report["snapshot_reconciliation"]["nonzero_at_snapshot"] == 1
        assert report["chain_completeness_verified"] is False
        assert report["wallet_total_nav_usd"] is None
        assert "frank-d0-local-index.json" in names
        assert any("frank-history" in n for n in names)
        assert any("frank-transfer-history/" in n for n in names)
        assert any("frank-transfer-history-parts/" in n for n in names)
        status = json.loads(z.read("summary.json"))
        assert status["inventory_reconciliation"] == "DATED_POINT_IN_TIME_NOT_LIVE"
        assert status["frank_transfer_signature_records"] == 0
        assert status["frank_transfer_history"] == "QUEUED_LOCALLY"
        assert status["git_sync"] == "NOT_REQUESTED"
    assert not (prod / "health.json").exists()
