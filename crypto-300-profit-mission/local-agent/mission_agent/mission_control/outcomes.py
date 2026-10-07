"""Forward outcome tracking for Mission Meme signals.

This module records what a user could actually receive from the same Jupiter
read-only quote path. It never substitutes Frank's fill for user entry and never
builds/signs/sends a transaction.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from ..hashing import digest
from .db import utc

TRACK_PATTERNS={"REENTRY_WATCH","ACCUMULATION","MULTIPLE"}
HORIZONS=(300,900,3600,21600,86400)
SAMPLE_SECONDS=300
HORIZON_GRACE_SECONDS=180
MAX_QUOTES_PER_CYCLE=2


def _decimal(value):
    if value is None:return None
    try:return Decimal(str(value))
    except (InvalidOperation,ValueError,TypeError):return None


class OutcomeTracker:
    def __init__(self,db,jupiter):
        self.db=db;self.jupiter=jupiter
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS outcome_tracks(
            tracking_id TEXT PRIMARY KEY,
            person_id TEXT NOT NULL,
            mint TEXT NOT NULL,
            episode_id TEXT,
            pattern TEXT NOT NULL,
            source_signal_id TEXT,
            source_signal_type TEXT,
            signal_at REAL,
            available_at REAL NOT NULL,
            initial_decision TEXT NOT NULL,
            entry_status TEXT NOT NULL,
            entry_input_usdc TEXT,
            entry_token_raw TEXT,
            token_decimals INTEGER,
            entry_execution_price_usdc TEXT,
            entry_price_impact_pct TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            body TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_outcome_tracks_available ON outcome_tracks(available_at,status);
        CREATE TABLE IF NOT EXISTS outcome_samples(
            sample_id TEXT PRIMARY KEY,
            tracking_id TEXT NOT NULL,
            sample_bucket INTEGER NOT NULL,
            sample_at REAL NOT NULL,
            age_seconds INTEGER NOT NULL,
            status TEXT NOT NULL,
            reason TEXT,
            out_usdc TEXT,
            execution_price_usdc TEXT,
            price_impact_pct TEXT,
            route_exists INTEGER,
            body TEXT NOT NULL,
            UNIQUE(tracking_id,sample_bucket),
            FOREIGN KEY(tracking_id) REFERENCES outcome_tracks(tracking_id)
        );
        CREATE INDEX IF NOT EXISTS idx_outcome_samples_track_time ON outcome_samples(tracking_id,sample_at);
        CREATE TABLE IF NOT EXISTS outcome_horizons(
            tracking_id TEXT NOT NULL,
            horizon_seconds INTEGER NOT NULL,
            status TEXT NOT NULL,
            sample_id TEXT,
            observed_at REAL,
            return_pct TEXT,
            reason TEXT,
            body TEXT NOT NULL,
            PRIMARY KEY(tracking_id,horizon_seconds),
            FOREIGN KEY(tracking_id) REFERENCES outcome_tracks(tracking_id)
        );
        """)
    @staticmethod
    def tracking_id(candidate):
        return digest({
            "person_id":candidate.get("person_id"),
            "mint":candidate.get("mint"),
            "episode_id":candidate.get("episode_id"),
            "pattern":candidate.get("pattern"),
            "source_signal_id":candidate.get("source_signal_id"),
            "source_signal_type":candidate.get("source_signal_type"),
        })
    def register(self,*,candidate,result,quote,now):
        pattern=candidate.get("pattern")
        if pattern not in TRACK_PATTERNS:return None
        tracking_id=self.tracking_id(candidate)
        existing=self.db.execute("SELECT tracking_id FROM outcome_tracks WHERE tracking_id=?",(tracking_id,)).fetchone()
        if existing:return None
        route_ok=quote.get("status")=="OK" and quote.get("route_exists") is True
        entry_raw=quote.get("out_amount_raw") if route_ok else None
        input_usdc=quote.get("input_usdc") if route_ok else None
        decimals=candidate.get("token_decimals")
        measured=entry_raw not in {None,""} and input_usdc not in {None,""} and decimals is not None
        entry_status="MEASURED" if measured else "UNAVAILABLE_AT_SIGNAL"
        signal_at=_decimal(candidate.get("source_signal_at") or candidate.get("latest_at"))
        body={
            "candidate":{k:candidate.get(k) for k in ("person_id","mint","episode_id","pattern","source_signal_id","source_signal_type","latest_at","latest_buy_at")},
            "initial_decision":result.get("decision"),
            "entry_quote":{k:quote.get(k) for k in ("status","reason","source","observed_at","input_usdc","out_amount_raw","token_out","execution_price_usdc","price_impact_pct","route_exists")},
            "sampling":{"sample_seconds":SAMPLE_SECONDS,"horizons_seconds":list(HORIZONS),"horizon_grace_seconds":HORIZON_GRACE_SECONDS},
        }
        self.db.execute(
            "INSERT INTO outcome_tracks VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                tracking_id,candidate.get("person_id"),candidate.get("mint"),candidate.get("episode_id"),pattern,
                candidate.get("source_signal_id"),candidate.get("source_signal_type"),
                None if signal_at is None else float(signal_at),float(now),result.get("decision") or "UNASSESSED",
                entry_status,str(input_usdc) if input_usdc is not None else None,str(entry_raw) if entry_raw is not None else None,
                int(decimals) if decimals is not None else None,
                str(quote.get("execution_price_usdc")) if quote.get("execution_price_usdc") is not None else None,
                str(quote.get("price_impact_pct")) if quote.get("price_impact_pct") is not None else None,
                "ACTIVE" if measured else "NO_ENTRY_QUOTE",utc(),json.dumps(body,sort_keys=True)
            )
        )
        return tracking_id
    def _record_horizon(self,track,horizon,sample=None,*,status,reason=None):
        if self.db.execute("SELECT 1 FROM outcome_horizons WHERE tracking_id=? AND horizon_seconds=?",(track["tracking_id"],horizon)).fetchone():return
        return_pct=None;sample_id=None;observed_at=None
        if sample:
            sample_id=sample["sample_id"];observed_at=sample["sample_at"]
            out=_decimal(sample.get("out_usdc"));entry=_decimal(track.get("entry_input_usdc"))
            if status=="MEASURED" and out is not None and entry and entry>0:return_pct=str((out/entry-Decimal(1))*Decimal(100))
        body={"tracking_id":track["tracking_id"],"horizon_seconds":horizon,"status":status,"sample_id":sample_id,"observed_at":observed_at,"return_pct":return_pct,"reason":reason}
        self.db.execute("INSERT OR IGNORE INTO outcome_horizons VALUES(?,?,?,?,?,?,?,?)",(track["tracking_id"],horizon,status,sample_id,observed_at,return_pct,reason,json.dumps(body,sort_keys=True)))
    def _mark_missed(self,now):
        rows=[dict(r) for r in self.db.execute("SELECT * FROM outcome_tracks WHERE status IN ('ACTIVE','NO_ENTRY_QUOTE')")]
        for track in rows:
            age=float(now)-float(track["available_at"])
            for h in HORIZONS:
                if self.db.execute("SELECT 1 FROM outcome_horizons WHERE tracking_id=? AND horizon_seconds=?",(track["tracking_id"],h)).fetchone():
                    continue
                sample=self.db.execute(
                    """SELECT * FROM outcome_samples
                       WHERE tracking_id=? AND age_seconds>=? AND age_seconds<=?
                       ORDER BY age_seconds,sample_at LIMIT 1""",
                    (track["tracking_id"],h,h+HORIZON_GRACE_SECONDS),
                ).fetchone()
                if sample:
                    sample=dict(sample)
                    self._record_horizon(track,h,sample,status=sample["status"],reason=sample.get("reason"))
                    continue
                if age<=h+HORIZON_GRACE_SECONDS:continue
                if track["entry_status"]!="MEASURED":
                    self._record_horizon(track,h,status="UNAVAILABLE",reason="ENTRY_QUOTE_UNAVAILABLE_AT_SIGNAL")
                else:self._record_horizon(track,h,status="MISSED_WINDOW",reason="NO_SAMPLE_WITHIN_HORIZON_GRACE")
            complete=self.db.execute("SELECT count(*) FROM outcome_horizons WHERE tracking_id=?",(track["tracking_id"],)).fetchone()[0]==len(HORIZONS)
            if complete and age>max(HORIZONS)+HORIZON_GRACE_SECONDS:
                gaps=self.db.execute("SELECT count(*) FROM outcome_horizons WHERE tracking_id=? AND status!='MEASURED'",(track["tracking_id"],)).fetchone()[0]
                self.db.execute("UPDATE outcome_tracks SET status=? WHERE tracking_id=?",("COMPLETE" if not gaps else "COMPLETE_WITH_GAPS",track["tracking_id"]))
    def sample_due(self,*,now=None,slippage_bps=100,max_quotes=MAX_QUOTES_PER_CYCLE):
        now=time.time() if now is None else float(now);self._mark_missed(now)
        rows=[dict(r) for r in self.db.execute("SELECT * FROM outcome_tracks WHERE status='ACTIVE' ORDER BY available_at")]
        sampled=0;errors=[]
        for track in rows:
            if sampled>=int(max_quotes):break
            age=max(0,int(now-float(track["available_at"])))
            if age<SAMPLE_SECONDS or age>max(HORIZONS)+HORIZON_GRACE_SECONDS:continue
            bucket=age//SAMPLE_SECONDS
            if self.db.execute("SELECT 1 FROM outcome_samples WHERE tracking_id=? AND sample_bucket=?",(track["tracking_id"],bucket)).fetchone():continue
            try:
                quote=self.jupiter.quote_token_to_usdc(
                    track["mint"],track["entry_token_raw"],int(track["token_decimals"]),slippage_bps=int(slippage_bps)
                )
                sample_at=float(quote.get("observed_at") or time.time());age_seconds=max(0,int(sample_at-float(track["available_at"])))
                status="MEASURED" if quote.get("status")=="OK" and quote.get("route_exists") is True and quote.get("out_usdc") is not None else "UNAVAILABLE"
                reason=quote.get("reason")
                body={"tracking_id":track["tracking_id"],"quote":quote,"available_at":track["available_at"],"age_seconds":age_seconds}
                sample_id=digest({"tracking_id":track["tracking_id"],"sample_bucket":bucket})
                self.db.execute(
                    "INSERT OR IGNORE INTO outcome_samples VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        sample_id,track["tracking_id"],bucket,sample_at,age_seconds,status,reason,
                        str(quote.get("out_usdc")) if quote.get("out_usdc") is not None else None,
                        str(quote.get("execution_price_usdc")) if quote.get("execution_price_usdc") is not None else None,
                        str(quote.get("price_impact_pct")) if quote.get("price_impact_pct") is not None else None,
                        None if quote.get("route_exists") is None else int(bool(quote.get("route_exists"))),
                        json.dumps(body,sort_keys=True)
                    )
                )
                sample=dict(self.db.execute("SELECT * FROM outcome_samples WHERE sample_id=?",(sample_id,)).fetchone())
                for h in HORIZONS:
                    if self.db.execute("SELECT 1 FROM outcome_horizons WHERE tracking_id=? AND horizon_seconds=?",(track["tracking_id"],h)).fetchone():continue
                    if h<=age_seconds<=h+HORIZON_GRACE_SECONDS:
                        self._record_horizon(track,h,sample,status=status,reason=reason)
                sampled+=1
            except Exception as exc:
                errors.append({"tracking_id":track["tracking_id"],"mint":track["mint"],"error":type(exc).__name__})
        self._mark_missed(now)
        return {"sampled":sampled,"errors":errors,"active":self.db.execute("SELECT count(*) FROM outcome_tracks WHERE status='ACTIVE'").fetchone()[0]}


