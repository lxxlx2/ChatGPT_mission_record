"""W08 local-only risk state and explicit quote routing."""
import json
import sqlite3
from email.message import Message
from io import BytesIO
from types import SimpleNamespace

import pytest

from mission_agent.mission_control import server
from mission_agent.mission_control.ata_backfill import b58encode
from mission_agent.mission_control.evidence_manifests import digest
from mission_agent.mission_control.frank_quote import FrankQuoteService, QuoteError
from mission_agent.mission_control.frank_risk_inputs import build_risk_inputs
from mission_agent.mission_control.frank_risk_runs import FrankRiskRuns, RiskRunError

NOW = 1_795_000_000
ASSET, USDC, AMM = (b58encode(bytes([x]) * 32) for x in (1, 2, 3))
SIG = "1" * 64
MANIFEST = "a" * 32


def risk_row(side="SELL", *, at=NOW-5, missing=None, position=None, market=None):
    return {
        "mint": ASSET, "chain": "solana", "latest_action_at": at, "latest_side": side,
        "latest_signature": SIG, "latest_fact_id": "e"*64,
        "facts": ["FRANK_LATEST_ACTION_" + side, "FRANK_SELL_OBSERVED_REVIEW_RISK"] if side == "SELL"
                 else ["FRANK_LATEST_ACTION_BUY"],
        "missing": missing or [], "market_reference": market, "position": position,
    }


def capture(rows, *, as_of=NOW, cutoff=NOW-1, manifest=MANIFEST, position=None, market=None):
    return {"as_of": as_of, "rows": rows, "source_refs": {
        "fact_manifest_id": manifest, "facts_sha256": digest([manifest, cutoff]),
        "fact_as_of": cutoff, "position_sha256": position, "market_sha256": market}}


def test_durable_idempotency_cursor_and_older_manifest(tmp_path):
    clock = [NOW]
    state = FrankRiskRuns(tmp_path, clock=lambda: clock[0])
    assert state.page()["rows"] == [] and not state.path.exists()
    a = state.create("one", MANIFEST, load_inputs=lambda _: capture([
        risk_row(missing=["MARKET_REFERENCE_MISSING", "sensitive/private/path"])]))
    assert a["created_updates"] == 2 and not a["notification_enabled"]
    page = state.page(limit=1)
    reopened = FrankRiskRuns(tmp_path, clock=lambda: clock[0])
    saved = reopened.create("one", MANIFEST, load_inputs=lambda _: pytest.fail("idempotent rerun called source"))
    assert saved == a == reopened.get(a["run_id"])
    assert "sensitive" not in json.dumps(page)
    next_page = reopened.page(limit=1, cursor=page["next_cursor"])
    assert {page["rows"][0]["kind"], next_page["rows"][0]["kind"]} == {"SELL_OBSERVED", "EVIDENCE_GAP"}
    with pytest.raises(RiskRunError):
        reopened.page(kind="SELL_OBSERVED", cursor=page["next_cursor"])
    clock[0] += 30
    older = reopened.create("older", load_inputs=lambda _: capture([risk_row(missing=["POSITION_STATE_UNKNOWN"])],
                                                                  as_of=clock[0], cutoff=NOW-60))
    assert older["older_rows_skipped"] == 1 and older["created_updates"] == 0
    repeat = reopened.create("repeat", load_inputs=lambda _: capture([
        risk_row(missing=["MARKET_REFERENCE_MISSING"])], as_of=clock[0], cutoff=NOW+1))
    assert repeat["created_updates"] == 0 and reopened.page()["total_matching"] == 2
    with pytest.raises(RiskRunError, match="IDEMPOTENCY"):
        reopened.create("one", "b"*32, load_inputs=lambda _: pytest.fail("conflict called source"))


