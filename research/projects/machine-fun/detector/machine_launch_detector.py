"""Independent, read-only Machine.fun LaunchLab event watcher.

No Frank imports, production mutations, trading, mail, daemon installation,
private keys, or credentials persisted. Manual run only.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib import request

PLATFORM_CONFIG = "3hVbfgB77tL1qDKhtMQoe4Gv7qPN2dGmKpD2KxWP2sPb"
LAUNCHLAB_PROGRAM = "LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj"
DISCRIMINATORS = {
    bytes.fromhex("4399af27da102620"): "InitializeV2",
    bytes.fromhex("25be7ede2c9aab11"): "InitializeWithToken2022",
}
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def decode_base58(value: str) -> bytes:
    n = 0
    for char in value:
        digit = B58_ALPHABET.find(char)
        if digit < 0:
            raise ValueError("invalid base58")
        n = 58 * n + digit
    zeros = len(value) - len(value.lstrip("1"))
    return b"\0" * zeros + (n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b"")


@dataclass(frozen=True)
class Launch:
    signature: str
    slot: int
    block_time: int | None
    instruction: str
    mint: str
    pool: str
    creator: str
    payer: str
    quote_mint: str
    platform_config: str
    evidence: str = "CHAIN_PLATFORM_CANDIDATE_UNENDORSED"


def detect_launches(tx: dict, signature: str, platform: str = PLATFORM_CONFIG) -> list[Launch]:
    """Parse all top-level and CPI raw compiled instructions; fail closed.

    RPC must use getTransaction encoding=json and maxSupportedTransactionVersion=1.
    """
    if not tx or not isinstance(tx, dict) or not isinstance(tx.get("meta"), dict):
        return []
    if tx["meta"].get("err") is not None:
        return []
    message = tx.get("transaction", {}).get("message", {})
    if not isinstance(message, dict):
        return []
    keys = [k.get("pubkey") if isinstance(k, dict) else k for k in message.get("accountKeys", [])]
    loaded = tx["meta"].get("loadedAddresses") or {}
    keys += list(loaded.get("writable") or []) + list(loaded.get("readonly") or [])
    instructions = list(message.get("instructions") or [])
    for inner in tx["meta"].get("innerInstructions") or []:
        instructions.extend(inner.get("instructions") or [])
    found: dict[tuple[str, str], Launch] = {}
    for ix in instructions:
        if not isinstance(ix, dict) or not isinstance(ix.get("programIdIndex"), int):
            continue
        try:
            if keys[ix["programIdIndex"]] != LAUNCHLAB_PROGRAM:
                continue
            raw = decode_base58(ix["data"])
            name = DISCRIMINATORS.get(raw[:8])
            if name is None:
                continue
            accounts = ix["accounts"]
            if len(accounts) < 8:
                continue
            payer, creator, config, pool, mint, quote = (
                keys[accounts[0]], keys[accounts[1]], keys[accounts[3]],
                keys[accounts[5]], keys[accounts[6]], keys[accounts[7]]
            )
            if config != platform or len({pool, mint, quote}) != 3:
                continue
            if not all(isinstance(s, str) and s for s in (payer, creator, pool, mint, quote)):
                continue
            event = Launch(signature, int(tx["slot"]), tx.get("blockTime"), name,
                           mint, pool, creator, payer, quote, config)
            found[(pool, mint)] = event
        except (ValueError, TypeError, KeyError, IndexError, OverflowError):
            continue
    return list(found.values())


class Journal:
    def __init__(self, location: Path):
        location.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(location)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS checkpoint (id INTEGER PRIMARY KEY CHECK(id=1), signature TEXT NOT NULL, slot INTEGER NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS events (signature TEXT PRIMARY KEY, slot INTEGER NOT NULL, state TEXT NOT NULL, payload TEXT, observed_at INTEGER NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS gaps (id INTEGER PRIMARY KEY AUTOINCREMENT, observed_at INTEGER NOT NULL, reason TEXT NOT NULL)")
        self.db.commit()

    def checkpoint(self) -> tuple[str, int] | None:
        row = self.db.execute("SELECT signature,slot FROM checkpoint WHERE id=1").fetchone()
        return (row[0], row[1]) if row else None

    def set_checkpoint(self, signature: str, slot: int) -> None:
        with self.db:
            self.db.execute("INSERT INTO checkpoint(id,signature,slot) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET signature=excluded.signature,slot=excluded.slot", (signature, slot))

    def state(self, signature: str) -> str | None:
        row = self.db.execute("SELECT state FROM events WHERE signature=?", (signature,)).fetchone()
        return row[0] if row else None

    def save(self, signature: str, slot: int, state: str, payload: str | None = None) -> None:
        prior = self.state(signature)
        if prior in ("LOCAL_ACCEPTED", "STDOUT_EMITTED") or (prior == "CANDIDATE" and state in ("IGNORED", "PENDING")):
            return
        with self.db:
            self.db.execute("INSERT INTO events(signature,slot,state,payload,observed_at) VALUES(?,?,?,?,?) ON CONFLICT(signature) DO UPDATE SET slot=excluded.slot,state=excluded.state,payload=excluded.payload", (signature, slot, state, payload, int(time.time())))

    def pending(self) -> list[tuple[str, int]]:
        return self.db.execute("SELECT signature,slot FROM events WHERE state='PENDING' ORDER BY slot LIMIT 100").fetchall()

    def candidates(self) -> list[tuple[str, str]]:
        return self.db.execute("SELECT signature,payload FROM events WHERE state='CANDIDATE' ORDER BY slot LIMIT 100").fetchall()

    def record_gap(self, reason: str) -> None:
        with self.db:
            self.db.execute("INSERT INTO gaps(observed_at,reason) VALUES(?,?)", (int(time.time()), reason))

    def close(self) -> None:
        self.db.close()


class Rpc:
    def __init__(self, http_url: str, timeout: float = 12):
        if not http_url.startswith("https://"):
            raise ValueError("HTTP RPC URL must start with https://")
        self.http_url, self.timeout = http_url, timeout
        self.seq = 0

    def call(self, method: str, params: list) -> object:
        self.seq += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self.seq, "method": method, "params": params}).encode()
        req = request.Request(self.http_url, body, {"Content-Type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=self.timeout) as res:
            response = json.loads(res.read(8_000_000))
        if response.get("error"):
            raise RuntimeError(f"RPC {method}: code {response['error'].get('code', 'unknown')}")
        return response.get("result")

    def signature_page(self, platform: str, before: str | None, limit: int) -> list[dict]:
        cfg = {"limit": limit, "commitment": "confirmed"}
        if before:
            cfg["before"] = before
        return self.call("getSignaturesForAddress", [platform, cfg]) or []

    def transaction(self, signature: str) -> dict | None:
        return self.call("getTransaction", [signature, {"encoding": "json", "commitment": "confirmed", "maxSupportedTransactionVersion": 1}])


async def execute_rpc(rpc: Rpc, method: str, *args):
    return await asyncio.to_thread(getattr(rpc, method), *args)


class Detector:
    def __init__(self, rpc: Rpc, journal: Journal, platform: str = PLATFORM_CONFIG,
                 local_notification: bool = False, page_size: int = 100, max_pages: int = 25):
        self.rpc, self.journal, self.platform = rpc, journal, platform
        self.local_notification = local_notification
        self.page_size, self.max_pages = page_size, max_pages

    async def process(self, signature: str, slot: int) -> None:
        if self.journal.state(signature) in ("IGNORED", "CANDIDATE", "LOCAL_ACCEPTED", "STDOUT_EMITTED"):
            return
        tx = None
        for delay in (0, 0.5, 1, 2):
            if delay:
                await asyncio.sleep(delay)
            try:
                tx = await execute_rpc(self.rpc, "transaction", signature)
                if tx is not None:
                    break
            except Exception:
                pass
        if tx is None:
            self.journal.save(signature, slot, "PENDING")
            return
        if not isinstance(tx.get("slot"), int) or not isinstance(tx.get("transaction", {}).get("message"), dict) or not isinstance(tx.get("meta"), dict):
            self.journal.save(signature, slot, "PENDING")
            return
        launches = detect_launches(tx, signature, self.platform)
        if not launches:
            self.journal.save(signature, slot, "IGNORED")
            return
        payload = json.dumps([asdict(x) for x in launches], ensure_ascii=False, separators=(",", ":"))
        self.journal.save(signature, slot, "CANDIDATE", payload)
        await self.deliver()

    async def deliver(self) -> None:
        for signature, payload in self.journal.candidates():
            events = json.loads(payload)
            # Console emission is only an observer output, not a remote delivery receipt.
            for event in events:
                print(json.dumps({"type": "MACHINE_FUN_CHAIN_CANDIDATE", **event}, ensure_ascii=False), flush=True)
            if self.local_notification:
                try:
                    for event in events:
                        title = "Machine.fun candidate launch"
                        body = f"Mint {event['mint']}  Slot {event['slot']} (UNENDORSED)"
                        await asyncio.to_thread(subprocess.run, ["osascript", "-e", 'on run argv\n display notification (item 2 of argv) with title (item 1 of argv)\nend run', title, body], capture_output=True, check=True, timeout=8)
                except Exception:
                    print("LOCAL_DELIVERY_FAILED: candidate remains pending", file=sys.stderr, flush=True)
                    continue
            # Terminal states mean emitted to a sink, not human receipt/Gmail SENT.
            state = "LOCAL_ACCEPTED" if self.local_notification else "STDOUT_EMITTED"
            self.journal.save(signature, int(events[0]["slot"]), state, payload)

    async def backfill(self) -> None:
        marker = self.journal.checkpoint()
        if marker is None:
            newest = await execute_rpc(self.rpc, "signature_page", self.platform, None, 1)
            if newest:
                self.journal.set_checkpoint(newest[0]["signature"], newest[0]["slot"])
                print("INITIAL_FENCE_SET: existing history not emitted", file=sys.stderr, flush=True)
            else:
                print("INITIAL_FENCE_EMPTY: next subscription event will be checked", file=sys.stderr, flush=True)
            return
        older_before = None
        collected: list[dict] = []
        found = False
        exhausted = False
        for _ in range(self.max_pages):
            page = await execute_rpc(self.rpc, "signature_page", self.platform, older_before, self.page_size)
            if not page:
                exhausted = True
                break
            for item in page:
                if item["signature"] == marker[0]:
                    found = True
                    break
                collected.append(item)
            if found:
                break
            if len(page) < self.page_size:
                exhausted = True
                break
            older_before = page[-1]["signature"]
        if not found:
            reason = "checkpoint not encountered within bounded history" + (" (history exhausted)" if exhausted else " (page budget hit)")
            self.journal.record_gap(reason)
            print("COVERAGE_GAP: "+reason, file=sys.stderr, flush=True)
            # Still inspect collected events; never claim this history window is complete.
        for item in reversed(collected):
            if item.get("err") is not None:
                self.journal.save(item["signature"], item["slot"], "IGNORED")
            else:
                await self.process(item["signature"], item["slot"])
        if found and collected:
            self.journal.set_checkpoint(collected[0]["signature"], collected[0]["slot"])

    async def retry_pending(self) -> None:
        for signature, slot in self.journal.pending():
            await self.process(signature, slot)
        await self.deliver()


async def listen(ws_url: str, detector: Detector, refresh_seconds: int = 25) -> None:
    if not ws_url.startswith("wss://"):
        raise ValueError("WS RPC URL must start with wss://")
    try:
        from websockets.asyncio.client import connect
    except ImportError as exc:
        raise RuntimeError("Install websockets==15.0.1") from exc
    while True:
        try:
            async with connect(ws_url, max_size=3_000_000, ping_interval=20, ping_timeout=20, open_timeout=15) as ws:
                await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "logsSubscribe", "params": [{"mentions": [detector.platform]}, {"commitment": "confirmed"}]}))
                ack = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                if ack.get("error") or ack.get("id") != 1 or not isinstance(ack.get("result"), int):
                    raise RuntimeError("logsSubscribe rejected")
                print("SUBSCRIBED: exact config; notifications are candidates only", file=sys.stderr, flush=True)
                try:
                    await detector.backfill()
                    await detector.retry_pending()
                except Exception:
                    print("BACKFILL_FAILURE: checkpoint not advanced", file=sys.stderr, flush=True)
                while True:
                    try:
                        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=refresh_seconds))
                    except asyncio.TimeoutError:
                        try:
                            await detector.backfill()
                            await detector.retry_pending()
                        except Exception:
                            print("BACKFILL_FAILURE: checkpoint not advanced", file=sys.stderr, flush=True)
                        continue
                    if msg.get("method") != "logsNotification":
                        continue
                    value = (msg.get("params", {}).get("result") or {}).get("value") or {}
                    signature, err = value.get("signature"), value.get("err")
                    slot = (msg.get("params", {}).get("result") or {}).get("context", {}).get("slot")
                    if not signature or not isinstance(slot, int):
                        continue
                    if err is not None:
                        detector.journal.save(signature, slot, "IGNORED")
                    else:
                        await detector.process(signature, slot)
        except asyncio.CancelledError:
            raise
        except Exception:
            print("WS_DISCONNECTED: will reconnect; checkpoint kept for backfill", file=sys.stderr, flush=True)
            await asyncio.sleep(4)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Independent Machine.fun read-only first-launch candidate detector")
    parser.add_argument("--db", type=Path, default=Path.home() / ".local/state/machine-fun/launch-events.sqlite")
    sub = parser.add_subparsers(dest="command", required=True)
    replay = sub.add_parser("replay", help="Offline parse of one getTransaction JSON payload")
    replay.add_argument("transaction_json", type=Path)
    replay.add_argument("--signature", required=True)
    watcher = sub.add_parser("listen", help="Explicitly start manual live watcher; never installs a daemon")
    watcher.add_argument("--notify-local", action="store_true", help="Use macOS Notification Center via osascript")
    watcher.add_argument("--refresh-seconds", type=int, default=25)
    args = parser.parse_args(argv)
    if args.command == "replay":
        data = json.loads(args.transaction_json.read_text(encoding="utf-8"))
        tx = data.get("result", data)
        for launch in detect_launches(tx, args.signature):
            print(json.dumps(asdict(launch), ensure_ascii=False))
        return 0
    if args.refresh_seconds < 5:
        parser.error("refresh-seconds must be >=5")
    http_url = os.environ.get("MACHINE_FUN_HTTP_RPC", "")
    ws_url = os.environ.get("MACHINE_FUN_WS_RPC", "")
    if not http_url or not ws_url:
        parser.error("set MACHINE_FUN_HTTP_RPC and MACHINE_FUN_WS_RPC in local environment (never commit secrets)")
    journal = Journal(args.db)
    try:
        asyncio.run(listen(ws_url, Detector(Rpc(http_url), journal, local_notification=args.notify_local), args.refresh_seconds))
    except KeyboardInterrupt:
        return 0
    finally:
        journal.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
