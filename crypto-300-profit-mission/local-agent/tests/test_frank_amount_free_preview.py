"""P3 offline UI and FAKE-ONLY notification isolation tests (no real providers)."""
import json

import pytest

from mission_agent.mission_control.intelligence_preview import (
    _solscan, analyze_rows, fake_intelligence_updates, main, render_html,
)

MINT = "4K1m7gAMDKzrxQn68yuZAd767w57Fw7Ykw69dG3umeta"
SIG = "5yJ2AbcfMNPqwxyz123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghi"


def candidate(**kw):
    x = dict(
        mint=MINT, pattern="MULTIPLE", source_signal_id="historical-v1-id",
        source_signal_at=1000, latest_at=1200, latest_buy_at=1000,
        latest_signature=SIG, latest_side="SELL", position_state="CLOSED",
        buy_count=2, sell_count=1, latest_buy_price_usdc="0.01",
        latest_buy_price_status="USDC_DIRECT",
    )
    x.update(kw)
    return x


def mark(**kw):
    x = dict(mint=MINT, chain="solana", source="fixture-dated-pool",
             observed_at=1200, price_usdc_per_token="0.012")
    x.update(kw)
    return x


def rows(items=None, markets=None, now=1300):
    return analyze_rows(items if items is not None else [candidate()],
                        as_of=now, max_market_age_seconds=300,
                        market_observations=markets)


def test_usable_card_contains_provenance_price_timestamp_and_no_execution():
    items = rows(markets={MINT: mark()})
    view = render_html(items, as_of=1300, simulated_updates=[])
    assert "20.0000%" in view
    assert MINT in view and SIG in view
    assert "NOT executable return" in view
    assert "NOT ASSESSED, user amount not supplied" in view
    assert "Copy CA" in view and "Solscan" in view
    assert "NO_SEND" not in view or "not sent" in view


def test_missing_market_is_explicit_and_does_not_guess_a_price():
    item = rows()[0]
    assert item["price"]["status"] == "PRICE_UNAVAILABLE"
    html = render_html([item], as_of=1300, simulated_updates=[])
    assert "PRICE_UNAVAILABLE" in html
    assert "MARKET_REFERENCE_MISSING" in html
    assert "20.0000%" not in html


def test_future_action_is_neither_displayed_as_signed_sell_nor_previewed():
    item = rows([candidate(latest_at=1400)])[0]
    assert item["latest_side"] == "UNVERIFIED"
    assert fake_intelligence_updates([item], as_of=1300, max_event_age_seconds=600) == []


def test_only_recent_verified_sell_produces_fake_intelligence_update():
    items = rows([candidate(), candidate(mint="new-mint", latest_side="BUY", latest_at=1250)])
    fake = fake_intelligence_updates(items, as_of=1300, max_event_age_seconds=600)
    assert len(fake) == 1
    assert fake[0]["kind"] == "INTELLIGENCE_UPDATE"
    assert fake[0]["event"] == "FRANK_VERIFIED_SELL"
    assert fake[0]["mode"] == "FAKE_PREVIEW_ONLY_NO_SEND"
    assert fake[0]["channels"] == [] and fake[0]["send_allowed"] is False
    assert "RAW_SIGNAL" not in json.dumps(fake)


def test_source_key_dedupe_in_batch_and_against_previously_seen():
    item = rows()[0]
    out = fake_intelligence_updates([item, item], as_of=1300, max_event_age_seconds=600)
    assert len(out) == 1
    old = {out[0]["key"]}
    assert fake_intelligence_updates([item], as_of=1300, max_event_age_seconds=600,
                                     previously_seen=old) == []
    assert out[0]["key"].startswith("INTELLIGENCE_UPDATE:")


def test_old_sell_stays_in_page_but_never_fake_notifies():
    item = rows()[0]
    assert fake_intelligence_updates([item], as_of=1300,
                                     max_event_age_seconds=50) == []
    assert "FRANK_LATEST_ACTION_SELL" in item["facts"]


def test_buy_accumulation_never_rebroadcasts_old_v1_alert():
    item = rows([candidate(pattern="ACCUMULATION", latest_side="BUY")])[0]
    assert "V1_SOURCE_ACCUMULATION" in item["facts"]
    assert fake_intelligence_updates([item], as_of=1300,
                                     max_event_age_seconds=600) == []


def test_unverifiable_signature_never_becomes_web_link_and_html_is_escaped():
    item = rows([candidate(mint='<img src=x onerror="alert(1)">',
                           latest_signature='<script>alert(1)</script>')])[0]
    view = render_html([item], as_of=1300, simulated_updates=[])
    assert "<img" not in view and "<script>alert" not in view
    assert "&lt;img" in view and "onerror" in view
    assert _solscan("tx", "<script>alert(1)</script>") == ""


def test_fake_notice_requires_positive_explicit_age_budget():
    with pytest.raises(ValueError, match="EVENT_FRESHNESS_LIMIT_REQUIRED"):
        fake_intelligence_updates(rows(), as_of=1300, max_event_age_seconds=0)


def test_local_json_cli_creates_html_and_fake_only_json(tmp_path):
    input_file = tmp_path / "candidates.json"
    input_file.write_text(json.dumps([candidate()]), encoding="utf-8")
    out_html = tmp_path / "frank.html"
    out_fake = tmp_path / "fake.json"
    args = ["--candidate-json", str(input_file),
            "--output", str(out_html), "--fake-out", str(out_fake),
            "--max-market-age-seconds", "300",
            "--max-event-age-seconds", "600", "--as-of", "1300"]
    assert main(args) == 0
    assert "LOCAL, READ-ONLY SNAPSHOT" in out_html.read_text()
    data = json.loads(out_fake.read_text())
    assert data["mode"] == "FAKE_PREVIEW_ONLY_NO_SEND"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["send_allowed"] is False


def test_invalid_batch_fails_instead_of_representing_empty_activity():
    with pytest.raises(ValueError, match="INVALID_CANDIDATE_BATCH"):
        analyze_rows([candidate()] * 5001, as_of=1300,
                     max_market_age_seconds=300)
