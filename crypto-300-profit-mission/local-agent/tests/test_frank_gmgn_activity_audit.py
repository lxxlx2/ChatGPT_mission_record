"""Focused provenance and complete-window tests for GMGN-vs-Mission review."""
from __future__ import annotations

import json
import sqlite3
from types import SimpleNamespace

import pytest

from scripts import audit_frank_gmgn_activity as m


W = m.ROOT_WALLET
MINT = "HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy"
S1 = "4sP6iSpctgnnbKsLcGRn1YvaPB7TF9EGc1A6KL4G7gGwLKdP1Jm6LfEH3fs9UhQLMFNPwJ6tmS4FaEAaGT9XCC9S"
S2 = "3" * 88
S3 = "5" * 88
T0, T1 = m.START, m.END


def db_fixture(tmp_path):
    path = tmp_path / "forward.sqlite"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE signatures (
            wallet TEXT NOT NULL, signature TEXT NOT NULL,
            person_id TEXT NOT NULL, block_time INTEGER NOT NULL
        );
        CREATE TABLE trades (
            wallet TEXT NOT NULL, signature TEXT NOT NULL,
            mint TEXT NOT NULL, side TEXT NOT NULL,
            block_time INTEGER NOT NULL
        );
    """)
    con.execute("INSERT INTO signatures VALUES(?,?,?,?)", (W, S1, "frank", T0 + 500))
    con.execute("INSERT INTO signatures VALUES(?,?,?,?)", (W, S2, "frank", T0 + 300))
    con.execute("INSERT INTO trades VALUES(?,?,?,?,?)", (W, S1, MINT, "BUY", T0 + 500))
    con.commit()
    con.close()
    return path


def fake_cli(pages, checked=0):
    calls=[]
    def run(argv, **kwargs):
        calls.append(argv)
        if argv[1:3] == ["config","--check"]:
            return SimpleNamespace(returncode=checked,stdout="",stderr="")
        cursor = argv[argv.index("--cursor") + 1] if "--cursor" in argv else None
        payload = pages[cursor]
        return SimpleNamespace(returncode=0,stdout=json.dumps(payload),stderr="")
    return run, calls


def page(activities, next_cursor=None):
    return {"code":0,"data":{"activities":activities,"next":next_cursor}}


def activity(sig, kind, tm, token=MINT):
    return {
        "tx_hash":sig,"event_type":kind,"timestamp":tm,
        "token":{"address":token},
    }


def test_same_exact_window_reports_signature_coverage_and_side_discrepancies(tmp_path):
    db=db_fixture(tmp_path)
    run,calls=fake_cli({
        None: page([
            activity(S3,"sell",T1 + 60),
            activity(S1,"buy",T0 + 500),
            activity(S2,"buy",T0 + 300),
        ],next_cursor="cursor-2"),
        "cursor-2": page([activity("6"*88,"sell",T0 - 1)]),
    })
    report=m.audit(db,T0,T1,tmp_path / "research",cli_path="gmgn-cli",run=run)
    assert report["status"] == "THIRD_PARTY_ACTIVITY_RECONCILED_REVIEW_ONLY"
    assert report["gmgn_unique_trade_signatures"] == 2
    assert report["gmgn_signatures_missing_from_root"] == 0
    assert report["gmgn_signatures_not_in_mission_trades"] == 1
    assert report["findings"]["IN_ROOT_NOT_CLASSIFIED_TRADE"] == 1
    assert report["findings"]["MATCH_SIDE_MINT"] == 1
    assert report["gmgn_pages_retrieved"] == 2
    assert report["trades_onchain_confirmed_by_this_script"] == 0
    assert report["production_db_writes"] == 0
    assert report["emails_sent"] == 0
    assert calls[0][1:3] == ["config","--check"]
    assert all("--raw" in x for x in calls[1:])


def test_missing_gmgn_auth_never_reports_a_complete_comparison(tmp_path):
    db=db_fixture(tmp_path)
    run,_=fake_cli({},checked=1)
    report=m.audit(db,T0,T1,tmp_path / "research",cli_path="gmgn-cli",run=run)
    assert report["status"] == "GMGN_SOURCE_UNAVAILABLE"
    assert report["gmgn_reason"] == "GMGN_KEY_NOT_CONFIGURED_OR_INVALID"
    assert not report["comparison_complete"]
    assert report["mission_trades"] == 1


def test_gmgn_truncated_history_does_not_pass_window(tmp_path):
    run,_=fake_cli({
        None: page([activity(S1,"buy",T1-5)],next_cursor=None),
    })
    with pytest.raises(m.IncompleteEvidence,match="GMGN_HISTORY_ENDS_BEFORE_WINDOW_COVERED"):
        m.collect_gmgn(W,T0,T1,cli_path="gmgn-cli",run=run)


def test_root_absent_activity_is_discrepancy_not_invented_trade(tmp_path):
    db=db_fixture(tmp_path)
    local=m.local_window(db,T0,T1)
    report=m.diff(local,[m.normalize(activity(S3,"buy",T0+100))])
    assert report["gmgn_signatures_missing_from_root"] == 1
    assert report["findings"]["NOT_IN_ROOT_SIGNATURE_INDEX"] == 1
    assert report["trades_onchain_confirmed_by_this_script"] == 0


def test_gmgn_requires_provenance_fields_and_chronological_order():
    with pytest.raises(m.IncompleteEvidence,match="GMGN_SIGNATURE_MISSING"):
        m.normalize({"event_type":"buy","timestamp":T1,"token":{"address":MINT}})
    with pytest.raises(m.IncompleteEvidence,match="GMGN_TRADE_MINT_MISSING"):
        m.normalize({"tx_hash":S1,"event_type":"buy","timestamp":T1})
    run,_=fake_cli({None: page([
        activity(S1,"buy",T0+20),
        activity(S2,"sell",T0+200),
    ],"next")})
    with pytest.raises(m.IncompleteEvidence,match="GMGN_ACTIVITY_NOT_NEWEST_FIRST"):
        m.collect_gmgn(W,T0,T1,cli_path="gmgn-cli",run=run)


def test_local_db_read_only_and_report_outside_production(tmp_path):
    db=db_fixture(tmp_path)
    orig=db.read_bytes()
    read=m.local_window(db,T0,T1)
    assert db.read_bytes()==orig
    assert len(read["signatures"]) == 2
    output=tmp_path/"isolated-output"
    path=m.write_report(output,{"status":"RESEARCH_ONLY"})
    assert path.stat().st_mode & 0o077 == 0
    assert json.loads(path.read_text())["status"]=="RESEARCH_ONLY"


def test_unknown_gmgn_activity_kind_is_not_silently_ignored_as_zero_buys():
    with pytest.raises(m.IncompleteEvidence,match="GMGN_ACTIVITY_TYPE_UNRECOGNIZED"):
        m.normalize(activity(S1,"swap_unknown_new_schema",T0 + 10))
    row=m.normalize(activity(S1,"transfer",T0 + 10))
    assert row["side"] is None
