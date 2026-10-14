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


def _two_rpc_failures(*, stamp):
    def unavailable(method, params):
        raise TimeoutError("provider unavailable")
    failed = capture_owner(OWNER_A, unavailable)
    assert failed["status"] == "PARTIAL_SOURCE"
    assert failed["slot_max"] is None and failed["slot_min"] is None
    assert failed["program_coverage"] == []
    assert len(failed["missing"]) == 2
    failed["observed_at_utc"] = stamp
    failed["capture_sha256"] = _fingerprint(failed)
    return failed


def test_more_than_100_out_of_order_imports_never_resurrect_old_balance(tmp_path):
    path = tmp_path / "old-history-import-after-latest.sqlite"
    # Truly latest chain slot is archived FIRST, then >100 older slot
    # snapshots are imported. A rowid DESC LIMIT 100 incorrectly returns
    # one of the old positive quantities instead of the latest absence.
    most_recent = _snapshot([], [], slots=(1000, 1001),
                            stamp="2026-10-14T11:59:00+00:00")
    db = WalletEvidenceStore(path)
    try:
        assert db.capture_wallet(most_recent)
        for slot in range(180, 300):
            old = _snapshot(
                [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM,
                       amount="2500000")], [],
                slots=(slot, slot + 1),
                stamp="2026-10-14T11:58:00+00:00",
            )
            assert db.capture_wallet(old)
        # Preserve the legacy bounded history API unchanged; prove why it
        # cannot be used to select the latest chain slot.
        assert len(db.read_wallet_captures(OWNER_A, limit=100)) == 100
        assert most_recent["capture_sha256"] not in {
            r["capture_sha256"]
            for r in db.read_wallet_captures(OWNER_A, limit=100)
        }
    finally:
        db.close()
    result = _read(path, [MINT])
    assert result["capture_candidates_examined"] == 121
    assert result["selected_capture_sha256"] == most_recent["capture_sha256"]
    assert result["slot_max"] == 1001
    assert result["mints"][0]["status"] == "ABSENT_IN_LATEST_DUAL_PROGRAM_SCAN"
    assert result["mints"][0]["observed_raw_amount"] is None
    assert result["mints"][0]["historical_sale_confirmed"] is False


def test_old_double_rpc_timeout_does_not_poison_later_healthy_capture(tmp_path):
    path = tmp_path / "failed-source-then-healthy.sqlite"
    old_failure = _two_rpc_failures(stamp="2026-10-14T11:57:00+00:00")
    healthy = _snapshot([], [], slots=(1000, 1001),
                        stamp="2026-10-14T11:59:00+00:00")
    db = WalletEvidenceStore(path)
    try:
        assert db.capture_wallet(old_failure)
        assert db.capture_wallet(healthy)
    finally:
        db.close()
    result = _read(path, [MINT])
    assert result["capture_candidates_examined"] == 2
    assert result["selected_capture_sha256"] == healthy["capture_sha256"]
    assert result["source_attempt_failed_no_slot"] is False
    assert result["slot_max"] == 1001
    assert result["mints"][0]["status"] == "ABSENT_IN_LATEST_DUAL_PROGRAM_SCAN"
    assert result["mints"][0]["observed_raw_amount"] is None


def test_latest_double_rpc_timeout_masks_older_healthy_balance(tmp_path):
    path = tmp_path / "healthy-then-failed-source.sqlite"
    healthy = _snapshot(
        [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM,
               amount="2500000")], [],
        slots=(1000, 1001), stamp="2026-10-14T11:57:00+00:00",
    )
    newest_failure = _two_rpc_failures(stamp="2026-10-14T11:59:00+00:00")
    db = WalletEvidenceStore(path)
    try:
        assert db.capture_wallet(healthy)
        assert db.capture_wallet(newest_failure)
    finally:
        db.close()
    result = _read(path, [MINT])
    assert result["selected_capture_sha256"] == newest_failure["capture_sha256"]
    assert result["capture_observed_at_utc"] == newest_failure["observed_at_utc"]
    assert result["source_attempt_failed_no_slot"] is True
    assert result["source_observation_status"] == "PARTIAL_SOURCE"
    assert result["slot_min"] is None and result["slot_max"] is None
    assert result["both_programs_observed"] is False
    assert result["mints"][0]["status"] == "SOURCE_ATTEMPT_FAILED_NO_SLOT"
    assert result["mints"][0]["observed_raw_amount"] is None
    assert result["wallet_nav_usd"] is None
    assert not result["current_live_portfolio_verified"]


