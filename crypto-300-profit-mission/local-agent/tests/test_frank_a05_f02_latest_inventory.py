"""A05/F02 regression: never mistake old, partial or absent RPC data for live holdings."""
from datetime import datetime, timezone
import json

import pytest

from mission_agent.mission_control.wallet_chain_capture import (
    SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM, capture_owner,
)
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_inventory_snapshot import (
    _fingerprint, latest_inventory,
)
from test_frank_a04_a05_chain_capture import (
    OWNER_A, MINT, ATA_A, ATA_B, entry, response, request_factory, pk,
)

NOW = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)
NEXT = pk(21)


def _snapshot(spl, token22, *, slots=(100, 101),
              stamp="2026-10-14T11:59:00+00:00", fail=None):
    request, _ = request_factory(
        response(slots[0], spl), response(slots[1], token22), fail=fail)
    snap = capture_owner(OWNER_A, request)
    snap["observed_at_utc"] = stamp
    snap["capture_sha256"] = _fingerprint(snap)
    return snap


def _read(path, mints, *, now=NOW, age=300):
    st = WalletEvidenceStore(path, read_only=True)
    try:
        return latest_inventory(st, wallet=OWNER_A, mints=mints,
                                as_of_utc=now, max_age_seconds=age)
    finally:
        st.close()


def test_latest_complete_absent_does_not_resurrect_old_positive(tmp_path):
    path = tmp_path / "research.sqlite"
    old = _snapshot(
        [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM, amount="2500000")],
        [], slots=(100, 101), stamp="2026-10-14T11:55:00+00:00")
    newer = _snapshot([], [], slots=(220, 221))
    db = WalletEvidenceStore(path)
    try:
        db.capture_wallet(old)
        db.capture_wallet(newer)
    finally:
        db.close()
    result = _read(path, [MINT])
    assert result["selected_capture_sha256"] == newer["capture_sha256"]
    assert result["slot_max"] == 221
    assert result["dual_program_queries_observed_non_atomic"]
    assert result["status_counts"] == {"ABSENT_IN_LATEST_DUAL_PROGRAM_SCAN": 1}
    row = result["mints"][0]
    assert row["observed_raw_amount"] is None
    assert not row["historical_sale_confirmed"]
    assert row["current_live_balance_verified"] is False
    assert result["wallet_nav_usd"] is None


def test_newest_partial_must_not_fall_back_to_older_complete(tmp_path):
    path = tmp_path / "research.sqlite"
    old = _snapshot(
        [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM)], [],
        slots=(100, 101), stamp="2026-10-14T11:54:00+00:00")
    newest = _snapshot([], [], slots=(301, 302), fail=TOKEN_2022_PROGRAM)
    db = WalletEvidenceStore(path)
    try:
        db.capture_wallet(old)
        db.capture_wallet(newest)
    finally:
        db.close()
    result = _read(path, [MINT])
    assert result["selected_capture_sha256"] == newest["capture_sha256"]
    assert result["mints"][0]["status"] == "UNKNOWN_MISSING_PROGRAM"
    assert result["mints"][0]["observed_raw_amount"] is None
    assert not result["dual_program_queries_observed_non_atomic"]


def test_multiple_accounts_observed_but_nonatomic_and_no_pnl(tmp_path):
    path = tmp_path / "research.sqlite"
    src = _snapshot(
        [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM, amount="1000000")],
        [entry(OWNER_A, MINT, ATA_B, TOKEN_2022_PROGRAM, amount="2000000")],
    )
    db = WalletEvidenceStore(path)
    try:
        assert db.capture_wallet(src)
    finally:
        db.close()
    result = _read(path, [MINT, NEXT])
    row = result["mints"][0]
    assert row["status"] == "OBSERVED_IN_DUAL_PROGRAM_SCAN_NON_ATOMIC"
    assert row["observed_raw_amount"] == "3000000"
    assert len(row["token_accounts"]) == 2
    assert row["realized_pnl_usd"] is None
    assert result["same_slot_atomic"] is False
    assert result["mints"][1]["status"] == "ABSENT_IN_LATEST_DUAL_PROGRAM_SCAN"
    assert result["current_live_portfolio_verified"] is False


