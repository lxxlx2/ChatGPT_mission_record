"""Atomic deterministic model state, signal ledger and delivery outbox; no GPT."""
import json
from decimal import Decimal
from ..db.connection import transaction
from ..hashing import digest
from .policy import POLICY_SHA256,USDC
from .evaluator import evaluate,watch_eligible,establish_t0,watch_tick
from .store import quantity

class Engine:
    def __init__(self,ledger,policy,*,dry_run=True):
        self.ledger,self.db,self.policy,self.dry_run=ledger,ledger.db,policy,dry_run
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS email_content(signal_id TEXT PRIMARY KEY,subject TEXT,body TEXT,content_hash TEXT);
        CREATE TABLE IF NOT EXISTS v1_meta(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS v1_seen(wallet TEXT,signature TEXT,PRIMARY KEY(wallet,signature));
        CREATE TABLE IF NOT EXISTS v1_states(person_id TEXT,mint TEXT,body TEXT,PRIMARY KEY(person_id,mint));
        CREATE TABLE IF NOT EXISTS v1_episodes(episode_id TEXT PRIMARY KEY,person_id TEXT,mint TEXT);
        CREATE TABLE IF NOT EXISTS v1_evaluations(evaluation_id TEXT PRIMARY KEY,person_id TEXT,mint TEXT,episode_id TEXT,at INTEGER,signature TEXT,body TEXT);
        ''')
        old=self.db.execute("SELECT value FROM v1_meta WHERE key='policy_hash'").fetchone()
        if old and old[0]!=POLICY_SHA256:raise ValueError('MODEL_POLICY_HASH_DRIFT')
        self.db.execute("INSERT OR IGNORE INTO v1_meta VALUES('policy_hash',?)",(POLICY_SHA256,))
        self.db.execute("INSERT OR IGNORE INTO v1_meta VALUES('duplicates_suppressed','0')")
        # Compatibility recovery may only copy an already frozen delivery.
        # Missing historical content is not safe to reconstruct with today's template.
        has_delivery=self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='gmail_delivery'").fetchone()
        for row in self.db.execute("SELECT s.signal_id FROM signals s LEFT JOIN email_content m USING(signal_id) WHERE s.signal_type='FRANK_MULTIPLE_SIGNAL' AND json_extract(s.body,'$.policy_id')='FRANK_LOCAL_SIGNAL_V1' AND m.signal_id IS NULL").fetchall():
            frozen=self.db.execute('SELECT subject,body,content_hash FROM gmail_delivery WHERE signal_id=?',(row['signal_id'],)).fetchone() if has_delivery else None
            if frozen and digest({'subject':frozen['subject'],'body':frozen['body']})==frozen['content_hash']:
                self.db.execute('INSERT INTO email_content VALUES(?,?,?,?)',(row['signal_id'],frozen['subject'],frozen['body'],frozen['content_hash']))
            else:
                self.db.execute("UPDATE outbox SET status=CASE WHEN status='DRY_RUN_AUDIT' THEN status ELSE 'CREDENTIAL_BLOCKED' END,last_error=? WHERE signal_id=? AND channel='gmail'",('INVALID_FROZEN_EMAIL_CONTENT' if frozen else 'MISSING_FROZEN_EMAIL_CONTENT',row['signal_id']))
    def _state(self,person,mint):
        r=self.db.execute('SELECT body FROM v1_states WHERE person_id=? AND mint=?',(person,mint)).fetchone()
        return json.loads(r[0]) if r else None
    def _save(self,s):self.db.execute('INSERT OR REPLACE INTO v1_states VALUES(?,?,?)',(s['person_id'],s['mint'],json.dumps(s,sort_keys=True)))
    def _emit(self,s,at,stage):
        sid=digest({'policy_id':self.policy['policy_id'],'policy_hash':POLICY_SHA256,'person_id':s['person_id'],'mint':s['mint'],'episode_id':s['episode_id'],'signal_type':stage['signal_type'],'stage':stage['stage']})
        if self.db.execute('SELECT 1 FROM signals WHERE signal_id=?',(sid,)).fetchone():
            self.db.execute("UPDATE v1_meta SET value=CAST(value AS INTEGER)+1 WHERE key='duplicates_suppressed'");return None
        buys=[e for e in s['events'] if e['direction']=='BUY'];latest=buys[-1];quote={}
        sold_quote={}
        for e in s['events']:
            target=quote if e['direction']=='BUY' else sold_quote
            target[e['quote_asset']]=str(Decimal(target.get(e['quote_asset'],'0'))+Decimal(e['quote_quantity']))
        position={'first_buy_at':buys[0]['at'],'last_buy_at':latest['at'],'buy_count':len(buys),'sell_count':sum(e['direction']=='SELL' for e in s['events']),'gross_token_bought':str(sum(int(e['token_amount_raw']) for e in buys)),'gross_token_sold':str(sum(int(e['token_amount_raw']) for e in s['events'] if e['direction']=='SELL')),'gross_quote_spent':quote,'gross_quote_received':sold_quote,'current_token_position':s['current_raw'],'current_token_quantity':quantity(s['current_raw'],latest['token_decimals']) if s['current_raw'] is not None else None,'episode_id':s['episode_id'],'inventory_scope':'OBSERVED_ACTIVE_SEQUENCE','lifetime_position':'LIFETIME_POSITION_UNKNOWN'}
        body={'policy_id':self.policy['policy_id'],'policy_hash':POLICY_SHA256,'signal_id':sid,'person_id':s['person_id'],'mint':s['mint'],'episode_id':s['episode_id'],'signal_type':stage['signal_type'],'stage':stage['stage'],'triggered_at':at,'first_trigger_at':at,'latest_trade_signature':s['events'][-1]['signature'],'triggering_signature':s['events'][-1]['signature'],'latest_buy_signature':latest['signature'],'latest_buy':quantity(latest['token_amount_raw'],latest['token_decimals']),'latest_quote_amount':latest['quote_quantity'],'quote_asset':latest['quote_asset'],'position':position,'reason_codes':stage['reason_codes'],'usd':'unavailable','delivery_mode':'DRY_RUN_AUDIT' if self.dry_run else 'LIVE'}
        encoded=json.dumps(body,sort_keys=True);content_hash=digest(body)
        self.db.execute('INSERT INTO signals VALUES(?,?,?,?,?,?,?,?,?)',(sid,s['person_id'],s['mint'],s['episode_id'],stage['signal_type'],stage['stage'],str(at),content_hash,encoded))
        for channel in (['local','gmail'] if stage['signal_type']=='FRANK_MULTIPLE_SIGNAL' else ['local']):self.db.execute('INSERT INTO outbox(signal_id,channel,status) VALUES(?,?,?)',(sid,channel,'DRY_RUN_AUDIT' if self.dry_run else 'PENDING'))
        row=self.db.execute('SELECT body FROM signatures WHERE signature=? AND person_id=?',(body['latest_trade_signature'],s['person_id'])).fetchone()
        if row:
            audit=json.loads(row[0]);audit['signal_ids']=sorted(set(audit.get('signal_ids',[])+[sid]))
            self.db.execute("UPDATE signatures SET body=?,alert_state='YES',alert_reason='DETERMINISTIC_STAGE_UPGRADE' WHERE signature=? AND person_id=?",(json.dumps(audit,sort_keys=True),body['latest_trade_signature'],s['person_id']))
        if stage['signal_type']=='FRANK_MULTIPLE_SIGNAL':
            from .email import content
            mail=content(body)
            self.db.execute('INSERT INTO email_content VALUES(?,?,?,?)',(sid,mail['subject'],mail['body'],mail['content_hash']))
        if stage['signal_type']=='FRANK_ACCUMULATION_SIGNAL':s['accumulation_emitted']=True
        else:s['multiple_emitted']=True
        return sid
    def _evaluate(self,s,at,signature,kind):
        result=evaluate(s,at,self.policy);ids=[]
        for stage in result['stages']:
            sid=self._emit(s,at,stage)
            if sid:ids.append(sid)
        result.update(signal_ids=ids,kind=kind)
        eid=digest({'episode':s['episode_id'],'at':at,'signature':signature,'kind':kind})
        self.db.execute('INSERT OR IGNORE INTO v1_evaluations VALUES(?,?,?,?,?,?,?)',(eid,s['person_id'],s['mint'],s['episode_id'],at,signature,json.dumps(result,sort_keys=True)))
        return result
    def tick(self,at):
        old=self.db.execute("SELECT value FROM v1_meta WHERE key='last_time'").fetchone()
        last=int(old[0]) if old else at
        if at<last:return
        tick=watch_tick(last)+3600
        while tick<=at:
            with transaction(self.db):
                rows=self.db.execute('SELECT body FROM v1_states').fetchall()
                for r in rows:
                    s=json.loads(r[0])
                    if s['state']!='OPEN':continue
                    latest=s['events'][-1]['at']
                    # No active sequence with >3h of no fresh buy can newly qualify.
                    if tick-latest>self.policy['mapping']['FRANK_MULTIPLE_SIGNAL']['stale_after_seconds']:continue
                    self._evaluate(s,tick,s['events'][-1]['signature'],'HOURLY_29')
                    s['watch_at']=tick if watch_eligible(s,tick,self.policy) else None;self._save(s)
                self.db.execute("INSERT OR REPLACE INTO v1_meta VALUES('last_time',?)",(str(tick),))
            tick+=3600
        self.db.execute("INSERT OR REPLACE INTO v1_meta VALUES('last_time',?)",(str(at),))
    def process(self,row):
        if self.db.execute('SELECT 1 FROM v1_seen WHERE wallet=? AND signature=?',(row['wallet'],row['signature'])).fetchone():return None
        e=json.loads(row['body']);at=row['block_time']
        if at is not None:self.tick(at)
        result=None
        with transaction(self.db):
            t=e.get('trade') if e['classification']=='ACTIVE_TRADE' else None
            if t and at is not None:
                evidence=e.get('evidence',{})
                if not e['frank_is_signer'] or evidence.get('tx_err') is not None or not all(evidence.get('classification_evidence',{}).get(k) for k in ['dex_program_interaction','swap_instruction_evidence','opposing_economic_flows']):raise ValueError('VERIFIED_ACTIVE_TRADE_REQUIRED')
                person,mint=row['person_id'],t['mint'];s=self._state(person,mint)
                if t['direction']=='BUY' and (s is None or s['state']!='OPEN'):
                    episode=digest({'policy':self.policy['policy_id'],'person':person,'mint':mint,'first_buy':row['signature']})
                    s={'person_id':person,'mint':mint,'episode_id':episode,'state':'OPEN','events':[],'current_raw':'0','peak_raw':'0','inventory_points':[],'t0':None,'t0_amount_status':'FAIL','hft':False,'accumulation_emitted':False,'multiple_emitted':False,'watch_at':None}
                    self.db.execute('INSERT OR IGNORE INTO v1_episodes VALUES(?,?,?)',(episode,person,mint))
                if s is not None:
                    amount_predicate=t.get('amount_predicate') or ('USDC_DIRECT_NUMERIC' if t['quote_asset']==USDC else 'UNDETERMINED')
                    if amount_predicate not in {'USDC_DIRECT_NUMERIC','SOL_EVENT_TIME_USDC_VERIFIED','UNDETERMINED'}:
                        raise ValueError('TRADE_AMOUNT_PREDICATE_INVALID')
                    event={'signature':row['signature'],'at':at,'slot':row['slot'],**t,'quote_quantity':quantity(t['quote_amount_raw'],t['quote_decimals']),'amount_predicate':amount_predicate};s['events'].append(event)
                    amount=int(t['token_amount_raw']);current=int(s['current_raw']) if s['current_raw'] is not None else None
                    if t['direction']=='BUY':
                        if current is not None:s['current_raw']=str(current+amount)
                    else:
                        if current is not None and amount<=current:s['current_raw']=str(current-amount)
                        else:s['current_raw']=None
                    if s['current_raw'] is None:s['state']='INVENTORY_UNDETERMINED'
                    elif int(s['current_raw'])==0:s['state']='CLOSED'
                    s['peak_raw']=str(max(int(s['peak_raw']),int(s['current_raw'] or '0')))
                    s['inventory_points'].append({'at':at,'raw':s['current_raw']})
                    m=self.policy['mapping']['FRANK_MULTIPLE_SIGNAL'];recent=[x for x in s['events'] if at-m['hft_window_seconds']<=x['at']<=at]
                    if len(recent)>=m['hft_swaps_min']:s['hft']=True
                    # A proven complete round trip inside the canonical approximate 20m reference.
                    if s['state']=='CLOSED' and at-s['events'][0]['at']<=m['rapid_roundtrip_reference_seconds']:s['hft']=True
                    if t['direction']=='BUY':establish_t0(s,self.policy)
                    clock=self.db.execute("SELECT value FROM v1_meta WHERE key='last_time'").fetchone()
                    evaluated_at=max(at,int(clock[0]) if clock else at)
                    result=self._evaluate(s,evaluated_at,row['signature'],'ACTIVE_TRADE');self._save(s)
                    ids=result['signal_ids'];body={**e,'signal_ids':sorted(set(e.get('signal_ids',[])+ids)),'v1_evaluation':result,'amount_predicate':event['amount_predicate']}
                    self.db.execute('UPDATE signatures SET body=?,alert_state=?,alert_reason=? WHERE wallet=? AND signature=?',(json.dumps(body,sort_keys=True),'YES' if body['signal_ids'] else 'NO','DETERMINISTIC_STAGE_UPGRADE' if ids else 'V1_PREDICATES:'+json.dumps(result['predicates'],sort_keys=True),row['wallet'],row['signature']))
                else:
                    self.db.execute("UPDATE signatures SET alert_reason='V1_SELL_POSITION_HISTORY_UNDETERMINED' WHERE wallet=? AND signature=?",(row['wallet'],row['signature']))
            if t and at is None:self.db.execute("UPDATE signatures SET alert_reason='V1_BLOCK_TIME_UNDETERMINED' WHERE wallet=? AND signature=?",(row['wallet'],row['signature']))
            self.db.execute('INSERT INTO v1_seen VALUES(?,?)',(row['wallet'],row['signature']))
        return result
    def drain(self,*,until=None):
        rows=self.db.execute('SELECT s.* FROM signatures s LEFT JOIN v1_seen v USING(wallet,signature) WHERE v.signature IS NULL ORDER BY s.block_time,s.slot,s.signature').fetchall()
        for row in rows:self.process(row)
        if until is not None:self.tick(until)
        return len(rows)
    def summary(self):
        counts=dict(self.db.execute('SELECT signal_type,count(*) FROM signals GROUP BY signal_type'))
        return {'mode':'DRY_RUN_ONLY' if self.dry_run else 'LIVE','policy_id':self.policy['policy_id'],'policy_hash':POLICY_SHA256,'tokens_evaluated':self.db.execute("SELECT count(DISTINCT json_extract(body,'$.trade.mint')) FROM signatures WHERE json_extract(body,'$.classification')='ACTIVE_TRADE'").fetchone()[0],'episodes_evaluated':self.db.execute('SELECT count(*) FROM v1_episodes').fetchone()[0],'accumulation_trigger_count':counts.get('FRANK_ACCUMULATION_SIGNAL',0),'multiple_trigger_count':counts.get('FRANK_MULTIPLE_SIGNAL',0),'same_stage_duplicate_suppressed':int(self.db.execute("SELECT value FROM v1_meta WHERE key='duplicates_suppressed'").fetchone()[0]),'undetermined_predicate_evaluations':self.db.execute("SELECT count(*) FROM v1_evaluations WHERE body LIKE '%UNDETERMINED%'").fetchone()[0],'unknown_incomplete_blocked':self.db.execute("SELECT count(DISTINCT signature) FROM signatures WHERE json_extract(body,'$.classification')='UNKNOWN_NEEDS_REVIEW' OR alert_reason IN ('V1_SELL_POSITION_HISTORY_UNDETERMINED','V1_BLOCK_TIME_UNDETERMINED') OR signature IN (SELECT signature FROM v1_evaluations WHERE body LIKE '%UNDETERMINED%')").fetchone()[0]}
