#!/usr/bin/env python3
"""Frank D1 existing local signed activity ledger, NOT complete chain history.

Only reads existing SQLite (mode=ro, query_only) and verified dated Git records.
Prints a private searchable HTML. No RPC, scanner, signal or production writes.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import quote
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
ATA_FILE = ROOT / "meme/evidence/frank-v2-ata-index-scope-correction-2026-10-11.json"
CLASSES = {"ACTIVE_TRADE", "PASSIVE_TRANSFER", "FAILED_TX", "ATA_CREATE",
           "UNKNOWN_NEEDS_REVIEW"}
SIDES = {"BUY", "ADD", "REENTRY", "SELL", "EXIT", "SELL_POSITION_UNRESOLVED"}
B58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,100}$")
MINT = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

def safe_id(v, pattern=B58):
    return v if isinstance(v, str) and pattern.fullmatch(v) else None

def fixed_class(v):
    return v if isinstance(v, str) and v in CLASSES else "OTHER_OR_UNKNOWN"

def connect(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("EXISTING_SOURCE_REQUIRED")
    db = sqlite3.connect("file:" + quote(str(p.resolve()), safe="/") + "?mode=ro",
                         uri=True, timeout=2, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    return db

def activity(path, as_of, days=1, max_rows=5000):
    if type(as_of) is not int or not 1_600_000_000 < as_of < 4_000_000_000:
        raise ValueError("INVALID_TIMESTAMP")
    if days not in (1, 7) or not 1 <= max_rows <= 5000:
        raise ValueError("BOUNDED_WINDOW_REQUIRED")
    after = as_of - 86400 * days
    db = connect(path)
    try:
        names = {x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"signatures", "trades"}.issubset(names):
            raise ValueError("SOURCE_TABLES_MISSING")
        sigs = db.execute(
            "SELECT wallet,signature,block_time,body FROM signatures "
            "WHERE person_id=? AND block_time BETWEEN ? AND ? "
            "ORDER BY block_time DESC,signature LIMIT ?",
            ("frank", after, as_of, max_rows+1)).fetchall()
        if len(sigs) > max_rows:
            raise ValueError("INDEX_WINDOW_TOO_LARGE_NOT_TRUNCATED")
        trades = db.execute(
            "SELECT t.wallet,t.signature,t.mint,t.side FROM trades t "
            "JOIN signatures s ON t.wallet=s.wallet AND t.signature=s.signature "
            "WHERE s.person_id=? AND s.block_time BETWEEN ? AND ?",
            ("frank", after, as_of)).fetchall()
        tmap, seen_trades = defaultdict(list), set()
        for t in trades:
            key = (t["wallet"], t["signature"], t["mint"], t["side"])
            if key in seen_trades:
                continue
            seen_trades.add(key)
            tmap[(t["wallet"], t["signature"])].append({
                "side": t["side"] if t["side"] in SIDES else "OTHER_SIDE",
                "mint": safe_id(t["mint"], MINT)})
        seen, rows = set(), []
        for s in sigs:
            key = (s["wallet"], s["signature"])
            if key in seen:
                raise ValueError("DUPLICATED_SIGNATURE")
            seen.add(key)
            try:
                body = json.loads(s["body"] or "{}")
                if not isinstance(body, dict):
                    body = {}
            except (TypeError, ValueError):
                body = {}
            cls = fixed_class(body.get("classification"))
            matched = tmap.get(key, [])
            status = ("CLASS_TRADE_MISMATCH" if matched and cls != "ACTIVE_TRADE"
                      else "ACTIVE_WITHOUT_TRADE_LEG" if not matched and cls == "ACTIVE_TRADE"
                      else "UNRESOLVED" if cls == "UNKNOWN_NEEDS_REVIEW"
                      else "MATCHED_OR_NOT_APPLICABLE")
            rows.append({"sig": safe_id(s["signature"]), "at": s["block_time"],
                         "class": cls, "trades": matched, "status": status})
        return {"as_of": as_of, "days": days, "rows": rows,
                "signatures": len(rows), "trade_legs": sum(len(x["trades"]) for x in rows),
                "categories": dict(sorted(Counter(x["class"] for x in rows).items())),
                "flags": dict(sorted(Counter(x["status"] for x in rows).items())),
                "full_chain_verified": False, "current_balance_verified": False}
    finally:
        db.close()

def dated_ata(path=ATA_FILE):
    evidence = json.loads(Path(path).read_text("utf-8"))
    if evidence.get("source_scope") != "DATED_READ_ONLY_ATA_VS_MAIN_WALLET_ACCOUNT_KEYS_NOT_FULL_CHAIN":
        raise ValueError("ATA_EVIDENCE_WRONG_SCOPE")
    if evidence.get("original_evidence_immutable") is not True or evidence.get("source_date_utc") != "2026-10-11":
        raise ValueError("ATA_EVIDENCE_NOT_FINAL")
    result = []
    fields = ("owner_index_missing_signatures", "missing_before_index_start",
              "missing_during_index_window", "inwindow_failed",
              "inwindow_success_unverified", "verified_extra_passive_receipts")
    for x in evidence.get("records", []):
        if not isinstance(x, dict) or not safe_id(x.get("mint"), MINT):
            raise ValueError("ATA_MINT_INVALID")
        values = []
        for key in fields:
            v = x.get(key)
            if type(v) is not int or not 0 <= v <= 1_000_000:
                raise ValueError("ATA_COUNT_INVALID")
            values.append(v)
        if values[0] != values[1] + values[2]:
            raise ValueError("ATA_INDEX_SCOPE_INCONSISTENT")
        result.append({"mint": x["mint"], "values": values})
    if len(result) != 2:
        raise ValueError("ATA_COHORT_CHANGED")
    return result

def render(report, ata):
    if report.get("full_chain_verified") is not False:
        raise ValueError("SCOPE_MUST_BE_LOCAL_ONLY")
    e = lambda s: escape(str(s), quote=True)
    body_rows = []
    for row in report["rows"]:
        sig = row["sig"]
        link = (f'<a href="https://solscan.io/tx/{e(sig)}" target="_blank" rel="noopener noreferrer">{e(sig[:10])}…</a>'
                if sig else "UNVERIFIED")
        at = (datetime.fromtimestamp(row["at"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
              if type(row["at"]) is int and 0 < row["at"] < 4102444800 else "UNVERIFIED")
        legs = []
        for leg in row["trades"]:
            mint = leg["mint"]
            dest = (f'<a href="https://solscan.io/token/{e(mint)}" target="_blank" rel="noopener noreferrer">{e(mint[:10])}…</a>'
                    if mint else "UNVERIFIED")
            legs.append(e(leg["side"]) + " " + dest)
        body_rows.append(f'<tr data-class="{e(row["class"])}"><td>{link}</td><td>{e(at)}</td>'
                         + f'<td>{e(row["class"])}</td><td>{e(row["status"])}</td>'
                         + f'<td>{"; ".join(legs) if legs else "—"}</td></tr>')
    gap_rows = "".join("<tr><td>" + e(x["mint"][:12]) + "…</td>"
                       + "".join("<td>" + str(n) + "</td>" for n in x["values"])
                       + "</tr>" for x in ata)
    summary = ", ".join(e(k) + ": " + str(v) for k, v in report["categories"].items())
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>Frank D1 本地钱包活动账本</title>
<style>body{{background:#0c1520;color:#dfe9f4;font:14px system-ui;margin:26px auto;max-width:1350px;padding:0 18px}}
a{{color:#91c4ff}}.notice{{border:1px solid #42526b;padding:14px;border-radius:8px;line-height:1.9}}
table{{border-collapse:collapse;width:100%}}th,td{{padding:9px;border-bottom:1px solid #344457;text-align:left}}
th{{background:#1a2635}}.scroll{{overflow:auto}}.controls{{display:flex;gap:12px;margin:15px 0}}
input,select{{padding:11px;background:#202e40;color:#fff;border:1px solid #44536b}}
input{{flex:1}}</style></head><body>
<h1>Frank D1 · 钱包活动事实账本（本地只读）</h1>
<div class="notice">时间窗口：最近 {report["days"]} 天；
本地索引签名 <strong>{report["signatures"]}</strong>；
已识别交易记录 <strong>{report["trade_legs"]}</strong>；
分类：{summary}。
<p>索引并非完整链上历史。被动转入、账户创建、失败交易不等于买入；待复核活动不是正式交易或 BUY。
本报告不提供当前余额、成本、PnL、实时 F01 资格或交易授权。</p></div>
<h2>实际已索引活动</h2><div class="controls">
<input id="search" placeholder="搜索交易分类、签名或代币">
<select id="type"><option value="ALL">全部</option>
<option value="ACTIVE_TRADE">主动交易</option><option value="PASSIVE_TRANSFER">被动活动</option>
<option value="UNKNOWN_NEEDS_REVIEW">待核实</option><option value="FAILED_TX">失败</option>
<option value="ATA_CREATE">账户创建</option><option value="OTHER_OR_UNKNOWN">其他</option></select>
</div><p>显示 <b id="shown">{report["signatures"]}</b> 条</p>
<div class="scroll"><table id="activity"><thead><tr><th>链上签名</th><th>UTC</th><th>来源分类</th>
<th>交易账本关联</th><th>确认的交易方向及代币</th></tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>
<h2>历史 ATA/主钱包签名范围差异（仅 2026-10-11 数据）</h2>
<p>主钱包 accountKeys 未出现的 ATA-only 交易不自动说明索引器故障；差异签名不等于转账或市场买入。
历史 J7/BPxx 案例来自仓库已修正证据，不能代替当前链上核验。</p>
<table><thead><tr><th>CA</th><th>范围差异</th><th>原索引开始前</th><th>索引期间</th><th>失败</th>
<th>成功但未核实</th><th>额外确认的被动收款</th></tr></thead><tbody>{gap_rows}</tbody></table>
<script>
const rows=Array.from(document.querySelectorAll("#activity tbody tr")),q=document.getElementById("search"),
k=document.getElementById("type");function update(){{let n=0;for(const r of rows){{
let ok=(k.value==="ALL"||r.dataset.class===k.value)&&r.textContent.toLowerCase().includes(q.value.trim().toLowerCase());
r.hidden=!ok;if(ok)n++;}}document.getElementById("shown").textContent=String(n);}}
q.addEventListener("input",update);k.addEventListener("change",update);
</script></body></html>'''

def publish(content, downloads):
    raw = content.encode("utf-8")
    if not 0 < len(raw) <= 5_000_000:
        raise ValueError("HTML_TOO_LARGE")
    downloads.mkdir(parents=True, exist_ok=True)
    dest = downloads / ("frank-d1-activity-" + datetime.now().strftime("%Y%m%d-%H%M%S")
                        + "-" + uuid.uuid4().hex[:8] + ".html")
    with tempfile.TemporaryDirectory(dir=downloads, prefix=".frank-d1-") as temp:
        source = Path(temp) / "activity.html"
        source.write_bytes(raw)
        os.link(source, dest)
    return dest

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--days", type=int, choices=(1,7), default=1)
    args = ap.parse_args(argv)
    try:
        evidence = activity(args.db, int(datetime.now(timezone.utc).timestamp()), args.days)
        out = publish(render(evidence, dated_ata()), Path.home() / "Downloads")
        print("FRANK_D1_ACTIVITY_READY=" + str(out))
        print("LOCAL_CLASS_COUNTS=" + json.dumps(evidence["categories"], sort_keys=True))
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(out)], check=False, timeout=8)
        return 0
    except (OSError, sqlite3.Error, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print("FRANK_D1_ACTIVITY_FAILED=" + type(exc).__name__, file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
