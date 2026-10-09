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


def test_ca_early_jupiter_quote_precedes_holder_history_and_is_timestamped(tmp_path):
    manager = ClusterJobManager(tmp_path / "control")
    mint = "So11111111111111111111111111111111111111112"
    manager.jobs["early"] = {
        "job_id": "early", "mint": mint, "preset": "quick",
        "status": "RUNNING", "progress": {},
    }
    calls = []
    def mocked_quote(quoted_mint, decimals, **kwargs):
        calls.append((quoted_mint, decimals, kwargs["usdc_amount"]))
        return {
            "status": "OK", "source": "JUPITER_OFFICIAL",
            "route_exists": True, "observed_at": 1_800_000_000.0,
            "execution_price_usdc": "0.00123",
            "price_impact_pct": "0.40",
            "route_plan": [{"internal": "not_for_preview"}],
        }
    manager.jupiter.quote_usdc_to_token = mocked_quote
    manager._set_progress("early", "BASE_READY", {
        "token_profile": {
            "status": "OK", "decimals": 6, "mint_authority": None,
            "freeze_authority": None,
        },
        "market": {
            "status": "OK", "name": "Example", "symbol": "EX",
            "main_pair": {"liquidity_usd": 50000},
        },
    })
    early = manager.get("early")
    assert calls == [(mint, 6, 30)]
    assert early["progress"]["stage"] == "BASE_READY"
    initial_quote = early["preview"]["execution_quote_30_usdc"]
    assert {k: initial_quote.get(k) for k in (
        "status","source","reason","observed_at","route_exists",
        "execution_price_usdc","price_impact_pct",
    )} == {
        "status": "OK", "source": "JUPITER_OFFICIAL",
        "reason": None, "observed_at": 1_800_000_000.0,
        "route_exists": True, "execution_price_usdc": "0.00123",
        "price_impact_pct": "0.40",
    }
    assert initial_quote["valid_until"] == 1_800_000_030.0
    assert initial_quote["quote_record_type"] == "HISTORICAL_SNAPSHOT"
    assert initial_quote["freshness_status"] in {"EXPIRED", "UNAVAILABLE"}
    assert initial_quote["is_current_at_response"] is False
    manager._set_progress("early", "HOLDERS_READY", {
        "top_accounts_resolved": 20, "raw_top10_resolved_pct": "42",
    })
    later = manager.get("early")
    assert later["preview"]["execution_quote_30_usdc"]["valid_until"] == initial_quote["valid_until"]
    assert later["preview"]["execution_quote_30_usdc"]["execution_price_usdc"] == "0.00123"
    assert later["preview"]["top_accounts_resolved"] == 20
    manager.executor.shutdown(wait=True)


def test_ca_early_quote_fails_closed_when_mint_decimals_unverified(tmp_path):
    manager = ClusterJobManager(tmp_path / "control")
    manager.jobs["unknown"] = {
        "job_id": "unknown", "mint": "X" * 44, "preset": "quick",
        "status": "RUNNING", "progress": {},
    }
    def must_not_quote(*args, **kwargs):
        raise AssertionError("unverified decimals must never request a trade quote")
    manager.jupiter.quote_usdc_to_token = must_not_quote
    manager._set_progress("unknown", "BASE_READY", {
        "token_profile": {"status": "UNAVAILABLE", "decimals": None},
        "market": {"status": "UNAVAILABLE"},
    })
    result = manager.get("unknown")["preview"]["execution_quote_30_usdc"]
    assert result["status"] == "UNAVAILABLE"
    assert result["reason"] == "TOKEN_DECIMALS_UNKNOWN"
    manager.executor.shutdown(wait=True)


