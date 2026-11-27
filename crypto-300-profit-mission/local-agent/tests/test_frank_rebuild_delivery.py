from email import message_from_bytes, policy
import hashlib
import json
from types import SimpleNamespace

import pytest

from mission_agent.frank.rpc import WALLET
from mission_agent.meme.holder_ranks import _b58
from mission_agent.signals.buy_admission import BACKPACK_MINT, BuyDeliveryGate, admit_buy, qualification
from mission_agent.mission_control.frank_buys import read_buys
from mission_agent.signals.category_evidence import COINGECKO_SOLANA
from mission_agent.signals.delivery import LocalNotifier, drain
from mission_agent.signals.engine import Engine
from mission_agent.signals.gmail import GmailOutbox
from mission_agent.signals.policy import BUY_DELIVERY_MAX_AGE_SECONDS, USDC, load_policy
from mission_agent.signals.scanner import Scanner
from mission_agent.signals.store import Ledger
from test_frank_fm import tx
from test_frank_gmail_delivery import Provider
from test_frank_rebuild_buys import AS_OF, MINT, UNKNOWN, config
from test_frank_v1 import POLICY


def indexed_buys(ledger, raw, mints, *,
                 schedule=((2700, 13000), (1500, 13000), (0, 5000))):
    """Give the real Scanner signed synthetic direct USDC buys through a fake RPC."""
    transactions = {}
    rows = []
    checkpoint = _b58(bytes(64))
    ledger.checkpoint(WALLET, checkpoint, 1)
    for offset, quote in schedule:
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


def prepare(tmp_path, mints, *, gate_at_enqueue=True, registry=True, clock=lambda: AS_OF):
    cfg = tmp_path / "qualifications.json"
    if registry:
        config(cfg)
        parsed = json.loads(cfg.read_text())
        parsed["records"].append({**parsed["records"][0], "mint": BACKPACK_MINT})
        cfg.write_text(json.dumps(parsed))
    gate = BuyDeliveryGate(cfg, clock=clock)
    ledger = Ledger(tmp_path / "db")
    indexed_buys(ledger, tmp_path / "raw", mints)
    engine = Engine(ledger, load_policy(POLICY), dry_run=False,
                    delivery_gate=gate if gate_at_enqueue else None)
    assert engine.drain() == len(mints) * 3
    return ledger, cfg, gate, engine


def test_routed_receipt_can_show_quantity_without_admitting_notification(tmp_path):
    ledger, cfg, gate, _ = prepare(tmp_path, [MINT])
    signal = json.loads(ledger.db.execute("SELECT body FROM signals WHERE signal_type='FRANK_MULTIPLE_SIGNAL'").fetchone()[0])
    row = ledger.db.execute("SELECT * FROM signatures WHERE signature=?", (signal["latest_buy_signature"],)).fetchone()
    event = json.loads(row["body"])
    event["trade"].update(
        route_intermediate_evidence_status="UNVERIFIED",
        route_amount_semantics="GROSS_QUOTE_OUT_NOT_EXACT_FINAL_TARGET_COST",
        route_intermediate_assets=[{"mint": UNKNOWN}],
    )
    binding = {key: row[key] for key in ("wallet", "signature", "slot", "block_time", "raw_hash")}
    assets = qualification(cfg, AS_OF)
    assert admit_buy(event, assets, mint=MINT, **binding) is None
    view = admit_buy(event, assets, mint=MINT, allow_unpriced=True, **binding)
    assert (view["quantity"], view["paid"], view["currency"]) == ("1", None, None)
    ledger.db.execute("UPDATE signatures SET body=? WHERE signature=?", (json.dumps(event), row["signature"]))
    assert gate.block_reason(ledger.db, signal) == "TRIGGER_IS_NOT_PROVEN_BUY"
    event["trade"]["referenced_pre_raw"] = event["trade"]["referenced_post_raw"]
    assert admit_buy(event, assets, mint=MINT, allow_unpriced=True, **binding) is None


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


