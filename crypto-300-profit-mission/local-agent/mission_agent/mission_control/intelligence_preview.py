"""Offline, read-only Option 3 P3 preview. No production sender, outbox, or API.

Creates a self-contained local HTML evidence page and a JSON array of
SIMULATED intelligence updates. Existing V1 alerts are not referenced or sent.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .intelligence import analyze_candidate

_BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,88}$")
_MAX_CANDIDATES = 5000


def _time(value: Any) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        return "UNKNOWN"
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except (OverflowError, ValueError, OSError):
        return "UNKNOWN"


def _s(value: Any) -> str:
    return html.escape(str(value) if value is not None else "UNKNOWN", quote=True)


def _solscan(kind: str, value: Any) -> str:
    if not isinstance(value, str) or not _BASE58.fullmatch(value):
        return ""
    if kind not in {"token", "tx"}:
        return ""
    return "https://solscan.io/" + kind + "/" + value


def _link(kind: str, value: Any, label: str) -> str:
    url = _solscan(kind, value)
    if not url:
        return ""
    return '<a href="' + _s(url) + '" target="_blank" rel="noopener noreferrer">' + _s(label) + "</a>"


def analyze_rows(
    candidates: list[Mapping[str, Any]],
    *,
    as_of: float,
    max_market_age_seconds: int,
    market_observations: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(candidates, list) or len(candidates) > _MAX_CANDIDATES:
        raise ValueError("INVALID_CANDIDATE_BATCH")
    markets = market_observations if isinstance(market_observations, Mapping) else {}
    result = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ValueError("INVALID_CANDIDATE")
        mint = candidate.get("mint")
        market = markets.get(mint) if isinstance(mint, str) else None
        item = analyze_candidate(
            candidate, as_of=as_of,
            market=market if isinstance(market, Mapping) else None,
            max_market_age_seconds=max_market_age_seconds,
        )
        item["model_episode_position_state"] = (candidate.get("position_state")
            if item.get("latest_action_at") is not None and
               isinstance(candidate.get("position_state"), str) else "UNVERIFIED")
        result.append(item)
    return result


def fake_intelligence_updates(
    analyses: list[Mapping[str, Any]], *, as_of: float,
    max_event_age_seconds: int, previously_seen: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return synthetic preview objects; this function has no provider/IO hooks.

    Deliberately limited to a VERIFIED new SELL event. No initial ACC/MULT
    rebroadcast, no implicit price-alert thresholds, no SEND authority.
    """
    if (isinstance(max_event_age_seconds, bool) or
            not isinstance(max_event_age_seconds, int) or
            max_event_age_seconds <= 0):
        raise ValueError("EVENT_FRESHNESS_LIMIT_REQUIRED")
    seen = set(previously_seen or ())
    updates = []
    for item in analyses:
        facts = item.get("facts") or []
        at = item.get("latest_action_at")
        signature = item.get("latest_signature")
        mint = item.get("mint")
        if ("FRANK_SELL_OBSERVED_REVIEW_RISK" not in facts or
                not isinstance(at, (float, int)) or isinstance(at, bool) or
                not (0 <= as_of - at <= max_event_age_seconds) or
                not isinstance(signature, str) or not signature or
                not isinstance(mint, str) or not mint):
            continue
        identity = json.dumps(
            ["INTELLIGENCE_UPDATE", "FRANK_SELL_OBSERVED_REVIEW_RISK",
             mint, signature, at], separators=(",", ":"), ensure_ascii=True,
        )
        key = "INTELLIGENCE_UPDATE:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        updates.append({
            "kind": "INTELLIGENCE_UPDATE",
            "mode": "FAKE_PREVIEW_ONLY_NO_SEND",
            "key": key,
            "mint": mint,
            "signature": signature,
            "observed_at": at,
            "event": "FRANK_VERIFIED_SELL",
            "body": "Frank confirmed SELL observed; review previous assumptions. Historical source fact, not trade advice.",
            "send_allowed": False,
            "channels": [],
        })
    return updates


