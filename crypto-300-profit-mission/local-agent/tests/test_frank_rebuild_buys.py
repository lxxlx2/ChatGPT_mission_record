import base64
from datetime import datetime, timezone
import gzip
import hashlib
from http.server import HTTPServer
import json
import time
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from mission_agent.frank.parser import WSOL
from mission_agent.frank.rpc import WALLET
from mission_agent.meme.holder_ranks import _b58
from mission_agent.mission_control.frank_buys import read_buys
from mission_agent.mission_control.server import DashboardState, Handler
from mission_agent.signals.buy_admission import BACKPACK_MINT, qualification
from mission_agent.signals.classifier import classify
from mission_agent.signals.engine import Engine
from mission_agent.signals.historical_usd_tick import capture_url
from mission_agent.signals.policy import USDC, load_policy
from mission_agent.signals.store import Ledger
from test_frank_fm import tx
from test_frank_local_signals import FIXTURES


AS_OF = 1796000000
MINT, BP, UNKNOWN = [_b58(bytes([n])*32) for n in (2, 3, 4)]


def config(path, *, exclude=False, as_of=AS_OF):
    path.write_text(json.dumps({"version": 1, "records": [
        {"chain": "solana", "mint": mint, "name": name, "status": status,
         "source": "synthetic fixture only", "observed_at": as_of-1000}
        for mint, name, status in (
            (MINT, "样例 Meme", "EXCLUDED" if exclude else "VERIFIED_MEME"),
            (BP, "BP fixture", "EXCLUDED"),
        )
    ]}))


def put(ledger, number, *, mint=MINT, kind="buy", at=AS_OF-1, person="frank", quote=USDC, token_raw="1000000"):
    signature = _b58(number.to_bytes(64, "big"))
    raw = tx()
    if kind == "passive":
        raw = json.loads(gzip.decompress((FIXTURES/"token.json.gz").read_bytes()))
    else:
        for side in ("preTokenBalances", "postTokenBalances"):
            raw["meta"][side][0]["mint"] = mint
            raw["meta"][side][1]["mint"] = quote
        raw["meta"]["postTokenBalances"][0]["uiTokenAmount"]["amount"] = token_raw
        if kind == "failed":
            raw["meta"]["err"] = {"InstructionError": [0, {"Custom": 4}]}
        if kind == "sell":
            raw["meta"]["preTokenBalances"], raw["meta"]["postTokenBalances"] = (
                raw["meta"]["postTokenBalances"], raw["meta"]["preTokenBalances"])
    raw["blockTime"] = at
    event = classify(signature, raw, WALLET)
    raw_hash = event["evidence"]["raw_transaction_sha256"]
    if kind == "mismatched":
        raw_hash = "a"*64
    ledger.put(person,event,raw_hash,"fixture")
    return signature


def test_read_verified_wallet_facts_only(tmp_path):
    db, cfg = tmp_path/"db", tmp_path/"qualification.json"
    ledger = Ledger(db)
    config(cfg)
    good = put(ledger, 1)
    for i, kwargs in enumerate([
        {"mint": BP}, {"mint": UNKNOWN}, {"kind": "failed"}, {"kind": "passive"},
        {"kind": "sell"}, {"kind": "mismatched"}, {"person": "other"},
    ], 2):
        put(ledger, i, **kwargs)
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    result = read_buys(db,cfg,as_of=AS_OF)
    assert result["status"] == "LOCAL_EVIDENCE_ONLY"
    assert result["rows"] == [{"mint": MINT, "name": "样例 Meme", "signature": good,
                               "slot": 12, "at": AS_OF-1, "quantity": "1", "paid": "0.5", "currency": "USDC",
                               "spent_usd": None, "entry_price_usd": None}]
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
    assert read_buys(db,cfg,as_of=AS_OF,mint=BP)["rows"] == []
    assert read_buys(db,tmp_path/"missing",as_of=AS_OF)["status"] == "QUALIFICATION_UNAVAILABLE"


