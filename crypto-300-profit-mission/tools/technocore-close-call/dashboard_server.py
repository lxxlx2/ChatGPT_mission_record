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
    STATIC_SCHEDULE_UTC,
    BRACKET_SCHEDULE_UTC,
    DENSE_MAX_DYNAMIC_KEYS,
    board_rows,
    fresh_price,
    latest_payload,
    room_recent_activity_age_s,
    room_registration_confirmed,
    load_state,
    local_board_matches,
    parse_export,
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


def _pnl_pairs(pnl: dict | None) -> list[tuple[str, Decimal]]:
    out = []
    if not isinstance(pnl, dict):
        return out
    for item in pnl.get("top") or []:
        try:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                out.append((str(item[0]), Decimal(str(item[1]))))
            elif isinstance(item, dict):
                did = item.get("key") or item.get("did")
                score = item.get("score")
                if did is not None and score is not None:
                    out.append((str(did), Decimal(str(score))))
        except Exception:
            continue
    return out


def _public_position_map(positions: dict | None) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    if not isinstance(positions, dict):
        return out
    for item in positions.get("top") or []:
        try:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                out[str(item[0])] = Decimal(str(item[1]))
            elif isinstance(item, dict):
                did = item.get("key") or item.get("did") or item.get("owner")
                pos = item.get("position")
                if pos is None:
                    pos = item.get("pos")
                if did is not None and pos is not None:
                    out[str(did)] = Decimal(str(pos))
        except Exception:
            continue
    return out


