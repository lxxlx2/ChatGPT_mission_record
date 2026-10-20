"""P4 historical local-index replay, explicitly NOT chain-verified/real-time.

Only feed genuine rows from an existing Frank /api/trades GET snapshot.
Each isolated event card uses its own dated signature/side but intentionally
does not invent source V1 signals, holdings, market quotes or order notional.
Historical fake SELL alerts are never sent or admitted to production.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import re
from typing import Any, Mapping

from mission_agent.mission_control.intelligence_preview import (
    analyze_rows, fake_intelligence_updates, render_html,
)

_BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,88}$")
_BUY = frozenset({"BUY", "ADD", "REENTRY"})
_SELL = frozenset({"SELL", "EXIT", "SELL_POSITION_UNRESOLVED"})
_SOURCE = "OLDER_FRANK_LOCAL_INDEX_SIGNED_TX_NOT_CHAIN_RECHECKED"


def select_cases(trades: list[dict[str, Any]], per_side: int = 5) -> list[dict[str, Any]]:
    """Pick at most five genuine signed BUY and five signed SELL category rows.

    The source must carry both source-side and raw-trade direction, agreeing.
    Do not equate an unresolved SELL with a complete exit.
    """
    if not isinstance(trades, list) or per_side < 1:
        raise ValueError("TRADE_SOURCE_OR_SAMPLE_SIZE_INVALID")
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for target in ("BUY", "SELL"):
        count = 0
        for trade in trades:
            if not isinstance(trade, Mapping):
                continue
            side = trade.get("side")
            direction = "BUY" if side in _BUY else "SELL" if side in _SELL else None
            if direction != target:
                continue
            body = trade.get("body")
            if not isinstance(body, Mapping) or body.get("direction") != direction:
                continue
            signature, mint, at = (trade.get("signature"), trade.get("mint"),
                                    trade.get("block_time"))
            if (not isinstance(signature, str) or not _BASE58.fullmatch(signature)
                    or not isinstance(mint, str) or not _BASE58.fullmatch(mint)
                    or not isinstance(at, (int, float)) or isinstance(at, bool)
                    or at <= 0 or at >= 253402300800 or signature in seen):
                continue
            seen.add(signature)
            selected.append({
                "signature": signature,
                "mint": mint,
                "block_time": float(at),
                "indexed_side": side,
                "direction": direction,
                "position_known_from_this_event": False,
                "source": _SOURCE,
            })
            count += 1
            if count >= per_side:
                break
    return selected


def run_replay(trades: list[dict[str, Any]], *, snapshot_at: float) -> dict[str, Any]:
    """Build past-as-of event cards and fake-only SELL notices for ten source rows.

    Current-state candidate records/episode facts are deliberately excluded.
    Reading an old source row today does not prove it was available at that
    historical time, nor that any V1 signal actually fired at the time.
    """
    selected = select_cases(trades)
    records: list[dict[str, Any]] = []
    analyses: list[dict[str, Any]] = []
    notices: list[dict[str, Any]] = []
    errors: list[str] = []
    for event in selected:
        at = event["block_time"]
        candidate = {
            "mint": event["mint"],
            "pattern": "UNKNOWN",
            "source_signal_id": None,
            "source_signal_at": None,
            "latest_side": event["direction"],
            "latest_at": at,
            "latest_signature": event["signature"],
            "latest_buy_at": at if event["direction"] == "BUY" else None,
            "latest_buy_price_usdc": None,
            "latest_buy_price_status": "QUOTE_PRICE_UNAVAILABLE",
            "position_state": None,
            "buy_count": None,
            "sell_count": None,
        }
        analysis = analyze_rows([candidate], as_of=at,
                                max_market_age_seconds=1,
                                market_observations=None)[0]
        before = analyze_rows([candidate], as_of=at - 1,
                              max_market_age_seconds=1,
                              market_observations=None)[0]
        immediate = fake_intelligence_updates([analysis], as_of=at,
                                              max_event_age_seconds=600)
        # Present the actual source-side category, not an invented full exit
        # or current zero balance. All messages are past-time unsent previews.
        for mock in immediate:
            if event["indexed_side"] == "SELL_POSITION_UNRESOLVED":
                mock["event"] = "观察到卖出 · 剩余仓位未核实"
                mock["position_assessment"] = "REMAINING_POSITION_UNVERIFIED"
            elif event["indexed_side"] == "EXIT":
                mock["event"] = "本地索引标记退出 · 当前钱包余额未核实"
                mock["position_assessment"] = "INDEXED_EXIT_CURRENT_BALANCE_UNVERIFIED"
            else:
                mock["event"] = "观察到卖出 · 是否全部退出未核实"
                mock["position_assessment"] = "REMAINING_POSITION_UNVERIFIED"
            mock["source_side"] = event["indexed_side"]
            mock["body"] = ("历史交易的模拟风险变化，非实时消息；"
                            "交易方向来自 Frank 本地索引。"
                            "当前账户/其他地址的剩余仓位未独立核验。")
            mock["current_wallet_balance_verified"] = False
        duplicate = fake_intelligence_updates(
            [analysis], as_of=at, max_event_age_seconds=600,
            previously_seen={x["key"] for x in immediate},
        )
        stale = fake_intelligence_updates([analysis], as_of=at + 601,
                                          max_event_age_seconds=600)
        checks = {
            "source_direction_reflected": analysis["latest_side"] == event["direction"],
            "source_signature_reflected": analysis["latest_signature"] == event["signature"],
            "future_trade_blocked": (
                before["latest_side"] == "UNVERIFIED" and
                before["latest_signature"] is None and
                "CANDIDATE_EVENT_AFTER_AS_OF" in before["missing"]
            ),
            "no_fabricated_market_or_pnl": (
                analysis["price"]["market_price_usdc"] is None and
                analysis["price"]["change_pct_vs_last_verified_buy"] is None and
                analysis["price"]["buy_price_usdc"] is None
            ),
            "no_v1_signal_invented": (
                analysis["source_signal_id"] is None and
                "V1_SOURCE_SIGNAL_NOT_VERIFIED" in analysis["missing"]
            ),
            "model_position_unverified": (
                analysis["model_episode_position_state"] == "UNVERIFIED"
            ),
            "no_user_order_amount": analysis["order_amount_usdc"] is None,
            "no_live_notification": analysis["alert_delivery_authorized"] is False,
            "mock_sell_trigger_matches": (
                len(immediate) == (1 if event["direction"] == "SELL" else 0)
                and all(x["send_allowed"] is False and not x["channels"] for x in immediate)
            ),
            "mock_dedup": len(duplicate) == 0,
            "historical_notice_not_live": len(stale) == 0,
            "unresolved_sell_not_called_exit": (
                event["indexed_side"] != "SELL_POSITION_UNRESOLVED"
                or analysis["model_episode_position_state"] == "UNVERIFIED"
            ),
            "mock_notice_residual_balance_unverified": (
                all(mock.get("current_wallet_balance_verified") is False
                    and mock.get("source_side") == event["indexed_side"]
                    and mock.get("position_assessment") in {
                        "REMAINING_POSITION_UNVERIFIED",
                        "INDEXED_EXIT_CURRENT_BALANCE_UNVERIFIED",
                    } for mock in immediate)
            ),
        }
        records.append({
            **event,
            "bangkok_time": datetime.fromtimestamp(
                at, timezone.utc).astimezone(__import__("zoneinfo").ZoneInfo("Asia/Bangkok")
                ).isoformat(timespec="seconds"),
            "checks": checks,
            "mock_notice_count": len(immediate),
            "mock_notice_kind": immediate[0]["kind"] if immediate else None,
            "fake_only": True,
            "chain_independently_rechecked": False,
            "known_v1_signal_at_event": False,
            "historical_time_observability_proven": False,
            "new_dashboard_live_display_proven": False,
        })
        if not all(checks.values()):
            errors.append("CASE_CHECK_FAILED:" + event["signature"])
        analyses.append(analysis)
        notices.extend(immediate)

    coverage = {
        "distinct_signatures": len({e["signature"] for e in selected}),
        "distinct_mints": len({e["mint"] for e in selected}),
        "indexed_sides": dict(Counter(e["indexed_side"] for e in selected)),
        "historical_fake_sell_notices": len(notices),
    }
    complete = len(selected) == 10 and all(
        sum(e["direction"] == d for e in selected) == 5 for d in ("BUY", "SELL")
    )
    if not complete:
        errors.append("FEWER_THAN_TEN_DATED_VALID_DISTINCT_TRADE_ROWS")
    html = render_html(analyses, as_of=snapshot_at, simulated_updates=notices)
    if not all(x["signature"] in html and x["mint"] in html for x in selected):
        errors.append("HISTORICAL_CARD_RENDER_MISSING_SOURCE_ID")
    for notice in notices:
        if (notice.get("mode") != "FAKE_PREVIEW_ONLY_NO_SEND" or
                notice.get("send_allowed") is not False or
                notice.get("channels") != []):
            errors.append("FAKE_NOTICE_SAFETY_ASSERTION_FAILED")
    return {
        "status": "PASS_LOCAL_INDEX_RETROSPECTIVE_REPLAY" if not errors
                  else "INCOMPLETE_OR_FAILED",
        "source_scope": "LOCAL_INDEX_ONLY_NOT_CHAIN_VERIFIED",
        "not_realtime": True,
        "independent_chain_verification": "NOT_PERFORMED",
        "historical_observability_proven": False,
        "old_v1_signal_emission_proven": False,
        "new_option3_live_alert_delivery_proven": False,
        "profit_or_executability_proven": False,
        "source_snapshot_at": snapshot_at,
        "counts": coverage,
        "cases": records,
        "errors": errors,
        "html": html,
    }
