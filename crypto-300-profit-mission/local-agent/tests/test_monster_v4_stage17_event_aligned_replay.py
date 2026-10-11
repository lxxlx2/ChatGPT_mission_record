"""Frozen retrospective event-aligned V4 1m reproducibility and no-lookahead tests."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

FILE=Path(__file__).parents[1]/"scripts"/"monster_v4_stage17_event_aligned_replay.py"

def load():
    root=Path(tempfile.gettempdir())/"monster-stage17-unit"
    root.mkdir(exist_ok=True)
    t=[{"date":"2025-11-17","symbol":"TNSRUSDT","base_open":"1",
        "first_hourly_high_2x_index":55}]
    t += [{"date":"2026-05-17","symbol":f"SY{i}USDT","base_open":"1",
           "first_hourly_high_2x_index":55} for i in range(19)]
    (root/"monster_stage16_actual_frozen_7d_outcome_labels_20261011.json").write_text(
        json.dumps({"schema":"MONSTER_STAGE16_FROZEN_7D_2X5X10X_OFFICIAL_1H_ACTUAL_CI_V1",
            "totals":{"gross_high_2x":20},
            "gross_high_2x_event_register":t,
            "only_5x":{"date":"2025-11-17","symbol":"TNSRUSDT",
                      "baseline_open":"1","first_high_5x_hour_index":78}}))
    archive=types.ModuleType("monster_v4_archive_universe_replay")
    archive.source=types.SimpleNamespace(EVIDENCE=root)
    archive.get_day=lambda *a,**k:None
    replay=types.ModuleType("monster_v4_historical_replay")
    replay.parse_ms=lambda s:int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)
    replay.utc=lambda t:datetime.fromtimestamp(t/1000,timezone.utc).isoformat().replace("+00:00","Z")
    replay.replay_case=lambda *a,**k:None
    sys.modules[archive.__name__]=archive
    sys.modules[replay.__name__]=replay
    spec=importlib.util.spec_from_file_location("stage17_testable",FILE)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def make_download(anchor,threshold):
    crossing=int(anchor.timestamp()*1000)+10*60000
    def download(symbol,day):
        day_zero=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
        data=[]
        for i in range(1440):
            tick=day_zero+i*60000
            high=threshold+1 if tick==crossing else 1
            data.append((tick,1,high,1,1,1000,50))
        return data,{"sha256":"a"*64}
    return download

class EventAlignedTests(unittest.TestCase):
    def test_frozen_twenty_plus_one(self):
        m=load()
        frozen=m.frozen_events()
        self.assertEqual(len(frozen),21)
        self.assertEqual(sum(x["threshold"]==5 for x in frozen),1)

    def test_earliest_verified_1m_high_vs_first_watch(self):
        m=load()
        event=m.frozen_events()[0]
        d=date.fromisoformat(event["date"])
        anchor=datetime(d.year,d.month,d.day,6,tzinfo=timezone.utc)+timedelta(hours=55)
        def score(context,bars,include_zero_trade_ticks):
            self.assertEqual(len(bars),3600)
            return {"symbol":context["symbol"],
                "first_watch_utc":(anchor-timedelta(minutes=10)).isoformat(),
                "watch_count":1,"d1_setups":1,"trade_proxies":[]}
        r=m.replay_event(event,downloader=make_download(anchor,2),scorer=score)
        self.assertEqual(r["status"],"COMPLETE_CAUSAL_1M_REPLAY")
        self.assertEqual(r["lead_minutes_if_watch"],20)
        self.assertEqual(r["classification"],"WATCH_BEFORE_OR_AT_FIRST_1M_CROSS")

    def test_no_minute_cross_must_censor_hourly_disagreement(self):
        m=load()
        e=m.frozen_events()[0]
        d=date.fromisoformat(e["date"])
        anchor=datetime(d.year,d.month,d.day,6,tzinfo=timezone.utc)+timedelta(hours=55)
        r=m.replay_event(e,downloader=make_download(anchor,10),
                scorer=lambda *a,**k:{"symbol":"TNSRUSDT"})
        self.assertEqual(r["status"],"CENSORED_OR_SOURCE_FAILED")
        self.assertIn("DISAGREE",r["reason"])

    def test_nonfrozen_event_rejected(self):
        m=load()
        with self.assertRaisesRegex(ValueError,"NONFROZEN_EVENT"):
            m.run(events=[{"date":"2025-12-01","symbol":"FAKEUSDT","threshold":5}],
                 worker=lambda e:e)

    def test_all_preregistered_and_no_trading_when_valid(self):
        m=load()
        def worker(e):
            return {"date":e["date"],"symbol":e["symbol"],"threshold":e["threshold"],
                    "status":"COMPLETE_CAUSAL_1M_REPLAY",
                    "classification":"NO_WATCH_IN_EVENT_ALIGNED_12H"}
        r=m.run(worker=worker,max_workers=2)
        self.assertEqual(r["summary"]["complete"],21)
        self.assertEqual(r["summary"]["classification_counts"],{
            "NO_WATCH_IN_EVENT_ALIGNED_12H":21})
        self.assertFalse(r["automated_trading"])
        self.assertTrue(r["not_out_of_sample"])

if __name__=="__main__":
    unittest.main()
