#!/usr/bin/env python3
"""D2 usable local HTML preview: dated verified 32-mint snapshot + current WATCH.

Read-only GET to existing Mac dashboard; reuse existing wallet_inventory logic.
Historical 2026-10-11 slot quantities are NEVER live holdings or USD valuations.
No production source/DB writes, Solana RPC, mail, orders or localhost server.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from html import escape
from http.client import HTTPConnection, HTTPException
from pathlib import Path
from urllib.parse import quote
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

from mission_agent.mission_control.wallet_inventory import reconcile_watchlist

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "meme/evidence/frank-v2-thirty-two-mint-finalized-2026-10-11.json"
MAX_BODY = 2_000_000
VALID_MINT = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
APPROVED_STATES = frozenset(("MODEL_OPEN", "NEEDS_INVENTORY_REVIEW",
    "HISTORICAL_EXIT", "WATCH_UNRESOLVED", "HISTORY_SELL_ONLY",
    "MODEL_STATE_ONLY", "PASSIVE_RECEIPT_ONLY", "OTHER_ACCOUNT_ACTIVITY"))
VALID_SNAPSHOT = frozenset(("NONZERO_AT_SLOT", "ZERO_AT_SLOT", "NOT_QUERIED_IN_SNAPSHOT"))
VALID_DISAGREEMENT = frozenset((
    "MODEL_CLOSED_WITH_RESIDUAL_BALANCE", "MODEL_UNKNOWN_WITH_POSITIVE_BALANCE",
    "MODEL_OPEN_WITH_ZERO_BALANCE", "MODEL_UNCERTAIN_WITH_POSITIVE_BALANCE",
))


def _port(home: Path) -> int:
    pointer = home / "Library/Application Support/FrankMeme/dashboard_port"
    if not pointer.is_file() or pointer.is_symlink() or pointer.stat().st_size > 8:
        raise RuntimeError("DASHBOARD_PORT_POINTER_UNAVAILABLE")
    raw = pointer.read_text("ascii").strip()
    if not raw.isascii() or not raw.isdecimal() or not 1024 <= int(raw) <= 65535:
        raise RuntimeError("DASHBOARD_PORT_INVALID")
    return int(raw)


def _watch(port: int) -> dict:
    conn = HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        conn.request("GET", "/api/frank-observed-watchlist",
                     headers={"Accept": "application/json", "Connection": "close"})
        res = conn.getresponse()
        if res.status != 200:
            raise RuntimeError("WATCHLIST_HTTP_NOT_200")
        if (res.getheader("Content-Type") or "").split(";", 1)[0].strip().lower() != "application/json":
            raise RuntimeError("WATCHLIST_NOT_JSON_MIME")
        size = res.getheader("Content-Length") or ""
        if not size.isascii() or not size.isdecimal() or not 0 < int(size) <= MAX_BODY:
            raise RuntimeError("WATCHLIST_SIZE_UNVERIFIED")
        body = res.read(int(size))
        if len(body) != int(size):
            raise RuntimeError("WATCHLIST_TRUNCATED")
        value = json.loads(body)
        if not isinstance(value, dict) or not isinstance(value.get("rows"), list):
            raise RuntimeError("WATCHLIST_SHAPE_UNVERIFIED")
        if value.get("status") in ("SOURCE_UNAVAILABLE", "UNAVAILABLE"):
            raise RuntimeError("WATCHLIST_SOURCE_UNAVAILABLE")
        return value
    except (OSError, ValueError, HTTPException, UnicodeError) as exc:
        raise RuntimeError("WATCHLIST_GET_FAILED") from exc
    finally:
        conn.close()


def _safe_mint(row: dict) -> str | None:
    mint = row.get("mint")
    return mint if isinstance(mint, str) and VALID_MINT.fullmatch(mint) else None


def _safe_state(raw, allowed: frozenset[str], unknown: str) -> str:
    return raw if isinstance(raw, str) and raw in allowed else unknown


def _ts(raw) -> str:
    try:
        if isinstance(raw, bool) or raw is None:
            return "未核实"
        t = float(raw)
        if not 0 < t < 4102444800:
            return "未核实"
        return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError, OverflowError):
        return "未核实"


def _amount(raw) -> str:
    # Bounded canonical decimal display from inventory.validate_record only.
    if not isinstance(raw, str) or not re.fullmatch(r"\d+(?:\.\d+)?", raw) or len(raw) > 120:
        return "未核实"
    return raw


def _html_cell(s) -> str:
    return escape(str(s), quote=True)


def render(report: dict, *, viewed_at: datetime | None = None) -> str:
    """Render a standalone filtered evidence table; all source strings escaped."""
    viewed_at = viewed_at or datetime.now(timezone.utc)
    if viewed_at.tzinfo is None:
        raise ValueError("DATE_MUST_BE_AWARE")
    if report.get("snapshot_status") != "DATED_POINT_IN_TIME_NOT_LIVE":
        raise ValueError("NO_VALID_DATED_SNAPSHOT")
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise ValueError("ROWS_MISSING")
    stamp = report.get("snapshot_date_bangkok")
    if not isinstance(stamp, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", stamp):
        raise ValueError("SNAPSHOT_DATE_INVALID")
    age = (viewed_at.date() - date.fromisoformat(stamp)).days
    if age < 0:
        raise ValueError("SNAPSHOT_FROM_FUTURE")
    html_rows = []
    matched = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        mint = _safe_mint(row)
        if mint is None:
            continue
        history = _safe_state(row.get("watch_state"), APPROVED_STATES, "UNRESOLVED")
        snapshot = _safe_state(row.get("snapshot_inventory_state"),
                               VALID_SNAPSHOT, "NOT_QUERIED_IN_SNAPSHOT")
        discrepancy = _safe_state(row.get("model_chain_disagreement"),
                                  VALID_DISAGREEMENT, "")
        if snapshot != "NOT_QUERIED_IN_SNAPSHOT":
            matched += 1
        historical_amount = (
            _amount(row.get("snapshot_token_quantity"))
            if snapshot in ("NONZERO_AT_SLOT", "ZERO_AT_SLOT") else "未核实")
        slot = row.get("snapshot_verified_slot")
        slot_text = str(slot) if type(slot) is int and slot > 0 else "未核实"
        source_link = "https://solscan.io/token/" + quote(mint, safe="")
        last_seen = _ts(row.get("last_signature_activity_time")
                        or row.get("last_event_time"))
        html_rows.append((mint, history, snapshot, historical_amount,
                          slot_text, discrepancy, last_seen, source_link))
    html_rows.sort(key=lambda x: (
        0 if x[2] == "NONZERO_AT_SLOT" else
        1 if x[5] else
        2 if x[2] == "ZERO_AT_SLOT" else 3, x[0]))
    stats = report.get("snapshot_reconciliation") or {}
    if type(stats.get("matched_mints")) is int and matched != stats["matched_mints"]:
        raise ValueError("MATCHED_MINT_COUNT_INCONSISTENT")
    table = "\n".join(
        "<tr data-state='" + _html_cell(r[1]) + "' data-snapshot='" +
        _html_cell(r[2]) + "' data-disagreement='" + _html_cell(bool(r[5])) +
        "'><td><a href='" + _html_cell(r[7]) +
        "' target='_blank' rel='noopener noreferrer'>" + _html_cell(r[0]) +
        "</a></td>" + "".join("<td>" + _html_cell(v) + "</td>"
                              for v in (r[1], r[2], r[3], r[4], r[5] or "—", r[6])) +
        "</tr>" for r in html_rows)
    note = ("这是独立只读预览，不是实时 Dashboard，也不提供交易建议。"
            "链上余额来自 " + stamp + " 已终结区块的 32 币抽样，距本次打开约 " +
            str(age) + " 天；各代币 slot 可能不同。"
            "未采样的代币均标记 NOT_QUERIED_IN_SNAPSHOT。"
            "余额非零仅说明当时持有数量，不代表今天仍持有、有流动性或价值超过 1 美元。"
            "成本、当前 USD 市值与 PnL 均未核实。")
    doc = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Frank V2 D2 · 历史持仓证据预览</title>
<style>
:root {color-scheme:dark} body{background:#0e131b;color:#e5eaf4;font:14px system-ui;margin:24px auto;max-width:1380px;padding:0 18px}
h1{font-size:23px} .note{padding:14px;border:1px solid #41506c;border-radius:8px;line-height:1.8;background:#182231}
.stats{display:flex;flex-wrap:wrap;gap:18px;margin:18px 0}.stats b{display:block;font-size:23px}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px} input,select{background:#192432;color:#fff;padding:10px;border:1px solid #435473;border-radius:7px}
input{min-width:260px;flex:1} .table{overflow-x:auto;border:1px solid #39475e;border-radius:8px}
table{width:100%;border-collapse:collapse;white-space:nowrap}td,th{padding:10px 13px;border-bottom:1px solid #283748;text-align:left}
tr:hover{background:#1c2937}th{background:#192432;position:sticky;top:0}a{color:#8bc3fa}
.caption{color:#a9b9ce;font-size:12px;line-height:1.7}
</style></head><body><h1>Frank V2 · D2 持仓证据对照（历史，只读）</h1>
<p class="note">__NOTE__</p>
<div class="stats"><div>本地观察记录<b id="total">__TOTAL__</b></div>
<div>样本核实币种<b>__MATCHED__</b></div><div>样本当时非零<b>__NONZERO__</b></div>
<div>样本当时为零<b>__ZERO__</b></div><div>没有这批余额证据<b>__UNQUERIED__</b></div>
<div>当前筛选显示<b id="visible">__VISIBLE__</b></div></div>
<div class="controls"><input id="search" placeholder="搜索公开代币 CA（完全本地过滤）">
<select id="filter"><option value="all">全部观察项目</option>
<option value="nonzero">历史样本非零</option><option value="zero">历史样本为零</option>
<option value="disagree">模型与历史样本矛盾</option>
<option value="unqueried">没有这批余额核验证据</option></select></div>
<div class="table"><table><thead><tr><th>CA / 打开 Solscan</th><th>观察状态（非链上证明）</th>
<th>历史样本状态</th><th>历史代币数量</th><th>历史 slot</th><th>模型/样本差异</th>
<th>最近本地活动</th></tr></thead><tbody>__ROWS__</tbody></table></div>
<p class="caption">仅来自本地 Frank 观察池 GET + Git 已有 2026-10-11 finalized 32 币证据；浏览器搜索/筛选不连接任何接口。
所有其他观察项目仍保留，没有样本 ≠ 余额为零。当前价格、PnL 与实际 F01 资格均未查询，也未授权交易。</p>
<script>
const all=Array.from(document.querySelectorAll("tbody tr"));
const search=document.getElementById("search"), filter=document.getElementById("filter");
function update() {
  const q=search.value.trim().toLowerCase(),mode=filter.value;let count=0;
  for(const row of all) {
    const valid=!q||row.cells[0].textContent.toLowerCase().includes(q);
    const sample=row.dataset.snapshot;
    const show=valid&&(mode==="all"||
      mode==="nonzero"&&sample==="NONZERO_AT_SLOT"||
      mode==="zero"&&sample==="ZERO_AT_SLOT"||
      mode==="disagree"&&row.dataset.disagreement==="True"||
      mode==="unqueried"&&sample==="NOT_QUERIED_IN_SNAPSHOT");
    row.hidden=!show;if(show)count++;
  }
  document.getElementById("visible").textContent=String(count);
}
search.addEventListener("input",update);filter.addEventListener("change",update);
</script></body></html>"""
    # Replace only self-generated safe placeholders, after HTML escaping.
    stats_count = lambda k: str(stats[k]) if type(stats.get(k)) is int and stats[k] >= 0 else "—"
    return (doc.replace("__NOTE__", _html_cell(note))
            .replace("__TOTAL__", str(len(html_rows)))
            .replace("__MATCHED__", str(matched))
            .replace("__NONZERO__", stats_count("nonzero_at_snapshot"))
            .replace("__ZERO__", stats_count("zero_at_snapshot"))
            .replace("__UNQUERIED__", stats_count("unresolved_without_snapshot"))
            .replace("__VISIBLE__", str(len(html_rows)))
            .replace("__ROWS__", table))