@pytest.mark.parametrize("case", ("bound_legacy", "corrupt_archive", "wrong_signature", "modern_failed"))
def test_dashboard_replays_only_bound_legacy_buy_evidence(tmp_path, case):
    prod, control = (tmp_path/name for name in ("production", "control"))
    archive = prod/"raw"
    archive.mkdir(parents=True)
    control.mkdir()
    cfg = control/"frank-buy-qualifications.json"
    now = int(time.time())
    config(cfg, as_of=now)
    db = prod/"forward.sqlite"
    ledger = Ledger(db)
    signature = _b58((1).to_bytes(64, "big"))
    raw = tx()
    raw["blockTime"] = now-1
    raw["transaction"]["signatures"] = [
        _b58((2).to_bytes(64, "big")) if case == "wrong_signature" else signature
    ]
    for field in ("preTokenBalances", "postTokenBalances"):
        raw["meta"][field][0]["mint"] = MINT
        raw["meta"][field][1]["mint"] = USDC
    event = classify(signature, raw, WALLET)
    raw_hash = event["evidence"]["raw_transaction_sha256"]
    if case != "modern_failed":
        for field in ("quote_legs", "route_amount_semantics", "route_intermediate_evidence_status"):
            del event["trade"][field]
    else:
        event["evidence"]["tx_err"] = "FAILED"
    assert ledger.put("frank", event, raw_hash, "must-not-choose-an-archive-location")
    if case == "corrupt_archive":
        raw["meta"]["fee"] += 1
    (archive/(signature+".json.gz")).write_bytes(gzip.compress(json.dumps(raw).encode()))

    assert read_buys(db, cfg, as_of=now)["rows"] == []
    indexed_body = ledger.db.execute("SELECT body FROM signatures").fetchone()[0]
    result = DashboardState(prod, control).frank_buys()
    if case == "bound_legacy":
        assert result["rows"] == [{"mint": MINT, "name": "样例 Meme", "signature": signature,
                                   "slot": 12, "at": now-1, "quantity": "1",
                                   "paid": "0.5", "currency": "USDC", "spent_usd": None, "entry_price_usd": None}]
    else:
        assert result["rows"] == []
    assert ledger.db.execute("SELECT body FROM signatures").fetchone()[0] == indexed_body
    assert ledger.db.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0

    # Exercise the same adapter through scanner reconciliation and the runner.
    import sqlite3
    from types import SimpleNamespace
    from scripts.accept_frank_rebuild import _wallet
    from mission_agent.signals.reconciliation import reconcile_snapshot
    snapshot = tmp_path / "snapshot.sqlite"
    with sqlite3.connect(snapshot) as copy:
        ledger.db.backup(copy)
        copy.execute("PRAGMA journal_mode=DELETE")
    ref = tmp_path / "independent.json"
    ref.write_text(json.dumps({
        "schema_version": 1, "chain": "solana", "commitment": "finalized",
        "complete": True, "start_slot": 12, "end_slot": 12, "finalized_through_slot": 12,
        "source_id": "independent_fixture", "capture_sha256": "a"*64,
        "person_id": "frank", "wallet": WALLET,
        "transactions": [{"signature": signature, "slot": 12, "expected_frank_buy": MINT,
                          "expectation_sha256": "b"*64}],
    }))
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    expected_hash = sha(snapshot)
    opts = (snapshot, expected_hash, ref, sha(ref))
    qualifications = (cfg, sha(cfg), now)
    ledger_result = reconcile_snapshot(*opts, scanner_source_id="scanner_test",
                                       buy_qualifications=qualifications)
    if case != "modern_failed":
        assert ledger_result["rows"][0]["buy_admission"]["reason"] == "LEGACY_BUY_ARCHIVE_UNAVAILABLE"
    result = reconcile_snapshot(*opts, scanner_source_id="scanner_test",
                                buy_qualifications=qualifications, buy_archive_root=control,
                                buy_legacy_archive_root=archive)
    buys = result["buy_admission"]
    kind = {"bound_legacy": "MATCHED_IN", "corrupt_archive": "UNRESOLVED",
            "wrong_signature": "UNRESOLVED", "modern_failed": "MISSED"}[case]
    assert buys["counts"][kind] == 1
    assert buys["chain_to_detection"]["percentile_method"] == "NEAREST_RANK"
    assert buys["chain_to_index"]["sample_count"] == (1 if case == "bound_legacy" else 0)
    assert buys["delivery_timing"] == "NOT_VERIFIED"
    args = SimpleNamespace(snapshot=snapshot, snapshot_sha256=expected_hash, reference=ref,
                           reference_sha256=sha(ref), scanner_source_id="scanner_test",
                           qualifications=cfg, qualifications_sha256=sha(cfg), qualification_as_of=now,
                           buy_archive_root=control, buy_legacy_archive_root=archive)
    summary = _wallet(args)
    assert summary["buy_admission"] == buys and "rows" not in summary
    assert sha(snapshot) == expected_hash
    bad = {"buy_archive_root": Path("relative"), "buy_legacy_archive_root": archive}
    for name, value in bad.items():
        with pytest.raises(ValueError, match="BUY_ARCHIVE_PATHS"):
            reconcile_snapshot(*opts, scanner_source_id="scanner_test", buy_qualifications=qualifications,
                               **{name: value})


def usd_observation(ledger, signature, asset, **values):
    wallet, slot, at, raw_hash = ledger.db.execute(
        "SELECT wallet,slot,block_time,raw_hash FROM signatures WHERE signature=?", (signature,)
    ).fetchone()
    return {"wallet": wallet, "signature": signature, "slot": slot, "block_time": at,
            "raw_hash": raw_hash, "mint": MINT, "quote_asset": asset, "source_at": at,
            "source": "fixture provider", "source_sha256": "a"*64, **values}


