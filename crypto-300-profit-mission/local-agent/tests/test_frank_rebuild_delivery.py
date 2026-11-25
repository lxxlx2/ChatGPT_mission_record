from email import message_from_bytes, policy
import json
from types import SimpleNamespace

import pytest

from mission_agent.frank.rpc import WALLET
from mission_agent.meme.holder_ranks import _b58
from mission_agent.signals.buy_admission import BACKPACK_MINT, BuyDeliveryGate
from mission_agent.signals.delivery import LocalNotifier, drain
from mission_agent.signals.engine import Engine
from mission_agent.signals.gmail import GmailOutbox
from mission_agent.signals.policy import USDC, load_policy
from mission_agent.signals.scanner import Scanner
from mission_agent.signals.store import Ledger
from test_frank_fm import tx
from test_frank_gmail_delivery import Provider
from test_frank_rebuild_buys import AS_OF, MINT, UNKNOWN, config
from test_frank_v1 import POLICY


def indexed_buys(ledger, raw, mints):
    """Give the real Scanner signed synthetic direct USDC buys through a fake RPC."""
    transactions = {}
    rows = []
    checkpoint = _b58(bytes(64))
    ledger.checkpoint(WALLET, checkpoint, 1)
    for step, (offset, quote) in enumerate(((2700, 13000), (1500, 13000), (0, 5000))):
        for mint in mints:
            slot = len(rows) + 2
            signature = _b58(slot.to_bytes(64, "big"))
            raw_tx = tx()
            raw_tx.update(slot=slot, blockTime=AS_OF - 1 - offset)
            raw_tx["transaction"]["signatures"] = [signature]
            for side in ("preTokenBalances", "postTokenBalances"):
                raw_tx["meta"][side][0]["mint"] = mint
                raw_tx["meta"][side][1]["mint"] = USDC
            raw_tx["meta"]["preTokenBalances"][1]["uiTokenAmount"]["amount"] = str(quote * 10**6)
            transactions[signature] = raw_tx
            rows.append({"signature": signature, "slot": slot, "blockTime": raw_tx["blockTime"]})

    class FakeRPC:
        def signatures(self, before=None):
            assert before is None
            return [*reversed(rows), {"signature": checkpoint, "slot": 1}]

        def transaction(self, signature):
            return transactions[signature]

    scanner = Scanner(ledger, {WALLET: "frank"}, raw, rpcs={WALLET: FakeRPC()}, mode="LIVE")
    result = scanner.cycle(WALLET)
    assert result["new_signatures"] == len(rows)
    assert ledger.cursor(WALLET)["signature"] == rows[-1]["signature"]
    assert len(list(raw.glob("*.json.gz"))) == len(rows)


def prepare(tmp_path, mints, *, gate_at_enqueue=True, registry=True):
    cfg = tmp_path / "qualifications.json"
    if registry:
        config(cfg)
        parsed = json.loads(cfg.read_text())
        parsed["records"].append({**parsed["records"][0], "mint": BACKPACK_MINT})
        cfg.write_text(json.dumps(parsed))
    gate = BuyDeliveryGate(cfg, clock=lambda: AS_OF)
    ledger = Ledger(tmp_path / "db")
    indexed_buys(ledger, tmp_path / "raw", mints)
    engine = Engine(ledger, load_policy(POLICY), dry_run=False,
                    delivery_gate=gate if gate_at_enqueue else None)
    assert engine.drain() == len(mints) * 3
    return ledger, cfg, gate, engine


def test_real_scanner_policy_and_gmail_accept_only_verified_meme(tmp_path, monkeypatch):
    ledger, _, gate, engine = prepare(tmp_path, [MINT, BACKPACK_MINT, UNKNOWN])
    outbox = GmailOutbox(ledger, delivery_gate=gate)
    counts = ledger.db.execute("SELECT count(*) FROM signatures").fetchone()[0]
    assert counts == ledger.db.execute("SELECT count(*) FROM v1_seen").fetchone()[0] == 9
    assert engine.drain() == 0
    rejected = {
        row[0]: json.loads(row[1])["delivery_scope_reason"]
        for row in ledger.db.execute("SELECT mint,body FROM signals WHERE mint != ?", (MINT,))
    }
    assert rejected == {
        BACKPACK_MINT: "EXCLUDED_NON_MEME_MINT",
        UNKNOWN: "MEME_QUALIFICATION_UNPROVEN",
    }
    assert {row[0] for row in ledger.db.execute("SELECT mint FROM outbox JOIN signals USING(signal_id)")} == {MINT}
    assert ledger.db.execute("SELECT count(*) FROM email_content").fetchone()[0] == 1

    provider = Provider()
    assert outbox.drain(provider)["sent_verified"] == 1
    assert provider.actions == ["ready", "find", "send", "get"]
    message = message_from_bytes(provider.sent[0], policy=policy.default)
    assert message["Subject"] == "Frank 买入 样例 Meme"
    body = message.get_content()
    assert "买入 1 枚 · 支付 5,000 USDC" in body
    assert "https://solscan.io/tx/" in body and MINT in body
    assert all(text not in body for text in ("USD 估值", "signal_id:", "模型", "仓位", "price"))
    assert outbox.drain(provider)["sent_verified"] == 1 and len(provider.sent) == 1
    monkeypatch.setattr("mission_agent.signals.gmail.kick", lambda *a, **k: None)
    monkeypatch.setattr("mission_agent.signals.delivery.shutil.which", lambda _: "mock-notifier")
    commands = []
    mock_run = lambda command, **kwargs: commands.append(command) or SimpleNamespace(returncode=0, stdout="")
    drain(ledger, LocalNotifier(run=mock_run), delivery_gate=gate)
    assert len(commands) == 2
    assert all("Frank 买入 样例 Meme" in command for command in commands)
    assert any("买入 1 枚 · 支付 5,000 USDC" in command[4] for command in commands)
    assert all("buy_count" not in command[4] and "cumulative" not in command[4] for command in commands)


