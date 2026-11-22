"""Regression checks for persistent cost-run binding and frozen reference prices."""

from concurrent.futures import ThreadPoolExecutor
from email.message import Message
from io import BytesIO
import json
import sqlite3
from types import SimpleNamespace

import pytest

from mission_agent.mission_control import server
from mission_agent.mission_control.evidence_manifests import ManifestError
from mission_agent.mission_control.market_observations import USDC, normalize_market
from mission_agent.mission_control.wallet_cost_store import CostStoreError, WalletCostStore, value_assets
from test_frank_market_observations import key, snapshot


MANIFEST, OTHER = "a" * 32, "b" * 32
REBUILD = "/api/frank-cost-rebuild"
BASIS = "/api/frank-cost-basis"


class TestInput:
    __test__ = False

    def __init__(self):
        self.requested = []

    def cost_input(self, manifest):
        self.requested.append(manifest)
        if manifest not in {MANIFEST, OTHER}:
            raise ManifestError("MANIFEST_NOT_FOUND", 404)
        return {"manifest_sha256": "1" * 64, "parser_sha256": "2" * 64, "as_of": 100}, [manifest]


def asset(mint, amount="1", quote=USDC):
    return {"mint": mint, "decimals": 0, "quantity_raw": amount,
            "known_cost_quantity_raw": amount, "unknown_cost_quantity_raw": "0",
            "remaining_costs": ([{"mint": quote, "decimals": 6, "denomination": "USDC",
                                  "raw_numerator": "1000000", "raw_denominator": "1",
                                  "covered_quantity_raw": amount}] if quote else []),
            "lots": [], "realized": [], "movements": []}


def market(mint, price, when=100):
    return normalize_market(mint, snapshot(mint, price=price, when=when), received_at=when)


def test_mixed_price_and_quote_never_fill_unknown_unrealized_or_wallet_total():
    rows, summary = value_assets([asset(key(1)), asset(key(2)), asset(key(3), quote=None)],
                                 {key(1): market(key(1), "2"), key(3): market(key(3), "4", when=1),
                                  USDC: market(USDC, "0.8")}, 110)
    assert summary["covered_positions"] == 1 and summary["unpriced_mints"] == [key(2), key(3)]
    assert summary["partial_value_usd"] == "2" and summary["full_wallet_value_usd"] is None
    assert rows[0]["unrealized_pnl"] is None
    comparison, = rows[0]["covered_unrealized_pnl"]
    assert (comparison["mint"], comparison["raw_numerator"], comparison["raw_denominator"]) == (
        USDC, "1500000", "1")
    assert comparison["target_observation"]["observation_sha256"] != comparison["quote_observation"]["observation_sha256"]
    assert all(not row["covered_unrealized_pnl"] for row in rows[1:])
    assert rows[2]["valuation"]["reason"] == "STALE_OBSERVATION"
    _, no_price = value_assets([asset(key(1))], {}, 110)
    assert no_price["partial_value_usd"] is None


@pytest.fixture
def store(tmp_path, monkeypatch):
    from mission_agent.mission_control import wallet_cost_fifo

    fixture = TestInput()
    observations = {key(1): market(key(1), "2"), USDC: market(USDC, "0.8")}

    def ledger(rows):
        return {"input_rows": len(rows), "fees": {"network_fee_lamports": "500"},
                "assets": [asset(key(index), quote=None) for index in range(1, 123 if rows == [MANIFEST] else 3)]}

    monkeypatch.setattr(wallet_cost_fifo, "build_cost_ledger", ledger)
    return WalletCostStore(tmp_path / "derived", fixture, observations.copy, clock=lambda: 111), fixture, observations


