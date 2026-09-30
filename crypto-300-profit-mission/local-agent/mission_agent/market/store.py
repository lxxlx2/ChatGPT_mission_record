from dataclasses import replace
from ..db.price_migrations import migrate_price
from ..db.connection import transaction
from ..clock import stamp
from ..hashing import canonical,digest,loads
from .bar import Bar,ASSETS,MINUTE

class PriceStore:
 def __init__(self,repo):
  self.repo=repo;self.db=repo.db;migrate_price(self.db,stamp(repo.clock.now()))
  with transaction(self.db):
   for asset in ASSETS:self.db.execute('INSERT OR IGNORE INTO price_source_state(asset) VALUES(?)',(asset,))
 def put(self,bar):
  now=stamp(self.repo.clock.now())
  with transaction(self.db):
   old=self.db.execute('SELECT * FROM price_bars_1m WHERE asset=? AND open_time_utc=? AND source=?',(bar.asset,bar.open_time_utc,bar.venue)).fetchone()
   state=self.db.execute('SELECT * FROM price_source_state WHERE asset=?',(bar.asset,)).fetchone()
   if old and old['source_hash']==bar.source_hash:
    self.db.execute('UPDATE price_source_state SET duplicate_event_count=duplicate_event_count+1 WHERE asset=?',(bar.asset,));return 'DUPLICATE'
   if old and old['is_closed'] and not bar.is_closed:return 'IGNORED_PROVISIONAL'
   if state['last_closed_bar_time'] is not None and bar.open_time_utc<state['last_closed_bar_time']:
    self.db.execute('UPDATE price_source_state SET out_of_order_count=out_of_order_count+1 WHERE asset=?',(bar.asset,))
   version=old['bar_version']+1 if old else 1;bar=replace(bar,bar_version=version)
   self.db.execute('INSERT INTO price_bars_1m VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(asset,open_time_utc,source) DO UPDATE SET payload_json=excluded.payload_json,is_closed=excluded.is_closed,source_hash=excluded.source_hash,bar_version=excluded.bar_version,updated_at=excluded.updated_at',
    (bar.asset,bar.open_time_utc,bar.venue,canonical(bar.value()).decode(),int(bar.is_closed),bar.source_hash,version,now,now))
   if bar.is_closed:
    last=max(state['last_closed_bar_time'] or bar.open_time_utc,bar.open_time_utc)
    self.db.execute('UPDATE price_source_state SET last_closed_bar_time=?,last_source_event_time=MAX(COALESCE(last_source_event_time,0),?),status=? WHERE asset=?',(last,bar.source_event_time or bar.close_time_utc,'CORRECTION_REPLAY_REQUIRED' if old and old['is_closed'] else 'CANONICAL_STORED',bar.asset))
   return 'UPDATED' if old else 'INSERTED'
 def bars(self,asset):
  for row in self.db.execute('SELECT payload_json FROM price_bars_1m WHERE asset=? AND is_closed=1 ORDER BY open_time_utc',(asset,)):
   value=loads(row[0]);value.pop('close_time_utc');yield Bar(**value)
 def gaps(self,asset,start=None,end=None):
  times=[r[0] for r in self.db.execute('SELECT open_time_utc FROM price_bars_1m WHERE asset=? AND is_closed=1 ORDER BY open_time_utc',(asset,))]
  if not times:return [] if start is None or end is None else list(range(start,end,MINUTE))
  start=times[0] if start is None else start;end=times[-1]+MINUTE if end is None else end
  actual=set(times);return [t for t in range(start,end,MINUTE) if t not in actual]
 def feature(self,asset,t,value):
  self.db.execute('INSERT INTO price_features VALUES(?,?,?) ON CONFLICT(asset,window_end) DO UPDATE SET payload_json=excluded.payload_json',(asset,t,canonical(value).decode()))
 def candidate(self,value):
  if value['asset'] not in ASSETS or value['event_type']!='RAW_PRICE_CANDIDATE' or value['missing_data'] or value['rule_version']!='PRICE_RULE_V1':raise ValueError('invalid raw price candidate')
  data=canonical(value);sha=digest(value)
  if len(data)>2000:raise ValueError('compact price evidence exceeds item budget')
  now=stamp(self.repo.clock.now());id=value['event_id']
  with transaction(self.db):
   old=self.db.execute('SELECT payload_sha256 FROM price_candidates WHERE event_id=?',(id,)).fetchone()
   if old:
    if old[0]!=sha:raise ValueError('PRICE_CANDIDATE_REVISION_CONFLICT')
    return 'DUPLICATE'
   self.db.execute('INSERT INTO price_candidates VALUES(?,?,?,?,?)',(id,value['asset'],value['window_end'],sha,data.decode()))
   self.db.execute('INSERT INTO candidates VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(id,'RAW_PRICE_CANDIDATE',value['source'],value['asset'],value['observed_at'],now,1,0,data.decode(),sha,'PENDING_DECISION',now))
   self.db.execute("INSERT INTO outbox(event_id,state,created_at,updated_at) VALUES(?,'PENDING',?,?)",(id,now,now))
   self.db.execute("INSERT INTO deliveries(event_id,policy,state,updated_at) VALUES(?,?,'PENDING_DECISION',?)",(id,self.repo.policy,now))
   return 'INSERTED'