def test_late_qualification_updates_history_without_releasing_legacy_pending_mail(tmp_path, monkeypatch):
    from mission_agent.mission_control.frank_buys import read_buys

    ledger, cfg, gate, _ = prepare(tmp_path, [MINT], gate_at_enqueue=False, registry=False)
    GmailOutbox(ledger).sync()  # legacy producer knew nothing about qualification
    cfg_doc = {"version": 1, "records": [
        {"chain": "solana", "mint": MINT, "name": "Fixture Meme", "status": "VERIFIED_MEME",
         "source": "synthetic source", "observed_at": AS_OF},
    ]}
    cfg.write_text(json.dumps(cfg_doc))
    history = read_buys(tmp_path / "db", cfg, as_of=AS_OF)["rows"]
    assert len(history) == 3 and all(row["mint"] == MINT for row in history)

    provider = Provider()
    box = GmailOutbox(ledger, delivery_gate=gate)
    box.drain(provider)
    row = ledger.db.execute("SELECT status,last_error,attempt_count FROM gmail_delivery").fetchone()
    assert tuple(row) == ("MEME_SCOPE_BLOCKED", "LEGACY_QUALIFICATION_OBSERVED_LATE", 0)
    assert provider.actions == []
    monkeypatch.setattr("mission_agent.signals.gmail.kick", lambda *a, **k: None)
    notified = []
    drain(ledger, notified.append, delivery_gate=gate)
    assert notified == []
    assert {row[0] for row in ledger.db.execute("SELECT status FROM outbox")} == {"MEME_SCOPE_BLOCKED"}

    reopened = Ledger(tmp_path / "db")
    GmailOutbox(reopened, delivery_gate=gate).drain(provider)
    assert provider.actions == []


def test_enqueue_bound_qualification_may_follow_chain_time_without_being_a_replay(tmp_path):
    cfg = tmp_path / "qualifications.json"
    config(cfg)
    doc = json.loads(cfg.read_text())
    doc["records"][0]["observed_at"] = AS_OF
    cfg.write_text(json.dumps(doc))
    ledger = Ledger(tmp_path / "db")
    indexed_buys(ledger, tmp_path / "raw", [MINT])
    gate = BuyDeliveryGate(cfg, clock=lambda: AS_OF)
    eng = Engine(ledger, load_policy(POLICY), dry_run=False, delivery_gate=gate)
    assert eng.drain() == 3
    body, = ledger.db.execute(
        "SELECT body FROM signals WHERE signal_type='FRANK_MULTIPLE_SIGNAL'"
    ).fetchone()
    signal = json.loads(body)
    assert signal["triggered_at"] < AS_OF
    assert signal["verified_buy"]["mint"] == MINT
    provider = Provider()
    assert GmailOutbox(ledger, delivery_gate=gate).drain(provider)["sent_verified"] == 1
    assert len(provider.sent) == 1

def test_restart_catches_up_expired_buys_without_enqueuing(tmp_path):
    ledger, cfg, gate, engine = prepare(tmp_path, [MINT], clock=lambda: AS_OF + 10800)
    rows = [json.loads(row[0]) for row in ledger.db.execute("SELECT body FROM signals")]
    assert len(rows) == 2
    assert {row["delivery_scope_reason"] for row in rows} == {"BUY_NOTIFICATION_EXPIRED"}
    assert ledger.db.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0
    assert ledger.db.execute("SELECT count(*) FROM email_content").fetchone()[0] == 0
    assert len(read_buys(tmp_path / "db", cfg, as_of=AS_OF + 10800)["rows"]) == 3
    assert engine.drain() == 0
    assert GmailOutbox(ledger, delivery_gate=gate).drain()["sent_verified"] == 0


def test_notification_age_uses_original_buy_and_frozen_policy_window(tmp_path):
    clock = AS_OF
    ledger, _, gate, _ = prepare(tmp_path, [MINT], clock=lambda: clock)
    frozen = load_policy(POLICY)["mapping"]
    ages = {stage: frozen[stage][key] for stage, key in (
        ("FRANK_ACCUMULATION_SIGNAL", "window_seconds"),
        ("FRANK_MULTIPLE_SIGNAL", "stale_after_seconds"),
    )}
    assert BUY_DELIVERY_MAX_AGE_SECONDS == ages
    for row in ledger.db.execute("SELECT body FROM signals"):
        signal = json.loads(row[0])
        buy_at = signal["verified_buy"]["at"]
        clock = buy_at + ages[signal["signal_type"]]
        assert gate.block_reason(ledger.db, signal) is None
        clock += 1
        assert gate.block_reason(ledger.db, {**signal, "triggered_at": clock}) == "BUY_NOTIFICATION_EXPIRED"
        assert gate.block_reason(ledger.db, {**signal, "triggered_at": clock + 1}) == "BUY_NOTIFICATION_TIME_UNVERIFIED"
        assert gate.block_reason(ledger.db, {**signal, "triggered_at": buy_at - 1}) == "BUY_NOTIFICATION_TIME_UNVERIFIED"


