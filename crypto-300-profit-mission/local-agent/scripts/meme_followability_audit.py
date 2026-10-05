"""Bounded available-history audit. No reconstructed historical detection or invented returns."""
import argparse,json,sqlite3
from collections import Counter
from pathlib import Path
from mission_agent.frank.archive import publish
from mission_agent.hashing import canonical
from mission_agent.meme.followability import HORIZONS

def main():
 p=argparse.ArgumentParser();p.add_argument('--history-db',type=Path,required=True);p.add_argument('--runtime-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();db=sqlite3.connect(f'file:{a.history_db}?mode=ro',uri=True);counts=Counter();positive_buys=0
 for row in db.execute('SELECT evidence_json FROM frank_transactions'):
  e=json.loads(row[0]);counts[e['mechanical_classification']]+=1
  if e['mechanical_classification']=='ACTIVE_SWAP_LIKE':positive_buys+=len({d['mint'] for d in e['token_balance_deltas'] if d['wallet_owned'] and int(d['delta'])>0})
 db.close();live=sqlite3.connect(f'file:{a.runtime_root / "forward.sqlite"}?mode=ro',uri=True);timings=[]
 for row in live.execute('SELECT t.block_time,o.detected_at,o.normalized_at FROM frank_transactions t JOIN frank_observations o USING(signature)'):
  if row[0] is not None:timings.append({'detected_minus_block_seconds':str(float(row[1])-row[0]),'normalized_minus_detected_seconds':str(float(row[2])-float(row[1]))})
 live.close();result={'status':'INSUFFICIENT_EXECUTABLE_PRICE_HISTORY','available_history_transactions':sum(counts.values()),'classifications':dict(counts),'positive_mint_active_observations':positive_buys,'historical_detection_times_available':False,'bulk_processing_time_is_historical_availability':False,'real_forward_timing_observations':len(timings),'timings':timings,'return_horizons':{str(h):{'measured_samples':0,'delayed_entry_return':None,'MFE':None,'MAE':None,'max_drawdown':None,'reason':'No executable same-notional historical bid/ask series or original historical detection timestamps'} for h in HORIZONS},'liquidity':None,'executable_size':None,'already_overextended_rate':None,'precision':None,'base_rate':None,'TTL_status':'TEMPORARY_SHADOW_TTL','strategy_validated':False,'contradiction_of_value_proven':False,'limitations':['Wallet fill is not substituted for user delayed entry.','Transaction balances establish chain flow, not a future executable price quote.','Hourly external consumer must permanently discard expired candidates.']};publish(a.output,canonical(result));print(json.dumps({k:v for k,v in result.items() if k not in ['timings','return_horizons']}))
if __name__=='__main__':main()