def test_new_partial_with_mint_is_not_mislabeled_whole_wallet_balance(tmp_path):
    path = tmp_path / "research.sqlite"
    src = _snapshot(
        [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM)],
        [], fail=TOKEN_2022_PROGRAM)
    db = WalletEvidenceStore(path)
    try:
        db.capture_wallet(src)
    finally:
        db.close()
    result = _read(path, [MINT])
    assert result["mints"][0]["status"] == "PARTIAL_PROGRAM_OBSERVED_NOT_WHOLE_BALANCE"
    assert result["mints"][0]["observed_raw_amount"] == "1000000"
    assert not result["dual_program_queries_observed_non_atomic"]


def test_stale_capture_does_not_qualify_as_current(tmp_path):
    path = tmp_path / "research.sqlite"
    src = _snapshot([entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM)], [],
                    stamp="2026-10-14T11:30:00+00:00")
    db = WalletEvidenceStore(path)
    try:
        db.capture_wallet(src)
    finally:
        db.close()
    result = _read(path, [MINT])
    assert not result["capture_fresh"]
    assert result["capture_age_seconds"] == 1800
    assert result["mints"][0]["status"] == "STALE_SNAPSHOT"
    assert result["mints"][0]["observed_raw_amount"] is None


def test_no_snapshot_is_unknown_not_balance_zero(tmp_path):
    path = tmp_path / "research.sqlite"
    db = WalletEvidenceStore(path)
    db.close()
    result = _read(path, [MINT])
    assert result["mints"][0]["status"] == "NO_CAPTURE"
    assert result["mints"][0]["observed_raw_amount"] is None
    assert result["selected_capture_sha256"] is None


def test_snapshot_content_tampering_is_detected_before_display(tmp_path):
    path = tmp_path / "research.sqlite"
    src = _snapshot([entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM)], [])
    db = WalletEvidenceStore(path)
    try:
        db.capture_wallet(src)
        with db.db:
            db.db.execute(
                "UPDATE evidence_documents SET payload_json=? "
                "WHERE kind='ACCOUNT_CAPTURE'",
                (json.dumps({**src, "slot_max": 999999}),))
    finally:
        db.close()
    with pytest.raises(ValueError, match="CAPTURE_SOURCE_HASH_MISMATCH"):
        _read(path, [MINT])


def test_32_explicit_targets_are_distinct_no_hardcoded_persons(tmp_path):
    path = tmp_path / "research.sqlite"
    db = WalletEvidenceStore(path)
    db.close()
    mints = [pk(i) for i in range(30, 62)]
    result = _read(path, mints)
    assert result["target_mint_count"] == 32
    assert result["target_count_equals_32"]
    assert len(result["mints"]) == 32
    assert all(p["observed_raw_amount"] is None for p in result["mints"])


@pytest.mark.parametrize("mints", [[], [MINT, MINT], ["not-an-address"], "some-string"])
def test_invalid_target_input_does_not_query_or_guess(tmp_path, mints):
    path = tmp_path / "research.sqlite"
    db = WalletEvidenceStore(path)
    db.close()
    with pytest.raises(ValueError, match="TARGET_MINTS_INVALID"):
        _read(path, mints)


def test_manual_cli_reuses_source_readonly_and_does_not_write_sidecar(tmp_path, capsys):
    from scripts.frank_research_latest_inventory import main
    from datetime import datetime, timezone
    import hashlib

    path = tmp_path / "research.sqlite"
    src = _snapshot(
        [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM)], [],
        slots=(100, 101),
        stamp=datetime.now(timezone.utc).isoformat(),
    )
    db = WalletEvidenceStore(path)
    try:
        db.capture_wallet(src)
    finally:
        db.close()
    file = tmp_path / "mints.json"
    file.write_text(json.dumps([MINT]), encoding="utf-8")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    assert main([
        "--wallet", OWNER_A,
        "--mint-file", str(file),
        "--sidecar", str(path),
    ]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["kind"] == "RESEARCH_OWNER_LATEST_CAPTURE_INVENTORY_NOT_LIVE"
    assert result["selected_capture_sha256"] == src["capture_sha256"]
    assert result["mints"][0]["status"] == "OBSERVED_IN_DUAL_PROGRAM_SCAN_NON_ATOMIC"
    assert result["mints"][0]["usd_value"] is None
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_manual_cli_missing_archive_does_not_create_empty_sqlite(tmp_path):
    from scripts.frank_research_latest_inventory import main

    absent = tmp_path / "missing-research.sqlite"
    file = tmp_path / "mints.json"
    file.write_text(json.dumps([MINT]), encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="SIDE_CAR_NOT_FOUND"):
        main([
            "--wallet", OWNER_A, "--mint-file", str(file),
            "--sidecar", str(absent),
        ])
    assert not absent.exists()
