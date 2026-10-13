"""C01/C08: one CA research entrance and zero implicit trading quotes.

These tests must fail against previous main: old quick/deep picker and
$30 Jupiter queries were part of general CA, contrary to the frozen plan.
Frank V1 follow-policy 30 USDC is a separate, unchanged signal authority.
"""
from pathlib import Path

import pytest

from mission_agent.mission_control import server


STATIC = Path(server.__file__).with_name("static")


def test_ca_preview_never_requests_default_thirty_dollar_quote(tmp_path):
    manager = server.ClusterJobManager(tmp_path / "control")
    class NeverQuote:
        called = 0
        def quote_usdc_to_token(self, *args, **kwargs):
            self.called += 1
            raise AssertionError("CA_DEFAULT_TRADE_QUOTE_FORBIDDEN")
    spy = NeverQuote()
    manager.jupiter = spy
    manager.jobs["job"] = {
        "job_id": "job", "mint": "So11111111111111111111111111111111111111112",
        "status": "RUNNING", "preset": "standard",
        "created_at": 1.0, "started_at": 1.0, "progress": {},
    }
    manager._set_progress("job", "BASE_READY", {
        "token_profile": {"status": "OK", "decimals": 6, "mint_authority": None},
        "market": {"status": "OK", "name": "Meme", "symbol": "MEME",
                   "main_pair": {"liquidity_usd": 100}},
    })
    assert spy.called == 0
    assert "execution_quote_30_usdc" not in manager.jobs["job"]["preview"]


def test_ca_final_report_does_not_create_a_second_default_quote(tmp_path, monkeypatch):
    manager = server.ClusterJobManager(tmp_path / "control")
    mint = "So11111111111111111111111111111111111111112"
    manager.jobs["job"] = {
        "job_id": "job", "mint": mint, "preset": "standard",
        "status": "QUEUED", "created_at": 1.0, "progress": {},
    }
    class DummyAnalyzer:
        def __init__(self, *args, **kwargs):
            pass
        def analyze(self):
            return {"mint": mint, "decimals": 6, "observed_at": 1.0,
                    "token_profile": {"status": "OK"}, "market": {"status": "OK"},
                    "coverage": {}, "assessment": {}}
    class FailQuote:
        called = 0
        def quote_usdc_to_token(self, *args, **kwargs):
            self.called += 1
            raise RuntimeError("should not be called")
    spy = FailQuote()
    manager.jupiter = spy
    monkeypatch.setattr(server, "WalletClusterAnalyzer", DummyAnalyzer)
    monkeypatch.setattr(server, "load_registry", lambda *args: {})
    monkeypatch.setattr(server, "markdown", lambda *args: "# CA Research\n")
    manager._run("job")
    assert spy.called == 0
    assert manager.jobs["job"]["status"] == "DONE"
    archived = manager.latest(mint)
    assert "execution_quote_30_usdc" not in archived
    assert (manager.report_root / mint / "latest.json").is_file()


def test_one_ca_query_is_presented_without_precision_selector():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert 'id="cluster-form"' in html
    assert 'id="cluster-mint"' in html
    assert 'id="cluster-preset"' not in html
    assert "quick:'快速" not in js
    assert "const preset = $('cluster-preset').value" not in js
    assert "preset:'standard'" in js or "preset: 'standard'" in js
    assert "每 owner 历史上限" in js
    assert "未确认" in html


def test_ca_html_and_js_do_not_render_implicit_quote_cards():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "Jupiter 可执行报价分开显示" not in html
    assert "execution_quote_30_usdc" not in js
    assert "$30 实际可成交价" not in js
    assert "$30 可成交报价" not in js
    assert "cluster-final-quote" not in js
    assert "cluster-preview-quote" not in js
    assert "cluster-preview" in html and "cluster-market" in html


def test_legacy_saved_ca_quote_is_never_marked_live(tmp_path):
    manager = server.ClusterJobManager(tmp_path / "control")
    mint = "So11111111111111111111111111111111111111112"
    d = manager.report_root / mint
    d.mkdir(parents=True)
    (d / "latest.json").write_text(__import__("json").dumps({
        "mint": mint, "execution_quote_30_usdc": {
            "status": "OK", "route_exists": True,
            "execution_price_usdc": "1",
            "price_impact_pct": "0.1",
            "observed_at": 9999999999,
        },
    }))
    read = manager.latest(mint)
    assert read["execution_quote_30_usdc"]["is_current_at_response"] is False
    assert read["execution_quote_30_usdc"]["freshness_status"] == "ARCHIVED_NOT_LIVE"