def report(db,*,since_epoch=None,until_epoch=None):
    clauses=[];params=[]
    if since_epoch is not None:clauses.append("available_at>=?");params.append(float(since_epoch))
    if until_epoch is not None:clauses.append("available_at<?");params.append(float(until_epoch))
    where=(" WHERE "+" AND ".join(clauses)) if clauses else ""
    tracks=[dict(r) for r in db.execute("SELECT * FROM outcome_tracks"+where+" ORDER BY available_at",params)]
    by_id={x["tracking_id"]:x for x in tracks}
    horizons=[dict(r) for r in db.execute("SELECT * FROM outcome_horizons ORDER BY horizon_seconds")]
    horizons=[x for x in horizons if x["tracking_id"] in by_id]
    samples=[dict(r) for r in db.execute("SELECT * FROM outcome_samples ORDER BY sample_at")]
    samples=[x for x in samples if x["tracking_id"] in by_id]
    summary={"track_count":len(tracks),"entry_measured":sum(x["entry_status"]=="MEASURED" for x in tracks),"by_pattern":{},"by_decision":{},"horizons":{}}
    for x in tracks:
        summary["by_pattern"][x["pattern"]]=summary["by_pattern"].get(x["pattern"],0)+1
        summary["by_decision"][x["initial_decision"]]=summary["by_decision"].get(x["initial_decision"],0)+1
    def stats(values):
        values=sorted(x for x in values if x is not None)
        if not values:return {"measured":0,"win_rate_pct":None,"median_return_pct":None,"mean_return_pct":None,"profit_factor":None}
        gains=sum((x for x in values if x>0),Decimal(0));losses=-sum((x for x in values if x<0),Decimal(0))
        profit_factor="INF" if gains>0 and losses==0 else None if losses==0 else str(gains/losses)
        mid=len(values)//2
        median=values[mid] if len(values)%2 else (values[mid-1]+values[mid])/Decimal(2)
        return {
            "measured":len(values),
            "win_rate_pct":str(Decimal(sum(x>0 for x in values))*100/Decimal(len(values))),
            "median_return_pct":str(median),
            "mean_return_pct":str(sum(values,Decimal(0))/Decimal(len(values))),
            "profit_factor":profit_factor,
        }
    grouped={"by_pattern":{},"by_decision":{}}
    for h in HORIZONS:
        rows=[x for x in horizons if x["horizon_seconds"]==h]
        values=[_decimal(x["return_pct"]) for x in rows if x["status"]=="MEASURED"]
        summary["horizons"][str(h)]={**stats(values),"total":len(rows)}
        for group_name,field in (("by_pattern","pattern"),("by_decision","initial_decision")):
            keys=sorted({by_id[x["tracking_id"]][field] for x in rows if x["tracking_id"] in by_id})
            grouped[group_name].setdefault(str(h),{})
            for key in keys:
                vals=[_decimal(x["return_pct"]) for x in rows if x["status"]=="MEASURED" and by_id[x["tracking_id"]][field]==key]
                grouped[group_name][str(h)][key]=stats(vals)
    summary["performance_groups"]=grouped
    h24=[x for x in horizons if x["horizon_seconds"]==86400 and x["status"]=="MEASURED" and _decimal(x["return_pct"]) is not None]
    by_mint=defaultdict(list)
    for row in h24:by_mint[by_id[row["tracking_id"]]["mint"]].append(_decimal(row["return_pct"]))
    ranked=sorted(by_mint,key=lambda mint:sum(by_mint[mint],Decimal(0)),reverse=True)
    def without(excluded):
        return [_decimal(x["return_pct"]) for x in h24 if by_id[x["tracking_id"]]["mint"] not in excluded]
    summary["robustness_24h"]={
        "all":stats(without(set())),
        "top_positive_mints":ranked[:3],
        "ex_top1":stats(without(set(ranked[:1]))),
        "ex_top3":stats(without(set(ranked[:3]))),
    }
    paths=defaultdict(list)
    for s in samples:
        if s["status"]=="MEASURED" and s.get("out_usdc") is not None:paths[s["tracking_id"]].append(s)
    path_stats={}
    for tid,rows in paths.items():
        entry=_decimal(by_id[tid]["entry_input_usdc"])
        vals=[_decimal(x["out_usdc"]) for x in rows];vals=[x for x in vals if x is not None]
        if not entry or not vals:continue
        returns=[(x/entry-1)*100 for x in vals]
        peak=entry;max_dd=Decimal(0)
        for value in vals:
            peak=max(peak,value);max_dd=min(max_dd,(value/peak-1)*100)
        path_stats[tid]={"mfe_5m_sampled_pct":str(max(returns)),"mae_5m_sampled_pct":str(min(returns)),"max_drawdown_5m_sampled_pct":str(max_dd),"samples":len(vals)}
    return {"schema_version":1,"generated_at":utc(),"summary":summary,"tracks":tracks,"horizons":horizons,"path_stats":path_stats,"methodology":{"entry":"JUPITER_USDC_TO_TOKEN_30USD_EXECUTABLE_QUOTE","exit":"JUPITER_SAME_TOKEN_RAW_TO_USDC_EXECUTABLE_QUOTE","path_sampling_seconds":SAMPLE_SECONDS,"horizon_grace_seconds":HORIZON_GRACE_SECONDS,"mfe_mae":"5-minute sampled, not tick-perfect"}}
