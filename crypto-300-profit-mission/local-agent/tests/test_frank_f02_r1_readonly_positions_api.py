"""F02-R1: localhost isolated API consumes pinned original-wire + read-only Sidecar."""
from datetime import datetime, timedelta, timezone
import copy
import http.client
from http.server import ThreadingHTTPServer
import json
import sqlite3
from pathlib import Path
import threading

import pytest

from mission_agent.mission_control.wallet_chain_capture import (
    SPL_TOKEN_PROGRAM, TOKEN_2022_PROGRAM, capture_owner,
)
from mission_agent.mission_control.wallet_evidence_store import WalletEvidenceStore
from mission_agent.mission_control.wallet_inventory_snapshot import _fingerprint
from mission_agent.mission_control.wallet_full_rpc_evidence import collect_owner_full_receipts
from scripts.frank_f02_readonly_positions_api import (
    REGISTRY, ROSTER, ResearchPositions, make_handler, main,
)
from scripts.frank_reconcile_frozen32_offline import load_frozen_roster
from test_frank_a04_a05_chain_capture import entry, pk, request_factory, response


WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
STAMP = datetime(2026, 10, 14, 15, 54, tzinfo=timezone.utc)


def _wire(n, slot, data):
    return json.dumps({
        "jsonrpc": "2.0", "id": n,
        "result": {"context": {"slot": slot}, "value": data},
    }).encode()


@pytest.fixture
def source(tmp_path):
    r = load_frozen_roster(ROSTER, WALLET)["records"]
    first, second = r[0]["mint"], r[1]["mint"]
    spl = _wire(1, 456895319, [
        entry(WALLET, first, pk(94), SPL_TOKEN_PROGRAM, amount="9007199254740993"),
        entry(WALLET, first, pk(95), SPL_TOKEN_PROGRAM, amount="7"),
    ])
    t22 = _wire(2, 456895320, [
        entry(WALLET, second, pk(96), TOKEN_2022_PROGRAM, amount="0"),
    ])
    bundle = collect_owner_full_receipts(
        wallet=WALLET, evidence_root=tmp_path / "bundle",
        read_raw=lambda m, p, ident: spl if ident == 1 else t22,
        observed_at_utc=STAMP.isoformat())
    assert bundle["manifest"]["complete"]
    sidecar = tmp_path / "private-research.sqlite"
    store = WalletEvidenceStore(sidecar)
    try:
        store.capture_wallet(bundle["snapshot"])
    finally:
        store.close()
    return {
        "bundle": bundle["bundle"],
        "sidecar": sidecar,
        "capture": bundle["snapshot"],
        "first": first, "second": second,
    }


@pytest.fixture
def service(source):
    return ResearchPositions(
        registry=REGISTRY, person_id="frank", wallet=WALLET,
        roster=ROSTER, bundle=Path(source["bundle"]),
        sidecar=source["sidecar"], max_age_seconds=300)


def test_f02_live_aged_owner_snapshot_preserves_exact_amount_and_two_slots(
        service, source):
    view = service.positions(as_of_utc=STAMP + timedelta(seconds=30))
    assert view["readiness"] == "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
    assert view["target_mint_count"] == 32
    assert view["slot_min"] == 456895319
    assert view["slot_max"] == 456895320
    assert view["same_slot_atomic"] is False
    assert view["verified_full_wire_capture_sha256"] == source["capture"]["capture_sha256"]
    assert view["latest_capture_sha256"] == source["capture"]["capture_sha256"]
    assert view["signals_allowed"] is False and view["trades_allowed"] is False
    row = view["mints"][0]
    assert row["state"] == "OPEN_ACCOUNT_NONZERO"
    assert row["observed_raw_amount"] == "9007199254741000"
    assert len(row["token_accounts"]) == 2
    assert row["observed_quantity"] is not None
    assert view["mints"][1]["state"] == "OPEN_ACCOUNT_ZERO"
    assert view["mints"][1]["observed_raw_amount"] == "0"
    assert view["mints"][2]["state"] == "NO_OPEN_ACCOUNT_OBSERVED"
    assert view["mints"][2]["observed_raw_amount"] is None
    assert view["state_counts"] == {
        "OPEN_ACCOUNT_NONZERO": 1, "OPEN_ACCOUNT_ZERO": 1,
        "NO_OPEN_ACCOUNT_OBSERVED": 30}
    assert all(row["value_usd"] is None and row["realized_pnl_usd"] is None
               for row in view["mints"])


def test_f02_stale_archive_never_reuses_positive_amount(service):
    view = service.positions(as_of_utc=STAMP + timedelta(seconds=301))
    assert view["readiness"] == "STALE_ARCHIVED_SOURCE"
    assert view["capture_fresh"] is False
    assert view["state_counts"] == {"SOURCE_UNAVAILABLE": 32}
    assert all(row["observed_raw_amount"] is None and
               row["observed_quantity"] is None and not row["token_accounts"]
               for row in view["mints"])


