import base64
import json

import pytest

from mission_agent.mission_control.db import ControlDB, utc
from mission_agent.mission_control.delivery import GmailDelivery, LocalDelivery, render
from mission_agent.signals.gmail import AmbiguousSend


class Provider:
    recipient = "owner@example.invalid"
    def __init__(self):
        self.messages = {}
        self.sent = []
        self.crash = False
        self.ambiguous = False
    def ready(self):
        return None
    def find_sent(self, wire_id, decision_id):
        return [mid for mid, msg in self.messages.items() if decision_id.encode() in base64.urlsafe_b64decode(msg["raw"] + "===")]
    def get(self, mid):
        return self.messages[mid]
    def send(self, raw):
        self.sent.append(raw)
        mid = "gmail-" + str(len(self.sent))
        self.messages[mid] = {
            "id": mid,
            "threadId": "thread-" + mid,
            "labelIds": ["SENT"],
            "raw": base64.urlsafe_b64encode(raw).decode(),
        }
        if self.crash:
            raise SystemExit("post-acceptance crash")
        if self.ambiguous:
            raise AmbiguousSend("provider accepted but response was ambiguous")
        return {"id": mid, "threadId": "thread-" + mid}


def event(db):
    payload = {
        "person_id":"frank", "mint":"Mint111111111111111", "episode_id":"ep1",
        "source_signal_id":"sig1", "source_signal_type":"FRANK_MULTIPLE_SIGNAL",
        "decision":"BUY", "created_at":utc(), "policy_id":"P1", "policy_hash":"hash1",
        "inputs":{"pattern":"MULTIPLE","position_state":"OPEN","buy_count":3,"sell_count":0,"latest_side":"BUY","latest_signature":"tx1"},
        "metrics":{"frank_latest_buy_price_usdc":"1","execution_price_usdc":"1.02","price_deviation_pct":"2","price_impact_pct":"0.5"},
        "reasons":["FRANK_MULTIPLE_ACTIVE"], "missing":[], "invalidation":["FRANK_SELL"],
    }
    row = db.record(payload, "P1", "hash1")["event"]
    return row


def age_retry(db, decision_id):
    db.db.execute("update gmail_delivery set last_attempt_at='2000-01-01T00:00:00+00:00' where decision_id=?", (decision_id,))


def test_review_mode_delivery_is_forbidden(tmp_path):
    db = ControlDB(tmp_path / "mission-control.sqlite")
    e = event(db)
    local = LocalDelivery(db, run=lambda *a,**k: pytest.fail("local delivery should not run"))
    local.enqueue(e, forbidden=True)
    GmailDelivery(db).enqueue(e, mode="DRY_RUN_AUDIT", forbidden=True)
    local.drain()
    GmailDelivery(db).drain(Provider())
    assert db.db.execute("select status from local_delivery").fetchone()[0] == "DRY_RUN_AUDIT"
    assert db.db.execute("select status from gmail_delivery").fetchone()[0] == "DRY_RUN_AUDIT"


def test_gmail_same_decision_id_sends_once_and_verifies_sent(tmp_path):
    db = ControlDB(tmp_path / "mission-control.sqlite")
    e = event(db)
    out = GmailDelivery(db)
    out.enqueue(e, mode="LIVE", forbidden=False)
    provider = Provider()
    out.drain(provider)
    out.drain(provider)
    assert len(provider.sent) == 1
    row = out.row(e["decision_id"])
    assert row["status"] == "SENT_VERIFIED"
    assert row["readback_verified"] == 1


def test_post_acceptance_crash_does_not_duplicate_email(tmp_path):
    db = ControlDB(tmp_path / "mission-control.sqlite")
    e = event(db)
    out = GmailDelivery(db)
    out.enqueue(e, mode="LIVE", forbidden=False)
    provider = Provider(); provider.crash = True
    with pytest.raises(SystemExit):
        out.drain(provider)
    assert len(provider.sent) == 1
    assert out.row(e["decision_id"])["status"] == "SENDING"
    provider.crash = False
    age_retry(db, e["decision_id"])
    out.drain(provider)
    assert len(provider.sent) == 1
    assert out.row(e["decision_id"])["status"] == "SENT_VERIFIED"