def test_out_of_order_import_of_older_double_failure_cannot_override_new_health(tmp_path):
    path = tmp_path / "healthy-then-archived-old-failure.sqlite"
    healthy = _snapshot(
        [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM, amount="500000")],
        [], slots=(1200, 1201), stamp="2026-10-14T11:59:00+00:00",
    )
    old_failure = _two_rpc_failures(stamp="2026-10-14T11:56:00+00:00")
    db = WalletEvidenceStore(path)
    try:
        db.capture_wallet(healthy)
        db.capture_wallet(old_failure)
    finally:
        db.close()
    result = _read(path, [MINT])
    assert result["selected_capture_sha256"] == healthy["capture_sha256"]
    assert result["slot_max"] == 1201
    assert result["source_attempt_failed_no_slot"] is False
    assert result["mints"][0]["observed_raw_amount"] == "500000"


def test_stale_latest_unslotted_attempt_cannot_replay_old_positive(tmp_path):
    path = tmp_path / "stale-failed-latest.sqlite"
    healthy = _snapshot(
        [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM, amount="100")],
        [], slots=(1000, 1001), stamp="2026-10-14T11:10:00+00:00",
    )
    failed = _two_rpc_failures(stamp="2026-10-14T11:20:00+00:00")
    db = WalletEvidenceStore(path)
    try:
        db.capture_wallet(healthy)
        db.capture_wallet(failed)
    finally:
        db.close()
    result = _read(path, [MINT])
    assert result["source_attempt_failed_no_slot"]
    assert not result["capture_fresh"]
    assert result["mints"][0]["status"] == "SOURCE_ATTEMPT_FAILED_NO_SLOT"
    assert result["mints"][0]["observed_raw_amount"] is None


