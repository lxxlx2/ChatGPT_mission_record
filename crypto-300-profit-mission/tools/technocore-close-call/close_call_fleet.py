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
    room_ok = False
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
        rooms = p.get("rooms")
        if isinstance(rooms, list) and state["room"] in rooms:
            room_ok = True
        elif isinstance(rooms, dict) and state["room"] in rooms:
            room_ok = True
        elif state["room"] in json.dumps(rooms, separators=(",", ":")):
            room_ok = True

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
    age = p.get("age_s")
    if age is None and ref.get("time"):
        try:
            ts = datetime.fromisoformat(str(ref["time"]).replace("Z", "+00:00"))
            age = max(0, int((datetime.now(timezone.utc) - ts).total_seconds()))
        except Exception:
            age = None
    if age is not None and int(age) > max_age:
        raise RuntimeError(f"stale referee reference: age_s={age} > {max_age}")
    n = int(p["n"])
    return {"n": n, "px": px, "age_s": age, "raw": p}


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
