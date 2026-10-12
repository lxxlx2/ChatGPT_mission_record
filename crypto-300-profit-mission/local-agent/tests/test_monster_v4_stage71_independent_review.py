"""Reviewer-authored regression and defect reproductions, synthetic inputs labeled.
Tests describing existing limitations deliberately assert current behavior;
passing tests do not mean those defects have been repaired.
"""
import copy, hashlib, importlib, io, random, shutil, sqlite3, subprocess, sys, tempfile, unittest, zipfile
from datetime import datetime,timedelta
from decimal import Decimal as D
from pathlib import Path
S=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(S))
p2=importlib.import_module('monster_v4_stage68_exposed2700_dual_lane_watch_p1_halfday_reserve')
p1=importlib.import_module('monster_v4_stage51_pinnedP1v03_full900_causal_minute_replay')
raw=importlib.import_module('monster_v4_stage38_usdm_original_v4_1m_pilot')
proj=importlib.import_module('monster_v4_stage70_historical_watch_projection_sqlite')
audit=importlib.import_module('monster_v4_stage71_independent_review_recompute')

def ev(symbol,kind,offset,quote='100'):
    clock=(datetime.fromisoformat('2025-03-30T06:00:00+00:00')+timedelta(minutes=offset)).isoformat().replace('+00:00','Z')
    return dict(date='2025-03-30',symbol=symbol,kind=kind,at_UTC=clock,asof_quote15=quote)
def pair(s,m,q='100'):
    return [ev(s,'FIRST_D0_WATCH',m,q),ev(s,'P1_FIRST_ASOF_ELIGIBLE',m,q)]

