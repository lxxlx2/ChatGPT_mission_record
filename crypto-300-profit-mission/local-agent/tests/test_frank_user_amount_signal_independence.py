"""Regression for PR #112: independently authorized V1 signal != follow quote.

All writes here target synthetic temporary SQLite databases. No RPC,
Jupiter, real Gmail, macOS notifications, or production installation.
"""
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from mission_agent.mission_control.delivery import render
from mission_agent.mission_control.policy import evaluate, load_policy
from mission_agent.mission_control.service import MissionMemeService
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy as source_policy_load
from mission_agent.signals.store import Ledger

from test_mission_control_delivery import event as sample_decision_event
from test_mission_control_service import _candidate
from mission_agent.mission_control.db import ControlDB

ROOT = Path(__file__).resolve().parents[1]
NO_SIZE_POLICY = ROOT / "config/follow_policy_v1.approved.json"
SOURCE_POLICY = ROOT / "config/frank_local_signal_v1.json"
ACC = {"signal_type": "FRANK_ACCUMULATION_SIGNAL", "stage": "PRECONFIRM",
       "reason_codes": ["TEST_SOURCE_STAGE"]}
MULT = {"signal_type": "FRANK_MULTIPLE_SIGNAL", "stage": "SUSPECTED_CONVICTION",
        "reason_codes": ["TEST_SOURCE_STAGE"]}


class NoNetworkQuotes:
    calls = 0

    def quote_usdc_to_token(self, *args, **kwargs):
        self.calls += 1
        raise AssertionError("NO_USER_AMOUNT_MUST_NOT_INVOKE_JUPITER")

    def quote_token_to_usdc(self, *args, **kwargs):
        self.calls += 1
        raise AssertionError("NO_USER_AMOUNT_MUST_NOT_INVOKE_EXIT_QUOTES")


def test_source_acc_multiple_outboxes_survive_unpriced_control_cycle(tmp_path):
    """Actual independent V1 Engine -> source SQLite -> Control view/decision.

    Two fresh source model signal records are emitted by Engine._emit(), not
    inserted as pretend Mission Control BUY alerts. Their V1 outbox remains
    independent of the optional Mission Control assessment and is not drained.
    """
    now = int(time.time())
    prod = tmp_path / "production-fixture"
    prod.mkdir()
    health = {
        "status": "RUNNING",
        "pid": os.getpid(),
        "last_successful_poll": datetime.now(timezone.utc).isoformat(),
        "poll_interval_seconds": 30,
        "source_drift": False,
        "consecutive_errors": 0,
    }
    (prod / "health.json").write_text(json.dumps(health))
    ledger = Ledger(prod / "forward.sqlite")
    engine = Engine(ledger, source_policy_load(SOURCE_POLICY), dry_run=False)

    for mint, kind, suffix in (("Mint111", ACC, "a"), ("Mint222", MULT, "b")):
        _, state, _ = _candidate(now, mint=mint, episode="ep-" + suffix, signal="v1-" + suffix)
        state.update(person_id="frank", mint=mint,
                     accumulation_emitted=False, multiple_emitted=False)
        ledger.db.execute(
            "INSERT INTO v1_states(person_id,mint,body) VALUES(?,?,?)",
            ("frank", mint, json.dumps(state)),
        )
        assert engine._emit(state, now, kind) is not None
    ledger.db.commit()
    original_signals = [
        tuple(row) for row in ledger.db.execute(
            "SELECT signal_id,signal_type,content_hash,body FROM signals ORDER BY signal_id"
        ).fetchall()
    ]
    original_outbox = [
        tuple(row) for row in ledger.db.execute(
            "SELECT signal_id,channel,status FROM outbox ORDER BY signal_id,channel"
        ).fetchall()
    ]
    assert len(original_signals) == 2
    assert len(original_outbox) == 3
    assert {r[1] for r in original_outbox} == {"local", "gmail"}
    assert all(row[2] == "PENDING" for row in original_outbox)
    assert ledger.db.execute("SELECT COUNT(*) FROM email_content").fetchone()[0] == 1
    ledger.db.close()

    quotes = NoNetworkQuotes()
    service = MissionMemeService(
        production_root=prod,
        control_root=tmp_path / "control",
        policy_path=NO_SIZE_POLICY,
        live_delivery=False,
    )
    service.jupiter = quotes
    service.outcomes.jupiter = quotes
    result = service.cycle()
    assert result["candidate_errors"] == []
    assert result["evaluated_count"] == 2
    assert result["delivery_allowed"] is False
    assert quotes.calls == 0
    assert service.control.db.execute("SELECT COUNT(*) FROM decision_outbox").fetchone()[0] == 0
    latest = [
        json.loads(row[0]) for row in service.control.db.execute(
            "SELECT body FROM candidate_latest ORDER BY mint"
        ).fetchall()
    ]
    assert len(latest) == 2
    for payload in latest:
        assert payload["decision"] == "WAIT"
        assert payload["inputs"]["source_signal_id"]
        assert payload["inputs"]["source_signal_type"] in {
            "FRANK_ACCUMULATION_SIGNAL", "FRANK_MULTIPLE_SIGNAL"
        }
        assert payload["metrics"]["execution_assessment_status"] == "NOT_ASSESSED"
        assert payload["inputs"]["quote"]["reason"] == "USER_ORDER_AMOUNT_NOT_SPECIFIED"
        assert payload["inputs"]["quote_observed_at"] is None
        assert "NO_EXECUTABLE_JUPITER_ROUTE" not in payload["reasons"]
    service.close()

    with sqlite3.connect(prod / "forward.sqlite") as db:
        assert [
            tuple(row) for row in db.execute(
                "SELECT signal_id,signal_type,content_hash,body FROM signals ORDER BY signal_id"
            )
        ] == original_signals
        assert [
            tuple(row) for row in db.execute(
                "SELECT signal_id,channel,status FROM outbox ORDER BY signal_id,channel"
            )
        ] == original_outbox


