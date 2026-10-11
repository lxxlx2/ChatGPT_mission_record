"""Stage18 source-true causal 3m/15m/60m price and quote gate diagnostics."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
FILE=Path(__file__).parents[1]/"scripts"/"monster_v4_stage18_missed_gate_diagnostic.py"
SYMS=("ENSOUSDT","ENAUSDT","STXUSDT","NILUSDT","SAGAUSDT","ZAMAUSDT","ARUSDT")

def load():
    evidence=Path(tempfile.gettempdir())/"monster-stage18-test"
    evidence.mkdir(exist_ok=True)
    (evidence/"monster_stage17_actual_firstcross_minute_replay_ci_20261011.json").write_text(
        json.dumps({"schema":"MONSTER_STAGE17_EXPOSED_EVENT_ALIGNED_TRUE_1M_V4_CI_V1",
            "cases":[{"symbol":s,"date":"2026-05-17","threshold_x":2,
                    "classification":"LATE" if s=="ARUSDT" else "NO_WATCH"} for s in SYMS]}))
    old=types.ModuleType("monster_v4_stage17_event_aligned_replay")
    old.archive=types.SimpleNamespace(source=types.SimpleNamespace(EVIDENCE=evidence),get_day=None)
    old.frozen_events=lambda: [{"date":"2026-05-17","symbol":s,"threshold":2,
            "base_open":"1","hour_index":55} for s in SYMS]
    old.utc_ms=lambda t:int(t.timestamp()*1000)
    old.replay=types.SimpleNamespace(utc=lambda t:datetime.fromtimestamp(t/1000,timezone.utc).isoformat())
    sys.modules[old.__name__]=old
    spec=importlib.util.spec_from_file_location("stage18_testable",FILE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def downloader(day_anchor,*,before_quote=50,price_trigger=False):
    cross=int(day_anchor.timestamp()*1000)+30*60000
    rise=int(day_anchor.timestamp()*1000)-10*60000
    def get(symbol,day):
        start=int(datetime(day.year,day.month,day.day,tzinfo=timezone.utc).timestamp()*1000)
        rows=[]
        for i in range(1440):
            ms=start+i*60000
            close=1.2 if price_trigger and ms>=rise else 1
            high=2.1 if ms==cross else close
            rows.append((ms,1,high,1,close,before_quote,5))
        return rows,{"sha256":"a"*64}
    return get

class Stage18Tests(unittest.TestCase):
    def test_freeze_exact_seven(self):
        m=load()
        self.assertEqual({r["symbol"] for r in m.frozen_failed_events()},set(SYMS))

    def test_liquidity_gate_causes_nontrigger(self):
        m=load()
        event=m.frozen_failed_events()[0]
        anchor=datetime(2026,5,17,6,tzinfo=timezone.utc)+timedelta(hours=55)
        out=m.analyze(event,download=downloader(anchor,before_quote=50,price_trigger=True))
        self.assertEqual(out["status"],"COMPLETE_GATE_DIAGNOSTIC")
        self.assertEqual(out["cause"],"LIQUIDITY_GATE_BLOCKED_ALL_PRICE_TRIGGERS")
        self.assertGreater(out["ticks_price_trigger_without_quote_gate"],0)
        self.assertEqual(out["ticks_price_and_quote_both_pass"],0)

    def test_no_momentum_when_only_1m_high_wick(self):
        m=load()
        event=m.frozen_failed_events()[0]
        anchor=datetime(2026,5,17,6,tzinfo=timezone.utc)+timedelta(hours=55)
        out=m.analyze(event,download=downloader(anchor,before_quote=100,price_trigger=False))
        self.assertEqual(out["cause"],"NO_FROZEN_MOMENTUM_TRIGGER_BEFORE_2X")

    def test_nonfrozen_event_rejected(self):
        m=load()
        with self.assertRaisesRegex(ValueError,"NONFROZEN_EVENT"):
            m.run(events=[{"date":"2026-05-17","symbol":"FAKEUSDT","threshold":2}],
                worker=lambda e:e)

    def test_cannot_claim_unmeasured_source_winner(self):
        m=load()
        event=m.frozen_failed_events()[0]
        def fail(symbol,day):
            raise ValueError("GAPPED_ARCHIVE_DAY")
        out=m.analyze(event,download=fail)
        self.assertEqual(out["status"],"SOURCE_FAILED_OR_CENSORED")

if __name__=="__main__":
    unittest.main()
