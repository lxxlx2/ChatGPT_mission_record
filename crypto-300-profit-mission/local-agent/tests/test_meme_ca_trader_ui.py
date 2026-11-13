"""Focused trader-facing CA UI data-contract tests. No network and no live service."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from mission_agent.mission_control.server import ClusterJobManager, Handler


class IDs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "id":
                self.ids.append(value)


def test_readonly_ca_preview_is_early_and_persists_during_deep_history(tmp_path):
    manager = ClusterJobManager(tmp_path / "control")
    manager.jobs["abc"] = {
        "job_id": "abc", "mint": "X" * 44, "preset": "quick",
        "status": "RUNNING", "progress": {},
    }
    manager._set_progress("abc", "BASE_READY", {
        "token_profile": {
            "status": "OK", "token_program": "SPL Token",
            "mint_authority": None, "freeze_authority": "risk",
            "active_extension_risks": [], "unresolved_sensitive_extensions": [],
        },
        "market": {
            "status": "OK", "name": "Example", "symbol": "EX",
            "price_usd": "0.0012", "market_cap_usd": 123400,
            "main_pair": {"liquidity_usd": 50000, "volume": {"h24": 18000}},
        },
    })
    first = manager.get("abc")
    assert first["preview"]["price_usd"] == "0.0012"
    assert first["preview"]["freeze_authority"] == "risk"
    assert first["preview"]["market_status"] == "OK"
    assert "frank" not in first["preview"]
    manager._set_progress("abc", "HOLDERS_READY", {
        "top_accounts_resolved": 20, "raw_top10_resolved_pct": "67.42",
    })
    manager._set_progress("abc", "OWNER_SCAN", {"scanned": 2, "target": 6})
    later = manager.get("abc")
    assert later["preview"]["market_cap_usd"] == first["preview"]["market_cap_usd"]
    assert later["preview"]["raw_top10_resolved_pct"] == "67.42"
    assert later["preview"]["top_accounts_resolved"] == 20
    assert later["progress"]["scanned"] == 2
    manager.executor.shutdown(wait=True)


def test_ca_ui_has_independent_fast_view_and_disclosed_technical_evidence():
    root = Handler.static_root
    html = (root / "index.html").read_text()
    js = (root / "app.js").read_text()
    parser = IDs()
    parser.feed(html)
    needed = [
        "cluster-preview", "cluster-summary", "cluster-conclusion",
        "cluster-market", "cluster-metrics", "cluster-holders",
        "cluster-token-profile", "cluster-coverage", "cluster-evidence",
    ]
    assert all(parser.ids.count(node) == 1 for node in needed)
    assert html.index('id="cluster-conclusion"') < html.index('id="cluster-holders"')
    assert html.index('id="cluster-market"') < html.index('id="cluster-holders"')
    assert html.index('id="cluster-holders"') < html.index('id="cluster-coverage"')
    assert 'class="panel cluster-detail-fold"' in html
    assert 'id="cluster-frank"' not in html
    assert "$('cluster-frank')" not in js
    assert "renderClusterPreview(job)" in js
    assert "trade_confirmed" not in js.split("function renderClusterPreview(job)")[1].split("function clusterErrorMessage")[0]
    assert 'data-view="signals"' in html and 'data-view="cluster"' in html



def test_ca_preview_never_requests_preset_jupiter_quote(tmp_path):
    manager = ClusterJobManager(tmp_path / "control")
    mint = "So11111111111111111111111111111111111111112"
    manager.jobs["early"] = {
        "job_id": "early", "mint": mint, "preset": "quick",
        "status": "RUNNING", "progress": {},
    }
    def no_automatic_quote(*args, **kwargs):
        raise AssertionError("NO_USER_DEFINED_NOTIONAL_NO_JUPITER_EXECUTION_QUOTE")
    manager.jupiter.quote_usdc_to_token = no_automatic_quote
    manager._set_progress("early", "BASE_READY", {
        "token_profile": {"status": "OK", "decimals": 6, "mint_authority": None,
                          "freeze_authority": None},
        "market": {"status": "OK", "name": "Example", "symbol": "EX",
                   "main_pair": {"liquidity_usd": 50000}},
    })
    preview = manager.get("early")["preview"]
    assert preview["price_usd"] is None or "price_usd" in preview
    assert "execution_quote_30_usdc" not in preview
    manager._set_progress("early", "HOLDERS_READY", {
        "top_accounts_resolved": 20, "raw_top10_resolved_pct": "42",
    })
    assert manager.get("early")["preview"]["top_accounts_resolved"] == 20
    manager.executor.shutdown(wait=True)


def test_ca_ui_does_not_show_fixed_execution_quote():
    root = Handler.static_root
    js = (root / "app.js").read_text()
    assert "fact('$30 可成交报价'" not in js
    assert "fact('$30 实际可成交价'" not in js
    assert "execution_quote_30_usdc" not in js
    assert "renderClusterPreview(job)" in js
    assert "查询时参考价" in js


def test_ca_legacy_fixed_quote_is_hidden_without_modifying_archive(tmp_path):
    import json
    from mission_agent.meme.cluster import markdown
    mint = "So11111111111111111111111111111111111111112"
    manager = ClusterJobManager(tmp_path / "control")
    dest = manager.report_root / mint
    dest.mkdir(parents=True)
    saved = {"mint": mint, "execution_quote_30_usdc": {
        "status": "OK", "source": "JUPITER_OFFICIAL",
        "execution_price_usdc": "0.001", "price_impact_pct": "0.2",
    }}
    (dest / "latest.json").write_text(json.dumps(saved))
    report = manager.latest(mint)
    assert "execution_quote_30_usdc" not in report
    assert json.loads((dest / "latest.json").read_text()) == saved
    md = markdown({**saved, "market": {"status": "UNAVAILABLE"}})
    assert "Jupiter $30 quote" not in md
    assert "Executable trade quote: not calculated" in md

    manager.jobs["stale"] = {
        "job_id": "stale", "mint": mint, "preset": "quick",
        "status": "RUNNING", "progress": {},
        "preview": {"execution_quote_30_usdc": saved["execution_quote_30_usdc"]},
    }
    assert "execution_quote_30_usdc" not in manager.get("stale")["preview"]
    manager.executor.shutdown(wait=True)


def test_real_ca_acceptance_script_has_no_forced_quote():
    import subprocess
    script = Handler.static_root.parents[2] / "scripts" / "accept_meme_ca_v3.sh"
    assert script.exists()
    body = script.read_text()
    assert "require_frank" not in body
    assert "quote_preview_seconds" not in body
    assert "full_report_seconds" in body
    assert "REAL_CA_SCHEMA_AND_SEMANTICS: PASS" in body
    assert "mission-control.sqlite" in body
    assert "No Mission Control loop" in body
    subprocess.run(["bash", "-n", str(script)], check=True)