def write_usd_evidence(path, *observations):
    path.write_text(json.dumps({"version": 1, "records": observations}))


def test_dashboard_reads_bound_usd_evidence_without_writing_ledger(tmp_path):
    prod, control = tmp_path/"production", tmp_path/"control"
    prod.mkdir()
    control.mkdir()
    cfg = control/"frank-buy-qualifications.json"
    now = int(time.time())
    config(cfg, as_of=now)
    db = prod/"forward.sqlite"
    ledger = Ledger(db)
    usdc = put(ledger, 1, at=now-1)
    sol = put(ledger, 2, quote=WSOL, at=now-2, token_raw="2500000")
    unpriced = put(ledger, 3, at=now-3)
    evidence = control/"frank-buy-usd-evidence.json"
    write_usd_evidence(
        evidence,
        usd_observation(ledger, usdc, USDC, usd_per_quote_unit="0.983"),
        usd_observation(ledger, sol, "SOL", spent_usd="1.68"),
    )
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    rows = DashboardState(prod, control).frank_buys()["rows"]
    assert [(r["signature"], r["spent_usd"], r["entry_price_usd"]) for r in rows] == [
        (usdc, "0.4915", "0.4915"),
        (sol, "1.68", "0.672"),
        (unpriced, None, None),
    ]
    assert [(r["currency"], r["quantity"]) for r in rows] == [("USDC", "1"), ("SOL", "2.5"), ("USDC", "1")]
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before


def second_capture(asset, at, *prices, returned_at=None):
    stamp = datetime.fromtimestamp(at if returned_at is None else returned_at, timezone.utc)
    rows = [{"symbol": f"{asset}/USD", "base_asset": asset, "quote_asset": "USD",
             "price": price, "trade_id": f"FIXTURE{i}", "trade_ts": stamp.strftime("%Y-%m-%dT%H:%M:%S.1Z")}
            for i, price in enumerate(prices)]
    raw = json.dumps({"error": [], "result": {"count": len(rows), "trades": rows}}).encode()
    return {"asset": asset, "block_time": at, "source_url": capture_url(asset, at),
            "source_sha256": hashlib.sha256(raw).hexdigest(), "raw_base64": base64.b64encode(raw).decode()}


def test_same_second_usd_estimates_do_not_become_exact_fills_or_change_ledger(tmp_path):
    db, cfg, evidence = (tmp_path/name for name in ("ledger", "qualification.json", "prices.json"))
    ledger = Ledger(db)
    config(cfg)
    at = AS_OF-1
    usdc = put(ledger, 1, at=at)
    sol = put(ledger, 2, at=at, quote=WSOL, token_raw="2500000")
    reused = put(ledger, 3, at=at, token_raw="2000000")
    next_second = put(ledger, 4, at=at+1)
    routed = put(ledger, 5, at=at)
    event = json.loads(ledger.db.execute("SELECT body FROM signatures WHERE signature=?", (routed,)).fetchone()[0])
    event["trade"].update(route_intermediate_evidence_status="UNVERIFIED",
                          route_amount_semantics="GROSS_QUOTE_OUT_NOT_EXACT_FINAL_TARGET_COST",
                          route_intermediate_assets=[{"mint": UNKNOWN}])
    with ledger.db:
        ledger.db.execute("UPDATE signatures SET body=? WHERE signature=?", (json.dumps(event), routed))
    exact = put(ledger, 6, at=at)
    disputed = put(ledger, 7, at=at)
    overrides = [
        usd_observation(ledger, exact, USDC, spent_usd="0.41"),
        usd_observation(ledger, disputed, USDC, spent_usd="0.43"),
        usd_observation(ledger, disputed, USDC, spent_usd="0.42"),
    ]
    evidence.write_text(json.dumps({"version": 2, "records": overrides, "captures": [
        second_capture("SOL", at, "112.25"),
        second_capture("USDC", at, "0.987", "0.9870"),
    ]}))
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    rows = {r["signature"]: r for r in read_buys(db, cfg, as_of=AS_OF, usd_evidence_path=evidence)["rows"]}
    for key, spent, each in [(usdc, "0.4935", "0.4935"), (sol, "56.125", "22.45"), (reused, "0.4935", "0.24675")]:
        row = rows[key]
        assert row["spent_usd"] is row["entry_price_usd"] is None
        assert row["estimated_spent_usd"] == spent and row["estimated_entry_price_usd"] == each
        assert row["usd_estimate_basis"] == "PAYMENT_ASSET_MARKET_TRADE_SAME_SECOND"
        assert not {"source_url", "source_sha256", "raw_base64"} & row.keys()
    for key in [next_second, routed, disputed]:
        assert rows[key]["spent_usd"] is rows[key]["entry_price_usd"] is None
        assert "estimated_spent_usd" not in rows[key]
    assert rows[routed]["paid"] is None
    assert rows[exact]["spent_usd"] == "0.41" and "estimated_spent_usd" not in rows[exact]
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
    assert not ledger.db.execute("SELECT 1 FROM outbox").fetchone()


