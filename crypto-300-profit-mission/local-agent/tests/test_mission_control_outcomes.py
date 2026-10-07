import json
import sqlite3

from mission_agent.mission_control.outcomes import OutcomeTracker, report


class Jup:
    def __init__(self):
        self.calls=[]
    def quote_token_to_usdc(self,mint,raw,decimals,slippage_bps=100):
        self.calls.append((mint,raw,decimals,slippage_bps))
        return {"status":"OK","source":"JUPITER_OFFICIAL","observed_at":600.0,"route_exists":True,"out_usdc":"36","execution_price_usdc":"1.2","price_impact_pct":"0.4"}


def db():
    x=sqlite3.connect(":memory:");x.row_factory=sqlite3.Row;return x


def candidate(pattern="MULTIPLE"):
    return {"person_id":"frank","mint":"M","episode_id":"E","pattern":pattern,"source_signal_id":"S","source_signal_type":"FRANK_MULTIPLE_SIGNAL","source_signal_at":100,"latest_at":100,"token_decimals":6}


def result(decision="BUY"):
    return {"decision":decision,"metrics":{}}


def entry_quote():
    return {"status":"OK","source":"JUPITER_OFFICIAL","observed_at":100.0,"route_exists":True,"input_usdc":"30","out_amount_raw":"30000000","token_out":"30","execution_price_usdc":"1","price_impact_pct":"0.2"}


def test_register_is_stable_and_does_not_duplicate():
    x=db();t=OutcomeTracker(x,Jup())
    first=t.register(candidate=candidate(),result=result(),quote=entry_quote(),now=100)
    second=t.register(candidate=candidate(),result=result(),quote=entry_quote(),now=101)
    assert first and second is None
    assert x.execute("select count(*) from outcome_tracks").fetchone()[0]==1


def test_five_minute_forward_sample_uses_exact_entry_raw_and_records_return():
    x=db();j=Jup();t=OutcomeTracker(x,j)
    tid=t.register(candidate=candidate(),result=result(),quote=entry_quote(),now=100)
    out=t.sample_due(now=400,slippage_bps=100,max_quotes=2)
    assert out["sampled"]==1
    assert j.calls==[("M","30000000",6,100)]
    row=x.execute("select * from outcome_horizons where tracking_id=? and horizon_seconds=300",(tid,)).fetchone()
    assert row["status"]=="MEASURED"
    assert row["return_pct"]=="20.0"


def test_late_sample_never_backfills_missed_horizon():
    x=db();t=OutcomeTracker(x,Jup())
    tid=t.register(candidate=candidate(),result=result(),quote=entry_quote(),now=100)
    t.sample_due(now=700,max_quotes=0)
    row=x.execute("select * from outcome_horizons where tracking_id=? and horizon_seconds=300",(tid,)).fetchone()
    assert row["status"]=="MISSED_WINDOW"


def test_no_entry_quote_stays_unavailable_instead_of_inventing_entry():
    x=db();t=OutcomeTracker(x,Jup())
    q={"status":"UNAVAILABLE","reason":"JUPITER_RATE_LIMITED","observed_at":100.0,"source":"JUPITER_OFFICIAL"}
    tid=t.register(candidate=candidate("ACCUMULATION"),result=result("WAIT"),quote=q,now=100)
    t.sample_due(now=700,max_quotes=2)
    row=x.execute("select * from outcome_horizons where tracking_id=? and horizon_seconds=300",(tid,)).fetchone()
    assert row["status"]=="UNAVAILABLE"
    assert row["reason"]=="ENTRY_QUOTE_UNAVAILABLE_AT_SIGNAL"


def test_report_separates_coverage_and_performance():
    x=db();j=Jup();t=OutcomeTracker(x,j)
    t.register(candidate=candidate(),result=result(),quote=entry_quote(),now=100)
    t.sample_due(now=400,max_quotes=2)
    data=report(x)
    assert data["summary"]["track_count"]==1
    assert data["summary"]["entry_measured"]==1
    assert data["summary"]["horizons"]["300"]["measured"]==1
