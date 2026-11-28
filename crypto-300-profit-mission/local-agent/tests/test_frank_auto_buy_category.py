"""Scanner-owned category receipts, using only an injected Demo transport."""
from functools import partial
import hashlib
import io
import json
from urllib.error import HTTPError

from mission_agent.meme.holder_ranks import _b58
from mission_agent.mission_control.frank_buys import read_buys
from mission_agent.signals.auto_buy_category import AutoBuyCategory
from mission_agent.signals.buy_admission import BACKPACK_MINT, BuyDeliveryGate
from mission_agent.signals.category_capture import capture
from mission_agent.signals.category_evidence import COINGECKO_SOLANA, read_scanner_category_evidence
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy
from mission_agent.signals.store import Ledger
from test_frank_rebuild_buys import AS_OF, MINT, UNKNOWN
from test_frank_rebuild_delivery import indexed_buys
from test_frank_v1 import POLICY


class Reply(io.BytesIO):
    def __init__(self, url, mint, categories):
        super().__init__(json.dumps({
            "name": "已核实代币", "preview_listing": False, "categories": categories,
            "platforms": {"solana": mint}, "detail_platforms": {"solana": {"contract_address": mint}},
        }).encode())
        self.url = url

    def geturl(self):
        return self.url


def test_scanner_discovery_qualifies_new_mint_for_existing_buy_and_delivery_paths(tmp_path):
    db = tmp_path / "ledger"
    ledger = Ledger(db)
    indexed_buys(ledger, tmp_path / "raw", [MINT, UNKNOWN, BACKPACK_MINT])
    requested = []

    def wire(request, timeout):
        mint = request.full_url.removeprefix(COINGECKO_SOLANA)
        requested.append(mint)
        assert request.get_header("X-cg-demo-api-key") == "fixture-key"
        return Reply(request.full_url, mint, ["Meme" if mint == MINT else "Stablecoins"])

    collector = AutoBuyCategory(ledger.db, api_key="fixture-key",
                               collect=partial(capture, open_url=wire), clock=lambda: AS_OF)
    assert collector.refresh() == {"status": "CURRENT", "requests": 2, "receipts": 2}
    assert set(requested) == {MINT, UNKNOWN}
    assert collector.refresh()["requests"] == 0
    assets = read_scanner_category_evidence(ledger.db, AS_OF)
    assert {key: value.status for key, value in assets.items()} == {MINT: "VERIFIED_MEME", UNKNOWN: "EXCLUDED"}
    assert read_scanner_category_evidence(ledger.db, AS_OF, mint=MINT) == {MINT: assets[MINT]}

    gate = BuyDeliveryGate(clock=lambda: AS_OF)
    Engine(ledger, load_policy(POLICY), dry_run=False, delivery_gate=gate).drain()
    signals = ledger.db.execute("SELECT mint FROM signals JOIN outbox USING(signal_id)").fetchall()
    assert signals and {row[0] for row in signals} == {MINT}
    buys = read_buys(db, None, as_of=AS_OF)["rows"]
    assert len(buys) == 3 and all(row["mint"] == MINT for row in buys)
    assert not any("fixture-key" in row[0] for row in ledger.db.execute("SELECT receipt FROM buy_category_auto"))


def test_backlog_survives_restart_without_repeating_resolved_requests_or_cutting_mints(tmp_path):
    target = tmp_path / "ledger"
    ledger = Ledger(target)
    mints = [_b58(bytes([i]) * 32) for i in range(91, 100)]
    indexed_buys(ledger, tmp_path / "raw", mints)
    clock = [AS_OF]
    calls = []

    def wire(request, timeout):
        mint = request.full_url.removeprefix(COINGECKO_SOLANA)
        calls.append(mint)
        if len(calls) == 2:
            raise HTTPError(request.full_url, 429, "fixture", {"Retry-After": "180"}, None)
        return Reply(request.full_url, mint, ["Meme"])

    def category(db):
        return AutoBuyCategory(db, api_key="fixture-key",
                               collect=partial(capture, open_url=wire), clock=lambda: clock[0])

    assert category(ledger.db).refresh()["status"] == "SOURCE_RATE_LIMIT"
    assert len(calls) == 2 and len(read_scanner_category_evidence(ledger.db, AS_OF)) == 1
    assert ledger.db.execute("SELECT count(*) FROM buy_category_auto").fetchone()[0] == len(mints)
    ledger.db.close()
    ledger = Ledger(target)
    runner = category(ledger.db)
    clock[0] += 179
    assert runner.refresh()["status"] == "SOURCE_BACKOFF" and len(calls) == 2
    clock[0] += 1
    assert runner.refresh()["requests"] == 6
    assert runner.refresh()["requests"] == 2
    assert runner.refresh()["requests"] == 0
    assert set(calls) == set(mints)
    assert len(calls) == len(mints) + 1
    assert set(read_scanner_category_evidence(ledger.db, clock[0])) == set(mints)


def test_unlisted_token_reconsiders_only_after_fresh_buy_and_spoofed_receipt_is_rejected(tmp_path):
    ledger = Ledger(tmp_path / "ledger")
    indexed_buys(ledger, tmp_path / "raw", [MINT])
    clock = [AS_OF]
    listed = False

    def wire(request, timeout):
        if not listed:
            raise HTTPError(request.full_url, 404, "fixture", {}, None)
        return Reply(request.full_url, MINT, ["Meme"])

    runner = AutoBuyCategory(ledger.db, api_key="fixture-key",
                             collect=partial(capture, open_url=wire), clock=lambda: clock[0])
    assert runner.refresh()["requests"] == 1
    assert runner.refresh()["requests"] == 0
    clock[0] += 1
    ledger.db.execute("UPDATE signatures SET slot=slot+100")
    listed = True
    assert runner.refresh()["receipts"] == 1
    assert read_scanner_category_evidence(ledger.db, clock[0], mint=MINT)[MINT].status == "VERIFIED_MEME"
    raw = ledger.db.execute("SELECT receipt FROM buy_category_auto WHERE mint=?", (MINT,)).fetchone()[0]
    receipt = json.loads(raw)
    receipt["body"] = receipt["body"].replace(MINT, UNKNOWN)
    receipt["sha256"] = hashlib.sha256(receipt["body"].encode()).hexdigest()
    receipt.update(mint=UNKNOWN, url=COINGECKO_SOLANA + UNKNOWN)
    ledger.db.execute("UPDATE buy_category_auto SET receipt=? WHERE mint=?", (json.dumps(receipt), MINT))
    assert read_scanner_category_evidence(ledger.db, clock[0]) == {}
