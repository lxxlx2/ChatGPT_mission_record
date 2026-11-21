"""Whole-window invariants for the existing D1 read-only backend."""
import base64
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
from types import SimpleNamespace

import pytest

from mission_agent.mission_control.wallet_activity import activity
from mission_agent.mission_control.wallet_activity_paging import activity_page
from mission_agent.mission_control import server

NOW = 1_795_000_000
WALLET, MINT_A, MINT_B = "2"*32, "3"*32, "4"*32


def make_db(path, count=17):
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE signatures(wallet TEXT,signature TEXT,person_id TEXT,slot INTEGER,
            block_time INTEGER,seen_at TEXT,raw_hash TEXT,body TEXT);
        CREATE TABLE trades(wallet TEXT,signature TEXT,mint TEXT,side TEXT);
        """)
        for i in range(count):
            add_row(db, i)


def add_row(db, i, *, stamp=NOW-100, person="frank"):
    cls = ["ACTIVE_TRADE", "PASSIVE_TRANSFER", "ATA_CREATE", "FAILED_TX",
           "UNKNOWN_NEEDS_REVIEW"][i % 5]
    alphabet, number, suffix = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz", i+1, ""
    while number:
        number, digit = divmod(number, 58)
        suffix = alphabet[digit] + suffix
    sig = "5"*72 + suffix.rjust(16, "1")
    body = {"classification": cls, "evidence": {"parser_version": "fixture-1",
        "token_balance_deltas": [
            {"mint": MINT_A, "wallet_owned": True, "owner": WALLET, "delta": "3"},
            {"mint": MINT_B, "wallet_owned": False, "owner": "7"*32, "delta": "-3"}]}}
    db.execute("INSERT INTO signatures VALUES(?,?,?,?,?,?,?,?)",
               (WALLET, sig, person, 100+i, stamp, "2026-11-01T00:00:00+00:00",
                "a"*64, json.dumps(body)))
    if cls == "ACTIVE_TRADE":
        db.execute("INSERT INTO trades VALUES(?,?,?,?)", (WALLET, sig, MINT_A, "BUY" if i % 2 else "SELL"))


def all_pages(path, **kwargs):
    result, cursor, totals = [], None, set()
    while True:
        page = activity_page(path, NOW, cursor=cursor, **kwargs)
        totals.add(page["total_signatures"])
        result.extend(page["rows"])
        assert page["has_more"] == (page["next_cursor"] is not None)
        if not page["has_more"]:
            break
        cursor = page["next_cursor"]
    return result, totals


def test_more_than_old_total_guard_is_lossless_and_readonly(tmp_path):
    p = tmp_path/"source.sqlite"
    make_db(p, 5103)
    before = hashlib.sha256(p.read_bytes()).hexdigest()
    full = activity(p, NOW, days=30)
    rows, totals = all_pages(p, days=30, page_size=233)
    assert len(full["rows"]) == len(rows) == 5103
    assert totals == {5103}
    assert len({r["index_rowid"] for r in rows}) == 5103
    assert {r["index_rowid"] for r in rows} == {r["index_rowid"] for r in full["rows"]}
    assert hashlib.sha256(p.read_bytes()).hexdigest() == before


def test_equal_timestamps_and_intervening_backfill_do_not_duplicate(tmp_path):
    p = tmp_path/"source.sqlite"
    make_db(p)
    first = activity_page(p, NOW, days="all", page_size=4)
    with sqlite3.connect(p) as db:
        add_row(db, 100, stamp=NOW-10_000)
    rows = list(first["rows"])
    cursor = first["next_cursor"]
    while cursor:
        page = activity_page(p, NOW+60, days="all", page_size=3, cursor=cursor)
        assert page["as_of"] == NOW
        assert page["total_signatures"] == 17
        rows += page["rows"]
        cursor = page["next_cursor"]
    assert len(rows) == len({r["index_rowid"] for r in rows}) == 17
    assert not page["immutable_source_snapshot"]
    assert "MAY_BE_UPDATED" in page["index_read_semantics"]


def test_filters_include_owned_passive_activity_not_counterparty(tmp_path):
    p = tmp_path/"source.sqlite"
    make_db(p)
    rows, totals = all_pages(p, days="all", page_size=2, mint=MINT_A)
    assert len(rows) == 17 and totals == {17}
    passive, _ = all_pages(p, days="all", kind="PASSIVE_TRANSFER", mint=MINT_A)
    assert passive and all(r["class"] == "PASSIVE_TRANSFER" for r in passive)
    other, totals = all_pages(p, days="all", mint=MINT_B)
    assert other == [] and totals == {0}
    buys, _ = all_pages(p, days="all", kind="BUY")
    sells, _ = all_pages(p, days="all", kind="SELL")
    assert buys and sells
    assert all(t["side"] == "BUY" for r in buys for t in r["trades"])
    assert all(t["side"] == "SELL" for r in sells for t in r["trades"])


def test_all_range_keeps_untimed_rows_and_excludes_other_person_or_future(tmp_path):
    p = tmp_path/"source.sqlite"
    make_db(p, 1)
    with sqlite3.connect(p) as db:
        add_row(db, 1, stamp=None)
        add_row(db, 2, stamp=NOW+1)
        add_row(db, 3, person="other")
        add_row(db, 4, stamp=NOW-40*86400)
    rows, total = all_pages(p, days="all", page_size=1)
    assert len(rows) == 3 and total == {3}
    assert sum(r["at"] is None for r in rows) == 1
    assert len(activity(p, NOW, days=30)["rows"]) == 1


def test_projection_exposes_evidence_without_raw_path_or_endpoint(tmp_path):
    p = tmp_path/"source.sqlite"
    make_db(p, 2)
    r = activity_page(p, NOW)["rows"]
    assert all(x["slot"] and x["raw_sha256"] == "a"*64 for x in r)
    assert all(x["parser_version"] == "fixture-1" and x["first_indexed_at"] for x in r)
    assert r[0]["wallet_mints"] == [MINT_A]
    assert {x["trade_match_status"] for x in r} == {"MATCHED", "NOT_APPLICABLE"}
    assert str(tmp_path) not in json.dumps(r)


@pytest.mark.parametrize("kwargs", [
    {"days": True}, {"days": 31}, {"page_size": 0}, {"page_size": True},
    {"page_size": 1001}, {"kind": "invalid"}, {"mint": "bad"},
    {"cursor": "bad!"}, {"cursor": "a"*4097}])
def test_invalid_requests_fail_closed(tmp_path, kwargs):
    p = tmp_path/"source.sqlite"
    make_db(p, 1)
    with pytest.raises(ValueError):
        activity_page(p, NOW, **kwargs)


def test_cursor_rejects_source_replacement_or_changed_filter(tmp_path):
    p = tmp_path/"source.sqlite"
    make_db(p)
    first = activity_page(p, NOW, page_size=2)
    with pytest.raises(ValueError, match="QUERY_CHANGED"):
        activity_page(p, NOW, cursor=first["next_cursor"], kind="BUY")
    replacement = tmp_path/"replacement.sqlite"
    shutil.copyfile(p, replacement)
    replacement.replace(p)
    with pytest.raises(ValueError, match="SOURCE_CHANGED"):
        activity_page(p, NOW, cursor=first["next_cursor"])


def test_malformed_cursor_field_types_are_rejected(tmp_path):
    p = tmp_path/"source.sqlite"
    make_db(p)
    cursor = activity_page(p, NOW, page_size=2)["next_cursor"]
    token = json.loads(base64.urlsafe_b64decode(cursor+"="*(-len(cursor)%4)))
    for key, bad in [("v", True), ("at", True), ("kind", []), ("after", [True, 1]), ("fence", -1), ("fence", 2**63)]:
        broken = dict(token); broken[key] = bad
        value = base64.urlsafe_b64encode(json.dumps(broken).encode()).decode().rstrip("=")
        with pytest.raises(ValueError, match="INVALID_ACTIVITY_CURSOR"):
            activity_page(p, NOW, cursor=value)


def test_actual_handler_dispatches_page_and_keeps_legacy_full_contract():
    h = server.Handler.__new__(server.Handler)
    h._allowed_host = lambda: True
    h._json = lambda value, status=200: (value, status)
    calls = []
    h.state = SimpleNamespace(frank_signed_activity=lambda days, **kw: calls.append((days, kw)) or {"days": days})
    h.path = "/api/frank-signed-activity?days=all&limit=200&kind=BUY&mint="+MINT_A
    assert h.do_GET()[1] == 200
    assert calls[-1] == ("all", {"page_size": 200, "cursor": None, "kind": "BUY", "mint": MINT_A})
    h.path = "/api/frank-signed-activity?days=30"
    assert h.do_GET() == ({"days": 30}, 200)
    assert calls[-1] == (30, {})
    for suffix in ["?limit=0", "?cursor=", "?kind=no", "?days=7&days=30", "?mint=bad", "?limit=1&limit=2"]:
        h.path = "/api/frank-signed-activity"+suffix
        assert h.do_GET()[1] == 400

