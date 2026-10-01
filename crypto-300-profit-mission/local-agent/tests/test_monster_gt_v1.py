from mission_agent.monster.ground_truth import discover,START,HOUR
from mission_agent.monster.archive import parse_zip
import io,zipfile

def bars(n=600):return [[START+i*HOUR,1.,1.,1.,1.,100.,100.,10] for i in range(n)]
def test_gt_highest_tier_and_earliest_peak_refractory():
 b=bars();b[10][2]=21;b[11][2]=21;b[180][2]=4
 es,c=discover(b,'spot','XUSDT')
 assert es[0]['exact_tier']==20 and es[0]['peak_time']==START+11*HOUR
 assert es[0]['crossings']['2']==START+11*HOUR
 assert all(e['anchor_time']>START+178*HOUR for e in es[1:])
 assert es[0]['new_listing'] is None

def test_gap_never_bridged_or_future_imputed():
 b=bars(200);b[180][2]=10;b=b[:50]+b[51:]
 es,c=discover(b,'spot','XUSDT');assert es==[] and c['eligible_anchors']==0

def test_failed_ohlc_archive_rejected_and_microseconds_normalized():
 row=f'{START*1000},1,2,0.5,1,10,0,10,2,0,0,0\n'
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w') as z:z.writestr('test.csv',row)
 assert parse_zip(buf.getvalue())[0][0]==START

def test_noise_horizons_censor_gaps_and_do_not_fill():
 from mission_agent.monster.evaluation import noise_audit
 b=bars(200);b[30][2]=3
 rows,summary,noise=noise_audit([('spot','XUSDT',START+HOUR)],{('spot','XUSDT'):b})
 assert rows[0]['24h_non2x'] is True and rows[0]['72h_non2x'] is False
 assert rows[0]['168h_non2x'] is False
 g=b[:50]+b[51:]
 rows,summary,noise=noise_audit([('spot','XUSDT',START+HOUR)],{('spot','XUSDT'):g})
 assert rows[0]['72h_status']=='CENSORED' and rows[0]['168h_max_multiple'] is None

def test_exact_peak_tier_keeps_extreme_illiquid_print():
 b=bars(300);b[50][2]=20;b[50][6]=0
 ev,_=discover(b,'futures','DELISTEDUSDT',earliest_archive_month='2025-01')
 assert ev[0]['exact_tier']==20 and ev[0]['max7d']==20
 assert ev[0]['new_listing'] is True

def test_archive_contract_rejects_invalid_ohlc_and_nonfinite_prices():
 import pytest
 for row in [f'{START},1,0.5,0.4,1,10,0,10,2,0,0,0\n',f'{START},nan,2,0.5,1,10,0,10,2,0,0,0\n']:
  buf=io.BytesIO()
  with zipfile.ZipFile(buf,'w') as z:z.writestr('test.csv',row)
  with pytest.raises(ValueError,match='CANDLE_CONTRACT_INVALID'):parse_zip(buf.getvalue())

def test_future_label_crossing_validation_audit_boundary_is_censored():
 from mission_agent.monster.ground_truth import SPLITS
 b=bars(240);start=SPLITS['AUDIT'][0]-72*HOUR
 for i,row in enumerate(b):row[0]=start+i*HOUR
 b[80][2]=12
 es,c=discover(b,'spot','XUSDT')
 assert es[0]['split']=='VALIDATION' and not es[0]['split_future_complete']
 assert es[0]['exact_tier']==10