@pytest.mark.parametrize("corruption", [
    "duplicate_spl",
    "duplicate_token_2022",
    "unsupported_program",
    "missing_entry_not_dict",
    "missing_reason_field",
    "unexpected_reason",
    "missing_error_type_field",
    "invalid_error_type",
    "unexpected_error_metadata",
    "nonempty_account_coverage",
    "nonempty_mints",
    "account_count_nonzero",
    "mint_count_nonzero",
    "same_slot_atomic",
    "unverified_wallet_total_contradiction",
    "extra_missing_program",
])
def test_malformed_slotless_failures_are_rejected_not_classified_as_dual_failure(
        tmp_path, corruption):
    import copy

    path = tmp_path / ("slotless-" + corruption + ".sqlite")
    healthy = _snapshot(
        [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM,
               amount="2500000")], [],
        slots=(1000, 1001), stamp="2026-10-14T11:57:00+00:00")
    bad = copy.deepcopy(_two_rpc_failures(
        stamp="2026-10-14T11:59:00+00:00"))
    if corruption == "duplicate_spl":
        bad["missing"][1] = copy.deepcopy(bad["missing"][0])
    elif corruption == "duplicate_token_2022":
        bad["missing"][0] = copy.deepcopy(bad["missing"][1])
    elif corruption == "unsupported_program":
        bad["missing"][1]["program_id"] = OWNER_A
    elif corruption == "missing_entry_not_dict":
        bad["missing"][1] = "TOKEN_ACCOUNT_QUERY_UNAVAILABLE"
    elif corruption == "missing_reason_field":
        del bad["missing"][0]["reason"]
    elif corruption == "unexpected_reason":
        bad["missing"][0]["reason"] = "TOKEN_ACCOUNT_NO_BALANCE"
    elif corruption == "missing_error_type_field":
        del bad["missing"][1]["error_type"]
    elif corruption == "invalid_error_type":
        bad["missing"][0]["error_type"] = "Timeout Error"
    elif corruption == "unexpected_error_metadata":
        bad["missing"][0]["endpoint"] = "untrusted"
    elif corruption == "nonempty_account_coverage":
        bad["program_coverage"] = [{"program_id": SPL_TOKEN_PROGRAM}]
    elif corruption == "nonempty_mints":
        bad["mints"] = [{"mint": MINT}]
    elif corruption == "account_count_nonzero":
        bad["account_count"] = 1
    elif corruption == "mint_count_nonzero":
        bad["mint_count_observed"] = 1
    elif corruption == "same_slot_atomic":
        bad["same_slot_atomic"] = True
    elif corruption == "unverified_wallet_total_contradiction":
        bad["wallet_total_balance_verified"] = True
    elif corruption == "extra_missing_program":
        bad["missing"].append(copy.deepcopy(bad["missing"][0]))
    bad["capture_sha256"] = _fingerprint(bad)
    db = WalletEvidenceStore(path)
    try:
        assert db.capture_wallet(healthy)
        # The archive's write method checks cryptographic integrity, not
        # meaning. The read projection must reject the altered semantics.
        assert db.capture_wallet(bad)
    finally:
        db.close()
    with pytest.raises(ValueError, match="OWNER_CAPTURE_SLOTLESS_PROGRAM_EVIDENCE_INVALID"):
        _read(path, [MINT])


def test_true_spl_and_token2022_double_failure_preserves_source_and_null_amount(tmp_path):
    path = tmp_path / "actual-shaped-double-timeout.sqlite"
    healthy = _snapshot(
        [entry(OWNER_A, MINT, ATA_A, SPL_TOKEN_PROGRAM, amount="900000")],
        [], slots=(1000, 1001), stamp="2026-10-14T11:57:00+00:00")
    failure = _two_rpc_failures(stamp="2026-10-14T11:59:00+00:00")
    assert {item["program_id"] for item in failure["missing"]} == {
        SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM}
    assert all(item["reason"] == "TOKEN_ACCOUNT_QUERY_UNAVAILABLE"
               and item["error_type"] == "TimeoutError"
               for item in failure["missing"])
    db = WalletEvidenceStore(path)
    try:
        db.capture_wallet(healthy)
        db.capture_wallet(failure)
    finally:
        db.close()
    result = _read(path, [MINT])
    assert result["selected_capture_sha256"] == failure["capture_sha256"]
    assert result["source_attempt_failed_no_slot"] is True
    assert result["status_counts"] == {"SOURCE_ATTEMPT_FAILED_NO_SLOT": 1}
    assert result["mints"][0]["observed_raw_amount"] is None
    assert result["mints"][0]["historical_sale_confirmed"] is False
    assert result["slot_max"] is None


def test_real_slotless_timeout_failure_before_health_is_not_permanent_poison(tmp_path):
    path = tmp_path / "error-before-health.sqlite"
    old = _two_rpc_failures(stamp="2026-10-14T11:57:00+00:00")
    healthy = _snapshot([], [], slots=(1100, 1101),
                        stamp="2026-10-14T11:59:00+00:00")
    db = WalletEvidenceStore(path)
    try:
        db.capture_wallet(old)
        db.capture_wallet(healthy)
    finally:
        db.close()
    result = _read(path, [MINT])
    assert result["selected_capture_sha256"] == healthy["capture_sha256"]
    assert result["source_attempt_failed_no_slot"] is False
    assert result["mints"][0]["status"] == "ABSENT_IN_LATEST_DUAL_PROGRAM_SCAN"
    assert result["mints"][0]["observed_raw_amount"] is None