class Review(unittest.TestCase):
    def test_official_minute_checksum_and_millisecond_microsecond_equivalence(self):
        from datetime import date
        day=date(2025,3,29);start=raw.msutc('2025-03-29T00:00:00Z')
        def archive(scale,skip=None):
            lines=[]
            for i in range(1440):
                if i==skip:continue
                lines.append(f'{(start+i*60000)*scale},100,101,99,100,1,{(start+i*60000+59999)*scale},1000,1,0,0,0')
            buf=io.BytesIO()
            with zipfile.ZipFile(buf,'w') as z:z.writestr('TESTUSDT-1m-2025-03-29.csv','\n'.join(lines))
            return buf.getvalue()
        def load(payload,wrong=False):
            checksum=('0'*64 if wrong else hashlib.sha256(payload).hexdigest()).encode()
            return raw.verified_1m_day('TESTUSDT',day,reader=lambda url,limit:checksum if url.endswith('.CHECKSUM') else payload)
        a,_=load(archive(1));b,_=load(archive(1000));self.assertEqual(a,b)
        with self.assertRaisesRegex(ValueError,'HASH_NOT_MATCH'):load(archive(1),True)
        with self.assertRaisesRegex(ValueError,'GAPPED'):load(archive(1,skip=700))
    def test_exact_900_identity_per_date_and_censor_retention(self):
        import monster_v4_stage65_new3_full900_official_hourly_SHA as source
        names=set(source.frozen());rows,_,_=p2.load()
        for date in p2.DATES:self.assertEqual({r['symbol'] for r in rows if r['date']==date},names)
        for r in rows:
            if r['minute_source_status']!=p2.VALID:
                self.assertIsNone(r['original_D0_first_UTC']);self.assertIsNone(r['P1v03_original_unbudgeted_candidate'])
    def test_future_source_gap_erases_whole_discovery_record_current_limitation(self):
        import monster_v4_stage66_new3_original_1m_D0_first5_vs_P1v03 as source
        hourly={'date':'2025-03-30','symbol':'SYNTHETICUSDT','source_status':source.HOUR_GOOD}
        def unavailable_after_early_valid_observations(symbol,date):
            raise FileNotFoundError('SYNTHETIC_ONLY: future source day missing after a valid early signal')
        result=source.process(hourly,loader=unavailable_after_early_valid_observations)
        self.assertIsNone(result['original_D0_first_UTC']);self.assertEqual(result['minute_source_status'],'CENSORED_OFFICIAL_1M_PUBLISHER_404')
    def test_older5400_counterexample_independently_recalculated(self):
        import json
        with tempfile.TemporaryDirectory() as td:
            audit.older6(Path(td));result=json.loads((Path(td)/'monster_stage71_independent_older5400_counterexample.json').read_text())
        self.assertEqual((result['old_urgent'],result['new_urgent'],result['old_early'],result['new_early'],result['D0_pre5_2x_denominator']),(127,113,21,20,28))
        aia=next(x for x in result['5x10x_cases'] if x['symbol']=='AIAUSDT')
        self.assertTrue(aia['old_early']);self.assertFalse(aia['new_early'])
    def test_stage68_changed_source_bytes_fail_closed(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            changed=Path(td)/p2.DATA.name;changed.write_bytes(p2.DATA.read_bytes()+b'\n')
            with patch.object(p2,'DATA',changed):
                with self.assertRaisesRegex(ValueError,'IMMUTABLE'):p2.load()
    def test_boundary_utc06_and_exact_halfday(self):
        events=sum((pair('X'+str(i),m) for i,m in enumerate([0,3,717,720,723,1437,1440])),[])
        log,state,c,h=p2.simulate(events)
        self.assertEqual([state[('2025-03-30','X'+str(i))]['urgent'] for i in range(7)],[True,True,False,True,True,True,True])
        self.assertEqual(c[('2025-03-30',0)],5);self.assertEqual(c[('2025-03-30',1)],1)
        self.assertEqual(h[('2025-03-30',0)],2)
    def test_late_half_inherits_unused_early_capacity(self):
        _,_,c,h=p2.simulate(sum((pair('L'+str(i),720+i*3) for i in range(6)),[]))
        self.assertEqual(c[('2025-03-30',0)],5);self.assertEqual(h[('2025-03-30',0)],0)
    def test_same_minute_watch_before_p1_quote_and_symbol_ties(self):
        log,state,_,_=p2.simulate(pair('Z',0,'200')+pair('B',0,'100')+pair('A',0,'100'))
        self.assertEqual([x['symbol'] for x in log if x['kind']=='P1_FIRST_ASOF_ELIGIBLE'],['Z','A','B'])
        self.assertFalse(state[('2025-03-30','B')]['urgent'])
    def test_unordered_full_replay_and_closed_tick_prefix(self):
        rows,_,_=p2.load();events,_=p2.validated_events(rows);expected=p2.simulate(events)[0]
        random.Random(71).shuffle(events);self.assertEqual(p2.simulate(events)[0],expected)
        for at in sorted({e['at_UTC'] for e in events}):
            cutoff=p2.stamp(at);prefix=[e for e in events if p2.stamp(e['at_UTC'])<=cutoff]
            self.assertEqual(p2.simulate(prefix)[0],[e for e in expected if p2.stamp(e['at_UTC'])<=cutoff])
    def test_future_outcome_labels_cannot_change_decisions(self):
        rows,_,_=p2.load();events,_=p2.validated_events(rows);before=p2.simulate(events)[0]
        for e in events:e['future_GT2x_EVALUATION_ONLY']=not e['future_GT2x_EVALUATION_ONLY'];e['first_2x_HIGH_EVALUATION_ONLY']='2099-01-01T00:00:00Z'
        self.assertEqual(p2.simulate(events)[0],before)
    def test_duplicate_delivery_rejected_not_idempotent(self):
        events=pair('X',0)
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):p2.simulate(events+[events[0]])
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):p2.simulate(events+[events[1]])
    def test_p1_without_watch_or_before_watch_rejected(self):
        with self.assertRaisesRegex(ValueError,'WITHOUT_UNIQUE'):p2.simulate([ev('X','P1_FIRST_ASOF_ELIGIBLE',0)])
        with self.assertRaisesRegex(ValueError,'WITHOUT_UNIQUE'):p2.simulate([ev('X','FIRST_D0_WATCH',3),ev('X','P1_FIRST_ASOF_ELIGIBLE',0)])
    def test_deferred_stays_deferred_no_backfill(self):
        events=pair('A',0)+pair('B',3)+pair('C',6)+pair('D',720)
        _,state,_,_=p2.simulate(events)
        self.assertFalse(state[('2025-03-30','C')]['urgent']);self.assertEqual(state[('2025-03-30','C')]['p1_UTC'],'2025-03-30T06:06:00Z')
    def test_restart_suffix_not_a_persistent_allocator(self):
        # Complete replay works; independent suffix loses prior WATCH/cap state.
        prefix=pair('A',0)+pair('B',3);suffix=pair('C',6)
        self.assertFalse(p2.simulate(prefix+suffix)[1][('2025-03-30','C')]['urgent'])
        self.assertTrue(p2.simulate(suffix)[1][('2025-03-30','C')]['urgent'])
    def test_p1_closed_bar_future_high_volume_price_mutations(self):
        start=raw.msutc('2025-03-29T06:00:00Z');bars=[(start+i*60000,D(100),D(101),D(99),D(100),D(100000),1) for i in range(2000)]
        t=start+1500*60000
        def features(x):
            pref=[D(0)]
            for b in x:pref.append(pref[-1]+b[5])
            return p1.at(x,pref,t,D(100))
        original=features(bars)
        for i in range(1500,len(bars)):bars[i]=(bars[i][0],D(100),D('1e9'),D(1),D('1e8'),D('1e12'),1)
        self.assertEqual(features(bars),original)
        self.assertEqual(original['quote15_USDT'],D(1500000));self.assertEqual(original['quote_prior45_USDT'],D(4500000))
    def test_d0_future_suffix_invariant(self):
        start=raw.msutc('2025-03-29T06:00:00Z');bars=[(start+i*60000,D(100),D(101),D(99),D(100),D(100000),1) for i in range(raw.BARS)]
        bars[1445]=(bars[1445][0],D(110),D(111),D(109),D(110),D(100000),1)
        cutoff=start+1500*60000
        a=raw.production_scan('TESTUSDT','2025-03-30',bars)
        for i in range(1500,len(bars)):bars[i]=(bars[i][0],D(200),D(999999),D(1),D(200),D('1e12'),1)
        b=raw.production_scan('TESTUSDT','2025-03-30',bars)
        self.assertEqual([t for t in a['WATCH_UTC'] if raw.msutc(t)<=cutoff],[t for t in b['WATCH_UTC'] if raw.msutc(t)<=cutoff]);self.assertTrue(a['WATCH_UTC'])
        self.assertEqual(audit.independent_raw_events(bars,'2025-03-30')['WATCH_UTC'],b['WATCH_UTC'])
    def test_independent_scheduler_all_identity_parity(self):
        rows,_,_=p2.load();events,_=p2.validated_events(rows);log=p2.simulate(events)[0];result=audit.recalculate(rows)
        decision={(e['date'],e['symbol']):e['budget_action']=='RESEARCH_URGENT_P2_CAP_CONSUMED' for e in log if e['kind']=='P1_FIRST_ASOF_ELIGIBLE'}
        self.assertEqual(decision,{(e['date'],e['symbol']):e['new_urgent'] for e in result['allocation']})
        self.assertEqual((result['watch'],result['p1'],result['old_urgent'],result['new_urgent'],result['old_early'],result['new_early']),(196,56,50,48,2,4))
    def test_upstream_blob_guard_missing_dependency_reproduction(self):
        # Synthetic mutation outside the real checkout, before importing modules.
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'crypto-300-profit-mission'/'local-agent'/'scripts';dst.parent.mkdir(parents=True)
            shutil.copytree(S,dst);shutil.copytree(p2.BASE,dst.parents[1]/'monster')
            changed=dst/'monster_v4_stage39_usdm_all900_sixday_original_1m.py'
            changed.write_text(changed.read_text()+"\n_original_evaluate=evaluate\ndef evaluate(*args,**kwargs):\n    result=_original_evaluate(*args,**kwargs)\n    result['WATCH_UTC']=[]\n    return result\n")
            result=subprocess.run([sys.executable,'-B','-c','import monster_v4_stage66_new3_original_1m_D0_first5_vs_P1v03 as s; s.frozen(); print("MUTATED_STAGE39_ACCEPTED_BY_STAGE66_FROZEN")'],cwd=dst,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertIn('MUTATED_STAGE39_ACCEPTED',result.stdout)
    def test_sqlite_persistence_duplicate_and_atomic_rollback(self):
        data=proj.source()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'review.sqlite'
            with sqlite3.connect(path,isolation_level=None) as db:
                proj.setup(db);self.assertEqual(proj.ingest(db,data[::-1]),937);snapshot=proj.snapshot(db)
                bad=copy.deepcopy(data[0]);bad['symbol']='ZZZ';bad['event_id']='monster68:'+bad['date']+':ZZZ:'+bad['kind']
                malformed=copy.deepcopy(data[-1]);malformed['event_id']='broken'
                with self.assertRaises(ValueError):proj.ingest(db,[bad,malformed])
                self.assertEqual(proj.snapshot(db),snapshot);self.assertEqual(proj.counts(db)['journal_events'],937)
            with sqlite3.connect(path,isolation_level=None) as db:
                self.assertEqual(proj.snapshot(db),snapshot);self.assertEqual(proj.ingest(db,data),0)
    def test_cli_existing_sqlite_reimport_false_failure_reproduction(self):
        with tempfile.TemporaryDirectory() as td:
            command=[sys.executable,'-B',str(S/'monster_v4_stage70_historical_watch_projection_sqlite.py'),'--db',td+'/review.sqlite','--out',td+'/out']
            a=subprocess.run(command,text=True,capture_output=True);b=subprocess.run(command,text=True,capture_output=True)
            self.assertEqual(a.returncode,0,a.stderr);self.assertNotEqual(b.returncode,0);self.assertIn('INPUT_EVENTS_OR_WATCH_DROPPED',b.stderr)
            with sqlite3.connect(td+'/review.sqlite') as db:self.assertEqual(proj.counts(db)['journal_events'],937)
if __name__=='__main__':unittest.main()
