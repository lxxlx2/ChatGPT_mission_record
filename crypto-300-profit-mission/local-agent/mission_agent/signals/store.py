"""Independent SQLite audit ledger; never edits the legacy scanner database."""
import json
from datetime import datetime, timezone
from decimal import Decimal
from ..db.connection import connect, transaction
from ..hashing import digest

def now(): return datetime.now(timezone.utc).isoformat()

def quantity(raw,decimals): return str(Decimal(raw)/(Decimal(10)**decimals))

class Ledger:
    def __init__(self,path):
        self.db=connect(path)
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS signatures(wallet TEXT,signature TEXT,person_id TEXT,slot INTEGER,block_time INTEGER,seen_at TEXT,classified_at TEXT,raw_hash TEXT,raw_reference TEXT,body TEXT,alert_state TEXT NOT NULL,alert_reason TEXT NOT NULL,PRIMARY KEY(wallet,signature));
        CREATE TABLE IF NOT EXISTS cursors(wallet TEXT PRIMARY KEY,signature TEXT,slot INTEGER,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS positions(person_id TEXT,mint TEXT,body TEXT,PRIMARY KEY(person_id,mint));
        CREATE TABLE IF NOT EXISTS trades(wallet TEXT,signature TEXT,mint TEXT,episode_id TEXT,block_time INTEGER,side TEXT,body TEXT,PRIMARY KEY(wallet,signature));
        CREATE TABLE IF NOT EXISTS signals(signal_id TEXT PRIMARY KEY,person_id TEXT,mint TEXT,episode_id TEXT,signal_type TEXT,stage TEXT,created_at TEXT,content_hash TEXT,body TEXT,UNIQUE(person_id,mint,episode_id,signal_type,stage));
        CREATE TABLE IF NOT EXISTS outbox(signal_id TEXT,channel TEXT,status TEXT,attempts INTEGER DEFAULT 0,last_error TEXT,receipt TEXT,PRIMARY KEY(signal_id,channel));
        CREATE TABLE IF NOT EXISTS health(wallet TEXT PRIMARY KEY,body TEXT);
        ''')
    def cursor(self,wallet):
        r=self.db.execute('SELECT * FROM cursors WHERE wallet=?',(wallet,)).fetchone()
        return dict(r) if r else None
    def checkpoint(self,wallet,signature,slot):
        with transaction(self.db):
            if self.cursor(wallet):raise ValueError('CURSOR_ALREADY_INITIALIZED')
            self.db.execute('INSERT INTO cursors VALUES(?,?,?,?)',(wallet,signature,slot,now()))
    def put(self,person,e,raw_hash,raw_reference,*,advance=False,dry_run=True,stages=()):
        wallet,sig=e['wallet'],e['signature']
        with transaction(self.db):
            old=self.db.execute('SELECT raw_hash FROM signatures WHERE wallet=? AND signature=?',(wallet,sig)).fetchone()
            if old:
                if old[0]!=raw_hash:raise ValueError('IMMUTABLE_RAW_CONFLICT')
                return False
            t=e.get('trade');position=None;signals=[]
            if t:
                r=self.db.execute('SELECT body FROM positions WHERE person_id=? AND mint=?',(person,t['mint'])).fetchone()
                p=json.loads(r[0]) if r else {'person_id':person,'mint':t['mint'],'state':'NONE','episode_id':None,'episode_number':0,'first_buy_at':None,'last_buy_at':None,'buy_count':0,'sell_count':0,'gross_token_bought':'0','gross_token_sold':'0','gross_quote_spent':{},'gross_quote_received':{},'current_token_position':'0','last_trade_signature':None,'history_complete':False}
                before=int(p['current_token_position']);amount=int(t['token_amount_raw'])
                if t['direction']=='BUY':
                    side='ADD' if p['state']=='OPEN' else 'REENTRY' if p['state']=='CLOSED' else 'BUY'
                    if p['state']!='OPEN':
                        episode=p['episode_number']+1
                        p.update(episode_number=episode,episode_id=digest({'person':person,'mint':t['mint'],'first':sig}),first_buy_at=e['block_time'],last_buy_at=None,buy_count=0,sell_count=0,gross_token_bought='0',gross_token_sold='0',gross_quote_spent={},gross_quote_received={},current_token_position='0')
                        before=0
                    p.update(state='OPEN',last_buy_at=e['block_time'],buy_count=p['buy_count']+1,gross_token_bought=str(int(p['gross_token_bought'])+amount),current_token_position=str(before+amount))
                    q=p['gross_quote_spent']
                else:
                    # A sell in incomplete prehistory must not invent an entry or an episode.
                    if p['state']!='OPEN' or amount>before:
                        e={**e,'classification_reason':'SIGNED_DEX_SWAP_POSITION_HISTORY_INCOMPLETE'}
                        unresolved={**t,'side':'SELL_POSITION_UNRESOLVED','position_before_raw':None,'position_after_raw':None,'episode_id':None,'reason':'INCOMPLETE_PREHISTORY_NO_EXIT_INFERENCE'}
                        self.db.execute('INSERT INTO trades VALUES(?,?,?,?,?,?,?)',(wallet,sig,t['mint'],None,e['block_time'],'SELL_POSITION_UNRESOLVED',json.dumps(unresolved,sort_keys=True)))
                        t=None
                    else:
                        remaining=before-amount;side='EXIT' if remaining==0 else 'SELL'
                        p.update(state='CLOSED' if remaining==0 else 'OPEN',sell_count=p['sell_count']+1,gross_token_sold=str(int(p['gross_token_sold'])+amount),current_token_position=str(remaining));q=p['gross_quote_received']
                if t:
                    q[t['quote_asset']]=str(Decimal(q.get(t['quote_asset'],'0'))+Decimal(quantity(t['quote_amount_raw'],t['quote_decimals'])))
                    p['last_trade_signature']=sig;position=p
                    trade={**t,'side':side,'position_before_raw':str(before),'position_after_raw':p['current_token_position'],'episode_id':p['episode_id']}
                    self.db.execute('INSERT INTO trades VALUES(?,?,?,?,?,?,?)',(wallet,sig,t['mint'],p['episode_id'],e['block_time'],side,json.dumps(trade,sort_keys=True)))
                    self.db.execute('INSERT OR REPLACE INTO positions VALUES(?,?,?)',(person,t['mint'],json.dumps(p,sort_keys=True)))
                    for stage in stages:
                        stype=stage['signal_type']; sid=digest({'person_id':person,'mint':t['mint'],'episode_id':p['episode_id'],'signal_type':stype,'stage':stage['stage']})
                        body={'signal_id':sid,'person_id':person,'mint':t['mint'],'episode_id':p['episode_id'],'signal_type':stype,'stage':stage['stage'],'triggered_at':e['block_time'],'latest_trade_signature':sig,'latest_buy':quantity(t['token_amount_raw'],t['token_decimals']),'latest_quote_amount':quantity(t['quote_amount_raw'],t['quote_decimals']),'quote_asset':t['quote_asset'],'position':p,'reason_codes':stage['reason_codes'],'usd':'unavailable'}
                        inserted=self.db.execute('INSERT OR IGNORE INTO signals VALUES(?,?,?,?,?,?,?,?,?)',(sid,person,t['mint'],p['episode_id'],stype,stage['stage'],now(),digest(body),json.dumps(body,sort_keys=True))).rowcount
                        if inserted:
                            signals.append(sid)
                            for channel in (['local','gmail'] if stype=='FRANK_MULTIPLE_SIGNAL' else ['local']):
                                self.db.execute('INSERT INTO outbox(signal_id,channel,status) VALUES(?,?,?)',(sid,channel,'DRY_RUN_AUDIT' if dry_run else 'PENDING'))
            body={**e,'person_id':person,'position_change':position,'signal_ids':signals}
            reason=e['classification_reason'] if not t else 'MODEL_NOT_QUALIFIED_OR_SAME_STAGE'
            if signals:reason='DETERMINISTIC_STAGE_UPGRADE'
            self.db.execute('INSERT INTO signatures VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(wallet,sig,person,e['slot'],e['block_time'],now(),now(),raw_hash,raw_reference,json.dumps(body,sort_keys=True),'YES' if signals else 'NO',reason))
            if advance:
                current=self.cursor(wallet)
                if current and e['slot']<current['slot']:raise ValueError('CURSOR_BACKWARD')
                self.db.execute('INSERT OR REPLACE INTO cursors VALUES(?,?,?,?)',(wallet,sig,e['slot'],now()))
        return True
    def audit(self,last=50):
        return [dict(r) for r in self.db.execute('SELECT signature,block_time,alert_state,alert_reason,body FROM signatures ORDER BY slot DESC,signature DESC LIMIT ?',(last,))]
    def inspect(self,sig):
        rows=[]
        for r in self.db.execute('SELECT * FROM signatures WHERE signature=?',(sig,)):
            item=dict(r);item['body']=json.loads(item['body']);item['delivery_state']=[dict(x) for x in self.db.execute('SELECT * FROM outbox WHERE signal_id IN (SELECT signal_id FROM signals WHERE json_extract(body,\'$.latest_trade_signature\')=?)',(sig,))];rows.append(item)
        return rows
