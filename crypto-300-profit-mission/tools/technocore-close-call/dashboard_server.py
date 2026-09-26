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
                gross_edges.append({
                    "name": f"T{k}",
                    "edge": abs(mark - px) * qty,
                    "entry": px,
                })
            except Exception:
                pass
        if int(bracket.get("round", 0) or 0) == 1:
            pairs = bracket.get("pairs") or []
            if pairs:
                try:
                    px = Decimal(str(pairs[0]["px"]))
                    qty = Decimal(str(pairs[0]["qty"]))
                    gross_edges.append({
                        "name": "BR-R1",
                        "edge": abs(mark - px) * qty,
                        "entry": px,
                    })
                except Exception:
                    pass

    gross_edges.sort(key=lambda x: x["edge"], reverse=True)
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
                "Gross edge 只是当前 mark 相对入场价的结构性毛收益估算，"
                "不等于官方 score，未扣真实 fee/clawback，也受 outcome 省略影响。"
            ),
        },
    }


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Close Call Dashboard</title>
<style>
:root{color-scheme:dark;--bg:#0b0d10;--card:#151922;--muted:#8d96a8;--text:#f5f7fb;--good:#49d17d;--warn:#ffcc66;--bad:#ff6b6b;--line:#2a3040}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}.title{font-size:28px;font-weight:750;margin-bottom:4px}.sub{color:var(--muted);margin-bottom:22px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}.value{font-size:27px;font-weight:750;margin-top:6px}.small{font-size:13px;color:var(--muted);margin-top:6px}
.good{color:var(--good)}.warn{color:var(--warn)}.bad{color:var(--bad)} h2{font-size:18px;margin:26px 0 12px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden}
th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left}th{color:var(--muted);font-weight:600;font-size:12px}tr:last-child td{border-bottom:0}.ours{background:rgba(73,209,125,.14)}.prize{box-shadow:inset 3px 0 0 var(--warn)}
.pill{display:inline-block;padding:3px 8px;border-radius:999px;background:#232a38;font-size:12px}.foot{margin-top:14px;color:var(--muted);font-size:12px}
.links a{color:#9ec1ff;text-decoration:none;margin-right:14px}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}} @media(max-width:520px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body><div class="wrap">
<div class="title">Close Call 实时面板</div>
<div class="sub" id="updated">加载中…</div>
<div class="grid">
  <div class="card"><div class="label">我们的公开排名</div><div class="value" id="rank">-</div><div class="small" id="rankDetail"></div></div>
  <div class="card"><div class="label">榜首 / 奖区分数线</div><div class="value" id="scores">-</div><div class="small" id="boardSize"></div></div>
  <div class="card"><div class="label">策略进度</div><div class="value" id="progress">-</div><div class="small" id="bracket"></div></div>
  <div class="card"><div class="label">最佳毛 Edge</div><div class="value" id="edge">-</div><div class="small" id="edgeDetail"></div></div>
</div>
<h2>官方公开榜</h2>
<table><thead><tr><th>公开名次</th><th>账户</th><th>Score</th><th>我们的标签</th></tr></thead><tbody id="rows"></tbody></table>
<div class="foot" id="note"></div>
<h2>市场状态</h2>
<div class="grid">
  <div class="card"><div class="label">Sweep</div><div class="value" id="sweep">-</div></div>
  <div class="card"><div class="label">Ref / Mark</div><div class="value" id="prices">-</div></div>
  <div class="card"><div class="label">Ref age</div><div class="value" id="age">-</div></div>
  <div class="card"><div class="label">已提交策略钱包</div><div class="value" id="wallets">-</div></div>
</div>
<div class="foot links">
<a href="https://technocore.chat/r/d-close1-pnl" target="_blank">官方 PnL 原始房间</a>
<a href="https://technocore.chat/r/d-close1-positions" target="_blank">官方 Positions 原始房间</a>
<a href="https://technocore.chat/r/d-close1-price" target="_blank">官方 Price 原始房间</a>
</div>
</div>
<script>
async function refresh(){
  try{
    const r=await fetch('/api/status',{cache:'no-store'}); const d=await r.json();
    document.getElementById('updated').textContent='自动刷新 · '+new Date(d.updated_at).toLocaleString()+' · '+d.phase;
    const rank=document.getElementById('rank'); rank.textContent=d.rank_text;
    rank.className='value '+(d.rank_status==='ON_BOARD'?'good':'warn');
    document.getElementById('rankDetail').textContent=d.best_ours ? (d.best_ours.label+' · score '+d.best_ours.score) : '当前没有我们的 DID 出现在官方公开 Top 列表';
    document.getElementById('scores').textContent=(d.leader_score??'-')+' / '+(d.prize_cutoff_score??'-');
    document.getElementById('boardSize').textContent='榜首 / 当前占据前三 prize places 的最低公开分 · '+d.prize_visible_wallets+' 个公开钱包在奖区组';
    document.getElementById('progress').textContent='Static '+d.static_done+'/'+d.static_total;
    document.getElementById('bracket').textContent='Bracket R'+(d.bracket_round??'-')+' · '+(d.bracket_status??'-')+' · '+d.bracket_pairs+' pairs';
    document.getElementById('edge').textContent=d.best_gross_edge ? d.best_gross_edge.edge+' POLF' : '-';
    document.getElementById('edgeDetail').textContent=d.best_gross_edge ? d.best_gross_edge.name+' · entry '+d.best_gross_edge.entry : '暂无';
    document.getElementById('sweep').textContent=d.sweep;
    document.getElementById('prices').textContent=d.ref+' / '+(d.mark??'-');
    document.getElementById('age').textContent=(d.age_s??'-')+'s';
    document.getElementById('wallets').textContent=d.submitted_wallets;
    const tbody=document.getElementById('rows'); tbody.innerHTML='';
    for(const x of d.board){
      const tr=document.createElement('tr');
      tr.className=[x.ours?'ours':'',x.prize_zone?'prize':''].filter(Boolean).join(' ');
      const rankText=(x.rank===x.index?'#'+x.rank:'并列 #'+x.rank)+(x.prize_zone?' · 奖区':'');
      tr.innerHTML='<td>'+rankText+'</td><td>'+x.did_short+'</td><td>'+x.score+'</td><td>'+(x.label?'<span class="pill">'+x.label+'</span>':'')+'</td>';
      tbody.appendChild(tr);
    }
    document.getElementById('note').textContent=d.notes.exact_rank+' '+d.notes.gross_edge;
  }catch(e){document.getElementById('updated').textContent='读取失败: '+e}
}
refresh(); setInterval(refresh,30000);
</script></body></html>"""


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