def test_ca_frontend_null_is_unknown_and_quote_is_time_limited():
    import subprocess
    root = Handler.static_root
    js = (root / "app.js").read_text()
    assert "const quoteFresh=" in js
    assert "quoteAge<=30" in js
    assert "报价已过期" in js
    assert "fact('$30 可成交报价'" in js
    script = r"""
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync(process.argv[1],'utf8');
const p1=js.slice(js.indexOf('const n = '), js.indexOf('const short ='));
const p2=js.slice(js.indexOf('function usd('), js.indexOf('function authorityText('));
if (!p1 || !p2) throw Error('MISSING_HELPERS');
const result=vm.runInNewContext(
  p1 + '\n' + p2 + '\n' +
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
    assert "first_quote_preview_seconds" in body
    assert "full_report_seconds" in body
    assert "REAL_CA_SCHEMA_AND_SEMANTICS: PASS" in body
    assert "mission-control.sqlite" in body
    assert "No Mission Control loop" in body
    subprocess.run(["bash","-n",str(script)],check=True)


def test_ca_partial_preview_survives_depth_failure_and_stale_quotes_are_hidden():
    import subprocess
    js=Handler.static_root / "app.js"
    script=r"""
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync(process.argv[1],'utf8');
const fn=js.slice(js.indexOf('function renderClusterPreview(job)'),js.indexOf('function clusterErrorMessage('));
const panel={hidden:true,innerHTML:''};
const now=Date.now()/1000;
const ctx={
  Date,Number,NaN,
  $:()=>panel,
  esc:x=>String(x ?? ''),
  usd:x=>x==null?'暂无':'$'+x,
  smallPrice:x=>String(x),
  pctText:x=>String(x)+'%',
  fact:(name,value)=>name+':'+value+';',
};
vm.runInNewContext(fn+'\nrenderClusterPreview(job);',
  {...ctx,job:{
    status:'ERROR',
    preview:{
      token_status:'OK',mint_authority:null,freeze_authority:null,
      market_status:'OK',name:'Sample',symbol:'S',
      price_usd:'0.01',market_cap_usd:null,liquidity_usd:null,
      execution_quote_30_usdc:{
        status:'OK',route_exists:true,observed_at:now-40,
        execution_price_usdc:'0.012',price_impact_pct:'0.2'
      }
    }
  }}
);
if(panel.hidden) throw Error('PREVIEW_DISCARDED_ON_FAILURE');
if(!panel.innerHTML.includes('深度分析未完成')) throw Error('MISSING_INCOMPLETE_WARNING');
if(!panel.innerHTML.includes('报价已过期')) throw Error('STALE_QUOTE_SHOWN');
if(!panel.innerHTML.includes('市值:暂无')) throw Error('MISSING_METRIC_ZEROED');
"""
    subprocess.run(["node","-e",script,str(js)],check=True)



def test_ca_quote_archive_has_explicit_expiry_and_dynamic_api_freshness(tmp_path, monkeypatch):
    import json
    import mission_agent.mission_control.server as server
    from mission_agent.meme.cluster import markdown

    sample = {
        "status": "OK", "route_exists": True,
        "observed_at": 1800000000.0,
        "execution_price_usdc": "0.001",
        "price_impact_pct": "0.2",
    }
    archived = server._annotate_ca_quote(sample, archived=True)
    assert archived["quote_record_type"] == "HISTORICAL_SNAPSHOT"
    assert archived["valid_until"] == 1800000030.0
    assert archived["freshness_status"] == "ARCHIVED_NOT_LIVE"
    assert archived["is_current_at_response"] is False
    assert "freshness_checked_at" not in archived
    current = server._annotate_ca_quote(archived, now=1800000020.0)
    assert current["is_current_at_response"] is True
    assert current["freshness_status"] == "CURRENT_AT_RESPONSE"
    at_expiry = server._annotate_ca_quote(archived, now=1800000030.0)
    assert at_expiry["is_current_at_response"] is True
    expired = server._annotate_ca_quote(archived, now=1800000030.001)
    assert expired["is_current_at_response"] is False
    assert expired["freshness_status"] == "EXPIRED"
    assert server._annotate_ca_quote({
        **sample, "observed_at": None,
    }, now=1800000010.0)["is_current_at_response"] is False
    assert server._annotate_ca_quote({
        **sample, "observed_at": 1800000060,
    }, now=1800000010.0)["is_current_at_response"] is False

    mint = "So11111111111111111111111111111111111111112"
    manager = ClusterJobManager(tmp_path / "control")
    dest = manager.report_root / mint
    dest.mkdir(parents=True)
    saved = {"mint":mint,"execution_quote_30_usdc":archived}
    (dest/"latest.json").write_text(json.dumps(saved))
    monkeypatch.setattr(server.time,"time",lambda:1800000020.0)
    read_now = manager.latest(mint)
    assert read_now["execution_quote_30_usdc"]["is_current_at_response"] is True
    monkeypatch.setattr(server.time,"time",lambda:1800000031.0)
    read_later = manager.latest(mint)
    assert read_later["execution_quote_30_usdc"]["is_current_at_response"] is False
    assert json.loads((dest/"latest.json").read_text()) == saved
    manager.executor.shutdown(wait=True)

    report = {"mint":mint,"observed_at":1800000005.0,
              "execution_quote_30_usdc":archived}
    rendered = markdown(report)
    assert "HISTORICAL_SNAPSHOT" in rendered
    assert 'Market snapshot (historical; not live)' in rendered
    assert "observed_at:" in rendered and "valid_until:" in rendered
    assert "30 seconds after quote" in rendered


def test_ca_quote_api_does_not_turn_old_or_unexecutable_route_into_current(tmp_path,monkeypatch):
    import time
    import mission_agent.mission_control.server as server
    manager = ClusterJobManager(tmp_path / "control")
    now = time.time()
    mint = "So11111111111111111111111111111111111111112"
    manager.jobs["stale"] = {
        "job_id":"stale", "mint":mint, "preset":"quick",
        "status":"RUNNING", "progress":{},
        "preview":{"execution_quote_30_usdc":{
            "status":"OK","route_exists":True,"observed_at":now-40,
            "execution_price_usdc":"0.01","price_impact_pct":"0.5",
        }},
    }
    assert manager.get("stale")["preview"]["execution_quote_30_usdc"]["freshness_status"] == "EXPIRED"
    manager.jobs["stale"]["preview"]["execution_quote_30_usdc"]["observed_at"] = now
    manager.jobs["stale"]["preview"]["execution_quote_30_usdc"]["route_exists"] = False
    assert manager.get("stale")["preview"]["execution_quote_30_usdc"]["is_current_at_response"] is False
    manager.executor.shutdown(wait=True)
