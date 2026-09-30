"""Durable synthetic provider, independent of client receipt transactions."""
from datetime import timedelta
from ..clock import stamp,parse_utc
from ..db.connection import connect,transaction

MODES=frozenset({'SUCCESS','TIMEOUT_BEFORE_SEND','TIMEOUT_AFTER_SEND','SENT_BUT_READBACK_MISS',
                 'SENT_BUT_RECEIPT_FAIL','DUPLICATE_SENT_RESULT','READBACK_RECOVERS_LATER'})


class MockGmail:
    def __init__(self,path,clock):
        self.db=connect(path);self.clock=clock
        self.db.execute('CREATE TABLE IF NOT EXISTS sent(id INTEGER PRIMARY KEY,event_id TEXT NOT NULL,subject TEXT NOT NULL,available_at TEXT NOT NULL,readable_at TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS calls(id INTEGER PRIMARY KEY,event_id TEXT NOT NULL,mode TEXT NOT NULL)')

    def close(self):
        self.db.close()

    def send(self,event_id,mode='SUCCESS',search_delay=0):
        if mode not in MODES or search_delay<0:
            raise ValueError('invalid mock mode/delay')
        with transaction(self.db):
            self.db.execute('INSERT INTO calls(event_id,mode) VALUES(?,?)',(event_id,mode))
        if mode=='TIMEOUT_BEFORE_SEND':
            raise TimeoutError('mock before acceptance')
        from ..storage import admit
        from pathlib import Path
        root=Path(self.db.execute('PRAGMA database_list').fetchone()[2]).parent
        admit(root,65536)
        subject=f'[MISSION:{event_id}] Synthetic canary'
        with transaction(self.db):
            visible=stamp(self.clock.now()+timedelta(seconds=search_delay))
            readable=stamp(self.clock.now()+timedelta(seconds=120 if mode in ('SENT_BUT_READBACK_MISS','READBACK_RECOVERS_LATER') else 0))
            cursor=self.db.execute('INSERT INTO sent(event_id,subject,available_at,readable_at) VALUES(?,?,?,?)',(event_id,subject,visible,readable))
            id=f'mock-{cursor.lastrowid}'
            if mode=='DUPLICATE_SENT_RESULT':
                self.db.execute('INSERT INTO sent(event_id,subject,available_at,readable_at) VALUES(?,?,?,?)',(event_id,subject,visible,readable))
        if mode=='TIMEOUT_AFTER_SEND':
            raise TimeoutError('mock after acceptance')
        return id

    def search_sent(self,event_id):
        rows=self.db.execute('SELECT * FROM sent WHERE event_id=? AND available_at<=? ORDER BY id',(event_id,stamp(self.clock.now()))).fetchall()
        return [f'mock-{r["id"]}' for r in rows if f'[MISSION:{event_id}]' in r['subject']]

    def readback(self,provider_id,event_id):
        try:id=int(provider_id.removeprefix('mock-'))
        except (ValueError,AttributeError):return None
        row=self.db.execute('SELECT * FROM sent WHERE id=?',(id,)).fetchone()
        if row is None or self.clock.now()<parse_utc(row['readable_at']):
            return None
        if row['event_id']!=event_id or f'[MISSION:{event_id}]' not in row['subject']:
            return None
        return {'provider_message_id':provider_id,'event_id':event_id,'labels':['SENT'],'subject':row['subject']}

    def count(self,event_id=None):
        return self.db.execute('SELECT COUNT(*) FROM sent'+(' WHERE event_id=?' if event_id else ''),((event_id,) if event_id else ())).fetchone()[0]

    def calls(self,event_id):
        return self.db.execute('SELECT COUNT(*) FROM calls WHERE event_id=?',(event_id,)).fetchone()[0]
