"""Isolated deterministic Monster D0/D1 shadow and backlog regression suite."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/monster_v4_shadow.py"
spec=importlib.util.spec_from_file_location("monster_v4_shadow",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
BASE=1_800_000_000_000

def row(sym,price,quote="200000"):
    return {"symbol":sym,"lastPrice":str(price),"quoteVolume":str(quote)}

def six_bars(now, rising=True):
    start=(now//m.INTERVAL_MS-6)*m.INTERVAL_MS
    bars=[]
    for i in range(6):
        price=1+i*.02 if rising else 1-i*.02
        bars.append([start+i*m.INTERVAL_MS,str(price),"1.2","0.8",
                     str(price),"100",start+(i+1)*m.INTERVAL_MS-1,
                     "200" if i>=3 else "100",50])
    return bars

class MonsterShadowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"monster.sqlite"
        self.db=m.open_store(self.path)
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
    def observe_two(self,sym="AAAUSDT"):
        self.assertEqual(m.observe_snapshot(self.db,"spot",BASE,[row(sym,1)])["watch_new"],0)
        return m.observe_snapshot(self.db,"spot",BASE+180_000,[row(sym,1.08)])
    def count(self,table):
        return self.db.execute("SELECT COUNT(*) FROM "+table).fetchone()[0]

    def test_watch_is_early_persisted_and_deduped(self):
        r=self.observe_two()
        self.assertEqual(r["watch_new"],1)
        self.assertEqual(self.count("candidate_queue"),1)
        self.assertEqual(self.count("events"),1)
        self.assertEqual(self.count("outbox"),1)
        m.observe_snapshot(self.db,"spot",BASE+360_000,[row("AAAUSDT",1.16)])
        self.assertEqual(self.count("events"),1)
        self.assertEqual(self.count("candidate_queue"),1)
        self.assertEqual(m.health(self.db,BASE+360_000)["mail_sent"],0)

    def test_restart_preserves_unfinished_watch_and_no_duplicate(self):
        self.observe_two()
        self.db.close()
        self.db=m.open_store(self.path)
        m.observe_snapshot(self.db,"spot",BASE+360_000,[row("AAAUSDT",1.17)])
        self.assertEqual(self.count("candidate_queue"),1)
        self.assertEqual(self.count("events"),1)

    def test_nonmonotonic_poll_rejected_without_mutation(self):
        self.observe_two()
        before=self.count("polls")
        with self.assertRaisesRegex(ValueError,"NON_MONOTONIC"):
            m.observe_snapshot(self.db,"spot",BASE+180_000,[row("AAAUSDT",4)])
        self.assertEqual(self.count("polls"),before)
        price=self.db.execute("SELECT price FROM snapshots").fetchone()[0]
        self.assertEqual(price,"1.08")

    def test_no_fake_momentum_from_bootstrap_or_stale_gap(self):
        self.assertEqual(m.observe_snapshot(self.db,"spot",BASE,
            [row("AAUSDT",3)])["watch_new"],0)
        self.assertEqual(m.observe_snapshot(self.db,"spot",BASE+30*60_000,
            [row("AAUSDT",30)])["watch_new"],0)
        self.assertEqual(self.count("outbox"),0)

    def test_bad_snapshot_and_other_venue_are_isolated(self):
        m.observe_snapshot(self.db,"spot",BASE,[row("AUSDT",1),
            row("BADUSDT","nan"),row("ZEROUSDT",1,"0")])
        r=m.observe_snapshot(self.db,"spot",BASE+180_000,
            [row("AUSDT",1.1),row("BADUSDT",-2)])
        self.assertEqual(r["invalid"],1)
        self.assertEqual(self.count("events"),1)
        self.assertEqual(m.observe_snapshot(self.db,"futures",BASE+180_000,
            [row("AUSDT",8)])["watch_new"],0)
        self.assertEqual(self.count("events"),1)

    def test_oldest_backlog_first_and_failure_retry_persist(self):
        self.observe_two("OLDUSDT")
        m.observe_snapshot(self.db,"spot",BASE+360_000,
            [row("OLDUSDT",1.08),row("NEWUSDT",1)])
        m.observe_snapshot(self.db,"spot",BASE+540_000,
            [row("OLDUSDT",1.08),row("NEWUSDT",1.11)])
        seen=[]
        def failing(venue,sym,now):
            seen.append(sym)
            raise OSError("network offline")
        result=m.process_queue(self.db,BASE+550_000,failing,limit=1)
        self.assertEqual(seen,["OLDUSDT"])
        self.assertEqual(result["deferred"],1)
        self.assertEqual(self.count("candidate_queue"),2)
        result=m.process_queue(self.db,BASE+610_000,
            lambda v,s,t:six_bars(t),limit=1)
        self.assertEqual(result["completed"],1)
        self.assertEqual(self.db.execute(
            "SELECT symbol FROM candidate_queue WHERE status='EVALUATED'").fetchone()[0],
            "NEWUSDT")
        result=m.process_queue(self.db,BASE+700_000,
            lambda v,s,t:six_bars(t),limit=8)
        self.assertEqual(result["completed"],1)
        self.assertEqual(self.count("candidate_queue"),2)
        self.assertEqual(m.health(self.db,BASE+700_000)["source_failures"],1)

    def test_setup_only_after_closed_real_candles(self):
        self.observe_two()
        now=BASE+600_000
        result=m.process_queue(self.db,now,lambda v,s,t:six_bars(now))
        self.assertEqual(result["completed"],1)
        self.assertEqual(self.db.execute(
            "SELECT status FROM candidate_queue").fetchone()[0],"EVALUATED")
        kinds=set(x["event_type"] for x in self.db.execute("SELECT event_type FROM events"))
        self.assertEqual(kinds,{"WATCH_EARLY","SETUP_ACTIVE"})

    def test_open_or_gapped_bars_cannot_claim_setup(self):
        now=BASE+600_000
        candles=six_bars(now)
        candles[-1][6]=now+300_000
        with self.assertRaisesRegex(ValueError,"GAPPED_OR_OPEN"):
            m.evaluate_closed_5m(candles,now)
        candles=six_bars(now)
        candles[4][0]+=60_000
        with self.assertRaisesRegex(ValueError,"GAPPED_OR_OPEN"):
            m.evaluate_closed_5m(candles,now)

    def test_late_queue_records_missed_deep_review_not_live_buy(self):
        self.observe_two()
        result=m.process_queue(self.db,BASE+180_000+16*60_000,
            lambda *args: self.fail("expired record fetched"))
        self.assertEqual(result["late"],1)
        self.assertEqual(self.db.execute(
            "SELECT status FROM candidate_queue").fetchone()[0],"LATE")
        self.assertEqual(m.health(self.db,BASE+2_000_000)["events"]["LATE_REVIEW"],1)

    def test_provider_failure_visible_and_other_venue_continues(self):
        m.observe_snapshot(self.db,"futures",BASE,[row("SAFEUSDT",1)])
        def market(v):
            if v=="spot":
                raise OSError("timeout")
            return [row("SAFEUSDT",1.1)],1
        with patch.object(m,"fetch_market",side_effect=market),patch.object(
            m,"fetch_5m",return_value=six_bars(BASE+180_000)):
            reports=m.scan_once(self.db,BASE+180_000)
        self.assertEqual(reports[0]["error"],"OSError")
        self.assertEqual(reports[1]["watch_new"],1)
        self.assertEqual(m.health(self.db,BASE+180_000)["source_failures"],1)

    def test_pre_watch_candles_never_upgrade_to_setup(self):
        self.observe_two()
        at=BASE+200_000
        r=m.process_queue(self.db,at,lambda v,s,t:six_bars(t))
        self.assertEqual(r["deferred"],1)
        self.assertEqual(self.count("events"),1)
        self.assertEqual(self.db.execute(
            "SELECT status FROM candidate_queue").fetchone()[0],"PENDING")
        at=BASE+600_000
        r=m.process_queue(self.db,at,lambda v,s,t:six_bars(t))
        self.assertEqual(r["completed"],1)
        self.assertEqual(self.count("events"),2)

    def test_zero_quote_is_observed_but_not_tradeable_signal(self):
        m.observe_snapshot(self.db,"spot",BASE,[row("IDLEUSDT",1,"0")])
        rec=m.observe_snapshot(self.db,"spot",BASE+180_000,
            [row("IDLEUSDT",10,"0")])
        self.assertEqual(rec["invalid"],0)
        self.assertEqual(rec["watch_new"],0)

    def test_invalidated_watch_is_single_event_and_rearm_is_recorded(self):
        self.observe_two()
        m.observe_snapshot(self.db,"spot",BASE+360_000,[row("AAAUSDT",.85)])
        self.assertEqual(m.health(self.db,BASE+360_000)["events"]["INVALIDATED"],1)
        m.observe_snapshot(self.db,"spot",BASE+540_000,[row("AAAUSDT",.81)])
        self.assertEqual(m.health(self.db,BASE+540_000)["events"]["INVALIDATED"],1)
        res=m.observe_snapshot(self.db,"spot",BASE+720_000,
            [row("AAAUSDT",.96)])
        self.assertEqual(res["watch_new"],1)
        self.assertEqual(m.health(self.db,BASE+720_000)["events"]["WATCH_EARLY"],2)

    def test_source_outage_and_recovery_only_emit_transitions(self):
        m.mark_source_health(self.db,"spot",BASE,"HTTPError:429")
        m.mark_source_health(self.db,"spot",BASE+30_000,"HTTPError:429")
        self.assertEqual(m.health(self.db,BASE+30_000)["events"]["SOURCE_DEGRADED"],1)
        self.assertEqual(m.health(self.db,BASE+30_000)["degraded_venues"],["spot"])
        m.mark_source_health(self.db,"spot",BASE+180_000)
        m.mark_source_health(self.db,"spot",BASE+360_000)
        h=m.health(self.db,BASE+360_000)
        self.assertEqual(h["events"]["SOURCE_RECOVERED"],1)
        self.assertEqual(h["degraded_venues"],[])
        self.assertEqual(h["source_failures"],2)
        self.assertEqual(h["mail_sent"],0)

    def test_duplicate_symbol_does_not_create_two_events(self):
        m.observe_snapshot(self.db,"spot",BASE,[row("DUSDT",1)])
        r=m.observe_snapshot(self.db,"spot",BASE+180_000,
             [row("DUSDT",1.1),row("DUSDT",1.2)])
        self.assertEqual(r["invalid"],1)
        self.assertEqual(self.count("events"),1)

if __name__=="__main__":
    unittest.main()