def test_ttl_transition_and_verified_position_decrease(tmp_path):
    clock = [NOW]
    store = FrankRiskRuns(tmp_path, clock=lambda: clock[0])
    observation = {"source": "DEXSCREENER_API", "chain_id": "solana", "currency": "USD",
                   "status": "OK", "observed_at": NOW-5, "mint": ASSET}
    observation["observation_sha256"] = digest(observation)
    def position(amount, at):
        return {"mint": ASSET, "raw_amount": amount, "observed_at": at,
                "decimals": 6, "verification": "COMPLETE_CAPTURE"}
    def load(amount, newest, refs):
        return lambda _: capture([risk_row("BUY", position=position(amount, newest), market=observation)],
                                 as_of=clock[0], position=refs, market="f"*64)
    initial = store.create("start", load_inputs=load("28", NOW-5, "a"*64))
    assert initial["created_updates"] == 0
    clock[0] += 61
    assert store.create("changed", load_inputs=load("17", NOW+60, "b"*64))["created_updates"] == 2
    assert {r["kind"] for r in store.page()["rows"]} == {"PRICE_REFERENCE_STALE", "POSITION_REDUCTION_OBSERVED"}
    assert store.create("same", load_inputs=load("17", NOW+60, "b"*64))["created_updates"] == 0


def test_old_sell_is_history_at_initialization_and_future_positions_do_not_count(tmp_path):
    store = FrankRiskRuns(tmp_path, clock=lambda: NOW)
    result = store.create("historical", load_inputs=lambda _: capture([risk_row(at=NOW-3600)]))
    assert result["created_updates"] == 0
    assert store.page()["total_matching"] == 0


def test_interrupted_write_rolls_back_rows_and_retry_commits_once(tmp_path):
    store = FrankRiskRuns(tmp_path, clock=lambda: NOW)
    store.create("initialize", load_inputs=lambda _: capture([]))
    with sqlite3.connect(store.path) as db:
        db.execute("CREATE TRIGGER stop_before_run BEFORE INSERT ON risk_runs BEGIN "
                   "SELECT RAISE(ABORT, 'injected interruption'); END")
    with pytest.raises(RiskRunError):
        store.create("retry", load_inputs=lambda _: capture([risk_row()]))
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT count(*) FROM risk_state").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM risk_updates").fetchone()[0] == 0
        db.execute("DROP TRIGGER stop_before_run")
    assert store.create("retry", load_inputs=lambda _: capture([risk_row()]))["created_updates"] == 1
    assert FrankRiskRuns(tmp_path).page()["total_matching"] == 1


def test_fixed_input_projects_only_hash_bound_succeeded_events_and_no_amount():
    fact = {"wallet": AMM, "signature": SIG, "slot": 5, "fact_id": "c"*64,
            "source_ref": {"raw_transaction_sha256": "e"*64}}
    original = {**fact, "event_at": NOW-10, "execution_status": "SUCCEEDED",
                "coverage": {"normalized_evidence": "BOUND"},
                "economic_exchange": {"basis": "VERIFIED_WALLET_BOUNDARY_SINGLE_TARGET",
                                      "mint": ASSET, "side": "SELL"}}
    fact["archived_replay"] = {"status": "VERIFIED", "raw_sha256": "e"*64, "fact": original}
    meta = {"as_of": NOW-3, "manifest_sha256": "d"*64, "manifest_id": MANIFEST}
    args = {"position_snapshot": None, "market": {}, "as_of": NOW}
    projection = build_risk_inputs(meta, [{"transaction_fact": fact}], **args)
    row = projection["rows"][0]
    assert row["latest_side"] == "SELL" and row["latest_fact_id"] == "c"*64
    assert row["order_amount_usdc"] is None and not row["alert_delivery_authorized"]
    original["event_at"] = NOW-2  # inside run, but after the fixed fact cutoff
    assert build_risk_inputs(meta, [{"transaction_fact": fact}], **args)["rows"] == []
    original.update(event_at=NOW-10, execution_status="FAILED")
    assert build_risk_inputs(meta, [{"transaction_fact": fact}], **args)["rows"] == []


def quote_input():
    return {"mint": ASSET, "input_mint": USDC, "input_amount_raw": "250000", "slippage_bps": 50}


