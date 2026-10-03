"""Pure current-run renderer and durable external-delivery handshake. No Gmail client."""
import html
from ..hashing import seal,digest,verify
from .schema import validate_run,epoch
from ..db.connection import transaction

def decision(candidate, run, *, send, now, reasons=None, text='Current evidence review'):
    """TEST fixture constructor only. Live investment decisions come from GPT."""
    if run['namespace']!='TEST':raise ValueError('TEST_DECISION_ONLY')
    return seal({'schema_version':2,'namespace':'TEST','decision_id':'meme:decision:'+digest({'run':run['run_id'],'signal':candidate['signal_id']}),'run_id':run['run_id'],'signal_id':candidate['signal_id'],'signal_type':candidate['signal_family_candidate'],'person_ids':candidate['person_ids'],'mint':candidate['mint'],'decision':'SEND' if send else 'NO_SEND','reason_codes':reasons or ['TEST_REVIEW'],'evidence':['TEST_CURRENT_RUN_EVIDENCE'],'risks':['TEST_ONLY'],'followable_now':bool(send),'confidence':'MEDIUM','decided_at':now,'candidate_age_seconds':max(0,int(epoch(now)-epoch(candidate['first_event_at']))),'text_zh':text,'model_task_version':'TEST_ONLY'})

def accepted_decisions(run, decisions, enrichment, now):
    validate_run(run,namespace=run['namespace']);candidates={c['signal_id']:c for c in run['candidates']}
    if enrichment is None or enrichment.get('run_id')!=run['run_id'] or enrichment.get('status')!='SUCCESS':return []
    if set(enrichment)-{'run_id','status','by_signal'}:raise ValueError('ENRICHMENT_FIELDS')
    if set(enrichment.get('by_signal',{}))-set(candidates):raise ValueError('OLD_ENRICHMENT_SIGNAL')
    selected=[];seen=set()
    for d in decisions:
        verify(d)
        if d.get('schema_version')!=2 or d.get('namespace')!=run['namespace'] or d.get('run_id')!=run['run_id'] or d.get('signal_id') not in candidates:raise ValueError('DECISION_CURRENT_RUN_BINDING')
        c=candidates[d['signal_id']]
        if d['decision_id']!='meme:decision:'+digest({'run':run['run_id'],'signal':c['signal_id']}):raise ValueError('DECISION_IDENTITY')
        if d['signal_id'] in seen:raise ValueError('DUPLICATE_DECISION')
        seen.add(d['signal_id'])
        if d['signal_type']!=c['signal_family_candidate'] or sorted(d['person_ids'])!=c['person_ids'] or d['mint']!=c['mint']:raise ValueError('DECISION_CHAIN_FACT_CONFLICT')
        if d['decision'] not in ('SEND','NO_SEND') or d['confidence'] not in ('HIGH','MEDIUM','LOW') or type(d['followable_now']) is not bool:raise ValueError('DECISION_SCHEMA')
        if not all(isinstance(d[k],list) and all(isinstance(x,str) for x in d[k]) for k in ['reason_codes','evidence','risks']):raise ValueError('DECISION_EVIDENCE_SCHEMA')
        if epoch(d['decided_at'])>epoch(now) or epoch(d['decided_at'])<epoch(run['created_at']):raise ValueError('DECISION_TIME')
        age=max(0,int(epoch(d['decided_at'])-epoch(c['first_event_at'])))
        if type(d['candidate_age_seconds']) is not int or d['candidate_age_seconds']!=age:raise ValueError('DECISION_AGE')
        if d['decision']=='SEND' and d['followable_now'] and d['evidence'] and epoch(now)<epoch(c['expires_at']) and epoch(d['decided_at'])<epoch(c['expires_at']):selected.append((c,d))
    return selected

def render(run, decisions, enrichment, now, *, fail=False):
    selected=accepted_decisions(run,decisions,enrichment,now)
    if not selected:return None
    tokens={}
    for c,d in selected:tokens.setdefault(c['mint'],[]).append((c,d))
    sections={'TOKEN_CONSENSUS':[],'PERSON_PATTERN':[]}
    for mint,rows in sorted(tokens.items()):
        family='TOKEN_CONSENSUS' if any(c['signal_family_candidate']=='TOKEN_CONSENSUS' for c,d in rows) else 'PERSON_PATTERN'
        facts={f['event_id']:f for c,d in rows for f in c['facts']}
        people=sorted({f['person_display_name'] for f in facts.values()});reasons=sorted({r for c,d in rows for r in d['reason_codes']});texts=[d.get('text_zh','') for c,d in rows]
        # Enrichment is keyed and bounded to this run's signal; plain text is always escaped.
        extra=[enrichment.get('by_signal',{}).get(c['signal_id'],'') for c,d in rows]
        if not all(isinstance(t,str) for t in texts+extra):raise ValueError('ENRICHMENT_TEXT')
        sections[family].append('<article data-token="'+digest({'mint':mint})+'"><h3>'+html.escape(mint)+'</h3><p>'+html.escape(' + '.join(people))+'</p><p>'+html.escape('; '.join(reasons))+'</p><p>'+html.escape(' '.join(texts+extra))+'</p><p>'+html.escape(' | '.join(sorted({c['first_event_at'] for c,d in rows})))+'</p><p>'+html.escape('; '.join(sorted({r for c,d in rows for r in d['risks']})))+'</p><pre>'+html.escape('; '.join(f['person_display_name']+': '+f['buy_amount']['quantity']+' token units' for f in facts.values()))+'</pre></article>')
    if fail:raise RuntimeError('RENDER_CRASH_BEFORE_ARTIFACT')
    body=''.join('<section data-family="'+family+'"><h2>'+label+'</h2>'+''.join(sections[family])+'</section>' for family,label in [('TOKEN_CONSENSUS','多人同币 / TOKEN_CONSENSUS'),('PERSON_PATTERN','单人模式 / PERSON_PATTERN')] if sections[family])
    content_hash=digest({'html':body});mid='meme:mail:'+digest({'namespace':run['namespace'],'run_id':run['run_id'],'signal_ids':sorted(c['signal_id'] for c,d in selected)})
    return seal({'schema_version':2,'namespace':run['namespace'],'run_id':run['run_id'],'mail_run_id':mid,'content_hash':content_hash,'html':body,'signal_ids':sorted(c['signal_id'] for c,d in selected),'decision_ids':sorted(d['decision_id'] for c,d in selected),'expires_at':min(c['expires_at'] for c,d in selected)})