def test_no_amount_is_not_market_route_failure_or_fake_jupiter_timestamp():
    policy, _ = load_policy(NO_SIZE_POLICY)
    assert "quote_usdc_amount" not in policy["decision"]
    candidate = {
        "runtime_status": "LIVE", "position_state": "OPEN", "current_raw": "500",
        "pattern": "ACCUMULATION", "latest_side": "BUY",
        "latest_buy_at": 1000, "latest_buy_price_usdc": "1",
    }
    for pattern in ("ACCUMULATION", "MULTIPLE"):
        q = {"status": "SKIPPED", "source": "NONE",
             "reason": "USER_ORDER_AMOUNT_NOT_SPECIFIED", "observed_at": None}
        result = evaluate({**candidate, "pattern": pattern}, q, policy, now=1005)
        assert result["decision"] == "WAIT"
        assert result["metrics"]["execution_assessment_status"] == "NOT_ASSESSED"
        assert "USER_ORDER_AMOUNT_NOT_SPECIFIED" in result["missing"]
        assert "NO_EXECUTABLE_JUPITER_ROUTE" not in result["reasons"]
        assert "EXECUTION_IMPACT_TOO_HIGH" not in result["reasons"]


def test_historical_impact_vs_missing_amount_rendering_are_distinct(tmp_path):
    db = ControlDB(tmp_path / "render.sqlite")
    original = sample_decision_event(db)
    stored = json.loads(original["body"])
    stored["decision"] = "WAIT"
    stored["reasons"] = ["EXECUTION_IMPACT_TOO_HIGH"]
    stored["missing"] = []
    high = render({"body": stored})
    assert "预计交易价格冲击超过策略阈值" in high["body"]
    assert "未指定用户交易金额" not in high["body"]
    stored["reasons"] = ["EXECUTION_NOT_ASSESSED_USER_AMOUNT_MISSING"]
    stored["missing"] = ["USER_ORDER_AMOUNT_NOT_SPECIFIED"]
    stored["inputs"]["quote"] = {
        "status": "SKIPPED", "source": "NONE",
        "reason": "USER_ORDER_AMOUNT_NOT_SPECIFIED",
    }
    stored["inputs"]["quote_observed_at"] = None
    stored["metrics"] = {
        "frank_buy_age_seconds": "1",
        "execution_assessment_status": "NOT_ASSESSED",
    }
    no_amount = render({"body": stored})
    assert "未指定用户交易金额" in no_amount["body"]
    assert "未请求 Jupiter 执行报价" in no_amount["body"]
    assert "Jupiter 报价观察时间：未记录" in no_amount["body"]
    assert "指定金额的参考报价" not in no_amount["body"]
    db.close()
