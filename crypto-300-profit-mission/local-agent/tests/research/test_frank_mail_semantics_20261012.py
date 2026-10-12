"""Future Frank Gmail presentation only: no provider calls or DB migration."""
from copy import deepcopy

from mission_agent.hashing import digest
from mission_agent.mission_control.delivery import render, GmailDelivery


def _event(side="SELL", status="INVENTORY_UNDETERMINED", decision="NO_BUY"):
    return {"body": {
        "mint": "2j5SaS7xy776qCBpyPQbZiyQSAtKiFgrwjfErthnW2ZM",
        "decision": decision,
        "created_at": "2026-10-12T14:57:44+00:00",
        "inputs": {
            "pattern": "MULTIPLE",
            "latest_side": side,
            "position_state": status,
            "latest_buy_original_quote_quantity": 15000,
            "latest_buy_original_quote_asset": "USDC",
            "latest_signature": "fixture_signature_does_not_call_network",
        },
        "metrics": {
            "frank_latest_buy_price_usdc": 0.009932,
            "execution_price_usdc": 0.00720451,
        },
        "reasons": ["POSITION_STATE_INVENTORY_UNDETERMINED"],
        "missing": [],
    }}


def test_sell_and_unconfirmed_position_take_priority_over_historical_multiple():
    mail = render(_event())
    assert "不跟 | Frank 最新卖出 · 仓位不明" in mail["subject"]
    assert "多次强加仓" not in mail["subject"]
    body = mail["body"]
    assert body.startswith("结论：不跟\nFrank 最新动作：卖出  |  当前仓位：仓位不明")
    assert "历史观察模式：多次强加仓" in body
    assert "历史最近一次买入投入：15,000.00 USDC" in body
    assert "技术审计信息（用于交易核查和邮件去重）" in body
    assert body.index("技术审计信息") > body.index("CA（单独一行")
    assert "交易哈希：fixture_signature_does_not_call_network" in body


def test_buy_preserves_accumulation_pattern_in_email_subject():
    mail = render(_event(side="BUY", status="OPEN", decision="BUY"))
    assert "可跟 | 多次强加仓" in mail["subject"]
    assert "Frank 最新动作：买入  |  当前仓位：持仓中" in mail["body"]
    assert "历史观察模式：多次强加仓" in mail["body"]


def test_uncertain_sell_has_explicit_context_even_when_unknown():
    mail = render(_event(side="SELL_POSITION_UNRESOLVED", status="INVENTORY_UNDETERMINED"))
    assert "卖出后仓位待确认" in mail["subject"]
    assert "仓位不明" in mail["subject"]


def test_missing_transaction_signature_does_not_create_fake_hash():
    e = _event()
    del e["body"]["inputs"]["latest_signature"]
    mail = render(e)
    assert "技术审计信息" in mail["body"]
    assert "交易哈希：" not in mail["body"]


def test_template_change_deterministic_and_does_not_mutate_decision():
    e = _event()
    previous = deepcopy(e)
    a, b = render(e), render(e)
    assert a == b and e == previous
    assert a["content_hash"] == digest({"subject":a["subject"],"body":a["body"]})


def test_frozen_provider_wire_footer_keeps_prior_behavior():
    class Stub:
        pass
    out = Stub()
    row = {"body":"FROZEN HISTORICAL CONTENT","decision_id":"immutable-id","content_hash":"immutable-hash"}
    assert GmailDelivery._wire_body(out,row) == (
        "FROZEN HISTORICAL CONTENT\n\n"
        "Mission-Decision-Identity: immutable-id\n"
        "Mission-Content-SHA256: immutable-hash\n")
