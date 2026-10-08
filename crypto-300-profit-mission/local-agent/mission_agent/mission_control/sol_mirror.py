"""Persistent read-only-source mirror that normalizes SOL-quoted Frank trades.

The frozen Frank V1 engine is reused unchanged in a separate control-owned DB.
Production forward.sqlite is never modified.
"""
from __future__ import annotations

import hashlib
import json
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..market.sol_usd import (
    BinanceSolUsdcHistoryClient,
    SELECTION_RULE,
    SOL_QUOTE_ASSETS,
    SOURCE,
    normalize_classification,
    reference_epoch,
    reference_key,
)
from ..signals.engine import Engine
from ..signals.policy import load_policy
from ..signals.store import Ledger
from .db import open_production_ro, utc
from .frank import _event_price_usdc, _quote_display

FATAL_ACCESS_REASONS={"BINANCE_HTTP_403","BINANCE_HTTP_418","BINANCE_HTTP_451"}


def _stable_hash(value):
    stable={k:v for k,v in value.items() if k!="observed_at"}
    return hashlib.sha256(json.dumps(stable,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()


def _evidence_hash(value):
    stable={k:v for k,v in value.items() if k not in {"observed_at","evidence_sha256"}}
    return hashlib.sha256(json.dumps(stable,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()


def _valid_reference(value,block_time):
    if not isinstance(value,dict) or value.get("status")!="VERIFIED":return False
    if value.get("source")!=SOURCE or value.get("symbol")!="SOLUSDC" or value.get("interval")!="1m" or value.get("selection_rule")!=SELECTION_RULE:return False
    try:
        expected=reference_epoch(block_time)
        if int(value.get("reference_epoch"))!=expected:return False
        open_ms=int(value["candle_open_ms"]);close_ms=int(value["candle_close_ms"])
        op=Decimal(str(value["open"]));hi=Decimal(str(value["high"]));lo=Decimal(str(value["low"]));cl=Decimal(str(value["close"]));selected=Decimal(str(value["sol_usdc"]))
    except (KeyError,TypeError,ValueError,InvalidOperation):return False
    if open_ms!=expected*1000 or close_ms>=int(block_time)*1000 or not open_ms<=close_ms<=open_ms+59999:return False
    if min(op,hi,lo,cl,selected)<=0 or hi<lo or not lo<=op<=hi or not lo<=cl<=hi or cl!=selected:return False
    return value.get("evidence_sha256")==_evidence_hash(value)


class SolNormalizedMirror:
    def __init__(self,source_db:Path,sidecar_db:Path,policy_path:Path,*,client=None):
        self.source_db=Path(source_db);self.sidecar_db=Path(sidecar_db)
        self.ledger=Ledger(self.sidecar_db)
        self.db=self.ledger.db
        self.engine=Engine(self.ledger,load_policy(policy_path),dry_run=True)
        self.client=client or BinanceSolUsdcHistoryClient()
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS sol_mirror_meta(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS sol_usdc_references(
          reference_key TEXT PRIMARY KEY,source TEXT,status TEXT,reference_epoch INTEGER,
          content_hash TEXT,body TEXT,created_at TEXT
        );
        """)
    def close(self):
        self.db.close()
    def _meta(self,key,default=None):
        row=self.db.execute("SELECT value FROM sol_mirror_meta WHERE key=?",(key,)).fetchone()
        return row[0] if row else default
    def _set_meta(self,key,value):
        self.db.execute("INSERT OR REPLACE INTO sol_mirror_meta VALUES(?,?)",(key,str(value)))
    def _reference(self,block_time):
        key=reference_key(block_time)
        row=self.db.execute("SELECT content_hash,body FROM sol_usdc_references WHERE reference_key=?",(key,)).fetchone()
        if row:
            try:value=json.loads(row["body"] if hasattr(row,"keys") else row[1])
            except (TypeError,ValueError):value=None
            content_hash=row["content_hash"] if hasattr(row,"keys") else row[0]
            if value and content_hash==_stable_hash(value) and _valid_reference(value,block_time):return value
        value=self.client.reference(block_time)
        if _valid_reference(value,block_time):
            self.db.execute("INSERT OR REPLACE INTO sol_usdc_references VALUES(?,?,?,?,?,?,?)",(key,SOURCE,"VERIFIED",reference_epoch(block_time),_stable_hash(value),json.dumps(value,sort_keys=True),utc()))
        return value
    def _insert_signature(self,row,body):
        self.db.execute(
            """INSERT OR IGNORE INTO signatures(
              wallet,signature,person_id,slot,block_time,seen_at,classified_at,raw_hash,raw_reference,body,alert_state,alert_reason
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                row["wallet"],row["signature"],row["person_id"],row["slot"],row["block_time"],
                row["seen_at"],row["classified_at"],row["raw_hash"],row["raw_reference"],
                json.dumps(body,sort_keys=True),"NO","SOL_NORMALIZED_MIRROR_PENDING",
            )
        )
    def sync(self):
        source=open_production_ro(self.source_db)
        copied=sol_trades=sol_resolved=sol_unresolved=0;failures={};max_rowid=int(self._meta("last_source_rowid","0") or 0)
        try:
            initialized=self._meta("initialized","0")=="1"
            if initialized:
                rows=source.execute(
                    "SELECT rowid,wallet,signature,person_id,slot,block_time,seen_at,classified_at,raw_hash,raw_reference,body FROM signatures WHERE rowid>? AND person_id='frank' ORDER BY block_time,slot,signature",
                    (max_rowid,),
                ).fetchall()
            else:
                rows=source.execute(
                    "SELECT rowid,wallet,signature,person_id,slot,block_time,seen_at,classified_at,raw_hash,raw_reference,body FROM signatures WHERE person_id='frank' ORDER BY block_time,slot,signature"
                ).fetchall()
            latest_time=None
            last_source_time=int(self._meta("last_source_block_time","0") or 0)
            for row in rows:
                max_rowid=max(max_rowid,int(row["rowid"]))
                if initialized and row["block_time"] is not None and int(row["block_time"]) < last_source_time:
                    raise RuntimeError("SOURCE_CHRONOLOGY_REGRESSION")
                try:classified=json.loads(row["body"])
                except (TypeError,ValueError):
                    failures["SOURCE_BODY_INVALID"]=failures.get("SOURCE_BODY_INVALID",0)+1;continue
                trade=classified.get("trade") or {}
                body=classified
                if classified.get("classification")=="ACTIVE_TRADE" and trade.get("quote_asset") in SOL_QUOTE_ASSETS:
                    sol_trades+=1
                    if row["block_time"] is None:
                        sol_unresolved+=1;failures["BLOCK_TIME_MISSING"]=failures.get("BLOCK_TIME_MISSING",0)+1
                    elif trade.get("quote_decimals") is None or trade.get("quote_amount_raw") in {None,""}:
                        sol_unresolved+=1;failures["SOL_QUOTE_FIELDS_MISSING"]=failures.get("SOL_QUOTE_FIELDS_MISSING",0)+1
                    else:
                        ref=self._reference(int(row["block_time"]))
                        if ref.get("reason") in FATAL_ACCESS_REASONS:
                            sol_unresolved+=1;failures[ref["reason"]]=failures.get(ref["reason"],0)+1
                        elif ref.get("status")=="VERIFIED":
                            body=normalize_classification(classified,ref,for_model=False)
                            normalized_trade=body.get("trade") or {}
                            if (
                                normalized_trade.get("quote_usdc_status")=="SOL_EVENT_TIME_USDC_VERIFIED"
                                and normalized_trade.get("quote_asset") in SOL_QUOTE_ASSETS
                            ):
                                sol_resolved+=1
                            else:
                                sol_unresolved+=1
                                failures["SOL_QUOTE_PROVENANCE_INELIGIBLE"]=failures.get("SOL_QUOTE_PROVENANCE_INELIGIBLE",0)+1
                        else:
                            sol_unresolved+=1;reason=ref.get("reason") or "SOL_REFERENCE_UNAVAILABLE";failures[reason]=failures.get(reason,0)+1
                self._insert_signature(row,body);copied+=1
                if row["block_time"] is not None:latest_time=max(latest_time or int(row["block_time"]),int(row["block_time"]))
            if rows:
                self.engine.drain(until=latest_time)
                self._set_meta("last_source_rowid",max_rowid);self._set_meta("initialized","1")
                if latest_time is not None:self._set_meta("last_source_block_time",latest_time)
            source_signals={r[0] for r in source.execute("SELECT signal_id FROM signals WHERE person_id='frank'")}
            mirror_signals={r[0] for r in self.db.execute("SELECT signal_id FROM signals WHERE person_id='frank'")}
            added=sorted(mirror_signals-source_signals)
            return {"status":"OK","copied":copied,"sol_trades":sol_trades,"sol_resolved":sol_resolved,"sol_unresolved":sol_unresolved,"failures":failures,"added_signal_count":len(added),"added_signal_ids":added[:50],"sidecar":str(self.sidecar_db)}
        except Exception as exc:
            return {"status":"DEGRADED","error":type(exc).__name__,"message":str(exc)[:240],"copied":copied,"sol_trades":sol_trades,"sol_resolved":sol_resolved,"sol_unresolved":sol_unresolved,"failures":failures,"sidecar":str(self.sidecar_db)}
        finally:
            source.close()
    def candidates(self):
        rows=self.db.execute("SELECT person_id,mint,body FROM v1_states WHERE person_id='frank'").fetchall();result=[]
        for row in rows:
            try:state=json.loads(row["body"])
            except (TypeError,ValueError):continue
            signals=self.db.execute("SELECT signal_id,signal_type,created_at FROM signals WHERE person_id=? AND mint=? AND episode_id=? ORDER BY CAST(created_at AS INTEGER),rowid",(row["person_id"],row["mint"],state.get("episode_id"))).fetchall()
            if not signals:continue
            sig=signals[-1]
            if sig["signal_type"]=="FRANK_MULTIPLE_SIGNAL":pattern="MULTIPLE"
            elif sig["signal_type"]=="FRANK_ACCUMULATION_SIGNAL":pattern="ACCUMULATION"
            else:continue
            events=state.get("events") or [];latest=events[-1] if events else None;buys=[e for e in events if e.get("direction")=="BUY"];latest_buy=buys[-1] if buys else None
            price=_event_price_usdc(latest_buy) if latest_buy else None;qd=_quote_display(latest_buy)
            model_asset=latest_buy.get("quote_asset") if latest_buy else None;model_qty=latest_buy.get("quote_quantity") if latest_buy else None
            if price is not None:price_status="SOL_EVENT_TIME_USDC_VERIFIED" if latest_buy and latest_buy.get("quote_usdc_status")=="SOL_EVENT_TIME_USDC_VERIFIED" else "USDC_DIRECT"
            elif model_asset in SOL_QUOTE_ASSETS or qd["asset"] in SOL_QUOTE_ASSETS:price_status="SOL_EVENT_TIME_USDC_UNAVAILABLE"
            else:price_status="QUOTE_PRICE_UNAVAILABLE"
            result.append({
                "person_id":row["person_id"],"mint":row["mint"],"episode_id":state.get("episode_id"),"pattern":pattern,
                "source_signal_id":sig["signal_id"],"source_signal_type":sig["signal_type"],"source_signal_at":sig["created_at"],
                "position_state":state.get("state"),"current_raw":state.get("current_raw"),"buy_count":len(buys),"sell_count":sum(e.get("direction")=="SELL" for e in events),
                "latest_side":latest.get("direction") if latest else None,"latest_signature":latest.get("signature") if latest else None,"latest_at":latest.get("at") if latest else None,
                "latest_buy_at":latest_buy.get("at") if latest_buy else None,"latest_buy_price_usdc":str(price) if price is not None else None,"latest_buy_price_status":price_status,
                "latest_buy_quote_asset":qd["asset"],"latest_buy_quote_quantity":qd["quantity"],"latest_buy_original_quote_asset":qd["asset"],"latest_buy_original_quote_quantity":qd["quantity"],
                "latest_buy_quote_was_normalized":qd["normalized"],"latest_buy_usdc_equivalent":qd["usdc_equivalent"],"latest_buy_model_quote_asset":model_asset,"latest_buy_model_quote_quantity":model_qty,
                "token_decimals":int(latest_buy.get("token_decimals")) if latest_buy and latest_buy.get("token_decimals") is not None else None,
                "events":events,"candidate_source":"SOL_NORMALIZED_SIDECAR",
            })
        result.sort(key=lambda x:int(x.get("latest_at") or 0),reverse=True);return result


def merge_candidates(base,overlay):
    rank={"REENTRY_WATCH":0,"ACCUMULATION":1,"MULTIPLE":2}
    merged={(x["person_id"],x["mint"],x.get("episode_id")):x for x in base}
    for item in overlay:
        key=(item["person_id"],item["mint"],item.get("episode_id"));old=merged.get(key)
        if old is None or rank.get(item.get("pattern"),-1)>rank.get(old.get("pattern"),-1):
            merged[key]=item;continue
        if old and rank.get(item.get("pattern"),-1)==rank.get(old.get("pattern"),-1) and item.get("latest_buy_price_status")=="SOL_EVENT_TIME_USDC_VERIFIED":
            merged[key]=item
    return sorted(merged.values(),key=lambda x:int(x.get("latest_at") or 0),reverse=True)