def test_ambiguous_send_is_never_automatically_resent(tmp_path):
    db = ControlDB(tmp_path / "mission-control.sqlite")
    e = event(db)
    out = GmailDelivery(db)
    out.enqueue(e, mode="LIVE", forbidden=False)
    provider = Provider(); provider.ambiguous = True
    out.drain(provider)
    assert len(provider.sent) == 1
    assert out.row(e["decision_id"])["status"] == "SENT_UNVERIFIED"
    provider.ambiguous = False
    out.drain(provider)
    assert len(provider.sent) == 1
    age_retry(db, e["decision_id"])
    out.drain(provider)
    assert len(provider.sent) == 1
    assert out.row(e["decision_id"])["status"] == "SENT_VERIFIED"


def test_sent_unverified_cannot_remain_ambiguous_forever(tmp_path):
    db = ControlDB(tmp_path / "mission-control.sqlite")
    e = event(db)
    out = GmailDelivery(db)
    out.enqueue(e, mode="LIVE", forbidden=False)
    db.db.execute(
        "update gmail_delivery set status='SENT_UNVERIFIED',created_at='2000-01-01T00:00:00+00:00',last_attempt_at='2000-01-01T00:00:00+00:00' where decision_id=?",
        (e["decision_id"],),
    )
    out.drain(None)
    row=out.row(e["decision_id"])
    assert row["status"]=="MANUAL_REVIEW"
    assert row["last_error"]=="GMAIL_SENT_OUTCOME_UNRESOLVED_TOO_LONG"
    assert db.db.execute("select status from decision_outbox where decision_id=? and channel='gmail'",(e["decision_id"],)).fetchone()[0]=="MANUAL_REVIEW"


def test_mission_control_notification_is_chinese_and_research_friendly(tmp_path):
    db=ControlDB(tmp_path/"mission-control.sqlite")
    e=event(db)
    rendered=render(e)
    assert "[Meme提醒] 可跟" in rendered["subject"]
    assert "结论：可跟" in rendered["body"]
    assert "CA（单独一行，便于长按复制）\nMint111111111111111\n" in rendered["body"]
    assert "Frank 买/卖次数" not in rendered["body"]
    assert "当前可成交价：1.02 USDC" in rendered["body"]
    assert "原因：Frank 当前处于多次强加仓模式" in rendered["body"]
    assert "Policy：" not in rendered["body"]


def test_mission_control_email_mobile_readable_amounts_keep_full_ca(tmp_path):
    db=ControlDB(tmp_path/"mission-control.sqlite")
    e=event(db)
    body=json.loads(e["body"]) if isinstance(e["body"],str) else e["body"]
    mint="METAewgxyPbgwsseH8T16a39CQ5VyVxZi9zXiDPY18m"
    body["mint"]=mint
    body["inputs"]["latest_buy_original_quote_asset"]="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    body["inputs"]["latest_buy_original_quote_quantity"]="40300.819981"
    body["metrics"]["frank_latest_buy_price_usdc"]="0.06281989977852861423955923621"
    body["metrics"]["price_impact_pct"]="0.123456789"
    rendered=render({"body":body})
    assert f"\n{mint}\n" in rendered["body"]
    assert "最近买入投入：40,300.82 USDC" in rendered["body"]
    assert "Frank 参考买价：0.06282 USDC" in rendered["body"]
    assert "预计价格冲击：0.12%" in rendered["body"]
    assert "Decision ID：" not in rendered["body"]


def test_mission_control_email_tiny_prices_remain_nonzero(tmp_path):
    db=ControlDB(tmp_path/"mission-control.sqlite")
    e=event(db)
    body=json.loads(e["body"]) if isinstance(e["body"],str) else e["body"]
    body["metrics"]["frank_latest_buy_price_usdc"]="0.00000000123456789"
    assert "Frank 参考买价：1.23e-9 USDC" in render({"body":body})["body"]