def quote_reply(data):
    return {"inputMint": data["input_mint"], "outputMint": data["mint"], "inAmount": data["input_amount_raw"],
            "outAmount": "520", "otherAmountThreshold": "517", "priceImpactPct": "0.002",
            "slippageBps": data["slippage_bps"], "swapMode": "ExactIn", "contextSlot": 629,
            "routePlan": [{"percent": 100, "swapInfo": {"ammKey": AMM, "inputMint": USDC,
                           "outputMint": ASSET, "inAmount": "250000", "outAmount": "520"}}],
            "swapTransaction": "TEST_PRIVATE_UNUSED"}


class Stub:
    def __init__(self, reply):
        self.reply, self.calls = reply, []
    def quote_exact_in(self, *args):
        self.calls.append(args)
        return self.reply[0], json.dumps(self.reply[1]).encode()


def handler(state, path, method="GET", payload=None, origin="http://127.0.0.1:8766", header=True):
    target = object.__new__(server.Handler)
    target.state, target.path, target.headers = state, path, Message()
    target.headers["Host"] = "127.0.0.1:8766"
    if origin:
        target.headers["Origin"] = origin
    if header:
        target.headers["X-Frank-Research-Read"] = "1"
    target.headers["Content-Type"] = "application/json"
    raw = json.dumps(payload).encode()
    target.headers["Content-Length"] = str(len(raw))
    target.rfile, target.wfile = BytesIO(raw), BytesIO()
    codes = []
    target.send_response = target.send_error = lambda status, *args: codes.append(status)
    target.send_header = lambda *args: None
    target.end_headers = lambda: None
    getattr(target, "do_"+method)()
    return codes[0], json.loads(target.wfile.getvalue() or b"null")


def test_http_explicit_amount_origin_quote_ttl_and_sanitized_route(tmp_path):
    payload = quote_input()
    stub = Stub((200, quote_reply(payload)))
    state = SimpleNamespace(frank_quote=FrankQuoteService(stub, clock=lambda: NOW),
                            risk_runs=FrankRiskRuns(tmp_path, clock=lambda: NOW),
                            risk_input=lambda manifest, key: capture([risk_row()]))
    assert handler(state, "/api/frank-quote")[0] == 404
    assert handler(state, "/api/frank-quote", "POST", {}, origin="http://127.0.0.1:8767")[0] == 403
    assert handler(state, "/api/frank-quote", "POST", {})[0] == 400
    assert handler(state, "/api/frank-intelligence-updates", header=False)[0] == 403
    assert handler(state, "/api/frank-intelligence-updates")[1]["rows"] == []
    assert not stub.calls
    status, response = handler(state, "/api/frank-quote", "POST", payload)
    assert status == 200 and stub.calls == [(USDC, ASSET, "250000", 50)]
    assert response["input"] == payload and response["out_amount_raw"] == "520"
    assert response["expires_at"] == NOW+30 and response["source_ref"]["http_status"] == 200
    assert "TEST_PRIVATE" not in json.dumps(response)
    status, run = handler(state, "/api/frank-intelligence-refresh", "POST",
                          {"input_manifest_id": MANIFEST, "idempotency_key": "test"})
    assert status == 201 and run["created_updates"] == 1
    status, found = handler(state, "/api/frank-intelligence-refresh?run_id="+run["run_id"])
    assert status == 200 and found == run
    assert len(stub.calls) == 1


def test_quote_no_route_and_mismatched_provider_inputs_do_not_become_prices():
    payload = quote_input()
    invalid = Stub((200, {**quote_reply(payload), "inAmount": "1"}))
    with pytest.raises(QuoteError, match="JUPITER_QUOTE_INPUT_MISMATCH"):
        FrankQuoteService(invalid, clock=lambda: NOW).create(payload)
    absent = Stub((400, {"errorCode": "NO_ROUTES_FOUND", "error": "sensitive private diagnostics"}))
    view = FrankQuoteService(absent, clock=lambda: NOW).create(payload)
    assert view["status"] == "NO_ROUTE" and not view["route_exists"] and "sensitive" not in json.dumps(view)
