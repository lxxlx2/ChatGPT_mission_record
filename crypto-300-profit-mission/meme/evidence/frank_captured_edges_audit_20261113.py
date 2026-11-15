"""Check this captured edge cohort against raw successful parsed instructions.

No source calls. Registry labels are checked against configuration, not independently
attested identities. Relation evidence is never a common-control proof.
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
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
assert subprocess.check_output(['git','-C',str(a.agent),'rev-parse','HEAD']).decode().strip()==a.expected_sha
assert not subprocess.check_output(['git','-C',str(a.agent),'status','--porcelain','--','mission_agent','config']).strip()
assert a.output.resolve() not in {(a.capture/n).resolve() for n in ['report.json','checkpoint.sqlite','status.json','done.json']}
socket_events={}
def audit(event,args):
    if event.startswith('socket.'):
        socket_events[event]=socket_events.get(event,0)+1
        raise RuntimeError('OFFLINE_NO_SOCKET')
sys.addaudithook(audit)
sys.path.insert(0,str(a.agent))
from mission_agent.frank.parser import _program_id
from mission_agent.meme.cluster import TOKEN_PROGRAMS

def digest(data):return hashlib.sha256(data).hexdigest()
raw=(a.capture/'report.json').read_bytes();r=json.loads(raw)
cp=a.capture/'checkpoint.sqlite';cp_sha=digest(cp.read_bytes())
db=sqlite3.connect(cp.absolute().as_uri()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON')
body,sha=db.execute('SELECT body,sha FROM metadata WHERE id=1').fetchone();assert digest(body.encode())==sha
meta=json.loads(body);head='';count=0;tx={}
for seq,body,sha in db.execute('SELECT seq,body,sha FROM reads ORDER BY seq'):
    e=json.loads(body);assert seq==count and digest(body.encode())==sha and e['previous_sha']==head
    head=sha;count+=1;q=e['request']
    if q['operation']=='getTransaction' and e['outcome']=='OK' and isinstance(e['response'],dict):
        sig=q['args'][0][0];value=e['response']
        if sig in tx:assert tx[sig]==value
        tx[sig]=value
assert head==meta['head'] and count==meta['entry_count'];db.close()

def movements(sig):
    t=tx[sig];m=t['meta'];assert 'err' in m and m['err'] is None
    assert t['transaction']['signatures'][0]==sig
    keys=[k['pubkey'] for k in t['transaction']['message']['accountKeys']]
    accounts={}
    for b in m['preTokenBalances']+m['postTokenBalances']:
        key=keys[b['accountIndex']];identity=(b['owner'],b['mint'])
        assert key not in accounts or accounts[key]==identity
        accounts[key]=identity
    ixs=list(t['transaction']['message']['instructions'])
    for group in m['innerInstructions']:ixs+=group['instructions']
    moves=[]
    for ix in ixs:
        parsed=ix.get('parsed');info=parsed.get('info') if isinstance(parsed,dict) else None
        if not isinstance(info,dict):continue
        program=_program_id(ix,keys);kind=parsed.get('type')
        if program=='11111111111111111111111111111111' and kind=='transfer':
            moves.append((info['source'],info['destination'],'SOL',str(info['lamports'])))
        elif program in TOKEN_PROGRAMS and kind in {'transfer','transferChecked'}:
            src=accounts.get(info.get('source'));dst=accounts.get(info.get('destination'))
            if src and dst and src[1]==dst[1]:
                amount=info.get('amount',(info.get('tokenAmount') or {}).get('amount'))
                if amount is not None:moves.append((src[0],dst[0],src[1],str(amount)))
    return moves

moves={sig:movements(sig) for sig in {e['signature'] for e in r['edges'] if e['signature']!='MULTI_TX'} | {c['signature'] for c in r['consolidation_evidence']}}
for c in r['consolidation_evidence']:
    assert (c['source_owner'],c['destination_owner'],c['mint'],str(c['amount_raw'])) in moves[c['signature']]
    assert tx[c['signature']]['blockTime']==c['block_time']
registry_bytes=(a.agent/'config/meme_special_addresses.json').read_bytes();registry=json.loads(registry_bytes)
scoped=(registry.get('tokens',{}).get(r['mint']) or {}).get('addresses',{})
def role(who):return (scoped.get(who) or registry.get('addresses',{}).get(who) or {}).get('role')
public={'PUBLIC_INFRA','PUBLIC_PROGRAM','ROUTER','BRIDGE','AMM_POOL','PROTOCOL_VAULT','CEX'}
strong={'EOA','DEV','CREATOR','TREASURY'}
keys=[json.dumps(e,sort_keys=True,separators=(',',':')) for e in r['edges']];assert len(keys)==len(set(keys))
counts=Counter()
for e in r['edges']:
    pair=(e['a'],e['b']);assert pair[0]<pair[1]
    kind=e['type']
    if kind in {'DIRECT_TOKEN_TRANSFER','DIRECT_QUOTE_TRANSFER'}:
        mint=r['mint'] if kind=='DIRECT_TOKEN_TRANSFER' else e['asset']
        assert any(tuple(sorted((s,d)))==pair and m==mint and amount==str(e['amount_raw']) for s,d,m,amount in moves[e['signature']])
        assert tx[e['signature']]['blockTime']==e['block_time']
    elif kind=='COMMON_CONSOLIDATION_UNRESOLVED':
        rows=[c for c in r['consolidation_evidence'] if c['destination_owner']==e['destination']]
        assert all(any(c['source_owner']==owner for c in rows) for owner in pair)
        assert e['signature'] in {c['signature'] for c in rows}
        assert role(e['destination']) not in public|strong
    elif kind in {'COMMON_SIGNER_UNRESOLVED','SHARED_INFRA'} and e['signature']=='MULTI_TX':
        for owner in pair:
            rows=[t for t in r['trade_evidence'] if t['owner']==owner and e['signer'] in t.get('signers',[])]
            assert rows
            assert any(any(k['pubkey']==e['signer'] and k['signer'] is True for k in tx[t['signature']]['transaction']['message']['accountKeys']) for t in rows)
        assert role(e['signer']) in public if kind=='SHARED_INFRA' else role(e['signer']) not in public|strong
    else:raise AssertionError('UNSUPPORTED_EDGE_COHORT')
    counts[kind]+=1
assert digest(cp.read_bytes())==cp_sha and not socket_events
out={'source_sha':a.expected_sha,'report_sha256':digest(raw),'checkpoint_sha256':cp_sha,'checkpoint_chain_reads':count,
     'edge_count':len(keys),'edge_types':dict(counts),'raw_instruction_supported_direct_edges':sum(counts[k] for k in ['DIRECT_TOKEN_TRANSFER','DIRECT_QUOTE_TRANSFER']),
     'multi_evidence_supported_derived_edges':sum(counts.values())-sum(counts[k] for k in ['DIRECT_TOKEN_TRANSFER','DIRECT_QUOTE_TRANSFER']),
     'consolidation_raw_rows_checked':len(r['consolidation_evidence']),'duplicate_edge_records':0,'invalid_references':0,
     'registry_sha256':digest(registry_bytes),'registry_real_world_identity_independently_verified':False,
     'common_control_or_full_history_claimed':False,'socket_events':socket_events,'checkpoint_hash_unchanged':True,'verdict':'PASS_FOR_THIS_CAPTURED_COHORT'}
a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
