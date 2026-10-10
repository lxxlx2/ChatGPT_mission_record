"""Hermetic full-universe historical research replay tests, no provider or credentials."""
import csv,gzip,importlib.util,io,json,random,tempfile,unittest,zipfile
from collections import deque
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/monster_full_market_history_diagnostic.py"
spec=importlib.util.spec_from_file_location("monster_full_market_history_diagnostic",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ReadonlyMarketReplayTests(unittest.TestCase):
 def test_closed_hour_does_not_peek_current_or_future_price(self):
  h=mod.H
  bars=[[i*h,1,1.01,.99,1,20,10000,100] for i in range(25)]
  event=[25*h,1.2,1.22,1,1.2,20,80000,400]
  p=deque(bars[1:],maxlen=24)
  signals,ratio=mod.signal_info(event,p,bars[0][0])
  self.assertEqual(round(ratio,2),8)
  self.assertTrue(signals["ANY_STRONG"])
  self.assertTrue(signals["EARLY_WATCH"])
  self.assertTrue(signals["BREAKOUT24"])
  self.assertTrue(signals["VOLUME_1H8"])
  self.assertTrue(signals["MOMENTUM4"])
  self.assertFalse(signals["NEW_NO_BASE"])
  delayed=deque(list(p)[:-1],maxlen=24)
  signals,_=mod.signal_info(event,delayed,bars[0][0])
  self.assertFalse(signals["VOLUME_1H8"])
  self.assertFalse(signals["BREAKOUT24"])

 def test_new_listing_does_not_need_24_hour_history(self):
  h=mod.H
  earlier=[[0,1,1,1,1,5,1000,10]]
  b=[h,1.1,1.2,1.1,1.2,20,150000,50]
  x,_=mod.signal_info(b,deque(earlier,maxlen=24),0)
  self.assertTrue(x["NEW_NO_BASE"])
  self.assertTrue(x["ANY_STRONG"])
  self.assertFalse(x["EARLY_WATCH"])
  stale,_=mod.signal_info([25*h,1.1,1.2,1.1,1.2,20,150000,50],deque(earlier,maxlen=24),0)
  self.assertFalse(stale["NEW_NO_BASE"])

 def test_archive_synthetic_3904_events_and_readonly_outputs(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   fm3=root/"crypto-monitor-fm3-evidence-20261001/monster"
   fm2=root/"crypto-monitor-fm2-evidence-20260930/monster"
   fm3.mkdir(parents=True)
   fm2.mkdir(parents=True)
   h=mod.H
   start=mod.EPOCHS["VALIDATION_2024"][0]
   bars=[]
   for i in range(50):
    c=1 if i<30 else 1.20
    q=10000 if i!=30 else 100000
    bars.append([start+i*h,c,c*1.01,c*.99,c,10,q,100])
   s=fm3/"bars/spot/TESTUSDT.json.gz"
   s.parent.mkdir(parents=True)
   with gzip.open(s,"wt") as stream:json.dump(bars,stream)
   (fm3/"expanded-coverage.json").write_text(json.dumps([{
    "venue":"spot","symbol":"TESTUSDT","bars_path":str(s),"bars":50
   }]))
   (fm2/"universe-current-merged-v1.json").write_text("[]")
   event={
    "event_id":"spot:TESTUSDT:synthetic","venue":"spot","symbol":"TESTUSDT",
    "anchor_time":start+29*h,"peak_time":start+48*h,
    "max7d":5.0,"crossings":{"2":start+45*h}}
   none={
    "event_id":"spot:NONEUSDT:synthetic","venue":"spot","symbol":"NONEUSDT",
    "anchor_time":start+29*h,"peak_time":start+48*h,
    "max7d":2.1,"crossings":{"2":start+45*h}}
   packet=root/"packet.zip"
   with zipfile.ZipFile(packet,"w") as z:
    z.writestr("events/train-instrument-events.json",json.dumps([none]*1920))
    z.writestr("events/validation-instrument-events.json",json.dumps([event]+[none]*441))
    z.writestr("events/ground-truth-events-v1.json",json.dumps([none]*1542))
   original=s.read_bytes()
   out=root/"results.zip"
   summary=mod.run(root,packet,out)
   self.assertEqual(summary["all_historical_event_count"],3904)
   self.assertEqual(summary["missing_count"],0)
   self.assertEqual(summary["stats"]["symbols_scanned"],1)
   self.assertEqual(s.read_bytes(),original)
   self.assertGreater(summary["stats"]["raw_ANY_STRONG"],0)
   with zipfile.ZipFile(out) as z:
    self.assertIsNone(z.testzip())
    cases=list(csv.DictReader(io.StringIO(z.read("all_gt_event_signal_coverage.csv").decode())))
    self.assertEqual(len(cases),3904)
    selected=[x for x in cases if x["event_id"]=="spot:TESTUSDT:synthetic"]
    self.assertEqual(len(selected),1)
    self.assertEqual(selected[0]["ANY_STRONG_first_pre2_utc"],mod.moment(start+31*h))
    self.assertEqual(set(z.namelist()),{"summary.json","all_gt_event_signal_coverage.csv","all_market_signal_episodes.csv","README.txt"})

if __name__=="__main__":unittest.main()
