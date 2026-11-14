"""Audit a completed independent-read prefix while the parent CA job may run.

Reads the append-only prefix in short SQLite queries; no long read transaction,
source calls, full-job verdict freeze or production write. Outputs stay private.
"""
from pathlib import Path
import sys,json,sqlite3,hashlib,time,argparse,subprocess
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--agent',type=Path,required=True)
p.add_argument('--expected-sha',required=True)
p.add_argument('--checkpoint',type=Path,required=True)
p.add_argument('--producer-sha')
p.add_argument('--output-dir',type=Path,required=True)
a=p.parse_args()
assert subprocess.check_output(['git','-C',str(a.agent),'rev-parse','HEAD']).decode().strip()==a.expected_sha
assert not subprocess.check_output(['git','-C',str(a.agent),'status','--porcelain']).strip()
source=a.checkpoint
assert source.resolve().parent!=a.output_dir.resolve()
context={'source_sha':a.producer_sha or a.expected_sha}
db=sqlite3.connect(source.absolute().as_uri()+'?mode=ro',uri=True)
meta=json.loads(db.execute('select body from metadata').fetchone()[0])
first=db.execute("select seq from reads where json_extract(body,'$.request.channel')='secondary_rpc' limit 1").fetchone()[0]-1
anchor=db.execute('select sha from reads where seq=?',(first-1,)).fetchone()[0] if first else ''
entries=[];head=anchor;offset=first;finished=False
out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
with (out/'reads.jsonl').open('w') as capture:
 while not finished:
  rows=db.execute('select seq,body,sha from reads where seq>=? order by seq limit 128',(offset,)).fetchall()
  assert rows
  for seq,body,sha in rows:
   entry=json.loads(body);q=entry['request']
   if q['channel'] not in {'rpc','secondary_rpc'} or q['operation']!='getMultipleAccounts':finished=True;break
   assert seq==first+len(entries) and hashlib.sha256(body.encode()).hexdigest()==sha and entry['previous_sha']==head
   assert q['channel']==('rpc' if len(entries)%2==0 else 'secondary_rpc') and entry['outcome']=='OK'
   capture.write(json.dumps({'seq':seq,'body':body,'sha':sha})+'\n');entries.append(entry);head=sha
  offset=first+len(entries)
db.close();assert len(entries)%2==0
addresses=[address for e in entries[::2] for address in e['request']['args'][0][0]]
assert addresses[0]==meta['mint'] and len(addresses)==len(set(addresses))
assert all(len(e['request']['args'][0][0])<=10 for e in entries)
events={}
def audit(event,args):
 if event.startswith('socket.'):
  events[event]=events.get(event,0)+1;raise RuntimeError('OFFLINE_NO_SOCKET')
sys.addaudithook(audit)
sys.path.insert(0,str(a.agent))
from mission_agent.meme.independent_check import collect_independent_balance_check
position=[0]
class Replay:
 def __init__(self,channel):self.channel=channel;self.calls=0;self.last_wire_error_code=None
 def call(self,method,params):
  e=entries[position[0]];assert e['request']=={'channel':self.channel,'operation':method,'args':[params],'kwargs':{'ttl':0}}
  position[0]+=1
  if self.channel=='secondary_rpc':self.calls=e['transport_evidence']['wire_used'];self.last_wire_error_code=e['transport_evidence']['last_source_error']
  return e['response']
result=collect_independent_balance_check(meta['mint'],addresses[1:],Replay('rpc'),Replay('secondary_rpc'),full_accounts=True,clock=lambda:entries[position[0]-1]['finished_at'])
assert position[0]==len(entries) and result['provided_account_set_compared'] and result['not_compared']==0
(out/'derived-private.json').write_text(json.dumps(result,indent=2))
receipt={k:result[k] for k in ['status','scope','accounts_compared','requested_addresses','not_compared','matches','differences','missing','batches_completed','secondary_wire_attempts','provided_account_set_compared','primary_slot_range','secondary_slot_range','single_common_slot']}
receipt.update(source_sha=context['source_sha'],producer_source_sha=context['source_sha'],verifier_source_sha=a.expected_sha,first_sequence=first,read_count=len(entries),previous_anchor_sha256=anchor,last_read_sha256=head,raw_capture_sha256=hashlib.sha256((out/'reads.jsonl').read_bytes()).hexdigest(),socket_events=events,whole_job_status_at_snapshot=meta['status'],whole_job_complete=False,secondary_verdict_frozen=False)
(out/'summary.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
