"""Frank D2: purely offline projection of a PR60-replayed full owner receipt.

No RPC, SQLite, current/live assertions, USD NAV, Gmail, signals, trades, or
production IO. Trust the original pinned PR60 replay for wire provenance, then
cross-check the in-memory replay snapshot before displaying dated balances.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from html import escape
import json
from .person_registry import _solana_pubkey_32_bytes

FRANK_WALLET = "498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ"
PROGRAMS = (
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
)
CAPTURE_STATUS = "BOTH_PROGRAMS_OBSERVED_NON_ATOMIC"


class AtSlotSourceError(ValueError):
    """Invalid, contradictory, partial, or wrongly attributed replay source."""


def _require(condition, reason):
    if not condition:
        raise AtSlotSourceError(reason)


def _utc(value):
    _require(isinstance(value, str), "OBSERVATION_TIME_MISSING")
    try:
        when = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AtSlotSourceError("OBSERVATION_TIME_INVALID") from exc
    _require(when.tzinfo is not None, "OBSERVATION_TIME_WITHOUT_ZONE")
    return when.astimezone(timezone.utc)


def _fingerprint(snapshot):
    body = {key: value for key, value in snapshot.items() if key != "capture_sha256"}
    return sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=False).encode("utf-8")).hexdigest()


def _mint_key(mint):
    return isinstance(mint, str) and _solana_pubkey_32_bytes(mint)


def project_replayed_owner(snapshot, watch, *, target_mints=(),
                           as_of=None, max_visible=200, outsider_reserve=40):
    """Return a bounded preview and complete summary from a verified PR60 replay.

    A missing active token account is NOT treated as an observed zero. A local
    model OPEN/CLOSED or SELL is unrelated to balance-at-slot evidence. The
    source is fresh only AT ITS FINALIZED SLOTS, never a perpetual live read.
    """
    _require(isinstance(snapshot, dict), "REPLAY_SOURCE_MISSING")
    _require(snapshot.get("wallet") == FRANK_WALLET, "OWNER_MISMATCH")
    _require(snapshot.get("network") == "solana-mainnet", "NETWORK_MISMATCH")
    _require(snapshot.get("status") == CAPTURE_STATUS and
             snapshot.get("both_programs_observed") is True and
             snapshot.get("same_slot_atomic") is False and
             snapshot.get("missing") == [], "BOTH_PROGRAMS_REQUIRED")
    _require(isinstance(snapshot.get("capture_sha256"), str) and
             snapshot["capture_sha256"] == _fingerprint(snapshot),
             "REPLAY_CAPTURE_FINGERPRINT_MISMATCH")
    _require(type(max_visible) is int and 60 <= max_visible <= 500 and
             type(outsider_reserve) is int and 0 <= outsider_reserve <= max_visible - 32,
             "PREVIEW_BOUNDS_INVALID")
    observed_time = _utc(snapshot.get("observed_at_utc"))
    asof = as_of or datetime.now(timezone.utc)
    _require(isinstance(asof, datetime) and asof.tzinfo is not None,
             "AS_OF_TIME_WITHOUT_ZONE")
    age_seconds = (asof.astimezone(timezone.utc) - observed_time).total_seconds()
    _require(age_seconds >= -60, "SOURCE_TIMESTAMP_IN_FUTURE")
    age_seconds = max(0, int(age_seconds))
    coverage = snapshot.get("program_coverage")
    _require(isinstance(coverage, list) and len(coverage) == 2,
             "PROGRAM_COVERAGE_MISSING")
    seen_accounts, by_mint, slots, per_program = set(), {}, [], []
    for idx, program in enumerate(PROGRAMS):
        section = coverage[idx]
        _require(isinstance(section, dict) and
                 section.get("program_id") == program and
                 section.get("wallet") == FRANK_WALLET and
                 section.get("commitment") == "finalized" and
                 section.get("source") == "SOLANA_GET_TOKEN_ACCOUNTS_BY_OWNER",
                 "PROGRAM_PROVENANCE_INVALID")
        slot = section.get("slot")
        accounts = section.get("accounts")
        _require(type(slot) is int and slot > 0 and
                 isinstance(accounts, list) and len(accounts) <= 50000 and
                 section.get("account_count") == len(accounts),
                 "PROGRAM_ACCOUNTS_OR_SLOT_INVALID")
        slots.append(slot)
        per_program.append({"program_id": program, "slot": slot,
                            "account_count": len(accounts)})
        for row in accounts:
            _require(isinstance(row, dict), "ACCOUNT_ROW_INVALID")
            account = row.get("token_account")
            mint = row.get("mint")
            raw = row.get("raw_amount")
            decimals = row.get("decimals")
            _require(_mint_key(account) and _mint_key(mint) and
                     row.get("owner") == FRANK_WALLET and
                     row.get("program_id") == program and row.get("slot") == slot and
                     row.get("state") in ("initialized", "frozen"),
                     "TOKEN_ACCOUNT_PROVENANCE_INVALID")
            _require(isinstance(raw, str) and raw.isascii() and raw.isdecimal() and
                     type(decimals) is int and 0 <= decimals <= 18,
                     "TOKEN_ACCOUNT_QUANTITY_INVALID")
            _require(account not in seen_accounts, "DUPLICATE_OWNER_TOKEN_ACCOUNT")
            seen_accounts.add(account)
            item = by_mint.setdefault(mint, {"raw": 0, "decimals": decimals,
                                            "account_count": 0, "programs": set(),
                                            "slots": set()})
            _require(item["decimals"] == decimals, "MINT_DECIMALS_CONFLICT")
            item["raw"] += int(raw)
            item["account_count"] += 1
            item["programs"].add(program)
            item["slots"].add(slot)
    _require(slots[0] <= slots[1] and
             snapshot.get("slot_min") == min(slots) and
             snapshot.get("slot_max") == max(slots),
             "SOURCE_SLOTS_CONFLICT")
    _require(snapshot.get("account_count") == len(seen_accounts) and
             snapshot.get("mint_count_observed") == len(by_mint),
             "SOURCE_TOTAL_COUNT_CONFLICT")
    declared = snapshot.get("mints")
    _require(isinstance(declared, list) and len(declared) == len(by_mint),
             "MINT_PROJECTION_MISMATCH")
    declared_seen = set()
    for row in declared:
        _require(isinstance(row, dict), "MINT_PROJECTION_INVALID")
        mint = row.get("mint")
        item = by_mint.get(mint)
        _require(item is not None and mint not in declared_seen and
                 row.get("raw_amount_observed_sum") == str(item["raw"]) and
                 row.get("decimals") == item["decimals"] and
                 row.get("slot_min") == min(item["slots"]) and
                 row.get("slot_max") == max(item["slots"]) and
                 len(row.get("token_accounts", [])) == item["account_count"],
                 "MINT_SOURCE_RECONCILIATION_FAILED")
        declared_seen.add(mint)
    _require(isinstance(watch, dict) and isinstance(watch.get("rows"), list),
             "WATCHLIST_SOURCE_INVALID")
    watch_by_mint = {}
    for row in watch["rows"]:
        _require(isinstance(row, dict) and _mint_key(row.get("mint")),
                 "WATCHLIST_MINT_INVALID")
        _require(row["mint"] not in watch_by_mint, "WATCHLIST_MINT_DUPLICATED")
        watch_by_mint[row["mint"]] = row
    _require(isinstance(target_mints, (list, tuple, set)) and
             len(target_mints) <= 256 and
             all(_mint_key(x) for x in target_mints), "TARGET_MINT_SET_INVALID")
    targets = set(target_mints)

    def preview_row(mint):
        item = by_mint.get(mint)
        local = watch_by_mint.get(mint, {})
        raw = item["raw"] if item else None
        return {
            "mint": mint,
            "target": mint in targets,
            "in_local_watchlist": mint in watch_by_mint,
            "at_slot_state": ("NO_ACTIVE_OWNER_TOKEN_ACCOUNT_OBSERVED_AT_SLOTS" if
                              item is None else "NONZERO_AT_SLOT" if raw else "ZERO_AT_SLOT"),
            "token_quantity_at_slots": (str(Decimal(raw) /
                                            (Decimal(10) ** item["decimals"]))
                                        if item else None),
            "raw_amount": str(raw) if item else None,
            "decimals": item["decimals"] if item else None,
            "token_account_count": item["account_count"] if item else 0,
            "program_ids": sorted(item["programs"]) if item else [],
            "finalized_slots": sorted(item["slots"]) if item else [],
            "model_state": str(local.get("local_model_state") or "NOT_IN_WATCHLIST"),
            "last_signed_side": str(local.get("last_event_side") or "UNRESOLVED"),
            "usd_value": None, "pnl_usd": None,
            "current_chain_balance_verified": False,
        }

    ordered_target = sorted(targets)
    ordered_watch = sorted((m for m in watch_by_mint if m not in targets),
                           key=lambda m: (by_mint.get(m, {}).get("raw", 0) == 0, m))
    outsiders = sorted((m for m, item in by_mint.items()
                       if m not in watch_by_mint and m not in targets and item["raw"] > 0))
    retained = ordered_target[:max_visible]
    outsider_limit = min(outsider_reserve, len(outsiders), max_visible - len(retained))
    retained += ordered_watch[:max_visible - len(retained) - outsider_limit]
    retained += outsiders[:max_visible - len(retained)]
    selected = [preview_row(m) for m in retained]
    _require(len(selected) <= max_visible, "PREVIEW_OVERFLOW")
    return {
        "status": "OFFLINE_VERIFIED_OWNER_BALANCES_AT_FINALIZED_SLOTS",
        "provenance": "PR60_FULL_WIRE_BYTES_OFFLINE_REPLAY",
        "observed_at_utc": observed_time.isoformat(),
        "observed_at_bangkok": observed_time.astimezone(
            __import__("zoneinfo").ZoneInfo("Asia/Bangkok")).isoformat(),
        "age_seconds_at_render": age_seconds,
        "source_capture_sha256": snapshot["capture_sha256"],
        "wallet": FRANK_WALLET,
        "program_coverage": per_program,
        "same_slot_atomic": False,
        "current_chain_balance_verified": False,
        "chain_history_complete": False,
        "usd_value_verified": False,
        "account_count": len(seen_accounts),
        "mint_count": len(by_mint),
        "nonzero_mint_count": sum(item["raw"] > 0 for item in by_mint.values()),
        "local_watchlist_mints": len(watch_by_mint),
        "local_watchlist_with_active_accounts": sum(m in by_mint for m in watch_by_mint),
        "local_watchlist_without_active_accounts": sum(m not in by_mint for m in watch_by_mint),
        "outside_watchlist_mints": sum(m not in watch_by_mint for m in by_mint),
        "target_mints_requested": len(targets),
        "target_mints_with_active_accounts": sum(m in by_mint for m in targets),
        "preview_limit": max_visible,
        "preview_rows": selected,
        "preview_is_bounded": True,
    }


def render_offline_html(projection):
    """Self-contained, searchable local preview; no external scripts or URLs."""
    _require(projection.get("status") ==
             "OFFLINE_VERIFIED_OWNER_BALANCES_AT_FINALIZED_SLOTS",
             "PREVIEW_REQUIRES_VERIFIED_PROJECTED_SOURCE")
    def fmt(value):
        return escape(str(value), quote=True)
    rows = []
    for row in projection["preview_rows"]:
        state = row["at_slot_state"]
        rows.append(
            "<tr><td><code>" + fmt(row["mint"]) + "</code></td><td>" +
            fmt(state) + "</td><td>" +
            fmt(row["token_quantity_at_slots"] if row["token_quantity_at_slots"] is not None else "未观察到账户") +
            "</td><td>" + fmt(row["token_account_count"]) + "</td><td>" +
            fmt(",".join(map(str, row["finalized_slots"]))) + "</td><td>" +
            fmt(row["model_state"]) + "</td><td>" + fmt(row["last_signed_side"]) +
            "</td><td>" + ("目标" if row["target"] else "观察池" if row["in_local_watchlist"] else "池外") +
            "</td></tr>"
        )
    rows_html = "".join(rows)
    slots_html = " / ".join(str(p["slot"]) + " (" + str(p["account_count"]) +
                            " accounts)" for p in projection["program_coverage"])
    html = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; form-action 'none'">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Frank D2 本地余额证据预览</title>
<style>body{font:14px system-ui,Arial;margin:24px;background:#101820;color:#e9eff6}
header{max-width:1100px;margin:auto}main{max-width:1100px;margin:auto}
h1{font-size:24px}.small{color:#bcc8d3}input{width:100%;box-sizing:border-box;padding:12px;margin:15px 0;background:#243240;color:white;border:1px solid #6a7e8f;border-radius:6px}
table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:9px;border-bottom:1px solid #30424d;text-align:left;word-break:break-all}th{position:sticky;top:0;background:#243240}
code{font-family:monospace}td:first-child{min-width:170px}details{margin:16px 0}.scroll{overflow:auto;max-height:65vh}
</style></head><body><header><h1>Frank D2 · 已核验历史点位余额</h1>
<p>仅本地、无网络、无报价、无交易。数据不是自动更新的实时仓位；不同 Program 的 slot 不是原子快照。</p>
<p class="small">证据采集 UTC：OBSERVED_UTC · 曼谷：OBSERVED_BKK · 渲染时已过去 AGE 秒</p>
<p class="small">SLOTS</p><p>账户 ACCOUNTS · Mint MINTS · 观察到非零 Mint NONZERO · 观察池外 Mint OUTSIDERS</p>
<p class="small">仅显示最多 LIMIT 行，搜索只覆盖本地已展示子集；完整私有账户数据未嵌入网页。零余额只代表指定 slot 观察到的账户为零；不存在账户不等于零。</p></header>
<main><input id="search" aria-label="搜索 Mint 或状态" placeholder="筛选本页 Mint、状态、模型">
<div class="scroll"><table><thead><tr><th>Mint</th><th>slot 状态</th><th>代币数量</th><th>账户数</th><th>slot</th><th>历史模型</th><th>最后交易方向</th><th>来源</th></tr></thead><tbody id="rows">ROWS</tbody></table></div>
<p class="small">所有市值、真实成本、盈亏和账户完整交易历史：未核实。历史模型信号不是当前买入建议。</p></main>
<script>document.getElementById('search').addEventListener('input',function(){var q=this.value.trim().toLowerCase();document.querySelectorAll('#rows tr').forEach(function(r){r.hidden=!r.textContent.toLowerCase().includes(q);});});</script>
</body></html>"""
    changes = {
        "OBSERVED_UTC": fmt(projection["observed_at_utc"]),
        "OBSERVED_BKK": fmt(projection["observed_at_bangkok"]),
        "AGE": fmt(projection["age_seconds_at_render"]),
        "SLOTS": fmt(slots_html),
        "ACCOUNTS": fmt(projection["account_count"]),
        "MINTS": fmt(projection["mint_count"]),
        "NONZERO": fmt(projection["nonzero_mint_count"]),
        "OUTSIDERS": fmt(projection["outside_watchlist_mints"]),
        "LIMIT": fmt(projection["preview_limit"]),
        "ROWS": rows_html,
    }
    # Replacement is exact on the uppercase template sentinels only.
    for key, value in changes.items():
        html = html.replace(key, value)
    return html
