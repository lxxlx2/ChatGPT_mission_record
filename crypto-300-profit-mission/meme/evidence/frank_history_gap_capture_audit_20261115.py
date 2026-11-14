"""Audit every original holder-classification gap from immutable private RPC reads.

No source traffic or report mutation. Outputs use hashes for case identities;
the optional private results file stays beside the supplied private capture.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

sys.dont_write_bytecode=True
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--agent',type=Path,required=True)
p.add_argument('--expected-sha',required=True)
p.add_argument('--capture',type=Path,required=True)
p.add_argument('--summary',type=Path,required=True)
p.add_argument('--private-results',type=Path)
a=p.parse_args()
assert not a.summary.resolve().is_relative_to(a.capture.resolve())
assert a.private_results is None or not a.private_results.resolve().is_relative_to(a.capture.resolve())
assert subprocess.check_output(['git','-C',str(a.agent),'rev-parse','HEAD'],text=True).strip()==a.expected_sha
assert not subprocess.check_output(['git','-C',str(a.agent),'status','--porcelain']).strip()
events=Counter()
def deny(event,args):
    if event.startswith('socket.'):
        events[event]+=1
        raise AssertionError('OFFLINE_NO_SOCKET')
sys.addaudithook(deny)
sys.path.insert(0,str(a.agent))
from mission_agent.signals.classifier import classify
from mission_agent.meme.history_classification import resolve_history_classification

def sha(value):return hashlib.sha256(value).hexdigest()
def file_sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

raw=(a.capture/'report.json').read_bytes();report=json.loads(raw)
done=json.loads((a.capture/'done.json').read_text())
assert done['status']=='DONE' and done['report_sha256']==sha(raw)
assert done['ca_job_id']==report['ca_job_id'] and done['mint']==report['mint']
cp=a.capture/'checkpoint.sqlite';cp_sha=file_sha(cp)
errors=[x for x in report['transaction_errors'] if x.get('phase')=='holder_classify' and x.get('error')=='CLASSIFICATION_UNRESOLVED']
contexts={(x['owner'],x['signature']) for x in errors};wanted={sig for _,sig in contexts};transactions={};refs={}
db=sqlite3.connect(cp.absolute().as_uri()+'?mode=ro',uri=True)
body,digest=db.execute('select body,sha from metadata where id=1').fetchone();assert sha(body.encode())==digest
meta=json.loads(body);assert meta['mint']==report['mint'] and meta['job_id']==report['ca_job_id']
head='';count=0
for seq,body,digest in db.execute('select seq,body,sha from reads order by seq'):
    e=json.loads(body);assert seq==count and sha(body.encode())==digest and e['previous_sha']==head
    count+=1;head=digest;q=e['request']
    if q['channel']=='rpc' and q['operation']=='getTransaction' and q['args'][0][0] in wanted and e['outcome']=='OK':
        sig=q['args'][0][0]
        if sig in transactions:assert transactions[sig]==e['response']
        transactions[sig]=e['response'];refs[sig]={'seq':seq,'source_read_sha256':digest}
assert head==meta['head'] and count==meta['entry_count'] and set(transactions)==wanted;db.close()
rows=[];private=[]
for owner,sig in sorted(contexts):
    tx=transactions[sig];strict=classify(sig,tx,owner)
    assert strict['classification']=='UNKNOWN_NEEDS_REVIEW'
    result=resolve_history_classification(strict,sig,tx,owner,report['mint'])
    assert classify(sig,tx,owner)==strict
    category=result.get('history_resolution')
    if category is None:
        category=('MULTIPLE_CHANGED_ASSETS' if len((strict.get('classification_details') or {}).get('changed_assets',[]))>2
                  else 'NO_SINGLE_BOUND_MARKET_ROUTE' if strict['classification_reason']=='AMBIGUOUS_USER_EXCHANGE_ASSETS'
                  else 'INSUFFICIENT_RETAINED_EXCHANGE_PROCEEDS')
    row={'owner_sha256':sha(owner.encode()),'signature_sha256':sha(sig.encode()),'before':strict['classification_reason'],
         'after':result['classification'],'category':category,'reason':result['classification_reason'],**refs[sig]}
    rows.append(row);private.append({'owner':owner,'signature':sig,'result':result})
assert not events and file_sha(cp)==cp_sha
if a.private_results:
    assert a.private_results.resolve() not in {cp.resolve(),(a.capture/'report.json').resolve(),(a.capture/'done.json').resolve()}
    a.private_results.write_text(json.dumps(private,indent=2))
summary={'source_sha':a.expected_sha,'report_sha256':sha(raw),'checkpoint_sha256':cp_sha,'checkpoint_chain_reads':count,
         'observations':len(errors),'unique_owner_signatures':len(contexts),'raw_transactions':len(transactions),
         'classification_counts':dict(Counter(r['after'] for r in rows)),'categories':dict(Counter(r['category'] for r in rows)),
         'default_shared_classifier_unchanged':True,'socket_events':dict(events),'checkpoint_original_hash_unchanged':True,'rows':rows}
assert a.summary.resolve() not in {cp.resolve(),(a.capture/'report.json').resolve(),(a.capture/'done.json').resolve()}
a.summary.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='rows'}))
