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
- open one static time-layer pair
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
    return {
        "trade_id": tid,
        "long": long_label,
        "short": short_label,
        "qty": str(qty),
        "px": str(px),
        "sweep": pr["n"],
        "response": response.strip(),
    }


def cmd_open_static(args) -> None:
    if not 1 <= args.cohort <= 16:
        raise SystemExit("cohort must be 1..16")
    state = load_state()
    k = f"{args.cohort:02d}"
    res = submit_pair(state, f"TIME-{k}-L", f"TIME-{k}-S", f"t{k}")
    state["static"][k] = res
    save_state(state)
    print(json.dumps(res, indent=2))


def cmd_open_bracket(_args) -> None:
    state = load_state()
    if int(state["bracket"].get("round", 0)) != 0:
        raise SystemExit("bracket round 1 already initialized")
    pairs = []
    for i in range(1, 17, 2):
        long_label = f"BR-{i:02d}"
        short_label = f"BR-{i+1:02d}"
        res = submit_pair(state, long_label, short_label, f"br1-{i:02d}")
        pairs.append(res)
        print(json.dumps(res))
        time.sleep(0.2)
    state["bracket"] = {
        "round": 1,
        "opened_at": datetime.now(timezone.utc).isoformat(),
        "pairs": pairs,
    }
    save_state(state)
    print("bracket round 1 submitted")


def main() -> None:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("init")
    p.set_defaults(fn=cmd_init)

    p = sp.add_parser("status")
    p.set_defaults(fn=cmd_status)

    p = sp.add_parser("bootstrap")
    p.add_argument("--wait", type=int, default=900, help="seconds to wait for room registration")
    p.add_argument("--delay", type=float, default=0.15, help="delay between owner registration posts")
    p.set_defaults(fn=cmd_bootstrap)

    p = sp.add_parser("open-static")
    p.add_argument("cohort", type=int)
    p.set_defaults(fn=cmd_open_static)

    p = sp.add_parser("open-bracket")
    p.set_defaults(fn=cmd_open_bracket)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