def _leader_position_estimate(
    current_board: list[dict],
    positions: dict | None,
    recent_limit: int = 24,
) -> dict | None:
    if not current_board:
        return None
    try:
        leader_score = Decimal(str(current_board[0]["score"]))
    except Exception:
        return None

    leader_dids = [
        str(row["did"])
        for row in current_board
        if row.get("did") and row.get("score") is not None
        and Decimal(str(row["score"])) == leader_score
    ]
    if not leader_dids:
        return None

    exact = _public_position_map(positions)
    exact_values = [(did, exact[did]) for did in leader_dids if did in exact]
    if exact_values:
        # Tied leader fleets often share a position. Use the median known
        # position so one anomalous key does not distort the relative target.
        vals = sorted(pos for _did, pos in exact_values)
        pos = vals[len(vals) // 2]
        return {
            "position": pos,
            "source": "official_positions",
            "sample_count": len(exact_values),
            "did": exact_values[0][0],
            "sweep_pair": None,
        }

    # Fall back to score-vs-mark slope from the newest pair of consecutive
    # referee sweeps in which a current leader DID appears in both snapshots.
    pnl_rows = []
    try:
        for rec in parse_export("d-close1-pnl"):
            p = rec.get("_payload")
            if isinstance(p, dict) and p.get("t") == "pnl":
                try:
                    n = int(p["n"])
                    mark = Decimal(str(p["mark"]))
                except Exception:
                    continue
                pnl_rows.append((n, mark, dict(_pnl_pairs(p))))
    except Exception:
        return None

    pnl_rows = pnl_rows[-max(2, int(recent_limit)):]
    candidates = []
    for did in leader_dids:
        for a, b in reversed(list(zip(pnl_rows, pnl_rows[1:]))):
            if b[0] != a[0] + 1 or did not in a[2] or did not in b[2]:
                continue
            dmark = b[1] - a[1]
            if dmark == 0:
                continue
            slope = (b[2][did] - a[2][did]) / dmark
            candidates.append((did, slope, (a[0], b[0])))
            break

    if not candidates:
        return None
    vals = sorted(x[1] for x in candidates)
    pos = vals[len(vals) // 2]
    rep = min(candidates, key=lambda x: abs(x[1] - pos))
    return {
        "position": pos,
        "source": "consecutive_pnl_slope",
        "sample_count": len(candidates),
        "did": rep[0],
        "sweep_pair": rep[2],
    }


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
    dense = state.get("dense") or {}

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
                    "qty": qty,
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
                        "qty": qty,
                        "base_fee": base_fee,
                        "estimated_score": edge - base_fee,
                        "side": "both",
                        "estimate_model": "base_fee",
                    })
                except Exception:
                    pass
        for ticket in dense.get("tickets") or []:
            try:
                ref_px = Decimal(str(ticket["ref"]))
                qty = Decimal(str(ticket["qty"]))
                edge = abs(mark - ref_px) * qty
                # Dense favored-ticket construction is designed so clawback
                # makes the target key's effective entry approximately the
                # sweep close. Until an official per-key score is published,
                # use the ticket ref as a transparent proxy for that close.
                gross_edges.append({
                    "name": f"DENSE-{int(ticket['index']):05d}",
                    "edge": edge,
                    "entry": ref_px,
                    "qty": qty,
                    "base_fee": Decimal("0"),
                    "estimated_score": edge,
                    "side": "both",
                    "estimate_model": "dense_ref_proxy",
                })
            except Exception:
                pass

        for ticket in dense.get("boost_tickets") or []:
            try:
                ref_px = Decimal(str(ticket["ref"]))
                qty = Decimal(str(ticket["qty"]))
                side = str(ticket.get("side") or "")
                if side == "long":
                    score = (mark - ref_px) * qty
                elif side == "short":
                    score = (ref_px - mark) * qty
                else:
                    continue
                gross_edges.append({
                    "name": f"BOOST-{side.upper()}-{int(ticket['reserve_index']):05d}",
                    "edge": score,
                    "entry": ref_px,
                    "qty": qty,
                    "base_fee": Decimal("0"),
                    "estimated_score": score,
                    "side": side,
                    "estimate_model": "dense_ref_proxy",
                })
            except Exception:
                pass

        for ticket in dense.get("v3_tickets") or []:
            try:
                ref_px = Decimal(str(ticket["ref"]))
                qty = Decimal(str(ticket["qty"]))
                for side in ("long", "short"):
                    score = (mark - ref_px) * qty if side == "long" else (ref_px - mark) * qty
                    gross_edges.append({
                        "name": f"V3-{side.upper()}-{int(ticket['reserve_index']):05d}",
                        "edge": score,
                        "entry": ref_px,
                        "qty": qty,
                        "base_fee": Decimal("0"),
                        "estimated_score": score,
                        "side": side,
                        "estimate_model": "dense_ref_proxy",
                    })
            except Exception:
                pass

        for ticket in dense.get("v4_tickets") or []:
            try:
                ref_px = Decimal(str(ticket["ref"]))
                qty = Decimal(str(ticket["qty"]))
                for side in ("long", "short"):
                    score = (mark - ref_px) * qty if side == "long" else (ref_px - mark) * qty
                    gross_edges.append({
                        "name": f"V4-{side.upper()}-{int(ticket['reserve_index']):05d}",
                        "edge": score,
                        "entry": ref_px,
                        "qty": qty,
                        "base_fee": Decimal("0"),
                        "estimated_score": score,
                        "side": side,
                        "estimate_model": "dense_ref_proxy",
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
    dynamic_keys = [k for k in state.get("keys", {}) if k.startswith("DENSE-")]
    submitted_wallets += len(dynamic_keys)

    ap = state.get("autopilot") or {}
    try:
        room_registered = room_registration_confirmed(state)
        room_activity_age_s = room_recent_activity_age_s(state["room"])
    except Exception:
        room_registered = False
        room_activity_age_s = None

    last_seen_at = ap.get("last_seen_at")
    autopilot_age_s = None
    if last_seen_at:
        try:
            autopilot_age_s = max(0, int((now - datetime.fromisoformat(last_seen_at)).total_seconds()))
        except Exception:
            autopilot_age_s = None

    bracket_status_text = str(bracket.get("status") or "")
    if "blocked" in bracket_status_text.lower():
        system_status = "NEEDS_ATTENTION"
        system_text = "策略遇到阻塞，需要检查"
        user_action = "需要检查后台状态"
    elif autopilot_age_s is None or autopilot_age_s > 180:
        system_status = "NEEDS_ATTENTION"
        system_text = "后台心跳异常"
        user_action = "需要检查后台是否仍在运行"
    elif pr["age_s"] > 120 and not (dense.get("v3_enabled") or dense.get("v4_enabled")):
        system_status = "WAITING"
        system_text = "正在等待更新的官方价格"
        user_action = "不用操作，程序会自动等待新价格"
    else:
        system_status = "OK"
        system_text = "策略正在正常自动运行"
        user_action = "现在不用做任何操作"

    pending_events = []
    # Dense mode freezes all future legacy Static/Bracket actions. Do not surface
    # their historical schedules as pending work on the user dashboard.
    if not dense.get("enabled"):
        for cohort, due_text in STATIC_SCHEDULE_UTC.items():
            key = f"{cohort:02d}"
            if key in state.get("static", {}):
                continue
            if key in (ap.get("missed_static") or {}):
                continue
            try:
                due = datetime.fromisoformat(due_text)
                pending_events.append((due, f"Static T{key} 自动开仓"))
            except Exception:
                pass

        round_no_now = int(bracket.get("round", 0) or 0)
        next_round = round_no_now + 1
        due_text = BRACKET_SCHEDULE_UTC.get(next_round)
        if due_text:
            try:
                due = datetime.fromisoformat(due_text)
                pending_events.append((due, f"Bracket R{next_round} 自动轮换"))
            except Exception:
                pass

    pending_events.sort(key=lambda x: x[0])
    next_event_at, next_event_text = (pending_events[0] if pending_events else (None, "等待最终结算"))
    next_event_due = bool(next_event_at and next_event_at <= now)
    next_event_lag_s = max(0, int((now - next_event_at).total_seconds())) if next_event_due else 0

    if next_event_due and system_status == "OK":
        system_status = "WAITING"
        system_text = f"{next_event_text} 已到时间，后台正在等待执行条件"
        user_action = "不用操作，后台会自动等待 fresh ref / gate 后执行"

    if dense.get("enabled"):
        if not room_registered:
            system_status = "WAITING"
            system_text = "交易房间注册尚未确认，正在自动处理"
            user_action = "不用操作，程序会自动注册并等待确认"
        pending = dense.get("pending") or {}
        if pending:
            if pending.get("status") == "registered":
                if dense.get("v4_enabled"):
                    next_event_text = f"Dense V4 第 {pending.get('index')} 组，等待下一 referee sweep 提交 8L + 8S ladder"
                elif dense.get("v3_enabled"):
                    next_event_text = f"Dense V3 第 {pending.get('index')} 组，等待下一 referee sweep 提交 8L + 8S"
                else:
                    next_event_text = f"Dense 第 {pending.get('index')} 组双向票，等待下一 fresh sweep 提交"
                next_event_at = None
                next_event_due = True
                next_event_lag_s = 0
            else:
                next_event_text = f"Dense 第 {pending.get('index')} 组正在注册"
                next_event_at = None
                next_event_due = True
                next_event_lag_s = 0
        else:
            if dense.get("v4_enabled"):
                next_event_text = "下一 referee sweep 创建 Dense V4 8L + 8S clawback ladder"
            elif dense.get("v3_enabled"):
                next_event_text = "下一 referee sweep 创建 Dense V3 8L + 8S"
            else:
                next_event_text = "下一 fresh sweep 创建新一组双向 favored tickets"
            next_event_at = None
            next_event_due = False
            next_event_lag_s = 0
        if system_status == "OK":
            if dense.get("v4_enabled") and dense.get("v5a_enabled") and dense.get("v5b_enabled"):
                active_h = dense.get("v5a_active") or {}
                active_c = dense.get("v5b_active") or {}
                if active_h:
                    system_text = "Dense V4 持续铺票，V5a 正在分阶段锁定利润"
                elif active_c:
                    system_text = "Dense V4 持续铺票，V5b 正在管理复利翻转仓位"
                else:
                    system_text = "Dense V4 持续铺票，V5a/V5b 等待下一次锁利或复利机会"
            elif dense.get("v4_enabled") and dense.get("v5a_enabled"):
                active_h = dense.get("v5a_active") or {}
                if active_h:
                    system_text = "Dense V4 持续铺票，V5a 正在分阶段锁定利润"
                else:
                    system_text = "Dense V4 持续铺票，V5a 正在等待锁利阈值"
            elif dense.get("v4_enabled"):
                system_text = "Dense V4 正在覆盖每一个 referee sweep"
            elif dense.get("v3_enabled"):
                system_text = "Dense V3 正在覆盖每一个 referee sweep"
            elif dense.get("v2_enabled"):
                system_text = "Dense V2 正在自动运行"
            else:
                system_text = "高密度双向策略正在自动运行"
            user_action = "现在不用做任何操作"

    target_to_prize = None
    if best_edge is not None and prize_cutoff is not None and mark is not None:
        try:
            cutoff = Decimal(str(prize_cutoff))
            qty = Decimal(str(best_edge["qty"]))
            entry = Decimal(str(best_edge["entry"]))
            base_fee = Decimal(str(best_edge["base_fee"]))
            need_move = (cutoff + base_fee) / qty
            side = best_edge.get("side", "both")
            down_target = entry - need_move if side in ("both", "short") else None
            up_target = entry + need_move if side in ("both", "long") else None
            down_gap = abs(mark - down_target) if down_target is not None else None
            up_gap = abs(up_target - mark) if up_target is not None else None
            if best_edge["estimated_score"] >= cutoff:
                nearest_side = "already_above"
                nearest_gap = Decimal("0")
                nearest_pct = Decimal("0")
            elif side == "short":
                nearest_side = "down"
                nearest_gap = down_gap
                nearest_pct = (down_gap / mark * Decimal("100")) if mark else None
            elif side == "long":
                nearest_side = "up"
                nearest_gap = up_gap
                nearest_pct = (up_gap / mark * Decimal("100")) if mark else None
            elif down_gap <= up_gap:
                nearest_side = "down"
                nearest_gap = down_gap
                nearest_pct = (down_gap / mark * Decimal("100")) if mark else None
            else:
                nearest_side = "up"
                nearest_gap = up_gap
                nearest_pct = (up_gap / mark * Decimal("100")) if mark else None
            target_to_prize = {
                "entry": str(entry),
                "qty": str(qty),
                "side": side,
                "down_target": str(down_target.quantize(Decimal("0.01"))) if down_target is not None else None,
                "up_target": str(up_target.quantize(Decimal("0.01"))) if up_target is not None else None,
                "nearest_side": nearest_side,
                "nearest_gap": str(nearest_gap.quantize(Decimal("0.01"))),
                "nearest_pct": str(nearest_pct.quantize(Decimal("0.01"))) if nearest_pct is not None else None,
                "cutoff": str(cutoff),
            }
        except Exception:
            target_to_prize = None

    relative_chase = None
    if best_edge is not None and leader is not None and mark is not None:
        try:
            leader_est = _leader_position_estimate(board, positions)
            if leader_est is not None:
                our_qty = Decimal(str(best_edge["qty"]))
                our_side = str(best_edge.get("side") or "both")
                if our_side == "long":
                    our_pos = our_qty
                elif our_side == "short":
                    our_pos = -our_qty
                else:
                    entry = Decimal(str(best_edge["entry"]))
                    our_pos = our_qty if mark >= entry else -our_qty

                leader_pos = Decimal(str(leader_est["position"]))
                our_score = Decimal(str(best_edge["estimated_score"]))
                leader_score_d = Decimal(str(leader))
                gap = leader_score_d - our_score
                rel_slope = our_pos - leader_pos

                direction = None
                delta = None
                target_mark = None
                pct = None
                if gap <= 0:
                    direction = "already_above"
                    delta = Decimal("0")
                    target_mark = mark
                    pct = Decimal("0")
                elif abs(rel_slope) >= Decimal("0.01"):
                    delta = gap / rel_slope
                    # A positive delta means an up move closes the gap; a
                    # negative delta means a down move closes it.
                    direction = "up" if delta > 0 else "down"
                    target_mark = mark + delta
                    pct = abs(delta) / mark * Decimal("100") if mark else None

                relative_chase = {
                    "leader_score": str(leader_score_d),
                    "our_score": str(our_score),
                    "score_gap": str(gap),
                    "our_position": str(our_pos),
                    "leader_position": str(leader_pos),
                    "relative_slope": str(rel_slope),
                    "direction": direction,
                    "move": str(abs(delta).quantize(Decimal("0.01"))) if delta is not None else None,
                    "move_pct": str(pct.quantize(Decimal("0.01"))) if pct is not None else None,
                    "target_mark": str(target_mark.quantize(Decimal("0.01"))) if target_mark is not None else None,
                    "position_source": leader_est.get("source"),
                    "position_sample_count": leader_est.get("sample_count"),
                    "position_sweep_pair": leader_est.get("sweep_pair"),
                    "assumption": "leader_position_unchanged",
                }
        except Exception:
            relative_chase = None

    if ours:
        rank_text = f"并列第 {ours[0]['rank']} 名"
        rank_status = "ON_BOARD"
        best_ours = ours[0]
    else:
        rank_text = f"Top {len(board)} 外" if board else "暂无榜单"
        rank_status = "OUTSIDE_BOARD"
        best_ours = None

    in_prize_zone = any(row.get("prize_zone") for row in ours)
    if in_prize_zone:
        prize_status_text = "已进入奖金区"
    elif ours:
        prize_status_text = "已上公开榜，暂未进奖金区"
    else:
        prize_status_text = "暂未进入奖金区"

    return {
        "updated_at": now.isoformat(),
        "phase": phase,
        "sweep": pr["n"],
        "ref": str(pr["px"]),
        "age_s": pr["age_s"],
        "mark": str(mark) if mark is not None else None,
        "rank_status": rank_status,
        "rank_text": rank_text,
        "in_prize_zone": in_prize_zone,
        "prize_status_text": prize_status_text,
        "system_status": system_status,
        "system_text": system_text,
        "user_action": user_action,
        "autopilot_age_s": autopilot_age_s,
        "next_event_text": next_event_text,
        "next_event_at": next_event_at.isoformat() if next_event_at else None,
        "next_event_due": next_event_due,
        "next_event_lag_s": next_event_lag_s,
        "last_action": ap.get("last_action"),
        "last_bracket_event": ap.get("last_bracket_event"),
        "last_dense_event": ap.get("last_dense_event"),
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
        "dense_enabled": bool(dense.get("enabled")),
        "dense_v2_enabled": bool(dense.get("v2_enabled")),
        "dense_v5a_enabled": bool(dense.get("v5a_enabled")),
        "dense_v5a_harvested_count": len(dense.get("v5a_harvested") or {}),
        "dense_v5a_active": dense.get("v5a_active"),
        "dense_v5a_last_locked": dense.get("v5a_last_locked"),
        "dense_v5a_last_skip": dense.get("v5a_last_skip"),
        "dense_v5b_enabled": bool(dense.get("v5b_enabled")),
        "dense_v5b_accept_new": bool(dense.get("v5b_accept_new", True)),
        "dense_v5b_pending": dense.get("v5b_pending"),
        "dense_v5b_active": dense.get("v5b_active"),
        "dense_v5b_closed_cycles": len(dense.get("v5b_cycles") or []),
        "dense_v5b_last_closed": dense.get("v5b_last_closed"),
        "dense_v5b_last_mark": dense.get("v5b_last_mark"),
        "dense_v4_enabled": bool(dense.get("v4_enabled")),
        "dense_v4_long_offset": dense.get("v4_long_offset"),
        "dense_v4_short_offsets": dense.get("v4_short_offsets"),
        "dense_v4_short_safeties": dense.get("v4_short_safeties"),
        "dense_v4_total_copies_per_side": dense.get("v4_total_copies_per_side"),
        "dense_v4_tickets": len(dense.get("v4_tickets") or []),
        "dense_v4_last_multiplicity": dense.get("last_v4_multiplicity"),
        "dense_v4_enabled_sweep": dense.get("v4_enabled_sweep"),
        "dense_v4_not_before_sweep": dense.get("v4_not_before_sweep"),
        "dense_v3_enabled": bool(dense.get("v3_enabled")),
        "dense_v3_offset": dense.get("v3_offset"),
        "dense_v3_total_copies_per_side": dense.get("v3_total_copies_per_side"),
        "dense_v3_tickets": len(dense.get("v3_tickets") or []),
        "dense_v3_reserve_registered": sum(1 for x in (dense.get("v3_reserve") or []) if x.get("status") == "registered"),
        "dense_v3_reserve_ready": sum(
            1 for x in (dense.get("v3_reserve") or [])
            if x.get("status") == "registered"
            and int(x.get("ready_after_sweep", 10**9)) <= int(pr["n"])
        ),
        "dense_v3_reserve_partial_errors": sum(
            1 for x in (dense.get("v3_reserve") or [])
            if x.get("status") == "partial_error"
        ),
        "dense_v3_last_multiplicity": dense.get("last_v3_multiplicity"),
        "dense_v3_age_gate_enabled": bool(dense.get("v3_ref_age_gate_enabled", False)),
        "dense_v2_offset": dense.get("v2_offset"),
        "dense_historical_low_ref": dense.get("historical_low_ref"),
        "dense_historical_high_ref": dense.get("historical_high_ref"),
        "dense_boost_tickets": len(dense.get("boost_tickets") or []),
        "dense_boost_total_copies": dense.get("v2_boost_total_copies"),
        "dense_boost_reserve_registered": sum(1 for x in (dense.get("boost_reserve") or []) if x.get("status") == "registered"),
        "dense_boost_reserve_ready": sum(
            1 for x in (dense.get("boost_reserve") or [])
            if x.get("status") == "registered"
            and int(x.get("ready_after_sweep", 10**9)) <= int(pr["n"])
        ),
        "dense_dynamic_key_cap": DENSE_MAX_DYNAMIC_KEYS,
        "dense_dynamic_keys": len(dynamic_keys),
        "dense_dynamic_key_budget_remaining": max(0, DENSE_MAX_DYNAMIC_KEYS - len(dynamic_keys)),
        "dense_last_boost": dense.get("last_boost"),
        "room_registered": room_registered,
        "room_activity_age_s": room_activity_age_s,
        "dense_submitted_sets": len(dense.get("tickets") or []),
        "dense_pending": dense.get("pending"),
        "dense_last_ticket": dense.get("last_ticket"),
        "best_gross_edge": (
            {
                "name": best_edge["name"],
                "edge": str(best_edge["edge"].quantize(Decimal("0.01"))),
                "entry": str(best_edge["entry"]),
                "qty": str(best_edge["qty"]),
                "base_fee": str(best_edge["base_fee"].quantize(Decimal("0.01"))),
                "estimated_score": str(best_edge["estimated_score"].quantize(Decimal("0.01"))),
                "side": best_edge.get("side", "both"),
                "estimate_model": best_edge.get("estimate_model", "base_fee"),
            }
            if best_edge else None
        ),
        "target_to_prize": target_to_prize,
        "relative_chase": relative_chase,
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
<title>Close Call 奖金追踪</title>
<style>
:root{
  color-scheme:dark;--bg:#080b12;--panel:#111725;--panel2:#0d1320;--line:#222c3d;
  --text:#f6f8fb;--muted:#8d99ae;--good:#48d287;--warn:#f5c85b;--bad:#ff7080;
  --blue:#7e9cff;--cyan:#55d4e5;--shadow:0 18px 55px rgba(0,0,0,.28)
}
*{box-sizing:border-box}html,body{margin:0;min-height:100%}
body{background:radial-gradient(circle at 15% -10%,rgba(126,156,255,.12),transparent 35%),linear-gradient(#080b12,#0a0e17);color:var(--text);font:14px/1.45 -apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
.shell{max-width:1240px;margin:auto;padding:30px 22px 56px}
.top{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:18px}.brand{display:flex;align-items:center;gap:13px}
.logo{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;font-weight:900;background:linear-gradient(135deg,#7e9cff,#a47fff 60%,#55d4e5)}
h1{font-size:26px;letter-spacing:-.03em;margin:0}.sub{color:var(--muted);font-size:12px;margin-top:3px}
.badge{border:1px solid #2d3950;background:#101725;border-radius:11px;padding:8px 10px;color:var(--muted);font-size:11px}
.actionbar{display:flex;align-items:center;justify-content:space-between;gap:16px;background:linear-gradient(90deg,rgba(72,210,135,.10),rgba(126,156,255,.06));border:1px solid rgba(72,210,135,.22);border-radius:16px;padding:15px 17px;margin-bottom:15px}
.actionleft{display:flex;align-items:center;gap:11px}.dot{width:10px;height:10px;border-radius:50%;background:var(--good);box-shadow:0 0 0 6px rgba(72,210,135,.08)}
.actiontitle{font-weight:800;font-size:15px}.actionsub{color:var(--muted);font-size:12px;margin-top:2px}.next{text-align:right}.next b{display:block;font-size:13px}.next span{color:var(--muted);font-size:11px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.card,.section{background:linear-gradient(180deg,#131a2a,#0e1421);border:1px solid var(--line);border-radius:17px;box-shadow:var(--shadow)}
.card{padding:17px 18px}.label{color:var(--muted);font-size:11px;font-weight:750;letter-spacing:.06em;text-transform:uppercase}.value{font-size:29px;font-weight:900;letter-spacing:-.035em;margin-top:7px}.hint{color:var(--muted);font-size:12px;margin-top:5px}.good{color:var(--good)}.warn{color:var(--warn)}.bad{color:var(--bad)}
.bigrow{display:grid;grid-template-columns:1.15fr .85fr;gap:12px;margin-top:12px}.bigcard{padding:20px}
.prizeStatus{font-size:34px;font-weight:900;letter-spacing:-.04em;margin-top:7px}.scoreline{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}.scoreline .main{font-size:36px;font-weight:900}.scoreline .small{color:var(--muted);font-size:12px}
.gap{margin-top:16px;padding:13px;border:1px solid rgba(245,200,91,.22);background:rgba(245,200,91,.06);border-radius:13px}.gap strong{font-size:19px}.gap p{margin:4px 0 0;color:var(--muted);font-size:11px}
.targets{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:12px}.target{padding:12px;background:rgba(8,11,18,.48);border:1px solid var(--line);border-radius:12px}.target b{display:block;font-size:20px;margin-top:3px}.target span{color:var(--muted);font-size:10px}
.progress{height:7px;background:#1b2333;border-radius:99px;overflow:hidden;margin-top:11px}.fill{height:100%;background:linear-gradient(90deg,var(--blue),var(--cyan));border-radius:99px}
.section{margin-top:14px;overflow:hidden;box-shadow:none}.sectionhead{padding:16px 18px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px}.sectiontitle{font-weight:850;font-size:15px}.sectionsub{font-size:11px;color:var(--muted);margin-top:2px}
table{width:100%;border-collapse:collapse}th,td{padding:11px 16px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}th{font-size:10px;color:#6f7c92;text-transform:uppercase;letter-spacing:.08em}td{font-size:12px}tr:last-child td{border-bottom:0}.ours td{background:rgba(72,210,135,.09)}.prize td:first-child{box-shadow:inset 3px 0 0 var(--warn)}
.pill{display:inline-block;border-radius:999px;padding:4px 8px;background:#20293a;border:1px solid #2d394e;color:#c9d3e2;font-size:10px}.pill.gold{background:rgba(245,200,91,.08);border-color:rgba(245,200,91,.25);color:#f5d36f}.pill.green{background:rgba(72,210,135,.09);border-color:rgba(72,210,135,.24);color:#7de9ad}
.did{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#b9c4d5}.tablewrap{overflow:auto}.note{padding:12px 18px;color:var(--muted);font-size:11px}
details{margin-top:14px;background:#0e1420;border:1px solid var(--line);border-radius:14px;padding:12px 14px;color:var(--muted)}summary{cursor:pointer;color:#b8c3d5;font-weight:700}.tech{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}.tech div{padding:10px;border-radius:10px;background:#111827}.tech b{display:block;color:var(--text);font-size:15px;margin-top:2px}.links{margin-top:10px;display:flex;gap:9px;flex-wrap:wrap}.links a{color:#aab9d5;text-decoration:none;font-size:11px}
@media(max-width:900px){.grid4{grid-template-columns:repeat(2,1fr)}.bigrow{grid-template-columns:1fr}.tech{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.shell{padding:20px 13px 40px}.top,.actionbar{align-items:flex-start;flex-direction:column}.next{text-align:left}.grid4{grid-template-columns:1fr}.targets{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="shell">
  <div class="top">
    <div class="brand"><div class="logo">CC</div><div><h1>Close Call 奖金追踪</h1><div class="sub" id="updated">正在读取比赛数据…</div></div></div>
    <div class="badge" id="phaseBadge">TRADING</div>
  </div>

  <div class="actionbar" id="actionbar">
    <div class="actionleft"><span class="dot" id="statusDot"></span><div><div class="actiontitle" id="systemText">读取后台状态…</div><div class="actionsub" id="userAction">-</div><div class="actionsub" id="lastAction">最近自动动作：读取中</div></div></div>
    <div class="next"><span>下一步自动动作</span><b id="nextEvent">-</b><span id="nextEventTime">-</span></div>
  </div>

  <div class="grid4">
    <div class="card"><div class="label">现在有没有进奖金区？</div><div class="value warn" id="prizeState">-</div><div class="hint">只有最终前三个 prize places 有奖金</div></div>
    <div class="card"><div class="label">我们当前最好公开名次</div><div class="value" id="rank">-</div><div class="hint" id="rankHint">-</div></div>
    <div class="card"><div class="label">当前奖金区分数线</div><div class="value" id="cutoff">-</div><div class="hint">达到这个附近才进入当前奖金竞争区</div></div>
    <div class="card"><div class="label">当前榜首</div><div class="value" id="leader">-</div><div class="hint">公开榜第一名的官方 Score</div></div>
  </div>

  <div class="bigrow">
    <div class="card bigcard">
      <div class="label">我们的当前最好成绩</div>
      <div class="scoreline"><div class="main" id="ourScore">-</div><div class="small" id="ourScoreType">-</div></div>
      <div class="gap">
        <strong id="scoreGap">-</strong>
        <p id="scoreExplain">这是估算值，只用来判断策略有没有接近奖区。</p>
      </div>
      <div class="targets">
        <div class="target"><span>如果继续下跌，粗略到这里</span><b id="downTarget">-</b></div>
        <div class="target"><span>如果继续上涨，粗略到这里</span><b id="upTarget">-</b></div>
      </div>
      <div class="hint" id="nearestTarget" style="margin-top:10px">目标会随奖区线变化，实际 clawback 也可能提高门槛。</div>
      <div class="gap" id="relativeChaseBox" style="margin-top:12px">
        <strong id="relativeChase">动态相对追赶线：计算中…</strong>
        <p id="relativeExplain">同时考虑我们当前最好仓位与榜首仓位的价格敏感度。</p>
      </div>
    </div>

    <div class="card bigcard">
      <div class="label">策略跑到哪一步？</div>
      <div style="margin-top:13px">
        <div style="display:flex;justify-content:space-between"><b id="staticTitle">Static -</b><span class="hint" id="staticRemain">-</span></div>
        <div class="progress"><div class="fill" id="staticFill" style="width:0%"></div></div>
      </div>
      <div style="margin-top:18px">
        <div style="display:flex;justify-content:space-between"><b id="bracketTitle">Bracket -</b><span class="hint" id="bracketHint">-</span></div>
        <div class="progress"><div class="fill" id="bracketFill" style="width:0%"></div></div>
      </div>
      <div class="hint" id="walletText" style="margin-top:18px">-</div>
    </div>
  </div>

  <div class="section">
    <div class="sectionhead"><div><div class="sectiontitle">官方公开榜</div><div class="sectionsub" id="boardSummary">这里只用来看竞争对手，以及我们的钱包有没有上榜。</div></div><span class="pill" id="boardCount">Top 25</span></div>
    <div class="tablewrap"><table><thead><tr><th>名次</th><th>账户</th><th>官方 Score</th><th>状态</th><th>我们的标签</th></tr></thead><tbody id="rows"></tbody></table></div>
    <div class="note" id="note"></div>
  </div>

  <details>
    <summary>系统技术信息（平时不用看）</summary>
    <div class="tech">
      <div><span>官方计分价格 Mark</span><b id="mark">-</b></div>
      <div><span>下单参考价 Ref</span><b id="ref">-</b></div>
      <div><span>Ref 新鲜度</span><b id="age">-</b></div>
      <div><span>Sweep</span><b id="sweep">-</b></div>
    </div>
    <div class="links">
      <a href="https://technocore.chat/r/d-close1-pnl" target="_blank">官方 PnL 原始数据 ↗</a>
      <a href="https://technocore.chat/r/d-close1-positions" target="_blank">官方 Positions 原始数据 ↗</a>
      <a href="https://technocore.chat/r/d-close1-price" target="_blank">官方 Price 原始数据 ↗</a>
    </div>
  </details>
</div>
<script>
function fmt(v,d=2){if(v===null||v===undefined||v==='')return '-';const n=Number(v);return Number.isFinite(n)?n.toLocaleString(undefined,{minimumFractionDigits:d,maximumFractionDigits:d}):String(v)}
async function refresh(){
  try{
    const r=await fetch('/api/status',{cache:'no-store'});const d=await r.json();if(d.error)throw new Error(d.error);
    document.getElementById('updated').textContent='实时更新 · '+new Date(d.updated_at).toLocaleString()+' · 每30秒刷新';
    document.getElementById('phaseBadge').textContent=d.phase;

    const dot=document.getElementById('statusDot');
    dot.style.background=d.system_status==='OK'?'var(--good)':(d.system_status==='WAITING'?'var(--warn)':'var(--bad)');
    document.getElementById('systemText').textContent=d.system_text;
    document.getElementById('userAction').textContent='你现在需要做什么：'+d.user_action;
    const lt=d.dense_last_ticket;
    const la=d.last_action;
    const lde=d.last_dense_event||{};
    if(String(lde.event||'').startsWith('v5b_')){
      let txt='最近自动动作：'+String(lde.event);
      if(lde.cycle_index)txt+=' · cycle '+lde.cycle_index;
      if(lde.side)txt+=' · '+String(lde.side).toUpperCase();
      if(lde.final_locked_score)txt+=' · 锁定 '+fmt(lde.final_locked_score)+' POLF';
      if(lde.projected_locked_score)txt+=' · projected '+fmt(lde.projected_locked_score);
      document.getElementById('lastAction').textContent=txt;
    }else if(String(lde.event||'').startsWith('v5a_')){
      let txt='最近自动动作：'+String(lde.event);
      if(lde.pair_id)txt+=' · '+lde.pair_id;
      if(lde.winner)txt+=' · '+String(lde.winner).toUpperCase();
      if(lde.locked_score)txt+=' · 锁定 '+fmt(lde.locked_score)+' POLF';
      if(lde.bootstrap_qty)txt+=' · bootstrap '+lde.bootstrap_qty;
      document.getElementById('lastAction').textContent=txt;
    }else if(d.dense_enabled && lt){
      let boostText='';
      if(lt.v4_multiplicity){
        boostText=' · V4 Long×'+Number(lt.v4_multiplicity.total_long_copies||1)+' / Short×'+Number(lt.v4_multiplicity.total_short_copies||1)+' ladder';
      }else if(lt.v3_multiplicity){
        boostText=' · V3 Long×'+Number(lt.v3_multiplicity.total_long_copies||1)+' / Short×'+Number(lt.v3_multiplicity.total_short_copies||1);
      }else if(lt.v2_boost){
        const bits=[];
        if(lt.v2_boost.long)bits.push('新低 Long×'+(1+Number(lt.v2_boost.long.submitted_extra_copies||0)));
        if(lt.v2_boost.short)bits.push('新高 Short×'+(1+Number(lt.v2_boost.short.submitted_extra_copies||0)));
        if(bits.length)boostText=' · '+bits.join(' / ');
      }
      document.getElementById('lastAction').textContent='最近自动动作：Dense #'+lt.index+' 已提交 · ref '+lt.ref+' · qty '+lt.qty+boostText;
    }else if(la){
      const actionName=la.action==='open_static'?('Static T'+la.cohort+' 已提交'):String(la.action||'自动动作');
      document.getElementById('lastAction').textContent='最近自动动作：'+actionName+(la.at?' · '+new Date(la.at).toLocaleString():'');
    }else{
      document.getElementById('lastAction').textContent='最近自动动作：暂无记录';
    }
    document.getElementById('nextEvent').textContent=d.next_event_text;
    if(d.next_event_due){
      const lag=Math.floor((d.next_event_lag_s||0)/60);
      document.getElementById('nextEventTime').textContent='已到执行时间'+(lag>0?' · 等待 '+lag+' 分钟':' · 正在等待本轮检查');
    }else{
      document.getElementById('nextEventTime').textContent=d.next_event_at?new Date(d.next_event_at).toLocaleString():'';
    }

    const prize=document.getElementById('prizeState');prize.textContent=d.prize_status_text;
    prize.className='value '+(d.in_prize_zone?'good':'warn');
    document.getElementById('rank').textContent=d.rank_text;
    document.getElementById('rankHint').textContent=d.best_ours?('我们的 '+d.best_ours.label+' · 官方 '+fmt(d.best_ours.score)):'我们的钱包还没出现在官方公开 Top '+d.board_size;
    document.getElementById('cutoff').textContent=fmt(d.prize_cutoff_score);
    document.getElementById('leader').textContent=fmt(d.leader_score);

    const best=d.best_gross_edge;
    let ourScore='-',scoreType='策略估算 Score',gapText='暂无可比数据';
    if(d.best_ours){ourScore=fmt(d.best_ours.score);scoreType='官方 Score · '+d.best_ours.label}
    else if(best){ourScore=fmt(best.estimated_score);scoreType='估算 Score · '+best.name+(best.estimate_model==='dense_ref_proxy'?' · Dense ref近似':'')+(best.side&&best.side!=='both'?' · '+best.side.toUpperCase():'')}
    document.getElementById('ourScore').textContent=ourScore+' POLF';
    document.getElementById('ourScoreType').textContent=scoreType;

    const scoreN=Number(d.best_ours?d.best_ours.score:(best?best.estimated_score:NaN));
    const cutoffN=Number(d.prize_cutoff_score);
    if(Number.isFinite(scoreN)&&Number.isFinite(cutoffN)){
      const diff=cutoffN-scoreN;
      gapText=diff>0?('按当前线估算，还差 '+fmt(diff)+' POLF'):('当前已高于奖区线约 '+fmt(Math.abs(diff))+' POLF');
    }
    document.getElementById('scoreGap').textContent=gapText;
    document.getElementById('scoreExplain').textContent=d.best_ours?'这里显示官方 Score。':(best&&best.estimate_model==='dense_ref_proxy'?'这里按 Dense ticket 的 ref 近似有效入场价估算，真实 sweep close / clawback 会造成偏差。':'这里显示我们当前最好候选的估算 Score，官方没上榜前只能作为参考。');

    const tp=d.target_to_prize;
    document.getElementById('downTarget').textContent=tp&&tp.down_target!==null?fmt(tp.down_target):'当前候选不看下跌';
    document.getElementById('upTarget').textContent=tp&&tp.up_target!==null?fmt(tp.up_target):'当前候选不看上涨';
    if(tp){
      let near='当前估算已经达到奖区线';
      if(tp.nearest_side==='down')near='最近路径：Mark 再跌约 '+fmt(tp.nearest_gap)+'（'+fmt(tp.nearest_pct)+'%）';
      if(tp.nearest_side==='up')near='最近路径：Mark 再涨约 '+fmt(tp.nearest_gap)+'（'+fmt(tp.nearest_pct)+'%）';
      document.getElementById('nearestTarget').textContent=near+'。按当前奖区线粗算，目标会动态变化，实际 clawback 可能提高门槛。';
    }else document.getElementById('nearestTarget').textContent='暂无目标估算。';

    const rc=d.relative_chase;
    const rcTitle=document.getElementById('relativeChase');
    const rcExplain=document.getElementById('relativeExplain');
    if(rc&&rc.direction){
      if(rc.direction==='already_above'){
        rcTitle.textContent='动态相对追赶线：当前估算已不低于榜首';
      }else{
        const dir=rc.direction==='up'?'上涨':'下跌';
        rcTitle.textContent='动态相对追赶线：Mark 再'+dir+'约 '+fmt(rc.move)+'（'+fmt(rc.move_pct)+'%）';
      }
      const source=rc.position_source==='official_positions'
        ?'榜首仓位取自官方 Positions'
        :('榜首仓位由连续 sweep '+((rc.position_sweep_pair||[]).join('→')||'')+' 的 Score/Mark 斜率估算');
      rcExplain.textContent='我们仓位斜率 '+fmt(rc.our_position)+' · 榜首 '+fmt(rc.leader_position)+' · 相对 '+fmt(rc.relative_slope)+' POLF/$1 · '+source+'。假设双方仓位保持不变；对手换仓后此线会自动重算。';
    }else{
      rcTitle.textContent='动态相对追赶线：暂时无法可靠计算';
      rcExplain.textContent='需要同时拿到我们当前最好候选的方向仓位，以及榜首的官方仓位或连续 sweep 斜率。';
    }

    if(d.dense_enabled){
      if(d.dense_v4_enabled){
        const layers=d.dense_v5b_enabled?'Dense V4 + V5a + V5b':(d.dense_v5a_enabled?'Dense V4 + V5a':'Dense V4');
        document.getElementById('staticTitle').textContent=layers+' 基础批次 '+d.dense_submitted_sets+' 组';
        document.getElementById('staticRemain').textContent='每 referee sweep：Long×8 @ 下限≈-5% · Short 3×+1% / 2×+1.7% / 3×+2%';
        document.getElementById('staticFill').style.width='100%';
        document.getElementById('bracketTitle').textContent='V4 Ladder 额外复制 '+d.dense_v4_tickets+' 组';
        const lastV4=d.dense_v4_last_multiplicity||{};
        const lastV4Copies=(lastV4.total_long_copies&&lastV4.total_short_copies)?(' · 最近 '+lastV4.total_long_copies+'L/'+lastV4.total_short_copies+'S'):'';
        const v4Err=Number((lastV4.errors||[]).length||0);
        const h=d.dense_v5a_active||{};
        const lock=d.dense_v5a_last_locked||{};
        const comp=d.dense_v5b_active||{};
        const compMark=d.dense_v5b_last_mark||{};
        const htxt=d.dense_v5a_enabled?(' · V5a 已锁 '+Number(d.dense_v5a_harvested_count||0)+(h.stage?(' · active '+h.stage):'')):'';
        const ctxt=d.dense_v5b_enabled?(' · V5b cycles '+Number(d.dense_v5b_closed_cycles||0)+(comp.status?(' · '+comp.status+' '+String(comp.side||'').toUpperCase()):'')):'';
        document.getElementById('bracketHint').textContent='Ready reserve '+d.dense_v3_reserve_ready+' / 注册 '+d.dense_v3_reserve_registered+lastV4Copies+(v4Err?(' · errors '+v4Err):'')+htxt+ctxt+' · Ref age 仅展示';
        document.getElementById('bracketFill').style.width='100%';
        const compoundScore=compMark.projected_flat_score?(' · V5b projected '+fmt(compMark.projected_flat_score)+' POLF'):'';
        document.getElementById('walletText').textContent='Dense keys '+d.dense_dynamic_keys+' / '+d.dense_dynamic_key_cap+' · 剩余预算 '+d.dense_dynamic_key_budget_remaining+(lock.locked_score?(' · 最近锁定 '+fmt(lock.locked_score)+' POLF'): '')+compoundScore+' · flow/state/missed/lock 安全门仍启用';
      }else if(d.dense_v3_enabled){
        document.getElementById('staticTitle').textContent='Dense V3 基础批次 '+d.dense_submitted_sets+' 组';
        document.getElementById('staticRemain').textContent='每个 referee sweep：Long×'+d.dense_v3_total_copies_per_side+' + Short×'+d.dense_v3_total_copies_per_side+' · 偏移 ±'+fmt(Number(d.dense_v3_offset||0)*100,0)+'%';
        document.getElementById('staticFill').style.width='100%';
        document.getElementById('bracketTitle').textContent='V3 额外复制票 '+d.dense_v3_tickets+' 组';
        const lastV3=d.dense_v3_last_multiplicity||{};
        const lastCopies=(lastV3.total_long_copies&&lastV3.total_short_copies)?(' · 最近 '+lastV3.total_long_copies+'L/'+lastV3.total_short_copies+'S'):'';
        const v3Err=Number(d.dense_v3_reserve_partial_errors||0);
        document.getElementById('bracketHint').textContent='Ready reserve '+d.dense_v3_reserve_ready+' / 注册 '+d.dense_v3_reserve_registered+lastCopies+(v3Err?(' · partial error '+v3Err):'')+' · Ref age 仅展示';
        document.getElementById('bracketFill').style.width='100%';
        document.getElementById('walletText').textContent='Dense keys '+d.dense_dynamic_keys+' / '+d.dense_dynamic_key_cap+' · 剩余预算 '+d.dense_dynamic_key_budget_remaining+' · flow/state/missed/lock 安全门仍启用';
      }else if(d.dense_v2_enabled){
        document.getElementById('staticTitle').textContent='Dense V2 基础双向票 '+d.dense_submitted_sets+' 组';
        document.getElementById('staticRemain').textContent='每个 fresh sweep 1L + 1S · 偏移 ±'+fmt(Number(d.dense_v2_offset||0)*100,0)+'%';
        document.getElementById('staticFill').style.width='100%';
        document.getElementById('bracketTitle').textContent='Extreme Boost '+d.dense_boost_tickets+' 张额外票';
        document.getElementById('bracketHint').textContent='新高加 short 到 '+d.dense_boost_total_copies+' 份 · 新低加 long 到 '+d.dense_boost_total_copies+' 份 · Ready reserve '+d.dense_boost_reserve_ready;
        document.getElementById('bracketFill').style.width='100%';
        document.getElementById('walletText').textContent='历史 Ref 区间 '+fmt(d.dense_historical_low_ref)+' ↔ '+fmt(d.dense_historical_high_ref)+' · Dense keys '+d.dense_dynamic_keys+' / '+d.dense_dynamic_key_cap+' · 剩余预算 '+d.dense_dynamic_key_budget_remaining;
      }else{
        document.getElementById('staticTitle').textContent='Dense 双向票 '+d.dense_submitted_sets+' 组';
        document.getElementById('staticRemain').textContent='每个 fresh sweep 自动新增 1 组';
        document.getElementById('staticFill').style.width='100%';
        document.getElementById('bracketTitle').textContent='旧策略已冻结';
        document.getElementById('bracketHint').textContent='保留 Static '+d.static_done+' 组 + Bracket R'+(d.bracket_round??'-')+' 现有仓位，不再继续加仓/轮换';
        document.getElementById('bracketFill').style.width='100%';
        document.getElementById('walletText').textContent='本地已创建策略钱包：'+d.submitted_wallets+' 个 · Dense 会继续按 sweep 增加';
      }
    }else{
      document.getElementById('staticTitle').textContent='Static '+d.static_done+' / '+d.static_total;
      document.getElementById('staticRemain').textContent='还剩 '+Math.max(0,d.static_total-d.static_done)+' 组';
      document.getElementById('staticFill').style.width=(100*d.static_done/d.static_total)+'%';
      document.getElementById('bracketTitle').textContent='Bracket R'+(d.bracket_round??'-')+' / 4';
      document.getElementById('bracketHint').textContent=(d.bracket_status??'-')+' · '+d.bracket_pairs+' pairs';
      document.getElementById('bracketFill').style.width=(25*Number(d.bracket_round||0))+'%';
      document.getElementById('walletText').textContent='已进入策略流程：'+d.submitted_wallets+' / 52 个钱包';
    }

    document.getElementById('boardCount').textContent='公开 Top '+d.board_size;
    document.getElementById('boardSummary').textContent=d.ours_on_board.length?'我们的钱包已出现在公开榜，绿色行为我们的。':'当前我们的钱包还没上榜，下面主要是竞争对手。';
    const tbody=document.getElementById('rows');tbody.innerHTML='';
    for(const x of d.board.slice(0,8)){
      const tr=document.createElement('tr');tr.className=[x.ours?'ours':'',x.prize_zone?'prize':''].filter(Boolean).join(' ');
      const status=x.ours?'<span class="pill green">我们的</span>':(x.prize_zone?'<span class="pill gold">奖区</span>':'');
      tr.innerHTML='<td><b>'+(x.rank===x.index?'#'+x.rank:'并列 #'+x.rank)+'</b></td><td class="did">'+x.did_short+'</td><td><b>'+fmt(x.score)+'</b></td><td>'+status+'</td><td>'+(x.label?'<span class="pill green">'+x.label+'</span>':'')+'</td>';
      tbody.appendChild(tr);
    }
    document.getElementById('note').textContent='如果我们的 DID 进入公开 Top '+d.board_size+'，这里会自动高亮并显示 TIME / BR 标签。没上榜时无法知道精确总排名。';

    document.getElementById('mark').textContent=fmt(d.mark);
    document.getElementById('ref').textContent=fmt(d.ref);
    document.getElementById('age').textContent=d.age_s+' 秒'+((d.dense_v3_enabled||d.dense_v4_enabled)?'（仅展示，不阻止交易）':'');
    document.getElementById('sweep').textContent=d.sweep;
  }catch(e){document.getElementById('systemText').textContent='面板读取失败';document.getElementById('userAction').textContent=e.message;document.getElementById('statusDot').style.background='var(--bad)'}
}
refresh();setInterval(refresh,30000);
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