def test_f02_no_archive_is_not_empty_wallet(tmp_path, source):
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(FileNotFoundError, match="SIDE_CAR_NOT_FOUND"):
        ResearchPositions(
            registry=REGISTRY, person_id="frank", wallet=WALLET,
            roster=ROSTER, bundle=Path(source["bundle"]),
            sidecar=missing, max_age_seconds=300)
    assert not missing.exists()


def test_f02_newer_unsupported_complete_capture_cannot_be_called_verified(
        service, source):
    newest = copy.deepcopy(source["capture"])
    newest["slot_min"] += 5
    newest["slot_max"] += 5
    newest["observed_at_utc"] = (STAMP + timedelta(seconds=10)).isoformat()
    newest["capture_sha256"] = _fingerprint(newest)
    st = WalletEvidenceStore(source["sidecar"])
    try:
        st.capture_wallet(newest)
    finally:
        st.close()
    view = service.positions(as_of_utc=STAMP + timedelta(seconds=40))
    assert view["latest_capture_sha256"] == newest["capture_sha256"]
    assert view["readiness"] == "LATEST_SOURCE_NOT_WIRE_VERIFIED"
    assert view["state_counts"] == {"SOURCE_UNAVAILABLE": 32}
    assert view["mints"][0]["observed_raw_amount"] is None


def test_f02_latest_two_rpc_failures_never_resurrect_old_good_balance(
        service, source):
    def fail(method, params):
        raise TimeoutError("no connection")
    failed = capture_owner(WALLET, fail)
    failed["observed_at_utc"] = (STAMP + timedelta(seconds=25)).isoformat()
    failed["capture_sha256"] = _fingerprint(failed)
    st = WalletEvidenceStore(source["sidecar"])
    try:
        st.capture_wallet(failed)
    finally:
        st.close()
    view = service.positions(as_of_utc=STAMP + timedelta(seconds=35))
    assert view["latest_capture_sha256"] == failed["capture_sha256"]
    assert view["readiness"] == "LATEST_CAPTURE_ATTEMPT_FAILED"
    assert view["source_attempt_failed_no_slot"] is True
    assert view["mints"][0]["observed_raw_amount"] is None
    assert view["state_counts"] == {"SOURCE_UNAVAILABLE": 32}


def test_f02_rejects_incorrect_person_wallet_and_bundle(tmp_path, source):
    for person, wallet in [("unknown", WALLET), ("frank", pk(18))]:
        with pytest.raises((KeyError, ValueError)):
            ResearchPositions(registry=REGISTRY, person_id=person,
                wallet=wallet, roster=ROSTER, bundle=Path(source["bundle"]),
                sidecar=source["sidecar"], max_age_seconds=300)
    other = copy.deepcopy(source["capture"])
    other["wallet"] = pk(88)
    with pytest.raises(ValueError, match="FROZEN_32_MINT_ROSTER_INVALID"):
        load_frozen_roster(ROSTER, pk(88))


