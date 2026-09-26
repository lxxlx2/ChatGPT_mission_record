# /// script
# requires-python = ">=3.12"
# dependencies = ["cryptography>=42"]
# ///

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from close_call_fleet import (
    FINAL_TIME_UTC,
    LOCK_TIME_UTC,
    board_rows,
    fresh_price,
    latest_payload,
    load_state,
    local_board_matches,
)


def _row_fields(row: dict) -> tuple[str | None, Decimal | None]:
    raw = row.get("raw")
    if isinstance(raw, list) and len(raw) >= 2:
        did = raw[0] if isinstance(raw[0], str) else None
        try:
            score = Decimal(str(raw[1]))
        except Exception:
            score = None
        return did, score

    did = row.get("key") or row.get("did") or row.get("owner")
    score_raw = row.get("score") or row.get("pnl")
    try:
        score = Decimal(str(score_raw)) if score_raw is not None else None
    except Exception:
        score = None
    return did if isinstance(did, str) else None, score


def _short_did(did: str | None) -> str:
    if not did:
        return "-"
    return did[:16] + "..." + did[-8:]


def snapshot() -> dict:
    state = load_state()
    pr = fresh_price(max_age=10**9)
    pnl = latest_payload("d-close1-pnl", "pnl")
    positions = latest_payload("d-close1-positions", "positions")
    rows = board_rows(pnl)

    did_to_label = {item["did"]: label for label, item in state["keys"].items()}
    board = []
    first_rank_for_score: dict[str, int] = {}
    for index, row in enumerate(rows, 1):
        did, score = _row_fields(row)
        score_text = str(score) if score is not None else None
        if score_text is not None and score_text not in first_rank_for_score:
            first_rank_for_score[score_text] = index
        rank = first_rank_for_score.get(score_text, index)
        board.append({
            "index": index,
            "rank": rank,
            "did": did,
            "did_short": _short_did(did),
            "score": score_text,
            "label": did_to_label.get(did),
            "ours": did in did_to_label,
            "prize_zone": rank <= 3,
        })

    ours = [row for row in board if row["ours"]]
    ours.sort(key=lambda x: (x["rank"], x["index"]))

    static_done = sorted(state.get("static", {}).keys())
    bracket = state.get("bracket") or {}

    mark = None
    if isinstance(pnl, dict) and pnl.get("mark") is not None:
        try:
            mark = Decimal(str(pnl["mark"]))
        except Exception:
            pass

    gross_edges = []
    if mark is not None:
        for k, rec in sorted(state.get("static", {}).items()):
            try:
                px = Decimal(str(rec["px"]))
                qty = Decimal(str(rec["qty"]))
                edge = abs(mark - px) * qty
                base_fee = Decimal("0.01") * qty * px
                gross_edges.append({
                    "name": f"T{k}",
                    "edge": edge,
                    "entry": px,
                    "base_fee": base_fee,
                    "estimated_score": edge - base_fee,
                })
            except Exception:
                pass
        if int(bracket.get("round", 0) or 0) == 1:
            pairs = bracket.get("pairs") or []
            if pairs:
                try:
                    px = Decimal(str(pairs[0]["px"]))
                    qty = Decimal(str(pairs[0]["qty"]))
                    edge = abs(mark - px) * qty
                    base_fee = Decimal("0.01") * qty * px
                    gross_edges.append({
                        "name": "BR-R1",
                        "edge": edge,
                        "entry": px,
                        "base_fee": base_fee,
                        "estimated_score": edge - base_fee,
                    })
                except Exception:
                    pass

    gross_edges.sort(key=lambda x: x["estimated_score"], reverse=True)
    best_edge = gross_edges[0] if gross_edges else None

    now = datetime.now(timezone.utc)
    if now < LOCK_TIME_UTC:
        phase = "TRADING"
    elif now < FINAL_TIME_UTC:
        phase = "LOCKED_WAITING_FINAL"
    else:
        phase = "FINAL"

    threshold = board[-1]["score"] if board else None
    leader = board[0]["score"] if board else None
    prize_rows = [row for row in board if row["prize_zone"]]
    prize_cutoff = prize_rows[-1]["score"] if prize_rows else None
    prize_visible_wallets = len(prize_rows)

    submitted_wallets = len(static_done) * 2
    if int(bracket.get("round", 0) or 0) >= 1:
        submitted_wallets += 2 * len(bracket.get("pairs") or [])

    if ours:
        rank_text = f"并列第 {ours[0]['rank']} 名"
        rank_status = "ON_BOARD"
        best_ours = ours[0]
    else:
        rank_text = f"Top {len(board)} 外" if board else "暂无榜单"
        rank_status = "OUTSIDE_BOARD"
        best_ours = None

    return {
        "updated_at": now.isoformat(),
        "phase": phase,
        "sweep": pr["n"],
        "ref": str(pr["px"]),
        "age_s": pr["age_s"],
        "mark": str(mark) if mark is not None else None,
        "rank_status": rank_status,
        "rank_text": rank_text,
        "best_ours": best_ours,
        "ours_on_board": ours,
        "leader_score": leader,
        "top_threshold_score": threshold,
        "prize_cutoff_score": prize_cutoff,
        "prize_visible_wallets": prize_visible_wallets,
        "board_size": len(board),
        "board": board,
        "static_done": len(static_done),
        "static_total": 16,
        "bracket_round": bracket.get("round"),
        "bracket_status": bracket.get("status"),
        "bracket_pairs": len(bracket.get("pairs") or []),
        "submitted_wallets": submitted_wallets,
        "best_gross_edge": (
            {
                "name": best_edge["name"],
                "edge": str(best_edge["edge"].quantize(Decimal("0.01"))),
                "entry": str(best_edge["entry"]),
                "base_fee": str(best_edge["base_fee"].quantize(Decimal("0.01"))),
                "estimated_score": str(best_edge["estimated_score"].quantize(Decimal("0.01"))),
            }
            if best_edge else None
        ),
        "market_positions": {
            "open": positions.get("open"),
            "longs": positions.get("longs"),
            "shorts": positions.get("shorts"),
        } if isinstance(positions, dict) else None,
        "notes": {
            "exact_rank": (
                "命中官方公开榜时可确认公开榜并列名次；未命中时只能确认在公开 Top 列表之外，"
                "官方没有公开所有 owner 的实时完整排序。"
            ),
            "gross_edge": (
                "最佳估算 Score 使用当前 mark、入场价和 1% base fee 粗算；"
                "它是策略观察值，非官方 Score，真实 clawback 与 outcome 省略仍会造成偏差。"
            ),
        },
    }


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#080b12">
<title>Close Call Control Center</title>
<style>
:root{
  color-scheme:dark;
  --bg:#080b12;
  --panel:#101522;
  --panel2:#151b2a;
  --panel3:#0d1220;
  --line:#222b3d;
  --line2:#2e3950;
  --text:#f7f9fc;
  --muted:#8e9bb0;
  --muted2:#657189;
  --accent:#7c9cff;
  --accent2:#9f7cff;
  --good:#45d483;
  --warn:#f5c85b;
  --bad:#ff6f7d;
  --cyan:#56d7e5;
  --shadow:0 18px 60px rgba(0,0,0,.32);
}
*{box-sizing:border-box}
html,body{min-height:100%;margin:0}
body{
  background:
    radial-gradient(circle at 15% -10%,rgba(124,156,255,.14),transparent 34%),
    radial-gradient(circle at 85% 0%,rgba(159,124,255,.10),transparent 30%),
    linear-gradient(180deg,#080b12 0%,#0a0e17 52%,#080b12 100%);
  color:var(--text);
  font:14px/1.45 -apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",Inter,Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
}
a{color:inherit}
.shell{max-width:1280px;margin:0 auto;padding:34px 24px 56px}
.topbar{display:flex;align-items:flex-start;justify-content:space-between;gap:22px;margin-bottom:24px}
.brand{display:flex;align-items:center;gap:14px}
.logo{
  width:46px;height:46px;border-radius:15px;display:grid;place-items:center;font-weight:900;font-size:18px;
  background:linear-gradient(135deg,#7c9cff,#9f7cff 58%,#56d7e5);
  box-shadow:0 10px 30px rgba(124,156,255,.28)
}
.title{font-size:28px;font-weight:800;letter-spacing:-.03em;margin:0}
.subtitle{color:var(--muted);margin-top:5px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.status-dot{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 0 5px rgba(69,212,131,.08)}
.header-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:flex-end}
.badge,.btn{
  display:inline-flex;align-items:center;gap:7px;border:1px solid var(--line2);background:rgba(16,21,34,.84);
  border-radius:11px;padding:8px 11px;color:var(--muted);font-size:12px;text-decoration:none
}
.btn:hover{border-color:#43506b;color:var(--text);background:#151b2a}
.hero{
  display:grid;grid-template-columns:1.2fr .8fr;gap:16px;margin-bottom:16px
}
.hero-main,.hero-side,.metric,.section{
  background:linear-gradient(180deg,rgba(21,27,42,.96),rgba(13,18,32,.96));
  border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow)
}
.hero-main{padding:22px}
.hero-side{padding:22px}
.eyebrow{color:var(--muted);font-size:11px;font-weight:700;letter-spacing:.11em;text-transform:uppercase}
.rank-line{display:flex;align-items:flex-end;gap:13px;margin-top:10px;flex-wrap:wrap}
.rank-big{font-size:46px;font-weight:900;letter-spacing:-.045em;line-height:1}
.rank-status{font-size:13px;color:var(--muted);padding-bottom:5px}
.rank-big.good{color:var(--good)}.rank-big.warn{color:var(--warn)}
.kpi-row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:22px}
.kpi{background:rgba(8,11,18,.48);border:1px solid var(--line);border-radius:13px;padding:13px}
.kpi .n{font-size:21px;font-weight:800;margin-top:3px}
.kpi .t{font-size:11px;color:var(--muted)}
.prize-head{display:flex;justify-content:space-between;align-items:center;gap:12px}
.prize-value{font-size:34px;font-weight:850;letter-spacing:-.03em;margin-top:9px}
.prize-sub{color:var(--muted);font-size:12px;margin-top:5px}
.gap-box{margin-top:18px;padding:13px;border-radius:13px;background:rgba(245,200,91,.06);border:1px solid rgba(245,200,91,.18)}
.gap-title{display:flex;justify-content:space-between;color:var(--muted);font-size:11px}
.gap-bar{height:7px;border-radius:99px;background:#1a2030;margin-top:9px;overflow:hidden}
.gap-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--accent),var(--warn));width:0%}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}
.metric{padding:17px 18px;box-shadow:none}
.metric .label{color:var(--muted);font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.metric .value{font-size:25px;font-weight:850;letter-spacing:-.025em;margin-top:7px}
.metric .hint{font-size:12px;color:var(--muted);margin-top:5px}
.progress-wrap{margin-top:11px;height:7px;background:#1b2231;border-radius:99px;overflow:hidden}
.progress{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--accent),var(--cyan));width:0%}
.section{margin-top:16px;overflow:hidden;box-shadow:none}
.section-head{padding:17px 18px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:12px}
.section-title{font-size:15px;font-weight:800}
.section-sub{font-size:12px;color:var(--muted);margin-top:2px}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;min-width:720px}
th,td{padding:12px 16px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}
th{font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted2);font-weight:800;background:rgba(8,11,18,.28)}
td{font-size:13px}
tr:last-child td{border-bottom:0}
tr:hover td{background:rgba(124,156,255,.035)}
tr.ours td{background:rgba(69,212,131,.09)}
tr.prize td:first-child{box-shadow:inset 3px 0 0 var(--warn)}
.rank-cell{font-weight:800}
.score-cell{font-variant-numeric:tabular-nums;font-weight:750}
.did{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#c6d0e1;font-size:12px}
.pill{display:inline-flex;align-items:center;padding:4px 8px;border-radius:999px;background:#20293a;color:#cbd5e6;font-size:11px;border:1px solid #2d394e}
.prize-pill{background:rgba(245,200,91,.09);border-color:rgba(245,200,91,.24);color:#f7d77d}
.ours-pill{background:rgba(69,212,131,.1);border-color:rgba(69,212,131,.24);color:#7ce9aa}
.table-actions{display:flex;gap:8px}
.mini-btn{cursor:pointer;border:1px solid var(--line2);background:#121827;color:var(--muted);border-radius:9px;padding:7px 10px;font-size:11px}
.mini-btn:hover{color:var(--text);border-color:#46536f}
.note{padding:13px 18px 16px;color:var(--muted);font-size:11px}
.footer-links{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.footer-links a{text-decoration:none;color:#a8b8d4;border:1px solid var(--line);background:#0e1420;padding:9px 11px;border-radius:10px;font-size:11px}
.footer-links a:hover{border-color:#40506c;color:#fff}
.hide{display:none}
@media(max-width:980px){
  .hero{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,1fr)}.kpi-row{grid-template-columns:repeat(3,1fr)}
}
@media(max-width:620px){
  .shell{padding:22px 14px 40px}.topbar{flex-direction:column}.header-actions{justify-content:flex-start}
  .metrics{grid-template-columns:1fr}.kpi-row{grid-template-columns:1fr}.rank-big{font-size:39px}.title{font-size:24px}
}
</style>
</head>
<body>
<div class="shell">
  <div class="topbar">
    <div class="brand">
      <div class="logo">CC</div>
      <div>
        <h1 class="title">Close Call Control Center</h1>
        <div class="subtitle"><span class="status-dot"></span><span id="updated">正在连接 referee…</span></div>
      </div>
    </div>
    <div class="header-actions">
      <span class="badge" id="phaseBadge">TRADING</span>
      <span class="badge" id="refreshBadge">30s 自动刷新</span>
    </div>
  </div>

  <div class="hero">
    <div class="hero-main">
      <div class="eyebrow">Our best published standing</div>
      <div class="rank-line">
        <div class="rank-big warn" id="rank">-</div>
        <div class="rank-status" id="rankDetail">读取中</div>
      </div>
      <div class="kpi-row">
        <div class="kpi"><div class="t">榜首 Score</div><div class="n" id="leaderScore">-</div></div>
        <div class="kpi"><div class="t">奖区分数线</div><div class="n" id="prizeCutoff">-</div></div>
        <div class="kpi"><div class="t">奖区公开钱包</div><div class="n" id="prizeWallets">-</div></div>
      </div>
    </div>

    <div class="hero-side">
      <div class="prize-head">
        <div>
          <div class="eyebrow">Estimated strategy score</div>
          <div class="prize-value" id="estScore">-</div>
          <div class="prize-sub" id="estScoreDetail">策略观察值，非官方 Score</div>
        </div>
        <span class="pill prize-pill">Prize focus</span>
      </div>
      <div class="gap-box">
        <div class="gap-title"><span>估算值相对奖区线</span><span id="gapText">-</span></div>
        <div class="gap-bar"><div class="gap-fill" id="gapFill"></div></div>
      </div>
    </div>
  </div>

  <div class="metrics">
    <div class="metric">
      <div class="label">Static progress</div>
      <div class="value" id="staticValue">-</div>
      <div class="progress-wrap"><div class="progress" id="staticProgress"></div></div>
      <div class="hint" id="staticHint">等待数据</div>
    </div>
    <div class="metric">
      <div class="label">Bracket</div>
      <div class="value" id="bracketValue">-</div>
      <div class="hint" id="bracketHint">-</div>
    </div>
    <div class="metric">
      <div class="label">Ref / Mark</div>
      <div class="value" id="prices">-</div>
      <div class="hint" id="priceHint">-</div>
    </div>
    <div class="metric">
      <div class="label">Strategy wallets</div>
      <div class="value" id="wallets">-</div>
      <div class="hint" id="walletHint">已提交策略交易的钱包</div>
    </div>
  </div>

  <div class="section">
    <div class="section-head">
      <div>
        <div class="section-title">官方公开榜</div>
        <div class="section-sub" id="boardSummary">读取 referee PnL board…</div>
      </div>
      <div class="table-actions">
        <button class="mini-btn" id="toggleRows" onclick="toggleRows()">显示全部</button>
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>公开名次</th><th>账户</th><th>Score</th><th>状态</th><th>我们的标签</th></tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </div>
    <div class="note" id="note"></div>
  </div>

  <div class="footer-links">
    <a href="https://technocore.chat/r/d-close1-pnl" target="_blank">PnL 原始房间 ↗</a>
    <a href="https://technocore.chat/r/d-close1-positions" target="_blank">Positions 原始房间 ↗</a>
    <a href="https://technocore.chat/r/d-close1-price" target="_blank">Price 原始房间 ↗</a>
  </div>
</div>
<script>
let SHOW_ALL=false;
let LAST=null;

function fmtNum(v, digits=2){
  if(v===null || v===undefined || v==='') return '-';
  const n=Number(v); if(!Number.isFinite(n)) return String(v);
  return n.toLocaleString(undefined,{minimumFractionDigits:digits,maximumFractionDigits:digits});
}
function renderBoard(d){
  const tbody=document.getElementById('rows'); tbody.innerHTML='';
  const list=SHOW_ALL ? d.board : d.board.slice(0,10);
  for(const x of list){
    const tr=document.createElement('tr');
    tr.className=[x.ours?'ours':'',x.prize_zone?'prize':''].filter(Boolean).join(' ');
    const rankText=x.rank===x.index ? '#'+x.rank : '并列 #'+x.rank;
    const status=x.ours
      ? '<span class="pill ours-pill">我们的</span>'
      : (x.prize_zone ? '<span class="pill prize-pill">奖区</span>' : '<span class="pill">公开榜</span>');
    tr.innerHTML =
      '<td class="rank-cell">'+rankText+'</td>'+
      '<td class="did">'+x.did_short+'</td>'+
      '<td class="score-cell">'+fmtNum(x.score)+'</td>'+
      '<td>'+status+'</td>'+
      '<td>'+(x.label?'<span class="pill ours-pill">'+x.label+'</span>':'')+'</td>';
    tbody.appendChild(tr);
  }
  document.getElementById('toggleRows').textContent=SHOW_ALL?'收起到 Top 10':'显示全部 '+d.board.length;
}
function toggleRows(){SHOW_ALL=!SHOW_ALL;if(LAST)renderBoard(LAST)}

async function refresh(){
  try{
    const r=await fetch('/api/status',{cache:'no-store'});
    const d=await r.json();
    if(d.error) throw new Error(d.error);
    LAST=d;

    const localTime=new Date(d.updated_at).toLocaleString();
    document.getElementById('updated').textContent='实时 · '+localTime+' · sweep '+d.sweep;
    document.getElementById('phaseBadge').textContent=d.phase;
    document.getElementById('refreshBadge').textContent='30s 自动刷新 · ref '+d.age_s+'s';

    const rank=document.getElementById('rank');
    rank.textContent=d.rank_text;
    rank.className='rank-big '+(d.rank_status==='ON_BOARD'?'good':'warn');
    document.getElementById('rankDetail').textContent=d.best_ours
      ? d.best_ours.label+' · 官方 Score '+fmtNum(d.best_ours.score)
      : '当前没有我们的 DID 出现在官方公开 Top '+d.board_size;

    document.getElementById('leaderScore').textContent=fmtNum(d.leader_score);
    document.getElementById('prizeCutoff').textContent=fmtNum(d.prize_cutoff_score);
    document.getElementById('prizeWallets').textContent=d.prize_visible_wallets;

    const best=d.best_gross_edge;
    document.getElementById('estScore').textContent=best ? fmtNum(best.estimated_score)+' POLF' : '-';
    document.getElementById('estScoreDetail').textContent=best
      ? best.name+' · gross '+fmtNum(best.edge)+' · base fee≈'+fmtNum(best.base_fee)
      : '暂无估算';

    let gapText='-'; let pct=0;
    const est=best?Number(best.estimated_score):NaN;
    const cut=Number(d.prize_cutoff_score);
    if(Number.isFinite(est)&&Number.isFinite(cut)&&cut!==0){
      const gap=cut-est;
      gapText=(gap>0?'距线约 ':'高于线约 ')+fmtNum(Math.abs(gap))+' POLF';
      pct=Math.max(0,Math.min(100,(est/cut)*100));
    }
    document.getElementById('gapText').textContent=gapText;
    document.getElementById('gapFill').style.width=pct+'%';

    document.getElementById('staticValue').textContent=d.static_done+' / '+d.static_total;
    document.getElementById('staticProgress').style.width=((d.static_done/d.static_total)*100)+'%';
    document.getElementById('staticHint').textContent='Static cohorts completed';

    document.getElementById('bracketValue').textContent='R'+(d.bracket_round??'-');
    document.getElementById('bracketHint').textContent=(d.bracket_status??'-')+' · '+d.bracket_pairs+' pairs';

    document.getElementById('prices').textContent=fmtNum(d.ref)+' / '+fmtNum(d.mark);
    document.getElementById('priceHint').textContent='ref age '+d.age_s+'s · sweep '+d.sweep;

    document.getElementById('wallets').textContent=d.submitted_wallets;
    document.getElementById('walletHint').textContent='已进入策略流程的钱包';

    document.getElementById('boardSummary').textContent=
      '公开 Top '+d.board_size+' · '+d.prize_visible_wallets+' 个钱包当前占据 prize-place 并列组';
    document.getElementById('note').textContent=d.notes.exact_rank+' '+d.notes.gross_edge;
    renderBoard(d);
  }catch(e){
    document.getElementById('updated').textContent='读取失败 · '+e.message;
    document.querySelector('.status-dot').style.background='var(--bad)';
  }
}
refresh();
setInterval(refresh,30000);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/status":
            try:
                body = json.dumps(snapshot(), ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:
                body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
            return

        if self.path in ("/", "/index.html"):
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def log_message(self, fmt, *args):
        return


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Close Call dashboard: http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