def test_ambiguous_wrong_or_untrusted_raw_receipt_leaves_usd_empty(tmp_path):
    db, cfg, evidence = (tmp_path/name for name in ("ledger", "qualification.json", "prices.json"))
    ledger = Ledger(db)
    config(cfg)
    at = AS_OF-1
    put(ledger, 1, at=at)
    valid = second_capture("USDC", at, "0.98")
    for captures in [
        [],
        [second_capture("SOL", at, "99")],
        [second_capture("USDC", at, "0.98", returned_at=at-1)],
        [second_capture("USDC", at, "0.98", "1.02")],
        [{**valid, "source_sha256": "0"*64}],
        [{**valid, "source_url": capture_url("USDC", at-1)}],
        [{**valid, "raw_base64": "err!"}],
        [valid, valid],
        [valid, {"asset": "USDC", "block_time": at}],
    ]:
        evidence.write_text(json.dumps({"version": 2, "records": [], "captures": captures}))
        row, = read_buys(db, cfg, as_of=AS_OF, usd_evidence_path=evidence)["rows"]
        assert row["spent_usd"] is row["entry_price_usd"] is None
        assert "estimated_spent_usd" not in row


@pytest.mark.parametrize("modifications", [
    {"wallet": UNKNOWN}, {"signature": "1"*64}, {"slot": 13}, {"block_time": AS_OF-2, "source_at": AS_OF-2},
    {"mint": UNKNOWN}, {"raw_hash": "b"*64}, {"quote_asset": "SOL"}, {"source_at": AS_OF-2},
    {"source_at": AS_OF}, {"source_sha256": "nohash"}, {"source": " "}, {"usd_per_quote_unit": "NaN"},
    {"usd_per_quote_unit": "-10"}, {"spent_usd": "100"},
])
def test_price_evidence_requires_exact_trade_asset_and_time(tmp_path, modifications):
    db, cfg, evidence = (tmp_path/name for name in ("ledger", "qualification.json", "prices.json"))
    config(cfg)
    ledger = Ledger(db)
    signature = put(ledger, 1)
    record = usd_observation(ledger, signature, USDC, usd_per_quote_unit="0.98")
    write_usd_evidence(evidence, {**record, **modifications})
    row, = read_buys(db, cfg, as_of=AS_OF, usd_evidence_path=evidence)["rows"]
    assert row["signature"] == signature and row["paid"] == "0.5"
    assert row["spent_usd"] is row["entry_price_usd"] is None


def test_changed_evidence_invalidates_cursor_and_duplicate_references_do_not_price_trade(tmp_path):
    db, cfg, evidence = (tmp_path/name for name in ("ledger", "qualification.json", "prices.json"))
    config(cfg)
    ledger = Ledger(db)
    signatures = [put(ledger, i) for i in range(1,32)]
    signature = signatures[-1]
    record = usd_observation(ledger, signature, USDC, usd_per_quote_unit="0.985")
    write_usd_evidence(evidence, record)
    page = read_buys(db, cfg, as_of=AS_OF, usd_evidence_path=evidence)
    assert page["rows"][0]["spent_usd"] == "0.4925"
    write_usd_evidence(evidence, record, {**record, "usd_per_quote_unit": "0.997"})
    with pytest.raises(ValueError, match="INVALID_OR_STALE_CURSOR"):
        read_buys(db, cfg, as_of=AS_OF, usd_evidence_path=evidence, cursor=page["next_cursor"])
    row = read_buys(db, cfg, as_of=AS_OF, usd_evidence_path=evidence)["rows"][0]
    assert row["signature"] == signature and row["spent_usd"] is row["entry_price_usd"] is None


def test_stable_same_second_paging_no_backfill_from_late_insert(tmp_path):
    db, cfg = tmp_path/"db", tmp_path/"qualification.json"
    ledger = Ledger(db)
    config(cfg)
    signatures = [put(ledger, i) for i in range(1,32)]
    first = read_buys(db,cfg,as_of=AS_OF)
    put(ledger, 100, at=AS_OF-2)
    token = first["next_cursor"]
    second = read_buys(db,cfg,as_of=AS_OF+10,cursor=token)
    assert [r["signature"] for r in first["rows"]+second["rows"]] == signatures[::-1]
    assert not second["next_cursor"]
    with pytest.raises(ValueError, match="INVALID_OR_STALE_CURSOR"):
        read_buys(db,cfg,as_of=AS_OF,days="30",cursor=token)
    config(cfg,exclude=True)
    with pytest.raises(ValueError, match="INVALID_OR_STALE_CURSOR"):
        read_buys(db,cfg,as_of=AS_OF,cursor=token)
    config(cfg)
    with pytest.raises(ValueError, match="INVALID_OR_STALE_CURSOR"):
        read_buys(db,cfg,as_of=AS_OF-1,cursor=token)


