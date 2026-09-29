# /// script
# requires-python = ">=3.12"
# dependencies = ["cryptography>=42"]
# ///
"""
Technocore Close Call fleet helper.

Secrets stay in ~/.config/technocore-close-call/keys.json (mode 600).
Nothing in this script writes private seeds to GitHub.

Immediate scope:
- init a fixed 52-key fleet
- bootstrap BASE-B0 + a dedicated low-traffic room
- register the remaining fleet
- read live referee status
- verify the exact local fleet is registered/minted before trading
- open one static time-layer pair
- inspect a submitted trade outcome in referee flow
- open bracket round 1

Later bracket rollovers are intentionally not automated in v1. They should be
added after we confirm live settlement behavior from round 1.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import stat
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BASE = "https://technocore.chat"
SEASON = "close-1"
STATE_PATH = Path("~/.config/technocore-close-call/keys.json").expanduser()
MULTICODEC_ED25519 = b"\xed\x01"
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

STATIC_SCHEDULE_UTC = {
    1: "2026-09-26T09:00:00+00:00",
    2: "2026-09-26T21:00:00+00:00",
    3: "2026-09-27T09:00:00+00:00",
    4: "2026-09-27T21:00:00+00:00",
    5: "2026-09-28T09:00:00+00:00",
    6: "2026-09-28T21:00:00+00:00",
    7: "2026-09-29T09:00:00+00:00",
    8: "2026-09-29T21:00:00+00:00",
    9: "2026-09-30T09:00:00+00:00",
    10: "2026-09-30T21:00:00+00:00",
    11: "2026-10-01T09:00:00+00:00",
    12: "2026-10-01T21:00:00+00:00",
    13: "2026-10-02T09:00:00+00:00",
    14: "2026-10-02T21:00:00+00:00",
    15: "2026-10-03T09:00:00+00:00",
    16: "2026-10-03T21:00:00+00:00",
}

BRACKET_SCHEDULE_UTC = {
    1: "2026-09-26T09:15:00+00:00",
    2: "2026-09-28T09:15:00+00:00",
    3: "2026-09-30T09:15:00+00:00",
    4: "2026-10-02T09:15:00+00:00",
}

LOCK_TIME_UTC = datetime.fromisoformat("2026-10-04T09:00:00+00:00")
FINAL_TIME_UTC = datetime.fromisoformat("2026-10-04T10:00:00+00:00")
AUTOPILOT_STOP_TIME_UTC = datetime.fromisoformat("2026-10-04T10:15:00+00:00")

DENSE_OFFSET = Decimal("0.02")
DENSE_V2_OFFSET = Decimal("0.01")
DENSE_V3_OFFSET = Decimal("0.02")
DENSE_QTY_SAFETY = Decimal("0.995")
DENSE_FUNDS_FACTOR = Decimal("1.05")
DENSE_MAX_DYNAMIC_KEYS = 60000
DENSE_V2_BOOST_TOTAL_COPIES = 8
DENSE_V2_BOOST_EXTRA_COPIES = DENSE_V2_BOOST_TOTAL_COPIES - 1
DENSE_V2_RESERVE_TARGET_PAIRS = 16
DENSE_V3_TOTAL_COPIES_PER_SIDE = 8
DENSE_V3_EXTRA_COPY_SETS = DENSE_V3_TOTAL_COPIES_PER_SIDE - 1
DENSE_V3_RESERVE_TARGET_SETS = 16

# V4 keeps the V3 "every referee sweep" coverage and 8 copies per side,
# but changes quote construction to the live competitor regime seen in the
# public room: deep long quote plus a short-side clawback ladder.
DENSE_V4_TOTAL_COPIES_PER_SIDE = 8
DENSE_V4_LONG_OFFSET = Decimal("0.05")
DENSE_V4_SHORT_OFFSETS = (
    Decimal("0.01"), Decimal("0.01"), Decimal("0.01"),
    Decimal("0.017"), Decimal("0.017"),
    Decimal("0.02"), Decimal("0.02"), Decimal("0.02"),
)
# These are cash-usage safety multipliers for the close≈ref sizing model.
# Aggressive +1% copies maximize size; deeper rungs deliberately keep more
# free cash so they tolerate a larger adverse within-sweep move before a
# funds void.
DENSE_V4_SHORT_SAFETIES = (
    Decimal("0.995"), Decimal("0.995"), Decimal("0.995"),
    Decimal("0.99"), Decimal("0.99"),
    Decimal("0.98"), Decimal("0.98"), Decimal("0.98"),
)

# V4.1 is a read-only research grid on this review branch. It is NOT wired into
# dense_submit_pending/autopilot. The eight bands keep one median/aggressive
# copy and progressively widen historical close/ref survival coverage.
DENSE_V41_LOOKBACK = 576
DENSE_V41_QUANTILE_BANDS = (
    (Decimal("0.40"), Decimal("0.60")),
    (Decimal("0.25"), Decimal("0.75")),
    (Decimal("0.15"), Decimal("0.85")),
    (Decimal("0.09"), Decimal("0.91")),
    (Decimal("0.05"), Decimal("0.95")),
    (Decimal("0.025"), Decimal("0.975")),
    (Decimal("0.005"), Decimal("0.995")),
    (Decimal("0.00"), Decimal("1.00")),
)

# V4.2 is a read-only frontier optimizer. It searches future fresh-account
# V4-style pairs against a static current-podium scenario and historical
# settlement-move distribution. Nothing here is wired to autopilot.
DENSE_V42_LONG_OFFSETS = (
    Decimal("0.01"), Decimal("0.02"), Decimal("0.03"),
    Decimal("0.04"), Decimal("0.05"),
)
DENSE_V42_SHORT_OFFSETS = DENSE_V42_LONG_OFFSETS
DENSE_V42_LONG_FRACTIONS = (Decimal("1.00"), Decimal("0.97"))
DENSE_V42_GREEDY_MOVE_SCENARIOS = 41
DENSE_V42_DEFAULT_START = Decimal("220")
DENSE_V42_DEFAULT_END = Decimal("245")
DENSE_V42_DEFAULT_STEP = Decimal("0.50")

# V5a is a conservative profit-harvest layer on top of V4. It never replaces
# the every-sweep entry engine. At most two copy-pairs from the same V4 cohort
# are harvested, leaving at least six copies open for continued frontier
# exposure.
V5A_MIN_SCORE = Decimal("180")
V5A_FIRST_TRIGGER_RATIO = Decimal("0.25")
V5A_SECOND_TRIGGER_RATIO = Decimal("0.45")
V5A_SECOND_MIN_SCORE = Decimal("300")
V5A_MAX_HARVESTS_PER_COHORT = 2
V5A_BOOT_FEE_BUFFER_PCT = Decimal("0.05")
V5A_BOOT_EXTRA_SAFETY = Decimal("1.10")

# V5b turns a flat, realized-profit V5a winner back into a small opposite-side
# position. Position size is capped by the realized-profit cushion so opening
# and closing fees do not immediately consume the original 10,000 POLF base.
V5B_MIN_SEED_SCORE = Decimal("40")
V5B_ENTRY_FEE_FRACTION = Decimal("0.45")
V5B_TAKE_GAIN = Decimal("30")
V5B_STOP_SCORE = Decimal("-25")
V5B_FEEDERS = 2
V5B_MAX_ACTIVE = 1
V5B_MIN_QTY = Decimal("0.10")
V5B_NO_NEW_AFTER_SWEEP = 2554

# Referee unlists a quiet private room after 12 sweeps (one hour). Refresh the
# room registration before that deadline so an unnoticed quiet period cannot
# make later owner registrations/trades invisible to the referee.
DENSE_ROOM_REFRESH_SWEEPS = 8

# Review hotfix gates. Keep new V5 overlays off until their economics are
# revalidated against the official fold; already-open actions can still be
# managed to completion.
V5A_REVIEW_PAUSE_NEW = True
V5B_REVIEW_PAUSE_NEW = True
V5B_STOP_RETAIN_RATIO = Decimal("0.85")
V5B_STOP_FLOOR = Decimal("20")


def b58(raw: bytes) -> str:
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, rem = divmod(n, 58)
        out = B58[rem] + out
    return out


def did_from_seed(seed_hex: str) -> str:
    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex))
    pub = key.public_key().public_bytes_raw()
    return "did:key:z" + b58(MULTICODEC_ED25519 + pub)


def sign(seed_hex: str, message: str) -> str:
    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex))
    sig = key.sign(message.encode("utf-8"))
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")


def compact(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def canonical_terms(terms: dict) -> str:
    return json.dumps(terms, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_state() -> dict:
    if not STATE_PATH.exists():
        raise SystemExit(f"missing {STATE_PATH}; run init first")
    mode = stat.S_IMODE(STATE_PATH.stat().st_mode)
    if mode & 0o077:
        raise SystemExit(f"{STATE_PATH} permissions are {oct(mode)}; require 0600")
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    os.chmod(tmp, 0o600)
    tmp.replace(STATE_PATH)
    os.chmod(STATE_PATH, 0o600)


def make_labels() -> list[str]:
    labels = [f"BASE-B{i}" for i in range(4)]
    for i in range(1, 17):
        labels += [f"TIME-{i:02d}-L", f"TIME-{i:02d}-S"]
    labels += [f"BR-{i:02d}" for i in range(1, 17)]
    assert len(labels) == 52
    return labels


def cmd_init(_args) -> None:
    if STATE_PATH.exists():
        raise SystemExit(f"refusing to overwrite existing {STATE_PATH}")
    keys = {}
    for label in make_labels():
        seed = secrets.token_hex(32)
        keys[label] = {
            "seed": seed,
            "did": did_from_seed(seed),
            "nonces": {},
        }
    controller_did = keys["BASE-B0"]["did"]
    suffix = hashlib.sha256(controller_did.encode()).hexdigest()[:10]
    state = {
        "season": SEASON,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "room": f"cc-lxx-{suffix}",
        "controller": "BASE-B0",
        "keys": keys,
        "static": {},
        "bracket": {"round": 0, "pairs": []},
    }
    save_state(state)
    print(f"created 52 keys in {STATE_PATH}")
    print("controller:", controller_did)
    print("room:", state["room"])
    print("private seeds were written only to the local 0600 file")


def next_nonce(state: dict, label: str, room: str) -> str:
    k = state["keys"][label]
    last = int(k["nonces"].get(room, 0))
    now = int(time.time() * 1000)
    n = max(now, last + 1)
    k["nonces"][room] = n
    save_state(state)
    return str(n)


def http_post_json(url: str, body: dict, timeout=15) -> str:
    data = json.dumps(body, separators=(",", ":")).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "close-call-fleet/1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def http_get(url: str, timeout=15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "close-call-fleet/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode(errors="replace")


def post_signed(state: dict, room: str, label: str, text: str) -> str:
    key = state["keys"][label]
    nonce = next_nonce(state, label, room)
    sig = sign(key["seed"], f"{room}|{nonce}|{text}")
    response = http_post_json(
        f"{BASE}/r/{room}",
        {"did": key["did"], "sig": sig, "nonce": nonce, "text": text},
    )
    # A successful write makes any cached room export stale immediately.
    _EXPORT_CACHE.pop(room, None)
    return response


def owner_text(did: str) -> str:
    return compact({"t": "owner", "season": SEASON, "key": did})


def room_text(room: str) -> str:
    return compact({"t": "room", "season": SEASON, "room": room})


_EXPORT_CACHE: dict[str, tuple[float, list[dict]]] = {}
EXPORT_CACHE_TTL_S = 5.0


def parse_export(room: str) -> list[dict]:
    now = time.monotonic()
    cached = _EXPORT_CACHE.get(room)
    if cached and now - cached[0] <= EXPORT_CACHE_TTL_S:
        return cached[1]

    body = http_get(f"{BASE}/r/{room}/export")
    out = []
    for line in body.splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            txt = rec.get("text")
            payload = json.loads(txt) if isinstance(txt, str) and txt.startswith("{") else None
            if isinstance(payload, dict):
                rec["_payload"] = payload
            out.append(rec)
        except Exception:
            continue

    _EXPORT_CACHE[room] = (now, out)
    return out


def latest_payload(room: str, kind: str | None = None) -> dict | None:
    rows = parse_export(room)
    for rec in reversed(rows):
        p = rec.get("_payload")
        if not isinstance(p, dict):
            continue
        if kind is None or p.get("t") == kind:
            return p
    return None


def contains_exact(value, needle: str) -> bool:
    if isinstance(value, str):
        return value == needle
    if isinstance(value, (list, tuple, set)):
        return any(contains_exact(item, needle) for item in value)
    if isinstance(value, dict):
        return needle in value or any(contains_exact(item, needle) for item in value.values())
    return False


def room_seen(room: str) -> bool:
    """Reconstruct latest referee listing state with exact room matching.

    This is intentionally a slow historical helper. The hot autopilot path uses
    the cached state updated once from the latest flow in room maintenance.
    """
    listed = False
    observed = False
    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        if contains_exact(p.get("rooms"), room):
            listed = True
            observed = True
        if contains_exact(p.get("unlisted"), room):
            listed = False
            observed = True
    return listed if observed else False


def collect_dids(value, out: set[str]) -> None:
    if isinstance(value, str):
        if value.startswith("did:key:z"):
            out.add(value)
        return
    if isinstance(value, list):
        for item in value:
            collect_dids(item, out)
        return
    if isinstance(value, dict):
        for item in value.values():
            collect_dids(item, out)


def add_dynamic_key(state: dict, label: str) -> dict:
    if label in state["keys"]:
        return state["keys"][label]
    dynamic_count = sum(1 for k in state["keys"] if k.startswith("DENSE-"))
    if dynamic_count >= DENSE_MAX_DYNAMIC_KEYS:
        raise RuntimeError(f"dense dynamic key safety cap reached: {dynamic_count}")
    seed = secrets.token_hex(32)
    item = {"seed": seed, "did": did_from_seed(seed), "nonces": {}}
    state["keys"][label] = item
    save_state(state)
    return item


def latest_flow_and_state() -> tuple[dict | None, dict | None]:
    return latest_payload("d-close1-flow", "flow"), latest_payload("d-close1-state", "state")


def flow_misses_room(flow: dict | None, room: str) -> bool:
    if not isinstance(flow, dict):
        return True
    return contains_exact(flow.get("missed") or [], room)


def flow_lists_room(flow: dict | None, room: str) -> bool:
    if not isinstance(flow, dict):
        return False
    rooms = flow.get("rooms")
    if isinstance(rooms, list):
        return room in rooms
    if isinstance(rooms, dict):
        return room in rooms or room in rooms.values()
    try:
        return room in json.dumps(rooms, separators=(",", ":"), ensure_ascii=False)
    except Exception:
        return False


def room_recent_activity_age_s(room: str) -> int | None:
    try:
        rows = parse_export(room)
    except Exception:
        return None
    for rec in reversed(rows):
        ts = rec.get("ts")
        if not isinstance(ts, str):
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
        except Exception:
            continue
    return None


def room_registration_confirmed(state: dict) -> bool:
    """Fast cached room state.

    dense_room_maintenance refreshes this cache from the latest referee flow.
    Avoid re-downloading the multi-megabyte flow export from every helper call.
    """
    return bool((state.get("dense") or {}).get("room_registration_confirmed"))


def dense_qty(ref_px: Decimal) -> Decimal:
    q = DENSE_QTY_SAFETY * Decimal("10000") / (ref_px * DENSE_FUNDS_FACTOR)
    return q.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def dense_offset(state: dict) -> Decimal:
    dense = state.get("dense") or {}
    if dense.get("v4_enabled"):
        return Decimal(str(dense.get("v4_reference_offset") or DENSE_V3_OFFSET))
    if dense.get("v3_enabled"):
        return Decimal(str(dense.get("v3_offset") or DENSE_V3_OFFSET))
    if dense.get("v2_enabled"):
        return Decimal(str(dense.get("v2_offset") or DENSE_V2_OFFSET))
    return Decimal(str(dense.get("offset") or DENSE_OFFSET))


def dense_prices(ref_px: Decimal, offset: Decimal) -> tuple[Decimal, Decimal]:
    cent = Decimal("0.01")
    low = (ref_px * (Decimal("1") - offset)).quantize(cent, rounding=ROUND_DOWN)
    high = (ref_px * (Decimal("1") + offset)).quantize(cent, rounding=ROUND_DOWN)
    return low, high


def dense_ref_bounds(dense: dict) -> tuple[Decimal | None, Decimal | None]:
    refs = []
    for ticket in dense.get("tickets") or []:
        try:
            refs.append(Decimal(str(ticket.get("ref"))))
        except Exception:
            pass
    for ticket in dense.get("boost_tickets") or []:
        try:
            refs.append(Decimal(str(ticket.get("ref"))))
        except Exception:
            pass
    if not refs:
        return None, None
    return min(refs), max(refs)


def dense_v2_init_bounds(dense: dict) -> None:
    if dense.get("historical_low_ref") is not None and dense.get("historical_high_ref") is not None:
        return
    low, high = dense_ref_bounds(dense)
    if low is not None:
        dense["historical_low_ref"] = str(low)
    if high is not None:
        dense["historical_high_ref"] = str(high)


def dense_v2_extreme_sides(state: dict, ref_px: Decimal) -> list[str]:
    dense = state.setdefault("dense", {})
    if not dense.get("v2_enabled"):
        return []
    dense_v2_init_bounds(dense)
    sides = []
    low = dense.get("historical_low_ref")
    high = dense.get("historical_high_ref")
    if low is None or ref_px < Decimal(str(low)):
        sides.append("long")
    if high is None or ref_px > Decimal(str(high)):
        sides.append("short")
    return sides


def dense_v2_update_bounds(state: dict, ref_px: Decimal) -> None:
    dense = state.setdefault("dense", {})
    dense_v2_init_bounds(dense)
    low = dense.get("historical_low_ref")
    high = dense.get("historical_high_ref")
    if low is None or ref_px < Decimal(str(low)):
        dense["historical_low_ref"] = str(ref_px)
    if high is None or ref_px > Decimal(str(high)):
        dense["historical_high_ref"] = str(ref_px)
    save_state(state)


def dense_v2_ready_reserve(dense: dict, sweep: int) -> list[dict]:
    return [
        item for item in (dense.get("boost_reserve") or [])
        if item.get("status") == "registered"
        and int(item.get("ready_after_sweep", 10**9)) <= int(sweep)
    ]


def dense_v2_maintain_reserve(state: dict, sweep: int) -> dict | None:
    dense = state.setdefault("dense", {})
    if not dense.get("v2_enabled") or not room_registration_confirmed(state):
        return None

    reserve = dense.setdefault("boost_reserve", [])
    available = [x for x in reserve if x.get("status") == "registered"]
    target = int(dense.get("v2_reserve_target_pairs") or DENSE_V2_RESERVE_TARGET_PAIRS)
    need = max(0, target - len(available))
    if need <= 0:
        return None

    created = []
    for _ in range(need):
        idx = int(dense.get("boost_next_index", 1))
        dense["boost_next_index"] = idx + 1
        base = f"DENSE-BOOST-{idx:05d}"
        target_label = f"{base}-T"
        feeder_label = f"{base}-F"
        add_dynamic_key(state, target_label)
        add_dynamic_key(state, feeder_label)

        regs = {}
        for role, label in (("target", target_label), ("feeder", feeder_label)):
            did = state["keys"][label]["did"]
            ack = post_signed(state, state["room"], label, owner_text(did))
            regs[role] = {
                "did": did,
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "ack": ack.strip().splitlines()[0] if ack.strip() else "",
            }
            time.sleep(0.05)

        item = {
            "index": idx,
            "target": target_label,
            "feeder": feeder_label,
            "status": "registered",
            "registered_sweep": int(sweep),
            "ready_after_sweep": int(sweep) + 1,
            "registrations": regs,
        }
        reserve.append(item)
        created.append(idx)
        dense["boost_reserve"] = reserve
        save_state(state)

    return {
        "event": "dense_v2_reserve_filled",
        "created_pairs": len(created),
        "reserve_pairs": len([x for x in reserve if x.get("status") == "registered"]),
        "indices": created,
    }


def dense_v2_submit_boost(state: dict, pr: dict, side: str, qty: Decimal, px: Decimal) -> dict:
    dense = state.setdefault("dense", {})
    reserve = dense_v2_ready_reserve(dense, pr["n"])
    need = int(dense.get("v2_boost_extra_copies") or DENSE_V2_BOOST_EXTRA_COPIES)
    selected = reserve[:need]
    submitted = []
    errors = []

    for copy_no, item in enumerate(selected, start=2):
        target = item["target"]
        feeder = item["feeder"]
        tid = f"x{item['index']:05d}{side[0]}-{int(time.time())}-{copy_no}"
        try:
            if side == "long":
                text = build_trade(
                    state, state["room"], feeder, target,
                    "sell", qty, px, pr["n"] + 2, tid,
                )
                ack = post_signed(state, state["room"], feeder, text)
            else:
                text = build_trade(
                    state, state["room"], target, feeder,
                    "sell", qty, px, pr["n"] + 2, tid,
                )
                ack = post_signed(state, state["room"], target, text)

            item["status"] = "consumed"
            item["consumed_at"] = datetime.now(timezone.utc).isoformat()
            item["trade_id"] = tid
            item["side"] = side
            item["sweep"] = pr["n"]
            item["ref"] = str(pr["px"])
            item["px"] = str(px)
            item["qty"] = str(qty)

            rec = {
                "reserve_index": item["index"],
                "copy_no": copy_no,
                "side": side,
                "target": target,
                "feeder": feeder,
                "trade_id": tid,
                "sweep": pr["n"],
                "ref": str(pr["px"]),
                "px": str(px),
                "qty": str(qty),
                "ack": ack.strip().splitlines()[0] if ack.strip() else "",
            }
            dense.setdefault("boost_tickets", []).append(rec)
            submitted.append(rec)
            save_state(state)
            time.sleep(0.05)
        except Exception as e:
            errors.append({
                "reserve_index": item.get("index"),
                "side": side,
                "error": str(e),
            })

    result = {
        "side": side,
        "requested_extra_copies": need,
        "submitted_extra_copies": len(submitted),
        "reserve_shortage": max(0, need - len(selected)),
        "errors": errors,
        "tickets": submitted,
    }
    dense["last_boost"] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "sweep": pr["n"],
        "ref": str(pr["px"]),
        **result,
    }
    save_state(state)
    return result


def dense_v3_ready_reserve(dense: dict, sweep: int) -> list[dict]:
    return [
        item for item in (dense.get("v3_reserve") or [])
        if item.get("status") == "registered"
        and int(item.get("ready_after_sweep", 10**9)) <= int(sweep)
    ]


def dense_v3_maintain_reserve(state: dict, sweep: int) -> dict | None:
    dense = state.setdefault("dense", {})
    if not (dense.get("v3_enabled") or dense.get("v4_enabled")) or not room_registration_confirmed(state):
        return None

    reserve = dense.setdefault("v3_reserve", [])
    available = [x for x in reserve if x.get("status") == "registered"]
    target = int(dense.get("v3_reserve_target_sets") or DENSE_V3_RESERVE_TARGET_SETS)
    need = max(0, target - len(available))
    if need <= 0:
        return None

    created = []
    for _ in range(need):
        idx = int(dense.get("v3_reserve_next_index", 1))
        dense["v3_reserve_next_index"] = idx + 1
        base = f"DENSE-V3-{idx:05d}"
        labels = {
            "long": f"{base}-L",
            "short": f"{base}-S",
            "feeder": f"{base}-F",
        }
        for label in labels.values():
            add_dynamic_key(state, label)

        regs = {}
        for role, label in labels.items():
            did = state["keys"][label]["did"]
            ack = post_signed(state, state["room"], label, owner_text(did))
            regs[role] = {
                "did": did,
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "ack": ack.strip().splitlines()[0] if ack.strip() else "",
            }
            time.sleep(0.05)

        item = {
            "index": idx,
            "labels": labels,
            "status": "registered",
            "registered_sweep": int(sweep),
            "ready_after_sweep": int(sweep) + 1,
            "registrations": regs,
            "trades": {},
        }
        reserve.append(item)
        created.append(idx)
        dense["v3_reserve"] = reserve
        save_state(state)

    return {
        "event": "dense_v3_reserve_filled",
        "created_sets": len(created),
        "reserve_sets": len([x for x in reserve if x.get("status") == "registered"]),
        "indices": created,
    }


def dense_v3_submit_multiplicity(
    state: dict,
    pr: dict,
    qty: Decimal,
    low: Decimal,
    high: Decimal,
) -> dict:
    dense = state.setdefault("dense", {})
    need = int(dense.get("v3_extra_copy_sets") or DENSE_V3_EXTRA_COPY_SETS)
    ready = dense_v3_ready_reserve(dense, pr["n"])
    selected = ready[:need]
    submitted = []
    errors = []

    for copy_no, item in enumerate(selected, start=2):
        labels = item["labels"]
        item["status"] = "in_progress"
        item["started_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        pair_record = {
            "reserve_index": item["index"],
            "copy_no": copy_no,
            "sweep": pr["n"],
            "ref": str(pr["px"]),
            "qty": str(qty),
            "low": str(low),
            "high": str(high),
            "long": labels["long"],
            "short": labels["short"],
            "feeder": labels["feeder"],
            "trades": {},
        }
        try:
            long_tid = f"v3{item['index']:05d}l-{int(time.time())}-{copy_no}"
            long_text = build_trade(
                state,
                state["room"],
                labels["feeder"],
                labels["long"],
                "sell",
                qty,
                low,
                pr["n"] + 2,
                long_tid,
            )
            long_ack = post_signed(state, state["room"], labels["feeder"], long_text)
            pair_record["trades"]["long"] = {
                "trade_id": long_tid,
                "px": str(low),
                "ack": long_ack.strip().splitlines()[0] if long_ack.strip() else "",
            }
            save_state(state)
            time.sleep(0.05)

            short_tid = f"v3{item['index']:05d}s-{int(time.time())}-{copy_no}"
            short_text = build_trade(
                state,
                state["room"],
                labels["short"],
                labels["feeder"],
                "sell",
                qty,
                high,
                pr["n"] + 2,
                short_tid,
            )
            short_ack = post_signed(state, state["room"], labels["short"], short_text)
            pair_record["trades"]["short"] = {
                "trade_id": short_tid,
                "px": str(high),
                "ack": short_ack.strip().splitlines()[0] if short_ack.strip() else "",
            }

            item["status"] = "consumed"
            item["consumed_at"] = datetime.now(timezone.utc).isoformat()
            item["sweep"] = pr["n"]
            item["ref"] = str(pr["px"])
            item["qty"] = str(qty)
            item["low"] = str(low)
            item["high"] = str(high)
            item["trades"] = pair_record["trades"]
            dense.setdefault("v3_tickets", []).append(pair_record)
            submitted.append(pair_record)
            save_state(state)
            time.sleep(0.05)
        except Exception as e:
            item["status"] = "partial_error"
            item["error_at"] = datetime.now(timezone.utc).isoformat()
            item["error"] = str(e)
            item["partial_trades"] = pair_record.get("trades") or {}
            save_state(state)
            errors.append({
                "reserve_index": item.get("index"),
                "copy_no": copy_no,
                "error": str(e),
                "partial_trades": pair_record.get("trades") or {},
            })

    result = {
        "requested_extra_copy_sets": need,
        "submitted_extra_copy_sets": len(submitted),
        "total_long_copies": 1 + len(submitted),
        "total_short_copies": 1 + len(submitted),
        "reserve_shortage": max(0, need - len(selected)),
        "errors": errors,
        "tickets": submitted,
    }
    dense["last_v3_multiplicity"] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "sweep": pr["n"],
        "ref": str(pr["px"]),
        **result,
    }
    save_state(state)
    return result


def dense_v4_profile(copy_no: int) -> dict:
    if not 1 <= int(copy_no) <= DENSE_V4_TOTAL_COPIES_PER_SIDE:
        raise ValueError("V4 copy_no must be 1..8")
    idx = int(copy_no) - 1
    return {
        "copy_no": int(copy_no),
        "long_offset": DENSE_V4_LONG_OFFSET,
        "short_offset": DENSE_V4_SHORT_OFFSETS[idx],
        "safety": DENSE_V4_SHORT_SAFETIES[idx],
    }


def dense_v4_limit_bounds(pr: dict) -> tuple[Decimal, Decimal]:
    ref = pr["px"]
    raw_limits = (pr.get("raw") or {}).get("limits")
    if isinstance(raw_limits, (list, tuple)) and len(raw_limits) >= 2:
        try:
            return Decimal(str(raw_limits[0])), Decimal(str(raw_limits[1]))
        except Exception:
            pass
    cent = Decimal("0.01")
    low = (ref * Decimal("0.95")).quantize(cent, rounding=ROUND_CEILING)
    high = (ref * Decimal("1.05")).quantize(cent, rounding=ROUND_DOWN)
    return low, high


def dense_v4_plan_copy(pr: dict, copy_no: int) -> dict:
    """Build one paired V4 long/short copy.

    The target long buys at the exact lower referee limit when available.
    The target short sells on its ladder rung. Quantity is sized from the
    official fold's cash test assuming sweep close ~= current referee ref,
    then multiplied by the rung's cash safety. This is an execution sizing
    model, not a guarantee against arbitrarily large within-sweep moves.
    """
    ref = pr["px"]
    profile = dense_v4_profile(copy_no)
    lower_limit, upper_limit = dense_v4_limit_bounds(pr)
    cent = Decimal("0.01")

    # At the 5% lower boundary, rounding down can slip outside official limits.
    # Prefer the referee's posted lower limit; fallback uses ROUND_CEILING.
    low = lower_limit
    desired_high = (ref * (Decimal("1") + profile["short_offset"])).quantize(
        cent, rounding=ROUND_DOWN
    )
    high = min(desired_high, upper_limit)

    # Official clawback funds model at close ~= ref.
    # Long target is the taker/buyer of the low-priced trade.
    long_fee_per_contract = max(Decimal("0.01") * low, ref - low)
    long_required = low + long_fee_per_contract

    # Short target is the maker/seller of the high-priced trade.
    short_fee_per_contract = max(Decimal("0.01") * high, high - ref)
    short_required = high + short_fee_per_contract

    # The feeder opens the opposite short at low, then buys it back at high.
    # First trade collateral+fee plus the second trade's buyer fee must remain
    # payable before the close releases the feeder lot.
    feeder_open_fee = max(Decimal("0.01") * low, low - ref)
    feeder_close_fee = max(Decimal("0.01") * high, ref - high)
    feeder_required = low + feeder_open_fee + feeder_close_fee

    required_per_contract = max(long_required, short_required, feeder_required)
    qty = (
        profile["safety"] * Decimal("10000") / required_per_contract
    ).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    return {
        **profile,
        "ref": ref,
        "low": low,
        "high": high,
        "qty": qty,
        "required_per_contract": required_per_contract,
        "lower_limit": lower_limit,
        "upper_limit": upper_limit,
    }


def dense_v4_resume_partial_errors(state: dict, pr: dict) -> list[dict]:
    """Resume only missing legs from V4 reserve copies in the same sweep."""
    dense = state.setdefault("dense", {})
    resumed = []
    dirty = False
    for item in dense.get("v3_reserve") or []:
        if item.get("status") != "partial_error" or item.get("mode") != "v4":
            continue
        try:
            if int(item.get("sweep", -1)) != int(pr["n"]):
                item["status"] = "partial_expired"
                item["expired_at"] = datetime.now(timezone.utc).isoformat()
                dirty = True
                continue
            copy_no = int(item["copy_no"])
            qty = Decimal(str(item["qty"]))
            low = Decimal(str(item["low"]))
            high = Decimal(str(item["high"]))
            labels = item["labels"]
            trades = dict(item.get("partial_trades") or {})

            if "long" not in trades:
                tid = deterministic_trade_id("v4l", item["index"], pr["n"], copy_no)
                text = build_trade(
                    state, state["room"], labels["feeder"], labels["long"],
                    "sell", qty, low, pr["n"] + 2, tid,
                )
                ack = post_signed(state, state["room"], labels["feeder"], text)
                trades["long"] = {
                    "trade_id": tid, "px": str(low), "qty": str(qty),
                    "ack": ack.strip().splitlines()[0] if ack.strip() else "",
                }
                item["partial_trades"] = trades
                save_state(state)
                time.sleep(0.05)

            if "short" not in trades:
                tid = deterministic_trade_id("v4s", item["index"], pr["n"], copy_no)
                text = build_trade(
                    state, state["room"], labels["short"], labels["feeder"],
                    "sell", qty, high, pr["n"] + 2, tid,
                )
                ack = post_signed(state, state["room"], labels["feeder"], text)
                trades["short"] = {
                    "trade_id": tid, "px": str(high), "qty": str(qty),
                    "ack": ack.strip().splitlines()[0] if ack.strip() else "",
                }

            pair_record = {
                "reserve_index": item["index"],
                "copy_no": copy_no,
                "sweep": int(pr["n"]),
                "ref": str(item["ref"]),
                "long_offset": str(DENSE_V4_LONG_OFFSET),
                "short_offset": str(item["short_offset"]),
                "safety": str(item["safety"]),
                "qty": str(qty),
                "low": str(low),
                "high": str(high),
                "long": labels["long"],
                "short": labels["short"],
                "feeder": labels["feeder"],
                "trades": trades,
                "resumed": True,
            }
            item["status"] = "consumed"
            item["consumed_at"] = datetime.now(timezone.utc).isoformat()
            item["trades"] = trades
            dense.setdefault("v4_tickets", []).append(pair_record)
            resumed.append(pair_record)
            dirty = True
            save_state(state)
        except Exception as e:
            item["status"] = "partial_error"
            item["error_at"] = datetime.now(timezone.utc).isoformat()
            item["error"] = str(e)
            dirty = True
            save_state(state)
    if dirty:
        save_state(state)
    return resumed


def dense_v4_submit_multiplicity(state: dict, pr: dict) -> dict:
    dense = state.setdefault("dense", {})
    resumed = dense_v4_resume_partial_errors(state, pr)
    ready = dense_v3_ready_reserve(dense, pr["n"])
    # Baseline pending batch is V4 copy #1. Reserve sets provide copies #2..#8.
    need = DENSE_V4_TOTAL_COPIES_PER_SIDE - 1
    remaining_need = max(0, need - len(resumed))
    selected = ready[:remaining_need]
    submitted = list(resumed)
    errors = []

    resumed_copy_nos = {int(x.get("copy_no", -1)) for x in resumed}
    fresh_copy_nos = [
        copy_no for copy_no in range(2, DENSE_V4_TOTAL_COPIES_PER_SIDE + 1)
        if copy_no not in resumed_copy_nos
    ][:len(selected)]

    for copy_no, item in zip(fresh_copy_nos, selected):
        labels = item["labels"]
        plan = dense_v4_plan_copy(pr, copy_no)
        item["status"] = "in_progress"
        item["started_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)

        pair_record = {
            "reserve_index": item["index"],
            "copy_no": copy_no,
            "sweep": pr["n"],
            "ref": str(pr["px"]),
            "long_offset": str(plan["long_offset"]),
            "short_offset": str(plan["short_offset"]),
            "safety": str(plan["safety"]),
            "qty": str(plan["qty"]),
            "low": str(plan["low"]),
            "high": str(plan["high"]),
            "long": labels["long"],
            "short": labels["short"],
            "feeder": labels["feeder"],
            "trades": {},
        }
        try:
            long_tid = deterministic_trade_id("v4l", item["index"], pr["n"], copy_no)
            long_text = build_trade(
                state,
                state["room"],
                labels["feeder"],
                labels["long"],
                "sell",
                plan["qty"],
                plan["low"],
                pr["n"] + 2,
                long_tid,
            )
            long_ack = post_signed(state, state["room"], labels["feeder"], long_text)
            pair_record["trades"]["long"] = {
                "trade_id": long_tid,
                "px": str(plan["low"]),
                "qty": str(plan["qty"]),
                "ack": long_ack.strip().splitlines()[0] if long_ack.strip() else "",
            }
            save_state(state)
            time.sleep(0.05)

            short_tid = deterministic_trade_id("v4s", item["index"], pr["n"], copy_no)
            short_text = build_trade(
                state,
                state["room"],
                labels["short"],
                labels["feeder"],
                "sell",
                plan["qty"],
                plan["high"],
                pr["n"] + 2,
                short_tid,
            )
            short_ack = post_signed(state, state["room"], labels["feeder"], short_text)
            pair_record["trades"]["short"] = {
                "trade_id": short_tid,
                "px": str(plan["high"]),
                "qty": str(plan["qty"]),
                "ack": short_ack.strip().splitlines()[0] if short_ack.strip() else "",
            }

            item["status"] = "consumed"
            item["consumed_at"] = datetime.now(timezone.utc).isoformat()
            item["mode"] = "v4"
            item["sweep"] = pr["n"]
            item["ref"] = str(pr["px"])
            item["qty"] = str(plan["qty"])
            item["low"] = str(plan["low"])
            item["high"] = str(plan["high"])
            item["short_offset"] = str(plan["short_offset"])
            item["safety"] = str(plan["safety"])
            item["trades"] = pair_record["trades"]
            dense.setdefault("v4_tickets", []).append(pair_record)
            submitted.append(pair_record)
            save_state(state)
            time.sleep(0.05)
        except Exception as e:
            item["status"] = "partial_error"
            item["error_at"] = datetime.now(timezone.utc).isoformat()
            item["error"] = str(e)
            item["partial_trades"] = pair_record.get("trades") or {}
            item["mode"] = "v4"
            item["sweep"] = pr["n"]
            item["copy_no"] = copy_no
            item["ref"] = str(pr["px"])
            item["qty"] = str(plan["qty"])
            item["low"] = str(plan["low"])
            item["high"] = str(plan["high"])
            item["short_offset"] = str(plan["short_offset"])
            item["safety"] = str(plan["safety"])
            save_state(state)
            errors.append({
                "reserve_index": item.get("index"),
                "copy_no": copy_no,
                "error": str(e),
                "partial_trades": pair_record.get("trades") or {},
            })

    result = {
        "requested_extra_copy_sets": need,
        "submitted_extra_copy_sets": len(submitted),
        "total_long_copies": 1 + len(submitted),
        "total_short_copies": 1 + len(submitted),
        "reserve_shortage": max(0, need - len(submitted)),
        "errors": errors,
        "tickets": submitted,
    }
    dense["last_v4_multiplicity"] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "sweep": pr["n"],
        "ref": str(pr["px"]),
        **result,
    }
    save_state(state)
    return result


def _pnl_marks_by_sweep() -> dict[int, Decimal]:
    out = {}
    for rec in parse_export("d-close1-pnl"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "pnl":
            continue
        try:
            out[int(p["n"])] = Decimal(str(p["mark"]))
        except Exception:
            continue
    return out


def _price_refs_by_sweep() -> dict[int, Decimal]:
    out = {}
    for rec in parse_export("d-close1-price"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "price":
            continue
        try:
            out[int(p["n"])] = Decimal(str((p.get("ref") or {})["px"]))
        except Exception:
            continue
    return out


def _flow_omitted_at_sweep(sweep: int) -> dict[str, int]:
    out = {"settled": 0, "void": 0, "mints": 0}
    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        try:
            if int(p.get("n")) != int(sweep):
                continue
        except Exception:
            continue
        omitted = p.get("omitted") or {}
        if not isinstance(omitted, dict):
            return out
        for name in out:
            try:
                out[name] = int(omitted.get(name) or 0)
            except Exception:
                out[name] = 0
        return out
    return out


def deterministic_trade_id(prefix: str, *parts) -> str:
    """Stable <=64-char id for one logical strategy action.

    This reduces accidental duplicate IDs but is not a full write-ahead
    exactly-once protocol by itself; callers still persist submission state.
    """
    raw = "|".join([str(prefix), *(str(x) for x in parts)])
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    clean_prefix = "".join(ch for ch in str(prefix) if ch.isalnum() or ch in "_-")[:40] or "cc"
    return f"{clean_prefix}-{digest}"


def _flow_room_missed_at_sweep(room: str, sweep: int) -> bool:
    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        try:
            if int(p.get("n")) != int(sweep):
                continue
        except Exception:
            continue
        return contains_exact(p.get("missed") or [], room)
    return False


def _v5a_missed_sweeps(room: str) -> set[int]:
    out = set()
    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        if not contains_exact(p.get("missed") or [], room):
            continue
        try:
            out.add(int(p["n"]))
        except Exception:
            pass
    return out


def _v5a_visible_outcomes(trade_ids: set[str]) -> dict[str, str]:
    out = {}
    if not trade_ids:
        return out
    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        for tid in trade_ids:
            if tid in out:
                continue
            if contains_value(p.get("settled"), tid):
                out[tid] = "settled"
            elif contains_value(p.get("void"), tid):
                out[tid] = "void"
    return out


def _v5a_v4_pairs(state: dict) -> list[dict]:
    dense = state.get("dense") or {}
    out = []

    for ticket in dense.get("tickets") or []:
        if ticket.get("mode") != "v4" or ticket.get("status") != "submitted":
            continue
        labels = ticket.get("labels") or {}
        trades = ticket.get("trades") or {}
        if not all(k in labels for k in ("long", "short")):
            continue
        try:
            out.append({
                "pair_id": f"base-{int(ticket['index']):05d}",
                "cohort_sweep": int(ticket["trade_sweep"]),
                "copy_no": 1,
                "long": labels["long"],
                "short": labels["short"],
                "qty": Decimal(str(ticket["qty"])),
                "low": Decimal(str(ticket["low"])),
                "high": Decimal(str(ticket["high"])),
                "long_trade_id": (trades.get("long") or {}).get("trade_id"),
                "short_trade_id": (trades.get("short") or {}).get("trade_id"),
                "source": "baseline",
            })
        except Exception:
            continue

    for ticket in dense.get("v4_tickets") or []:
        try:
            out.append({
                "pair_id": f"v4-{int(ticket['reserve_index']):05d}",
                "cohort_sweep": int(ticket["sweep"]),
                "copy_no": int(ticket["copy_no"]),
                "long": str(ticket["long"]),
                "short": str(ticket["short"]),
                "qty": Decimal(str(ticket["qty"])),
                "low": Decimal(str(ticket["low"])),
                "high": Decimal(str(ticket["high"])),
                "long_trade_id": ((ticket.get("trades") or {}).get("long") or {}).get("trade_id"),
                "short_trade_id": ((ticket.get("trades") or {}).get("short") or {}).get("trade_id"),
                "source": "reserve",
            })
        except Exception:
            continue

    return out


def _v5a_opening_state(pair: dict, settlement_close: Decimal) -> dict:
    """Reconstruct a fresh V4 target pair under the frozen official fold.

    V4 keys are fresh when the two opening trades are posted. The first trade is
    feeder sell -> long target at low; the second is short target sell -> feeder
    at high. This lets us deterministically check funds and reconstruct both
    target accounts once the next referee close is known.
    """
    q = pair["qty"]
    low = pair["low"]
    high = pair["high"]
    mint = Decimal("10000")
    fee_rate = Decimal("0.01")

    low_base = fee_rate * q * low
    feeder_sell_fee = max(low_base, (low - settlement_close) * q)
    long_buy_fee = max(low_base, (settlement_close - low) * q)

    feeder_cash = mint
    long_cash = mint
    if feeder_cash < q * low + feeder_sell_fee:
        return {"settled": False, "reason": "opening_feeder_low_funds"}
    if long_cash < q * low + long_buy_fee:
        return {"settled": False, "reason": "opening_long_funds"}

    feeder_cash -= q * low + feeder_sell_fee
    long_cash -= q * low + long_buy_fee

    high_base = fee_rate * q * high
    short_sell_fee = max(high_base, (high - settlement_close) * q)
    feeder_buy_fee = max(high_base, (settlement_close - high) * q)

    short_cash = mint
    if short_cash < q * high + short_sell_fee:
        return {"settled": False, "reason": "opening_short_funds"}
    if feeder_cash < feeder_buy_fee:
        return {"settled": False, "reason": "opening_feeder_high_fee"}

    short_cash -= q * high + short_sell_fee
    feeder_cash -= feeder_buy_fee
    feeder_cash += q * (Decimal("2") * low - high)

    return {
        "settled": True,
        "settlement_close": settlement_close,
        "qty": q,
        "long_cash": long_cash,
        "short_cash": short_cash,
        "feeder_cash": feeder_cash,
        "long_pos": q,
        "short_pos": -q,
        "long_lot_px": low,
        "short_lot_px": high,
        "opening_fees": {
            "long": long_buy_fee,
            "short": short_sell_fee,
            "feeder_low": feeder_sell_fee,
            "feeder_high": feeder_buy_fee,
        },
    }


def _v5a_scores(open_state: dict, mark: Decimal) -> dict:
    q = Decimal(str(open_state["qty"]))
    long_cash = Decimal(str(open_state["long_cash"]))
    short_cash = Decimal(str(open_state["short_cash"]))
    low = Decimal(str(open_state["long_lot_px"]))
    high = Decimal(str(open_state["short_lot_px"]))
    long_pos = Decimal(str(open_state["long_pos"]))
    short_pos = Decimal(str(open_state["short_pos"]))

    long_value = long_cash + max(long_pos, Decimal("0")) * mark
    if long_pos < 0:
        long_value += -long_pos * (Decimal("2") * low - mark)

    short_value = short_cash
    if short_pos < 0:
        short_value += -short_pos * (Decimal("2") * high - mark)
    elif short_pos > 0:
        short_value += short_pos * mark

    return {
        "long": long_value - Decimal("10000"),
        "short": short_value - Decimal("10000"),
    }


def _v5a_prize_cutoff() -> Decimal | None:
    pnl = latest_payload("d-close1-pnl", "pnl")
    pairs = _pnl_pairs(pnl)
    if len(pairs) < 3:
        return None
    return pairs[2][1]


def _v5a_harvest_thresholds() -> tuple[Decimal, Decimal]:
    cutoff = _v5a_prize_cutoff()
    if cutoff is None:
        return V5A_MIN_SCORE, V5A_SECOND_MIN_SCORE
    first = max(V5A_MIN_SCORE, cutoff * V5A_FIRST_TRIGGER_RATIO)
    second = max(V5A_SECOND_MIN_SCORE, cutoff * V5A_SECOND_TRIGGER_RATIO)
    return first, second


def _v5a_bootstrap_qty(
    q: Decimal,
    long_cash: Decimal,
    short_cash: Decimal,
    short_lot_px: Decimal,
    harvest_px: Decimal,
) -> Decimal | None:
    """Choose a small first close that self-funds the rest of the close.

    The protocol checks fee cash before releasing collateral. We reserve enough
    cash for a hypothetical 5% close-price gap on the remaining position. The
    first tranche must itself be affordable under the same 5% fee buffer.
    """
    fee_buf = V5A_BOOT_FEE_BUFFER_PCT * harvest_px
    if fee_buf <= 0:
        return None

    long_release = harvest_px
    short_release = Decimal("2") * short_lot_px - harvest_px
    if long_release <= 0 or short_release <= 0:
        return None

    need_long = max(Decimal("0"), (fee_buf * q - long_cash) / long_release)
    need_short = max(Decimal("0"), (fee_buf * q - short_cash) / short_release)
    raw = max(Decimal("0.10"), need_long, need_short) * V5A_BOOT_EXTRA_SAFETY
    boot = raw.quantize(Decimal("0.01"), rounding=ROUND_CEILING)
    boot = min(boot, q)

    max_affordable = min(long_cash / fee_buf, short_cash / fee_buf, q)
    max_affordable = max_affordable.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    if boot < Decimal("0.10") or boot > max_affordable:
        return None
    return boot


def _v5a_apply_close(
    account_state: dict,
    qty: Decimal,
    px: Decimal,
    settlement_close: Decimal,
) -> dict:
    """Apply one long-sells-to-short close to reconstructed target accounts."""
    q_rem = Decimal(str(account_state["qty"]))
    if qty <= 0 or qty > q_rem:
        return {"settled": False, "reason": "bad_close_qty"}

    long_cash = Decimal(str(account_state["long_cash"]))
    short_cash = Decimal(str(account_state["short_cash"]))
    short_lot_px = Decimal(str(account_state["short_lot_px"]))

    base = Decimal("0.01") * qty * px
    seller_fee = max(base, (px - settlement_close) * qty)
    buyer_fee = max(base, (settlement_close - px) * qty)

    if long_cash < seller_fee:
        return {"settled": False, "reason": "harvest_long_fee_funds"}
    if short_cash < buyer_fee:
        return {"settled": False, "reason": "harvest_short_fee_funds"}

    long_cash -= seller_fee
    long_cash += qty * px

    short_cash -= buyer_fee
    short_cash += qty * (Decimal("2") * short_lot_px - px)

    left = q_rem - qty
    out = dict(account_state)
    out.update({
        "settled": True,
        "qty": str(left),
        "long_cash": str(long_cash),
        "short_cash": str(short_cash),
        "long_pos": str(left),
        "short_pos": str(-left),
    })
    return out


def _v5a_pair_snapshot(
    state: dict,
    pair: dict,
    refs: dict[int, Decimal],
    marks: dict[int, Decimal],
    missed_sweeps: set[int],
    visible_outcomes: dict[str, str],
    room_submissions: dict[str, dict],
    mark: Decimal,
) -> dict | None:
    submit_sweep = int(pair["cohort_sweep"])
    settlement_sweep = submit_sweep + 1
    # Official clawback uses the sweep close from d-close1-price.ref.px.
    # pnl.mark is the global board mark and must never substitute for it.
    settlement_close = refs.get(settlement_sweep)
    if settlement_close is None:
        return None
    if settlement_sweep in missed_sweeps:
        return None

    # Explicit void always wins. Compact flow can omit thousands of outcomes,
    # so an absent id cannot be treated as authoritative void/settled here.
    # The deterministic local fold below is used only when the room itself was
    # not missed; new V5a harvests are review-paused by default.
    for tid in (pair.get("long_trade_id"), pair.get("short_trade_id")):
        if not tid or visible_outcomes.get(tid) == "void":
            return None
        if visible_outcomes.get(tid) != "settled" and tid not in room_submissions:
            return None

    opening = _v5a_opening_state(pair, settlement_close)
    if not opening.get("settled"):
        return None
    scores = _v5a_scores(opening, mark)
    winner = "long" if scores["long"] >= scores["short"] else "short"
    return {
        "pair": pair,
        "opening": opening,
        "scores": scores,
        "winner": winner,
        "winner_score": scores[winner],
        "settlement_sweep": settlement_sweep,
        "settlement_close": settlement_close,
    }


def _v5a_candidates(state: dict, pr: dict | None = None) -> dict:
    dense = state.setdefault("dense", {})
    if pr is None:
        pr = fresh_price(max_age=10**9)
    pnl = latest_payload("d-close1-pnl", "pnl")
    try:
        mark = Decimal(str((pnl or {})["mark"]))
    except Exception:
        return {"mark": None, "first_threshold": None, "second_threshold": None, "candidates": []}

    refs = _price_refs_by_sweep()
    marks = _pnl_marks_by_sweep()
    pairs = _v5a_v4_pairs(state)
    missed_sweeps = _v5a_missed_sweeps(state["room"])
    trade_ids = {
        tid
        for pair in pairs
        for tid in (pair.get("long_trade_id"), pair.get("short_trade_id"))
        if tid
    }
    visible_outcomes = _v5a_visible_outcomes(trade_ids)
    room_submissions = trade_submissions_in_room(state["room"], trade_ids)

    first_threshold, second_threshold = _v5a_harvest_thresholds()
    harvested = dense.setdefault("v5a_harvested", {})
    active = dense.get("v5a_active")
    active_pair = active.get("pair_id") if isinstance(active, dict) else None

    by_cohort_harvested = Counter()
    for rec in harvested.values():
        try:
            by_cohort_harvested[int(rec["cohort_sweep"])] += 1
        except Exception:
            pass

    snaps = []
    for pair in pairs:
        if pair["pair_id"] in harvested or pair["pair_id"] == active_pair:
            continue
        snap = _v5a_pair_snapshot(
            state, pair, refs, marks, missed_sweeps, visible_outcomes, room_submissions, mark
        )
        if not snap:
            continue

        already = int(by_cohort_harvested.get(pair["cohort_sweep"], 0))
        allowed = 0
        if snap["winner_score"] >= first_threshold:
            allowed = 1
        if snap["winner_score"] >= second_threshold:
            allowed = V5A_MAX_HARVESTS_PER_COHORT
        if already >= allowed:
            continue

        snap["harvested_in_cohort"] = already
        snap["allowed_in_cohort"] = allowed
        snaps.append(snap)

    snaps.sort(key=lambda x: (x["winner_score"], -x["pair"]["copy_no"]), reverse=True)
    return {
        "sweep": pr["n"],
        "ref": pr["px"],
        "mark": mark,
        "first_threshold": first_threshold,
        "second_threshold": second_threshold,
        "candidates": snaps,
    }


def _v5a_submit_close(
    state: dict,
    pair: dict,
    qty: Decimal,
    pr: dict,
    prefix: str,
) -> dict:
    tid = deterministic_trade_id(
        "v5a", prefix, pair["pair_id"], pr["n"], str(qty), str(pr["px"])
    )
    text = build_trade(
        state,
        state["room"],
        pair["long"],
        pair["short"],
        "sell",
        qty,
        pr["px"],
        pr["n"] + 2,
        tid,
    )
    ack = post_signed(state, state["room"], pair["long"], text)
    return {
        "trade_id": tid,
        "qty": str(qty),
        "px": str(pr["px"]),
        "submission_sweep": int(pr["n"]),
        "maker": pair["long"],
        "taker": pair["short"],
        "ack": ack.strip().splitlines()[0] if ack.strip() else "",
    }


def dense_v5a_harvest_step(state: dict, pr: dict) -> dict | None:
    dense = state.setdefault("dense", {})
    if not dense.get("v5a_enabled") or not dense.get("v4_enabled"):
        return None

    flow, st = latest_flow_and_state()
    flow_n = int(flow["n"]) if isinstance(flow, dict) and flow.get("n") is not None else None
    state_n = int(st["n"]) if isinstance(st, dict) and st.get("n") is not None else None
    if flow_n != pr["n"] or state_n != pr["n"]:
        return None
    if not room_registration_confirmed(state) or flow_misses_room(flow, state["room"]):
        return None

    refs = _price_refs_by_sweep()
    active = dense.get("v5a_active")
    if isinstance(active, dict):
        stage = active.get("stage")
        if stage not in ("bootstrap_submitted", "finish_submitted"):
            return None
        action = active.get("action") or {}
        submit_sweep = int(action.get("submission_sweep", -1))
        if pr["n"] <= submit_sweep:
            return None

        settlement_close = refs.get(submit_sweep + 1)
        if settlement_close is None:
            return None
        if _flow_room_missed_at_sweep(state["room"], submit_sweep + 1):
            active["stage"] = "blocked_missed_settlement_sweep"
            active["blocked_at"] = datetime.now(timezone.utc).isoformat()
            dense["v5a_active"] = active
            save_state(state)
            return {
                "event": "v5a_harvest_blocked",
                "reason": "room_missed_settlement_sweep",
                "pair_id": active.get("pair_id"),
                "settlement_sweep": submit_sweep + 1,
            }

        outcome_info = trade_outcome_from_flow(action.get("trade_id"))
        visible = outcome_info.get("outcome")
        if visible and visible.get("status") == "void":
            active["stage"] = "blocked_visible_void"
            active["void"] = visible
            dense["v5a_active"] = active
            save_state(state)
            return {
                "event": "v5a_harvest_blocked",
                "reason": "visible_close_void",
                "pair_id": active.get("pair_id"),
                "void": visible,
            }
        omitted = _flow_omitted_at_sweep(submit_sweep + 1)
        if not visible or visible.get("status") != "settled":
            # If compact flow omitted outcomes, authoritative visibility is not
            # available. Continue only with deterministic local reconstruction;
            # if nothing was omitted, absence is suspicious and we wait.
            if not (omitted.get("settled") or omitted.get("void")):
                return None
            tid = action.get("trade_id")
            submissions = trade_submissions_in_room(state["room"], {tid} if tid else set())
            if not tid or tid not in submissions:
                return None
            active["outcome_evidence"] = {
                "mode": "local_reconstruction_due_to_compact_omission",
                "settlement_sweep": submit_sweep + 1,
                "omitted": omitted,
                "trade_id": tid,
                "room_submission": submissions[tid],
            }

        account_state = active.get("account_state") or {}
        applied = _v5a_apply_close(
            account_state,
            Decimal(str(action["qty"])),
            Decimal(str(action["px"])),
            settlement_close,
        )
        if not applied.get("settled"):
            active["stage"] = "blocked_simulated_void"
            active["simulation_reason"] = applied.get("reason")
            dense["v5a_active"] = active
            save_state(state)
            return {
                "event": "v5a_harvest_blocked",
                "reason": applied.get("reason"),
                "pair_id": active.get("pair_id"),
            }

        active["account_state"] = applied
        active.setdefault("verified_actions", []).append({
            **action,
            "settlement_sweep": submit_sweep + 1,
            "settlement_close": str(settlement_close),
            "visible_outcome": visible,
        })

        remaining = Decimal(str(applied["qty"]))
        if remaining <= Decimal("0"):
            long_locked = Decimal(str(applied["long_cash"])) - Decimal("10000")
            short_locked = Decimal(str(applied["short_cash"])) - Decimal("10000")
            winner = active["winner"]
            locked_score = long_locked if winner == "long" else short_locked
            record = {
                "pair_id": active["pair_id"],
                "cohort_sweep": active["pair"]["cohort_sweep"],
                "copy_no": active["pair"]["copy_no"],
                "winner": winner,
                "trigger_score": active["trigger_score"],
                "locked_score": str(locked_score),
                "long_locked_score": str(long_locked),
                "short_locked_score": str(short_locked),
                "closed_at": datetime.now(timezone.utc).isoformat(),
                "verified_actions": active.get("verified_actions") or [],
            }
            dense.setdefault("v5a_harvested", {})[active["pair_id"]] = record
            dense["v5a_last_locked"] = record
            dense["v5a_active"] = None
            save_state(state)
            return {
                "event": "v5a_harvest_locked",
                "pair_id": record["pair_id"],
                "winner": winner,
                "locked_score": record["locked_score"],
                "cohort_sweep": record["cohort_sweep"],
                "copy_no": record["copy_no"],
            }

        # A settled tranche releases collateral. Close the rest in one shot
        # only when both accounts can already afford a conservative 5% fee gap.
        # Otherwise submit another small bootstrap tranche and repeat.
        if stage == "bootstrap_submitted":
            pair = active["pair"]
            long_cash = Decimal(str(applied["long_cash"]))
            short_cash = Decimal(str(applied["short_cash"]))
            fee_buffer_total = V5A_BOOT_FEE_BUFFER_PCT * pr["px"] * remaining
            action_count = len(active.get("verified_actions") or [])
            if action_count >= 6:
                active["stage"] = "blocked_too_many_bootstrap_tranches"
                dense["v5a_active"] = active
                save_state(state)
                return {
                    "event": "v5a_harvest_blocked",
                    "reason": "too_many_bootstrap_tranches",
                    "pair_id": active["pair_id"],
                    "remaining": str(remaining),
                }

            if long_cash >= fee_buffer_total and short_cash >= fee_buffer_total:
                next_qty = remaining
                next_stage = "finish_submitted"
                prefix = f"h5f-{pair['cohort_sweep']}-{pair['copy_no']}"
                event = "v5a_harvest_finish_submitted"
            else:
                next_qty = _v5a_bootstrap_qty(
                    remaining,
                    long_cash,
                    short_cash,
                    Decimal(str(applied["short_lot_px"])),
                    pr["px"],
                )
                if next_qty is None:
                    active["stage"] = "blocked_cannot_fund_next_tranche"
                    dense["v5a_active"] = active
                    save_state(state)
                    return {
                        "event": "v5a_harvest_blocked",
                        "reason": "cannot_fund_next_tranche",
                        "pair_id": active["pair_id"],
                        "remaining": str(remaining),
                    }
                next_stage = "bootstrap_submitted"
                prefix = f"h5b-{pair['cohort_sweep']}-{pair['copy_no']}-{action_count+1}"
                event = "v5a_harvest_bootstrap_resubmitted"

            nxt = _v5a_submit_close(state, pair, next_qty, pr, prefix)
            active["stage"] = next_stage
            active["action"] = nxt
            active["last_tranche_submitted_at"] = datetime.now(timezone.utc).isoformat()
            dense["v5a_active"] = active
            save_state(state)
            return {
                "event": event,
                "pair_id": active["pair_id"],
                "qty": str(next_qty),
                "remaining_before": str(remaining),
                "sweep": pr["n"],
                "px": str(pr["px"]),
            }

        return None

    # No harvest is currently in flight. New harvest selection is review-paused;
    # any already-started staged close above is still managed.
    if V5A_REVIEW_PAUSE_NEW:
        return None
    if not dense.get("v5a_accept_new", True):
        return None
    if int(dense.get("v5a_last_scan_sweep", -1)) == int(pr["n"]):
        return None

    try:
        report = _v5a_candidates(state, pr)
    except Exception as e:
        dense["v5a_last_scan_error"] = {
            "sweep": int(pr["n"]),
            "at": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }
        save_state(state)
        return None

    dense["v5a_last_scan_sweep"] = int(pr["n"])
    dense.pop("v5a_last_scan_error", None)
    save_state(state)
    candidates = report.get("candidates") or []
    if not candidates:
        return None

    snap = candidates[0]
    pair = snap["pair"]
    opening = snap["opening"]
    boot = _v5a_bootstrap_qty(
        pair["qty"],
        Decimal(str(opening["long_cash"])),
        Decimal(str(opening["short_cash"])),
        Decimal(str(opening["short_lot_px"])),
        pr["px"],
    )
    if boot is None:
        dense["v5a_last_skip"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "pair_id": pair["pair_id"],
            "reason": "cannot_bootstrap_close_with_5pct_fee_buffer",
            "winner_score": str(snap["winner_score"]),
        }
        save_state(state)
        return None

    action = _v5a_submit_close(
        state,
        pair,
        boot,
        pr,
        f"h5b-{pair['cohort_sweep']}-{pair['copy_no']}",
    )
    active = {
        "pair_id": pair["pair_id"],
        "pair": {
            **pair,
            "qty": str(pair["qty"]),
            "low": str(pair["low"]),
            "high": str(pair["high"]),
        },
        "winner": snap["winner"],
        "trigger_score": str(snap["winner_score"]),
        "first_threshold": str(report["first_threshold"]),
        "second_threshold": str(report["second_threshold"]),
        "stage": "bootstrap_submitted",
        "account_state": {
            "settled": True,
            "settlement_close": str(opening["settlement_close"]),
            "qty": str(opening["qty"]),
            "long_cash": str(opening["long_cash"]),
            "short_cash": str(opening["short_cash"]),
            "feeder_cash": str(opening["feeder_cash"]),
            "long_pos": str(opening["long_pos"]),
            "short_pos": str(opening["short_pos"]),
            "long_lot_px": str(opening["long_lot_px"]),
            "short_lot_px": str(opening["short_lot_px"]),
        },
        "action": action,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    dense["v5a_active"] = active
    save_state(state)
    return {
        "event": "v5a_harvest_bootstrap_submitted",
        "pair_id": pair["pair_id"],
        "cohort_sweep": pair["cohort_sweep"],
        "copy_no": pair["copy_no"],
        "winner": snap["winner"],
        "trigger_score": str(snap["winner_score"]),
        "bootstrap_qty": str(boot),
        "total_qty": str(pair["qty"]),
        "sweep": pr["n"],
        "px": str(pr["px"]),
    }


def cmd_dense_v5a_preview(_args) -> None:
    state = load_state()
    report = _v5a_candidates(state)
    print("=== DENSE V5A HARVEST PREVIEW ===")
    print("sweep:", report.get("sweep"), "ref:", report.get("ref"), "mark:", report.get("mark"))
    print("first_threshold:", report.get("first_threshold"))
    print("second_threshold:", report.get("second_threshold"))
    print("active:", json.dumps((state.get("dense") or {}).get("v5a_active"), ensure_ascii=False, default=str))
    print("harvested_count:", len(((state.get("dense") or {}).get("v5a_harvested") or {})))
    candidates = report.get("candidates") or []
    print("eligible_candidates:", len(candidates))
    for snap in candidates[:12]:
        pair = snap["pair"]
        print(
            pair["pair_id"],
            "sweep", pair["cohort_sweep"],
            "copy", pair["copy_no"],
            "winner", snap["winner"],
            "score", snap["winner_score"].quantize(Decimal("0.01")),
            "already", snap["harvested_in_cohort"],
            "allowed", snap["allowed_in_cohort"],
        )


def cmd_enable_dense_v5a(_args) -> None:
    state = load_state()
    dense = state.setdefault("dense", {})
    if not dense.get("v4_enabled"):
        raise SystemExit("Dense V5a harvest requires Dense V4 to remain enabled")
    dense["v5a_enabled"] = True
    dense["v5a_accept_new"] = True
    dense["v5a_enabled_at"] = datetime.now(timezone.utc).isoformat()
    dense["v5a_min_score"] = str(V5A_MIN_SCORE)
    dense["v5a_first_trigger_ratio"] = str(V5A_FIRST_TRIGGER_RATIO)
    dense["v5a_second_trigger_ratio"] = str(V5A_SECOND_TRIGGER_RATIO)
    dense["v5a_second_min_score"] = str(V5A_SECOND_MIN_SCORE)
    dense["v5a_max_harvests_per_cohort"] = V5A_MAX_HARVESTS_PER_COHORT
    dense.setdefault("v5a_harvested", {})
    save_state(state)
    print("Dense V5a HARVEST ENABLED")
    print("V4 entry engine remains enabled")
    print("first harvest threshold: max(180, 25% of current prize cutoff)")
    print("second harvest threshold: max(300, 45% of current prize cutoff)")
    print("max harvested copy-pairs per V4 cohort:", V5A_MAX_HARVESTS_PER_COHORT)
    print("review pause for new V5a harvests:", V5A_REVIEW_PAUSE_NEW)
    print("at least 6/8 copies per cohort remain open")
    print("harvest uses staged close with a 5% fee-cash bootstrap buffer")


def cmd_pause_dense_v5a(_args) -> None:
    state = load_state()
    dense = state.setdefault("dense", {})
    if not dense.get("v5a_enabled"):
        print("Dense V5a is not enabled")
        return
    dense["v5a_accept_new"] = False
    dense["v5a_paused_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    print("Dense V5a NEW HARVESTS PAUSED")
    print("V4 entry engine remains enabled")
    if dense.get("v5a_active"):
        print("an in-flight staged harvest will continue until it is flat or blocked")


def _v5b_pair_lookup(state: dict) -> dict[str, dict]:
    return {pair["pair_id"]: pair for pair in _v5a_v4_pairs(state)}


def _v5b_seed_candidates(state: dict) -> list[dict]:
    dense = state.setdefault("dense", {})
    pairs = _v5b_pair_lookup(state)
    cycles = [x for x in (dense.get("v5b_cycles") or []) if isinstance(x, dict)]

    used_seed_ids = {
        rec.get("source_seed_id")
        for rec in cycles
        if rec.get("source_seed_id")
    }
    pending = dense.get("v5b_pending")
    if isinstance(pending, dict) and pending.get("source_seed_id"):
        used_seed_ids.add(pending.get("source_seed_id"))
    active = dense.get("v5b_active")
    if isinstance(active, dict) and active.get("source_seed_id"):
        used_seed_ids.add(active.get("source_seed_id"))

    out = []

    for pair_id, rec in (dense.get("v5a_harvested") or {}).items():
        if not isinstance(rec, dict):
            continue
        seed_id = f"v5a:{pair_id}"
        if seed_id in used_seed_ids:
            continue
        try:
            locked = Decimal(str(rec["locked_score"]))
        except Exception:
            continue
        if locked < V5B_MIN_SEED_SCORE:
            continue
        pair = pairs.get(pair_id)
        if not pair:
            continue
        winner = str(rec.get("winner"))
        if winner not in ("long", "short"):
            continue
        out.append({
            "source_seed_id": seed_id,
            "source_pair_id": pair_id,
            "source_cycle_index": None,
            "source_winner": winner,
            "winner_label": pair[winner],
            "flip_side": "short" if winner == "long" else "long",
            "locked_score": locked,
            "cash": Decimal("10000") + locked,
            "closed_at": rec.get("closed_at"),
        })

    for rec in cycles:
        try:
            cycle_idx = int(rec["cycle_index"])
            locked = Decimal(str(rec["final_locked_score"]))
        except Exception:
            continue
        if rec.get("close_reason") != "take_profit" or locked < V5B_MIN_SEED_SCORE:
            continue
        seed_id = f"v5b:{cycle_idx}"
        if seed_id in used_seed_ids:
            continue
        prev_side = str(rec.get("side"))
        if prev_side not in ("long", "short"):
            continue
        out.append({
            "source_seed_id": seed_id,
            "source_pair_id": rec.get("source_pair_id"),
            "source_cycle_index": cycle_idx,
            "source_winner": prev_side,
            "winner_label": rec.get("winner_label"),
            "flip_side": "short" if prev_side == "long" else "long",
            "locked_score": locked,
            "cash": Decimal(str(rec["final_cash"])),
            "closed_at": rec.get("closed_at"),
        })

    out.sort(key=lambda x: (x["locked_score"], str(x.get("closed_at") or "")), reverse=True)
    return out


def _v5b_plan_qty(seed_score: Decimal, cash: Decimal, px: Decimal) -> Decimal:
    # At close ~= trade price, each side pays 1%. Cap the opening fee to 45%
    # of the realized cushion. This leaves room for a later close fee and keeps
    # the 10,000 POLF principal mostly protected on a flat round trip.
    fee_budget = max(Decimal("0"), seed_score * V5B_ENTRY_FEE_FRACTION)
    notional_by_fee = fee_budget / Decimal("0.01")
    # Independent cash cap with a 3% funds buffer for modest intra-sweep moves.
    notional_by_cash = cash / Decimal("1.03")
    notional = min(notional_by_fee, notional_by_cash)
    if px <= 0:
        return Decimal("0")
    return (notional / px).quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def _v5b_side_fees(
    side: str,
    qty: Decimal,
    px: Decimal,
    close: Decimal,
) -> tuple[Decimal, Decimal]:
    base = Decimal("0.01") * qty * px
    gap = (close - px) * qty
    buyer = max(base, gap)
    seller = max(base, -gap)
    if side == "long":
        return buyer, seller
    return seller, buyer


def _v5b_maker_fee(side: str, qty: Decimal, px: Decimal, close: Decimal) -> Decimal:
    return _v5b_side_fees(side, qty, px, close)[0]


def _v5b_score(cash: Decimal, side: str, qty: Decimal, entry_px: Decimal, mark: Decimal) -> Decimal:
    if side == "long":
        value = cash + qty * mark
    else:
        value = cash + qty * (Decimal("2") * entry_px - mark)
    return value - Decimal("10000")


def _v5b_project_flat_score(
    cash: Decimal,
    side: str,
    qty: Decimal,
    entry_px: Decimal,
    close_px: Decimal,
) -> Decimal:
    close_side = "short" if side == "long" else "long"
    fee = _v5b_maker_fee(close_side, qty, close_px, close_px)
    if side == "long":
        flat_cash = cash + qty * close_px - fee
    else:
        flat_cash = cash + qty * (Decimal("2") * entry_px - close_px) - fee
    return flat_cash - Decimal("10000")


def _v5b_register_pending(state: dict, pr: dict) -> dict | None:
    dense = state.setdefault("dense", {})
    pending = dense.get("v5b_pending")

    if isinstance(dense.get("v5b_active"), dict):
        return None
    if int(pr["n"]) >= V5B_NO_NEW_AFTER_SWEEP:
        dense["v5b_last_no_seed"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "sweep": int(pr["n"]),
            "reason": "new_cycle_cutoff",
        }
        save_state(state)
        return None

    # Persist the registration plan before generating/posting feeder keys. This
    # makes every later failure observable and resumable.
    if not isinstance(pending, dict):
        try:
            seeds = _v5b_seed_candidates(state)
        except Exception as e:
            dense["v5b_last_error"] = {
                "at": datetime.now(timezone.utc).isoformat(),
                "sweep": int(pr["n"]),
                "stage": "seed_scan",
                "error": str(e),
            }
            save_state(state)
            return None

        if not seeds:
            harvested = dense.get("v5a_harvested") or {}
            pair_ids = set(_v5b_pair_lookup(state))
            dense["v5b_last_no_seed"] = {
                "at": datetime.now(timezone.utc).isoformat(),
                "sweep": int(pr["n"]),
                "reason": "seed_scan_empty",
                "harvested_count": len(harvested),
                "harvested_ids": sorted(str(x) for x in harvested.keys())[:12],
                "known_pair_count": len(pair_ids),
                "v4_00213_known": "v4-00213" in pair_ids,
                "cycle_count": len(dense.get("v5b_cycles") or []),
            }
            save_state(state)
            return None

        seed = seeds[0]
        idx = int(dense.get("v5b_next_index", 1))
        labels = [f"DENSE-V5B-{idx:05d}-F{i}" for i in range(1, V5B_FEEDERS + 1)]

        # Seed candidates use Decimal for calculations, but persistent state is
        # JSON. Convert numeric seed fields before the first save or json.dumps
        # will raise "Object of type Decimal is not JSON serializable".
        persisted_seed = {
            **seed,
            "locked_score": str(seed["locked_score"]),
            "cash": str(seed["cash"]),
        }

        pending = {
            "index": idx,
            **persisted_seed,
            "feeder_labels": labels,
            "registrations": [],
            "registered_sweep": None,
            "ready_after_sweep": None,
            "status": "creating_keys",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        dense["v5b_pending"] = pending
        dense["v5b_next_index"] = idx + 1
        dense["v5b_last_error"] = None
        dense["v5b_last_no_seed"] = None
        save_state(state)

    if pending.get("status") == "creating_keys":
        try:
            for label in pending["feeder_labels"]:
                add_dynamic_key(state, label)
            pending["status"] = "waiting_room"
            dense["v5b_pending"] = pending
            save_state(state)
        except Exception as e:
            dense["v5b_pending"] = pending
            dense["v5b_last_error"] = {
                "at": datetime.now(timezone.utc).isoformat(),
                "sweep": int(pr["n"]),
                "stage": "create_feeder_keys",
                "cycle_index": pending.get("index"),
                "error": str(e),
            }
            save_state(state)
            return pending

    if pending.get("status") == "waiting_room":
        if not room_registration_confirmed(state):
            return pending
        pending["status"] = "registering"
        dense["v5b_pending"] = pending
        save_state(state)

    if pending.get("status") == "registering":
        if not room_registration_confirmed(state):
            return pending
        done = {
            rec.get("label")
            for rec in (pending.get("registrations") or [])
            if isinstance(rec, dict)
        }
        try:
            for label in pending["feeder_labels"]:
                if label in done:
                    continue
                key = add_dynamic_key(state, label)
                ack = post_signed(state, state["room"], label, owner_text(key["did"]))
                pending.setdefault("registrations", []).append({
                    "label": label,
                    "did": key["did"],
                    "posted_at": datetime.now(timezone.utc).isoformat(),
                    "ack": ack.strip().splitlines()[0] if ack.strip() else "",
                })
                dense["v5b_pending"] = pending
                dense["v5b_last_error"] = None
                save_state(state)
                time.sleep(0.08)

            pending["registered_sweep"] = int(pr["n"])
            pending["ready_after_sweep"] = int(pr["n"]) + 1
            pending["status"] = "registered"
            dense["v5b_pending"] = pending
            dense["v5b_last_error"] = None
            save_state(state)
        except Exception as e:
            dense["v5b_pending"] = pending
            dense["v5b_last_error"] = {
                "at": datetime.now(timezone.utc).isoformat(),
                "sweep": int(pr["n"]),
                "stage": "register_feeders",
                "cycle_index": pending.get("index"),
                "registered_count": len(pending.get("registrations") or []),
                "error": str(e),
            }
            save_state(state)
            return pending

    return pending


def _v5b_split_qty(total: Decimal) -> list[Decimal]:
    cent = Decimal("0.01")
    first = (total / Decimal(V5B_FEEDERS)).quantize(cent, rounding=ROUND_DOWN)
    parts = [first for _ in range(V5B_FEEDERS)]
    used = sum(parts, Decimal("0"))
    parts[-1] += total - used
    return parts


def _v5b_submit_leg(
    state: dict,
    winner_label: str,
    feeder_label: str,
    side: str,
    qty: Decimal,
    px: Decimal,
    sweep: int,
    tid: str,
) -> dict:
    maker_side = "buy" if side == "long" else "sell"
    text = build_trade(
        state,
        state["room"],
        winner_label,
        feeder_label,
        maker_side,
        qty,
        px,
        sweep + 2,
        tid,
    )
    ack = post_signed(state, state["room"], winner_label, text)
    return {
        "trade_id": tid,
        "winner": winner_label,
        "feeder": feeder_label,
        "side": side,
        "maker_side": maker_side,
        "qty": str(qty),
        "px": str(px),
        "submission_sweep": int(sweep),
        "ack": ack.strip().splitlines()[0] if ack.strip() else "",
    }


def _v5b_submit_open(state: dict, pending: dict, pr: dict) -> dict:
    seed_score = Decimal(str(pending["locked_score"]))
    cash = Decimal(str(pending["cash"]))
    qty = _v5b_plan_qty(seed_score, cash, pr["px"])
    if qty < V5B_MIN_QTY:
        raise RuntimeError("V5b planned quantity below minimum")

    parts = _v5b_split_qty(qty)
    trades = []
    for i, (label, part) in enumerate(zip(pending["feeder_labels"], parts), 1):
        tid = deterministic_trade_id("v5bo", pending["index"], pr["n"], i)
        trades.append(_v5b_submit_leg(
            state,
            pending["winner_label"],
            label,
            pending["flip_side"],
            part,
            pr["px"],
            pr["n"],
            tid,
        ))
        time.sleep(0.06)

    active = {
        "cycle_index": int(pending["index"]),
        "source_seed_id": pending["source_seed_id"],
        "source_pair_id": pending["source_pair_id"],
        "source_cycle_index": pending.get("source_cycle_index"),
        "source_winner": pending["source_winner"],
        "winner_label": pending["winner_label"],
        "side": pending["flip_side"],
        "seed_locked_score": str(seed_score),
        "cash_before_open": str(cash),
        "entry_px": str(pr["px"]),
        "qty": str(qty),
        "parts": [str(x) for x in parts],
        "feeder_labels": list(pending["feeder_labels"]),
        "open_trades": trades,
        "open_submission_sweep": int(pr["n"]),
        "status": "opening_submitted",
        "opened_at": datetime.now(timezone.utc).isoformat(),
    }
    dense = state.setdefault("dense", {})
    dense["v5b_active"] = active
    dense["v5b_pending"] = None
    save_state(state)
    return {
        "event": "v5b_open_submitted",
        "cycle_index": active["cycle_index"],
        "source_seed_id": active.get("source_seed_id"),
        "source_pair_id": active["source_pair_id"],
        "side": active["side"],
        "seed_locked_score": active["seed_locked_score"],
        "qty": active["qty"],
        "px": active["entry_px"],
        "sweep": pr["n"],
    }


def _v5b_verify_open(state: dict, active: dict, pr: dict) -> dict | None:
    submit_sweep = int(active["open_submission_sweep"])
    if pr["n"] <= submit_sweep:
        return None
    settle_sweep = submit_sweep + 1
    refs = _price_refs_by_sweep()
    close = refs.get(settle_sweep)
    if close is None:
        return None
    if _flow_room_missed_at_sweep(state["room"], settle_sweep):
        active["status"] = "blocked_open_missed"
        active["blocked_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        return {"event": "v5b_blocked", "reason": "open_settlement_room_missed"}

    outcomes = _v5a_visible_outcomes({x["trade_id"] for x in active.get("open_trades") or []})
    if any(outcomes.get(x["trade_id"]) == "void" for x in active.get("open_trades") or []):
        active["status"] = "blocked_open_void"
        active["visible_outcomes"] = outcomes
        save_state(state)
        return {"event": "v5b_blocked", "reason": "visible_open_void"}
    unknown = [
        x["trade_id"] for x in active.get("open_trades") or []
        if outcomes.get(x["trade_id"]) != "settled"
    ]
    if unknown:
        omitted = _flow_omitted_at_sweep(settle_sweep)
        if not (omitted.get("settled") or omitted.get("void")):
            return None
        submissions = trade_submissions_in_room(state["room"], set(unknown))
        if any(tid not in submissions for tid in unknown):
            return None
        active["outcome_evidence"] = {
            "mode": "local_reconstruction_due_to_compact_omission",
            "settlement_sweep": settle_sweep,
            "unknown_trade_ids": unknown,
            "omitted": omitted,
            "room_submissions": {tid: submissions[tid] for tid in unknown},
        }

    qty = Decimal(str(active["qty"]))
    px = Decimal(str(active["entry_px"]))
    cash_before = Decimal(str(active["cash_before_open"]))
    fee = _v5b_maker_fee(active["side"], qty, px, close)
    required = qty * px + fee
    if cash_before < required:
        active["status"] = "blocked_open_simulated_funds"
        active["required"] = str(required)
        save_state(state)
        return {"event": "v5b_blocked", "reason": "simulated_open_funds"}

    feeder_cash_after_open = []
    for trade in active.get("open_trades") or []:
        part = Decimal(str(trade["qty"]))
        _maker_fee, taker_fee = _v5b_side_fees(active["side"], part, px, close)
        feeder_required = part * px + taker_fee
        if Decimal("10000") < feeder_required:
            active["status"] = "blocked_open_feeder_funds"
            active["feeder_required"] = str(feeder_required)
            save_state(state)
            return {"event": "v5b_blocked", "reason": "simulated_open_feeder_funds"}
        feeder_cash_after_open.append(str(Decimal("10000") - feeder_required))

    cash_after = cash_before - required
    active["feeder_cash_after_open"] = feeder_cash_after_open
    active["open_settlement_sweep"] = settle_sweep
    active["open_settlement_close"] = str(close)
    active["open_fee"] = str(fee)
    active["cash_after_open"] = str(cash_after)
    active["status"] = "open_verified"
    active["verified_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    return {
        "event": "v5b_open_verified",
        "cycle_index": active["cycle_index"],
        "side": active["side"],
        "qty": active["qty"],
        "cash_after_open": str(cash_after),
        "open_fee": str(fee),
        "settlement_close": str(close),
    }


def _v5b_submit_close(state: dict, active: dict, pr: dict, reason: str, projected: Decimal) -> dict:
    close_side = "short" if active["side"] == "long" else "long"
    parts = [Decimal(str(x)) for x in active["parts"]]
    trades = []
    for i, (label, part) in enumerate(zip(active["feeder_labels"], parts), 1):
        tid = deterministic_trade_id("v5bc", active["cycle_index"], pr["n"], i)
        trades.append(_v5b_submit_leg(
            state,
            active["winner_label"],
            label,
            close_side,
            part,
            pr["px"],
            pr["n"],
            tid,
        ))
        time.sleep(0.06)

    active["close_trades"] = trades
    active["close_submission_sweep"] = int(pr["n"])
    active["close_px"] = str(pr["px"])
    active["close_reason"] = reason
    active["projected_locked_score_at_submit"] = str(projected)
    active["status"] = "closing_submitted"
    active["close_submitted_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    return {
        "event": "v5b_close_submitted",
        "cycle_index": active["cycle_index"],
        "reason": reason,
        "projected_locked_score": str(projected),
        "sweep": pr["n"],
        "px": str(pr["px"]),
    }


def _v5b_verify_close(state: dict, active: dict, pr: dict) -> dict | None:
    submit_sweep = int(active["close_submission_sweep"])
    if pr["n"] <= submit_sweep:
        return None
    settle_sweep = submit_sweep + 1
    refs = _price_refs_by_sweep()
    close = refs.get(settle_sweep)
    if close is None:
        return None
    if _flow_room_missed_at_sweep(state["room"], settle_sweep):
        active["status"] = "blocked_close_missed"
        save_state(state)
        return {"event": "v5b_blocked", "reason": "close_settlement_room_missed"}

    outcomes = _v5a_visible_outcomes({x["trade_id"] for x in active.get("close_trades") or []})
    if any(outcomes.get(x["trade_id"]) == "void" for x in active.get("close_trades") or []):
        active["status"] = "blocked_close_void"
        active["visible_outcomes"] = outcomes
        save_state(state)
        return {"event": "v5b_blocked", "reason": "visible_close_void"}
    unknown = [
        x["trade_id"] for x in active.get("close_trades") or []
        if outcomes.get(x["trade_id"]) != "settled"
    ]
    if unknown:
        omitted = _flow_omitted_at_sweep(settle_sweep)
        if not (omitted.get("settled") or omitted.get("void")):
            return None
        submissions = trade_submissions_in_room(state["room"], set(unknown))
        if any(tid not in submissions for tid in unknown):
            return None
        active["outcome_evidence"] = {
            "mode": "local_reconstruction_due_to_compact_omission",
            "settlement_sweep": settle_sweep,
            "unknown_trade_ids": unknown,
            "omitted": omitted,
            "room_submissions": {tid: submissions[tid] for tid in unknown},
        }

    qty = Decimal(str(active["qty"]))
    entry = Decimal(str(active["entry_px"]))
    cash = Decimal(str(active["cash_after_open"]))
    close_px = Decimal(str(active["close_px"]))
    close_side = "short" if active["side"] == "long" else "long"
    fee = _v5b_maker_fee(close_side, qty, close_px, close)

    if cash < fee:
        active["status"] = "blocked_close_simulated_funds"
        active["close_fee"] = str(fee)
        save_state(state)
        return {"event": "v5b_blocked", "reason": "simulated_close_fee_funds"}

    feeder_cash = [Decimal(str(x)) for x in (active.get("feeder_cash_after_open") or [])]
    for i, trade in enumerate(active.get("close_trades") or []):
        part = Decimal(str(trade["qty"]))
        _maker_fee, taker_fee = _v5b_side_fees(close_side, part, close_px, close)
        if i >= len(feeder_cash) or feeder_cash[i] < taker_fee:
            active["status"] = "blocked_close_feeder_funds"
            active["blocking_feeder_index"] = i
            active["blocking_feeder_fee"] = str(taker_fee)
            save_state(state)
            return {"event": "v5b_blocked", "reason": "simulated_close_feeder_funds"}

    if active["side"] == "long":
        final_cash = cash - fee + qty * close_px
    else:
        final_cash = cash - fee + qty * (Decimal("2") * entry - close_px)

    final_score = final_cash - Decimal("10000")
    record = {
        **active,
        "status": "closed",
        "close_settlement_sweep": settle_sweep,
        "close_settlement_close": str(close),
        "close_fee": str(fee),
        "final_cash": str(final_cash),
        "final_locked_score": str(final_score),
        "closed_at": datetime.now(timezone.utc).isoformat(),
    }
    dense = state.setdefault("dense", {})
    dense.setdefault("v5b_cycles", []).append(record)
    dense["v5b_last_closed"] = record
    dense["v5b_active"] = None
    save_state(state)
    return {
        "event": "v5b_cycle_closed",
        "cycle_index": record["cycle_index"],
        "reason": record["close_reason"],
        "seed_locked_score": record["seed_locked_score"],
        "final_locked_score": record["final_locked_score"],
        "side": record["side"],
    }


def _v5b_stop_score(seed_locked_score: Decimal) -> Decimal:
    return max(V5B_STOP_FLOOR, seed_locked_score * V5B_STOP_RETAIN_RATIO)


def dense_v5b_step(
    state: dict,
    pr: dict,
    allow_new: bool = True,
    allow_pending: bool = True,
) -> dict | None:
    dense = state.setdefault("dense", {})
    if not dense.get("v5b_enabled") or not dense.get("v4_enabled"):
        return None

    dense["v5b_last_check"] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "sweep": int(pr["n"]),
        "pending": bool(isinstance(dense.get("v5b_pending"), dict)),
        "active": bool(isinstance(dense.get("v5b_active"), dict)),
    }
    save_state(state)

    # V5a and V5b operate on disjoint accounts. Do not pause compound risk
    # management merely because another V5a harvest is in flight.
    active = dense.get("v5b_active")
    if isinstance(active, dict):
        status = active.get("status")
        if status == "opening_submitted":
            return _v5b_verify_open(state, active, pr)
        if status == "open_verified":
            pnl = latest_payload("d-close1-pnl", "pnl")
            try:
                mark = Decimal(str((pnl or {})["mark"]))
            except Exception:
                return None
            cash = Decimal(str(active["cash_after_open"]))
            qty = Decimal(str(active["qty"]))
            entry = Decimal(str(active["entry_px"]))
            current_score = _v5b_score(cash, active["side"], qty, entry, mark)
            projected = _v5b_project_flat_score(cash, active["side"], qty, entry, pr["px"])
            seed = Decimal(str(active["seed_locked_score"]))
            take = seed + V5B_TAKE_GAIN
            stop = _v5b_stop_score(seed)
            if projected >= take:
                return _v5b_submit_close(state, active, pr, "take_profit", projected)
            if projected <= stop:
                return _v5b_submit_close(state, active, pr, "stop", projected)
            dense["v5b_last_mark"] = {
                "sweep": int(pr["n"]),
                "mark": str(mark),
                "current_score": str(current_score),
                "projected_flat_score": str(projected),
                "take_score": str(take),
                "stop_score": str(stop),
            }
            save_state(state)
            return None
        if status == "closing_submitted":
            return _v5b_verify_close(state, active, pr)
        return None

    pending = dense.get("v5b_pending")
    if isinstance(pending, dict) and not allow_pending:
        return None

    if isinstance(pending, dict):
        if not dense.get("v5b_accept_new", True):
            return None

        if pending.get("status") in ("creating_keys", "waiting_room", "registering"):
            pending = _v5b_register_pending(state, pr)
            if not isinstance(pending, dict):
                return None
            if pending.get("status") in ("creating_keys", "waiting_room", "registering"):
                err = dense.get("v5b_last_error")
                return {
                    "event": "v5b_wait_feeder_registration",
                    "cycle_index": pending.get("index"),
                    "registered_count": len(pending.get("registrations") or []),
                    "pending_status": pending.get("status"),
                    "error": (err or {}).get("error") if isinstance(err, dict) else None,
                    "sweep": pr["n"],
                }

        ready_after = pending.get("ready_after_sweep")
        if ready_after is None or int(pr["n"]) < int(ready_after):
            return None
        if not allow_new or V5B_REVIEW_PAUSE_NEW:
            return None
        flow, st = latest_flow_and_state()
        flow_n = int(flow["n"]) if isinstance(flow, dict) and flow.get("n") is not None else None
        state_n = int(st["n"]) if isinstance(st, dict) and st.get("n") is not None else None
        if flow_n != pr["n"] or state_n != pr["n"]:
            return None
        if not room_registration_confirmed(state) or flow_misses_room(flow, state["room"]):
            return None
        return _v5b_submit_open(state, pending, pr)

    if not allow_new or V5B_REVIEW_PAUSE_NEW:
        return None
    if not dense.get("v5b_accept_new", True):
        return None
    pending = _v5b_register_pending(state, pr)
    if pending:
        if pending.get("status") == "registering":
            err = dense.get("v5b_last_error")
            return {
                "event": "v5b_wait_feeder_registration",
                "cycle_index": pending.get("index"),
                "registered_count": len(pending.get("registrations") or []),
                "error": (err or {}).get("error") if isinstance(err, dict) else None,
                "sweep": pr["n"],
            }
        return {
            "event": "v5b_seed_registered",
            "cycle_index": pending["index"],
            "source_seed_id": pending.get("source_seed_id"),
            "source_pair_id": pending["source_pair_id"],
            "side": pending["flip_side"],
            "seed_locked_score": str(pending["locked_score"]),
            "ready_after_sweep": pending["ready_after_sweep"],
        }
    return None


def cmd_dense_v5b_preview(_args) -> None:
    state = load_state()
    pr = fresh_price(max_age=10**9)
    dense = state.get("dense") or {}
    print("=== DENSE V5B COMPOUND PREVIEW ===")
    print("sweep:", pr["n"], "ref:", pr["px"])
    print("enabled:", bool(dense.get("v5b_enabled")))
    print("accept_new:", bool(dense.get("v5b_accept_new", True)))
    print("active:", json.dumps(dense.get("v5b_active"), ensure_ascii=False, default=str))
    print("pending:", json.dumps(dense.get("v5b_pending"), ensure_ascii=False, default=str))
    print("closed_cycles:", len(dense.get("v5b_cycles") or []))
    seeds = _v5b_seed_candidates(state)
    print("eligible_seeds:", len(seeds))
    for seed in seeds[:10]:
        qty = _v5b_plan_qty(seed["locked_score"], seed["cash"], pr["px"])
        est_fee = Decimal("0.01") * qty * pr["px"]
        print(
            seed.get("source_seed_id"),
            "pair", seed["source_pair_id"],
            "parent_cycle", seed.get("source_cycle_index"),
            "winner", seed["source_winner"],
            "flip", seed["flip_side"],
            "locked", seed["locked_score"],
            "cash", seed["cash"],
            "planned_qty", qty,
            "estimated_open_fee", est_fee.quantize(Decimal("0.01")),
            "take_score", (seed["locked_score"] + V5B_TAKE_GAIN),
            "stop_score", _v5b_stop_score(seed["locked_score"]),
        )


def cmd_enable_dense_v5b(_args) -> None:
    state = load_state()
    dense = state.setdefault("dense", {})
    if not dense.get("v4_enabled") or not dense.get("v5a_enabled"):
        raise SystemExit("Dense V5b requires V4 and V5a enabled")
    dense["v5b_enabled"] = True
    dense["v5b_accept_new"] = True
    dense["v5b_enabled_at"] = datetime.now(timezone.utc).isoformat()
    dense["v5b_entry_fee_fraction"] = str(V5B_ENTRY_FEE_FRACTION)
    dense["v5b_take_gain"] = str(V5B_TAKE_GAIN)
    dense["v5b_stop_score"] = str(V5B_STOP_SCORE)
    dense.setdefault("v5b_cycles", [])
    dense.setdefault("v5b_next_index", 1)
    save_state(state)
    print("Dense V5b COMPOUND ENABLED")
    print("V4 entry and V5a harvest remain enabled")
    print("seed minimum locked score:", V5B_MIN_SEED_SCORE)
    print("flip direction: opposite the V5a winning side")
    print("opening base-fee budget:", V5B_ENTRY_FEE_FRACTION, "of realized seed score")
    print("take-profit locked-score gain:", V5B_TAKE_GAIN)
    print("stop projected locked score: max(", V5B_STOP_FLOOR, ", seed *", V5B_STOP_RETAIN_RATIO, ")")
    print("review pause for new V5b cycles:", V5B_REVIEW_PAUSE_NEW)
    print("max active compound accounts:", V5B_MAX_ACTIVE)


def cmd_pause_dense_v5b(_args) -> None:
    state = load_state()
    dense = state.setdefault("dense", {})
    dense["v5b_accept_new"] = False
    dense["v5b_paused_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    print("Dense V5b NEW CYCLES PAUSED")
    print("an in-flight compound cycle is still managed to take-profit/stop/close")


def dense_register_pending(state: dict, sweep: int) -> dict:
    dense = state.setdefault("dense", {})
    pending = dense.get("pending")
    if not isinstance(pending, dict):
        idx = int(dense.get("next_index", 1))
        base = f"DENSE-{idx:05d}"
        labels = {
            "long": f"{base}-L",
            "short": f"{base}-S",
            "feeder": f"{base}-F",
        }
        for label in labels.values():
            add_dynamic_key(state, label)
        pending = {
            "index": idx,
            "labels": labels,
            "status": "waiting_room",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_sweep": sweep,
            "registrations": {},
            "trades": {},
        }
        dense["pending"] = pending
        dense["next_index"] = idx + 1
        save_state(state)

    if pending.get("status") == "waiting_room":
        if not room_registration_confirmed(state):
            return pending
        pending["status"] = "registering"
        dense["pending"] = pending
        save_state(state)

    if pending.get("status") == "registering":
        if not room_registration_confirmed(state):
            return pending
        for role, label in pending["labels"].items():
            if role in pending["registrations"]:
                continue
            did = state["keys"][label]["did"]
            ack = post_signed(state, state["room"], label, owner_text(did))
            pending["registrations"][role] = {
                "did": did,
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "ack": ack.strip().splitlines()[0] if ack.strip() else "",
            }
            dense["pending"] = pending
            save_state(state)
            time.sleep(0.08)
        pending["status"] = "registered"
        pending["registered_sweep"] = sweep
        pending["ready_after_sweep"] = sweep + 1
        dense["pending"] = pending
        save_state(state)

    return pending


def dense_room_maintenance(state: dict, pr: dict) -> dict | None:
    """Keep the dedicated room referee-listed with one hot-path flow read.

    The latest flow carries both listing and unlisting transitions. The cached
    local flag remains authoritative between transitions, avoiding repeated
    multi-megabyte historical export downloads from helper calls.
    """
    dense = state.setdefault("dense", {})
    pending = dense.get("pending")

    latest_flow, _st = latest_flow_and_state()
    flow_n = int(latest_flow["n"]) if isinstance(latest_flow, dict) and latest_flow.get("n") is not None else pr["n"]

    if isinstance(latest_flow, dict):
        if contains_exact(latest_flow.get("unlisted"), state["room"]):
            dense["room_registration_confirmed"] = False
            dense["room_registration_lost_at"] = datetime.now(timezone.utc).isoformat()
        if contains_exact(latest_flow.get("rooms"), state["room"]):
            dense["room_registration_confirmed"] = True
            dense["room_registration_confirmed_at"] = datetime.now(timezone.utc).isoformat()
            dense["room_registration_refresh_sweep"] = flow_n
        save_state(state)

    confirmed = room_registration_confirmed(state)
    try:
        last_refresh = int(dense.get("room_registration_refresh_sweep", -10**9))
    except Exception:
        last_refresh = -10**9
    refresh_due = confirmed and (flow_n - last_refresh >= DENSE_ROOM_REFRESH_SWEEPS)

    if not confirmed or refresh_due:
        requested = dense.get("room_registration_requested_sweep")
        ack = None
        posted = False
        if requested != flow_n:
            ack = post_signed(
                state,
                "close1",
                state["controller"],
                room_text(state["room"]),
            )
            posted = True
            dense["room_registration_requested_sweep"] = flow_n
            dense["room_registration_requested_at"] = datetime.now(timezone.utc).isoformat()
            save_state(state)

        if not confirmed:
            return {
                "event": "dense_wait_room_registration",
                "sweep": pr["n"],
                "flow_sweep": flow_n,
                "room": state["room"],
                "registration_posted": posted,
                "pending_index": pending.get("index") if isinstance(pending, dict) else None,
                "ack": ack.strip().splitlines()[0] if isinstance(ack, str) and ack.strip() else None,
            }

    if isinstance(pending, dict) and pending.get("needs_owner_reregister"):
        if not room_registration_confirmed(state):
            return {
                "event": "dense_wait_room_registration",
                "sweep": pr["n"],
                "flow_sweep": flow_n,
                "room": state["room"],
                "pending_index": pending.get("index"),
            }

        reposted = []
        for role, label in pending["labels"].items():
            did = state["keys"][label]["did"]
            ack = post_signed(state, state["room"], label, owner_text(did))
            reposted.append({
                "role": role,
                "label": label,
                "did": did,
                "posted_at": datetime.now(timezone.utc).isoformat(),
                "ack": ack.strip().splitlines()[0] if ack.strip() else "",
            })
            time.sleep(0.08)

        pending.setdefault("owner_reregistrations", []).append({
            "sweep": flow_n,
            "records": reposted,
        })
        pending["needs_owner_reregister"] = False
        pending["registered_sweep"] = flow_n
        pending["ready_after_sweep"] = max(int(pr["n"]), flow_n) + 1
        dense["pending"] = pending
        save_state(state)
        return {
            "event": "dense_owner_registrations_reposted",
            "sweep": pr["n"],
            "flow_sweep": flow_n,
            "index": pending.get("index"),
            "ready_after_sweep": pending["ready_after_sweep"],
            "count": len(reposted),
        }

    return None


def dense_submit_pending(state: dict, pr: dict) -> dict | None:
    dense = state.setdefault("dense", {})
    pending = dense.get("pending")
    if not isinstance(pending, dict) or pending.get("status") != "registered":
        return None
    if pr["n"] < int(pending.get("ready_after_sweep", 10**9)):
        return None
    if dense.get("v4_enabled") and pr["n"] < int(dense.get("v4_not_before_sweep", 0)):
        return {
            "event": "dense_v4_wait_reserve_prime",
            "sweep": pr["n"],
            "not_before_sweep": dense.get("v4_not_before_sweep"),
            "pending_index": pending.get("index"),
        }
    if dense.get("v3_enabled") and pr["n"] < int(dense.get("v3_not_before_sweep", 0)):
        return {
            "event": "dense_v3_wait_reserve_prime",
            "sweep": pr["n"],
            "not_before_sweep": dense.get("v3_not_before_sweep"),
            "pending_index": pending.get("index"),
        }

    flow, st = latest_flow_and_state()
    flow_n = int(flow["n"]) if isinstance(flow, dict) and flow.get("n") is not None else None
    state_n = int(st["n"]) if isinstance(st, dict) and st.get("n") is not None else None
    if flow_n != pr["n"] or state_n != pr["n"]:
        return {
            "event": "dense_wait_alignment",
            "sweep": pr["n"],
            "flow_sweep": flow_n,
            "state_sweep": state_n,
        }

    if not room_registration_confirmed(state):
        return {
            "event": "dense_wait_room_registration",
            "sweep": pr["n"],
            "room": state["room"],
            "pending_index": pending.get("index"),
        }

    if flow_misses_room(flow, state["room"]):
        return {
            "event": "dense_wait_room_catchup",
            "sweep": pr["n"],
            "reason": "dedicated room appears in referee missed ranges",
        }

    labels = pending["labels"]
    if dense.get("v4_enabled"):
        v4_plan = dense_v4_plan_copy(pr, 1)
        qty = v4_plan["qty"]
        low, high = v4_plan["low"], v4_plan["high"]
        offset = v4_plan["short_offset"]
    else:
        v4_plan = None
        qty = dense_qty(pr["px"])
        offset = dense_offset(state)
        low, high = dense_prices(pr["px"], offset)
    if qty < Decimal("0.1"):
        raise RuntimeError("dense quantity below minimum")

    trades = pending.setdefault("trades", {})
    if "long" not in trades:
        tid = deterministic_trade_id("d4l", pending["index"], pr["n"])
        text = build_trade(
            state,
            state["room"],
            labels["feeder"],
            labels["long"],
            "sell",
            qty,
            low,
            pr["n"] + 2,
            tid,
        )
        ack = post_signed(state, state["room"], labels["feeder"], text)
        trades["long"] = {
            "trade_id": tid,
            "target": labels["long"],
            "feeder": labels["feeder"],
            "side": "long",
            "px": str(low),
            "qty": str(qty),
            "sweep": pr["n"],
            "ack": ack.strip().splitlines()[0] if ack.strip() else "",
        }
        pending["trades"] = trades
        dense["pending"] = pending
        save_state(state)
        time.sleep(0.08)

    if "short" not in trades:
        tid = deterministic_trade_id("d4s", pending["index"], pr["n"])
        text = build_trade(
            state,
            state["room"],
            labels["short"],
            labels["feeder"],
            "sell",
            qty,
            high,
            pr["n"] + 2,
            tid,
        )
        ack = post_signed(state, state["room"], labels["feeder"], text)
        trades["short"] = {
            "trade_id": tid,
            "target": labels["short"],
            "feeder": labels["feeder"],
            "side": "short",
            "px": str(high),
            "qty": str(qty),
            "sweep": pr["n"],
            "ack": ack.strip().splitlines()[0] if ack.strip() else "",
        }
        pending["trades"] = trades
        dense["pending"] = pending
        save_state(state)

    boost = {}
    extreme_sides = []
    if dense.get("v4_enabled"):
        multiplicity = dense_v4_submit_multiplicity(state, pr)
        pending["v4_multiplicity"] = multiplicity
        pending["v4_profile"] = {
            "copy_no": 1,
            "long_offset": str(v4_plan["long_offset"]),
            "short_offset": str(v4_plan["short_offset"]),
            "safety": str(v4_plan["safety"]),
            "required_per_contract": str(v4_plan["required_per_contract"]),
        }
        boost = multiplicity
    elif dense.get("v3_enabled"):
        multiplicity = dense_v3_submit_multiplicity(state, pr, qty, low, high)
        pending["v3_multiplicity"] = multiplicity
        boost = multiplicity
    else:
        extreme_sides = dense_v2_extreme_sides(state, pr["px"])
        if dense.get("v2_enabled") and extreme_sides:
            if "long" in extreme_sides:
                boost["long"] = dense_v2_submit_boost(state, pr, "long", qty, low)
            if "short" in extreme_sides:
                boost["short"] = dense_v2_submit_boost(state, pr, "short", qty, high)
            pending["v2_boost"] = boost

    pending["status"] = "submitted"
    pending["submitted_at"] = datetime.now(timezone.utc).isoformat()
    pending["trade_sweep"] = pr["n"]
    pending["ref"] = str(pr["px"])
    pending["low"] = str(low)
    pending["high"] = str(high)
    pending["qty"] = str(qty)
    pending["offset"] = str(offset)
    if v4_plan is not None:
        pending["mode"] = "v4"
        pending["long_offset"] = str(v4_plan["long_offset"])
        pending["short_offset"] = str(v4_plan["short_offset"])
        pending["safety"] = str(v4_plan["safety"])
    dense.setdefault("tickets", []).append(pending)
    dense["last_ticket"] = pending
    dense["pending"] = None
    dense["submitted_sets"] = len(dense["tickets"])
    dense_v2_update_bounds(state, pr["px"])
    save_state(state)
    return {
        "event": "dense_ticket_submitted",
        "index": pending["index"],
        "sweep": pr["n"],
        "ref": str(pr["px"]),
        "low": str(low),
        "high": str(high),
        "qty": str(qty),
        "long": labels["long"],
        "short": labels["short"],
        "feeder": labels["feeder"],
        "offset": str(offset),
        "extreme_sides": extreme_sides,
        "boost": boost,
        "v3_multiplicity": pending.get("v3_multiplicity"),
        "v4_multiplicity": pending.get("v4_multiplicity"),
        "v4_profile": pending.get("v4_profile"),
    }


def dense_autopilot_step(state: dict, now: datetime) -> dict:
    dense = state.setdefault("dense", {})
    pr = fresh_price(max_age=10**9)

    pending = dense.get("pending")
    if not isinstance(pending, dict) or pending.get("status") in ("waiting_room", "registering"):
        pending = dense_register_pending(state, pr["n"])

    maintenance = dense_room_maintenance(state, pr)
    if maintenance:
        return maintenance

    pending = dense_register_pending(state, pr["n"])

    if dense.get("v3_enabled") or dense.get("v4_enabled"):
        reserve_event = dense_v3_maintain_reserve(state, pr["n"])
    else:
        reserve_event = dense_v2_maintain_reserve(state, pr["n"])
    if reserve_event:
        dense["last_reserve_event"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            **reserve_event,
        }
        save_state(state)

    if (
        not (dense.get("v3_enabled") or dense.get("v4_enabled"))
        and pr["age_s"] is not None
        and int(pr["age_s"]) > 120
    ):
        return {
            "event": "dense_wait_fresh_ref",
            "sweep": pr["n"],
            "age_s": pr["age_s"],
            "pending_index": (dense.get("pending") or {}).get("index"),
            "pending_status": (dense.get("pending") or {}).get("status"),
        }

    # 1. Current-sweep V4 gets the first executable strategy slot.
    v4_wait = None
    submitted = dense_submit_pending(state, pr)
    if submitted and submitted.get("event") == "dense_ticket_submitted":
        dense["last_seen_sweep"] = pr["n"]
        save_state(state)
        next_pending = dense_register_pending(state, pr["n"])
        submitted["next_batch"] = next_pending["index"]
        return submitted
    if submitted:
        v4_wait = submitted

    last_ticket = dense.get("last_ticket") or {}
    try:
        v4_done_this_sweep = (
            last_ticket.get("mode") == "v4"
            and last_ticket.get("status") == "submitted"
            and int(last_ticket.get("trade_sweep", -1)) == int(pr["n"])
        )
    except Exception:
        v4_done_this_sweep = False

    # 2. Manage an already-open V5b only. No pending/new V5b work can preempt
    # an active V5a staged close.
    compound = dense_v5b_step(
        state, pr, allow_new=False, allow_pending=False
    )
    if compound:
        return compound

    # 3. Continue an already-started V5a staged close.
    if isinstance(dense.get("v5a_active"), dict):
        harvest = dense_v5a_harvest_step(state, pr)
        if harvest:
            return harvest

    if v4_wait:
        return v4_wait

    # 4. Only after V4 and active V5 risk management are clear may pending/new
    # V5b housekeeping progress. New opens remain review-paused.
    if v4_done_this_sweep:
        compound = dense_v5b_step(
            state, pr, allow_new=True, allow_pending=True
        )
        if compound:
            return compound

    # 5. New V5a harvests are review-paused until projected locked-value logic
    # is implemented and revalidated.
    if v4_done_this_sweep and not isinstance(dense.get("v5a_active"), dict):
        harvest = dense_v5a_harvest_step(state, pr)
        if harvest:
            return harvest

    last_seen_sweep = dense.get("last_seen_sweep")
    if last_seen_sweep == pr["n"]:
        return {
            "event": "dense_heartbeat",
            "sweep": pr["n"],
            "ref": str(pr["px"]),
            "age_s": pr["age_s"],
            "submitted_sets": len(dense.get("tickets") or []),
            "pending_index": (dense.get("pending") or {}).get("index"),
        }

    dense["last_seen_sweep"] = pr["n"]
    save_state(state)

    pending = dense_register_pending(state, pr["n"])
    return {
        "event": "dense_batch_registered",
        "index": pending["index"],
        "sweep": pr["n"],
        "ready_after_sweep": pending.get("ready_after_sweep"),
        "labels": pending["labels"],
    }


def fleet_registration_evidence(state: dict) -> dict:
    """Verify the 51 non-controller registrations are still present in our room.

    Public flow posts intentionally omit most minted DIDs when the 4096-byte room
    message cap is reached. Therefore absence from flow.mints is not a mint failure.
    The controller is proven owner indirectly once its room registration appears in
    referee flow; the remaining 51 registrations are checked byte-for-byte in the
    dedicated low-traffic room and we reject any referee missed range naming it.
    """
    controller = state["controller"]
    local = {label: item["did"] for label, item in state["keys"].items()}
    expected = {label: did for label, did in local.items() if label != controller}
    seen: set[str] = set()
    bad_author: list[str] = []

    for rec in parse_export(state["room"]):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "owner" or p.get("season") != SEASON:
            continue
        did = p.get("key")
        if did not in expected.values():
            continue
        if rec.get("from") != did:
            bad_author.append(did)
            continue
        seen.add(did)

    flow_rows = parse_export("d-close1-flow")
    room_missed = []
    for rec in flow_rows:
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        missed = p.get("missed") or []
        if state["room"] in json.dumps(missed, separators=(",", ":"), ensure_ascii=False):
            room_missed.append({"n": p.get("n"), "missed": missed})

    missing_labels = [label for label, did in expected.items() if did not in seen]
    return {
        "expected": len(expected),
        "seen": len(seen),
        "missing_labels": missing_labels,
        "bad_author": bad_author,
        "room_missed": room_missed,
    }


def fleet_gate(state: dict, max_age: int = 120) -> dict:
    pr = fresh_price(max_age=10**9)
    flow_rows = parse_export("d-close1-flow")
    visible_mints: set[str] = set()
    latest_flow = None
    omitted_mints = 0

    for rec in flow_rows:
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        latest_flow = p
        collect_dids(p.get("mints"), visible_mints)
        omitted = p.get("omitted") or {}
        if isinstance(omitted, dict):
            try:
                omitted_mints += int(omitted.get("mints") or 0)
            except Exception:
                pass

    room_ok = room_registration_confirmed(state)

    st = latest_payload("d-close1-state", "state")
    local = {label: item["did"] for label, item in state["keys"].items()}
    visible_local = [label for label, did in local.items() if did in visible_mints]
    reg = fleet_registration_evidence(state)

    flow_n = int(latest_flow["n"]) if latest_flow and latest_flow.get("n") is not None else None
    state_n = int(st["n"]) if st and st.get("n") is not None else None
    age = pr["age_s"]
    latest_missed = latest_flow.get("missed") if latest_flow else None

    checks = {
        "fresh": age is None or int(age) <= max_age,
        "room_registered": room_ok,
        "flow_current": flow_n == pr["n"],
        "state_current": state_n == pr["n"],
        "dedicated_registrations": reg["seen"] == reg["expected"] and not reg["bad_author"],
        "dedicated_room_no_missed_ranges": not reg["room_missed"],
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "sweep": pr["n"],
        "ref": str(pr["px"]),
        "age_s": age,
        "flow_sweep": flow_n,
        "state_sweep": state_n,
        "room": state["room"],
        "visible_minted": len(visible_local),
        "total": len(local),
        "omitted_mints": omitted_mints,
        "registration_seen": reg["seen"],
        "registration_expected": reg["expected"],
        "registration_missing": reg["missing_labels"],
        "registration_bad_author": reg["bad_author"],
        "room_missed": reg["room_missed"],
        "latest_missed": latest_missed,
    }


def require_fleet_gate(state: dict) -> dict:
    report = fleet_gate(state)
    if not report["pass"]:
        raise SystemExit(
            "fleet gate BLOCKED; run 'gate' and resolve failed checks before trading"
        )
    return report


def fresh_price(max_age=600) -> dict:
    p = latest_payload("d-close1-price", "price")
    if not p:
        raise RuntimeError("no price post found")
    ref = p.get("ref") or {}
    px = Decimal(str(ref.get("px")))

    reported_age = p.get("age_s")
    derived_age = None
    if ref.get("time"):
        try:
            ts = datetime.fromisoformat(str(ref["time"]).replace("Z", "+00:00"))
            derived_age = max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
        except Exception:
            derived_age = None

    ages = []
    for value in (reported_age, derived_age):
        if value is None:
            continue
        try:
            ages.append(int(value))
        except Exception:
            pass
    age = max(ages) if ages else None

    if age is not None and age > max_age:
        raise RuntimeError(
            f"stale referee reference: effective_age_s={age} > {max_age} "
            f"(reported_age_s={reported_age}, derived_age_s={derived_age})"
        )
    n = int(p["n"])
    return {
        "n": n,
        "px": px,
        "age_s": age,
        "reported_age_s": reported_age,
        "derived_age_s": derived_age,
        "raw": p,
    }


def cmd_ids(_args) -> None:
    state = load_state()
    print("label,did")
    for label in make_labels():
        item = state["keys"].get(label)
        if item:
            print(f"{label},{item['did']}")


def cmd_status(_args) -> None:
    pr = fresh_price(max_age=10**9)
    st = latest_payload("d-close1-state", "state")
    pnl = latest_payload("d-close1-pnl", "pnl")
    print("sweep:", pr["n"], "ref:", pr["px"], "age_s:", pr["age_s"])
    if st:
        print("owners:", st.get("owners"), "rooms:", st.get("rooms"))
    if pnl:
        print("mark:", pnl.get("mark"))
        top = pnl.get("top")
        if top is not None:
            print("top:", json.dumps(top, ensure_ascii=False)[:2000])


def cmd_gate(_args) -> None:
    state = load_state()
    report = fleet_gate(state)
    print("sweep:", report["sweep"], "ref:", report["ref"], "age_s:", report["age_s"])
    print("flow_sweep:", report["flow_sweep"], "state_sweep:", report["state_sweep"])
    print("room:", report["room"], "registered:", report["checks"]["room_registered"])
    print(
        "visible mint subset:",
        f'{report["visible_minted"]}/{report["total"]}',
        "(informational only; flow posts may omit minted DIDs)",
    )
    print("flow omitted_mints total in retained window:", report["omitted_mints"])
    print(
        "dedicated registrations:",
        f'{report["registration_seen"]}/{report["registration_expected"]}',
    )
    if report["registration_missing"]:
        print("registration missing:", ",".join(report["registration_missing"]))
    if report["registration_bad_author"]:
        print("registration bad_author:", ",".join(report["registration_bad_author"]))
    print("dedicated room missed ranges:", report["room_missed"])
    print("latest missed:", report["latest_missed"])
    for name, ok in report["checks"].items():
        print(f"check {name}:", "PASS" if ok else "FAIL")
    print("GATE:", "PASS_OPEN_ALLOWED" if report["pass"] else "BLOCK")


def cmd_bootstrap(args) -> None:
    state = load_state()
    controller = state["controller"]
    room = state["room"]
    did = state["keys"][controller]["did"]

    print("register controller in close1")
    print(post_signed(state, "close1", controller, owner_text(did)).strip())

    print("request dedicated room registration")
    print(post_signed(state, "close1", controller, room_text(room)).strip())

    deadline = time.time() + args.wait
    while time.time() < deadline:
        try:
            if room_seen(room):
                print("room is visible in referee flow:", room)
                break
        except Exception as e:
            print("room check warning:", e)
        time.sleep(20)
    else:
        raise SystemExit(
            f"room {room} not observed in d-close1-flow within {args.wait}s; "
            "do not register fleet yet; retry bootstrap later"
        )

    labels = [x for x in make_labels() if x != controller]
    print(f"registering {len(labels)} remaining keys in {room}")
    for i, label in enumerate(labels, 1):
        did = state["keys"][label]["did"]
        try:
            post_signed(state, room, label, owner_text(did))
            print(f"{i:02d}/{len(labels)} {label} {did}")
        except Exception as e:
            print(f"FAILED {label}: {e}")
        time.sleep(args.delay)
    print("registration messages sent; wait at least one fresh sweep before opening positions")


def q_for_cash(cash: Decimal, px: Decimal) -> Decimal:
    q = Decimal("0.95") * cash / (px * Decimal("1.04"))
    return q.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def build_trade(state: dict, room: str, maker_label: str, taker_label: str,
                side: str, qty: Decimal, px: Decimal, until: int, trade_id: str) -> str:
    maker = state["keys"][maker_label]
    taker = state["keys"][taker_label]
    terms = {
        "id": trade_id,
        "maker": maker["did"],
        "px": f"{px:.2f}",
        "qty": f"{qty:.2f}",
        "side": side,
        "taker": taker["did"],
        "until": int(until),
    }
    can = canonical_terms(terms)
    maker_sig = sign(maker["seed"], f"{SEASON}|terms|{can}")
    taker_sig = sign(taker["seed"], f"{SEASON}|accept|{can}|{taker['did']}")
    msg = {
        "t": "trade",
        "season": SEASON,
        "terms": terms,
        "taker": taker["did"],
        "maker_sig": maker_sig,
        "taker_sig": taker_sig,
    }
    return compact(msg)


def submit_pair(state: dict, long_label: str, short_label: str, prefix: str) -> dict:
    pr = fresh_price(max_age=600)
    if pr["age_s"] is not None and int(pr["age_s"]) > 120:
        raise RuntimeError(
            f"reference age_s={pr['age_s']} is above preferred 120s; "
            "wait for a fresher sweep rather than forcing entry"
        )
    px = pr["px"]
    qty = q_for_cash(Decimal("10000"), px)
    tid = f"{prefix}-{int(time.time())}"
    text = build_trade(
        state, state["room"], long_label, short_label,
        "buy", qty, px, pr["n"] + 2, tid,
    )
    response = post_signed(state, state["room"], long_label, text)
    submission = None
    for rec in reversed(parse_export(state["room"])):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "trade":
            continue
        if ((p.get("terms") or {}).get("id")) == tid:
            submission = {
                "seq": rec.get("seq"),
                "ts": rec.get("ts"),
                "from": rec.get("from"),
            }
            break
    return {
        "trade_id": tid,
        "long": long_label,
        "short": short_label,
        "qty": str(qty),
        "px": str(px),
        "sweep": pr["n"],
        "submission": submission,
        "post_ack": response.strip().splitlines()[0] if response.strip() else "",
    }


def open_static_cohort(state: dict, cohort: int) -> dict:
    if not 1 <= cohort <= 16:
        raise RuntimeError("cohort must be 1..16")
    k = f"{cohort:02d}"
    existing = state.setdefault("static", {}).get(k)
    if existing:
        return {"status": "already_submitted", "cohort": k, "trade": existing}

    require_fleet_gate(state)
    res = submit_pair(state, f"TIME-{k}-L", f"TIME-{k}-S", f"t{k}")
    state["static"][k] = res
    save_state(state)
    return {"status": "submitted", "cohort": k, "trade": res}


def cmd_open_static(args) -> None:
    state = load_state()
    result = open_static_cohort(state, args.cohort)
    if result["status"] == "already_submitted":
        print("static cohort already submitted; refusing duplicate:", result["cohort"])
    print(json.dumps(result, indent=2))


def contains_value(value, needle: str) -> bool:
    if isinstance(value, str):
        return needle in value
    if isinstance(value, list):
        return any(contains_value(item, needle) for item in value)
    if isinstance(value, dict):
        return any(contains_value(item, needle) for item in value.values())
    return False


def matching_fragment(value, needle: str):
    if isinstance(value, str):
        return value if needle in value else None
    if isinstance(value, list):
        out = [item for item in value if contains_value(item, needle)]
        return out or None
    if isinstance(value, dict):
        out = {k: v for k, v in value.items() if contains_value(v, needle)}
        return out or None
    return None


def cmd_check_trade(args) -> None:
    state = load_state()

    if args.trade_id:
        trade_id = args.trade_id
    elif args.cohort is not None:
        k = f"{args.cohort:02d}"
        rec = state.get("static", {}).get(k)
        if not rec:
            raise SystemExit(f"no saved static cohort {k}")
        trade_id = rec["trade_id"]
    else:
        raise SystemExit("provide --trade-id or --cohort")

    submission = None
    for rec in parse_export(state["room"]):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "trade":
            continue
        if ((p.get("terms") or {}).get("id")) == trade_id:
            submission = {
                "seq": rec.get("seq"),
                "ts": rec.get("ts"),
                "from": rec.get("from"),
            }
            break

    outcome = None
    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        if contains_value(p.get("settled"), trade_id):
            outcome = {
                "status": "settled",
                "sweep": p.get("n"),
                "detail": matching_fragment(p.get("settled"), trade_id),
            }
        if contains_value(p.get("void"), trade_id):
            outcome = {
                "status": "void",
                "sweep": p.get("n"),
                "detail": matching_fragment(p.get("void"), trade_id),
            }

    pr = fresh_price(max_age=10**9)
    print("trade_id:", trade_id)
    print("submission:", json.dumps(submission, ensure_ascii=False))
    print("current_sweep:", pr["n"], "ref:", pr["px"], "age_s:", pr["age_s"])

    if outcome:
        print("OUTCOME:", outcome["status"].upper())
        print("outcome_sweep:", outcome["sweep"])
        print("detail:", json.dumps(outcome["detail"], ensure_ascii=False))
        return

    omitted = {"settled": 0, "void": 0}
    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        om = p.get("omitted") or {}
        if isinstance(om, dict):
            for name in omitted:
                try:
                    omitted[name] += int(om.get(name) or 0)
                except Exception:
                    pass

    print("OUTCOME: NOT_VISIBLE")
    print("omitted_outcomes_in_retained_window:", json.dumps(omitted))
    print(
        "note: NOT_VISIBLE is inconclusive when referee flow reports omitted settled/void entries; "
        "do not resubmit the same trade id"
    )


def trade_submissions_in_room(room: str, trade_ids: set[str]) -> dict[str, dict]:
    """Return locally observable signed trade submissions for requested IDs.

    A record counts only when the room export contains the exact trade id and
    the technocore author is one of the countersigned parties. This is used as
    a prerequisite before local reconstruction when compact referee flow omitted
    the authoritative settled/void entry.
    """
    wanted = {str(tid) for tid in trade_ids if tid}
    if not wanted:
        return {}
    out: dict[str, dict] = {}
    for rec in parse_export(room):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "trade" or p.get("season") != SEASON:
            continue
        terms = p.get("terms") or {}
        tid = terms.get("id")
        if tid not in wanted:
            continue
        author = rec.get("from")
        maker = terms.get("maker")
        taker = p.get("taker") or terms.get("taker")
        if author not in (maker, taker):
            continue
        out[tid] = {
            "seq": rec.get("seq"),
            "ts": rec.get("ts"),
            "from": author,
            "maker": maker,
            "taker": taker,
        }
        if len(out) == len(wanted):
            break
    return out


def trade_outcome_from_flow(trade_id: str) -> dict:
    outcome = None
    omitted = {"settled": 0, "void": 0}
    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        if contains_value(p.get("settled"), trade_id):
            outcome = {
                "status": "settled",
                "sweep": p.get("n"),
                "detail": matching_fragment(p.get("settled"), trade_id),
            }
        if contains_value(p.get("void"), trade_id):
            outcome = {
                "status": "void",
                "sweep": p.get("n"),
                "detail": matching_fragment(p.get("void"), trade_id),
            }
        om = p.get("omitted") or {}
        if isinstance(om, dict):
            for name in omitted:
                try:
                    omitted[name] += int(om.get(name) or 0)
                except Exception:
                    pass
    return {"outcome": outcome, "omitted": omitted}


def cmd_check_bracket(_args) -> None:
    state = load_state()
    bracket = state.get("bracket") or {}
    pairs = bracket.get("pairs") or []
    if not pairs:
        raise SystemExit("no bracket pairs saved")

    pr = fresh_price(max_age=10**9)
    print("bracket_round:", bracket.get("round"), "status:", bracket.get("status"))
    print("pairs_saved:", len(pairs))
    print("current_sweep:", pr["n"], "ref:", pr["px"], "age_s:", pr["age_s"])

    counts = {"settled": 0, "void": 0, "not_visible": 0}
    omitted_seen = {"settled": 0, "void": 0}

    for pair in pairs:
        trade_id = pair.get("trade_id")
        if not trade_id:
            continue
        info = trade_outcome_from_flow(trade_id)
        outcome = info["outcome"]
        omitted_seen = info["omitted"]
        if outcome:
            status = outcome["status"]
            counts[status] += 1
            print(
                trade_id,
                pair.get("long"),
                pair.get("short"),
                "OUTCOME:",
                status.upper(),
                "sweep:",
                outcome.get("sweep"),
            )
        else:
            counts["not_visible"] += 1
            print(
                trade_id,
                pair.get("long"),
                pair.get("short"),
                "OUTCOME: NOT_VISIBLE",
            )

    print("summary:", json.dumps(counts, sort_keys=True))
    print("retained_flow_omitted:", json.dumps(omitted_seen, sort_keys=True))
    if counts["void"]:
        print("BRACKET_CHECK: REVIEW_VOID")
    elif counts["settled"] == len(pairs):
        print("BRACKET_CHECK: ALL_VISIBLE_SETTLED")
    elif counts["not_visible"] and (omitted_seen["settled"] or omitted_seen["void"]):
        print("BRACKET_CHECK: OUTCOMES_PARTLY_OR_FULLY_OMITTED")
    else:
        print("BRACKET_CHECK: PENDING_OR_INCONCLUSIVE")



def flatten_dicts(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from flatten_dicts(item)
    elif isinstance(value, list):
        for item in value:
            yield from flatten_dicts(item)


def board_rows(pnl: dict | None) -> list[dict]:
    if not isinstance(pnl, dict):
        return []
    top = pnl.get("top")
    if not isinstance(top, list):
        return []
    rows = []
    for i, item in enumerate(top, 1):
        if isinstance(item, dict):
            row = dict(item)
        else:
            row = {"raw": item}
        row["_board_index"] = i
        rows.append(row)
    return rows


def local_board_matches(state: dict, rows: list[dict]) -> list[dict]:
    did_to_label = {item["did"]: label for label, item in state["keys"].items()}
    matches = []
    for row in rows:
        raw = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        for did, label in did_to_label.items():
            if did in raw:
                matches.append({"label": label, "did": did, "row": row})
                break
    return matches


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


def _rec_time(rec: dict) -> datetime | None:
    ts = rec.get("ts")
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _price_timeline() -> list[tuple[datetime, int, Decimal]]:
    out = []
    for rec in parse_export("d-close1-price"):
        p = rec.get("_payload")
        dt = _rec_time(rec)
        if not isinstance(p, dict) or p.get("t") != "price" or dt is None:
            continue
        try:
            out.append((dt, int(p["n"]), Decimal(str((p.get("ref") or {})["px"]))))
        except Exception:
            continue
    out.sort(key=lambda x: x[0])
    return out


def _source_ref_for_time(
    dt: datetime | None,
    timeline: list[tuple[datetime, int, Decimal]],
) -> tuple[int | None, Decimal | None]:
    if dt is None:
        return None, None
    for pdt, n, px in reversed(timeline):
        if pdt <= dt:
            return n, px
    return None, None


def cmd_competitor_scan(args) -> None:
    """Read-only live scan of public Close Call rooms.

    No local keys are posted and no state is modified.
    """
    pr = fresh_price(max_age=10**9)
    pnl_rows = []
    for rec in parse_export("d-close1-pnl"):
        p = rec.get("_payload")
        if isinstance(p, dict) and p.get("t") == "pnl":
            pnl_rows.append(p)
    pnl_rows = pnl_rows[-max(2, int(args.pnl)):]

    print("=== CLOSE CALL COMPETITOR SCAN ===")
    print("ref_sweep:", pr["n"], "ref:", pr["px"], "age_s:", pr["age_s"])

    latest_pairs = []
    latest_mark = None
    if pnl_rows:
        print("\n# recent pnl snapshots")
        for p in pnl_rows:
            pairs = _pnl_pairs(p)
            scores = Counter(str(score) for _, score in pairs)
            leader = max((score for _, score in pairs), default=None)
            common = scores.most_common(1)[0] if scores else (None, 0)
            print(
                "sweep", p.get("n"),
                "mark", p.get("mark"),
                "leader", leader,
                "largest_tie_score", common[0],
                "largest_tie_count", common[1],
                "listed", len(pairs),
            )

        latest = pnl_rows[-1]
        latest_pairs = _pnl_pairs(latest)
        try:
            latest_mark = Decimal(str(latest.get("mark")))
        except Exception:
            latest_mark = None

        print("\n# latest public top")
        for i, (did, score) in enumerate(latest_pairs[:25], 1):
            print(i, did, score)

    price_timeline = _price_timeline()
    positions = latest_payload("d-close1-positions", "positions")
    position_map = {}
    if isinstance(positions, dict):
        print("\n# latest positions summary")
        print(
            "sweep", positions.get("n"),
            "open", positions.get("open"),
            "longs", positions.get("longs"),
            "shorts", positions.get("shorts"),
        )
        print("top_positions:")
        for item in (positions.get("top") or [])[:20]:
            print(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
            try:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    position_map[str(item[0])] = Decimal(str(item[1]))
            except Exception:
                pass

    # Infer the current leaderboard regime from public score sensitivity and any
    # DIDs that overlap the public top-position list.
    if latest_pairs and latest_mark is not None:
        history = defaultdict(list)
        for p in pnl_rows:
            try:
                mark = Decimal(str(p.get("mark")))
                n = int(p.get("n"))
            except Exception:
                continue
            for did, score in _pnl_pairs(p):
                history[did].append((n, mark, score))

        print("\n# current board diagnostics")
        for rank, (did, score) in enumerate(latest_pairs[:25], 1):
            known_pos = position_map.get(did)
            slope_pos = None
            slope_pair = None
            hist = history.get(did) or []
            if len(hist) >= 2:
                # A score-vs-mark slope only equals position while the account
                # did not trade between the two snapshots. Restrict this to
                # consecutive referee sweeps; sparse top-board appearances can
                # span closes/flips and produce absurd pseudo-positions.
                for a, b in reversed(list(zip(hist, hist[1:]))):
                    if b[0] != a[0] + 1:
                        continue
                    dmark = b[1] - a[1]
                    if dmark != 0:
                        slope_pos = (b[2] - a[2]) / dmark
                        slope_pair = (a[0], b[0])
                        break

            pos = known_pos if known_pos is not None else slope_pos
            eff = None
            if pos is not None and abs(pos) >= Decimal("0.1"):
                try:
                    eff = latest_mark - score / pos
                except Exception:
                    eff = None

            if rank <= 12 or known_pos is not None:
                print(
                    "rank", rank,
                    "did", did,
                    "score", score,
                    "known_position", str(known_pos) if known_pos is not None else None,
                    "slope_position_est", str(slope_pos.quantize(Decimal("0.01"))) if slope_pos is not None else None,
                    "slope_pair", slope_pair,
                    "effective_entry_est", str(eff.quantize(Decimal("0.01"))) if eff is not None else None,
                )

        if price_timeline:
            refs = [px for _dt, _n, px in price_timeline]
            min_ref = min(refs)
            max_ref = max(refs)
            max_single_short_quote = max_ref * Decimal("1.05")
            min_single_long_quote = min_ref * Decimal("0.95")
            print("\n# referee price-history reachability")
            print(
                "price_posts", len(price_timeline),
                "min_ref", min_ref,
                "max_ref", max_ref,
                "min_5pct_buy", min_single_long_quote.quantize(Decimal("0.01")),
                "max_5pct_sell", max_single_short_quote.quantize(Decimal("0.01")),
            )

        if latest_pairs:
            leader_score = latest_pairs[0][1]
            leader_cohort = [did for did, score in latest_pairs if score == leader_score]
            rep = leader_cohort[0] if leader_cohort else latest_pairs[0][0]
            hist = history.get(rep) or []
            slope_series = []
            sparse_transitions = []
            for a, b in zip(hist, hist[1:]):
                dmark = b[1] - a[1]
                if dmark == 0:
                    continue
                slope = (b[2] - a[2]) / dmark
                if b[0] == a[0] + 1:
                    slope_series.append((a[0], b[0], slope))
                else:
                    sparse_transitions.append((a[0], b[0], slope))
            signs = set()
            for _a, _b, slope in slope_series:
                if slope > Decimal("5"):
                    signs.add("long")
                elif slope < Decimal("-5"):
                    signs.add("short")
                else:
                    signs.add("flat")
            print("\n# current leader cohort path diagnostics")
            print(
                "leader_tie_count", len(leader_cohort),
                "representative_did", rep,
                "appearances_in_requested_pnl_window", len(hist),
                "first_seen_sweep", hist[0][0] if hist else None,
                "last_seen_sweep", hist[-1][0] if hist else None,
                "observed_consecutive_position_regimes", sorted(signs),
                "flip_evidence_from_consecutive_snapshots", ("long" in signs and "short" in signs),
                "sparse_transition_count", len(sparse_transitions),
            )
            if slope_series:
                print("recent_consecutive_position_slopes:")
                for a_n, b_n, slope in slope_series[-12:]:
                    print(a_n, "->", b_n, str(slope.quantize(Decimal("0.01"))))
            if sparse_transitions:
                print("recent_sparse_transition_slopes_NOT_positions:")
                for a_n, b_n, slope in sparse_transitions[-6:]:
                    print(a_n, "->", b_n, str(slope.quantize(Decimal("0.01"))))

            if hist:
                cur_score = hist[-1][2]
                cur_mark = hist[-1][1]
                recent_pos = slope_series[-1][2] if slope_series else None
                if recent_pos is not None and abs(recent_pos) >= Decimal("0.1"):
                    synthetic_entry = cur_mark - cur_score / recent_pos
                    reachable = None
                    if price_timeline:
                        if recent_pos < 0:
                            reachable = synthetic_entry <= max(px for _dt, _n, px in price_timeline) * Decimal("1.05")
                        else:
                            reachable = synthetic_entry >= min(px for _dt, _n, px in price_timeline) * Decimal("0.95")
                    print(
                        "synthetic_effective_entry", synthetic_entry.quantize(Decimal("0.01")),
                        "single_trade_reachable_from_visible_ref_history", reachable,
                    )
                    print(
                        "synthetic_entry_note:",
                        "If reachability is False, realized PnL/cash carry is mathematically required. "
                        "If True, a historical single entry remains possible and flip/reinvestment is not proven."
                    )

    rows = parse_export("close1")
    sample = rows[-max(1, int(args.sample)):]
    kinds = Counter()
    templates = Counter()
    template_makers = defaultdict(set)
    deviations = Counter()
    large_terms = []
    top_dids = {did for did, _ in latest_pairs[:12]}
    top_hits = defaultdict(list)

    for rec in sample:
        p = rec.get("_payload")
        if not isinstance(p, dict):
            continue
        kind = p.get("t") or "?"
        kinds[kind] += 1
        if kind not in ("trade", "offer"):
            continue
        terms = p.get("terms")
        if not isinstance(terms, dict):
            continue
        key = (
            str(terms.get("side")),
            str(terms.get("px")),
            str(terms.get("qty")),
            str(terms.get("until")),
        )
        templates[key] += 1
        if terms.get("maker"):
            template_makers[key].add(str(terms.get("maker")))

        rec_dt = _rec_time(rec)
        source_sweep, source_ref = _source_ref_for_time(rec_dt, price_timeline)

        try:
            px = Decimal(str(terms["px"]))
            qty = Decimal(str(terms["qty"]))
            dev = None
            if source_ref is not None:
                dev = (px / source_ref - Decimal("1")) * Decimal("100")
            if qty >= Decimal("40"):
                if dev is not None:
                    bucket = dev.quantize(Decimal("0.1"))
                    deviations[str(bucket)] += 1
                large_terms.append({
                    "side": terms.get("side"),
                    "px": str(px),
                    "qty": str(qty),
                    "source_sweep": source_sweep,
                    "source_ref": str(source_ref) if source_ref is not None else None,
                    "dev_pct": str(dev.quantize(Decimal("0.01"))) if dev is not None else None,
                    "id": terms.get("id"),
                })
        except Exception:
            pass

        maker = str(terms.get("maker")) if terms.get("maker") is not None else None
        taker = p.get("taker")
        if maker in top_dids:
            top_hits[maker].append({
                "role": "maker",
                "side": terms.get("side"),
                "px": terms.get("px"),
                "qty": terms.get("qty"),
                "until": terms.get("until"),
                "source_sweep": source_sweep,
                "source_ref": str(source_ref) if source_ref is not None else None,
                "ts": rec.get("ts"),
                "id": terms.get("id"),
            })
        if isinstance(taker, str) and taker in top_dids:
            top_hits[taker].append({
                "role": "taker",
                "maker_side": terms.get("side"),
                "px": terms.get("px"),
                "qty": terms.get("qty"),
                "until": terms.get("until"),
                "source_sweep": source_sweep,
                "source_ref": str(source_ref) if source_ref is not None else None,
                "ts": rec.get("ts"),
                "id": terms.get("id"),
            })

    print("\n# recent close1 public sample")
    print("messages:", len(sample), "kinds:", json.dumps(dict(kinds), sort_keys=True))
    print("top_templates:")
    for key, count in templates.most_common(10):
        print(
            count,
            "makers", len(template_makers[key]),
            "side", key[0],
            "px", key[1],
            "qty", key[2],
            "until", key[3],
        )

    print("large_qty_actual_submission_deviation_buckets_pct:", json.dumps(dict(deviations), sort_keys=True))
    print("recent_large_terms:")
    for item in large_terms[-20:]:
        print(json.dumps(item, sort_keys=True))

    if top_hits:
        print("\n# recent trades involving current top DIDs")
        rank_map = {did: i for i, (did, _) in enumerate(latest_pairs[:25], 1)}
        for did in sorted(top_hits, key=lambda x: rank_map.get(x, 999)):
            print("rank", rank_map.get(did), did)
            for item in top_hits[did][-5:]:
                print(json.dumps(item, ensure_ascii=False, sort_keys=True))





def _leader_registered_rooms() -> list[str]:
    """Rooms ever listed by the referee, plus the always-listed public room."""
    seen = {"close1"}
    order = ["close1"]

    def collect(value):
        if isinstance(value, str):
            if value not in seen and not value.startswith("d-close1"):
                seen.add(value)
                order.append(value)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                collect(item)
            return
        if isinstance(value, dict):
            for item in value.values():
                collect(item)

    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if isinstance(p, dict) and p.get("t") == "flow":
            collect(p.get("rooms"))
    return order


def _leader_trade_perspective(did: str, payload: dict) -> dict | None:
    terms = payload.get("terms") or {}
    maker = terms.get("maker")
    taker = payload.get("taker") or terms.get("taker")
    side = terms.get("side")
    try:
        qty = Decimal(str(terms["qty"]))
        px = Decimal(str(terms["px"]))
    except Exception:
        return None

    if did == maker:
        role = "maker"
        action = side
    elif did == taker:
        role = "taker"
        action = "buy" if side == "sell" else "sell" if side == "buy" else None
    else:
        return None
    if action not in ("buy", "sell"):
        return None
    signed_qty = qty if action == "buy" else -qty
    return {
        "role": role,
        "action": action,
        "signed_qty": signed_qty,
        "qty": qty,
        "px": px,
        "maker": maker,
        "taker": taker,
    }


def _leader_flow_outcomes(trade_ids: set[str]) -> dict[str, dict]:
    """Visible compact-flow outcomes for selected trade ids."""
    wanted = {str(x) for x in trade_ids if x}
    out = {}
    if not wanted:
        return out
    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "flow":
            continue
        try:
            n = int(p["n"])
        except Exception:
            continue
        settled = p.get("settled")
        void = p.get("void")
        for tid in wanted:
            if tid in out:
                continue
            if contains_value(settled, tid):
                out[tid] = {"status": "settled", "sweep": n}
                continue
            if contains_value(void, tid):
                reason = None
                if isinstance(void, (list, tuple)):
                    for item in void:
                        if isinstance(item, (list, tuple)) and item and item[0] == tid:
                            reason = item[1] if len(item) > 1 else None
                            break
                        if isinstance(item, dict) and item.get("id") == tid:
                            reason = item.get("reason") or item.get("outcome")
                            break
                out[tid] = {"status": "void", "sweep": n, "reason": reason}
    return out


def _leader_scan_trades(
    targets: set[str],
    room_mode: str = "registered",
    room_limit: int = 0,
) -> dict:
    rooms = ["close1"] if room_mode == "public" else _leader_registered_rooms()
    if room_limit and room_limit > 0:
        rooms = rooms[:room_limit]

    price_timeline = _price_timeline()
    by_did = {did: [] for did in targets}
    failed = []
    scanned = []

    for room in rooms:
        try:
            rows = parse_export(room)
        except Exception as e:
            failed.append({"room": room, "error": str(e)})
            continue
        scanned.append(room)
        for rec in rows:
            p = rec.get("_payload")
            if not isinstance(p, dict) or p.get("t") != "trade" or p.get("season") != SEASON:
                continue
            terms = p.get("terms") or {}
            tid = terms.get("id")
            if not isinstance(tid, str):
                continue
            dt = _rec_time(rec)
            source_sweep, source_ref = _source_ref_for_time(dt, price_timeline)
            for did in targets:
                view = _leader_trade_perspective(did, p)
                if view is None:
                    continue
                by_did[did].append({
                    "trade_id": tid,
                    "room": room,
                    "seq": rec.get("seq"),
                    "ts": rec.get("ts"),
                    "publisher": rec.get("from"),
                    "source_sweep": source_sweep,
                    "source_ref": source_ref,
                    "first_possible_sweep": (
                        source_sweep + 1 if source_sweep is not None else None
                    ),
                    "until": terms.get("until"),
                    **view,
                })

    trade_ids = {
        x["trade_id"]
        for rows in by_did.values()
        for x in rows
        if x.get("trade_id")
    }
    outcomes = _leader_flow_outcomes(trade_ids)
    for did, rows in by_did.items():
        rows.sort(key=lambda x: (
            x.get("ts") or "",
            int(x.get("seq") or 0),
            x.get("room") or "",
        ))
        for row in rows:
            outcome = outcomes.get(row["trade_id"])
            row["outcome"] = outcome.get("status") if outcome else "not_visible"
            row["outcome_sweep"] = outcome.get("sweep") if outcome else None
            row["void_reason"] = outcome.get("reason") if outcome else None

    return {
        "room_mode": room_mode,
        "rooms_discovered": len(_leader_registered_rooms()),
        "rooms_scanned": scanned,
        "rooms_failed": failed,
        "trades": by_did,
    }


def _leader_position_history(targets: set[str]) -> dict[str, dict[int, Decimal]]:
    out = {did: {} for did in targets}
    for rec in parse_export("d-close1-positions"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "positions":
            continue
        try:
            n = int(p["n"])
        except Exception:
            continue
        pos_map = _v42_position_map(p)
        for did in targets:
            if did in pos_map:
                out[did][n] = pos_map[did]
    return out


def _leader_pnl_history(targets: set[str]) -> dict[str, list[dict]]:
    out = {did: [] for did in targets}
    for rec in parse_export("d-close1-pnl"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "pnl":
            continue
        try:
            n = int(p["n"])
            mark = Decimal(str(p["mark"]))
        except Exception:
            continue
        score_map = dict(_pnl_pairs(p))
        for did in targets:
            if did in score_map:
                out[did].append({
                    "sweep": n,
                    "mark": mark,
                    "score": score_map[did],
                })
    return out


def _leader_price_reachability() -> list[dict]:
    """Cumulative legal quote and fee-adjusted score envelope by sweep.

    For a fresh long opened at legal price p in a sweep with closing price c,
    the buyer's score contribution at a later mark m is:

        qty * (m - p) - max(1% * qty * p, qty * (c - p))
      = qty * (m - max(1.01 * p, c))

    The minimum fee-adjusted effective long cost in a sweep is therefore
    max(1.01 * lower_limit, close).

    Symmetrically, a fresh short's best fee-adjusted effective sale price is
    min(0.99 * upper_limit, close).
    """
    out = []
    min_buy = None
    max_sell = None
    min_effective_long_cost = None
    max_effective_short_sale = None
    cent = Decimal("0.01")

    for rec in parse_export("d-close1-price"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "price":
            continue
        try:
            n = int(p["n"])
        except Exception:
            continue

        applied = _v41_px(p.get("applied"))
        close = _v41_px(p.get("ref"))
        if applied is None or close is None:
            continue

        low = (applied * Decimal("0.95")).quantize(cent, rounding=ROUND_CEILING)
        high = (applied * Decimal("1.05")).quantize(cent, rounding=ROUND_DOWN)
        effective_long_cost = max(close, Decimal("1.01") * low)
        effective_short_sale = min(close, Decimal("0.99") * high)

        min_buy = low if min_buy is None else min(min_buy, low)
        max_sell = high if max_sell is None else max(max_sell, high)
        min_effective_long_cost = (
            effective_long_cost
            if min_effective_long_cost is None
            else min(min_effective_long_cost, effective_long_cost)
        )
        max_effective_short_sale = (
            effective_short_sale
            if max_effective_short_sale is None
            else max(max_effective_short_sale, effective_short_sale)
        )

        out.append({
            "sweep": n,
            "applied": applied,
            "close": close,
            "lower_limit": low,
            "upper_limit": high,
            "min_legal_buy_seen": min_buy,
            "max_legal_sell_seen": max_sell,
            "best_effective_long_cost_seen": min_effective_long_cost,
            "best_effective_short_sale_seen": max_effective_short_sale,
        })
    return out

def _leader_reach_at_sweep(history: list[dict], sweep: int) -> dict | None:
    found = None
    for row in history:
        if int(row["sweep"]) > int(sweep):
            break
        found = row
    return found


def _leader_min_carry_required(
    score: Decimal,
    mark: Decimal,
    position: Decimal,
    min_legal_buy: Decimal | None,
    max_legal_sell: Decimal | None,
    best_effective_long_cost: Decimal | None = None,
    best_effective_short_sale: Decimal | None = None,
) -> tuple[Decimal | None, Decimal | None]:
    """(synthetic effective entry, conservative realized-carry lower bound).

    The fee-adjusted bounds are stronger than the raw legal-price bounds because
    every settled trade pays at least the 1% base fee and may pay clawback.

    When fee-adjusted history is unavailable, fall back to the older raw-price
    lower bound so callers/tests remain well-defined.
    """
    if position == 0:
        return None, max(score, Decimal("0"))

    synthetic = mark - score / position
    required = Decimal("0")

    if position > 0:
        if best_effective_long_cost is not None:
            max_open_score = position * (mark - best_effective_long_cost)
            required = score - max_open_score
        elif min_legal_buy is not None and synthetic < min_legal_buy:
            required = position * (min_legal_buy - synthetic)
    else:
        qty = abs(position)
        if best_effective_short_sale is not None:
            max_open_score = qty * (best_effective_short_sale - mark)
            required = score - max_open_score
        elif max_legal_sell is not None and synthetic > max_legal_sell:
            required = qty * (synthetic - max_legal_sell)

    return synthetic, max(required, Decimal("0"))

def _leader_transition_kind(prev_pos: Decimal, cur_pos: Decimal) -> str:
    eps = Decimal("0.01")
    p0 = abs(prev_pos) < eps
    c0 = abs(cur_pos) < eps
    if p0 and c0:
        return "flat"
    if p0:
        return "open_long" if cur_pos > 0 else "open_short"
    if c0:
        return "flatten"
    if prev_pos * cur_pos < 0:
        return "flip_to_long" if cur_pos > 0 else "flip_to_short"
    if abs(cur_pos) > abs(prev_pos) + eps:
        return "increase_long" if cur_pos > 0 else "increase_short"
    if abs(cur_pos) + eps < abs(prev_pos):
        return "reduce_long" if cur_pos > 0 else "reduce_short"
    return "hold_long" if cur_pos > 0 else "hold_short"


def _leader_build_path(
    did: str,
    pnl_rows: list[dict],
    pos_by_sweep: dict[int, Decimal],
    reachability: list[dict],
    trades: list[dict],
) -> dict:
    rows = [dict(x) for x in pnl_rows]

    # Weak position fallback from consecutive PnL snapshots. It is useful as a
    # directional diagnostic only. It must not be promoted to a true position
    # transition because trading between snapshots can distort the slope.
    slope = {}
    for a, b in zip(rows, rows[1:]):
        if b["sweep"] != a["sweep"] + 1:
            continue
        dmark = b["mark"] - a["mark"]
        if dmark != 0:
            slope[b["sweep"]] = (b["score"] - a["score"]) / dmark

    for row in rows:
        n = int(row["sweep"])
        if n in pos_by_sweep:
            position = pos_by_sweep[n]
            evidence = "published_position"
        elif n in slope:
            position = slope[n]
            evidence = "consecutive_pnl_slope"
        else:
            position = None
            evidence = "missing"

        row["position"] = position
        row["position_evidence"] = evidence
        reach = _leader_reach_at_sweep(reachability, n)
        row["min_legal_buy_seen"] = reach["min_legal_buy_seen"] if reach else None
        row["max_legal_sell_seen"] = reach["max_legal_sell_seen"] if reach else None
        row["best_effective_long_cost_seen"] = (
            reach["best_effective_long_cost_seen"] if reach else None
        )
        row["best_effective_short_sale_seen"] = (
            reach["best_effective_short_sale_seen"] if reach else None
        )

        if position is not None:
            synthetic, carry_lb = _leader_min_carry_required(
                row["score"],
                row["mark"],
                position,
                row["min_legal_buy_seen"],
                row["max_legal_sell_seen"],
                row["best_effective_long_cost_seen"],
                row["best_effective_short_sale_seen"],
            )
            row["synthetic_effective_entry"] = synthetic
            row["min_realized_carry_required"] = carry_lb
            row["score_intercept"] = row["score"] - position * row["mark"]
            if abs(position) < Decimal("0.01"):
                row["flat_realized_score"] = row["score"]
        else:
            row["synthetic_effective_entry"] = None
            row["min_realized_carry_required"] = None
            row["score_intercept"] = None

    transitions = []
    inferred_diagnostics = []
    for prev, cur in zip(rows, rows[1:]):
        if prev.get("position") is None or cur.get("position") is None:
            continue
        if cur["sweep"] != prev["sweep"] + 1:
            continue

        both_published = (
            prev.get("position_evidence") == "published_position"
            and cur.get("position_evidence") == "published_position"
        )
        kind = _leader_transition_kind(prev["position"], cur["position"])
        hold_expected = (
            prev["score"]
            + prev["position"] * (cur["mark"] - prev["mark"])
        )
        impact = cur["score"] - hold_expected

        base = {
            "from_sweep": prev["sweep"],
            "to_sweep": cur["sweep"],
            "kind": kind,
            "position_before": prev["position"],
            "position_after": cur["position"],
            "delta_position": cur["position"] - prev["position"],
            "score_before": prev["score"],
            "score_after": cur["score"],
            "mark_before": prev["mark"],
            "mark_after": cur["mark"],
            "hold_expected_score": hold_expected,
            "trade_impact_at_current_mark": impact,
            "min_carry_required_after": cur.get("min_realized_carry_required"),
            "synthetic_entry_after": cur.get("synthetic_effective_entry"),
            "position_evidence_before": prev.get("position_evidence"),
            "position_evidence_after": cur.get("position_evidence"),
        }

        if not both_published:
            if not (kind.startswith("hold") and abs(impact) < Decimal("0.01")):
                inferred_diagnostics.append(base)
            continue

        if kind.startswith("hold"):
            continue

        nearby = []
        for trade in trades:
            osweep = trade.get("outcome_sweep")
            first = trade.get("first_possible_sweep")
            if osweep == cur["sweep"] or (
                osweep is None
                and first is not None
                and prev["sweep"] < int(first) <= cur["sweep"]
            ):
                nearby.append({
                    "trade_id": trade["trade_id"],
                    "action": trade["action"],
                    "signed_qty": trade["signed_qty"],
                    "px": trade["px"],
                    "room": trade["room"],
                    "outcome": trade["outcome"],
                    "outcome_sweep": trade["outcome_sweep"],
                })
        base["nearby_trades"] = nearby
        transitions.append(base)

    visible_settled = sum(1 for x in trades if x.get("outcome") == "settled")
    visible_void = sum(1 for x in trades if x.get("outcome") == "void")
    not_visible = sum(1 for x in trades if x.get("outcome") == "not_visible")
    carry_values = [
        x["min_realized_carry_required"]
        for x in rows
        if x.get("min_realized_carry_required") is not None
    ]
    flat_values = [
        x["flat_realized_score"]
        for x in rows
        if x.get("flat_realized_score") is not None
    ]

    return {
        "did": did,
        "first_visible_sweep": rows[0]["sweep"] if rows else None,
        "last_visible_sweep": rows[-1]["sweep"] if rows else None,
        "snapshot_count": len(rows),
        "transition_count": len(transitions),
        "inferred_diagnostic_count": len(inferred_diagnostics),
        "trade_count_found_in_scanned_rooms": len(trades),
        "trade_outcomes": {
            "visible_settled": visible_settled,
            "visible_void": visible_void,
            "not_visible": not_visible,
        },
        "max_min_realized_carry_required": max(carry_values) if carry_values else None,
        "max_flat_realized_score": max(flat_values) if flat_values else None,
        "latest_snapshot": rows[-1] if rows else None,
        "transitions": transitions,
        "inferred_position_diagnostics": inferred_diagnostics,
        "trades": trades,
        "snapshots": rows,
    }

def cmd_leader_path_replay(args) -> None:
    state = load_state()
    pnl = latest_payload("d-close1-pnl", "pnl")
    pairs = _pnl_pairs(pnl)
    our_dids = {str(v.get("did")) for v in state.get("keys", {}).values() if v.get("did")}
    leaders = [
        {"rank": rank, "did": did, "score": score}
        for rank, (did, score) in enumerate(pairs, 1)
        if did not in our_dids
    ][:max(1, int(args.top))]
    if not leaders:
        raise SystemExit("no non-local leaders in public pnl subset")

    targets = {x["did"] for x in leaders}
    pnl_hist = _leader_pnl_history(targets)
    pos_hist = _leader_position_history(targets)
    reachability = _leader_price_reachability()
    trade_scan = _leader_scan_trades(
        targets,
        room_mode=args.rooms,
        room_limit=max(0, int(args.room_limit)),
    )

    paths = []
    for leader in leaders:
        did = leader["did"]
        path = _leader_build_path(
            did,
            pnl_hist.get(did) or [],
            pos_hist.get(did) or {},
            reachability,
            trade_scan["trades"].get(did) or [],
        )
        path["current_public_rank"] = leader["rank"]
        path["current_public_score"] = leader["score"]
        paths.append(path)

    report = {
        "mode": "read_only_leader_path_replay",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pnl_sweep": pnl.get("n") if isinstance(pnl, dict) else None,
        "pnl_mark": pnl.get("mark") if isinstance(pnl, dict) else None,
        "leaders_requested": len(leaders),
        "room_scan": {
            "mode": trade_scan["room_mode"],
            "rooms_discovered": trade_scan["rooms_discovered"],
            "rooms_scanned_count": len(trade_scan["rooms_scanned"]),
            "rooms_failed": trade_scan["rooms_failed"],
        },
        "method_note": (
            "Published PnL/positions are authoritative snapshots. "
            "consecutive_pnl_slope is weaker position evidence. "
            "min_realized_carry_required is a conservative mathematical lower "
            "bound from historical legal quote limits, not a full cash-ledger replay. "
            "Trade outcomes missing from compact flow remain not_visible."
        ),
        "leaders": paths,
    }
    print(json.dumps(report, indent=2, default=str))


def cmd_leader_path_summary(args) -> None:
    state = load_state()
    pnl = latest_payload("d-close1-pnl", "pnl")
    pairs = _pnl_pairs(pnl)
    our_dids = {str(v.get("did")) for v in state.get("keys", {}).values() if v.get("did")}
    leaders = [
        {"rank": rank, "did": did, "score": score}
        for rank, (did, score) in enumerate(pairs, 1)
        if did not in our_dids
    ][:max(1, int(args.top))]
    targets = {x["did"] for x in leaders}
    pnl_hist = _leader_pnl_history(targets)
    pos_hist = _leader_position_history(targets)
    reachability = _leader_price_reachability()
    trade_scan = _leader_scan_trades(
        targets,
        room_mode=args.rooms,
        room_limit=max(0, int(args.room_limit)),
    )

    print(
        "rank,did,current_score,latest_position,latest_position_evidence,"
        "synthetic_entry,min_realized_carry_required,max_min_carry_required,"
        "max_flat_realized_score,transitions,trades_found,visible_settled,"
        "visible_void,not_visible"
    )
    for leader in leaders:
        did = leader["did"]
        path = _leader_build_path(
            did,
            pnl_hist.get(did) or [],
            pos_hist.get(did) or {},
            reachability,
            trade_scan["trades"].get(did) or [],
        )
        latest = path.get("latest_snapshot") or {}
        outcomes = path["trade_outcomes"]
        print(
            leader["rank"],
            did,
            leader["score"],
            latest.get("position"),
            latest.get("position_evidence"),
            latest.get("synthetic_effective_entry"),
            latest.get("min_realized_carry_required"),
            path.get("max_min_realized_carry_required"),
            path.get("max_flat_realized_score"),
            path.get("transition_count"),
            path.get("trade_count_found_in_scanned_rooms"),
            outcomes["visible_settled"],
            outcomes["visible_void"],
            outcomes["not_visible"],
            sep=",",
        )



def _leader_price_window(start_sweep: int, end_sweep: int) -> list[dict]:
    cent = Decimal("0.01")
    out = []
    for rec in parse_export("d-close1-price"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "price":
            continue
        try:
            n = int(p["n"])
        except Exception:
            continue
        if n < start_sweep or n > end_sweep:
            continue
        applied = _v41_px(p.get("applied"))
        close = _v41_px(p.get("ref"))
        if applied is None or close is None:
            continue
        low = (applied * Decimal("0.95")).quantize(cent, rounding=ROUND_CEILING)
        high = (applied * Decimal("1.05")).quantize(cent, rounding=ROUND_DOWN)
        out.append({
            "sweep": n,
            "applied": applied,
            "close": close,
            "lower_limit": low,
            "upper_limit": high,
        })
    out.sort(key=lambda x: x["sweep"])
    return out


def _leader_buyer_fee(qty: Decimal, px: Decimal, close: Decimal) -> Decimal:
    return max(
        Decimal("0.01") * qty * px,
        qty * (close - px),
    )


def _leader_pivot_snapshot(
    pnl_rows: list[dict],
    pos_by_sweep: dict[int, Decimal],
    sweep: int,
) -> dict | None:
    rows = [x for x in pnl_rows if int(x["sweep"]) <= int(sweep)]
    if not rows:
        return None
    exact = [x for x in rows if int(x["sweep"]) == int(sweep)]
    row = dict(exact[-1] if exact else rows[-1])

    if int(row["sweep"]) in pos_by_sweep:
        row["position"] = pos_by_sweep[int(row["sweep"])]
        row["position_evidence"] = "published_position"
        return row

    # Local slope fallback for the requested diagnostic snapshot only.
    previous = None
    for candidate in pnl_rows:
        if int(candidate["sweep"]) < int(row["sweep"]):
            previous = candidate
        elif int(candidate["sweep"]) >= int(row["sweep"]):
            break
    if previous is not None and int(row["sweep"]) == int(previous["sweep"]) + 1:
        dmark = row["mark"] - previous["mark"]
        if dmark != 0:
            row["position"] = (row["score"] - previous["score"]) / dmark
            row["position_evidence"] = "consecutive_pnl_slope"
            return row

    row["position"] = None
    row["position_evidence"] = "missing"
    return row


def _leader_open_long_candidate(
    price_row: dict,
    target_score: Decimal,
    target_mark: Decimal,
    target_qty: Decimal,
) -> dict:
    px = price_row["lower_limit"]
    close = price_row["close"]
    fee = _leader_buyer_fee(target_qty, px, close)
    score_from_fresh_long = target_qty * (target_mark - px) - fee
    carry_required = target_score - score_from_fresh_long
    cash_required_before_open = target_qty * px + fee
    return {
        "sweep": price_row["sweep"],
        "applied": price_row["applied"],
        "close": close,
        "buy_px": px,
        "qty": target_qty,
        "buyer_fee": fee,
        "cash_required_before_open": cash_required_before_open,
        "score_from_fresh_long_at_target": score_from_fresh_long,
        "locked_carry_required_before_open": max(carry_required, Decimal("0")),
    }


def _leader_direct_flip_candidate(
    price_row: dict,
    pre: dict,
    target: dict,
) -> dict | None:
    pre_pos = pre.get("position")
    target_pos = target.get("position")
    if pre_pos is None or target_pos is None or pre_pos >= 0 or target_pos <= 0:
        return None

    short_qty = abs(Decimal(str(pre_pos)))
    long_qty = Decimal(str(target_pos))
    trade_qty = short_qty + long_qty
    px = price_row["lower_limit"]
    close = price_row["close"]
    fee = _leader_buyer_fee(trade_qty, px, close)

    pre_score_at_close = (
        Decimal(str(pre["score"]))
        + Decimal(str(pre_pos)) * (close - Decimal(str(pre["mark"])))
    )
    trade_value_change_at_close = trade_qty * (close - px) - fee
    modeled_target_score = (
        pre_score_at_close
        + trade_value_change_at_close
        + long_qty * (Decimal(str(target["mark"])) - close)
    )
    gap = Decimal(str(target["score"])) - modeled_target_score

    # Official Fold.check evaluates funds before close proceeds are released.
    # For a one-trade flip, only the excess long_qty opens, but the buyer fee is
    # charged on the full short_qty + long_qty trade.
    cash_required_before_flip = long_qty * px + fee

    return {
        "sweep": price_row["sweep"],
        "mode": "single_trade_flip",
        "pre_position": pre_pos,
        "pre_position_evidence": pre.get("position_evidence"),
        "target_position": target_pos,
        "buy_qty": trade_qty,
        "buy_px": px,
        "buyer_fee": fee,
        "cash_required_before_flip": cash_required_before_flip,
        "modeled_target_score": modeled_target_score,
        "observed_target_score": target["score"],
        "observed_minus_modeled": gap,
        "absolute_gap": abs(gap),
    }


def _leader_two_step_pivot_candidate(
    close_row: dict,
    open_row: dict,
    pre: dict,
    target: dict,
) -> dict | None:
    pre_pos = pre.get("position")
    target_pos = target.get("position")
    if pre_pos is None or target_pos is None or pre_pos >= 0 or target_pos <= 0:
        return None
    if int(open_row["sweep"]) <= int(close_row["sweep"]):
        return None

    short_qty = abs(Decimal(str(pre_pos)))
    long_qty = Decimal(str(target_pos))

    close_px = close_row["lower_limit"]
    close_fee = _leader_buyer_fee(short_qty, close_px, close_row["close"])
    score_at_close_sweep = (
        Decimal(str(pre["score"]))
        + Decimal(str(pre_pos))
        * (close_row["close"] - Decimal(str(pre["mark"])))
    )
    flat_score = (
        score_at_close_sweep
        + short_qty * (close_row["close"] - close_px)
        - close_fee
    )

    open_px = open_row["lower_limit"]
    open_fee = _leader_buyer_fee(long_qty, open_px, open_row["close"])
    modeled_target_score = (
        flat_score
        + long_qty * (Decimal(str(target["mark"])) - open_px)
        - open_fee
    )
    gap = Decimal(str(target["score"])) - modeled_target_score

    return {
        "mode": "close_then_open",
        "close_sweep": close_row["sweep"],
        "open_sweep": open_row["sweep"],
        "pre_position": pre_pos,
        "pre_position_evidence": pre.get("position_evidence"),
        "target_position": target_pos,
        "close_short_qty": short_qty,
        "close_buy_px": close_px,
        "close_fee": close_fee,
        "flat_score_after_close": flat_score,
        "open_long_qty": long_qty,
        "open_buy_px": open_px,
        "open_fee": open_fee,
        "cash_required_before_open": long_qty * open_px + open_fee,
        "modeled_target_score": modeled_target_score,
        "observed_target_score": target["score"],
        "observed_minus_modeled": gap,
        "absolute_gap": abs(gap),
    }


def _leader_pivot_solve_report(
    state: dict,
    rank: int,
    from_sweep: int,
    target_sweep: int,
) -> dict:
    pnl = latest_payload("d-close1-pnl", "pnl")
    pairs = _pnl_pairs(pnl)
    our_dids = {
        str(v.get("did"))
        for v in state.get("keys", {}).values()
        if v.get("did")
    }
    leaders = [
        {"rank": r, "did": did, "score": score}
        for r, (did, score) in enumerate(pairs, 1)
        if did not in our_dids
    ]
    if rank < 1 or rank > len(leaders):
        raise ValueError(f"rank {rank} outside visible non-local leaders")

    leader = leaders[rank - 1]
    did = leader["did"]
    pnl_hist = _leader_pnl_history({did})[did]
    pos_hist = _leader_position_history({did})[did]

    pre = _leader_pivot_snapshot(pnl_hist, pos_hist, from_sweep)
    target = _leader_pivot_snapshot(pnl_hist, pos_hist, target_sweep)
    if pre is None or target is None:
        raise ValueError("missing pre or target PnL snapshot")
    if int(target["sweep"]) != int(target_sweep):
        raise ValueError("target sweep lacks a PnL snapshot")
    if target.get("position_evidence") != "published_position":
        raise ValueError("target sweep lacks a published position")

    price_rows = _leader_price_window(int(pre["sweep"]) + 1, target_sweep)
    if not price_rows:
        raise ValueError("no price sweeps in pivot window")

    open_long = [
        _leader_open_long_candidate(
            row,
            Decimal(str(target["score"])),
            Decimal(str(target["mark"])),
            Decimal(str(target["position"])),
        )
        for row in price_rows
    ]
    open_long.sort(key=lambda x: (
        x["locked_carry_required_before_open"],
        x["cash_required_before_open"],
    ))

    direct = []
    for row in price_rows:
        candidate = _leader_direct_flip_candidate(row, pre, target)
        if candidate is not None:
            direct.append(candidate)
    direct.sort(key=lambda x: x["absolute_gap"])

    two_step = []
    for close_row in price_rows:
        for open_row in price_rows:
            candidate = _leader_two_step_pivot_candidate(
                close_row, open_row, pre, target
            )
            if candidate is not None:
                two_step.append(candidate)
    two_step.sort(key=lambda x: x["absolute_gap"])

    reachability = _leader_price_reachability()
    target_reach = _leader_reach_at_sweep(reachability, target_sweep)
    target_fee_adjusted_carry = None
    if target_reach is not None:
        _synthetic, target_fee_adjusted_carry = _leader_min_carry_required(
            Decimal(str(target["score"])),
            Decimal(str(target["mark"])),
            Decimal(str(target["position"])),
            target_reach["min_legal_buy_seen"],
            target_reach["max_legal_sell_seen"],
            target_reach["best_effective_long_cost_seen"],
            target_reach["best_effective_short_sale_seen"],
        )

    return {
        "mode": "read_only_leader_pivot_solver",
        "leader": leader,
        "pre_snapshot": pre,
        "target_snapshot": target,
        "price_window": price_rows,
        "target_fee_adjusted_min_realized_carry": target_fee_adjusted_carry,
        "best_open_long_only": open_long[0] if open_long else None,
        "best_direct_flip": direct[0] if direct else None,
        "best_close_then_open": two_step[0] if two_step else None,
        "open_long_candidates": open_long,
        "direct_flip_candidates": direct,
        "close_then_open_candidates": two_step,
        "method_note": (
            "The pre-snapshot position may be consecutive_pnl_slope evidence and "
            "is therefore weak. Target position must be published_position. "
            "Buyer fees use the official 1%/clawback max rule. Candidate prices "
            "use the lowest legal two-decimal quote because that minimizes the "
            "buyer's fee-adjusted effective cost. Funds requirements are shown "
            "where they can be derived, but hidden lot/cash history prevents a "
            "full authoritative feasibility proof."
        ),
    }


def cmd_leader_pivot_solve(args) -> None:
    report = _leader_pivot_solve_report(
        load_state(),
        int(args.rank),
        int(args.from_sweep),
        int(args.target_sweep),
    )
    print(json.dumps(report, indent=2, default=str))


def cmd_leader_pivot_summary(args) -> None:
    report = _leader_pivot_solve_report(
        load_state(),
        int(args.rank),
        int(args.from_sweep),
        int(args.target_sweep),
    )
    print("leader_rank:", report["leader"]["rank"])
    print("leader_did:", report["leader"]["did"])
    print("pre_snapshot:", json.dumps(report["pre_snapshot"], default=str))
    print("target_snapshot:", json.dumps(report["target_snapshot"], default=str))
    print(
        "target_fee_adjusted_min_realized_carry:",
        report["target_fee_adjusted_min_realized_carry"],
    )
    print("best_open_long_only:", json.dumps(report["best_open_long_only"], default=str))
    print("best_direct_flip:", json.dumps(report["best_direct_flip"], default=str))
    print(
        "best_close_then_open:",
        json.dumps(report["best_close_then_open"], default=str),
    )


def cmd_progress(_args) -> None:
    state = load_state()
    pr = fresh_price(max_age=10**9)
    pnl = latest_payload("d-close1-pnl", "pnl")
    positions = latest_payload("d-close1-positions", "positions")
    rows = board_rows(pnl)
    mine = local_board_matches(state, rows)

    now = datetime.now(timezone.utc)
    static_done = sorted(state.get("static", {}).keys())
    bracket = state.get("bracket") or {}

    print("=== CLOSE CALL PROGRESS ===")
    print("utc_now:", now.isoformat())
    print("sweep:", pr["n"], "ref:", pr["px"], "age_s:", pr["age_s"])
    print("mark:", pnl.get("mark") if isinstance(pnl, dict) else None)
    print("static:", f"{len(static_done)}/16", ",".join(static_done) if static_done else "-")
    print(
        "bracket:",
        "round", bracket.get("round"),
        "status", bracket.get("status"),
        "pairs", len(bracket.get("pairs") or []),
    )

    if now < LOCK_TIME_UTC:
        print("phase: TRADING")
        print("lock_in_seconds:", int((LOCK_TIME_UTC - now).total_seconds()))
    elif now < FINAL_TIME_UTC:
        print("phase: LOCKED_WAITING_FINAL")
        print("final_in_seconds:", int((FINAL_TIME_UTC - now).total_seconds()))
    else:
        print("phase: FINAL_WINDOW")

    print("official_board_entries:", len(rows))
    if rows:
        print("official_board_top:")
        for row in rows[:10]:
            print(json.dumps(row, ensure_ascii=False, sort_keys=True))

    if mine:
        print("our_visible_board_entries:")
        for item in mine:
            print(item["label"], json.dumps(item["row"], ensure_ascii=False, sort_keys=True))
    else:
        print("our_visible_board_entries: NONE")
        if rows:
            print(
                "rank_note: none of our DIDs appears in the published live-board subset; "
                "exact overall rank is not derivable from the compact public board"
            )

    if isinstance(positions, dict):
        print(
            "market_positions:",
            "open", positions.get("open"),
            "longs", positions.get("longs"),
            "shorts", positions.get("shorts"),
        )

    entries = []
    for k, rec in sorted(state.get("static", {}).items()):
        try:
            entries.append({
                "name": f"T{k}",
                "px": Decimal(str(rec["px"])),
                "qty": Decimal(str(rec["qty"])),
            })
        except Exception:
            pass
    if int(bracket.get("round", 0) or 0) == 1:
        pairs = bracket.get("pairs") or []
        if pairs:
            try:
                entries.append({
                    "name": "BR-R1",
                    "px": Decimal(str(pairs[0]["px"])),
                    "qty": Decimal(str(pairs[0]["qty"])),
                })
            except Exception:
                pass

    mark = None
    if isinstance(pnl, dict) and pnl.get("mark") is not None:
        try:
            mark = Decimal(str(pnl["mark"]))
        except Exception:
            mark = None

    if mark is not None and entries:
        print("strategy_gross_edge_before_fees:")
        for item in entries:
            edge = abs(mark - item["px"]) * item["qty"]
            print(
                item["name"],
                "entry", item["px"],
                "qty", item["qty"],
                "gross_pair_winner_edge", edge.quantize(Decimal("0.01")),
            )
        print(
            "edge_note: structural mark-to-entry movement only; this is not an official score "
            "and excludes actual settlement/clawback fees and omitted-outcome uncertainty"
        )

def submit_trade_at_ref(
    state: dict,
    maker_label: str,
    taker_label: str,
    side: str,
    qty: Decimal,
    px: Decimal,
    sweep: int,
    prefix: str,
) -> dict:
    tid = f"{prefix}-{int(time.time())}"
    text = build_trade(
        state,
        state["room"],
        maker_label,
        taker_label,
        side,
        qty,
        px,
        sweep + 2,
        tid,
    )
    response = post_signed(state, state["room"], maker_label, text)
    submission = None
    for rec in reversed(parse_export(state["room"])):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "trade":
            continue
        if ((p.get("terms") or {}).get("id")) == tid:
            submission = {
                "seq": rec.get("seq"),
                "ts": rec.get("ts"),
                "from": rec.get("from"),
            }
            break
    return {
        "trade_id": tid,
        "long": maker_label if side == "buy" else taker_label,
        "short": taker_label if side == "buy" else maker_label,
        "maker": maker_label,
        "taker": taker_label,
        "side": side,
        "qty": str(qty),
        "px": str(px),
        "sweep": sweep,
        "submission": submission,
        "post_ack": response.strip().splitlines()[0] if response.strip() else "",
    }


def _bracket_round_record(bracket: dict, round_no: int) -> dict:
    rounds = bracket.setdefault("rounds", {})
    key = str(round_no)
    if key not in rounds:
        pairs = json.loads(json.dumps(bracket.get("pairs") or []))
        open_px = pairs[0].get("px") if pairs else None
        rounds[key] = {
            "round": round_no,
            "open_px": open_px,
            "pairs": pairs,
            "status": bracket.get("status") or "submitted",
            "opened_at": bracket.get("opened_at"),
            "submitted_at": bracket.get("submitted_at"),
        }
    return rounds[key]


def _saved_trade_health(trades: list[dict]) -> dict:
    visible_settled = 0
    visible_void = []
    not_visible = 0
    omitted = {"settled": 0, "void": 0}
    for trade in trades:
        tid = trade.get("trade_id")
        if not tid:
            continue
        info = trade_outcome_from_flow(tid)
        omitted = info["omitted"]
        outcome = info["outcome"]
        if not outcome:
            not_visible += 1
        elif outcome["status"] == "settled":
            visible_settled += 1
        else:
            visible_void.append({
                "trade_id": tid,
                "detail": outcome.get("detail"),
                "sweep": outcome.get("sweep"),
            })
    return {
        "visible_settled": visible_settled,
        "visible_void": visible_void,
        "not_visible": not_visible,
        "omitted": omitted,
    }


def bracket_autopilot_step(state: dict, now: datetime) -> dict | None:
    bracket = state.get("bracket") or {}
    round_no = int(bracket.get("round", 0) or 0)
    if round_no <= 0 or round_no >= 4:
        return None

    next_round = round_no + 1
    due_text = BRACKET_SCHEDULE_UTC.get(next_round)
    if not due_text or now < datetime.fromisoformat(due_text):
        return None

    current = _bracket_round_record(bracket, round_no)
    pairs = current.get("pairs") or bracket.get("pairs") or []
    if not pairs:
        return {
            "event": "bracket_blocked",
            "reason": "no_current_pairs",
            "round": round_no,
        }

    open_health = _saved_trade_health(pairs)
    if open_health["visible_void"]:
        bracket["status"] = "blocked_visible_void"
        bracket["blocking_voids"] = open_health["visible_void"]
        save_state(state)
        return {
            "event": "bracket_blocked",
            "reason": "visible_open_void",
            "round": round_no,
            "voids": open_health["visible_void"],
        }

    reg = fleet_registration_evidence(state)
    if reg["room_missed"]:
        bracket["status"] = "blocked_room_missed"
        save_state(state)
        return {
            "event": "bracket_blocked",
            "reason": "dedicated_room_missed",
            "round": round_no,
            "missed": reg["room_missed"],
        }

    rollover = bracket.get("rollover")
    if not isinstance(rollover, dict) or int(rollover.get("from_round", -1)) != round_no:
        gate = fleet_gate(state)
        if not gate["pass"]:
            return {
                "event": "bracket_wait_gate",
                "round": round_no,
                "checks": gate["checks"],
                "sweep": gate["sweep"],
            }

        pr = fresh_price(max_age=120)
        old_px = Decimal(str(current.get("open_px") or pairs[0]["px"]))
        close_px = pr["px"]
        survivors = []
        for pair in pairs:
            survivors.append(pair["long"] if close_px >= old_px else pair["short"])

        rollover = {
            "from_round": round_no,
            "to_round": next_round,
            "status": "closing",
            "started_at": now.isoformat(),
            "close_px": str(close_px),
            "close_sweep": pr["n"],
            "survivors": survivors,
            "closes": [],
            "opens": [],
            "open_outcome_basis": (
                "no visible void; omitted public outcomes accepted only with "
                "retained signed submissions and no dedicated-room missed ranges"
            ),
        }
        bracket["rollover"] = rollover
        bracket["status"] = f"r{round_no}_closing"
        save_state(state)

    if rollover["status"] == "closing":
        close_px = Decimal(str(rollover["close_px"]))
        close_sweep = int(rollover["close_sweep"])
        done = {x.get("maker") for x in rollover.get("closes", [])}

        for idx, pair in enumerate(pairs, 1):
            maker = pair["long"]
            taker = pair["short"]
            if maker in done:
                continue
            qty = Decimal(str(pair["qty"]))
            res = submit_trade_at_ref(
                state,
                maker,
                taker,
                "sell",
                qty,
                close_px,
                close_sweep,
                f"br{round_no}c-{idx:02d}",
            )
            rollover["closes"].append(res)
            bracket["rollover"] = rollover
            save_state(state)

        if len(rollover["closes"]) != len(pairs):
            return {
                "event": "bracket_closing_partial",
                "round": round_no,
                "done": len(rollover["closes"]),
                "total": len(pairs),
                "sweep": close_sweep,
            }

        rollover["status"] = "waiting_close_sweep"
        bracket["status"] = f"r{round_no}_waiting_close"
        save_state(state)
        return {
            "event": "bracket_close_submitted",
            "round": round_no,
            "next_round": next_round,
            "pairs": len(pairs),
            "close_px": rollover["close_px"],
            "close_sweep": close_sweep,
        }

    if rollover["status"] == "waiting_close_sweep":
        pr = fresh_price(max_age=10**9)
        if pr["n"] <= int(rollover["close_sweep"]):
            return {
                "event": "bracket_wait_close_settlement_sweep",
                "round": round_no,
                "current_sweep": pr["n"],
                "close_sweep": rollover["close_sweep"],
            }

        health = _saved_trade_health(rollover.get("closes") or [])
        if health["visible_void"]:
            rollover["status"] = "blocked_visible_close_void"
            rollover["blocking_voids"] = health["visible_void"]
            bracket["status"] = "blocked_visible_close_void"
            save_state(state)
            return {
                "event": "bracket_blocked",
                "reason": "visible_close_void",
                "round": round_no,
                "voids": health["visible_void"],
            }

        gate = fleet_gate(state)
        if not gate["pass"]:
            return {
                "event": "bracket_wait_gate_after_close",
                "round": round_no,
                "checks": gate["checks"],
                "sweep": gate["sweep"],
            }

        pr = fresh_price(max_age=120)
        rollover["status"] = "opening_next"
        rollover["next_open_px"] = str(pr["px"])
        rollover["next_open_sweep"] = pr["n"]
        bracket["status"] = f"r{next_round}_opening"
        save_state(state)

    if rollover["status"] == "opening_next":
        survivors = list(rollover["survivors"])
        targets = list(zip(survivors[0::2], survivors[1::2]))
        open_px = Decimal(str(rollover["next_open_px"]))
        open_sweep = int(rollover["next_open_sweep"])
        existing = {x.get("maker") for x in rollover.get("opens", [])}

        for idx, (maker, taker) in enumerate(targets, 1):
            if maker in existing:
                continue
            qty = q_for_cash(Decimal("10000"), open_px)
            if qty < Decimal("0.1"):
                continue
            res = submit_trade_at_ref(
                state,
                maker,
                taker,
                "buy",
                qty,
                open_px,
                open_sweep,
                f"br{next_round}-{idx:02d}",
            )
            rollover["opens"].append(res)
            bracket["rollover"] = rollover
            save_state(state)

        if len(rollover["opens"]) != len(targets):
            return {
                "event": "bracket_opening_partial",
                "round": next_round,
                "done": len(rollover["opens"]),
                "total": len(targets),
                "sweep": open_sweep,
            }

        new_pairs = []
        for res in rollover["opens"]:
            new_pairs.append({
                "trade_id": res["trade_id"],
                "long": res["maker"],
                "short": res["taker"],
                "qty": res["qty"],
                "px": res["px"],
                "sweep": res["sweep"],
                "submission": res.get("submission"),
                "post_ack": res.get("post_ack"),
            })

        current["status"] = "closed_assumed_or_visible"
        current["close_px"] = rollover["close_px"]
        current["close_sweep"] = rollover["close_sweep"]
        current["closes"] = rollover["closes"]
        current["survivors"] = survivors
        current["close_health"] = _saved_trade_health(rollover["closes"])

        rounds = bracket.setdefault("rounds", {})
        rounds[str(next_round)] = {
            "round": next_round,
            "open_px": str(open_px),
            "pairs": json.loads(json.dumps(new_pairs)),
            "status": "submitted",
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "source_survivors": survivors,
        }

        bracket["round"] = next_round
        bracket["pairs"] = new_pairs
        bracket["status"] = "submitted"
        bracket["opened_at"] = datetime.now(timezone.utc).isoformat()
        bracket["submitted_at"] = datetime.now(timezone.utc).isoformat()
        bracket.pop("rollover", None)
        save_state(state)

        return {
            "event": "bracket_round_opened",
            "round": next_round,
            "pairs": len(new_pairs),
            "open_px": str(open_px),
            "open_sweep": open_sweep,
            "survivors": survivors,
        }

    return None


def cmd_enable_dense(args) -> None:
    state = load_state()
    dense = state.setdefault("dense", {})
    dense["enabled"] = True
    dense["enabled_at"] = datetime.now(timezone.utc).isoformat()
    dense["mode"] = "favored-ticket-both-sides-every-sweep"
    dense["offset"] = str(DENSE_OFFSET)
    dense["qty_safety"] = str(DENSE_QTY_SAFETY)
    dense["legacy_static_frozen_after"] = sorted(state.get("static", {}).keys())
    dense["legacy_bracket_frozen_round"] = (state.get("bracket") or {}).get("round")
    state["legacy_strategy_frozen"] = True
    dense.setdefault("next_index", 1)
    dense.setdefault("tickets", [])
    save_state(state)
    print("dense mode ENABLED")
    print("existing positions are left untouched")
    print("legacy future static/bracket actions are frozen while dense mode is enabled")
    print("new mode: one favored long + one favored short target per fresh sweep")
    print("offset:", DENSE_OFFSET, "dynamic key safety cap:", DENSE_MAX_DYNAMIC_KEYS)


def cmd_enable_dense_v2(_args) -> None:
    state = load_state()
    dense = state.setdefault("dense", {})
    dense["enabled"] = True
    dense["v2_enabled"] = True
    dense["v2_enabled_at"] = datetime.now(timezone.utc).isoformat()
    dense["mode"] = "dense-v2-baseline-plus-extreme-boost"
    dense["v2_offset"] = str(DENSE_V2_OFFSET)
    dense["v2_boost_total_copies"] = DENSE_V2_BOOST_TOTAL_COPIES
    dense["v2_boost_extra_copies"] = DENSE_V2_BOOST_EXTRA_COPIES
    dense["v2_reserve_target_pairs"] = DENSE_V2_RESERVE_TARGET_PAIRS
    dense.setdefault("boost_next_index", 1)
    dense.setdefault("boost_reserve", [])
    dense.setdefault("boost_tickets", [])
    dense_v2_init_bounds(dense)
    state["legacy_strategy_frozen"] = True
    save_state(state)
    print("Dense V2 ENABLED")
    print("baseline: one favored long + one favored short per fresh sweep")
    print("offset:", DENSE_V2_OFFSET)
    print("extreme boost: total", DENSE_V2_BOOST_TOTAL_COPIES, "copies on the new-extreme side")
    print("reserve target pairs:", DENSE_V2_RESERVE_TARGET_PAIRS)
    print("historical_low_ref:", dense.get("historical_low_ref"))
    print("historical_high_ref:", dense.get("historical_high_ref"))
    print("existing Dense tickets and pending batch are preserved")


def cmd_enable_dense_v3(_args) -> None:
    state = load_state()
    dense = state.setdefault("dense", {})
    dense["enabled"] = True
    dense["v3_enabled"] = True
    dense["v3_enabled_at"] = datetime.now(timezone.utc).isoformat()
    dense["v2_enabled"] = False
    dense["mode"] = "dense-v3-every-sweep-bidirectional-multiplicity"
    dense["v3_offset"] = str(DENSE_V3_OFFSET)
    dense["v3_total_copies_per_side"] = DENSE_V3_TOTAL_COPIES_PER_SIDE
    dense["v3_extra_copy_sets"] = DENSE_V3_EXTRA_COPY_SETS
    dense["v3_reserve_target_sets"] = DENSE_V3_RESERVE_TARGET_SETS
    dense["v3_ref_age_gate_enabled"] = False
    dense.setdefault("v3_reserve_next_index", 1)
    dense.setdefault("v3_reserve", [])
    dense.setdefault("v3_tickets", [])
    dense_v2_init_bounds(dense)
    state["legacy_strategy_frozen"] = True

    pr = fresh_price(max_age=10**9)
    dense["v3_enabled_sweep"] = pr["n"]
    dense["v3_not_before_sweep"] = pr["n"] + 1
    save_state(state)

    reserve_event = dense_v3_maintain_reserve(state, pr["n"])
    if reserve_event:
        dense["last_reserve_event"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            **reserve_event,
        }
        save_state(state)

    print("Dense V3 ENABLED")
    print("coverage: every aligned referee sweep")
    print("copies per side:", DENSE_V3_TOTAL_COPIES_PER_SIDE)
    print("offset:", DENSE_V3_OFFSET)
    print("ref age gate: DISABLED (official referee sweep/ref remains authoritative)")
    print("flow/state alignment + room/missed/lock gates: ENABLED")
    print("reserve target sets:", DENSE_V3_RESERVE_TARGET_SETS)
    print("reserve primed on sweep:", dense.get("v3_enabled_sweep"))
    print("first V3 trade sweep >=", dense.get("v3_not_before_sweep"))
    print("dynamic key safety cap:", DENSE_MAX_DYNAMIC_KEYS)
    print("existing Dense tickets and pending batch are preserved")



def _v41_px(value) -> Decimal | None:
    try:
        if isinstance(value, dict):
            value = value.get("px")
        if value is None:
            return None
        px = Decimal(str(value))
        return px if px > 0 else None
    except Exception:
        return None


def _v41_move_samples(lookback: int = DENSE_V41_LOOKBACK) -> list[dict]:
    """Historical within-sweep close moves: price.ref / price.applied - 1."""
    out = []
    for rec in parse_export("d-close1-price"):
        p = rec.get("_payload")
        if not isinstance(p, dict) or p.get("t") != "price":
            continue
        applied = _v41_px(p.get("applied"))
        close = _v41_px(p.get("ref"))
        if applied is None or close is None:
            continue
        try:
            n = int(p["n"])
        except Exception:
            continue
        out.append({
            "n": n,
            "applied": applied,
            "close": close,
            "move": close / applied - Decimal("1"),
        })
    out.sort(key=lambda x: x["n"])
    if lookback and lookback > 0:
        out = out[-lookback:]
    return out


def _v41_quantile(values: list[Decimal], q: Decimal, upper: bool = False) -> Decimal:
    if not values:
        raise ValueError("empty V4.1 sample")
    xs = sorted(values)
    q = max(Decimal("0"), min(Decimal("1"), q))
    pos = q * Decimal(len(xs) - 1)
    idx = int(pos.to_integral_value(rounding=ROUND_CEILING if upper else ROUND_DOWN))
    idx = max(0, min(len(xs) - 1, idx))
    return xs[idx]


def _v41_stress_band(samples: list[dict], copy_no: int) -> dict:
    if not 1 <= int(copy_no) <= len(DENSE_V41_QUANTILE_BANDS):
        raise ValueError("V4.1 copy_no must be 1..8")
    if len(samples) < 24:
        raise ValueError("V4.1 needs at least 24 historical price samples")
    low_q, high_q = DENSE_V41_QUANTILE_BANDS[int(copy_no) - 1]
    moves = [Decimal(str(x["move"])) for x in samples]
    return {
        "low_q": low_q,
        "high_q": high_q,
        "coverage": high_q - low_q,
        "low_move": _v41_quantile(moves, low_q, upper=False),
        "high_move": _v41_quantile(moves, high_q, upper=True),
    }


def _v41_side_fees(
    maker_side: str,
    qty: Decimal,
    px: Decimal,
    close: Decimal,
) -> tuple[Decimal, Decimal]:
    """Official clawback fee pair: (maker_fee, taker_fee)."""
    base = Decimal("0.01") * qty * px
    gap = (close - px) * qty
    buyer = max(base, gap)
    seller = max(base, -gap)
    if maker_side == "buy":
        return buyer, seller
    if maker_side == "sell":
        return seller, buyer
    raise ValueError("maker_side must be buy/sell")


def _v41_simulate_pair(
    low: Decimal,
    high: Decimal,
    long_qty: Decimal,
    short_qty: Decimal,
    close: Decimal,
) -> dict:
    """Replay the two fresh V4 legs with the official fold cash semantics."""
    mint = Decimal("10000")
    feeder_cash = mint
    long_cash = mint
    short_cash = mint

    # Leg 1: feeder maker sells to the long target.
    feeder_fee, long_fee = _v41_side_fees("sell", long_qty, low, close)
    feeder_need = long_qty * low + feeder_fee
    long_need = long_qty * low + long_fee
    long_settled = feeder_cash >= feeder_need and long_cash >= long_need
    if not long_settled:
        return {
            "long_settled": False,
            "short_settled": False,
            "long_fee": long_fee,
            "short_fee": None,
            "reason": "long_leg_funds",
        }

    feeder_cash -= feeder_need
    long_cash -= long_need
    feeder_short = long_qty

    # Leg 2: short target maker sells to the feeder.
    #
    # Match official Fold.check semantics exactly: funds are checked BEFORE
    # Account.apply releases collateral/proceeds from closing the feeder's
    # existing short. Therefore a feeder buy that only closes its short needs
    # fee cash here, while any excess quantity opening a new long additionally
    # needs opening_long * high collateral. Do not credit close proceeds before
    # this check.
    short_fee, feeder_buy_fee = _v41_side_fees("sell", short_qty, high, close)
    short_need = short_qty * high + short_fee
    feeder_opening_long = max(Decimal("0"), short_qty - feeder_short)
    feeder_need_2 = feeder_opening_long * high + feeder_buy_fee
    short_settled = short_cash >= short_need and feeder_cash >= feeder_need_2

    return {
        "long_settled": True,
        "short_settled": bool(short_settled),
        "long_fee": long_fee,
        "short_fee": short_fee,
        "reason": None if short_settled else "short_leg_funds",
    }


def _v41_max_qty(predicate, upper_hint: Decimal) -> Decimal:
    """Largest 0.01-contract quantity accepted by a monotone cash predicate."""
    cent = Decimal("0.01")
    hi = max(10, int((upper_hint / cent).to_integral_value(rounding=ROUND_DOWN)))
    lo = 10
    best = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        qty = Decimal(mid) * cent
        if predicate(qty):
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return Decimal(best) * cent


def dense_v41_plan_copy(
    pr: dict,
    copy_no: int,
    samples: list[dict] | None = None,
) -> dict:
    """Read-only proposed V4.1 plan with independent long/short quantities."""
    samples = samples if samples is not None else _v41_move_samples()
    band = _v41_stress_band(samples, copy_no)
    ref = Decimal(str(pr["px"]))
    lower_limit, upper_limit = dense_v4_limit_bounds(pr)
    cent = Decimal("0.01")

    stress_low = (ref * (Decimal("1") + band["low_move"])).quantize(
        cent, rounding=ROUND_DOWN
    )
    stress_high = (ref * (Decimal("1") + band["high_move"])).quantize(
        cent, rounding=ROUND_CEILING
    )
    stress_closes = tuple(sorted(set([stress_low, ref.quantize(cent), stress_high])))

    low = lower_limit

    # Choose the short quote around the 1% clawback boundary for the upper edge
    # of this copy's empirical band: close ~= 0.99 * quote.
    target_close = max(ref, stress_high)
    desired_high = (target_close / Decimal("0.99")).quantize(
        cent, rounding=ROUND_CEILING
    )
    min_high = (ref / Decimal("0.99")).quantize(cent, rounding=ROUND_CEILING)
    high = min(upper_limit, max(min_high, desired_high))

    mint = Decimal("10000")
    long_upper = (mint / min(stress_closes)).quantize(cent, rounding=ROUND_DOWN)

    def long_ok(qty: Decimal) -> bool:
        for close in stress_closes:
            feeder_fee, long_fee = _v41_side_fees("sell", qty, low, close)
            if mint < qty * low + feeder_fee:
                return False
            if mint < qty * low + long_fee:
                return False
        return True

    long_qty = _v41_max_qty(long_ok, long_upper)

    def short_ok(qty: Decimal) -> bool:
        if qty > long_qty:
            return False
        return all(
            _v41_simulate_pair(low, high, long_qty, qty, close)["short_settled"]
            for close in stress_closes
        )

    short_qty = _v41_max_qty(short_ok, long_qty)

    return {
        **band,
        "copy_no": int(copy_no),
        "sample_count": len(samples),
        "ref": ref,
        "low": low,
        "high": high,
        "long_qty": long_qty,
        "short_qty": short_qty,
        "short_offset": high / ref - Decimal("1"),
        "stress_closes": stress_closes,
        "lower_limit": lower_limit,
        "upper_limit": upper_limit,
    }


def _v41_summary(values: list[Decimal]) -> dict:
    if not values:
        return {"count": 0, "mean": None, "p10": None, "p50": None, "min": None}
    xs = sorted(values)
    return {
        "count": len(xs),
        "mean": sum(xs, Decimal("0")) / Decimal(len(xs)),
        "p10": _v41_quantile(xs, Decimal("0.10")),
        "p50": _v41_quantile(xs, Decimal("0.50")),
        "min": xs[0],
    }


def dense_v41_backtest(pr: dict, samples: list[dict] | None = None) -> dict:
    """Compare current V4 with the proposed eight-copy V4.1 grid."""
    samples = samples if samples is not None else _v41_move_samples()
    if len(samples) < 24:
        raise ValueError("V4.1 needs at least 24 historical price samples")

    current = [
        dense_v4_plan_copy(pr, i)
        for i in range(1, DENSE_V4_TOTAL_COPIES_PER_SIDE + 1)
    ]
    proposed = [
        dense_v41_plan_copy(pr, i, samples)
        for i in range(1, len(DENSE_V41_QUANTILE_BANDS) + 1)
    ]

    ref = Decimal(str(pr["px"]))
    scenario_up = ref * Decimal("1.05")
    scenario_down = ref * Decimal("0.95")
    scenario_up_10 = ref * Decimal("1.10")
    scenario_down_10 = ref * Decimal("0.90")
    report = {}

    for name, plans in (("current_v4", current), ("proposed_v41", proposed)):
        long_qs, short_qs = [], []
        long_scores, short_scores = [], []
        long_scores_10, short_scores_10 = [], []
        no_long = 0
        no_short = 0

        for sample in samples:
            close = (ref * (Decimal("1") + Decimal(str(sample["move"])))).quantize(
                Decimal("0.01")
            )
            surviving_long = []
            surviving_short = []
            scores_long = []
            scores_short = []

            for plan in plans:
                if name == "current_v4":
                    ql = qs = Decimal(str(plan["qty"]))
                else:
                    ql = Decimal(str(plan["long_qty"]))
                    qs = Decimal(str(plan["short_qty"]))

                sim = _v41_simulate_pair(
                    Decimal(str(plan["low"])),
                    Decimal(str(plan["high"])),
                    ql,
                    qs,
                    close,
                )
                if sim["long_settled"]:
                    surviving_long.append(ql)
                    scores_long.append(
                        ql * (scenario_up - Decimal(str(plan["low"])))
                        - Decimal(str(sim["long_fee"]))
                    )
                    # Keep the same settlement fee; final S only changes final
                    # mark-to-position value.
                    long_scores_10.append(
                        ql * (scenario_up_10 - Decimal(str(plan["low"])))
                        - Decimal(str(sim["long_fee"]))
                    )
                if sim["short_settled"]:
                    surviving_short.append(qs)
                    scores_short.append(
                        qs * (Decimal(str(plan["high"])) - scenario_down)
                        - Decimal(str(sim["short_fee"]))
                    )
                    short_scores_10.append(
                        qs * (Decimal(str(plan["high"])) - scenario_down_10)
                        - Decimal(str(sim["short_fee"]))
                    )

            if surviving_long:
                long_qs.append(max(surviving_long))
                long_scores.append(max(scores_long))
                # The tail list currently contains one value per surviving
                # copy in this sample. Collapse the current sample's suffix.
                k = len(scores_long)
                if k:
                    sample_vals = long_scores_10[-k:]
                    del long_scores_10[-k:]
                    long_scores_10.append(max(sample_vals))
            else:
                no_long += 1

            if surviving_short:
                short_qs.append(max(surviving_short))
                short_scores.append(max(scores_short))
                k = len(scores_short)
                if k:
                    sample_vals = short_scores_10[-k:]
                    del short_scores_10[-k:]
                    short_scores_10.append(max(sample_vals))
            else:
                no_short += 1

        report[name] = {
            "samples": len(samples),
            "no_long_survivor": no_long,
            "no_short_survivor": no_short,
            "best_long_qty": _v41_summary(long_qs),
            "best_short_qty": _v41_summary(short_qs),
            "best_long_score_if_final_ref_plus_5pct": _v41_summary(long_scores),
            "best_short_score_if_final_ref_minus_5pct": _v41_summary(short_scores),
            "best_long_score_if_final_ref_plus_10pct": _v41_summary(long_scores_10),
            "best_short_score_if_final_ref_minus_10pct": _v41_summary(short_scores_10),
        }

    return report


def _v41_local_open_candidates(state: dict) -> list[dict]:
    """Conservative reconstruction of currently unmodified V4 target pairs."""
    pairs = _v5a_v4_pairs(state)
    dense = state.get("dense") or {}
    modified = set((dense.get("v5a_harvested") or {}).keys())
    active = dense.get("v5a_active")
    if isinstance(active, dict) and active.get("pair_id"):
        modified.add(str(active["pair_id"]))

    refs = _price_refs_by_sweep()
    missed = _v5a_missed_sweeps(state["room"])
    trade_ids = {
        tid
        for pair in pairs
        for tid in (pair.get("long_trade_id"), pair.get("short_trade_id"))
        if tid
    }
    visible = _v5a_visible_outcomes(trade_ids)
    submissions = trade_submissions_in_room(state["room"], trade_ids)
    out = []

    for pair in pairs:
        if pair["pair_id"] in modified:
            continue
        settle_sweep = int(pair["cohort_sweep"]) + 1
        close = refs.get(settle_sweep)
        if close is None or settle_sweep in missed:
            continue

        ltid = pair.get("long_trade_id")
        stid = pair.get("short_trade_id")
        if not ltid or not stid:
            continue

        omitted = _flow_omitted_at_sweep(settle_sweep)
        compact_incomplete = bool(omitted.get("settled") or omitted.get("void"))
        long_visible = visible.get(ltid) == "settled"
        short_visible = visible.get(stid) == "settled"
        long_local = (
            visible.get(ltid) != "void"
            and compact_incomplete
            and ltid in submissions
        )
        short_local = (
            visible.get(stid) != "void"
            and compact_incomplete
            and stid in submissions
        )
        long_evidence = long_visible or long_local
        short_evidence = short_visible or short_local
        long_evidence_mode = (
            "visible_settled" if long_visible
            else "local_reconstruction" if long_local
            else "none"
        )
        short_evidence_mode = (
            "visible_settled" if short_visible
            else "local_reconstruction" if short_local
            else "none"
        )
        if not long_evidence and not short_evidence:
            continue

        qty = Decimal(str(pair["qty"]))
        sim = _v41_simulate_pair(
            Decimal(str(pair["low"])),
            Decimal(str(pair["high"])),
            qty,
            qty,
            close,
        )
        out.append({
            "pair": pair,
            "close": close,
            "long_settled": bool(long_evidence and sim["long_settled"]),
            "short_settled": bool(short_evidence and sim["short_settled"]),
            "long_evidence_mode": long_evidence_mode,
            "short_evidence_mode": short_evidence_mode,
            "long_fee": sim["long_fee"],
            "short_fee": sim["short_fee"],
        })
    return out


def _v41_candidate_score(candidate: dict, side: str, final_s: Decimal) -> Decimal | None:
    pair = candidate["pair"]
    qty = Decimal(str(pair["qty"]))
    if side == "long":
        if not candidate["long_settled"]:
            return None
        return (
            qty * (final_s - Decimal(str(pair["low"])))
            - Decimal(str(candidate["long_fee"]))
        )
    if side == "short":
        if not candidate["short_settled"]:
            return None
        return (
            qty * (Decimal(str(pair["high"])) - final_s)
            - Decimal(str(candidate["short_fee"]))
        )
    raise ValueError("side must be long/short")


def cmd_dense_v41_preview(args) -> None:
    samples = _v41_move_samples(args.lookback)
    pr = fresh_price(max_age=10**9)
    if len(samples) < 24:
        raise SystemExit(f"only {len(samples)} usable V4.1 samples")

    moves = sorted(Decimal(str(x["move"])) for x in samples)
    print("=== DENSE V4.1 READ-ONLY PREVIEW ===")
    print("sweep:", pr["n"], "ref:", pr["px"], "samples:", len(samples))
    print("move_min:", (moves[0] * 100).quantize(Decimal("0.0001")), "%")
    print("move_p01:", (_v41_quantile(moves, Decimal("0.01")) * 100).quantize(Decimal("0.0001")), "%")
    print("move_p50:", (_v41_quantile(moves, Decimal("0.50")) * 100).quantize(Decimal("0.0001")), "%")
    print("move_p99:", (_v41_quantile(moves, Decimal("0.99"), upper=True) * 100).quantize(Decimal("0.0001")), "%")
    print("move_max:", (moves[-1] * 100).quantize(Decimal("0.0001")), "%")
    print("copy,low_q,high_q,low_move,high_move,long_px,short_px,long_qty,short_qty,short_offset")
    for copy_no in range(1, len(DENSE_V41_QUANTILE_BANDS) + 1):
        plan = dense_v41_plan_copy(pr, copy_no, samples)
        print(
            copy_no,
            plan["low_q"],
            plan["high_q"],
            (plan["low_move"] * 100).quantize(Decimal("0.0001")),
            (plan["high_move"] * 100).quantize(Decimal("0.0001")),
            plan["low"],
            plan["high"],
            plan["long_qty"],
            plan["short_qty"],
            (plan["short_offset"] * 100).quantize(Decimal("0.0001")),
            sep=",",
        )


def cmd_dense_v41_backtest(args) -> None:
    samples = _v41_move_samples(args.lookback)
    pr = fresh_price(max_age=10**9)
    print(json.dumps(dense_v41_backtest(pr, samples), indent=2, default=str))


def cmd_dense_final_s_grid(args) -> None:
    state = load_state()
    candidates = _v41_local_open_candidates(state)
    start = Decimal(str(args.start))
    end = Decimal(str(args.end))
    step = Decimal(str(args.step))
    if step <= 0:
        raise SystemExit("step must be > 0")

    print("S,candidate_count,rank,score,label,side,pair_id,cohort_sweep,copy_no,evidence_mode")
    final_s = start
    while final_s <= end:
        scored = []
        for candidate in candidates:
            pair = candidate["pair"]
            for side in ("long", "short"):
                score = _v41_candidate_score(candidate, side, final_s)
                if score is None:
                    continue
                scored.append({
                    "score": score,
                    "label": pair[side],
                    "side": side,
                    "pair_id": pair["pair_id"],
                    "cohort_sweep": pair["cohort_sweep"],
                    "copy_no": pair["copy_no"],
                    "evidence_mode": candidate.get(
                        "long_evidence_mode" if side == "long" else "short_evidence_mode",
                        "unknown",
                    ),
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:3]
        if not top:
            print(final_s, 0, "", "", "", "", "", "", "", sep=",")
        else:
            for rank, item in enumerate(top, 1):
                print(
                    final_s,
                    len(scored),
                    rank,
                    item["score"].quantize(Decimal("0.000001")),
                    item["label"],
                    item["side"],
                    item["pair_id"],
                    item["cohort_sweep"],
                    item["copy_no"],
                    item["evidence_mode"],
                    sep=",",
                )
        final_s += step




def _v42_s_grid(start: Decimal, end: Decimal, step: Decimal) -> list[Decimal]:
    if step <= 0 or end < start:
        raise ValueError("invalid final-S grid")
    out = []
    s = start
    while s <= end:
        out.append(s)
        s += step
    return out


def _v42_position_map(positions: dict | None) -> dict[str, Decimal]:
    out = {}
    if not isinstance(positions, dict):
        return out
    for item in positions.get("top") or []:
        try:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                out[str(item[0])] = Decimal(str(item[1]))
            elif isinstance(item, dict):
                did = item.get("key") or item.get("did")
                pos = item.get("position")
                if pos is None:
                    pos = item.get("pos")
                if did is not None and pos is not None:
                    out[str(did)] = Decimal(str(pos))
        except Exception:
            continue
    return out


def _v42_recent_slope_positions(dids: set[str], rows: int = 16) -> dict[str, Decimal]:
    history = defaultdict(list)
    pnl_rows = []
    for rec in parse_export("d-close1-pnl"):
        p = rec.get("_payload")
        if isinstance(p, dict) and p.get("t") == "pnl":
            pnl_rows.append(p)
    for p in pnl_rows[-max(2, int(rows)):]:
        try:
            n = int(p["n"])
            mark = Decimal(str(p["mark"]))
        except Exception:
            continue
        for did, score in _pnl_pairs(p):
            if did in dids:
                history[did].append((n, mark, score))

    out = {}
    for did, hist in history.items():
        for a, b in reversed(list(zip(hist, hist[1:]))):
            if b[0] != a[0] + 1:
                continue
            dmark = b[1] - a[1]
            if dmark == 0:
                continue
            out[did] = (b[2] - a[2]) / dmark
            break
    return out


def _v42_competitor_model(state: dict, s_grid: list[Decimal]) -> dict:
    """Static current-position podium scenario.

    Known public positions are preferred. Consecutive-score slopes are a weak
    fallback because an account may trade between snapshots. A flat fallback is
    used only so the diagnostic remains defined when public position coverage is
    sparse. This model is a stress scenario, not an election-style prediction.
    """
    pnl = latest_payload("d-close1-pnl", "pnl")
    pairs = _pnl_pairs(pnl)
    if len(pairs) < 3:
        raise ValueError("public pnl top has fewer than 3 entries")
    mark = Decimal(str(pnl["mark"]))
    positions = _v42_position_map(latest_payload("d-close1-positions", "positions"))
    our_dids = {str(v.get("did")) for v in state.get("keys", {}).values() if v.get("did")}
    competitors = [(did, score) for did, score in pairs if did not in our_dids]
    if len(competitors) < 3:
        raise ValueError("fewer than 3 non-local public competitors")

    slope_fallback = _v42_recent_slope_positions({did for did, _ in competitors[:25]})
    lines = []
    for rank, (did, score) in enumerate(competitors[:25], 1):
        if did in positions:
            pos = positions[did]
            evidence = "published_position"
        elif did in slope_fallback:
            pos = slope_fallback[did]
            evidence = "consecutive_pnl_slope"
        else:
            pos = Decimal("0")
            evidence = "flat_score_fallback"
        lines.append({
            "rank_at_mark": rank,
            "did": did,
            "score_at_mark": score,
            "mark": mark,
            "position": pos,
            "evidence": evidence,
        })

    podium = {}
    for final_s in s_grid:
        scores = sorted(
            (
                line["score_at_mark"] + line["position"] * (final_s - mark)
                for line in lines
            ),
            reverse=True,
        )
        podium[final_s] = scores[2]

    return {
        "pnl_sweep": pnl.get("n"),
        "mark": mark,
        "lines": lines,
        "podium": podium,
    }


def _v42_existing_frontier(state: dict, s_grid: list[Decimal]) -> dict[Decimal, Decimal]:
    candidates = _v41_local_open_candidates(state)
    floor = Decimal("-1e30")
    out = {s: floor for s in s_grid}
    for candidate in candidates:
        for final_s in s_grid:
            for side in ("long", "short"):
                score = _v41_candidate_score(candidate, side, final_s)
                if score is not None and score > out[final_s]:
                    out[final_s] = score
    return out


def _v42_quote(ref: Decimal, offset: Decimal, side: str, lo: Decimal, hi: Decimal) -> Decimal:
    cent = Decimal("0.01")
    if side == "long":
        px = (ref * (Decimal("1") - offset)).quantize(cent, rounding=ROUND_DOWN)
        return max(lo, px)
    if side == "short":
        px = (ref * (Decimal("1") + offset)).quantize(cent, rounding=ROUND_CEILING)
        return min(hi, px)
    raise ValueError("side must be long/short")


def dense_v42_plan_pair(
    pr: dict,
    samples: list[dict],
    band_no: int,
    long_offset: Decimal,
    short_offset: Decimal,
    long_fraction: Decimal,
    source: str = "v42_grid",
) -> dict | None:
    band = _v41_stress_band(samples, band_no)
    ref = Decimal(str(pr["px"]))
    lower_limit, upper_limit = dense_v4_limit_bounds(pr)
    low = _v42_quote(ref, long_offset, "long", lower_limit, upper_limit)
    high = _v42_quote(ref, short_offset, "short", lower_limit, upper_limit)
    if low >= ref or high <= ref:
        return None

    cent = Decimal("0.01")
    stress_low = (ref * (Decimal("1") + band["low_move"])).quantize(
        cent, rounding=ROUND_DOWN
    )
    stress_high = (ref * (Decimal("1") + band["high_move"])).quantize(
        cent, rounding=ROUND_CEILING
    )
    stress_closes = tuple(sorted(set([stress_low, ref.quantize(cent), stress_high])))
    mint = Decimal("10000")

    def long_ok(qty: Decimal) -> bool:
        for close in stress_closes:
            feeder_fee, long_fee = _v41_side_fees("sell", qty, low, close)
            if mint < qty * low + feeder_fee:
                return False
            if mint < qty * low + long_fee:
                return False
        return True

    long_upper = (mint / low).quantize(cent, rounding=ROUND_DOWN)
    long_max = _v41_max_qty(long_ok, long_upper)
    long_qty = (long_max * long_fraction).quantize(cent, rounding=ROUND_DOWN)
    if long_qty < Decimal("0.10"):
        return None

    def short_ok(qty: Decimal) -> bool:
        if qty > long_qty:
            return False
        return all(
            _v41_simulate_pair(low, high, long_qty, qty, close)["short_settled"]
            for close in stress_closes
        )

    short_qty = _v41_max_qty(short_ok, long_qty)
    if short_qty < Decimal("0.10"):
        return None

    return {
        "source": source,
        "band_no": int(band_no),
        "low_q": band["low_q"],
        "high_q": band["high_q"],
        "low_move": band["low_move"],
        "high_move": band["high_move"],
        "ref": ref,
        "low": low,
        "high": high,
        "long_offset": ref and (ref - low) / ref,
        "short_offset": ref and (high - ref) / ref,
        "long_fraction": long_fraction,
        "long_qty": long_qty,
        "short_qty": short_qty,
        "stress_closes": stress_closes,
    }


def _v42_current_template(pr: dict, copy_no: int) -> dict:
    plan = dense_v4_plan_copy(pr, copy_no)
    ref = Decimal(str(pr["px"]))
    return {
        "source": "current_v4_template",
        "band_no": 0,
        "low_q": None,
        "high_q": None,
        "low_move": None,
        "high_move": None,
        "ref": ref,
        "low": Decimal(str(plan["low"])),
        "high": Decimal(str(plan["high"])),
        "long_offset": Decimal(str(plan["long_offset"])),
        "short_offset": Decimal(str(plan["short_offset"])),
        "long_fraction": Decimal("1"),
        "long_qty": Decimal(str(plan["qty"])),
        "short_qty": Decimal(str(plan["qty"])),
        "stress_closes": (ref,),
    }


def _v42_candidate_pool(pr: dict, samples: list[dict]) -> list[dict]:
    pool = []
    for band_no in range(1, len(DENSE_V41_QUANTILE_BANDS) + 1):
        for long_offset in DENSE_V42_LONG_OFFSETS:
            for short_offset in DENSE_V42_SHORT_OFFSETS:
                for long_fraction in DENSE_V42_LONG_FRACTIONS:
                    plan = dense_v42_plan_pair(
                        pr, samples, band_no, long_offset, short_offset, long_fraction
                    )
                    if plan is not None:
                        pool.append(plan)
    for copy_no in range(1, DENSE_V4_TOTAL_COPIES_PER_SIDE + 1):
        pool.append(_v42_current_template(pr, copy_no))

    # Deduplicate mechanically identical score/risk plans while retaining the
    # widest empirical band metadata for review.
    dedup = {}
    for plan in pool:
        key = (
            plan["low"], plan["high"], plan["long_qty"], plan["short_qty"],
            plan["stress_closes"],
        )
        prev = dedup.get(key)
        if prev is None:
            dedup[key] = plan
            continue
        prev_width = (
            (prev.get("high_q") or Decimal("0"))
            - (prev.get("low_q") or Decimal("0"))
        )
        width = (
            (plan.get("high_q") or Decimal("0"))
            - (plan.get("low_q") or Decimal("0"))
        )
        if width > prev_width:
            dedup[key] = plan
    return list(dedup.values())


def _v42_eval_moves(samples: list[dict], count: int) -> list[Decimal]:
    moves = sorted(Decimal(str(x["move"])) for x in samples)
    if not moves:
        return []
    if len(moves) <= count:
        return moves
    out = []
    for i in range(count):
        idx = int(round(i * (len(moves) - 1) / max(1, count - 1)))
        value = moves[idx]
        if not out or value != out[-1]:
            out.append(value)
    return out


def _v42_plan_lines(plan: dict, ref: Decimal, moves: list[Decimal]) -> list[dict]:
    out = []
    cent = Decimal("0.01")
    for move in moves:
        close = (ref * (Decimal("1") + move)).quantize(cent)
        sim = _v41_simulate_pair(
            Decimal(str(plan["low"])),
            Decimal(str(plan["high"])),
            Decimal(str(plan["long_qty"])),
            Decimal(str(plan["short_qty"])),
            close,
        )
        row = {"move": move, "close": close, "long": None, "short": None}
        if sim["long_settled"]:
            q = Decimal(str(plan["long_qty"]))
            row["long"] = (
                q,
                -(q * Decimal(str(plan["low"])) + Decimal(str(sim["long_fee"]))),
            )
        if sim["short_settled"]:
            q = Decimal(str(plan["short_qty"]))
            row["short"] = (
                -q,
                q * Decimal(str(plan["high"])) - Decimal(str(sim["short_fee"])),
            )
        out.append(row)
    return out


def _v42_line_score(line: tuple[Decimal, Decimal] | None, final_s: Decimal) -> Decimal | None:
    if line is None:
        return None
    return line[0] * final_s + line[1]


def _v42_plan_score(lines: dict, final_s: Decimal) -> Decimal | None:
    scores = [
        score for score in (
            _v42_line_score(lines.get("long"), final_s),
            _v42_line_score(lines.get("short"), final_s),
        )
        if score is not None
    ]
    return max(scores) if scores else None


def _v42_frontier_stats(
    frontier: list[list[Decimal]],
    podium: list[Decimal],
) -> dict:
    gaps = []
    covered = 0
    for row in frontier:
        for idx, score in enumerate(row):
            gap = podium[idx] - score
            if gap <= 0:
                covered += 1
                gaps.append(Decimal("0"))
            else:
                gaps.append(gap)
    total = len(gaps)
    positive = [g for g in gaps if g > 0]
    return {
        "cells": total,
        "covered_cells": covered,
        "coverage_rate": Decimal(covered) / Decimal(total) if total else Decimal("0"),
        "mean_positive_gap": (
            sum(positive, Decimal("0")) / Decimal(len(positive))
            if positive else Decimal("0")
        ),
        "max_gap": max(gaps) if gaps else Decimal("0"),
        "total_gap": sum(gaps, Decimal("0")),
    }


def _v42_apply_candidate(
    frontier: list[list[Decimal]],
    lines: list[dict],
    s_grid: list[Decimal],
) -> list[list[Decimal]]:
    out = [list(row) for row in frontier]
    for mi, scenario in enumerate(lines):
        for si, final_s in enumerate(s_grid):
            score = _v42_plan_score(scenario, final_s)
            if score is not None and score > out[mi][si]:
                out[mi][si] = score
    return out


def _v42_greedy_select(
    pool: list[dict],
    existing: dict[Decimal, Decimal],
    podium_map: dict[Decimal, Decimal],
    ref: Decimal,
    eval_moves: list[Decimal],
    s_grid: list[Decimal],
    copies: int,
) -> tuple[list[dict], list[list[Decimal]], dict]:
    podium = [podium_map[s] for s in s_grid]
    frontier = [
        [existing[s] for s in s_grid]
        for _move in eval_moves
    ]
    selected = []
    remaining = []
    for idx, plan in enumerate(pool):
        remaining.append({
            "index": idx,
            "plan": plan,
            "lines": _v42_plan_lines(plan, ref, eval_moves),
        })

    baseline = _v42_frontier_stats(frontier, podium)
    rounds = []
    current_stats = baseline
    for _round in range(max(0, int(copies))):
        best = None
        for item in remaining:
            trial = _v42_apply_candidate(frontier, item["lines"], s_grid)
            stats = _v42_frontier_stats(trial, podium)
            key = (
                stats["covered_cells"],
                -stats["total_gap"],
                -stats["max_gap"],
            )
            if best is None or key > best["key"]:
                best = {
                    "key": key,
                    "item": item,
                    "frontier": trial,
                    "stats": stats,
                }
        if best is None:
            break

        # Stop once the candidate pool cannot improve the objective. The first
        # real V4.2 run showed rounds 2..8 selecting mechanically different
        # plans with exactly identical coverage/gap statistics.
        improved = (
            best["stats"]["covered_cells"] > current_stats["covered_cells"]
            or best["stats"]["total_gap"] < current_stats["total_gap"]
            or best["stats"]["max_gap"] < current_stats["max_gap"]
        )
        if not improved:
            break

        chosen = best["item"]
        selected.append(chosen["plan"])
        frontier = best["frontier"]
        current_stats = best["stats"]
        rounds.append(best["stats"])
        remaining = [x for x in remaining if x["index"] != chosen["index"]]

    return selected, frontier, {
        "baseline": baseline,
        "rounds": rounds,
        "saturated": len(selected) < max(0, int(copies)),
        "selected_count": len(selected),
    }


def _v42_full_report(
    state: dict,
    pr: dict,
    samples: list[dict],
    s_grid: list[Decimal],
    copies: int,
    greedy_move_scenarios: int,
) -> dict:
    competitor = _v42_competitor_model(state, s_grid)
    existing = _v42_existing_frontier(state, s_grid)
    pool = _v42_candidate_pool(pr, samples)
    eval_moves = _v42_eval_moves(samples, greedy_move_scenarios)
    selected, _frontier, greedy = _v42_greedy_select(
        pool,
        existing,
        competitor["podium"],
        Decimal(str(pr["px"])),
        eval_moves,
        s_grid,
        copies,
    )

    # Final evaluation uses every retained historical move, not only the
    # quantile-thinned move set used by greedy search.
    full_moves = [Decimal(str(x["move"])) for x in samples]
    podium_vec = [competitor["podium"][s] for s in s_grid]
    full_frontier = [[existing[s] for s in s_grid] for _ in full_moves]
    for plan in selected:
        full_frontier = _v42_apply_candidate(
            full_frontier,
            _v42_plan_lines(plan, Decimal(str(pr["px"])), full_moves),
            s_grid,
        )
    final_stats = _v42_frontier_stats(full_frontier, podium_vec)

    grid = []
    for si, final_s in enumerate(s_grid):
        vals = sorted(row[si] for row in full_frontier)
        beat = sum(1 for value in vals if value >= podium_vec[si])
        grid.append({
            "S": final_s,
            "podium_static": podium_vec[si],
            "existing_best": existing[final_s],
            "optimized_min": vals[0],
            "optimized_p10": _v41_quantile(vals, Decimal("0.10")),
            "optimized_p50": _v41_quantile(vals, Decimal("0.50")),
            "optimized_max": vals[-1],
            "beat_podium_rate": Decimal(beat) / Decimal(len(vals)) if vals else Decimal("0"),
        })

    return {
        "mode": "read_only_v42_static_podium_scenario",
        "ref_sweep": pr["n"],
        "ref": pr["px"],
        "historical_samples": len(samples),
        "candidate_pool": len(pool),
        "greedy_move_scenarios": len(eval_moves),
        "target_start": s_grid[0],
        "target_end": s_grid[-1],
        "target_step": s_grid[1] - s_grid[0] if len(s_grid) > 1 else Decimal("0"),
        "competitor": {
            "pnl_sweep": competitor["pnl_sweep"],
            "mark": competitor["mark"],
            "lines": competitor["lines"][:12],
        },
        "baseline_stats": greedy["baseline"],
        "greedy_round_stats": greedy["rounds"],
        "optimizer_saturated": greedy.get("saturated"),
        "selected_count": greedy.get("selected_count"),
        "final_full_history_stats": final_stats,
        "selected": selected,
        "grid": grid,
        "note": (
            "Competitor scores are static-current-position stress lines, not a "
            "forecast. consecutive_pnl_slope and flat_score_fallback evidence "
            "are weaker than published_position."
        ),
    }


def cmd_dense_v42_optimize(args) -> None:
    state = load_state()
    pr = fresh_price(max_age=10**9)
    samples = _v41_move_samples(args.lookback)
    if len(samples) < 24:
        raise SystemExit(f"only {len(samples)} usable V4.2 samples")
    s_grid = _v42_s_grid(
        Decimal(str(args.start)),
        Decimal(str(args.end)),
        Decimal(str(args.step)),
    )
    report = _v42_full_report(
        state,
        pr,
        samples,
        s_grid,
        int(args.copies),
        int(args.move_scenarios),
    )
    print(json.dumps(report, indent=2, default=str))


def cmd_dense_v42_grid(args) -> None:
    state = load_state()
    pr = fresh_price(max_age=10**9)
    samples = _v41_move_samples(args.lookback)
    if len(samples) < 24:
        raise SystemExit(f"only {len(samples)} usable V4.2 samples")
    s_grid = _v42_s_grid(
        Decimal(str(args.start)),
        Decimal(str(args.end)),
        Decimal(str(args.step)),
    )
    report = _v42_full_report(
        state,
        pr,
        samples,
        s_grid,
        int(args.copies),
        int(args.move_scenarios),
    )
    print(
        "S,podium_static,existing_best,optimized_min,optimized_p10,"
        "optimized_p50,optimized_max,beat_podium_rate"
    )
    for row in report["grid"]:
        print(
            row["S"],
            row["podium_static"],
            row["existing_best"],
            row["optimized_min"],
            row["optimized_p10"],
            row["optimized_p50"],
            row["optimized_max"],
            row["beat_podium_rate"],
            sep=",",
        )


def cmd_dense_v4_preview(_args) -> None:
    pr = fresh_price(max_age=10**9)
    print("=== DENSE V4 PREVIEW ===")
    print("sweep:", pr["n"], "ref:", pr["px"], "age_s:", pr["age_s"])
    lo, hi = dense_v4_limit_bounds(pr)
    print("official_limits:", lo, hi)
    print("copy,long_px,short_px,qty,short_offset,safety,required_per_contract")
    for copy_no in range(1, DENSE_V4_TOTAL_COPIES_PER_SIDE + 1):
        plan = dense_v4_plan_copy(pr, copy_no)
        print(
            copy_no,
            plan["low"],
            plan["high"],
            plan["qty"],
            plan["short_offset"],
            plan["safety"],
            plan["required_per_contract"],
            sep=",",
        )


def cmd_enable_dense_v4(_args) -> None:
    state = load_state()
    dense = state.setdefault("dense", {})
    pending = dense.get("pending")
    if isinstance(pending, dict) and (pending.get("trades") or {}):
        raise SystemExit(
            "refusing V4 mode switch while the pending Dense batch has partial trades; "
            "wait for it to finish or inspect dense-status first"
        )
    dense["enabled"] = True
    dense["v4_enabled"] = True
    dense["v4_enabled_at"] = datetime.now(timezone.utc).isoformat()
    dense["v3_enabled"] = False
    dense["v2_enabled"] = False
    dense["mode"] = "dense-v4-asymmetric-clawback-ladder"
    dense["v4_long_offset"] = str(DENSE_V4_LONG_OFFSET)
    dense["v4_short_offsets"] = [str(x) for x in DENSE_V4_SHORT_OFFSETS]
    dense["v4_short_safeties"] = [str(x) for x in DENSE_V4_SHORT_SAFETIES]
    dense["v4_total_copies_per_side"] = DENSE_V4_TOTAL_COPIES_PER_SIDE
    # Compatibility field used by older displays only.
    dense["v4_reference_offset"] = str(DENSE_V3_OFFSET)
    dense["v4_ref_age_gate_enabled"] = False
    dense.setdefault("v4_tickets", [])
    dense_v2_init_bounds(dense)
    state["legacy_strategy_frozen"] = True

    pr = fresh_price(max_age=10**9)
    dense["v4_enabled_sweep"] = pr["n"]
    dense["v4_not_before_sweep"] = pr["n"] + 1
    save_state(state)

    # Reuse the already-proven V3 paired reserve structure. If the pool was
    # partially consumed, replenish it before the first V4 trade sweep.
    reserve_event = dense_v3_maintain_reserve(state, pr["n"])
    if reserve_event:
        dense["last_reserve_event"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            **reserve_event,
        }
        save_state(state)

    print("Dense V4 ENABLED")
    print("coverage: every aligned referee sweep")
    print("long quote: referee lower limit (~-5%)")
    print("short ladder: 3x +1.0%, 2x +1.7%, 3x +2.0%")
    print("copies per side:", DENSE_V4_TOTAL_COPIES_PER_SIDE)
    print("ref age gate: DISABLED")
    print("flow/state alignment + room/missed/lock gates: ENABLED")
    print("paired reserve target sets:", dense.get("v3_reserve_target_sets") or DENSE_V3_RESERVE_TARGET_SETS)
    print("enabled on sweep:", dense.get("v4_enabled_sweep"))
    print("first V4 trade sweep >=", dense.get("v4_not_before_sweep"))
    print("dynamic key safety cap:", DENSE_MAX_DYNAMIC_KEYS)
    print("existing positions and current pending baseline batch are preserved")


def cmd_disable_dense(_args) -> None:
    state = load_state()
    dense = state.setdefault("dense", {})
    dense["enabled"] = False
    dense["disabled_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    print("dense mode DISABLED; no new dense batches will be created")


def cmd_dense_status(_args) -> None:
    state = load_state()
    dense = state.get("dense") or {}
    print("enabled:", bool(dense.get("enabled")))
    print("v2_enabled:", bool(dense.get("v2_enabled")))
    print("v3_enabled:", bool(dense.get("v3_enabled")))
    print("v4_enabled:", bool(dense.get("v4_enabled")))
    print("submitted_sets:", len(dense.get("tickets") or []))
    active_offset = (
        "v4-ladder" if dense.get("v4_enabled")
        else dense.get("v3_offset") if dense.get("v3_enabled")
        else dense.get("v2_offset") if dense.get("v2_enabled")
        else dense.get("offset")
    )
    print("active_offset:", active_offset)
    print("historical_low_ref:", dense.get("historical_low_ref"))
    print("historical_high_ref:", dense.get("historical_high_ref"))
    print("boost_tickets:", len(dense.get("boost_tickets") or []))
    reserve = dense.get("boost_reserve") or []
    print("boost_reserve_registered:", sum(1 for x in reserve if x.get("status") == "registered"))
    current_sweep_for_reserve = None
    try:
        _reserve_pr = fresh_price(max_age=10**9)
        current_sweep_for_reserve = int(_reserve_pr["n"])
    except Exception:
        current_sweep_for_reserve = int(dense.get("last_seen_sweep") or 0)
    print("boost_reserve_ready:", sum(
        1 for x in reserve
        if x.get("status") == "registered"
        and int(x.get("ready_after_sweep", 10**9)) <= current_sweep_for_reserve
    ))
    v3_reserve = dense.get("v3_reserve") or []
    print("v3_total_copies_per_side:", dense.get("v3_total_copies_per_side"))
    print("v3_enabled_sweep:", dense.get("v3_enabled_sweep"))
    print("v3_not_before_sweep:", dense.get("v3_not_before_sweep"))
    print("v3_multiplicity_tickets:", len(dense.get("v3_tickets") or []))
    print("v3_reserve_registered:", sum(1 for x in v3_reserve if x.get("status") == "registered"))
    print("v3_reserve_ready:", sum(
        1 for x in v3_reserve
        if x.get("status") == "registered"
        and int(x.get("ready_after_sweep", 10**9)) <= current_sweep_for_reserve
    ))
    print("v3_reserve_partial_errors:", sum(1 for x in v3_reserve if x.get("status") == "partial_error"))
    print("v4_total_copies_per_side:", dense.get("v4_total_copies_per_side"))
    print("v4_enabled_sweep:", dense.get("v4_enabled_sweep"))
    print("v4_not_before_sweep:", dense.get("v4_not_before_sweep"))
    print("v4_long_offset:", dense.get("v4_long_offset"))
    print("v4_short_offsets:", dense.get("v4_short_offsets"))
    print("v4_short_safeties:", dense.get("v4_short_safeties"))
    print("v4_multiplicity_tickets:", len(dense.get("v4_tickets") or []))
    last_v4 = dense.get("last_v4_multiplicity") or {}
    if last_v4:
        print("last_v4_sweep:", last_v4.get("sweep"))
        print("last_v4_ref:", last_v4.get("ref"))
        print("last_v4_long_copies:", last_v4.get("total_long_copies"))
        print("last_v4_short_copies:", last_v4.get("total_short_copies"))
        print("last_v4_reserve_shortage:", last_v4.get("reserve_shortage"))
        print("last_v4_errors:", len(last_v4.get("errors") or []))
    last_v3 = dense.get("last_v3_multiplicity") or {}
    if last_v3:
        print("last_v3_sweep:", last_v3.get("sweep"))
        print("last_v3_ref:", last_v3.get("ref"))
        print("last_v3_long_copies:", last_v3.get("total_long_copies"))
        print("last_v3_short_copies:", last_v3.get("total_short_copies"))
        print("last_v3_reserve_shortage:", last_v3.get("reserve_shortage"))
        print("last_v3_errors:", len(last_v3.get("errors") or []))
    print("v5a_enabled:", bool(dense.get("v5a_enabled")))
    print("v5a_accept_new:", bool(dense.get("v5a_accept_new", True)))
    print("v5a_harvested_count:", len(dense.get("v5a_harvested") or {}))
    active_v5a = dense.get("v5a_active")
    if isinstance(active_v5a, dict):
        print("v5a_active_pair:", active_v5a.get("pair_id"))
        print("v5a_active_stage:", active_v5a.get("stage"))
        print("v5a_active_winner:", active_v5a.get("winner"))
        print("v5a_active_trigger_score:", active_v5a.get("trigger_score"))
    else:
        print("v5a_active_pair: null")
        print("v5a_active_stage: null")
    last_locked_v5a = dense.get("v5a_last_locked")
    if isinstance(last_locked_v5a, dict):
        print("v5a_last_locked_pair:", last_locked_v5a.get("pair_id"))
        print("v5a_last_locked_winner:", last_locked_v5a.get("winner"))
        print("v5a_last_locked_score:", last_locked_v5a.get("locked_score"))
    last_skip_v5a = dense.get("v5a_last_skip")
    if isinstance(last_skip_v5a, dict):
        print("v5a_last_skip_pair:", last_skip_v5a.get("pair_id"))
        print("v5a_last_skip_reason:", last_skip_v5a.get("reason"))
        print("v5a_last_skip_score:", last_skip_v5a.get("winner_score"))

    print("v5b_enabled:", bool(dense.get("v5b_enabled")))
    print("v5b_accept_new:", bool(dense.get("v5b_accept_new", True)))
    print("v5b_closed_cycles:", len(dense.get("v5b_cycles") or []))
    v5b_last_check = dense.get("v5b_last_check")
    if isinstance(v5b_last_check, dict):
        print("v5b_last_check_at:", v5b_last_check.get("at"))
        print("v5b_last_check_sweep:", v5b_last_check.get("sweep"))
        print("v5b_last_check_pending:", v5b_last_check.get("pending"))
        print("v5b_last_check_active:", v5b_last_check.get("active"))
    else:
        print("v5b_last_check_at: null")
        print("v5b_last_check_sweep: null")
    v5b_last_error = dense.get("v5b_last_error")
    if isinstance(v5b_last_error, dict):
        print("v5b_last_error_stage:", v5b_last_error.get("stage"))
        print("v5b_last_error_registered_count:", v5b_last_error.get("registered_count"))
        print("v5b_last_error:", v5b_last_error.get("error"))
    else:
        print("v5b_last_error: null")
    v5b_last_no_seed = dense.get("v5b_last_no_seed")
    if isinstance(v5b_last_no_seed, dict):
        print("v5b_last_no_seed_reason:", v5b_last_no_seed.get("reason"))
        print("v5b_last_no_seed_harvested_count:", v5b_last_no_seed.get("harvested_count"))
        print("v5b_last_no_seed_v4_00213_known:", v5b_last_no_seed.get("v4_00213_known"))
    else:
        print("v5b_last_no_seed_reason: null")
    v5b_pending = dense.get("v5b_pending")
    if isinstance(v5b_pending, dict):
        print("v5b_pending_cycle:", v5b_pending.get("index"))
        print("v5b_pending_source:", v5b_pending.get("source_pair_id"))
        print("v5b_pending_side:", v5b_pending.get("flip_side"))
        print("v5b_pending_ready_after_sweep:", v5b_pending.get("ready_after_sweep"))
    else:
        print("v5b_pending_cycle: null")
    v5b_active = dense.get("v5b_active")
    if isinstance(v5b_active, dict):
        print("v5b_active_cycle:", v5b_active.get("cycle_index"))
        print("v5b_active_source:", v5b_active.get("source_pair_id"))
        print("v5b_active_side:", v5b_active.get("side"))
        print("v5b_active_status:", v5b_active.get("status"))
        print("v5b_active_qty:", v5b_active.get("qty"))
        print("v5b_active_entry_px:", v5b_active.get("entry_px"))
    else:
        print("v5b_active_cycle: null")
        print("v5b_active_status: null")
    v5b_mark = dense.get("v5b_last_mark")
    if isinstance(v5b_mark, dict):
        print("v5b_current_score:", v5b_mark.get("current_score"))
        print("v5b_projected_flat_score:", v5b_mark.get("projected_flat_score"))
        print("v5b_take_score:", v5b_mark.get("take_score"))
        print("v5b_stop_score:", v5b_mark.get("stop_score"))
    v5b_closed = dense.get("v5b_last_closed")
    if isinstance(v5b_closed, dict):
        print("v5b_last_closed_cycle:", v5b_closed.get("cycle_index"))
        print("v5b_last_closed_reason:", v5b_closed.get("close_reason"))
        print("v5b_last_closed_score:", v5b_closed.get("final_locked_score"))

    dynamic_keys = sum(1 for k in state.get("keys", {}) if k.startswith("DENSE-"))
    print("dynamic_keys:", dynamic_keys)
    print("dynamic_key_cap:", DENSE_MAX_DYNAMIC_KEYS)
    print("dynamic_key_budget_remaining:", max(0, DENSE_MAX_DYNAMIC_KEYS - dynamic_keys))
    print("next_index:", dense.get("next_index"))
    print("room_registration_requested_sweep:", dense.get("room_registration_requested_sweep"))
    print("room_registration_confirmed:", room_registration_confirmed(state))
    print("room_recent_activity_age_s:", room_recent_activity_age_s(state["room"]))
    try:
        pr = fresh_price(max_age=10**9)
        print("ref_sweep:", pr["n"])
        print("ref:", pr["px"])
        print("effective_ref_age_s:", pr["age_s"])
        if dense.get("v3_enabled") or dense.get("v4_enabled"):
            print("ref_age_gate_enabled: False")
            print("eligible_by_ref_age: True")
        else:
            print("ref_age_gate_enabled: True")
            print("eligible_by_ref_age:", pr["age_s"] is None or int(pr["age_s"]) <= 120)
    except Exception as e:
        print("ref_status_error:", str(e))

    try:
        latest_flow, _latest_state = latest_flow_and_state()
        print("room_listed_in_latest_flow_registration_events:", flow_lists_room(latest_flow, state["room"]))
        if isinstance(latest_flow, dict):
            print("latest_flow_sweep:", latest_flow.get("n"))
    except Exception as e:
        print("room_status_error:", str(e))

    pending = dense.get("pending")
    if isinstance(pending, dict):
        print("pending_index:", pending.get("index"))
        print("pending_status:", pending.get("status"))
        print("pending_ready_after_sweep:", pending.get("ready_after_sweep"))
        print("pending_needs_owner_reregister:", bool(pending.get("needs_owner_reregister")))
        print("pending_owner_reregister_count:", len(pending.get("owner_reregistrations") or []))
    else:
        print("pending_index: null")
        print("pending_status: null")
        print("pending_ready_after_sweep: null")
    last_ticket = dense.get("last_ticket")
    print("last_ticket:", json.dumps(last_ticket, ensure_ascii=False, sort_keys=True))
    if isinstance(last_ticket, dict):
        for role in ("long", "short"):
            trade = (last_ticket.get("trades") or {}).get(role) or {}
            trade_id = trade.get("trade_id")
            if not trade_id:
                continue
            info = trade_outcome_from_flow(trade_id)
            outcome = info.get("outcome")
            if outcome:
                print(
                    f"last_{role}_outcome:",
                    outcome.get("status"),
                    "sweep:",
                    outcome.get("sweep"),
                )
            else:
                print(
                    f"last_{role}_outcome: NOT_VISIBLE",
                    "omitted_settled:",
                    (info.get("omitted") or {}).get("settled", 0),
                    "omitted_void:",
                    (info.get("omitted") or {}).get("void", 0),
                )


def autopilot_iteration(late_minutes: int = 180) -> dict:
    state = load_state()
    now = datetime.now(timezone.utc)
    ap = state.setdefault("autopilot", {})

    if now >= AUTOPILOT_STOP_TIME_UTC:
        ap["stopped_at"] = now.isoformat()
        ap["stop_reason"] = "contest final window complete"
        save_state(state)
        return {
            "event": "contest_complete",
            "stop": True,
            "at": now.isoformat(),
        }
    ap.setdefault("missed_static", {})
    ap["last_seen_at"] = now.isoformat()

    pr = fresh_price(max_age=10**9)
    ap["last_sweep"] = pr["n"]
    ap["last_ref"] = str(pr["px"])
    ap["last_age_s"] = pr["age_s"]

    if now >= LOCK_TIME_UTC:
        save_state(state)
        return {
            "event": "locked_monitoring",
            "sweep": pr["n"],
            "ref": str(pr["px"]),
            "age_s": pr["age_s"],
            "final_in_seconds": max(0, int((FINAL_TIME_UTC - now).total_seconds())),
        }

    if (state.get("dense") or {}).get("enabled"):
        result = dense_autopilot_step(state, now)
        ap = state.setdefault("autopilot", {})
        ap["last_dense_event"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            **result,
        }
        save_state(state)
        return result

    if state.get("legacy_strategy_frozen"):
        save_state(state)
        return {
            "event": "legacy_frozen_heartbeat",
            "sweep": pr["n"],
            "ref": str(pr["px"]),
            "age_s": pr["age_s"],
            "reason": "legacy static/bracket automation remains frozen",
        }

    for cohort, due_text in STATIC_SCHEDULE_UTC.items():
        k = f"{cohort:02d}"
        if k in state.get("static", {}):
            continue
        if k in ap["missed_static"]:
            continue

        due = datetime.fromisoformat(due_text)
        lag_s = (now - due).total_seconds()
        if lag_s < 0:
            continue

        if lag_s > late_minutes * 60:
            ap["missed_static"][k] = {
                "due": due_text,
                "observed_at": now.isoformat(),
                "lag_minutes": round(lag_s / 60, 1),
                "reason": "outside automatic catch-up window",
            }
            save_state(state)
            return {
                "event": "static_skipped_late",
                "cohort": k,
                "lag_minutes": round(lag_s / 60, 1),
                "sweep": pr["n"],
            }

        try:
            gate = fleet_gate(state)
        except Exception as e:
            save_state(state)
            return {
                "event": "wait_gate_error",
                "cohort": k,
                "error": str(e),
                "sweep": pr["n"],
            }

        if not gate["pass"]:
            save_state(state)
            return {
                "event": "wait_gate_block",
                "cohort": k,
                "checks": gate["checks"],
                "sweep": pr["n"],
            }

        result = open_static_cohort(state, cohort)
        ap = state.setdefault("autopilot", {})
        ap["last_action"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            "action": "open_static",
            "cohort": k,
            "result": result["status"],
            "trade_id": (result.get("trade") or {}).get("trade_id"),
        }
        save_state(state)
        return {
            "event": "static_action",
            "cohort": k,
            "result": result,
            "sweep": pr["n"],
        }

    bracket_event = bracket_autopilot_step(state, now)
    if bracket_event:
        ap = state.setdefault("autopilot", {})
        ap["last_bracket_event"] = {
            "at": datetime.now(timezone.utc).isoformat(),
            **bracket_event,
        }
        save_state(state)
        return bracket_event

    bracket = state.get("bracket") or {}
    round_no = int(bracket.get("round", 0) or 0)

    save_state(state)
    return {
        "event": "heartbeat",
        "sweep": pr["n"],
        "ref": str(pr["px"]),
        "age_s": pr["age_s"],
        "next_static": next(
            (
                f"{cohort:02d}"
                for cohort, due_text in STATIC_SCHEDULE_UTC.items()
                if f"{cohort:02d}" not in state.get("static", {})
                and f"{cohort:02d}" not in ap["missed_static"]
            ),
            None,
        ),
        "bracket_round": round_no,
    }


def cmd_autopilot(args) -> None:
    last_sweep = None
    while True:
        try:
            result = autopilot_iteration(late_minutes=args.late_minutes)
            sweep = result.get("sweep")
            if result.get("event") != "heartbeat" or sweep != last_sweep:
                print(
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(result, ensure_ascii=False, sort_keys=True),
                    flush=True,
                )
            last_sweep = sweep
            if result.get("stop"):
                print("autopilot contest complete; exiting normally", flush=True)
                return
        except KeyboardInterrupt:
            print("autopilot stopped", flush=True)
            return
        except Exception as e:
            print(
                datetime.now(timezone.utc).isoformat(),
                json.dumps({"event": "error", "error": str(e)}, ensure_ascii=False),
                flush=True,
            )

        if args.once:
            return
        time.sleep(max(10, args.poll))


def cmd_open_bracket(_args) -> None:
    state = load_state()
    require_fleet_gate(state)

    bracket = state.setdefault("bracket", {"round": 0, "pairs": []})
    round_no = int(bracket.get("round", 0))
    if round_no not in (0, 1):
        raise SystemExit(f"bracket is already beyond round 1: round={round_no}")

    if round_no == 0:
        bracket.update({
            "round": 1,
            "status": "opening",
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "pairs": [],
        })
        save_state(state)

    existing = {p.get("long"): p for p in bracket.get("pairs", []) if isinstance(p, dict)}
    targets = [
        (f"BR-{i:02d}", f"BR-{i+1:02d}", f"br1-{i:02d}")
        for i in range(1, 17, 2)
    ]

    for long_label, short_label, prefix in targets:
        if long_label in existing:
            print("skip already submitted:", long_label, existing[long_label].get("trade_id"))
            continue
        res = submit_pair(state, long_label, short_label, prefix)
        bracket["pairs"].append(res)
        bracket["status"] = "opening"
        bracket["last_submit_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        existing[long_label] = res
        print(json.dumps(res, ensure_ascii=False))
        time.sleep(0.2)

    if len(bracket.get("pairs", [])) != 8:
        raise SystemExit(
            f"bracket round 1 partial: {len(bracket.get('pairs', []))}/8 pairs saved; "
            "re-run open-bracket to resume without duplicating completed pairs"
        )

    bracket["status"] = "submitted"
    bracket["submitted_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    print("bracket round 1 submitted: 8/8 pairs")


def main() -> None:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("init")
    p.set_defaults(fn=cmd_init)

    p = sp.add_parser("status")
    p.set_defaults(fn=cmd_status)

    p = sp.add_parser("ids")
    p.set_defaults(fn=cmd_ids)

    p = sp.add_parser("progress")
    p.set_defaults(fn=cmd_progress)

    p = sp.add_parser("competitor-scan")
    p.add_argument("--sample", type=int, default=400, help="recent close1 messages to inspect")
    p.add_argument("--pnl", type=int, default=12, help="recent pnl snapshots to inspect")
    p.set_defaults(fn=cmd_competitor_scan)

    p = sp.add_parser("leader-path-replay")
    p.add_argument("--top", type=int, default=8, help="current non-local leaders to reconstruct")
    p.add_argument(
        "--rooms",
        choices=("public", "registered"),
        default="registered",
        help="scan only close1 or all rooms ever listed by the referee",
    )
    p.add_argument(
        "--room-limit",
        type=int,
        default=0,
        help="optional cap on registered rooms scanned; 0 means all",
    )
    p.set_defaults(fn=cmd_leader_path_replay)

    p = sp.add_parser("leader-path-summary")
    p.add_argument("--top", type=int, default=8)
    p.add_argument("--rooms", choices=("public", "registered"), default="registered")
    p.add_argument("--room-limit", type=int, default=0)
    p.set_defaults(fn=cmd_leader_path_summary)

    p = sp.add_parser("leader-pivot-solve")
    p.add_argument("--rank", type=int, default=1)
    p.add_argument("--from-sweep", type=int, default=956)
    p.add_argument("--target-sweep", type=int, default=960)
    p.set_defaults(fn=cmd_leader_pivot_solve)

    p = sp.add_parser("leader-pivot-summary")
    p.add_argument("--rank", type=int, default=1)
    p.add_argument("--from-sweep", type=int, default=956)
    p.add_argument("--target-sweep", type=int, default=960)
    p.set_defaults(fn=cmd_leader_pivot_summary)

    p = sp.add_parser("gate")
    p.set_defaults(fn=cmd_gate)

    p = sp.add_parser("bootstrap")
    p.add_argument("--wait", type=int, default=900, help="seconds to wait for room registration")
    p.add_argument("--delay", type=float, default=0.15, help="delay between owner registration posts")
    p.set_defaults(fn=cmd_bootstrap)

    p = sp.add_parser("open-static")
    p.add_argument("cohort", type=int)
    p.set_defaults(fn=cmd_open_static)

    p = sp.add_parser("check-trade")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--trade-id")
    g.add_argument("--cohort", type=int, choices=range(1, 17))
    p.set_defaults(fn=cmd_check_trade)

    p = sp.add_parser("open-bracket")
    p.set_defaults(fn=cmd_open_bracket)

    p = sp.add_parser("check-bracket")
    p.set_defaults(fn=cmd_check_bracket)

    p = sp.add_parser("enable-dense")
    p.set_defaults(fn=cmd_enable_dense)

    p = sp.add_parser("enable-dense-v2")
    p.set_defaults(fn=cmd_enable_dense_v2)

    p = sp.add_parser("enable-dense-v3")
    p.set_defaults(fn=cmd_enable_dense_v3)

    p = sp.add_parser("dense-v4-preview")
    p.set_defaults(fn=cmd_dense_v4_preview)

    p = sp.add_parser("dense-v41-preview")
    p.add_argument("--lookback", type=int, default=DENSE_V41_LOOKBACK)
    p.set_defaults(fn=cmd_dense_v41_preview)

    p = sp.add_parser("dense-v41-backtest")
    p.add_argument("--lookback", type=int, default=DENSE_V41_LOOKBACK)
    p.set_defaults(fn=cmd_dense_v41_backtest)

    p = sp.add_parser("dense-final-s-grid")
    p.add_argument("--start", type=str, default="200")
    p.add_argument("--end", type=str, default="260")
    p.add_argument("--step", type=str, default="0.50")
    p.set_defaults(fn=cmd_dense_final_s_grid)

    p = sp.add_parser("dense-v42-optimize")
    p.add_argument("--lookback", type=int, default=DENSE_V41_LOOKBACK)
    p.add_argument("--start", type=str, default=str(DENSE_V42_DEFAULT_START))
    p.add_argument("--end", type=str, default=str(DENSE_V42_DEFAULT_END))
    p.add_argument("--step", type=str, default=str(DENSE_V42_DEFAULT_STEP))
    p.add_argument("--copies", type=int, default=DENSE_V4_TOTAL_COPIES_PER_SIDE)
    p.add_argument("--move-scenarios", type=int, default=DENSE_V42_GREEDY_MOVE_SCENARIOS)
    p.set_defaults(fn=cmd_dense_v42_optimize)

    p = sp.add_parser("dense-v42-grid")
    p.add_argument("--lookback", type=int, default=DENSE_V41_LOOKBACK)
    p.add_argument("--start", type=str, default=str(DENSE_V42_DEFAULT_START))
    p.add_argument("--end", type=str, default=str(DENSE_V42_DEFAULT_END))
    p.add_argument("--step", type=str, default=str(DENSE_V42_DEFAULT_STEP))
    p.add_argument("--copies", type=int, default=DENSE_V4_TOTAL_COPIES_PER_SIDE)
    p.add_argument("--move-scenarios", type=int, default=DENSE_V42_GREEDY_MOVE_SCENARIOS)
    p.set_defaults(fn=cmd_dense_v42_grid)

    p = sp.add_parser("dense-v5a-preview")
    p.set_defaults(fn=cmd_dense_v5a_preview)

    p = sp.add_parser("enable-dense-v5a")
    p.set_defaults(fn=cmd_enable_dense_v5a)

    p = sp.add_parser("pause-dense-v5a")
    p.set_defaults(fn=cmd_pause_dense_v5a)

    p = sp.add_parser("dense-v5b-preview")
    p.set_defaults(fn=cmd_dense_v5b_preview)

    p = sp.add_parser("enable-dense-v5b")
    p.set_defaults(fn=cmd_enable_dense_v5b)

    p = sp.add_parser("pause-dense-v5b")
    p.set_defaults(fn=cmd_pause_dense_v5b)

    p = sp.add_parser("enable-dense-v4")
    p.set_defaults(fn=cmd_enable_dense_v4)

    p = sp.add_parser("disable-dense")
    p.set_defaults(fn=cmd_disable_dense)

    p = sp.add_parser("dense-status")
    p.set_defaults(fn=cmd_dense_status)

    p = sp.add_parser("autopilot")
    p.add_argument("--poll", type=int, default=60, help="seconds between checks")
    p.add_argument(
        "--late-minutes",
        type=int,
        default=180,
        help="maximum automatic catch-up delay for a scheduled static cohort",
    )
    p.add_argument("--once", action="store_true", help="run one cycle and exit")
    p.set_defaults(fn=cmd_autopilot)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