def render_html(
    analyses: list[Mapping[str, Any]], *, as_of: float,
    simulated_updates: list[Mapping[str, Any]],
) -> str:
    cards = []
    for a in analyses:
        price = a["price"]
        delta = price.get("change_pct_vs_last_verified_buy")
        if delta is None:
            comparison = "UNAVAILABLE (" + str(price["status"]) + ")"
        else:
            comparison = str(delta) + "% relative to verified Frank buy reference; NOT executable return"
        facts = ", ".join(a["facts"]) or "NONE_VERIFIED"
        missing = ", ".join(a["missing"]) or "NONE_REPORTED"
        mint = a["mint"]
        signature = a.get("latest_signature")
        pattern = a.get("pattern")
        cards.append(
            '<article class="card"><div class="label">' + _s(pattern) +
            ' / RESEARCH ONLY</div><h2 class="mint">' + _s(mint) + '</h2>' +
            '<div class="actions"><button type="button" data-ca="' +
            _s(mint) + '">Copy CA</button> ' + _link("token", mint, "Token on Solscan") +
            " " + _link("tx", signature, "Verified transaction") + "</div>" +
            '<dl><dt>Latest verified side</dt><dd>' + _s(a["latest_side"]) +
            '</dd><dt>Latest action time</dt><dd>' + _s(_time(a.get("latest_action_at"))) +
            '</dd><dt>V1 source signal ID</dt><dd>' + _s(a.get("source_signal_id")) +
            '</dd><dt>Model episode state (NOT chain balance)</dt><dd>' +
            _s(a.get('model_episode_position_state')) +
            '</dd><dt>Source-confirmed facts</dt><dd>' + _s(facts) +
            '</dd><dt>Not verified / missing</dt><dd>' + _s(missing) +
            '</dd><dt>Price comparison</dt><dd>' + _s(comparison) +
            '</dd><dt>Frank verified buy reference (USDC/token)</dt><dd>' +
            _s(price.get("buy_price_usdc")) +
            '</dd><dt>Market reference (USDC/token)</dt><dd>' +
            _s(price.get("market_price_usdc")) +
            '</dd><dt>Market source and observation time</dt><dd>' +
            _s(price.get("market_source")) + " / " +
            _s(_time(price.get("market_observed_at"))) +
            '</dd><dt>Execution</dt><dd>NOT ASSESSED, user amount not supplied</dd></dl></article>'
        )
    notices = "".join(
        '<li><strong>FAKE ONLY, UNSENT</strong> ' + _s(n["event"]) + " " +
        _s(n["mint"]) + " (" + _s(_time(n["observed_at"])) + ")</li>"
        for n in simulated_updates
    )
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; connect-src 'none'; form-action 'none'">
<title>Frank Option 3: evidence-only local preview</title>
<style>
:root{font-family:system-ui,-apple-system,sans-serif;color-scheme:light dark}
body{max-width:1100px;margin:auto;padding:18px;line-height:1.5}
header{border-bottom:1px solid #777;padding-bottom:12px}
.tag{font-weight:bold}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:16px}
.card{border:1px solid #888;border-radius:12px;padding:16px;overflow-wrap:anywhere}
.label{font-size:.78rem;font-weight:bold}h2{font-size:1.05rem}
dl{display:grid;grid-template-columns:1fr 2fr;gap:8px}dt{font-weight:600}dd{margin:0}
.actions{margin-bottom:14px}button{padding:6px 12px;cursor:pointer}
input{padding:8px;max-width:100%}.notice{border-top:1px solid #777;padding-top:12px;margin-top:16px}
</style></head><body>
<header><h1>Frank amount-free intelligence</h1>
<p class="tag">LOCAL, READ-ONLY SNAPSHOT / RESEARCH ONLY / NOT LIVE ALERTS</p>
<p>Snapshot as of """ + _s(_time(as_of)) + """.
Original V1 ACCUMULATION/MULTIPLE delivery is not accessed or changed.
No amount, route, liquidity or user follow-profit claim is made.</p>
<label>Find CA (locally) <input id="filter" type="search" placeholder="Filter visible cards"></label></header>
<main id="cards">""" + "".join(cards) + """</main>
<section class="notice"><h2>Simulated intelligence changes, not sent</h2>
<p>Only observed SELL events with verifiable signatures in the explicitly selected
freshness window qualify for this demonstration. Other risk state transitions
are not authorized or asserted. Repeated source events are deduplicated within
this batch. The original V1 alerts are never replayed here.</p>
<ul>""" + (notices or "<li>No qualifying new SELL fact in this snapshot.</li>") + """</ul></section>
<script>
document.getElementById('filter').addEventListener('input',function(){
 const q=this.value.toLowerCase();
 document.querySelectorAll('.card').forEach(c=>c.hidden=!c.textContent.toLowerCase().includes(q));
});
document.querySelectorAll('button[data-ca]').forEach(b=>b.addEventListener('click',async()=>{
 const ca=b.getAttribute('data-ca');
 try{if(!navigator.clipboard)throw Error('clipboard unavailable');
  await navigator.clipboard.writeText(ca);b.textContent='Copied CA';}
 catch(e){const t=document.createElement('textarea');t.value=ca;document.body.appendChild(t);
  t.select();let ok=document.execCommand('copy');t.remove();
  b.textContent=ok?'Copied CA':'Select and copy CA above';}
}));
</script></body></html>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Frank Option 3 OFFLINE preview; no sender and no network")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--candidate-json", type=Path, help="Explicit local file containing candidate list")
    src.add_argument("--production-root", type=Path, help="Explicit existing Frank local root, read-only SQLite")
    parser.add_argument("--market-json", type=Path, help="Optional explicit offline {mint: market observation} mapping")
    parser.add_argument("--previous-fake-json", type=Path, help="Optional prior fake preview JSON for cross-run simulated dedupe (read only)")
    parser.add_argument("--output", type=Path, required=True, help="Local HTML output path")
    parser.add_argument("--fake-out", type=Path, required=True, help="Local fake-only alert JSON output path")
    parser.add_argument("--max-market-age-seconds", type=int, required=True)
    parser.add_argument("--max-event-age-seconds", type=int, required=True)
    parser.add_argument("--as-of", type=float, help="Optional reproducible Unix-second cutoff; default invocation time")
    args = parser.parse_args(argv)
    if args.output.resolve() == args.fake_out.resolve():
        parser.error("HTML and fake JSON output paths must differ")
    as_of = time.time() if args.as_of is None else args.as_of
    if args.production_root is not None:
        from .frank import FrankReader
        candidates = FrankReader(args.production_root).candidates()
    else:
        candidates = json.loads(args.candidate_json.read_text(encoding="utf-8"))
    markets = json.loads(args.market_json.read_text(encoding="utf-8")) if args.market_json else None
    analyses = analyze_rows(
        candidates, as_of=as_of, max_market_age_seconds=args.max_market_age_seconds,
        market_observations=markets,
    )
    previous = json.loads(args.previous_fake_json.read_text(encoding="utf-8")) if args.previous_fake_json else None
    seen = {str(msg["key"]) for msg in previous.get("messages", []) if isinstance(msg, dict) and isinstance(msg.get("key"), str)} if isinstance(previous, dict) else set()
    updates = fake_intelligence_updates(
        analyses, as_of=as_of, max_event_age_seconds=args.max_event_age_seconds,
        previously_seen=seen,
    )
    args.output.write_text(render_html(analyses, as_of=as_of, simulated_updates=updates), encoding="utf-8")
    args.fake_out.write_text(
        json.dumps({"mode": "FAKE_PREVIEW_ONLY_NO_SEND", "as_of": as_of,
                    "messages": updates}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps({"status": "OFFLINE_PREVIEW_WRITTEN", "cards": len(analyses),
                      "fake_updates": len(updates), "no_send": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
