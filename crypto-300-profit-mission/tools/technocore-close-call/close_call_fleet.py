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
from decimal import Decimal, ROUND_DOWN
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
DENSE_QTY_SAFETY = Decimal("0.995")
DENSE_FUNDS_FACTOR = Decimal("1.05")
DENSE_MAX_DYNAMIC_KEYS = 8000


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
    return http_post_json(
        f"{BASE}/r/{room}",
        {"did": key["did"], "sig": sig, "nonce": nonce, "text": text},
    )


def owner_text(did: str) -> str:
    return compact({"t": "owner", "season": SEASON, "key": did})


def room_text(room: str) -> str:
    return compact({"t": "room", "season": SEASON, "room": room})


def parse_export(room: str) -> list[dict]:
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


def room_seen(room: str) -> bool:
    for rec in parse_export("d-close1-flow"):
        p = rec.get("_payload")
        if not isinstance(p, dict):
            continue
        rooms = p.get("rooms")
        if isinstance(rooms, list) and room in rooms:
            return True
        if isinstance(rooms, dict) and room in rooms:
            return True
        if room in json.dumps(rooms, separators=(",", ":")):
            return True
    return False


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
    missed = flow.get("missed") or []
    return room in json.dumps(missed, separators=(",", ":"), ensure_ascii=False)


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
    dense = state.setdefault("dense", {})
    if dense.get("room_registration_confirmed"):
        return True
    try:
        if room_seen(state["room"]):
            dense["room_registration_confirmed"] = True
            dense["room_registration_confirmed_at"] = datetime.now(timezone.utc).isoformat()
            save_state(state)
            return True
    except Exception:
        pass
    return False


def dense_qty(ref_px: Decimal) -> Decimal:
    q = DENSE_QTY_SAFETY * Decimal("10000") / (ref_px * DENSE_FUNDS_FACTOR)
    return q.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def dense_prices(ref_px: Decimal) -> tuple[Decimal, Decimal]:
    cent = Decimal("0.01")
    low = (ref_px * (Decimal("1") - DENSE_OFFSET)).quantize(cent, rounding=ROUND_DOWN)
    high = (ref_px * (Decimal("1") + DENSE_OFFSET)).quantize(cent, rounding=ROUND_DOWN)
    return low, high


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
            "status": "registering",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_sweep": sweep,
            "registrations": {},
            "trades": {},
        }
        dense["pending"] = pending
        dense["next_index"] = idx + 1
        save_state(state)

    if pending.get("status") == "registering":
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
    """Maintain room/owner prerequisites independently of price freshness.

    Important: flow.rooms is a per-sweep registration record, not a durable
    membership list. A room does not need to appear in every later flow post.
    Once a registration is observed, keep that fact locally. The room itself is
    kept alive by our continuing writes, so technocore's 7-day idle deletion
    rule is not a practical risk while this autopilot is running.
    """
    dense = state.setdefault("dense", {})
    pending = dense.get("pending")
    if not isinstance(pending, dict):
        return None

    latest_flow, _st = latest_flow_and_state()
    flow_n = int(latest_flow["n"]) if isinstance(latest_flow, dict) and latest_flow.get("n") is not None else pr["n"]

    if not room_registration_confirmed(state):
        requested = dense.get("room_registration_requested_sweep")
        ack = None
        if requested != flow_n:
            ack = post_signed(
                state,
                "close1",
                state["controller"],
                room_text(state["room"]),
            )
            dense["room_registration_requested_sweep"] = flow_n
            dense["room_registration_requested_at"] = datetime.now(timezone.utc).isoformat()
            save_state(state)
        return {
            "event": "dense_wait_room_registration",
            "sweep": pr["n"],
            "flow_sweep": flow_n,
            "room": state["room"],
            "registration_posted": requested != flow_n,
            "pending_index": pending.get("index"),
            "ack": ack.strip().splitlines()[0] if isinstance(ack, str) and ack.strip() else None,
        }

    # A prior false-positive "room inactive" check may have marked the pending
    # owners for re-registration. Re-posting is harmless and gives the pending
    # batch a clean, post-fix registration point.
    if pending.get("needs_owner_reregister"):
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
        dense.pop("room_registration_requested_sweep", None)
        dense.pop("room_registration_requested_at", None)
        save_state(state)
        return {
            "event": "dense_owner_registrations_reposted",
            "sweep": pr["n"],
            "flow_sweep": flow_n,
            "index": pending.get("index"),
            "ready_after_sweep": pending["ready_after_sweep"],
            "count": len(reposted),
        }

    dense.pop("room_registration_requested_sweep", None)
    dense.pop("room_registration_requested_at", None)
    save_state(state)
    return None


