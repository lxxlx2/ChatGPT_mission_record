"""Frank P4 isolated activity/RISK RESEARCH ONLY, sourced from actual indexed rows.

Show verified locally indexed signed buys and sales *independently* from the
current ACCUMULATION/MULTIPLE candidate subset. An observed sale is NOT evidence
that a previous buy alert was generated/delivered, or that Frank exited fully.
No amount, quote, provider, outbox, delivery or automatic order logic.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from html import escape
import re
from typing import Any, Mapping

_BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,88}$")
_BUYS = {"BUY", "ADD", "REENTRY"}
_SELLS = {"SELL", "EXIT", "SELL_POSITION_UNRESOLVED"}
_SIDES = _BUYS | _SELLS
_LABELS = {
    "BUY": "已索引买入（不是跟买建议）",
    "ADD": "已索引追加买入（不是跟买建议）",
    "REENTRY": "已索引重新买入（不是此前持续持仓的证明）",
    "SELL": "已索引卖出；剩余仓位未核实",
    "EXIT": "本地索引分类为退出；当前链上余额未核实",
    "SELL_POSITION_UNRESOLVED": "观察到卖出；剩余仓位无法确定",
}


def build_activity_watch(
    trades: list[Mapping[str, Any]], candidates: list[Mapping[str, Any]],
    *, as_of: float,
) -> dict[str, Any]:
    if not isinstance(trades, list) or len(trades) > 100:
        raise ValueError("ACTIVITY_INPUT_MUST_BE_BOUNDED_100")
    if not isinstance(candidates, list):
        raise ValueError("CANDIDATES_MUST_BE_LIST")
    if isinstance(as_of, bool) or not isinstance(as_of, (int, float)) or as_of <= 0:
        raise ValueError("INVALID_SNAPSHOT_TIME")
    candidate_mints = {
        x.get("mint") for x in candidates
        if isinstance(x, Mapping) and isinstance(x.get("mint"), str)
    }
    items: list[dict[str, Any]] = []
    seen: dict[str, tuple[str, str, int]] = {}
    omissions = Counter()
    for raw in trades:
        if not isinstance(raw, Mapping):
            omissions["INVALID_SOURCE_ROW"] += 1
            continue
        signature, mint, side = raw.get("signature"), raw.get("mint"), raw.get("side")
        ts = raw.get("block_time")
        body = raw.get("body")
        if (not isinstance(signature, str) or not _BASE58.fullmatch(signature)
                or not isinstance(mint, str) or not _BASE58.fullmatch(mint)
                or side not in _SIDES or isinstance(ts, bool)
                or not isinstance(ts, (int, float))
                or ts < 1_600_000_000 or ts > as_of
                or not isinstance(body, Mapping)):
            omissions["UNVERIFIABLE_SOURCE_FIELDS"] += 1
            continue
        expected_direction = "BUY" if side in _BUYS else "SELL"
        if body.get("direction") != expected_direction:
            omissions["DIRECTION_MISMATCH_NOT_DISPLAYED"] += 1
            continue
        event_key = (mint, side, int(ts))
        if signature in seen:
            if seen[signature] != event_key:
                raise ValueError("SAME_SIGNATURE_CONFLICTING_SOURCE_FACTS")
            omissions["DUPLICATE_SIGNATURE_SUPPRESSED"] += 1
            continue
        seen[signature] = event_key
        items.append({
            "mint": mint,
            "signature": signature,
            "source_side": side,
            "observed_at": int(ts),
            "label": _LABELS[side],
            "kind": "OBSERVED_SELL_REVIEW" if side in _SELLS else "OBSERVED_BUY_RESEARCH",
            "in_current_candidate_mint_set": mint in candidate_mints,
            "related_to_prior_v1_signal": "NOT_VERIFIED",
            "recipient_alert_delivery": "NOT_VERIFIED",
            "current_wallet_balance": "NOT_VERIFIED",
            "quote_or_pnl": "NOT_ASSESSED",
            "live_notification_eligible": False,
            "send_allowed": False,
            "channels": [],
        })
    items.sort(key=lambda x: (-x["observed_at"], x["signature"]))
    return {
        "status": "LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY",
        "captured_at": as_of,
        "scope": "LATEST_100_LOCAL_INDEX_TRADES_NOT_COMPLETE_CHAIN",
        "source_rows_considered": len(trades),
        "displayed_transactions": len(items),
        "counts": {
            "buy_category": sum(x["source_side"] in _BUYS for x in items),
            "sell_category": sum(x["source_side"] in _SELLS for x in items),
            "sell_not_in_current_candidate_mint_set": sum(
                x["source_side"] in _SELLS and not x["in_current_candidate_mint_set"]
                for x in items),
            "unresolved_position_sell": sum(
                x["source_side"] == "SELL_POSITION_UNRESOLVED" for x in items),
            "omissions": dict(omissions),
        },
        "items": items,
        "prior_v1_signal_linkage_verified": False,
        "real_notifications_authorized": False,
        "new_rpc_or_provider_used": False,
        "user_order_amount": None,
    }


def render_activity_watch(report: Mapping[str, Any]) -> str:
    if report.get("status") != "LOCAL_SOURCE_ACTIVITY_RESEARCH_ONLY":
        raise ValueError("INVALID_ACTIVITY_RESEARCH_REPORT")
    counts = report["counts"]
    cards = []
    for x in report["items"][:40]:
        mint, sig = x["mint"], x["signature"]
        when = datetime.fromtimestamp(x["observed_at"], timezone.utc).isoformat()
        flag = ("当前候选有同币种（不证明同轮信号）"
                if x["in_current_candidate_mint_set"] else
                "当前候选无此币种，仍保留历史活动事实")
        tx_url = "https://solscan.io/tx/" + sig
        cards.append(
            '<article class="card"><strong>' + escape(x["label"]) +
            '</strong><p>本地索引时间 UTC：' + escape(when) +
            '</p><p>CA：<code>' + escape(mint) + '</code> ' +
            '<button type="button" data-ca="' + escape(mint, quote=True) +
            '">复制 CA</button></p><p><a rel="noopener noreferrer" '
            'target="_blank" href="' + escape(tx_url, quote=True) +
            '">交易签名证据 ↗</a></p><p>' + escape(flag) +
            '</p><p>是否关联此前已发买入提醒：未核实；当前链上仓位：未核实</p>'
            '</article>'
        )
    summary = (
        f'交易 {report["displayed_transactions"]} 条；'
        f'买类 {counts["buy_category"]}；卖类 {counts["sell_category"]}；'
        f'卖类中未进入当前候选币种集合 {counts["sell_not_in_current_candidate_mint_set"]}；'
        f'仓位未确定的卖出 {counts["unresolved_position_sell"]}。'
    )
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Frank 历史活动与风险观察（隔离 QA）</title>'
        '<style>body{font:15px system-ui;background:#171923;color:#eee;'
        'margin:24px auto;padding:0 12px;max-width:1080px}a{color:#a7d8ff}'
        '.card{background:#262a37;padding:15px;border-radius:8px;margin:12px 0;'
        'overflow-wrap:anywhere}code{font-size:12px}button{cursor:pointer}</style>'
        '</head><body><h1>Frank 钱包活动与风险观察 · 只读隔离验收</h1>'
        '<p>快照来自旧 Frank 本地已索引交易，不是实时行情/全链数据。'
        '卖出无需先触发新的买入信号，但不能冒充此前提醒的清仓或已送达通知。'
        '页面不会自动发送通知、下单或计算用户买入金额。</p>'
        '<p><strong>' + escape(summary) + '</strong></p>'
        '<p>只显示最近 40 条有效记录；如交易超过 100 条，源接口本身仅返回最新 100 条。'
        '代币名额与当前候选不一致是正常现象；不要把缺失的候选当成没发生交易。</p>'
        '<p><a href="/">返回 Frank 智能分析首页</a></p>'
        + "".join(cards) +
        '<script>document.addEventListener("click",async e=>{'
        'const el=e.target.closest("button[data-ca]");if(!el)return;'
        'try{await navigator.clipboard.writeText(el.dataset.ca);'
        'el.textContent="已复制 CA"}catch(_){el.textContent="请手动复制 CA"}})'
        '</script></body></html>'
    )
