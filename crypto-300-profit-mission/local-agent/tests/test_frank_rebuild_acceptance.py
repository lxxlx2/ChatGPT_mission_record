"""Regression coverage for the unified offline Frank release checks."""
from contextlib import closing
import gzip
import hashlib
import json
import shutil
import sqlite3
import sys

import pytest

from mission_agent.frank.rpc import WALLET
from mission_agent.meme.holder_ranks import _b58
from mission_agent.mission_control.archived_wallet_facts import read_archived_classification
from mission_agent.signals.auto_buy_category import AutoBuyCategory
from mission_agent.signals.buy_reconciliation import audit_buys
from mission_agent.signals.category_evidence import COINGECKO_SOLANA
from mission_agent.signals.classifier import classify
from mission_agent.signals.engine import Engine
from mission_agent.signals.gmail import GmailOutbox
from mission_agent.signals.policy import USDC, load_policy
from mission_agent.signals.reconciliation import ReconciliationError, reconcile_snapshot
from mission_agent.signals.store import Ledger
from scripts import accept_frank_rebuild as acceptance, frank_local_signal_service as service
from test_frank_fm import tx
from test_frank_rebuild_buys import AS_OF, MINT, config
from test_frank_rebuild_delivery import indexed_buys, prepare
from test_frank_v1 import POLICY


REV = "ab" * 20


@pytest.fixture
def isolated_phases(monkeypatch):
    calls = []

    def clean(revision):
        calls.append(("sha", revision))
        return revision == REV

    monkeypatch.setattr(acceptance, "_assert_revision", clean)
    monkeypatch.setattr(acceptance, "_pytest", lambda *args, **kw: {"status": "PASS"})
    monkeypatch.setattr(acceptance, "_run", lambda *args, **kw: {"status": "PASS"})
    return calls


def test_default_machine_report_leaves_live_and_deployment_gates_closed(isolated_phases, capsys):
    assert acceptance.main(["--source-sha", REV]) == 2
    report = json.loads(capsys.readouterr().out)
    assert isolated_phases == [("sha", REV), ("sha", REV)]
    assert report["status"] == "PARTIAL"
    assert report["isolated_python"]["status"] == report["isolated_node"]["status"] == "PASS"
    assert report["isolated_chrome"]["status"] == report["supplied_wallet_window"]["status"] == "BLOCKED"
    assert report["live_ca_freshness_and_latency"]["status"] == "BLOCKED"
    assert report["real_recipient_delivery"]["status"] == "NOT_VERIFIED"
    assert report["deployment"] == "NO_GO"


