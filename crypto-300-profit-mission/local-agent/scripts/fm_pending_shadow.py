"""Explicit bounded private-test queue pump; no scheduler or investment delivery."""
import argparse,json,sqlite3,time,signal
from pathlib import Path
from scripts.fm_private_shadow import run

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--run-id',required=True);p.add_argument('--db-name',default='forward.sqlite');p.add_argument('--seconds',type=int,default=7500);a=p.parse_args();start=time.monotonic();stopping=False
 def stop(*_):
  nonlocal stopping
  stopping=True
 signal.signal(signal.SIGTERM,stop)
 while not stopping and time.monotonic()-start<a.seconds:
  db=sqlite3.connect(f'file:{a.root/a.db_name}?mode=ro',uri=True)
  existing=db.execute("SELECT batch_id FROM batches WHERE state='BUILT' ORDER BY generated_at,batch_id LIMIT 1").fetchone();pending=db.execute("SELECT count(*) FROM outbox WHERE state='PENDING'").fetchone()[0];seq=int(db.execute("SELECT value FROM meta WHERE key='batch_seq'").fetchone()[0]);db.close()
  if pending or existing:
   receipt=f'private-shadow-forward-batch{seq if existing else seq+1:04d}-result.json'
   try:run(a.root,a.run_id,a.db_name,receipt)
   except Exception as exc:
    with (a.root/'private-shadow-errors.jsonl').open('a') as f:f.write(json.dumps({'utc_epoch':str(time.time()),'error':type(exc).__name__})+'\n')
  for _ in range(10):
   if stopping:break
   time.sleep(1)
if __name__=='__main__':main()