def test_paging_rejects_a_replaced_ledger(tmp_path):
    db, cfg = tmp_path/"db", tmp_path/"qualification.json"
    config(cfg)
    ledger = Ledger(db)
    for number in range(1, 32):
        put(ledger, number)
    token = read_buys(db, cfg, as_of=AS_OF)["next_cursor"]
    ledger.db.close()
    replacement = tmp_path/"replacement"
    other = Ledger(replacement)
    put(other, 100)
    other.db.close()
    replacement.replace(db)
    with pytest.raises(ValueError, match="INVALID_OR_STALE_CURSOR"):
        read_buys(db, cfg, as_of=AS_OF, cursor=token)


def test_notification_rehearsal_guards_actual_outbox_and_rechecks_identity(tmp_path, monkeypatch):
    db, cfg = tmp_path/"db", tmp_path/"qualification.json"
    ledger = Ledger(db)
    config(cfg)
    assets = qualification(cfg,AS_OF)
    policy = load_policy(Path(__file__).resolve().parents[1]/"config/frank_local_signal_v1.json")
    for i, kwargs in enumerate([{"mint":BP}, {"mint":UNKNOWN}, {"kind":"failed"}, {"kind":"passive"},
                                {"kind":"mismatched"}],1):
        put(ledger,i,**kwargs)
    # Force an otherwise-qualified policy stage; use the real Engine write path.
    monkeypatch.setattr("mission_agent.signals.engine.evaluate",lambda *_:{
        "stages":[{"signal_type":"FRANK_MULTIPLE_SIGNAL","stage":"fixture","reason_codes":[]}],
        "predicates":{}})
    eng = Engine(ledger,policy,rebuild_assets=assets)
    eng.drain()
    assert ledger.db.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0
    put(ledger,99)
    eng.drain()
    assert [tuple(r) for r in ledger.db.execute("SELECT channel,status FROM outbox ORDER BY channel")] == [("gmail","DRY_RUN_AUDIT"),("local","DRY_RUN_AUDIT")]
    assert Engine(ledger,policy,rebuild_assets=assets).drain() == 0
    with pytest.raises(ValueError,match="DRY_RUN_ONLY"):
        Engine(ledger,policy,dry_run=False,rebuild_assets=assets)


def test_dashboard_endpoint_reads_ledger_and_requires_same_origin_header(tmp_path):
    prod, control = tmp_path/"prod", tmp_path/"control"
    prod.mkdir()
    control.mkdir()
    config(control/"frank-buy-qualifications.json",as_of=int(time.time()))
    ledger = Ledger(prod/"forward.sqlite")
    sig = put(ledger,1,at=int(time.time())-1)
    class TestHandler(Handler):
        state = DashboardState(prod,control)
    with HTTPServer(("127.0.0.1",0),TestHandler) as server:
        runner = Thread(target=server.serve_forever,daemon=True)
        runner.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/api/frank-buys"
        try:
            with pytest.raises(HTTPError) as error:
                urlopen(endpoint, timeout=3)
            assert error.value.code == 403
            headers = {"X-Frank-Research-Read": "1"}
            with urlopen(Request(endpoint+"?days=all", headers=headers),timeout=3) as response:
                result = json.load(response)
            assert [r["signature"] for r in result["rows"]] == [sig]
            with pytest.raises(HTTPError) as error:
                urlopen(Request(endpoint+"?days=all&days=1",headers=headers),timeout=3)
            assert error.value.code == 400
        finally:
            server.shutdown()
            runner.join()