def test_required_wallet_check_cannot_pass_without_buy_expectations(isolated_phases, capsys, monkeypatch):
    monkeypatch.setattr(acceptance, "_wallet", lambda _: {
        "status": "MATCHED_WITHIN_SUPPLIED_WINDOW",
        "buy_admission": {"status": "MATCHED_WITHIN_SUPPLIED_WINDOW", "counts": {"EXPECTED_IN": 0}},
    })
    assert acceptance.main(["--source-sha", REV, "--require-wallet-window"]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "PARTIAL"


def test_source_drift_stops_machine_acceptance(isolated_phases, capsys, monkeypatch):
    revisions = iter((True, False))
    monkeypatch.setattr(acceptance, "_assert_revision", lambda _: next(revisions))
    assert acceptance.main(["--source-sha", REV]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "FAIL" and report["source_intact"] is False
    assert report["deployment"] == "NO_GO"


def test_wallet_flags_reach_reconciler_and_summary_excludes_private_rows(
        tmp_path, isolated_phases, capsys, monkeypatch):
    archive = tmp_path / "raw"
    legacy = tmp_path / "legacy"

    def reconcile(snapshot, snapshot_hash, reference, reference_hash, *, scanner_source_id,
                  buy_qualifications, buy_archive_root, buy_legacy_archive_root):
        assert (snapshot, snapshot_hash, reference, reference_hash) == (
            tmp_path / "db", "a" * 64, tmp_path / "reference", "b" * 64)
        assert scanner_source_id == "independent_fixture"
        assert buy_qualifications == (tmp_path / "qual", "c" * 64, AS_OF)
        assert (buy_archive_root, buy_legacy_archive_root) == (archive, legacy)
        return {"status": "MATCHED_WITHIN_SUPPLIED_WINDOW", "rows": ["private"],
                "unexpected_signatures": ["private"], "buy_admission": {
                    "status": "MATCHED_WITHIN_SUPPLIED_WINDOW", "counts": {"EXPECTED_IN": 2},
                    "chain_to_index": {"p95_seconds": 3, "unknown_count": 0, "sample_count": 2},
                }}

    monkeypatch.setattr(acceptance, "reconcile_snapshot", reconcile)
    flags = ["--source-sha", REV, "--allow-partial", "--require-wallet-window", "--snapshot", str(tmp_path / "db"),
             "--snapshot-sha256", "a" * 64, "--reference", str(tmp_path / "reference"),
             "--reference-sha256", "b" * 64, "--scanner-source-id", "independent_fixture",
             "--qualifications", str(tmp_path / "qual"), "--qualifications-sha256", "c" * 64,
             "--qualification-as-of", str(AS_OF), "--buy-archive-root", str(archive),
             "--buy-legacy-archive-root", str(legacy), "--max-index-p95-seconds"]
    assert acceptance.main([*flags, "4"]) == 0
    passing = capsys.readouterr().out
    assert "private" not in passing
    assert json.loads(passing)["wallet_index_sla"] == {
        "status": "PASS", "threshold_seconds": 4, "p95_seconds": 3, "sample_count": 2,
    }
    assert acceptance.main([*flags, "2"]) == 1
    assert json.loads(capsys.readouterr().out)["wallet_index_sla"]["status"] == "FAIL"


@pytest.mark.parametrize("mode", ["correct", "missing", "wrong_index", "legacy_shape", "unexpected"])
def test_buy_reconciliation_accounts_for_every_multileg_row(tmp_path, monkeypatch, mode):
    cfg = tmp_path / "qualifications.json"
    config(cfg)
    with sqlite3.connect(":memory:") as db:
        db.row_factory = sqlite3.Row
        db.executescript("""
            CREATE TABLE signatures(wallet, signature, body, block_time, raw_hash, seen_at);
            CREATE TABLE trades(wallet, signature, side, mint, body);
        """)
        legs = [{"leg_index": 3, "mint": MINT, "direction": "BUY"},
                {"leg_index": 7, "mint": MINT, "direction": "BUY"}]
        db.execute("INSERT INTO signatures VALUES(?,?,?,?,?,?)",
                   (WALLET, "fixture", json.dumps({"classification": "ACTIVE_TRADE", "trade_legs": legs}),
                    AS_OF - 20, "a" * 64, AS_OF - 2))
        for leg in legs[:1] if mode == "missing" else legs:
            db.execute("INSERT INTO trades VALUES(?,?,?,?,?)", (WALLET, "fixture", "BUY", MINT, json.dumps(leg)))
        expected = [{"leg_index": leg["leg_index"], "mint": MINT} for leg in reversed(legs)]
        if mode == "wrong_index":
            expected[0]["leg_index"] = 8
        elif mode == "legacy_shape":
            expected = MINT
        elif mode == "unexpected":
            expected = False
        ref = {"person_id": "frank", "wallet": WALLET, "transactions": [{
            "expected_frank_buy": expected, "expectation_sha256": "b" * 64, "slot": 12,
        }]}
        result = {"unexpected_indexed_signatures": [], "rows": [{
            "signature": "fixture", "stages": {"indexed": {"status": "MATCH"}},
        }]}

        def admit(event, assets, **identity):
            assert identity["leg_index"] in {3, 7}
            return {"mint": MINT}

        monkeypatch.setattr("mission_agent.signals.buy_reconciliation.admit_buy", admit)
        audited = audit_buys(db, ref, result, cfg, checksum(cfg), AS_OF)
    expected_status = {"correct": "MATCHED_IN", "missing": "UNRESOLVED", "wrong_index": "WRONG_MINT",
                       "legacy_shape": "WRONG_MINT", "unexpected": "UNEXPECTED"}
    assert audited["counts"][expected_status[mode]] == 1
    if mode == "correct":
        assert [row["leg_index"] for row in result["rows"][0]["buy_admission"]["projected_buys"]] == [3, 7]
        assert audited["chain_to_index"]["sample_count"] == 1


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_buy_reconciliation_uses_pinned_scanner_category_at_the_same_cutoff(tmp_path):
    cfg = tmp_path / "qualification.json"
    cfg.write_text('{"version":1,"records":[]}')
    ledger = Ledger(tmp_path / "ledger")
    try:
        indexed_buys(ledger, tmp_path / "raw", [MINT])
        body = json.dumps({"name": "fixture", "preview_listing": False, "categories": ["Meme"],
                           "platforms": {"solana": MINT},
                           "detail_platforms": {"solana": {"contract_address": MINT}}})
        receipt = {"mint": MINT, "url": COINGECKO_SOLANA + MINT, "observed_at": AS_OF,
                   "body": body, "sha256": hashlib.sha256(body.encode()).hexdigest()}

        def collect(mints, *, api_key, clock, on_result):
            assert mints == [MINT]
            on_result(MINT, "CAPTURED", None)
            return {"records": [receipt]}, {}

        collector = AutoBuyCategory(ledger.db, api_key="fixture", collect=collect, clock=lambda: AS_OF)
        assert collector.refresh()["receipts"] == 1
        sig, slot = tuple(ledger.db.execute("SELECT signature,slot FROM signatures ORDER BY slot DESC").fetchone())
        reference = {"wallet": WALLET, "person_id": "frank", "transactions": [
            {"slot": slot, "expected_frank_buy": MINT, "expectation_sha256": "c" * 64},
        ]}
        result = {"unexpected_indexed_signatures": [], "rows": [
            {"signature": sig, "stages": {"indexed": {"status": "MATCH"}, "detection": {"status": "MATCH"}}},
        ]}

        def counts(as_of):
            return audit_buys(ledger.db, reference, result, cfg, checksum(cfg), as_of)["counts"]

        assert counts(AS_OF - 1)["MATCHED_IN"] == 0
        assert counts(AS_OF)["MATCHED_IN"] == 1
        cfg.write_text(json.dumps({"version": 1, "records": [
            {"chain": "solana", "mint": MINT, "status": "EXCLUDED", "source": "fixture", "observed_at": AS_OF},
        ]}))
        assert counts(AS_OF)["MISSED"] == 1
    finally:
        ledger.db.close()


def test_offline_buy_checks_replay_only_bound_archive_and_refuse_a_wal(tmp_path):
    cfg = tmp_path / "qualification.json"
    config(cfg)
    archive = tmp_path / "raw"
    archive.mkdir()
    signature = _b58((1).to_bytes(64, "big"))
    raw = tx()
    raw["blockTime"] = AS_OF - 10
    raw["transaction"]["signatures"] = [signature]
    for side in ("preTokenBalances", "postTokenBalances"):
        raw["meta"][side][0]["mint"] = MINT
        raw["meta"][side][1]["mint"] = USDC
    event = classify(signature, raw, WALLET)
    raw_hash = event["evidence"]["raw_transaction_sha256"]
    for field in ("quote_legs", "route_amount_semantics", "route_intermediate_evidence_status"):
        del event["trade"][field]
    ledger = Ledger(tmp_path / "ledger.sqlite")
    assert ledger.put("frank", event, raw_hash, str(tmp_path / "untrusted-ledger-path"))
    ledger.checkpoint(WALLET, signature, raw["slot"])
    backup = tmp_path / "backup.sqlite"
    try:
        with sqlite3.connect(backup) as dest:
            ledger.db.backup(dest)
            assert dest.execute("PRAGMA journal_mode=DELETE").fetchone()[0] == "delete"
    finally:
        ledger.db.close()
    reference = tmp_path / "reference.json"
    reference.write_text(json.dumps({
        "schema_version": 1, "chain": "solana", "commitment": "finalized", "complete": True,
        "start_slot": raw["slot"], "end_slot": raw["slot"], "finalized_through_slot": raw["slot"],
        "source_id": "fixture_explorer", "capture_sha256": "c" * 64, "wallet": WALLET, "person_id": "frank",
        "transactions": [{"signature": signature, "slot": raw["slot"],
                          "expected_frank_buy": MINT, "expectation_sha256": "f" * 64}],
    }))
    before = checksum(backup)

    def audit():
        return reconcile_snapshot(backup, before, reference, checksum(reference),
                                  scanner_source_id="fixture_scanner", buy_qualifications=(cfg, checksum(cfg), AS_OF),
                                  buy_archive_root=archive)

    assert audit()["buy_admission"]["counts"]["UNRESOLVED"] == 1
    obj = archive / (signature + ".json.gz")
    obj.write_bytes(gzip.compress(json.dumps(raw).encode()))
    assert audit()["buy_admission"]["counts"]["MATCHED_IN"] == 1
    raw["meta"]["fee"] += 1
    obj.write_bytes(gzip.compress(json.dumps(raw).encode()))
    assert audit()["buy_admission"]["counts"]["UNRESOLVED"] == 1
    assert checksum(backup) == before
    backup.with_name(backup.name + "-wal").touch()
    with pytest.raises(ReconciliationError, match="SNAPSHOT_SIDECAR_PRESENT"):
        audit()


def durable_identities(db):
    queries = (
        "SELECT wallet,signature,slot,updated_at FROM cursors ORDER BY wallet",
        "SELECT wallet,signature,slot,block_time,raw_hash FROM signatures ORDER BY wallet,slot",
        "SELECT signal_id,content_hash FROM signals ORDER BY signal_id",
        "SELECT signal_id,channel,status,attempts,receipt FROM outbox ORDER BY signal_id,channel",
        "SELECT signal_id,wire_message_id,content_hash,status,attempt_count,receipt FROM gmail_delivery ORDER BY signal_id",
    )
    return [[tuple(row) for row in db.execute(query)] for query in queries]


def test_restore_to_new_root_keeps_raw_cursor_and_delivery_identity(tmp_path, monkeypatch, capsys):
    old = tmp_path / "old_machine"
    old.mkdir()
    ledger, _, gate, _ = prepare(old, [MINT])
    other_wallet = _b58((13).to_bytes(32, "big"))
    ledger.checkpoint(other_wallet, _b58((23).to_bytes(64, "big")), 8)
    GmailOutbox(ledger, delivery_gate=gate).sync()
    before = durable_identities(ledger.db)
    assert list(map(len, before)) == [2, 3, 2, 3, 1]

    staging = tmp_path / "new_machine"
    staging.mkdir()
    backup = staging / "forward.sqlite"
    with closing(sqlite3.connect(backup)) as destination:
        ledger.db.backup(destination)
        assert destination.execute("PRAGMA journal_mode=DELETE").fetchone()[0] == "delete"
    ledger.db.close()
    shutil.copytree(old / "raw", staging / "raw")
    shutil.copy2(old / "qualifications.json", staging / "qualifications.json")
    old.rename(tmp_path / "removed_original_mount")
    assert not old.exists()
    registry = staging / "registry.json"
    registry.write_text(json.dumps({"persons": [{"person_id": "frank", "enabled": True, "wallets": [
        {"address": wallet, "chain": "solana"} for wallet in (WALLET, other_wallet)
    ]}]}))
    before_preflight = checksum(backup)
    state_before = sorted(staging.iterdir())
    monkeypatch.setattr(sys, "argv", ["frank_local_signal_service.py", "--check",
                                    "--root", str(staging), "--registry", str(registry),
                                    "--policy", str(POLICY),
                                    "--authority-lock", str(staging / "authority.lock")])
    monkeypatch.setattr(service, "configured_scanner_rpc",
                        lambda *a: pytest.fail("portable preflight cannot require host credentials"))
    service.main()
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PREFLIGHT_PASS"
    assert result["pending_unprocessed_signatures"] == 0
    assert [(row["wallet"], row["signature"], row["slot"]) for row in result["cursor"]] == [
        item[:3] for wallet in (WALLET, other_wallet) for item in before[0] if item[0] == wallet
    ]
    assert checksum(backup) == before_preflight and sorted(staging.iterdir()) == state_before

    restored = Ledger(backup)
    try:
        assert durable_identities(restored.db) == before
        for wallet, signature, slot, at, raw_hash in before[1]:
            event = read_archived_classification(staging / "raw", {
                "wallet": wallet, "sig": signature, "slot": slot, "at": at, "raw_sha256": raw_hash,
            })
            assert event and event["trade"]["mint"] == MINT
        assert Engine(restored, load_policy(POLICY), dry_run=True).drain() == 0
        GmailOutbox(restored).sync()
        assert durable_identities(restored.db) == before
    finally:
        restored.db.close()


@pytest.mark.parametrize(("suffix", "error"), [
    ("-wal", "SCANNER_SNAPSHOT_WAL_NOT_INCLUDED"),
    ("-shm", "SCANNER_SNAPSHOT_SIDECAR_PRESENT"),
    ("-journal", "SCANNER_SNAPSHOT_SIDECAR_PRESENT"),
])
def test_portable_preflight_rejects_even_empty_sidecars(tmp_path, suffix, error):
    path = tmp_path / "backup.sqlite"
    with closing(sqlite3.connect(path)) as db:
        db.execute("CREATE TABLE cursors(wallet)")
    path.with_name(path.name + suffix).touch()
    with pytest.raises(ValueError, match=error):
        service.check_snapshot(path, [])
