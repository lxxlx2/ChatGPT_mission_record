#!/usr/bin/env python3
"""Create X-ready market content from public sources without publishing it."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import email.utils
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
DEFAULT_ARTIFACTS = ROOT / "artifacts"
DEFAULT_STATE = ROOT / "state" / "seen.json"
NASDAQ_HOST = "api.nasdaq.com"
KRAKEN_HOST = "api.kraken.com"
RSS_HOSTS = {"www.federalreserve.gov", "www.sec.gov"}
SOURCE_HOSTS = {NASDAQ_HOST, KRAKEN_HOST, *RSS_HOSTS}
MAX_RESPONSE_BYTES = 1_000_000
MARKET_SYMBOLS = (
    ("COMP", "index", "Nasdaq Comp"),
    ("NDX", "index", "Nasdaq-100"),
    ("SOX", "index", "Semis"),
)
IMMUTABLE_ARTIFACT_FILES = (
    "candidate.txt",
    "approval-packet.md",
    "source-snapshot.json",
    "detected-trends.json",
    "analysis.json",
    "quality-check.json",
)


class PipelineError(RuntimeError):
    pass


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_money(value: str) -> float:
    return float(value.replace("$", "").replace(",", "").strip())


def parse_percent(value: str) -> float:
    return float(value.replace("%", "").replace("+", "").strip())


def parse_trade_date(value: object) -> str:
    match = re.search(r"[A-Z][a-z]{2} \d{1,2}, \d{4}", str(value or ""))
    if not match:
        raise PipelineError(f"Nasdaq returned an unreadable trade timestamp: {value}")
    return dt.datetime.strptime(match.group(0), "%b %d, %Y").date().isoformat()


def checked_read(url: str, allowed_hosts: set[str], headers: dict[str, str]) -> tuple[bytes, str]:
    requested = urllib.parse.urlparse(url)
    if requested.scheme != "https" or requested.hostname not in allowed_hosts:
        raise PipelineError(f"source is not allowlisted: {url}")
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=25) as response:
        final = urllib.parse.urlparse(response.url)
        if final.scheme != "https" or final.hostname not in allowed_hosts:
            raise PipelineError(f"source redirected outside allowlist: {response.url}")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_RESPONSE_BYTES:
            raise PipelineError(f"source response is too large: {url}")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise PipelineError(f"source response exceeded limit: {url}")
        if response.status != 200:
            raise PipelineError(f"source returned HTTP {response.status}: {url}")
    return raw, response.url


def fetch_nasdaq(now: dt.datetime) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object]]:
    result: dict[str, object] = {}
    receipts: list[dict[str, object]] = []
    headers = {
        "User-Agent": "Mozilla/5.0 AppleWebKit/537.36 Chrome/140 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nasdaq.com/market-activity/",
    }
    for symbol, asset_class, display_name in MARKET_SYMBOLS:
        url = f"https://{NASDAQ_HOST}/api/quote/{symbol}/info?assetclass={asset_class}"
        raw, final_url = checked_read(url, {NASDAQ_HOST}, headers)
        payload = json.loads(raw)
        data = payload.get("data")
        if not isinstance(data, dict):
            raise PipelineError(f"Nasdaq returned no data for {symbol}")
        # Nasdaq normally exposes the regular-session close as secondaryData
        # after hours, but on weekends it can omit secondaryData and put the
        # latest completed session in primaryData instead.
        market_status = str(data.get("marketStatus") or "")
        primary = data.get("primaryData")
        secondary = data.get("secondaryData")
        if market_status == "After-Hours" and isinstance(secondary, dict):
            field = secondary
            price_basis = "regular_close"
        elif isinstance(primary, dict):
            field = primary
            price_basis = "latest_session_primary" if market_status == "Closed" else "live_primary"
        elif isinstance(secondary, dict):
            field = secondary
            price_basis = "regular_close"
        else:
            field = None
        if not isinstance(field, dict):
            raise PipelineError(f"Nasdaq quote shape changed for {symbol}")
        price = parse_money(str(field["lastSalePrice"]))
        change = parse_percent(str(field["percentageChange"]))
        if not (0 < price < 1_000_000 and -50 <= change <= 50):
            raise PipelineError(f"Nasdaq quote failed sanity bounds for {symbol}")
        trade_timestamp = field.get("lastTradeTimestamp")
        result[symbol] = {
            "display_name": display_name,
            "price_usd": price,
            "change_percent": change,
            "trade_timestamp": trade_timestamp,
            "trade_date": parse_trade_date(trade_timestamp),
            "market_status": market_status,
            "price_basis": price_basis,
        }
        receipts.append({"source": "Nasdaq", "url": url, "final_url": final_url, "fetched_at": iso(utc_now()), "response_sha256": sha256(raw)})
    observed_dates = {symbol: str(value["trade_date"]) for symbol, value in result.items()}
    trade_dates = set(observed_dates.values())
    if len(trade_dates) != 1:
        raise PipelineError(f"Nasdaq index basket is not from one session: {', '.join(sorted(trade_dates))}")
    trade_date = dt.date.fromisoformat(next(iter(trade_dates)))
    market_date = now.astimezone(ZoneInfo("America/New_York")).date()
    if not 0 <= (market_date - trade_date).days <= 4:
        raise PipelineError(f"Nasdaq index basket is stale or future-dated: {trade_date}")
    selection = {
        "policy": "fixed US equity index basket sharing one recent Nasdaq session",
        "selected_trade_date": trade_date.isoformat(),
        "selected_symbols": list(result),
        "observed_trade_dates": observed_dates,
    }
    return result, receipts, selection


def fetch_kraken(now: dt.datetime) -> tuple[dict[str, object], list[dict[str, object]]]:
    url = f"https://{KRAKEN_HOST}/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD"
    raw, final_url = checked_read(url, {KRAKEN_HOST}, {"User-Agent": "x-revenue-workflow/1.0", "Accept": "application/json"})
    payload = json.loads(raw)
    if payload.get("error") != [] or not isinstance(payload.get("result"), dict):
        raise PipelineError("Kraken returned an API error")
    aliases = {"BTC": ("XBT",), "ETH": ("ETH",), "SOL": ("SOL",)}
    result: dict[str, object] = {}
    for symbol, needles in aliases.items():
        matches = [(key, value) for key, value in payload["result"].items() if any(needle in key for needle in needles)]
        if len(matches) != 1:
            raise PipelineError(f"Kraken pair resolution changed for {symbol}")
        pair, data = matches[0]
        price = float(data["c"][0])
        open_price = float(data["o"])
        change = (price / open_price - 1) * 100
        if not (0 < price < 10_000_000 and 0 < open_price < 10_000_000 and -50 <= change <= 50):
            raise PipelineError(f"Kraken quote failed sanity bounds for {symbol}")
        result[symbol] = {"price_usd": price, "utc_open_usd": open_price, "change_percent_vs_utc_open": change, "resolved_pair": pair}
    receipt = {"source": "Kraken", "url": url, "final_url": final_url, "fetched_at": iso(utc_now()), "response_sha256": sha256(raw)}
    return result, [receipt]


def parse_rfc_date(value: str) -> dt.datetime:
    parsed = email.utils.parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def fetch_rss(now: dt.datetime) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    feeds = (
        ("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml"),
        ("SEC", "https://www.sec.gov/news/pressreleases.rss"),
    )
    items: list[dict[str, object]] = []
    receipts: list[dict[str, object]] = []
    keywords = {"market": 3, "trading": 3, "crypto": 3, "rate": 3, "monetary": 3, "investment": 2, "bank": 2, "adviser": 2, "securities": 2, "fraud": 1}
    for source, url in feeds:
        raw, final_url = checked_read(url, RSS_HOSTS, {"User-Agent": "x-revenue-workflow/1.0 contact=local-user", "Accept": "application/rss+xml,text/xml"})
        root = ET.fromstring(raw.lstrip(b"\xef\xbb\xbf"))
        for node in root.findall(".//item")[:20]:
            title = " ".join((node.findtext("title") or "").split())
            link = (node.findtext("link") or "").strip()
            date_raw = (node.findtext("pubDate") or "").strip()
            if not title or not link or not date_raw:
                continue
            published = parse_rfc_date(date_raw)
            age_hours = (now - published).total_seconds() / 3600
            if age_hours < -5 / 60 or age_hours > 24 * 7:
                continue
            age_hours = max(0.0, age_hours)
            lower = title.lower()
            relevance = sum(weight for word, weight in keywords.items() if word in lower)
            score = round(1 + relevance + max(0.0, 72 - age_hours) / 24, 3)
            items.append({"source": source, "title": title, "url": link, "published_at": iso(published), "age_hours": round(age_hours, 2), "trend_score": score})
        receipts.append({"source": source, "url": url, "final_url": final_url, "fetched_at": iso(utc_now()), "response_sha256": sha256(raw)})
    deduped: dict[str, dict[str, object]] = {}
    for item in items:
        key = re.sub(r"[^a-z0-9]+", " ", str(item["title"]).lower()).strip()
        if key not in deduped or float(item["trend_score"]) > float(deduped[key]["trend_score"]):
            deduped[key] = item
    ranked = sorted(
        deduped.values(),
        key=lambda value: (
            -float(value["trend_score"]),
            -dt.datetime.fromisoformat(str(value["published_at"]).replace("Z", "+00:00")).timestamp(),
        ),
    )
    return ranked[:8], receipts


def signed(value: float) -> str:
    return f"{value:+.2f}%"


def analyze(stocks: dict[str, object], crypto: dict[str, object], trends: list[dict[str, object]]) -> dict[str, object]:
    stock_changes = [float(value["change_percent"]) for value in stocks.values()]
    crypto_changes = [float(crypto[s]["change_percent_vs_utc_open"]) for s in ("BTC", "ETH", "SOL")]
    stock_up = sum(value > 0 for value in stock_changes)
    crypto_up = sum(value > 0 for value in crypto_changes)
    if stock_up >= 2 and crypto_up >= 2:
        signal = "broad_risk_on"
        interpretation = "risk appetite is broad across US stocks and crypto"
    elif stock_up <= 1 and crypto_up <= 1:
        signal = "broad_risk_off"
        interpretation = "risk appetite is weak across US stocks and crypto"
    else:
        signal = "cross_asset_divergence"
        interpretation = "US stocks and crypto diverge; conviction is limited"
    return {
        "signal": signal,
        "interpretation": interpretation,
        "stock_breadth_up": stock_up,
        "crypto_breadth_up": crypto_up,
        "stock_dispersion_percentage_points": round(max(stock_changes) - min(stock_changes), 2),
        "crypto_dispersion_percentage_points": round(max(crypto_changes) - min(crypto_changes), 2),
        "top_official_trend": {
            "source": trends[0]["source"],
            "title": trends[0]["title"],
            "trend_score": trends[0]["trend_score"],
        } if trends else None,
    }


def make_candidate(now: dt.datetime, stocks: dict[str, object], crypto: dict[str, object], analysis: dict[str, object]) -> str:
    session = dt.date.fromisoformat(str(next(iter(stocks.values()))["trade_date"]))
    session_label = f"{session:%b} {session.day}"
    stock_text = ", ".join(f"{value['display_name']} {signed(float(value['change_percent']))}" for value in stocks.values())
    text = (
        f"{session_label} pulse: {stock_text}; "
        f"BTC {signed(float(crypto['BTC']['change_percent_vs_utc_open']))}, "
        f"ETH {signed(float(crypto['ETH']['change_percent_vs_utc_open']))}, SOL {signed(float(crypto['SOL']['change_percent_vs_utc_open']))} vs UTC open. "
        f"Breadth {analysis['stock_breadth_up']}/3 stock indexes, {analysis['crypto_breadth_up']}/3 crypto. "
        f"Read: {analysis['interpretation']}. Nasdaq + Kraken, {now:%H:%M} UTC."
    )
    return text


def quality(candidate: str, receipts: list[dict[str, object]], now: dt.datetime) -> dict[str, object]:
    forbidden = re.findall(r"\b(?:guaranteed?|sure profit|must buy|must sell|risk[- ]free)\b", candidate, flags=re.I)
    fetched = [dt.datetime.fromisoformat(str(item["fetched_at"]).replace("Z", "+00:00")) for item in receipts]
    checks = {
        "length_at_most_280": len(candidate) <= 280,
        "source_receipts_present": len(receipts) >= len(MARKET_SYMBOLS) + 3,
        "sources_fresh_at_generation": all(abs((now - value).total_seconds()) <= 300 for value in fetched),
        "no_guarantee_or_trade_directive": not forbidden,
        "uses_only_constructed_source_values": True,
        "human_approval_required": True,
        "external_publish_not_called": True,
    }
    return {"passed": all(checks.values()), "checks": checks, "character_count": len(candidate), "forbidden_matches": forbidden}


def safe_root(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise PipelineError("unsafe output root")
    resolved = expanded.resolve()
    if resolved == Path("/") or resolved == Path.home():
        raise PipelineError("unsafe output root")
    if resolved != DEFAULT_ARTIFACTS.resolve():
        raise PipelineError("output root must be the canonical x-revenue artifacts directory")
    return resolved


def canonical_artifact(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise PipelineError("artifact path must not be a symlink")
    resolved = expanded.resolve()
    if resolved.parent != DEFAULT_ARTIFACTS.resolve() or not resolved.is_dir():
        raise PipelineError("artifact must be one direct child of the canonical artifacts directory")
    return resolved


def safe_state_file(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_symlink() or expanded.resolve() != DEFAULT_STATE.resolve():
        raise PipelineError("state file must be the canonical x-revenue state file")
    return expanded.resolve()


@contextlib.contextmanager
def exclusive_run_lock(state_file: Path):
    state_file.parent.mkdir(parents=True, exist_ok=True)
    lock_path = state_file.with_name("run.lock")
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise PipelineError("another x-revenue run is already active") from exc
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def load_validated_artifact(artifact: Path) -> dict[str, object]:
    artifact = canonical_artifact(artifact)
    required = {*IMMUTABLE_ARTIFACT_FILES, "approval.json", "manifest.json"}
    linked = sorted(name for name in required if (artifact / name).is_symlink())
    if linked:
        raise PipelineError(f"artifact contains symlinked files: {', '.join(linked)}")
    missing = sorted(name for name in required if not (artifact / name).is_file())
    if missing:
        raise PipelineError(f"artifact is incomplete; missing: {', '.join(missing)}")

    candidate_raw = (artifact / "candidate.txt").read_bytes()
    candidate = candidate_raw.rstrip(b"\n")
    manifest = json.loads((artifact / "manifest.json").read_text())
    approval = json.loads((artifact / "approval.json").read_text())
    qa = json.loads((artifact / "quality-check.json").read_text())
    source_snapshot = json.loads((artifact / "source-snapshot.json").read_text())
    stocks = source_snapshot.get("stocks", {})
    stock_selection = source_snapshot.get("stock_selection", {})
    stock_dates = {
        value.get("trade_date")
        for value in stocks.values()
        if isinstance(value, dict)
    } if isinstance(stocks, dict) else set()
    receipts = source_snapshot.get("receipts", [])
    receipt_schemes = {
        urllib.parse.urlparse(str(receipt.get("final_url", ""))).scheme
        for receipt in receipts
        if isinstance(receipt, dict)
    }
    receipt_hosts = {
        urllib.parse.urlparse(str(receipt.get("final_url", ""))).hostname
        for receipt in receipts
        if isinstance(receipt, dict)
    }
    generated_at = dt.datetime.fromisoformat(str(manifest.get("generated_at_utc", "")).replace("Z", "+00:00"))
    generated_market_date = generated_at.astimezone(ZoneInfo("America/New_York")).date()
    stock_session_age = (generated_market_date - dt.date.fromisoformat(next(iter(stock_dates)))).days if len(stock_dates) == 1 and None not in stock_dates else -1
    stored_hashes = manifest.get("file_sha256", {})
    checks = {
        "run_id_matches_directory": manifest.get("run_id") == artifact.name,
        "candidate_matches_manifest": sha256(candidate) == manifest.get("candidate_sha256"),
        "candidate_matches_approval": sha256(candidate) == approval.get("candidate_sha256"),
        "immutable_file_hashes_match": isinstance(stored_hashes, dict)
        and all(stored_hashes.get(name) == sha256((artifact / name).read_bytes()) for name in IMMUTABLE_ARTIFACT_FILES),
        "quality_passed": qa.get("passed") is True and all(qa.get("checks", {}).values()),
        "manifest_ready_for_approval": manifest.get("content_ready_for_human_approval") is True,
        "quality_stage_passed": manifest.get("stage_status", {}).get("QUALITY_CHECK") == "PASS",
        "source_receipts_allowlisted": isinstance(receipts, list) and len(receipts) >= len(MARKET_SYMBOLS) + 3
        and receipt_hosts <= SOURCE_HOSTS
        and receipt_schemes == {"https"}
        and None not in receipt_hosts,
        "stock_session_consistent": isinstance(stocks, dict)
        and set(stocks) == {symbol for symbol, _, _ in MARKET_SYMBOLS}
        and len(stock_dates) == 1
        and None not in stock_dates,
        "stock_selection_matches_snapshot": isinstance(stock_selection, dict)
        and stock_selection.get("selected_symbols") == list(stocks)
        and stock_selection.get("selected_trade_date") == next(iter(stock_dates), None),
        "stock_session_recent_at_generation": 0 <= stock_session_age <= 4,
        "external_publish_not_recorded": manifest.get("external_publish_performed") is False,
        "approval_status_valid": approval.get("status") in {"PENDING_HUMAN_APPROVAL", "APPROVED", "REJECTED"},
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise PipelineError(f"artifact integrity check failed: {', '.join(failed)}")
    return {
        "artifact": artifact,
        "candidate": candidate,
        "manifest": manifest,
        "approval": approval,
        "quality": qa,
        "checks": checks,
    }


def _write_run_locked(output_root: Path, state_file: Path) -> Path:
    now = utc_now()
    output_root.mkdir(parents=True, exist_ok=True)
    staging = output_root / f".tmp-{uuid.uuid4().hex}"
    staging.mkdir(exist_ok=False)
    target: Path | None = None
    temp_state: Path | None = None
    renamed = False
    try:
        stocks, receipts_a, stock_selection = fetch_nasdaq(now)
        crypto, receipts_b = fetch_kraken(now)
        trends, receipts_c = fetch_rss(now)
        receipts = receipts_a + receipts_b + receipts_c
        analysis = analyze(stocks, crypto, trends)
        candidate = make_candidate(now, stocks, crypto, analysis)
        checked_at = utc_now()
        qa = quality(candidate, receipts, checked_at)
        candidate_digest = sha256(candidate.encode())
        substantive_candidate = re.sub(r", \d{2}:\d{2} UTC\.$", ".", candidate)
        fingerprint = sha256(substantive_candidate.encode())
        state = json.loads(state_file.read_text()) if state_file.exists() else {"candidate_fingerprints": []}
        duplicate = fingerprint in state.get("candidate_fingerprints", [])
        qa["checks"]["not_previously_generated"] = not duplicate
        qa["passed"] = all(qa["checks"].values())
        if not qa["passed"]:
            failed = [name for name, passed in qa["checks"].items() if not passed]
            raise PipelineError(f"quality gate failed: {', '.join(failed)}")
        breaking_values = {
            **{symbol: float(value["change_percent"]) for symbol, value in stocks.items()},
            **{symbol: float(crypto[symbol]["change_percent_vs_utc_open"]) for symbol in ("BTC", "ETH", "SOL")},
        }
        mover, move = max(breaking_values.items(), key=lambda item: abs(item[1]))
        breaking = {"triggered": abs(move) >= 3.0, "threshold_percent": 3.0, "largest_move": {"symbol": mover, "change_percent": round(move, 2)}, "action": "queue_for_human_review" if abs(move) >= 3.0 else "none"}
        source_snapshot = {"generated_at": iso(checked_at), "stock_selection": stock_selection, "stocks": stocks, "crypto": crypto, "receipts": receipts}
        manifest = {
            "schema_version": 1,
            "run_id": now.strftime("%Y%m%dT%H%M%SZ"),
            "generated_at_utc": iso(now),
            "quality_checked_at_utc": iso(checked_at),
            "generated_at_asia_bangkok": now.astimezone(dt.timezone(dt.timedelta(hours=7))).isoformat(),
            "pipeline": ["SOURCE", "DETECTION", "ANALYSIS", "DRAFT", "QUALITY_CHECK", "HUMAN_APPROVAL", "PUBLISH", "ANALYTICS"],
            "pipeline_branches": {
                "market_candidate": ["Nasdaq session selection", "Kraken live ticker", "cross-asset analysis", "candidate"],
                "official_trend_context": ["Federal Reserve and SEC RSS", "title deduplication", "recency and keyword scoring", "approval packet"],
            },
            "stage_status": {"SOURCE": "COMPLETE", "DETECTION": "COMPLETE", "ANALYSIS": "COMPLETE", "DRAFT": "COMPLETE", "QUALITY_CHECK": "PASS" if qa["passed"] else "FAIL", "HUMAN_APPROVAL": "PENDING", "PUBLISH": "LOCKED", "ANALYTICS": "NOT_APPLICABLE_BEFORE_PUBLISH"},
            "candidate_sha256": candidate_digest,
            "deduplication_fingerprint_sha256": fingerprint,
            "content_ready_for_human_approval": qa["passed"],
            "external_publish_performed": False,
            "model_used": None,
            "analysis_method": "deterministic cross-asset breadth and dispersion",
        }
        approval = {"status": "PENDING_HUMAN_APPROVAL", "candidate_sha256": candidate_digest, "decision": None, "actor": None, "decided_at": None, "note": None, "external_publish_allowed": False}
        brief = ["# X revenue candidate approval packet", "", f"Generated: {iso(now)}", "", "## Candidate", "", candidate, "", "## Detected official-source trends", ""]
        for item in trends[:5]:
            brief.append(f"- [{item['source']}] [{item['title']}]({item['url']}) — score {item['trend_score']}, published {item['published_at']}")
        brief.extend(["", "## Safety state", "", "Pending human approval. No external publish call was made.", ""])
        files: dict[str, bytes] = {
            "candidate.txt": (candidate + "\n").encode(),
            "approval-packet.md": ("\n".join(brief)).encode(),
            "source-snapshot.json": canonical_bytes(source_snapshot),
            "detected-trends.json": canonical_bytes({"items": trends, "breaking_detection": breaking}),
            "analysis.json": canonical_bytes(analysis),
            "quality-check.json": canonical_bytes(qa),
            "approval.json": canonical_bytes(approval),
        }
        manifest["file_sha256"] = {name: sha256(files[name]) for name in IMMUTABLE_ARTIFACT_FILES}
        files["manifest.json"] = canonical_bytes(manifest)
        for name, raw in files.items():
            (staging / name).write_bytes(raw)
        target = output_root / manifest["run_id"]
        if target.exists():
            raise PipelineError(f"refusing to overwrite existing run: {target}")
        staging.rename(target)
        renamed = True
        load_validated_artifact(target)
        new_state = {"candidate_fingerprints": (state.get("candidate_fingerprints", []) + [fingerprint])[-200:], "last_run": manifest["run_id"]}
        temp_state = state_file.with_name(f".{state_file.name}.{uuid.uuid4().hex}.tmp")
        temp_state.write_bytes(canonical_bytes(new_state))
        temp_state.replace(state_file)
        return target
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        if renamed and target is not None:
            shutil.rmtree(target, ignore_errors=True)
        if temp_state is not None:
            temp_state.unlink(missing_ok=True)
        raise


def write_run(output_root: Path, state_file: Path) -> Path:
    output_root = safe_root(output_root)
    state_file = safe_state_file(state_file)
    with exclusive_run_lock(state_file):
        return _write_run_locked(output_root, state_file)


def approve(artifact: Path, decision: str, actor: str, note: str | None) -> None:
    artifact = canonical_artifact(artifact)
    lock_path = artifact / "approval.lock"
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise PipelineError("another approval decision is already active") from exc
        validated = load_validated_artifact(artifact)
        approval_path = artifact / "approval.json"
        candidate = validated["candidate"]
        approval = validated["approval"]
        if approval.get("status") != "PENDING_HUMAN_APPROVAL":
            raise PipelineError("approval has already been decided")
        if sha256(candidate) != approval.get("candidate_sha256"):
            raise PipelineError("candidate changed after generation")
        approval.update({"status": "APPROVED" if decision == "approve" else "REJECTED", "decision": decision, "actor": actor, "decided_at": iso(utc_now()), "note": note, "external_publish_allowed": False})
        temp = approval_path.with_name(f".approval.json.{uuid.uuid4().hex}.tmp")
        try:
            temp.write_bytes(canonical_bytes(approval))
            temp.replace(approval_path)
        finally:
            temp.unlink(missing_ok=True)


def publish_check(artifact: Path) -> dict[str, object]:
    validated = load_validated_artifact(artifact)
    approval = validated["approval"]
    candidate = validated["candidate"]
    checks = {
        "human_approved": approval.get("status") == "APPROVED",
        "candidate_unchanged": sha256(candidate) == approval.get("candidate_sha256"),
        "approval_allows_external_publish": approval.get("external_publish_allowed") is True,
        "x_credential_present": bool(os.environ.get("X_BEARER_TOKEN")),
        "publisher_implemented": False,
    }
    return {"ready": all(checks.values()), "checks": checks, "external_request_made": False, "reason": "publisher intentionally remains disabled until an approved X account and explicit publish authorization are available"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--output-root", type=Path, default=DEFAULT_ARTIFACTS)
    run.add_argument("--state-file", type=Path, default=DEFAULT_STATE)
    approval = sub.add_parser("approve")
    approval.add_argument("--artifact", type=Path, required=True)
    approval.add_argument("--decision", choices=("approve", "reject"), required=True)
    approval.add_argument("--actor", required=True)
    approval.add_argument("--note")
    check = sub.add_parser("publish-check")
    check.add_argument("--artifact", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--artifact", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            target = write_run(args.output_root, args.state_file)
            print(json.dumps({"status": "READY_FOR_HUMAN_APPROVAL", "artifact": str(target), "candidate": str(target / "candidate.txt")}, indent=2))
        elif args.command == "approve":
            approve(args.artifact, args.decision, args.actor, args.note)
            print(json.dumps({"status": args.decision.upper(), "artifact": str(args.artifact)}))
        elif args.command == "publish-check":
            result = publish_check(args.artifact)
            print(json.dumps(result, indent=2))
            return 0 if result["ready"] else 3
        else:
            result = load_validated_artifact(args.artifact)
            print(json.dumps({"status": "VALID", "artifact": str(result["artifact"]), "checks": result["checks"]}, indent=2))
    except (PipelineError, OSError, ValueError, KeyError, json.JSONDecodeError, ET.ParseError) as exc:
        print(json.dumps({"status": "FAILED_CLOSED", "error_type": type(exc).__name__, "error": str(exc)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