def test_dashboard_http_usd_sidecar_precision_and_size_limit(tmp_path):
    prod, control = tmp_path/"prod", tmp_path/"control"
    prod.mkdir()
    control.mkdir()
    now = int(time.time())
    config(control/"frank-buy-qualifications.json", as_of=now)
    db = prod/"forward.sqlite"
    ledger = Ledger(db)
    sig = put(ledger, 1, at=now-1)
    sidecar = control/"frank-buy-usd-evidence.json"
    record = usd_observation(ledger, sig, USDC, usd_per_quote_unit="0.983456789012345678901")
    payload = json.dumps({"version": 1, "records": [record]}).replace(
        '"0.983456789012345678901"', "0.983456789012345678901"
    ).encode()
    # Trailing JSON whitespace is valid, so the larger input is rejected only by the bound.
    cap = 4 * 1024 * 1024
    at_limit = payload.ljust(cap)
    before = hashlib.sha256(db.read_bytes()).hexdigest()

    class TestHandler(Handler):
        state = DashboardState(prod, control)

    with HTTPServer(("127.0.0.1", 0), TestHandler) as server:
        runner = Thread(target=server.serve_forever, daemon=True)
        runner.start()
        request = Request(f"http://127.0.0.1:{server.server_port}/api/frank-buys?days=all",
                          headers={"X-Frank-Research-Read": "1"})
        try:
            for raw, expected in [
                (at_limit, "0.4917283945061728394505"),
                (at_limit + b" ", None),
                (payload.replace(b'"version": 1', b'"version": 1, "version": 1'), None),
                (payload, "0.4917283945061728394505"),
            ]:
                sidecar.write_bytes(raw)
                with urlopen(request, timeout=3) as response:
                    row, = json.load(response)["rows"]
                assert row["signature"] == sig and row["paid"] == "0.5"
                assert row["spent_usd"] == row["entry_price_usd"] == expected
        finally:
            server.shutdown()
            runner.join()
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before


def test_browser_default_entry_filters_and_prefills_ca(tmp_path):
    """Optional isolated Chromium check: FRANK_TEST_CHROMIUM=/path/to/chromium."""
    import os
    from datetime import datetime, timezone
    binary = os.environ.get("FRANK_TEST_CHROMIUM")
    if not binary:
        pytest.skip("FRANK_TEST_CHROMIUM is not set")
    from playwright.sync_api import sync_playwright, expect
    from mission_agent.mission_control.server import DashboardHTTPServer
    from mission_agent.signals.scanner import Scanner

    prod, control = tmp_path/"prod", tmp_path/"control"
    prod.mkdir()
    control.mkdir()
    at = int(time.time())
    config(control/"frank-buy-qualifications.json",as_of=at)
    ledger = Ledger(prod/"forward.sqlite")
    buy = put(ledger,1,at=at-1,token_raw="2500000")
    put(ledger,2,mint=BP,at=at-2)
    put(ledger,3,kind="failed",at=at-3)
    for number in range(4, 205):
        put(ledger, number, kind="failed", at=at-40*86400)
    Scanner(ledger, {WALLET: "frank"}, tmp_path / "raw", rpcs={WALLET: object()}, mode="LIVE")
    health_path = prod/"health.json"
    runtime = {"status":"RUNNING","pid":os.getpid(),"last_successful_poll":datetime.now(timezone.utc).isoformat(),
               "poll_interval_seconds":30,"raw_pending":1}
    health_path.write_text(json.dumps(runtime))
    ledger.checkpoint(WALLET, buy, 12)
    ledger.db.execute("INSERT INTO health VALUES (?,?)", (WALLET, json.dumps({
        "status":"RUNNING","last_successful_poll":time.time(),"lag_seconds":0,
        "last_chain_signature":buy,"last_local_signature":buy,
    })))
    write_usd_evidence(
        control/"frank-buy-usd-evidence.json",
        usd_observation(ledger, buy, USDC, usd_per_quote_unit="0.983"),
    )
    before = hashlib.sha256((prod/"forward.sqlite").read_bytes()).hexdigest()
    class TestHandler(Handler):
        state = DashboardState(prod,control)
    with DashboardHTTPServer(("127.0.0.1",0),TestHandler) as server:
        runner = Thread(target=server.serve_forever,daemon=True)
        runner.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as api:
                browser = api.chromium.launch(executable_path=binary,args=["--disable-background-networking", "--disable-sync"])
                page = browser.new_page()
                errors, requests, served_paths = [], [], []
                allowed_apis = {"/api/frank-buys", "/api/cluster-latest", "/api/frank-signed-activity"}
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                def route_local_read(route):
                    request = route.request
                    if request.method != "GET" or not request.url.startswith(base+"/"):
                        route.abort()
                        return
                    path = request.url.removeprefix(base).split("?", 1)[0]
                    if path.startswith("/api/") and path not in allowed_apis:
                        route.abort()
                        return
                    served_paths.append(path)
                    route.continue_()

                page.route("**/*", route_local_read)
                page.on("request",lambda req:requests.append((req.method, req.url)))
                page.goto(base,wait_until="domcontentloaded")
                expect(page.get_by_role("heading",name="Meme 研究台")).to_be_visible()
                rows = page.locator("#frank-buy-rows tr")
                expect(rows).to_have_count(1)
                expect(rows.first).to_contain_text("样例 Meme")
                expect(rows.first.locator(".buy-value").nth(0)).to_have_text("花费$0.49")
                expect(rows.first.locator(".buy-value").nth(1)).to_have_text("买入价$0.20")
                expect(rows.first).not_to_contain_text("USDC")
                expect(page.locator("#follow-opportunities")).to_be_hidden()
                page.locator("#frank-buy-mint").fill(BP)
                page.get_by_role("button",name="筛选",exact=True).click()
                expect(page.locator("#frank-buy-status")).to_contain_text("采集尚未追平")
                health_path.write_text(json.dumps({**runtime, "status": "RETRY_PENDING", "raw_pending": 0,
                                                   "wallet_scan_failures": 1}))
                page.get_by_role("button",name="筛选",exact=True).click()
                expect(page.locator("#frank-buy-status")).to_contain_text("采集尚未追平")
                health_path.write_text(json.dumps({**runtime, "raw_pending": 0, "wallet_scan_failures": 0}))
                page.get_by_role("button",name="筛选",exact=True).click()
                expect(page.locator("#frank-buy-status")).to_contain_text("这段时间没有已核实的买入记录")
                page.locator("#frank-buy-mint").fill(MINT)
                page.get_by_role("button",name="筛选",exact=True).click()
                expect(rows).to_have_count(1)
                page.locator("#frank-buy-rows").get_by_role("button",name="查 CA").click()
                expect(page.locator("#cluster-mint")).to_have_value(MINT)
                page.goto(base+"/#signals",wait_until="domcontentloaded")
                page.locator("#signed-activity-days").select_option("all")
                signed_rows = page.locator("#signed-activity-rows tr")
                expect(signed_rows).to_have_count(100)
                load_older = page.get_by_role("button",name="加载更早流水")
                load_older.click()
                expect(signed_rows).to_have_count(200)
                load_older.click()
                expect(signed_rows).to_have_count(204)
                expect(load_older).to_be_hidden()
                signature_filter = page.locator("#signed-activity-search")
                signature_filter.fill(buy)
                signature_filter.press("Enter")
                expect(signed_rows).to_have_count(1)
                expect(signed_rows.first).to_contain_text("主动交易")
                expect(signed_rows.first).to_contain_text("买入")
                expect(signed_rows.first.locator("td").nth(1).get_by_role("link")).to_have_attribute(
                    "href", "https://solscan.io/tx/" + buy
                )
                assert not errors
                assert all(method=="GET" and url.startswith(base+"/") for method,url in requests)
                assert {path for path in served_paths if path.startswith("/api/")} == allowed_apis
                assert hashlib.sha256((prod/"forward.sqlite").read_bytes()).hexdigest() == before
                browser.close()
        finally:
            server.shutdown()
            runner.join()


