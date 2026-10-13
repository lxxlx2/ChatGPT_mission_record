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


def test_ca_early_preview_never_requests_implicit_trade_quote(tmp_path):
    manager = ClusterJobManager(tmp_path / "control")
    manager.jobs["early"] = {
        "job_id": "early", "mint": "So11111111111111111111111111111111111111112",
        "preset": "standard", "status": "RUNNING", "progress": {},
    }
    class FailQuote:
        def quote_usdc_to_token(self, *args, **kwargs):
            raise AssertionError("NO_IMPLICIT_JUPITER_IN_CA")
    manager.jupiter = FailQuote()
    manager._set_progress("early", "BASE_READY", {
        "token_profile": {"status": "OK", "decimals": 6},
        "market": {"status": "OK", "name": "Example", "symbol": "EX",
                   "price_usd": "0.0012",
                   "main_pair": {"liquidity_usd": 50000}},
    })
    first = manager.get("early")
    assert first["progress"]["stage"] == "BASE_READY"
    assert first["preview"]["price_usd"] == "0.0012"
    assert "execution_quote_30_usdc" not in first["preview"]
    manager._set_progress("early", "HOLDERS_READY", {
        "top_accounts_resolved": 20, "raw_top10_resolved_pct": "42",
    })
    assert manager.get("early")["preview"]["top_accounts_resolved"] == 20
    manager.executor.shutdown(wait=True)


def test_ca_preview_missing_decimals_does_not_trigger_default_quote(tmp_path):
    manager = ClusterJobManager(tmp_path / "control")
    manager.jobs["unknown"] = {
        "job_id": "unknown", "mint": "X" * 44, "preset": "standard",
        "status": "RUNNING", "progress": {},
    }
    class FailQuote:
        def quote_usdc_to_token(self, *args, **kwargs):
            raise AssertionError("CA_QUOTE_NOT_REQUESTED")
    manager.jupiter = FailQuote()
    manager._set_progress("unknown", "BASE_READY", {
        "token_profile": {"status": "UNAVAILABLE", "decimals": None},
        "market": {"status": "UNAVAILABLE"},
    })
    preview = manager.get("unknown")["preview"]
    assert preview["token_status"] == "UNAVAILABLE"
    assert "execution_quote_30_usdc" not in preview
    manager.executor.shutdown(wait=True)


def test_ca_frontend_null_is_unknown_and_never_auto_quotes():
    import subprocess
    root = Handler.static_root
    js = (root / "app.js").read_text()
    assert "execution_quote_30_usdc" not in js
    assert "caQuoteCurrent(" not in js
    assert "cluster-final-quote" not in js
    assert "quoteAge<=30" not in js
    assert "fact('$30 可成交报价'" not in js
    script = r"""
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync(process.argv[1],'utf8');
const p1=js.slice(js.indexOf('const n = '), js.indexOf('const short ='));
const p2=js.slice(js.indexOf('function usd('), js.indexOf('function authorityText('));
if (!p1 || !p2) throw Error('MISSING_HELPERS');
const result=vm.runInNewContext(
  p1 + '\\n' + p2 + '\\n' +
  '({missing:[n(null),money(null),smallPrice(null),usd(null),pctText(null)],' +
  'zero:[n(0),money(0),usd(0),pctText(0)]})'
);
if(result.missing.some(v=>v!=='暂无')) throw Error('MISSING_MARKED_AS_ZERO');
if(result.zero[2]!=='$0' || result.zero[3]!=='0%') throw Error('REAL_ZERO_HIDDEN');
"""
    subprocess.run(["node", "-e", script, str(root / "app.js")], check=True)


def test_real_ca_acceptance_script_is_readonly_and_does_not_require_frank_presence():
    import subprocess
    script=Handler.static_root.parents[2] / "scripts" / "accept_meme_ca_v3.sh"
    assert script.exists()
    body=script.read_text()
    assert "require_frank" not in body
    assert "first_quote_preview_seconds" not in body
    assert "IMPLICIT_QUOTE_IN_PREVIEW" in body
    assert "IMPLICIT_QUOTE_IN_REPORT" in body
    assert "full_report_seconds" in body
    assert "REAL_CA_SCHEMA_AND_SEMANTICS: PASS" in body
    assert "mission-control.sqlite" in body
    assert "No Mission Control loop" in body
    subprocess.run(["bash","-n",str(script)],check=True)


