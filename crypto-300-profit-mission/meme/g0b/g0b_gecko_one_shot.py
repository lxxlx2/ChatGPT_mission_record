"""2026-10-28 approved, free, one-time G0-B historical price feasibility pilot.

Never imports local-agent, signs a transaction, contacts production, or writes
protected data. No automatic schedule. Only GeckoTerminal public GET with a
total *attempt* ceiling of 50 and a strictly serialized >=12.5s spacing.
Default execution is OFF; GitHub's explicit one-shot workflow supplies --execute.
This is in-sample proxy feasibility, NOT backtested executable returns.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import build_opener, HTTPRedirectHandler, Request

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "evidence/frank-trade-coverage-sol-usdt-complex-2026-10-04.json"
PINNED_BLOB_SHA1 = "a31a2bbcd1fe7c70951152f2a23edca6c934dc40"
HOST = "https://api.geckoterminal.com"
PREFIX = HOST + "/api/v2"
MAX_GET = 50
MIN_SPACING_SECONDS = 12.5
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
WSOL = "So11111111111111111111111111111111111111112"
DELAYS = (30, 120, 300, 900, 3600)
HORIZON = 86400


class StopPilot(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        return None


def utc(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")


def load_manifest():
    raw = STUDY.read_bytes()
    calc = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if calc != PINNED_BLOB_SHA1:
        raise ValueError("PINNED_STUDY_GIT_BLOB_MISMATCH")
    study = json.loads(raw)
    signals = study["models"]["M3"]["signals"]
    if len(signals) != 32:
        raise ValueError("SIGNAL_COUNT_DRIFT")
    episode = {}
    for signal in signals:
        key = signal["episode_id"]
        kind = signal["signal_type"]
        if kind not in ("FRANK_ACCUMULATION_SIGNAL", "FRANK_MULTIPLE_SIGNAL"):
            raise ValueError("UNKNOWN_SIGNAL_TYPE")
        row = episode.setdefault(key, {
            "episode_id": key, "mint": signal["mint"],
            "signal_time": int(signal["triggered_at"]), "kinds": set()})
        if row["mint"] != signal["mint"]:
            raise ValueError("EPISODE_MINT_DRIFT")
        row["signal_time"] = min(row["signal_time"], int(signal["triggered_at"]))
        row["kinds"].add(kind)
    if len(episode) != 22 or len({r["mint"] for r in episode.values()}) != 18:
        raise ValueError("EPISODE_POPULATION_DRIFT")
    ordered = sorted(episode.values(), key=lambda r: (r["signal_time"], r["episode_id"]))
    mult = [r for r in ordered if "FRANK_MULTIPLE_SIGNAL" in r["kinds"]][:4]
    acc = [r for r in ordered if "FRANK_MULTIPLE_SIGNAL" not in r["kinds"]][:4]
    recovered = sorted((
        c for c in study["COMPLEX"]["cases"]
        if c.get("shadow_trade", {}).get("direction") == "BUY"
        and len(c.get("shadow_episode_ids") or []) == 1
        and c["shadow_episode_ids"][0] not in episode
    ), key=lambda c: (int(c["at"]), c["signature"]))
    controls = recovered[:4]
    if len(mult) != 4 or len(acc) != 4 or len(controls) != 4:
        raise ValueError("PREDECLARED_COHORT_NOT_AVAILABLE")
    rows = []
    for kind, group, attr in (("MULT", mult, "signal_time"), ("ACC_ONLY", acc, "signal_time")):
        for i, s in enumerate(group, 1):
            rows.append({"id": ("M" if kind == "MULT" else "A") + str(i),
                "kind": kind, "episode_id": s["episode_id"], "mint": s["mint"],
                "t0": s[attr], "t0_utc": utc(s[attr]),
                "t0_basis": "FIRST_FROZEN_ACC_OR_MULT_SIGNAL_T0"})
    for i, c in enumerate(controls, 1):
        t0 = int(c["at"])
        rows.append({"id": "C" + str(i), "kind": "RECOVERED_BUY_NO_SIGNAL_CONTROL",
            "episode_id": c["shadow_episode_ids"][0],
            "mint": c["shadow_trade"]["mint"], "t0": t0, "t0_utc": utc(t0),
            "t0_basis": "RECONSTRUCTED_ACTIVE_BUY_EVENT_HYPOTHETICAL_CONTROL"})
    if len(rows) != 12 or len({r["mint"] for r in rows}) != 12:
        raise ValueError("MINT_DUPLICATE_OR_WRONG_COUNT")
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return rows, digest


class PublicGet:
    def __init__(self, max_calls=MAX_GET):
        if not (1 <= max_calls <= MAX_GET):
            raise ValueError("INVALID_HTTP_BUDGET")
        self.max_calls = max_calls
        self.attempts = []
        self.last_at = None
        self.opener = build_opener(NoRedirect)

    def get(self, path, query=None):
        if not path.startswith("/networks/solana/"):
            raise StopPilot("UNAPPROVED_ENDPOINT")
        url = PREFIX + path + (("?" + urlencode(query)) if query else "")
        if len(self.attempts) >= self.max_calls:
            raise StopPilot("HTTP_ATTEMPTS_CAP_REACHED")
        if self.last_at is not None:
            pause = self.last_at + MIN_SPACING_SECONDS - time.monotonic()
            if pause > 0:
                time.sleep(pause)
        self.last_at = time.monotonic()
        record = {"sequence": len(self.attempts) + 1, "url": url, "status": None}
        self.attempts.append(record)  # reserve the attempt BEFORE network
        request = Request(url, headers={
            "Accept": "application/json;version=20230203",
            "User-Agent": "frank-g0b-free-one-shot-research/1.0",
        }, method="GET")
        try:
            with self.opener.open(request, timeout=22) as response:
                if response.geturl() != url:
                    raise StopPilot("UNEXPECTED_REDIRECT")
                data = response.read(2_000_001)
                record["status"] = response.status
                if len(data) > 2_000_000:
                    raise StopPilot("RESPONSE_TOO_LARGE")
                record["bytes"] = len(data)
                record["sha256"] = hashlib.sha256(data).hexdigest()
                payload = json.loads(data)
                if not isinstance(payload, dict):
                    raise StopPilot("NON_OBJECT_JSON")
                return payload
        except HTTPError as exc:
            record["status"] = exc.code
            if exc.code == 429:
                raise StopPilot("HTTP_429_STOP_NO_RETRY") from exc
            if exc.code in (401, 402, 403) or exc.code in (301, 302, 307, 308):
                raise StopPilot("AUTH_OR_REDIRECT_NOT_ALLOWED") from exc
            if exc.code >= 500:
                raise StopPilot("UPSTREAM_SERVER_FAILURE") from exc
            return None
        except (URLError, TimeoutError, OSError) as exc:
            record["status"] = "TRANSPORT_FAILURE"
            raise StopPilot("NETWORK_FAILURE_NO_RETRY") from exc
        except (ValueError, UnicodeError) as exc:
            record["status"] = "INVALID_JSON"
            raise StopPilot("PROVIDER_DATA_FORMAT_ERROR") from exc


def parse_pool_created(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.timestamp() if dt.tzinfo else None
    except ValueError:
        return None


def select_pool(data, mint, t0):
    """Deterministic oldest *currently returned*, existing-at-T0 pool.

    Cannot reconstruct pools omitted by the present-day top-pools ranking.
    This cohort is never promoted to unbiased historic liquidity.
    """
    eligible = []
    for pool in data.get("data", []):
        if not isinstance(pool, dict):
            continue
        att = pool.get("attributes") or {}
        rel = pool.get("relationships") or {}
        base = ((rel.get("base_token") or {}).get("data") or {}).get("id") or ""
        quote = ((rel.get("quote_token") or {}).get("data") or {}).get("id") or ""
        if not isinstance(base, str) or not isinstance(quote, str):
            continue
        base_mint = base.removeprefix("solana_")
        quote_mint = quote.removeprefix("solana_")
        if base_mint == mint and quote_mint in (USDC, WSOL):
            side = "base"
        elif quote_mint == mint and base_mint in (USDC, WSOL):
            side = "quote"
        else:
            continue
        created = parse_pool_created(att.get("pool_created_at"))
        if created is None or created > t0:
            continue
        ident = str(pool.get("id") or "")
        addr = (att.get("address") or ident.removeprefix("solana_"))
        if not isinstance(addr, str) or len(addr) < 32:
            continue
        eligible.append({
            "address": addr, "side": side, "created_at": att["pool_created_at"],
            "quote_mint": quote_mint if side == "base" else base_mint,
            "present_day_selection_bias": True})
    eligible.sort(key=lambda x: (x["created_at"], x["address"]))
    return eligible[0] if eligible else None


def extract_bars(doc):
    obj = (doc.get("data") or {}).get("attributes") or {}
    raw = obj.get("ohlcv_list") or []
    seen = set()
    bars = []
    for v in raw:
        if not isinstance(v, list) or len(v) < 6:
            continue
        try:
            stamp = int(v[0])
            close = float(v[4])
            volume = float(v[5])
        except (TypeError, ValueError, OverflowError):
            continue
        if (stamp in seen or not math.isfinite(close) or close <= 0
                or not math.isfinite(volume) or volume < 0):
            continue
        seen.add(stamp)
        bars.append({"t": stamp, "c": close, "v": volume,
                     "o": v[1], "h": v[2], "l": v[3]})
    return sorted(bars, key=lambda x: x["t"])


def close_proxy(rows, target):
    eligible = [b for b in rows if target <= b["t"] <= target + 180 and b["v"] > 0]
    if not eligible:
        return None
    bar = eligible[0]
    return {"candle_start": bar["t"], "close_usd": bar["c"],
            "volume_usd": bar["v"],
            "price_known_no_earlier_than": bar["t"] + 60,
            "lookahead_from_target_seconds": bar["t"] + 60 - target}


def run(execute=False, max_http=50, out_dir=None):
    selection, locked_hash = load_manifest()
    results = {
        "status": "SELECTION_LOCKED_OFFLINE",
        "study_git_blob": PINNED_BLOB_SHA1,
        "selection_sha256": locked_hash,
        "selection_rule": "FIRST_4_CHRONOLOGICAL_MULT_EPISODES_FIRST_SIGNAL_T0;FIRST_4_CHRONOLOGICAL_ACC_ONLY;FIRST_4_CHRONOLOGICAL_COMPLEX_RECOVERED_BUY_NON_SIGNAL",
        "notes": [
            "M3 is in-sample; no strategy GO, no verified executable followers.",
            "Control cases are biased subset of reconstructed UNKNOWN trades, not representative of 166 non-signal episodes.",
            "Token/pool discovery uses present-day ranked first page and oldest pool created before T0; survivorship persists.",
            "Candle close is known after its 1-minute interval; not a timestamp-exact or executable fill.",
            "Missing/mismatched tokens and absent liquidity are retained, not silently replaced.",
        ],
        "selection": selection,
        "http_max": max_http,
        "http_spacing_min_seconds": MIN_SPACING_SECONDS,
        "http_attempts": [],
        "cases": [],
        "provider_responses": [],
    }
    transport = PublicGet(max_http)
    try:
        if not execute:
            return results
        results["status"] = "REQUESTS_STARTED"
        for item in selection:
            entry = {"id": item["id"], "kind": item["kind"], "mint": item["mint"],
                     "t0": item["t0"], "state": "NO_POOL_PROOF",
                     "delays": {}, "pool": None}
            results["cases"].append(entry)
            doc = transport.get("/networks/solana/tokens/" + item["mint"] + "/pools",
                                {"page": 1})
            if doc is None:
                entry["state"] = "POOL_DISCOVERY_HTTP_NOT_FOUND"
                continue
            pool = select_pool(doc, item["mint"], item["t0"])
            if pool is None:
                entry["state"] = "NO_ELIGIBLE_HISTORIC_POOL_ON_CURRENT_FIRST_PAGE"
                continue
            entry["pool"] = pool
            url = ("/networks/solana/pools/" + pool["address"] + "/ohlcv/minute")
            opts = {"aggregate": 1, "currency": "usd", "token": pool["side"],
                    "include_empty_intervals": "false"}
            # First time window encloses T0 through T0+3600s; exit is fixed T0+24h.
            entry_doc = transport.get(url, {**opts,
                "before_timestamp": item["t0"] + 75 * 60, "limit": 120})
            if entry_doc is None:
                entry["state"] = "ENTRY_OHLCV_HTTP_NOT_FOUND"
                continue
            exit_doc = transport.get(url, {**opts,
                "before_timestamp": item["t0"] + HORIZON + 6 * 60, "limit": 30})
            if exit_doc is None:
                entry["state"] = "EXIT_OHLCV_HTTP_NOT_FOUND"
                continue
            entry_bars = extract_bars(entry_doc)
            exit_bars = extract_bars(exit_doc)
            results["provider_responses"].append({"id": item["id"],
                "entry_ohlcv_raw": entry_doc, "exit_ohlcv_raw": exit_doc})
            entry["entry_bars"] = len(entry_bars)
            entry["exit_bars"] = len(exit_bars)
            exit_target = item["t0"] + HORIZON
            exit_px = close_proxy(exit_bars, exit_target)
            for delay in DELAYS:
                entry_px = close_proxy(entry_bars, item["t0"] + delay)
                observation = {
                    "delay_seconds": delay, "entry": entry_px, "exit": exit_px,
                    "gross_candle_close_proxy_pct": None,
                    "illustrative_2pct_roundtrip_cost_proxy_pct": None,
                }
                if entry_px and exit_px:
                    ratio = exit_px["close_usd"] / entry_px["close_usd"]
                    observation["gross_candle_close_proxy_pct"] = round((ratio - 1) * 100, 6)
                    observation["illustrative_2pct_roundtrip_cost_proxy_pct"] = round((ratio * 0.98 - 1) * 100, 6)
                entry["delays"][str(delay)] = observation
            entry["state"] = ("COARSE_PRICE_PROXY_PARTIAL" if any(
                v["gross_candle_close_proxy_pct"] is None for v in entry["delays"].values())
                else "COARSE_PRICE_PROXY_FIVE_LAGS")
        results["status"] = "ALL_PREDECLARED_CASES_VISITED"
    except StopPilot as exc:
        results["status"] = "HALTED_PARTIAL"
        results["stop_reason"] = str(exc)
    except (ValueError, KeyError, TypeError) as exc:
        results["status"] = "HALTED_PARTIAL"
        results["stop_reason"] = "UNEXPECTED_PROVIDER_SCHEMA_OR_LOCAL_INPUT"
        results["failure_type"] = type(exc).__name__
    finally:
        results["http_attempts"] = transport.attempts
        results["http_used"] = len(transport.attempts)
        if results["http_used"] > MAX_GET:
            raise AssertionError("HTTP_BUDGET_VIOLATION")
        eligible = Counter(x["kind"] for x in results["cases"]
            if x["state"] == "COARSE_PRICE_PROXY_FIVE_LAGS")
        attempted = Counter(x["kind"] for x in results["cases"])
        results["summary"] = {
            "intended_episodes": len(selection), "attempted_episodes": dict(attempted),
            "complete_five_lag_proxy_episodes": dict(eligible),
            "states": dict(Counter(x["state"] for x in results["cases"])),
            "total_provider_get_attempts": len(transport.attempts),
            "real_executable_quotes_verified": 0, "strategy_verdict": "NEED_MORE_DATA",
            "pilot_basis": "IN_SAMPLE_FEASIBILITY_ONLY_NO_REAL_EXECUTION_PROOF",
        }
        if out_dir is not None:
            dest = Path(out_dir)
            dest.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(results, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)
            (dest / "g0b_public_receipts.json").write_text(payload, encoding="utf-8")
        print("G0B_RESEARCH_SUMMARY_JSON:", json.dumps({
            "status": results["status"], "study_git_blob": PINNED_BLOB_SHA1,
            "selection_sha256": locked_hash, "summary": results["summary"],
            "stop_reason": results.get("stop_reason"),
        }, sort_keys=True))
        for row in results["cases"]:
            print("G0B_EPISODE_JSON:", json.dumps({
                "id": row["id"], "kind": row["kind"], "mint": row["mint"],
                "state": row["state"], "pool": row["pool"],
                "proxy_gross_pct": {k: v["gross_candle_close_proxy_pct"]
                    for k, v in row["delays"].items()},
            }, sort_keys=True))
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true",
                        help="Run the explicitly user-authorized one-shot GeckoTerminal GET requests.")
    parser.add_argument("--max-http", type=int, default=MAX_GET)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()
    run(args.execute, args.max_http, args.out_dir)


if __name__ == "__main__":
    main()