def test_frozen_run_and_all_pages_survive_new_run_and_market_changes(store):
    target, manifests, prices = store
    with pytest.raises(CostStoreError, match="COST_RUN_NOT_FOUND"):
        target.page()
    assert not target.root.exists()
    first = target.create(MANIFEST, "initial")
    assert target.get(first["run_id"]) == first
    assert target.create(MANIFEST, "another-key") == first
    assert manifests.requested == [MANIFEST]
    with pytest.raises(CostStoreError, match="COST_IDEMPOTENCY_CONFLICT"):
        target.create(OTHER, "another-key")
    page = target.page(limit=17)
    collected = list(page["rows"])
    assert page["valuation"]["partial_value_usd"] == "2"
    prices.clear()
    second = target.create(OTHER, "second")
    assert target.page()["run_id"] == second["run_id"]
    assert second["valuation"]["partial_value_usd"] is None
    with pytest.raises(CostStoreError, match="COST_CURSOR_QUERY_CHANGED"):
        target.page(run_id=second["run_id"], cursor=page["next_cursor"])
    while page["next_cursor"]:
        page = target.page(limit=17, cursor=page["next_cursor"])
        assert page["run_id"] == first["run_id"]
        assert page["valuation"]["partial_value_usd"] == "2"
        collected.extend(page["rows"])
    assert len(collected) == len({item["mint"] for item in collected}) == 122
    assert target.page(run_id=first["run_id"], mint=key(99))["rows"] == [
        next(item for item in collected if item["mint"] == key(99))]


def test_concurrent_same_manifest_is_single_complete_run(store):
    target, _, _ = store
    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = list(executor.map(lambda k: target.create(MANIFEST, k), ("one", "two")))
    assert first == second
    assert target.page(run_id=first["run_id"])["total_matching"] == 122
    with sqlite3.connect(target.path) as db:
        assert db.execute("SELECT count(*) FROM cost_runs").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM cost_keys").fetchone()[0] == 2


@pytest.mark.parametrize("resealed", [False, True])
def test_persisted_asset_corruption_never_yields_mutated_result(store, resealed):
    target, _, _ = store
    target.create(MANIFEST, "initial")
    from mission_agent.mission_control.evidence_manifests import digest
    changed = asset(key(1), "9")
    with sqlite3.connect(target.path) as db:
        db.execute("UPDATE cost_assets SET body=? WHERE mint=?", (json.dumps(changed), key(1)))
        if resealed:
            db.execute("UPDATE cost_assets SET sha256=? WHERE mint=?", (digest(changed), key(1)))
    with pytest.raises(CostStoreError, match="COST_RUN_INTEGRITY_FAILED"):
        target.page(mint=key(1))


def call(target, path, method="GET", body=None, origin="http://127.0.0.1:8766", read=True):
    handler = object.__new__(server.Handler)
    handler.state = SimpleNamespace(wallet_cost=target)
    handler.path, handler.headers = path, Message()
    handler.headers["Host"] = "127.0.0.1:8766"
    if origin is not None:
        handler.headers["Origin"] = origin
    if read:
        handler.headers["X-Frank-Research-Read"] = "1"
    handler.headers["Content-Type"] = "application/json"
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    handler.headers["Content-Length"] = str(len(raw))
    handler.rfile, handler.wfile = BytesIO(raw), BytesIO()
    codes = []
    handler.send_response = handler.send_error = lambda code, *args: codes.append(code)
    handler.send_header = lambda *_: None
    handler.end_headers = lambda: None
    getattr(handler, "do_" + method)()
    return codes[0], json.loads(handler.wfile.getvalue())


def test_http_routes_are_same_origin_and_bind_immutable_input(store):
    target, _, _ = store
    request = {"input_manifest_id": MANIFEST, "idempotency_key": "ui"}
    assert call(target, REBUILD, "POST", request, origin="http://127.0.0.1:8765")[0] == 403
    assert call(target, REBUILD, "POST", request, origin=None)[0] == 403
    assert call(target, REBUILD, "POST", {**request, "debug": True})[0] == 400
    assert call(target, BASIS, read=False)[0] == 403
    assert call(target, BASIS + "?limit=2&limit=3")[0] == 400
    assert not target.root.exists()
    code, published = call(target, REBUILD, "POST", request)
    assert code == 201 and published["state"] == "COMPLETE"
    assert call(target, REBUILD + "?run_id=" + published["run_id"]) == (200, published)
    code, page = call(target, BASIS + "?limit=2")
    assert code == 200 and page["total_matching"] == 122 and page["returned"] == 2
    assert call(target, REBUILD, "POST", {**request, "input_manifest_id": OTHER}) == (
        409, {"error": "COST_IDEMPOTENCY_CONFLICT"})