def test_ca_partial_preview_survives_depth_failure_without_implicit_quote():
    import subprocess
    js=Handler.static_root / "app.js"
    script=r"""
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync(process.argv[1],'utf8');
const fn=js.slice(js.indexOf('function renderClusterPreview(job)'),js.indexOf('function clusterErrorMessage('));
const panel={hidden:true,innerHTML:''};
const ctx={
  $:()=>panel,
  esc:x=>String(x ?? ''),
  usd:x=>x==null?'暂无':'$'+x,
  pctText:x=>String(x)+'%',
  fact:(name,value)=>name+':'+value+';',
};
vm.runInNewContext(fn+'\\nrenderClusterPreview(job);',
  {...ctx,job:{
    status:'ERROR',
    preview:{
      token_status:'OK',mint_authority:null,freeze_authority:null,
      market_status:'OK',name:'Sample',symbol:'S',
      price_usd:'0.01',market_cap_usd:null,liquidity_usd:null,
    }
  }}
);
if(panel.hidden) throw Error('PREVIEW_DISCARDED_ON_FAILURE');
if(!panel.innerHTML.includes('深度分析未完成')) throw Error('MISSING_INCOMPLETE_WARNING');
if(panel.innerHTML.includes('$30')) throw Error('IMPLICIT_QUOTE_REAPPEARED');
if(!panel.innerHTML.includes('市值:暂无')) throw Error('MISSING_METRIC_ZEROED');
"""
    subprocess.run(["node","-e",script,str(js)],check=True)


def test_ca_legacy_quote_archive_is_permanently_not_live(tmp_path, monkeypatch):
    import json
    import mission_agent.mission_control.server as server
    from mission_agent.meme.cluster import markdown
    sample = {"status": "OK", "route_exists": True,
              "observed_at": 1800000000.0,
              "execution_price_usdc": "0.001",
              "price_impact_pct": "0.2"}
    archived = server._annotate_ca_quote(sample, archived=True)
    assert archived["quote_record_type"] == "HISTORICAL_SNAPSHOT"
    assert archived["valid_until"] == 1800000030.0
    assert archived["freshness_status"] == "ARCHIVED_NOT_LIVE"
    assert archived["is_current_at_response"] is False
    mint = "So11111111111111111111111111111111111111112"
    manager = ClusterJobManager(tmp_path / "control")
    dest = manager.report_root / mint
    dest.mkdir(parents=True)
    saved = {"mint":mint,"execution_quote_30_usdc":archived}
    (dest/"latest.json").write_text(json.dumps(saved))
    monkeypatch.setattr(server.time,"time",lambda:1800000020.0)
    now = manager.latest(mint)
    assert now["execution_quote_30_usdc"]["is_current_at_response"] is False
    assert now["execution_quote_30_usdc"]["freshness_status"] == "ARCHIVED_NOT_LIVE"
    monkeypatch.setattr(server.time,"time",lambda:1800000031.0)
    later = manager.latest(mint)
    assert later["execution_quote_30_usdc"]["freshness_status"] == "ARCHIVED_NOT_LIVE"
    assert json.loads((dest/"latest.json").read_text()) == saved
    manager.executor.shutdown(wait=True)
    report = {"mint":mint,"observed_at":1800000005.0,
              "execution_quote_30_usdc":archived}
    rendered = markdown(report)
    assert "Legacy archived Jupiter $30 quote (not current)" in rendered
    assert "Market snapshot (historical; not live)" in rendered
    assert "observed_at=" in rendered
    fresh = markdown({"mint":mint,"observed_at":1800000005.0})
    assert "No automatic execution quote was requested" in fresh


def test_ca_legacy_preview_never_promotes_old_quote_to_live(tmp_path):
    import time
    manager = ClusterJobManager(tmp_path / "control")
    now = time.time()
    mint = "So11111111111111111111111111111111111111112"
    manager.jobs["stale"] = {
        "job_id":"stale", "mint":mint, "preset":"standard",
        "status":"RUNNING", "progress":{},
        "preview":{"execution_quote_30_usdc":{
            "status":"OK","route_exists":True,"observed_at":now,
            "execution_price_usdc":"0.01","price_impact_pct":"0.5",
        }},
    }
    entry = manager.get("stale")["preview"]["execution_quote_30_usdc"]
    assert entry["freshness_status"] == "ARCHIVED_NOT_LIVE"
    assert entry["is_current_at_response"] is False
    manager.jobs["stale"]["preview"]["execution_quote_30_usdc"]["route_exists"] = False
    assert manager.get("stale")["preview"]["execution_quote_30_usdc"]["is_current_at_response"] is False
    manager.executor.shutdown(wait=True)


def test_ca_frontend_never_exposes_legacy_execution_quote_as_current():
    from mission_agent.mission_control.server import Handler
    js = (Handler.static_root / "app.js").read_text()
    html = (Handler.static_root / "index.html").read_text()
    assert "execution_quote_30_usdc" not in js
    assert "caScheduleQuoteExpiry" not in js
    assert "caQuoteCurrent" not in js
    assert "cluster-preview-quote" not in js
    assert "cluster-final-quote" not in js
    assert "$30 实际可成交价" not in js
    assert "id=\\\"cluster-preset\\\"" not in html
    assert "统一研究入口" in html