def generate(watch: dict, snapshot: dict, *, now: datetime | None = None) -> str:
    return render(reconcile_watchlist(watch, snapshot), viewed_at=now)


def main() -> int:
    home = Path.home()
    try:
        import signal as signals
        def _timeout(_, __): raise TimeoutError("D2_TOTAL_TIMEOUT")
        signals.signal(signals.SIGALRM, _timeout)
        signals.setitimer(signals.ITIMER_REAL, 15.0)
        try:
            evidence = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            report = _watch(_port(home))
            html = generate(report, evidence)
        finally:
            signals.setitimer(signals.ITIMER_REAL, 0.0)
        raw = html.encode("utf-8")
        if not 0 < len(raw) <= 3_000_000:
            raise RuntimeError("HTML_SIZE_OUT_OF_BOUND")
        downloads = home / "Downloads"
        downloads.mkdir(exist_ok=True, parents=True)
        target = downloads / (
            "frank-d2-dated-inventory-" + datetime.now().strftime("%Y%m%d-%H%M%S") +
            "-" + uuid4().hex[:8] + ".html")
        with tempfile.TemporaryDirectory(prefix=".frank-d2-", dir=downloads) as root:
            tmp = Path(root) / "preview.html"
            tmp.write_bytes(raw)
            os.link(tmp, target)
        print("FRANK_D2_PREVIEW_READY=" + str(target), flush=True)
        print("FRANK_D2_INVENTORY_SOURCE=DATED_2026_10_11_NOT_LIVE", flush=True)
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(target)], check=False, timeout=10)
        return 0
    except (RuntimeError, ValueError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        print("FRANK_D2_PREVIEW_FAILED=" + type(exc).__name__, file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