def test_queued_buy_can_expire_during_gmail_readback_before_first_send(tmp_path, monkeypatch):
    clock = AS_OF
    ledger, _, gate, _ = prepare(tmp_path, [MINT], clock=lambda: clock)
    outbox = GmailOutbox(ledger, delivery_gate=gate)

    class DelayedProvider(Provider):
        def find_sent(self, wire_id, sid):
            nonlocal clock
            clock = AS_OF + 10800
            return super().find_sent(wire_id, sid)

    provider = DelayedProvider()
    outbox.drain(provider)
    assert provider.actions == ["ready", "find"]
    assert tuple(ledger.db.execute("SELECT status,last_error,attempt_count FROM gmail_delivery").fetchone()) == (
        "MEME_SCOPE_BLOCKED", "BUY_NOTIFICATION_EXPIRED", 0)
    monkeypatch.setattr("mission_agent.signals.gmail.kick", lambda *a, **k: None)
    drain(ledger, lambda _: pytest.fail("expired notification reached the OS"), delivery_gate=gate)
    assert {tuple(r) for r in ledger.db.execute("SELECT status,last_error,attempts FROM outbox")} == {
        ("MEME_SCOPE_BLOCKED", "BUY_NOTIFICATION_EXPIRED", 0)}


def test_expired_inflight_gmail_reads_receipt_without_resending(tmp_path):
    clock = AS_OF
    ledger, _, gate, _ = prepare(tmp_path, [MINT], clock=lambda: clock)
    provider = Provider()
    provider.crash = True
    with pytest.raises(SystemExit, match="post-acceptance crash"):
        GmailOutbox(ledger, delivery_gate=gate).drain(provider)
    ledger.db.close()

    clock = AS_OF + 10800
    provider.crash = False
    provider.actions.clear()
    reopened = Ledger(tmp_path / "db")
    assert GmailOutbox(reopened, delivery_gate=gate).drain(provider)["sent_verified"] == 1
    assert provider.actions == ["ready", "find", "get"] and len(provider.sent) == 1


@pytest.mark.parametrize("reason,offset", [
    ("MEME_QUALIFICATION_UNPROVEN", 120),
    ("BUY_NOTIFICATION_EXPIRED", 10801),
])
def test_later_buy_can_qualify_once_after_a_stage_that_never_queued(tmp_path, reason, offset):
    cfg = tmp_path / "qualifications.json"
    config(cfg)
    if reason == "MEME_QUALIFICATION_UNPROVEN":
        cfg.write_text('{"version": 1, "records": []}')
    clock = AS_OF + (10800 if reason == "BUY_NOTIFICATION_EXPIRED" else 0)
    gate = BuyDeliveryGate(cfg, clock=lambda: clock)
    ledger = Ledger(tmp_path / "db")
    indexed_buys(ledger, tmp_path / "raw", [MINT],
                 schedule=((2700, 13000), (1500, 13000), (0, 5000),
                           (-offset - 1, 13000), (-offset - 121, 13000)))
    policy = load_policy(POLICY)
    engine = Engine(ledger, policy, dry_run=False, delivery_gate=gate)
    events = ledger.db.execute("SELECT * FROM signatures ORDER BY block_time").fetchall()
    for event in events[:3]:
        engine.process(event)
    original = {r["signal_id"]: dict(r) for r in ledger.db.execute("SELECT * FROM signals")}
    assert len(original) == 2
    assert {json.loads(r["body"])["delivery_scope_reason"] for r in ledger.db.execute(
        "SELECT body FROM signals")} == {reason}
    assert ledger.db.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0

    config(cfg)
    engine.tick(clock)
    assert ledger.db.execute("SELECT count(*) FROM outbox").fetchone()[0] == 0
    for event in events[3:]:
        clock = event["block_time"]
        engine.process(event)
    delivered_stages = ledger.db.execute(
        "SELECT s.signal_type,s.body FROM signals s JOIN outbox o USING(signal_id) WHERE o.channel='gmail'"
    ).fetchall()
    assert len(delivered_stages) == 1
    stage, body = delivered_stages[0]
    signal = json.loads(body)
    assert stage == "FRANK_MULTIPLE_SIGNAL"
    assert signal["verified_buy"]["signature"] == events[3]["signature"]
    assert signal["signal_id"] in original
    archived = [json.loads(r[0])["signal"] for r in ledger.db.execute(
        "SELECT body FROM v1_evaluations WHERE json_extract(body, '$.kind')='BUY_DELIVERY_BLOCKED'")]
    assert original[signal["signal_id"]] in archived
    assert len(archived) == len({r["signal_id"] for r in archived}) == 2
    assert ledger.db.execute("SELECT count(*) FROM signals").fetchone()[0] == 2
    provider = Provider()
    assert GmailOutbox(ledger, delivery_gate=gate).drain(provider)["sent_verified"] == 1
    ledger.db.close()
    reopened = Ledger(tmp_path / "db")
    assert Engine(reopened, policy, dry_run=False, delivery_gate=gate).drain() == 0
    GmailOutbox(reopened, delivery_gate=gate).drain(provider)
    assert len(provider.sent) == 1


