"""Several independent buys may share a signature while V1 counts one event per mint."""
import json
import sqlite3

import pytest

from mission_agent.frank.parser import DEX_PROGRAMS, WSOL
from mission_agent.frank.rpc import WALLET
from mission_agent.meme.holder_ranks import _b58
from mission_agent.mission_control.frank_buys import read_buys
from mission_agent.mission_control.wallet_activity import activity
from mission_agent.mission_control.wallet_history import export_history
from mission_agent.mission_control.wallet_watch import from_sqlite
from mission_agent.signals.__main__ import inspect
from mission_agent.signals.buy_admission import BuyDeliveryGate, admit_buy, qualification
from mission_agent.signals.classifier import USDT, classify
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import USDC, load_policy
from mission_agent.signals.scanner import Scanner
from mission_agent.signals.store import Ledger
from test_frank_rebuild_buys import AS_OF, MINT, UNKNOWN, config, put
from test_frank_v1 import POLICY


DEX = sorted(DEX_PROGRAMS)[0]
TOKEN = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
SIGNATURE = _b58(bytes([8]) * 64)


def _purchase(mints, *, parsed=True, quotes=None):
    quotes = quotes or [USDC] * len(mints)
    names = [WALLET]
    before, after, outer, inner, logs = [], [], [], [], []
    for i, (mint, quote) in enumerate(zip(mints, quotes, strict=True)):
        start = len(names)
        payment, received, spent_by_market, paid_to_market = [
            _b58(bytes([80 + j]) * 32) for j in range(start, start + 4)
        ]
        names.extend((payment, received, spent_by_market, paid_to_market))

        def token(index, asset, amount):
            return {"accountIndex": index, "mint": asset, "owner": WALLET,
                    "uiTokenAmount": {"amount": str(amount), "decimals": 6}}

        paid = (12000 + i) * 10**6
        bought = (i + 1) * 10**6
        before.extend((token(start, quote, paid), token(start + 1, mint, 0)))
        after.extend((token(start, quote, 0), token(start + 1, mint, bought)))

        def transfer(src, dst, asset, amount, owner):
            return {"programId": TOKEN, "parsed": {"type": "transferChecked", "info": {
                "source": src, "destination": dst, "mint": asset, "authority": owner,
                "tokenAmount": {"amount": str(amount), "decimals": 6},
            }}}

        ix = {"programId": DEX}
        if parsed:
            ix["parsed"] = {"type": "swap", "info": {"authority": WALLET}}
        outer.append(ix)
        inner.append({"index": i, "instructions": [
            transfer(payment, paid_to_market, quote, paid, WALLET),
            transfer(spent_by_market, received, mint, bought, paid_to_market),
        ]})
        logs.extend((f"Program {DEX} invoke [1]", "Program log: Instruction: Swap",
                     f"Program {TOKEN} invoke [2]", f"Program {TOKEN} success",
                     f"Program {TOKEN} invoke [2]", f"Program {TOKEN} success",
                     f"Program {DEX} success"))
    return {
        "slot": 12, "blockTime": AS_OF - 1,
        "transaction": {"signatures": [SIGNATURE], "message": {
            "accountKeys": [{"pubkey": key, "signer": i == 0} for i, key in enumerate(names)],
            "instructions": outer,
        }},
        "meta": {"err": None, "fee": 5000, "preBalances": [100000] * len(names),
                 "postBalances": [95000] + [100000] * (len(names) - 1),
                 "preTokenBalances": before, "postTokenBalances": after,
                 "innerInstructions": inner, "logMessages": logs},
    }


def _store(ledger, tx):
    event = classify(SIGNATURE, tx, WALLET)
    assert ledger.put("frank", event, event["evidence"]["raw_transaction_sha256"], "fixture")
    return event


def _both_assets(cfg):
    config(cfg)
    doc = json.loads(cfg.read_text())
    doc["records"].append({**doc["records"][0], "mint": UNKNOWN, "name": "第二币"})
    cfg.write_text(json.dumps(doc))


