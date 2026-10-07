"""Read-only Frank production adapter for Mission Meme V1."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .db import open_production_ro

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
WSOL = "So11111111111111111111111111111111111111112"


def _pid_alive(pid: int | str | None) -> bool:
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (TypeError, ValueError, OverflowError):
        return False


def _token_quantity(event: dict) -> Decimal | None:
    try:
        return Decimal(event["token_amount_raw"]) / (Decimal(10) ** int(event["token_decimals"]))
    except (KeyError, InvalidOperation, ValueError, TypeError):
        return None


def _event_price_usdc(event: dict) -> Decimal | None:
    quantity = _token_quantity(event)
    if not quantity:
        return None
    try:
        amount_predicate=event.get("amount_predicate")
        direct_usdc=amount_predicate in (None,"USDC_DIRECT_NUMERIC")
        if event.get("quote_asset") == USDC and direct_usdc and not event.get("quote_normalization"):
            return Decimal(str(event["quote_quantity"])) / quantity
        if (
            event.get("amount_predicate")=="SOL_EVENT_TIME_USDC_VERIFIED"
            and event.get("quote_usdc_status")=="SOL_EVENT_TIME_USDC_VERIFIED"
            and event.get("quote_usdc_equivalent") is not None
        ):
            return Decimal(str(event["quote_usdc_equivalent"])) / quantity
    except (KeyError, InvalidOperation, ZeroDivisionError, TypeError):
        return None
    return None


def _quote_display(event: dict | None) -> dict:
    if not event:
        return {"asset": None, "quantity": None, "normalized": False, "usdc_equivalent": None}
    original = event.get("original_quote") or {}
    if event.get("quote_normalization") == "SOL_TO_USDC_SHADOW_EQUIVALENT" and original:
        return {
            "asset": original.get("quote_asset"),
            "quantity": original.get("quote_quantity"),
            "normalized": True,
            "usdc_equivalent": event.get("quote_usdc_equivalent"),
        }
    direct_usdc=event.get("amount_predicate") in (None,"USDC_DIRECT_NUMERIC")
    return {
        "asset": event.get("quote_asset"),
        "quantity": event.get("quote_quantity"),
        "normalized": False,
        "usdc_equivalent": (
            event.get("quote_usdc_equivalent")
            if event.get("quote_asset") != USDC
            else event.get("quote_quantity") if direct_usdc else None
        ),
    }


class FrankReader:
    def __init__(self, production_root: Path, person_id: str = "frank"):
        self.root = Path(production_root)
        self.person_id = str(person_id)
        self.database = self.root / "forward.sqlite"
        self.health_path = self.root / "health.json"

    def runtime(self, now: float | None = None) -> dict:
        now = time.time() if now is None else now
        if not self.health_path.is_file():
            return {"status": "UNKNOWN", "reason": "HEALTH_FILE_MISSING"}
        try:
            health = json.loads(self.health_path.read_text())
        except (OSError, ValueError):
            return {"status": "UNKNOWN", "reason": "HEALTH_FILE_UNREADABLE"}
        raw_status = health.get("status")
        pid = health.get("pid")
        alive = _pid_alive(pid)
        last = health.get("last_successful_poll")
        poll_interval = int(health.get("poll_interval_seconds") or 30)
        age = None
        if last:
            try:
                age = max(0.0, now - __import__("datetime").datetime.fromisoformat(last).timestamp())
            except (ValueError, TypeError):
                age = None
        db_ok = False
        try:
            db = open_production_ro(self.database)
            db.execute("SELECT 1").fetchone()
            db.close()
            db_ok = True
        except (OSError, ValueError, sqlite3.Error):
            db_ok = False
        if not alive:
            status, reason = "OFFLINE", "PID_NOT_ALIVE"
        elif age is None:
            status, reason = "UNKNOWN", "LAST_SUCCESSFUL_POLL_UNKNOWN"
        elif age > poll_interval * 3:
            status, reason = "OFFLINE", "HEARTBEAT_STALE"
        elif not db_ok:
            status, reason = "DEGRADED", "PRODUCTION_DB_UNREADABLE"
        elif health.get("source_drift"):
            status, reason = "DEGRADED", "SOURCE_DRIFT"
        elif raw_status != "RUNNING":
            status, reason = "DEGRADED", "SERVICE_" + str(raw_status or "UNKNOWN")
        elif int(health.get("consecutive_errors") or 0) > 0:
            status, reason = "DEGRADED", "CONSECUTIVE_ERRORS"
        else:
            status, reason = "LIVE", "OK"
        return {**health, "status": status, "runtime_reason": reason, "pid_alive": alive, "heartbeat_age_seconds": age, "production_db_readable": db_ok}

    def candidates(self) -> list[dict]:
        db = open_production_ro(self.database)
        try:
            rows = db.execute("SELECT person_id,mint,body FROM v1_states").fetchall()
            result = []
            for row in rows:
                try:
                    state = json.loads(row["body"])
                except (TypeError, ValueError):
                    continue
                events = state.get("events") or []
                latest = events[-1] if events else None
                buys = [e for e in events if e.get("direction") == "BUY"]

                signals = db.execute(
                    "SELECT signal_id,signal_type,created_at,body FROM signals WHERE person_id=? AND mint=? AND episode_id=? ORDER BY CAST(created_at AS INTEGER),rowid",
                    (row["person_id"], row["mint"], state.get("episode_id")),
                ).fetchall()

                source_signal_id = None
                source_signal_type = None
                source_signal_at = None
                if signals:
                    signal_row = signals[-1]
                    source_signal_id = signal_row["signal_id"]
                    source_signal_type = signal_row["signal_type"]
                    source_signal_at = signal_row["created_at"]
                    if source_signal_type == "FRANK_MULTIPLE_SIGNAL":
                        pattern = "MULTIPLE"
                    elif source_signal_type == "FRANK_ACCUMULATION_SIGNAL":
                        pattern = "ACCUMULATION"
                    else:
                        continue
                else:
                    # A confirmed re-entry is useful research evidence even before
                    # it qualifies for the frozen ACCUMULATION/MULTIPLE model.
                    # Do not invent an amount threshold here: this is WATCH only,
                    # never an actionable Frank signal by itself.
                    first = events[0] if events else None
                    if state.get("state") != "OPEN" or not first or first.get("direction") != "BUY":
                        continue
                    first_signature = first.get("signature")
                    if not first_signature:
                        continue
                    reentry = db.execute(
                        "SELECT side,block_time FROM trades WHERE signature=? AND mint=? ORDER BY rowid DESC LIMIT 1",
                        (first_signature, row["mint"]),
                    ).fetchone()
                    if not reentry or reentry["side"] != "REENTRY":
                        continue
                    pattern = "REENTRY_WATCH"
                    source_signal_type = "FRANK_REENTRY_WATCH"
                    source_signal_at = str(first.get("at") or reentry["block_time"] or "")
                latest_buy = buys[-1] if buys else None
                latest_buy_price = _event_price_usdc(latest_buy) if latest_buy else None
                quote_display = _quote_display(latest_buy)
                model_quote_asset = latest_buy.get("quote_asset") if latest_buy else None
                model_quote_quantity = latest_buy.get("quote_quantity") if latest_buy else None
                if latest_buy_price is not None:
                    price_status = "SOL_EVENT_TIME_USDC_VERIFIED" if latest_buy and latest_buy.get("quote_usdc_status") == "SOL_EVENT_TIME_USDC_VERIFIED" else "USDC_DIRECT"
                elif latest_buy and latest_buy.get("amount_predicate")=="UNDETERMINED" and model_quote_asset==USDC:
                    price_status = "COMPOSITE_QUOTE_PRICE_UNAVAILABLE"
                elif model_quote_asset in {"SOL", WSOL} or quote_display["asset"] in {"SOL", WSOL}:
                    price_status = "SOL_EVENT_TIME_USDC_UNAVAILABLE"
                else:
                    price_status = "QUOTE_PRICE_UNAVAILABLE"
                result.append({
                    "person_id": row["person_id"], "mint": row["mint"], "episode_id": state.get("episode_id"),
                    "pattern": pattern, "source_signal_id": source_signal_id, "source_signal_type": source_signal_type,
                    "source_signal_at": source_signal_at, "position_state": state.get("state"), "current_raw": state.get("current_raw"),
                    "buy_count": len(buys), "sell_count": sum(e.get("direction") == "SELL" for e in events),
                    "latest_side": latest.get("direction") if latest else None, "latest_signature": latest.get("signature") if latest else None,
                    "latest_at": latest.get("at") if latest else None, "latest_buy_at": latest_buy.get("at") if latest_buy else None,
                    "latest_buy_price_usdc": str(latest_buy_price) if latest_buy_price is not None else None,
                    "latest_buy_price_status": price_status,
                    # Public/legacy quote fields always describe what Frank actually paid.
                    "latest_buy_quote_asset": quote_display["asset"],
                    "latest_buy_quote_quantity": quote_display["quantity"],
                    "latest_buy_original_quote_asset": quote_display["asset"],
                    "latest_buy_original_quote_quantity": quote_display["quantity"],
                    "latest_buy_quote_was_normalized": quote_display["normalized"],
                    "latest_buy_usdc_equivalent": quote_display["usdc_equivalent"],
                    # Synthetic model fields are explicit so API consumers cannot confuse them with payment evidence.
                    "latest_buy_model_quote_asset": model_quote_asset,
                    "latest_buy_model_quote_quantity": model_quote_quantity,
                    "token_decimals": int(latest_buy.get("token_decimals")) if latest_buy and latest_buy.get("token_decimals") is not None else None,
                    "events": events,
                })
            result.sort(key=lambda x: int(x.get("latest_at") or 0), reverse=True)
            return result
        finally:
            db.close()

    def mint_snapshot(self, mint: str) -> dict:
        """Read Frank's exact-person observed state for one mint without creating a signal."""
        person_id=self.person_id
        db = open_production_ro(self.database)
        try:
            row = db.execute(
                "SELECT person_id,mint,body FROM v1_states WHERE person_id=? AND mint=? LIMIT 1",
                (person_id,mint),
            ).fetchone()
            if not row:
                return {"status":"NOT_OBSERVED","mint":mint}
            try:
                state=json.loads(row["body"])
            except (TypeError,ValueError):
                return {"status":"UNAVAILABLE","reason":"STATE_BODY_INVALID","mint":mint}
            events=state.get("events") or []
            latest=events[-1] if events else None
            buys=[event for event in events if event.get("direction")=="BUY"]
            sells=[event for event in events if event.get("direction")=="SELL"]
            signal=db.execute(
                "SELECT signal_type,created_at FROM signals WHERE person_id=? AND mint=? AND episode_id=? ORDER BY rowid DESC LIMIT 1",
                (row["person_id"],mint,state.get("episode_id")),
            ).fetchone()
            return {
                "status":"OBSERVED","person_id":row["person_id"],"mint":mint,
                "episode_id":state.get("episode_id"),"position_state":state.get("state"),
                "current_raw":state.get("current_raw"),"buy_count":len(buys),"sell_count":len(sells),
                "latest_side":latest.get("direction") if latest else None,
                "latest_at":latest.get("at") if latest else None,
                "latest_signature":latest.get("signature") if latest else None,
                "signal_type":signal["signal_type"] if signal else None,
                "signal_at":signal["created_at"] if signal else None,
            }
        finally:
            db.close()

    def review_activity(self, limit: int = 30) -> list[dict]:
        """Expose ambiguous active swap-like facts without promoting them to trades/signals."""
        db = open_production_ro(self.database)
        try:
            try:
                rows=db.execute(
                    """SELECT signature,block_time,body FROM signatures
                       WHERE json_extract(body,'$.classification')='UNKNOWN_NEEDS_REVIEW'
                         AND (
                           json_extract(body,'$.evidence.mechanical_classification')='ACTIVE_SWAP_LIKE'
                           OR (
                             json_extract(body,'$.frank_is_signer')=1
                             AND json_extract(body,'$.evidence.tx_err') IS NULL
                             AND json_extract(body,'$.evidence.classification_evidence.opposing_economic_flows')=1
                           )
                         )
                       ORDER BY block_time DESC LIMIT ?""",
                    (limit,),
                ).fetchall()
            except sqlite3.Error:
                return []
            result=[]
            for row in rows:
                try:body=json.loads(row["body"])
                except (TypeError,ValueError):continue
                evidence=body.get("evidence") or {}
                grouped={}
                for delta in evidence.get("token_balance_deltas") or []:
                    if not delta.get("wallet_owned"):continue
                    try:
                        raw=int(delta.get("delta") or 0);decimals=int(delta.get("decimals"))
                    except (TypeError,ValueError):continue
                    if not raw:continue
                    mint=delta.get("mint")
                    if not mint:continue
                    item=grouped.setdefault(mint,{"mint":mint,"delta_raw":0,"decimals":decimals})
                    if item["decimals"]!=decimals:continue
                    item["delta_raw"]+=raw
                for flow in evidence.get("decoded_transient_token_flows") or []:
                    try:
                        raw=int(flow.get("net_transfer_raw") or 0);decimals=int(flow.get("decimals"))
                    except (TypeError,ValueError):continue
                    mint=flow.get("mint")
                    if not mint or not raw:continue
                    item=grouped.setdefault(mint,{"mint":mint,"delta_raw":0,"decimals":decimals})
                    if item["decimals"]!=decimals:continue
                    item["delta_raw"]+=raw
                assets=[
                    {**item,"delta_raw":str(item["delta_raw"])}
                    for item in grouped.values() if item["delta_raw"]
                ]
                quote_mints={USDC,WSOL,"Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"}
                result.append({
                    "signature":row["signature"],"block_time":row["block_time"],
                    "classification_reason":body.get("classification_reason"),
                    "review_scope":(
                        "ACTIVE_SWAP_LIKE"
                        if evidence.get("mechanical_classification")=="ACTIVE_SWAP_LIKE"
                        else "SIGNED_OPPOSING_FLOW_MARKET_UNPROVEN"
                    ),
                    "candidate_mints":[x["mint"] for x in assets if x["mint"] not in quote_mints],
                    "assets":assets,
                    "program_ids":evidence.get("program_ids") or [],
                    "dex_program_interaction":bool((evidence.get("classification_evidence") or {}).get("dex_program_interaction")),
                    "swap_instruction_evidence":bool((evidence.get("classification_evidence") or {}).get("swap_instruction_evidence")),
                    "opposing_economic_flows":bool((evidence.get("classification_evidence") or {}).get("opposing_economic_flows")),
                })
            return result
        finally:
            db.close()

    def recent_trades(self, limit: int = 100) -> list[dict]:
        db = open_production_ro(self.database)
        try:
            rows = db.execute("SELECT wallet,signature,mint,episode_id,block_time,side,body FROM trades ORDER BY block_time DESC LIMIT ?", (limit,)).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["body"] = json.loads(item["body"])
                result.append(item)
            return result
        finally:
            db.close()
