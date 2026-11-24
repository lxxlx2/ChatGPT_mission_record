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

from mission_agent.frank.rpc import WALLET
from mission_agent.meme.holder_ranks import _b58
from mission_agent.mission_control.frank_buys import read_buys
from mission_agent.mission_control.server import DashboardState, Handler
from mission_agent.signals.buy_admission import qualification
from mission_agent.signals.classifier import classify
from mission_agent.signals.engine import Engine
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


def put(ledger, number, *, mint=MINT, kind="buy", at=AS_OF-1, person="frank"):
    signature = _b58(number.to_bytes(64, "big"))
    raw = tx()
    if kind == "passive":
        raw = json.loads(gzip.decompress((FIXTURES/"token.json.gz").read_bytes()))
    else:
        for side in ("preTokenBalances", "postTokenBalances"):
            raw["meta"][side][0]["mint"] = mint
            raw["meta"][side][1]["mint"] = USDC
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
                               "slot": 12, "at": AS_OF-1, "quantity": "1", "paid": "0.5", "currency": "USDC"}]
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
    assert read_buys(db,cfg,as_of=AS_OF,mint=BP)["rows"] == []
    assert read_buys(db,tmp_path/"missing",as_of=AS_OF)["status"] == "QUALIFICATION_UNAVAILABLE"


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


def test_browser_default_entry_filters_and_prefills_ca(tmp_path):
    """Optional isolated Chromium check: FRANK_TEST_CHROMIUM=/path/to/chromium."""
    import os
    binary = os.environ.get("FRANK_TEST_CHROMIUM")
    if not binary:
        pytest.skip("FRANK_TEST_CHROMIUM is not set")
    from playwright.sync_api import sync_playwright, expect
    from mission_agent.mission_control.server import DashboardHTTPServer

    prod, control = tmp_path/"prod", tmp_path/"control"
    prod.mkdir()
    control.mkdir()
    at = int(time.time())
    config(control/"frank-buy-qualifications.json",as_of=at)
    ledger = Ledger(prod/"forward.sqlite")
    put(ledger,1,at=at-1)
    put(ledger,2,mint=BP,at=at-2)
    put(ledger,3,kind="failed",at=at-3)
    class TestHandler(Handler):
        state = DashboardState(prod,control)
    with DashboardHTTPServer(("127.0.0.1",0),TestHandler) as server:
        runner = Thread(target=server.serve_forever,daemon=True)
        runner.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as api:
                browser = api.chromium.launch(executable_path=binary,args=["--no-sandbox"])
                page = browser.new_page()
                errors, requests = [], []
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(base+"/") else route.abort())
                page.on("request",lambda req:requests.append((req.method, req.url)))
                page.goto(base,wait_until="domcontentloaded")
                expect(page.get_by_role("heading",name="Frank 买入")).to_be_visible()
                expect(page.locator("#frank-buy-rows article")).to_have_count(1)
                expect(page.locator("#frank-buy-rows")).to_contain_text("样例 Meme")
                expect(page.locator("#frank-buy-rows")).to_contain_text("支付 0.5 USDC")
                expect(page.locator("#follow-opportunities")).to_be_hidden()
                page.locator("#frank-buy-mint").fill(BP)
                page.get_by_role("button",name="筛选",exact=True).click()
                expect(page.locator("#frank-buy-status")).to_contain_text("所选范围暂未核实买入")
                page.locator("#frank-buy-mint").fill(MINT)
                page.get_by_role("button",name="筛选",exact=True).click()
                expect(page.locator("#frank-buy-rows article")).to_have_count(1)
                page.locator("#frank-buy-rows").get_by_role("button",name="链上查询").click()
                expect(page.locator("#cluster-mint")).to_have_value(MINT)
                assert not errors
                assert all(method=="GET" and url.startswith(base+"/") for method,url in requests)
                assert not any(url.startswith(base+"/api/") and not any(
                    key in url for key in ("/api/frank-buys", "/api/cluster-latest")) for _,url in requests)
                browser.close()
        finally:
            server.shutdown()
            runner.join()