@pytest.mark.parametrize("parsed", [False, True])
def test_scanner_keeps_two_distinct_mints_and_each_payment(tmp_path, parsed):
    tx = _purchase([MINT, UNKNOWN], parsed=parsed)
    path, cfg = tmp_path / "ledger.sqlite", tmp_path / "qualifications.json"
    ledger = Ledger(path)
    _both_assets(cfg)
    checkpoint = _b58(bytes([7]) * 64)
    ledger.checkpoint(WALLET, checkpoint, 1)

    class RPC:
        def signatures(self, before=None):
            assert before is None
            return [{"signature": SIGNATURE, "slot": 12, "blockTime": AS_OF - 1},
                    {"signature": checkpoint, "slot": 1, "blockTime": AS_OF - 60}]

        def transaction(self, sig):
            assert sig == SIGNATURE
            return tx

    scanner = Scanner(ledger, {WALLET: "frank"}, tmp_path / "raw", rpcs={WALLET: RPC()}, mode="LIVE")
    assert scanner.cycle(WALLET)["new_signatures"] == 1
    assert scanner.cycle(WALLET)["new_signatures"] == 0
    assert ledger.cursor(WALLET)["signature"] == SIGNATURE
    assert len(list((tmp_path / "raw").glob("*.json.gz"))) == 1
    assert ledger.db.execute("SELECT count(*) FROM signatures").fetchone()[0] == 1
    rows = read_buys(path, cfg, as_of=AS_OF)["rows"]
    assert [(a["mint"], a["leg_index"], a["paid"], a["quantity"]) for a in rows] == [
        (UNKNOWN, 1, "12001", "2"), (MINT, 0, "12000", "1"),
    ]
    assert [a["leg_index"] for a in activity(path, AS_OF)["rows"][0]["trades"]] == [0, 1]
    state = Engine(ledger, load_policy(POLICY))
    assert state.drain() == 1
    assert state.drain() == 0
    assert state._state("frank", MINT)["current_raw"] == "1000000"
    assert state._state("frank", UNKNOWN)["current_raw"] == "2000000"
    assert state.summary()["tokens_evaluated"] == 2


def test_repeated_mint_retains_legs_without_increasing_v1_event_count(tmp_path):
    db, cfg = tmp_path / "ledger.sqlite", tmp_path / "qualifications.json"
    ledger = Ledger(db)
    config(cfg)
    event = _store(ledger, _purchase([MINT, MINT, MINT]))
    rows = read_buys(db, cfg, as_of=AS_OF)["rows"]
    assert [row["leg_index"] for row in rows] == [2, 1, 0]
    assert [row["leg_index"] for row in activity(db, AS_OF)["rows"][0]["trades"]] == [0, 1, 2]
    diagnostic, = inspect(ledger.db, SIGNATURE)
    assert diagnostic["trade_record"] is None
    assert [row["leg_index"] for row in diagnostic["trade_records"]] == [0, 1, 2]
    history = export_history(db)
    assert history["multileg_conflicting_trade_keys"] == 0
    assert [r["trade_raw_fields"]["leg_index"] for r in history["records"]] == [0, 1, 2]
    assert history["per_mint_cashflow_observations"][MINT]["direct_local_usdc_buy_outflow"] == "36003.000000"
    engine = Engine(ledger, load_policy(POLICY))
    assert engine.drain() == 1
    m = engine._state("frank", MINT)
    assert len(m["events"]) == 1
    assert m["current_raw"] == "6000000" and m["events"][0]["quote_quantity"] == "36003"
    watched = next(r for r in from_sqlite(db)["rows"] if r["mint"] == MINT)
    assert watched["local_recognized_buys"] == 3
    assert watched["conflicting_trade_signatures"] == 0
    assert watched["last_observed_quote_quantity"] == "12002"
    assert ledger.db.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0
    gate = BuyDeliveryGate(cfg, clock=lambda: AS_OF)
    fact, blocked = gate.assess(ledger.db, {
        "delivery_mode": "LIVE", "person_id": "frank", "mint": MINT,
        "triggering_signature": SIGNATURE, "latest_trade_signature": SIGNATURE,
        "latest_buy_signature": SIGNATURE, "triggered_at": AS_OF - 1,
        "signal_type": "FRANK_MULTIPLE_SIGNAL",
    })
    assert blocked is None
    assert (fact["leg_indices"], fact["quantity"], fact["paid"]) == ([0, 1, 2], "6", "36003")
    identity = {"mint": MINT, "wallet": WALLET, "signature": SIGNATURE, "slot": 12,
                "block_time": AS_OF - 1, "raw_hash": event["evidence"]["raw_transaction_sha256"]}
    assert admit_buy(event, qualification(cfg, AS_OF), **identity, leg_index=1)["paid"] == "12001"