def test_offline_reconciliation_separates_missed_unexpected_pending_and_latency(tmp_path):
    import sqlite3
    from datetime import datetime, timezone
    from mission_agent.signals.reconciliation import ReconciliationError, reconcile_snapshot

    cfg, backup, ref = (tmp_path/name for name in ("qualifications.json","backup.sqlite","reference.json"))
    config(cfg)
    ledger = Ledger(tmp_path/"ledger")
    at = AS_OF-10
    good = put(ledger,1,at=at)
    excluded = put(ledger,2,at=at,mint=BP)
    unexpected = put(ledger,3,at=at)
    unknown = put(ledger,4,at=at,kind="failed")
    unseen = _b58((5).to_bytes(64,"big"))
    pending = _b58((6).to_bytes(64,"big"))
    unqualified = put(ledger,7,mint=UNKNOWN,at=at)
    ledger.checkpoint(WALLET,pending,14)
    ledger.db.execute("CREATE TABLE signature_detections(wallet,signature,person_id,slot,seen_at)")
    ledger.db.execute("INSERT INTO signature_detections VALUES (?,?,?,?,?)",(WALLET,good,"frank",12,at+2.25))
    ledger.db.execute("UPDATE signatures SET seen_at=? WHERE signature=?",
                      (datetime.fromtimestamp(at+4,timezone.utc).isoformat(),good))
    with sqlite3.connect(backup) as target:
        ledger.db.backup(target)
        target.execute("PRAGMA journal_mode=DELETE")
    ref.write_text(json.dumps({"schema_version":1,"chain":"solana","commitment":"finalized","complete":True,
        "start_slot":12,"end_slot":14,"finalized_through_slot":14,"person_id":"frank","wallet":WALLET,
        "source_id":"independent_fixture","capture_sha256":"a"*64,"transactions":[
            {"signature":sig,"slot":slot,**({"expected_frank_buy":want,"expectation_sha256":"b"*64}
                                         if want is not None else {})}
            for sig,slot,want in [(good,12,MINT),(excluded,12,False),(unexpected,12,False),
                                  (unknown,12,None),(unseen,13,MINT),(pending,14,MINT),
                                  (unqualified,12,False)]
        ]}))
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    args = (backup,sha(backup),ref,sha(ref))
    result = reconcile_snapshot(*args,scanner_source_id="scanner_fixture",buy_qualifications=(cfg,sha(cfg),AS_OF))
    buys = result["buy_admission"]
    assert result["status"] == buys["status"] == "GAPS"
    assert buys["counts"] == {"EXPECTED_IN":3,"EXPECTED_OUT":3,"MATCHED_IN":1,"MATCHED_OUT":1,
                             "MISSED":1,"PENDING":1,"UNEXPECTED":1,"UNRESOLVED":2,"WRONG_MINT":0}
    assert buys["chain_to_detection"]["minimum_seconds"] == 2.25
    assert buys["chain_to_index"]["maximum_seconds"] == 4
    assert buys["delivery_timing"] == "NOT_VERIFIED"
    assert sha(backup) == args[1]
    with pytest.raises(ReconciliationError,match="BUY_QUALIFICATION_SHA256_MISMATCH"):
        reconcile_snapshot(*args,scanner_source_id="scanner_fixture",buy_qualifications=(cfg,"0"*64,AS_OF))