@pytest.mark.parametrize("mint,registry,expected", [
    (BACKPACK_MINT, True, "EXCLUDED_NON_MEME_MINT"),
    (UNKNOWN, True, "MEME_QUALIFICATION_UNPROVEN"),
    (MINT, False, "MEME_QUALIFICATION_UNAVAILABLE"),
])
def test_legacy_pending_identity_is_blocked_without_provider_calls(
        tmp_path, monkeypatch, mint, registry, expected):
    ledger, cfg, gate, _ = prepare(tmp_path, [mint], gate_at_enqueue=not registry, registry=registry)
    if not registry:
        assert ledger.db.execute("SELECT count(*) FROM signatures").fetchone()[0] == 3
        assert ledger.db.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0
        assert {json.loads(row[0])["delivery_scope_reason"] for row in ledger.db.execute(
            "SELECT body FROM signals")} == {expected}
        return

    # Existing transport had already frozen this unsafe row before the new gate.
    GmailOutbox(ledger).sync()
    identity = ledger.db.execute("SELECT wire_message_id,content_hash FROM gmail_delivery").fetchone()
    box = GmailOutbox(ledger, delivery_gate=gate)
    provider = Provider()
    box.drain(provider)
    row = ledger.db.execute("SELECT * FROM gmail_delivery").fetchone()
    assert row["status"] == "MEME_SCOPE_BLOCKED" and row["last_error"] == expected
    assert row["attempt_count"] == 0 and provider.actions == []
    assert (row["wire_message_id"], row["content_hash"]) == tuple(identity)
    assert row["sent_at"] is None and row["receipt"] is None
    monkeypatch.setattr("mission_agent.signals.gmail.kick", lambda *a, **k: None)
    drain(ledger, lambda _: pytest.fail("scope blocked local notifier"), delivery_gate=gate)
    assert {row[0] for row in ledger.db.execute("SELECT status FROM outbox")} == {"MEME_SCOPE_BLOCKED"}


def test_revocation_keeps_ambiguous_gmail_state_and_reads_back_without_resend(tmp_path):
    ledger, cfg, gate, _ = prepare(tmp_path, [MINT])
    outbox = GmailOutbox(ledger, delivery_gate=gate)
    provider = Provider()
    provider.crash = True
    with pytest.raises(SystemExit, match="post-acceptance crash"):
        outbox.drain(provider)
    assert ledger.db.execute("SELECT status FROM gmail_delivery").fetchone()[0] == "SENDING"
    cfg.unlink()
    assert outbox.drain()["sent_unverified"] == 1
    provider.actions.clear()
    provider.crash = False
    assert outbox.drain(provider)["sent_verified"] == 1
    assert provider.actions == ["ready", "find", "get"] and len(provider.sent) == 1


def test_gmail_checks_qualification_again_immediately_before_send(tmp_path):
    ledger, cfg, gate, _ = prepare(tmp_path, [MINT])
    outbox = GmailOutbox(ledger, delivery_gate=gate)

    class RevokingProvider(Provider):
        def find_sent(self, wire_id, sid):
            cfg.unlink()
            return super().find_sent(wire_id, sid)

    provider = RevokingProvider()
    outbox.drain(provider)
    row = ledger.db.execute("SELECT status,last_error,attempt_count FROM gmail_delivery").fetchone()
    assert tuple(row) == ("MEME_SCOPE_BLOCKED", "MEME_QUALIFICATION_UNAVAILABLE", 0)
    assert provider.actions == ["ready", "find"]


def test_manual_review_queue_does_not_restart(tmp_path):
    ledger, _, gate, _ = prepare(tmp_path, [MINT])
    outbox = GmailOutbox(ledger, delivery_gate=gate)
    outbox.sync()
    ledger.db.execute("UPDATE gmail_delivery SET status='MANUAL_REVIEW',last_error='KNOWN_HISTORICAL_STATE'")
    provider = Provider()
    outbox.drain(provider)
    assert tuple(ledger.db.execute("SELECT status,last_error FROM gmail_delivery").fetchone()) == (
        "MANUAL_REVIEW", "KNOWN_HISTORICAL_STATE")
    assert provider.actions == []


def test_scope_blocked_local_inflight_recovers_receipt_without_invoking_os(tmp_path, monkeypatch):
    ledger, cfg, gate, _ = prepare(tmp_path, [MINT])
    sid, body, content_hash = ledger.db.execute(
        "SELECT signal_id,body,content_hash FROM signals WHERE signal_type='FRANK_MULTIPLE_SIGNAL'",
    ).fetchone()
    notifier = LocalNotifier(run=lambda *a, **k: pytest.fail("notifier must only read cached receipt"),
                             receipt_root=tmp_path / "local-receipts")
    notifier.receipt_path(json.loads(body)).write_text(json.dumps(
        {"signal_id": sid, "content_hash": content_hash, "status": "COMMAND_ACCEPTED"}))
    ledger.db.execute("UPDATE outbox SET status='IN_FLIGHT',attempts=1 WHERE channel='local'")
    cfg.unlink()
    monkeypatch.setattr("mission_agent.signals.gmail.kick", lambda *a, **k: None)
    drain(ledger, notifier, delivery_gate=gate)
    states = {row[0] for row in ledger.db.execute("SELECT status FROM outbox WHERE channel='local'")}
    assert states == {"COMMAND_ACCEPTED", "SENT_UNVERIFIED"}