def test_scoped_wrapped_sol_debits_exclude_rent_and_other_lamport_outflow(tmp_path):
    tx = _purchase([MINT, UNKNOWN], quotes=[WSOL, WSOL])
    msg = tx["transaction"]["message"]
    meta = tx["meta"]
    setup, cleanup = [], []
    for idx, group in enumerate(meta["innerInstructions"]):
        source = group["instructions"][0]["parsed"]["info"]["source"]
        group["index"] += 2
        group["instructions"][0]["parsed"]["info"]["tokenAmount"]["decimals"] = 9
        setup.append({"programId": TOKEN, "parsed": {"type": "initializeAccount3", "info": {
            "mint": WSOL, "account": source, "owner": WALLET,
        }}})
        cleanup.append({"programId": TOKEN, "parsed": {"type": "closeAccount", "info": {
            "account": source, "owner": WALLET, "destination": WALLET,
        }}})
    msg["instructions"] = setup + msg["instructions"] + cleanup
    for field in ("preTokenBalances", "postTokenBalances"):
        meta[field] = [row for row in meta[field] if row["mint"] != WSOL]
    meta["logMessages"] = []
    # Total wallet lamport change includes items besides these specific debits.
    meta["preBalances"][0] = 80_000_000_000
    meta["postBalances"][0] = 55_000_000_000
    db, cfg = tmp_path / "ledger.sqlite", tmp_path / "qualifications.json"
    ledger = Ledger(db)
    _both_assets(cfg)
    _store(ledger, tx)
    assert [(row["leg_index"], row["currency"], row["paid"]) for row in read_buys(db, cfg, as_of=AS_OF)["rows"]] == [
        (3, "SOL", "12.001"), (2, "SOL", "12"),
    ]
    cleanup[0]["parsed"]["info"]["destination"] = _b58(bytes([12]) * 32)
    classified = classify(SIGNATURE, tx, WALLET)
    assert classified["classification"] == "UNKNOWN_NEEDS_REVIEW"


def test_repeated_mint_multiple_quote_currencies_do_not_become_a_usdc_signal(tmp_path):
    db, cfg = tmp_path / "ledger.sqlite", tmp_path / "qualifications.json"
    ledger = Ledger(db)
    config(cfg)
    event = _store(ledger, _purchase([MINT, MINT], quotes=[USDC, USDT]))
    assert [row["currency"] for row in read_buys(db, cfg, as_of=AS_OF)["rows"]] == ["USDT", "USDC"]
    engine = Engine(ledger, load_policy(POLICY))
    assert engine.drain() == 1
    state = engine._state("frank", MINT)
    assert len(state["events"]) == 1
    assert state["events"][0]["amount_predicate"] == "UNDETERMINED"
    assert engine.summary()["multiple_trigger_count"] == 0
    identity = {"mint": MINT, "wallet": WALLET, "signature": SIGNATURE, "slot": 12,
                "block_time": AS_OF - 1, "raw_hash": event["evidence"]["raw_transaction_sha256"]}
    assert admit_buy(event, qualification(cfg, AS_OF), **identity) is None


@pytest.mark.parametrize("invalid", ["same_outer", "misaligned_logs", "missing_transfer", "different_debit"])
def test_unattributable_multi_target_remains_without_buy_legs(invalid):
    tx = _purchase([MINT, UNKNOWN], parsed=False)
    if invalid == "same_outer":
        tx["meta"]["innerInstructions"][0]["instructions"].extend(tx["meta"]["innerInstructions"].pop()["instructions"])
    elif invalid == "misaligned_logs":
        tx["meta"]["logMessages"].pop()
    elif invalid == "missing_transfer":
        tx["meta"]["innerInstructions"][0]["instructions"].pop()
    else:
        tx["meta"]["innerInstructions"][1]["instructions"][0]["parsed"]["info"]["authority"] = "unverified"
    classified = classify(SIGNATURE, tx, WALLET)
    assert classified["classification"] == "UNKNOWN_NEEDS_REVIEW"
    assert not classified.get("trade_legs")


def test_old_trade_rows_and_cursor_survive_schema_migration(tmp_path):
    db = tmp_path / "ledger.sqlite"
    # Construct the old table, including an existing non-contiguous rowid.
    with sqlite3.connect(db) as legacy:
        legacy.execute("CREATE TABLE trades(wallet TEXT,signature TEXT,mint TEXT,episode_id TEXT,"
                       "block_time INTEGER,side TEXT,body TEXT,PRIMARY KEY(wallet,signature))")
        legacy.execute("INSERT INTO trades(rowid,wallet,signature,mint,episode_id,block_time,side,body) "
                       "VALUES(?,?,?,?,?,?,?,?)", (41, WALLET, "historical", MINT, "episode", AS_OF - 100, "BUY", "{}"))
    ledger = Ledger(db)
    ledger.checkpoint(WALLET, "checkpoint", 5)
    _store(ledger, _purchase([MINT, UNKNOWN]))
    old = ledger.db.execute("SELECT rowid,body FROM trades WHERE signature='historical'").fetchone()
    assert tuple(old) == (41, "{}")
    assert ledger.cursor(WALLET)["signature"] == "checkpoint"
    assert ledger.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    ledger.db.close()
    reopened = Ledger(db)
    assert reopened.db.execute("SELECT count(*) FROM trades").fetchone()[0] == 3
    with pytest.raises(sqlite3.IntegrityError):
        reopened.db.execute("INSERT INTO trades SELECT * FROM trades WHERE signature=? LIMIT 1", (SIGNATURE,))