def _write_category_fixture(path, mints, *, at=AS_OF, categories=None):
    records = []
    for mint in mints:
        body = json.dumps({
            "name": "自动分类样例 Meme", "preview_listing": False, "platforms": {"solana": mint},
            "detail_platforms": {"solana": {"contract_address": mint}},
            "categories": (categories or {}).get(mint, ["Meme"]),
        })
        records.append({"mint": mint, "observed_at": at, "url": COINGECKO_SOLANA + mint,
                        "body": body, "sha256": hashlib.sha256(body.encode()).hexdigest()})
    path.write_text(json.dumps({"version": 1, "records": records}))


def test_category_only_is_explicit_and_uses_shared_new_buy_delivery_contract(tmp_path, monkeypatch):
    raw, db, sidecar = (tmp_path / name for name in ("raw", "db", "receipts"))
    cfg = tmp_path / "no-manual-registry"
    _write_category_fixture(sidecar, [MINT, BACKPACK_MINT, UNKNOWN],
                            categories={UNKNOWN: ["Technology", "Solana Ecosystem"]})
    gate = BuyDeliveryGate(cfg, clock=lambda: AS_OF, category_evidence_path=sidecar)
    ledger = Ledger(db)
    try:
        indexed_buys(ledger, raw, [MINT, BACKPACK_MINT, UNKNOWN])
        engine = Engine(ledger, load_policy(POLICY), dry_run=False, delivery_gate=gate)
        assert engine.drain() == 9
        recent = read_buys(db, cfg, as_of=AS_OF, category_evidence_path=sidecar)
        assert [row["mint"] for row in recent["rows"]] == [MINT] * 3
        found = {r[0]: json.loads(r[1]) for r in ledger.db.execute("SELECT mint,body FROM signals")}
        assert found[BACKPACK_MINT]["delivery_scope_reason"] == "EXCLUDED_NON_MEME_MINT"
        assert found[UNKNOWN]["delivery_scope_reason"] == "MEME_QUALIFICATION_UNPROVEN"
        admitted = found[MINT]
        assert gate.block_reason(ledger.db, admitted) is None
        assert BuyDeliveryGate(cfg, clock=lambda: AS_OF).block_reason(ledger.db, admitted) == "MEME_QUALIFICATION_UNAVAILABLE"
        outbox = GmailOutbox(ledger, delivery_gate=gate)
        provider = Provider()
        assert outbox.drain(provider)["sent_verified"] == 1
        assert outbox.drain(provider)["sent_verified"] == 1 and len(provider.sent) == 1
        assert "自动分类样例 Meme" in message_from_bytes(provider.sent[0], policy=policy.default)["Subject"]
        monkeypatch.setattr("mission_agent.signals.gmail.kick", lambda *a, **k: None)
        local = []
        drain(ledger, lambda s: local.append(s) or {"mock": True}, delivery_gate=gate)
        assert local and all(row["mint"] == MINT for row in local)
        assert len(local) == len({row["signal_id"] for row in local})
    finally:
        ledger.db.close()


def test_late_category_capture_cannot_send_legacy_pending_and_manual_pending_wins(tmp_path):
    ledger, cfg, _, _ = prepare(tmp_path, [MINT], gate_at_enqueue=False, registry=False)
    try:
        sidecar = tmp_path / "receipts"
        _write_category_fixture(sidecar, [MINT])
        gate = BuyDeliveryGate(cfg, clock=lambda: AS_OF, category_evidence_path=sidecar)
        signal = json.loads(ledger.db.execute(
            "SELECT body FROM signals WHERE signal_type='FRANK_MULTIPLE_SIGNAL'").fetchone()[0])
        assert gate.block_reason(ledger.db, signal) == "LEGACY_QUALIFICATION_OBSERVED_LATE"
        assert len(read_buys(tmp_path/"db", cfg, as_of=AS_OF, category_evidence_path=sidecar)["rows"]) == 3
        # Deliberate local PENDING supersedes a CoinGecko positive.
        config(cfg)
        manual = json.loads(cfg.read_text())
        manual["records"][0]["status"] = "PENDING"
        cfg.write_text(json.dumps(manual))
        assert gate.block_reason(ledger.db, signal) == "MEME_QUALIFICATION_UNPROVEN"
        assert read_buys(tmp_path/"db", cfg, as_of=AS_OF, category_evidence_path=sidecar)["rows"] == []
        cfg.write_text("{}")
        assert gate.block_reason(ledger.db, signal) == "MEME_QUALIFICATION_UNAVAILABLE"
    finally:
        ledger.db.close()
