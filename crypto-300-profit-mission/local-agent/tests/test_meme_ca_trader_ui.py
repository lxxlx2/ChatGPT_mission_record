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