def test_f02_actual_loopback_http_api_only_exposes_bound_32(service):
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service))
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        def get(path, host=None):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            headers = {} if host is None else {"Host": host}
            conn.request("GET", path, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()
            result = (resp.status, dict(resp.getheaders()), json.loads(raw))
            conn.close()
            return result
        status, headers, data = get("/api/research/positions?person_id=frank")
        assert status == 200
        assert headers["Cache-Control"] == "no-store"
        assert "Access-Control-Allow-Origin" not in headers
        assert data["person_id"] == "frank" and data["target_mint_count"] == 32
        assert data["verified_pnl_usd"] is None
        assert get("/api/research/positions?person_id=unknown")[0] == 400
        assert get("/api/research/positions?wallet=" + pk(88))[0] == 400
        assert get("/api/candidates")[0] == 404
        assert get("/api/research/positions", host="example.com")[0] == 403
    finally:
        server.shutdown()
        server.server_close()
        t.join(timeout=5)


def test_f02_plan_only_no_sidecar_read_and_no_listener(source, capsys):
    assert main(["--bundle", source["bundle"],
                 "--sidecar", "/definitely/absent/nonexistent.sqlite"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["status"] == "PLAN_ONLY"
    assert doc["sidecar_opened"] is False
    assert doc["network_invoked"] is False


def test_f02_readonly_sidecar_bytes_unchanged(source, service):
    before = source["sidecar"].read_bytes()
    view = service.positions(as_of_utc=STAMP + timedelta(seconds=60))
    assert view["readiness"] == "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
    assert source["sidecar"].read_bytes() == before



def _archive_partial(sidecar, *, slot, stamp):
    request, calls = request_factory(
        response(slot, []), response(slot, []), fail=SPL_TOKEN_PROGRAM)
    partial = capture_owner(WALLET, request)
    assert {x["program_id"] for x in partial["missing"]} == {SPL_TOKEN_PROGRAM}
    assert partial["status"] == "PARTIAL_SOURCE"
    assert partial["slot_max"] == slot
    assert len(calls) == 2
    partial["observed_at_utc"] = stamp.isoformat()
    partial["capture_sha256"] = _fingerprint(partial)
    store = WalletEvidenceStore(sidecar)
    try:
        assert store.capture_wallet(partial)
    finally:
        store.close()
    return partial


def _actual_http(service, *, as_of, monkeypatch):
    selected = service.positions
    monkeypatch.setattr(service, "positions", lambda: selected(as_of_utc=as_of))
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/api/research/positions?person_id=frank")
        res = conn.getresponse()
        status = res.status
        doc = json.loads(res.read())
        conn.close()
        return status, doc
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("lower_or_higher_slot", [456895318, 456895321])
def test_later_partial_attempt_fails_closed_even_if_its_slot_is_lower(
        service, source, monkeypatch, lower_or_higher_slot):
    later = _archive_partial(
        source["sidecar"], slot=lower_or_higher_slot,
        stamp=STAMP + timedelta(seconds=10))
    status, body = _actual_http(
        service, as_of=STAMP + timedelta(seconds=20), monkeypatch=monkeypatch)
    assert status == 200
    assert body["readiness"] == "LATEST_CAPTURE_ATTEMPT_FAILED"
    assert body["archive_observation_usable"] is False
    assert body["latest_attempt_source_status"] == "PARTIAL_SOURCE"
    assert body["latest_attempt_capture_sha256"] == later["capture_sha256"]
    assert body["latest_attempt_slot_max"] == lower_or_higher_slot
    assert body["latest_attempt_missing_program_ids"] == [SPL_TOKEN_PROGRAM]
    assert body["latest_capture_sha256"] == source["capture"]["capture_sha256"]
    assert body["target_mint_count"] == 32
    assert body["state_counts"] == {"SOURCE_UNAVAILABLE": 32}
    assert all(item["observed_raw_amount"] is None
               and item["observed_quantity"] is None
               and item["token_accounts"] == []
               for item in body["mints"])


def test_earlier_partial_backfill_does_not_mask_newer_verified_observation(
        service, source):
    partial = _archive_partial(
        source["sidecar"], slot=456895318,
        stamp=STAMP - timedelta(seconds=10))
    result = service.positions(as_of_utc=STAMP + timedelta(seconds=20))
    assert result["readiness"] == "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
    assert result["latest_attempt_capture_sha256"] == source["capture"]["capture_sha256"]
    assert result["latest_attempt_capture_sha256"] != partial["capture_sha256"]
    assert result["mints"][0]["observed_raw_amount"] == "9007199254741000"


def test_history_import_of_older_slots_preserves_latest_source(service, source):
    older = copy.deepcopy(source["capture"])
    older["slot_min"] -= 50
    older["slot_max"] -= 50
    older["observed_at_utc"] = (STAMP - timedelta(seconds=30)).isoformat()
    older["capture_sha256"] = _fingerprint(older)
    store = WalletEvidenceStore(source["sidecar"])
    try:
        assert store.capture_wallet(older)
    finally:
        store.close()
    result = service.positions(as_of_utc=STAMP + timedelta(seconds=20))
    assert result["readiness"] == "FRESH_VERIFIED_ARCHIVED_OBSERVATION"
    assert result["latest_attempt_capture_sha256"] == source["capture"]["capture_sha256"]
    assert result["mints"][0]["observed_raw_amount"] == "9007199254741000"


def test_later_unverified_full_attempt_with_lower_slot_masked(service, source):
    low = copy.deepcopy(source["capture"])
    low["slot_min"] -= 10
    low["slot_max"] -= 10
    low["observed_at_utc"] = (STAMP + timedelta(seconds=10)).isoformat()
    low["capture_sha256"] = _fingerprint(low)
    st = WalletEvidenceStore(source["sidecar"])
    try:
        assert st.capture_wallet(low)
    finally:
        st.close()
    result = service.positions(as_of_utc=STAMP + timedelta(seconds=20))
    assert result["readiness"] == "LATEST_SOURCE_NOT_WIRE_VERIFIED"
    assert result["latest_attempt_capture_sha256"] == low["capture_sha256"]
    assert result["mints"][0]["observed_raw_amount"] is None


def test_broken_readonly_sqlite_schema_returns_fixed_http_503(
        service, source, monkeypatch):
    db = sqlite3.connect(source["sidecar"])
    try:
        db.execute("DROP TABLE evidence_documents")
        db.commit()
    finally:
        db.close()
    status, result = _actual_http(
        service, as_of=STAMP + timedelta(seconds=20), monkeypatch=monkeypatch)
    assert status == 503
    assert result == {"status": "RESEARCH_SOURCE_UNAVAILABLE"}