def dense_submit_pending(state: dict, pr: dict) -> dict | None:
    dense = state.setdefault("dense", {})
    pending = dense.get("pending")
    if not isinstance(pending, dict) or pending.get("status") != "registered":
        return None
    if pr["n"] < int(pending.get("ready_after_sweep", 10**9)):
        return None

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
    qty = dense_qty(pr["px"])
    low, high = dense_prices(pr["px"])
    if qty < Decimal("0.1"):
        raise RuntimeError("dense quantity below minimum")

    trades = pending.setdefault("trades", {})
    if "long" not in trades:
        tid = f"d{pending['index']:05d}l-{int(time.time())}"
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
        tid = f"d{pending['index']:05d}s-{int(time.time())}"
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
        ack = post_signed(state, state["room"], labels["short"], text)
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

    pending["status"] = "submitted"
    pending["submitted_at"] = datetime.now(timezone.utc).isoformat()
    pending["trade_sweep"] = pr["n"]
    pending["ref"] = str(pr["px"])
    pending["low"] = str(low)
    pending["high"] = str(high)
    pending["qty"] = str(qty)
    dense.setdefault("tickets", []).append(pending)
    dense["last_ticket"] = pending
    dense["pending"] = None
    dense["submitted_sets"] = len(dense["tickets"])
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
    }


def dense_autopilot_step(state: dict, now: datetime) -> dict:
    dense = state.setdefault("dense", {})
    pr = fresh_price(max_age=10**9)

    # Registration does not depend on a fresh trading reference. Keep one batch
    # pre-registered so a future fresh sweep can be used immediately instead of
    # wasting that sweep on key creation.
    pending = dense.get("pending")
    if not isinstance(pending, dict) or pending.get("status") == "registering":
        pending = dense_register_pending(state, pr["n"])
        if pr["age_s"] is not None and int(pr["age_s"]) > 120:
            return {
                "event": "dense_batch_registered_wait_fresh",
                "index": pending["index"],
                "sweep": pr["n"],
                "age_s": pr["age_s"],
                "ready_after_sweep": pending["ready_after_sweep"],
                "labels": pending["labels"],
            }

    maintenance = dense_room_maintenance(state, pr)
    if maintenance:
        return maintenance

    if pr["age_s"] is not None and int(pr["age_s"]) > 120:
        return {
            "event": "dense_wait_fresh_ref",
            "sweep": pr["n"],
            "age_s": pr["age_s"],
            "pending_index": (dense.get("pending") or {}).get("index"),
            "pending_status": (dense.get("pending") or {}).get("status"),
        }

    # Retry a ready pending batch on the same sweep until flow/state catch up.
    # Only de-duplicate after the pending batch has either submitted or is not yet ready.
    submitted = dense_submit_pending(state, pr)
    if submitted and submitted.get("event") not in ("dense_wait_alignment", "dense_wait_room_catchup", "dense_wait_room_registration", "dense_owner_registrations_reposted"):
        dense["last_seen_sweep"] = pr["n"]
        save_state(state)
        pending = dense_register_pending(state, pr["n"])
        submitted["next_batch"] = pending["index"]
        return submitted
    if submitted:
        return submitted

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
        "ready_after_sweep": pending["ready_after_sweep"],
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
    pnl_rows = pnl_rows[-max(1, int(args.pnl)):]

    print("=== CLOSE CALL COMPETITOR SCAN ===")
    print("ref_sweep:", pr["n"], "ref:", pr["px"], "age_s:", pr["age_s"])

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
        pairs = _pnl_pairs(latest)
        print("\n# latest public top")
        for i, (did, score) in enumerate(pairs[:25], 1):
            print(i, did, score)

    positions = latest_payload("d-close1-positions", "positions")
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

    rows = parse_export("close1")
    sample = rows[-max(1, int(args.sample)):]
    kinds = Counter()
    templates = Counter()
    template_makers = defaultdict(set)
    deviations = Counter()
    large_terms = []

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
        try:
            px = Decimal(str(terms["px"]))
            qty = Decimal(str(terms["qty"]))
            dev = (px / pr["px"] - Decimal("1")) * Decimal("100")
            if qty >= Decimal("40"):
                bucket = dev.quantize(Decimal("0.1"))
                deviations[str(bucket)] += 1
                large_terms.append({
                    "side": terms.get("side"),
                    "px": str(px),
                    "qty": str(qty),
                    "dev_pct": str(dev.quantize(Decimal("0.01"))),
                    "id": terms.get("id"),
                })
        except Exception:
            pass

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

    print("large_qty_deviation_buckets_pct:", json.dumps(dict(deviations), sort_keys=True))
    print("recent_large_terms:")
    for item in large_terms[-20:]:
        print(json.dumps(item, sort_keys=True))


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
    print("submitted_sets:", len(dense.get("tickets") or []))
    print("next_index:", dense.get("next_index"))
    print("room_registration_requested_sweep:", dense.get("room_registration_requested_sweep"))
    print("room_registration_confirmed:", room_registration_confirmed(state))
    print("room_recent_activity_age_s:", room_recent_activity_age_s(state["room"]))
    try:
        pr = fresh_price(max_age=10**9)
        print("ref_sweep:", pr["n"])
        print("ref:", pr["px"])
        print("effective_ref_age_s:", pr["age_s"])
        print("fresh_for_trade:", pr["age_s"] is None or int(pr["age_s"]) <= 120)
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
