"""Preserve prior shadow DB; replay raw evidence into a new parser-version DB.

Actual first-detection times survive unchanged. Replay never manufactures a
backdated observation or emits a historical candidate as a new live event.
"""
import argparse,gzip,json,sqlite3
from pathlib import Path
from mission_agent.frank.collector import verify_acceptance
from mission_agent.frank.parser import normalize,PARSER_VERSION
from mission_agent.frank.rpc import SolanaRPC
from mission_agent.frank.store import FrankStore
from mission_agent.frank.archive import publish
from mission_agent.db.repository import Repository
from mission_agent.hashing import canonical

def main():
 p=argparse.ArgumentParser();p.add_argument('--old',type=Path,required=True);p.add_argument('--new',type=Path,required=True);p.add_argument('--manual',type=Path,required=True);p.add_argument('--raw500',type=Path,required=True);p.add_argument('--processed',type=Path,required=True);a=p.parse_args()
 verify_acceptance({'manual':str(a.manual),'raw':str(a.raw500),'processed':str(a.processed)})
 if a.new.exists():raise ValueError('MIGRATION_TARGET_MUST_BE_NEW')
 old=sqlite3.connect(f'file:{a.old}/forward.sqlite?mode=ro',uri=True);old.row_factory=sqlite3.Row
 if old.execute('SELECT count(*) FROM candidates').fetchone()[0]:raise ValueError('LIVE_CANDIDATES_REQUIRE_SEPARATE_ARCHIVE_MIGRATION')
 prior=old.execute("SELECT * FROM frank_cursor WHERE name='latest'").fetchone();rows=old.execute('SELECT evidence_json FROM frank_transactions ORDER BY block_time,slot,signature').fetchall();observations={r['signature']:dict(r) for r in old.execute('SELECT * FROM frank_observations')}
 a.new.mkdir(mode=0o700,parents=True);raw=a.new/'raw';raw.mkdir(mode=0o700);repo=Repository(a.new/'forward.sqlite');store=FrankStore(repo);seed=set();rpc=SolanaRPC()
 for path in sorted((a.processed/'normalized500').glob('*.json.gz')):
  e=json.loads(gzip.decompress(path.read_bytes()));store.put(e);seed.add(e['signature'])
 migrated=[]
 for row in rows:
  before=json.loads(row[0]);sig=before['signature']
  if sig in seed:continue
  cache=a.old/'raw'/(sig+'.json.gz')
  if cache.exists():data=cache.read_bytes();tx=json.loads(gzip.decompress(data))
  else:
   if sig in observations:raise ValueError('OBSERVED_TRANSACTION_RAW_MISSING')
   tx=rpc.transaction(sig);data=gzip.compress(json.dumps(tx,separators=(',',':'),allow_nan=False).encode(),mtime=0)
  after=normalize(sig,tx)
  for field in ('token_balance_deltas','wallet_is_signer','wallet_is_fee_payer','authority_accounts','mechanical_classification'):
   if before[field]!=after[field]:raise ValueError('LIVE_REPLAY_REQUIRES_REVIEW:'+field)
  publish(raw/cache.name,data);observation=observations.get(sig);store.put(after,observation=observation);migrated.append(sig)
 latest=next(e for e in store.evidence() if e['signature']==prior['signature']);store.put(latest,advance=True)
 result={'status':'PRESERVED_OLD_DB_AND_MIGRATED','parser_version':PARSER_VERSION,'raw_transactions_replayed':len(migrated),'real_observations_preserved':len(observations),'classification_unchanged':True,'canonical_axes_unchanged':True,'cursor_signature_preserved':True,'new_candidates_emitted_by_migration':0,'source_initial_cursor_only_rpc_calls':rpc.calls}
 publish(a.new/'migration-result.json',canonical(result));old.close();repo.close();print(json.dumps(result))
if __name__=='__main__':main()