class MailOutbox:
    def __init__(self,db):self.db=db
    def prepare(self,run,decisions,enrichment,now):
        artifact=render(run,decisions,enrichment,now)
        # Canonical NO_SEND decisions are durable audit records even with no mail artifact.
        accepted_decisions(run,decisions,{'run_id':run['run_id'],'status':'SUCCESS','by_signal':{}},now)
        from ..hashing import canonical
        with transaction(self.db):
            for d in decisions:
                old=self.db.execute('SELECT body FROM meme_decisions WHERE decision_id=?',(d['decision_id'],)).fetchone()
                body=canonical(d).decode()
                if old and old[0]!=body:raise ValueError('IMMUTABLE_DECISION_CONFLICT')
                self.db.execute('INSERT OR IGNORE INTO meme_decisions VALUES(?,?,?,?)',(d['decision_id'],d['run_id'],d['signal_id'],body))
            if artifact is None:return None
            old=self.db.execute('SELECT content_hash FROM meme_mail_outbox WHERE mail_run_id=?',(artifact['mail_run_id'],)).fetchone()
            if old:
                if old[0]!=artifact['content_hash']:raise ValueError('IMMUTABLE_MAIL_CONFLICT')
                return artifact
            if any(self.db.execute('SELECT 1 FROM meme_mail_signals WHERE signal_id=?',(s,)).fetchone() for s in artifact['signal_ids']):return None
            self.db.execute("INSERT INTO meme_mail_outbox VALUES(?,?,?,?,?,'PENDING',NULL)",(artifact['mail_run_id'],artifact['run_id'],artifact['content_hash'],artifact['expires_at'],canonical(artifact).decode()))
            for s in artifact['signal_ids']:self.db.execute('INSERT INTO meme_mail_signals VALUES(?,?)',(s,artifact['mail_run_id']))
        return artifact
    def claim(self,mid,now):
        with transaction(self.db):
            row=self.db.execute('SELECT * FROM meme_mail_outbox WHERE mail_run_id=?',(mid,)).fetchone()
            if not row:return False
            if epoch(now)>=epoch(row['expires_at']):
                self.db.execute("UPDATE meme_mail_outbox SET state='EXPIRED_NO_SEND' WHERE mail_run_id=? AND state='PENDING'",(mid,));return False
            return self.db.execute("UPDATE meme_mail_outbox SET state='INFLIGHT' WHERE mail_run_id=? AND state='PENDING'",(mid,)).rowcount==1
    def simulate_delivery(self,mid,provider,now,*,crash=False):
        from ..hashing import loads
        row=self.db.execute('SELECT * FROM meme_mail_outbox WHERE mail_run_id=?',(mid,)).fetchone()
        if not row or loads(row['body'])['namespace']!='TEST' or getattr(provider,'namespace',None)!='TEST':raise ValueError('NO_REAL_GMAIL_SENDER')
        if row['state'] in ('INFLIGHT','UNCERTAIN'):
            matches=provider.search_sent(mid,row['content_hash'])
            valid=[m for m in matches if provider.readback(m,mid,row['content_hash'])]
            with transaction(self.db):
                if len(matches)==len(valid)==1:self.db.execute("UPDATE meme_mail_outbox SET state='SENT',receipt=? WHERE mail_run_id=?",(valid[0],mid))
                else:self.db.execute("UPDATE meme_mail_outbox SET state='UNCERTAIN' WHERE mail_run_id=?",(mid,))
            return
        if not self.claim(mid,now):return
        message=provider.accept(mid,row['content_hash'],loads(row['body']))
        if crash:raise SystemExit('ACCEPTED_LOCAL_SENT_LOST')
        with transaction(self.db):self.db.execute("UPDATE meme_mail_outbox SET state='UNCERTAIN',receipt=? WHERE mail_run_id=?",(message,mid))
        self.simulate_delivery(mid,provider,now)
