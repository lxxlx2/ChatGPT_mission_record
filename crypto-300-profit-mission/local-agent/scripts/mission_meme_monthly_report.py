#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from mission_agent.mission_control.outcomes import report


def epoch(value):
    if value is None:return None
    return datetime.fromisoformat(value.replace("Z","+00:00")).timestamp()


def pct(value):
    return "N/A" if value is None else str(value)+"%"


def main():
    parser=argparse.ArgumentParser(description="Mission Meme forward outcome report")
    parser.add_argument("--control-root",required=True)
    parser.add_argument("--since",help="ISO time, e.g. 2026-10-07T00:00:00+07:00")
    parser.add_argument("--until",help="ISO exclusive end")
    parser.add_argument("--output-dir")
    args=parser.parse_args()

    db_path=Path(args.control_root)/"mission-control.sqlite"
    if not db_path.is_file():raise SystemExit("MISSION_CONTROL_DB_NOT_FOUND")
    db=sqlite3.connect(db_path);db.row_factory=sqlite3.Row
    try:data=report(db,since_epoch=epoch(args.since),until_epoch=epoch(args.until))
    finally:db.close()

    out=Path(args.output_dir) if args.output_dir else Path(args.control_root)/"reports"
    out.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path=out/(stamp+"-meme-outcomes.json")
    md_path=out/(stamp+"-meme-outcomes.md")
    json_path.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))

    s=data["summary"]
    lines=[
        "# Mission Meme 月度/区间策略结果",
        "",
        f"生成时间: {data['generated_at']}",
        f"样本数: {s['track_count']}",
        f"有真实可执行入场报价: {s['entry_measured']}",
        "",
        "## 模式数量",
    ]
    for k,v in sorted(s["by_pattern"].items()):lines.append(f"- {k}: {v}")
    lines+=["","## 初始决策数量"]
    for k,v in sorted(s["by_decision"].items()):lines.append(f"- {k}: {v}")
    lines+=["","## 固定时间收益","", "|时间|有效样本/总样本|胜率|中位收益|","|---|---:|---:|---:|"]
    labels={"300":"5m","900":"15m","3600":"1h","21600":"6h","86400":"24h"}
    for h,row in s["horizons"].items():
        lines.append(f"|{labels.get(h,h+'s')}|{row['measured']}/{row['total']}|{pct(row['win_rate_pct'])}|{pct(row['median_return_pct'])}|")
    lines+=["","## 方法","",
        "- 入场：信号可用时 Jupiter 30 USDC -> token 的实际只读可执行报价。",
        "- 退出：同一笔入场得到的 token raw 数量 -> USDC 的 Jupiter 只读可执行报价。",
        "- 固定周期：T+5m / 15m / 1h / 6h / 24h。",
        "- MFE/MAE/最大回撤：5 分钟采样近似，不是逐 tick 极值。",
        "- 超出固定周期容忍窗口后才拿到的价格会标为 MISSED_WINDOW，不会拿晚到价格冒充历史价格。",
        "",
        "## 单样本路径统计",
    ]
    for tid,row in data["path_stats"].items():
        lines.append(f"- {tid[:12]}…: MFE {row['mfe_5m_sampled_pct']}%, MAE {row['mae_5m_sampled_pct']}%, MaxDD {row['max_drawdown_5m_sampled_pct']}%, samples={row['samples']}")
    md_path.write_text("\n".join(lines)+"\n")
    print(json.dumps({"status":"OK","json":str(json_path),"markdown":str(md_path),"summary":s},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