def test_exact_official_backpack_exclusion_overrides_a_stale_positive_label(tmp_path, monkeypatch):
    db, cfg = tmp_path/"db", tmp_path/"qualification.json"
    ledger = Ledger(db)
    config(cfg)
    doc=json.loads(cfg.read_text())
    doc["records"].append({**doc["records"][0],"mint":BACKPACK_MINT,"name":"BP"})
    cfg.write_text(json.dumps(doc))
    put(ledger,1,mint=BACKPACK_MINT)
    assert read_buys(db,cfg,as_of=AS_OF)["rows"] == []
    policy = load_policy(Path(__file__).resolve().parents[1]/"config/frank_local_signal_v1.json")
    def unexpected_evaluation(*_):
        pytest.fail("known non-Meme must not enter model evaluation")
    monkeypatch.setattr("mission_agent.signals.engine.evaluate",unexpected_evaluation)
    Engine(ledger,policy,rebuild_assets=qualification(cfg,AS_OF)).drain()
    assert ledger.db.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0


def test_dashboard_imports_exact_category_receipts_without_manual_prefill(tmp_path):
    from mission_agent.signals.category_evidence import COINGECKO_SOLANA

    prod, control = tmp_path/"prod", tmp_path/"control"
    prod.mkdir()
    control.mkdir()
    now = int(time.time())
    db = prod/"forward.sqlite"
    ledger = Ledger(db)
    launch, wrong, conflict, excluded, future = [_b58(bytes([n])*32) for n in range(5, 10)]
    mints = [MINT, launch, wrong, conflict, excluded, future, BACKPACK_MINT]
    for i, mint in enumerate(mints, 1):
        put(ledger, i, mint=mint, at=now-1)
    before = hashlib.sha256(db.read_bytes()).hexdigest()

    def receipt(mint, categories, *, detail=None, when=now):
        body = json.dumps({
            "name": "Same Name", "preview_listing": False,
            "platforms": {"solana": mint}, "detail_platforms": {"solana": {"contract_address": detail or mint}},
            "categories": categories,
        })
        return {"mint": mint, "observed_at": when, "url": COINGECKO_SOLANA+mint,
                "body": body, "sha256": hashlib.sha256(body.encode()).hexdigest()}

    path = control/"frank-buy-category-evidence.json"
    evidence = [
        receipt(MINT, ["Meme", "Solana Meme"]),
        receipt(launch, ["Pump.fun Ecosystem"]),
        receipt(wrong, ["Meme"], detail=MINT),
        receipt(conflict, ["Meme"]),
        receipt(conflict, ["Stablecoins"]),
        receipt(excluded, ["Liquid Staking Tokens"]),
        receipt(future, ["Meme"], when=now+60),
        receipt(BACKPACK_MINT, ["Meme"]),
        receipt(MINT, ["Pump.fun Ecosystem"], when=now-1),
    ]
    def write(data):
        path.write_text(json.dumps({"version": 1, "records": data}))

    write(evidence)
    dashboard = DashboardState(prod, control)
    row, = dashboard.frank_buys()["rows"]
    assert row["mint"] == MINT and row["name"] == "Same Name" and row["paid"] == "0.5"
    evidence[0]["sha256"] = "0"*64
    write(evidence)
    assert dashboard.frank_buys()["rows"] == []
    manual = control/"frank-buy-qualifications.json"
    config(manual, as_of=now)
    assert [row["mint"] for row in dashboard.frank_buys()["rows"]] == [MINT]
    write([receipt(MINT, ["Meme"])])
    config(manual, exclude=True, as_of=now)
    assert dashboard.frank_buys()["rows"] == []
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
