"""Replay the private probe capture against a fixed source with network denied.

Verifies every request in order, including cache TTL behavior. A stopped capture
ends with the same source failure and writes only private partial evidence.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import sys

os.umask(0o077)
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True);p.add_argument('--capture',type=Path,required=True)
p.add_argument('--seed-cache',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
a.output.mkdir(mode=0o700)
attempted_network=0
def deny(*args,**kwargs):
    global attempted_network
    attempted_network+=1
    raise RuntimeError('OFFLINE_NETWORK_DENIED')
socket.socket.connect=socket.socket.connect_ex=socket.create_connection=socket.getaddrinfo=deny
sys.path.insert(0,str(a.source))
from mission_agent.meme import cluster as c
from mission_agent.mission_control.server import CLUSTER_PRESETS
def digest(data):return hashlib.sha256(data).hexdigest()
def key(method,params):return json.dumps([method,params],sort_keys=True,separators=(',',':'))
receipt=json.loads((a.capture/'result.json').read_bytes())
stopped=receipt['status']=='STOPPED'
class CapturedSourceStop(BaseException):pass
assert receipt['original_seed_unchanged'] and receipt['seed_cache_sha256']==digest(a.seed_cache.read_bytes())
manifest_bytes=(a.capture/'wire-manifest.json').read_bytes()
assert digest(manifest_bytes)==receipt['manifest_sha256']
entries=json.loads(manifest_bytes);responses=[]
for e in entries:
    request=(a.capture/'raw'/f'{e["ordinal"]:04d}-request.json').read_bytes()
    body=(a.capture/'raw'/f'{e["ordinal"]:04d}-response.bin').read_bytes()
    assert digest(request)==e['request_sha256'] and digest(body)==e['response_sha256']
    assert e['body_within_limit']
    req=json.loads(request);value=json.loads(body)
    assert value.get('id')==req['id']
    if e['http_status']==200:
        assert 'result' in value and not value.get('error')
    else:
        assert stopped and e==entries[-1] and value.get('error')
    responses.append((request,body,e))
db=sqlite3.connect(a.seed_cache.resolve().as_uri()+'?mode=ro',uri=True)
for body,expires,body_hash,cache_key in db.execute("SELECT body,expires_at,content_hash,key FROM rpc_cache WHERE method='getTransaction'"):
    value=json.loads(body)
    assert c._hash(value)==body_hash
db.close()
initial=datetime.fromisoformat(receipt['started_at_utc']).timestamp()
class Clock:
    seconds=0.
    def epoch(self):return initial+self.seconds
    def monotonic(self):return self.seconds
    def sleep(self,seconds):self.seconds+=max(0,float(seconds))
clock=Clock();c.time.time=clock.epoch;c.time.monotonic=clock.monotonic;c.time.sleep=clock.sleep
seed=sqlite3.connect(a.seed_cache.resolve().as_uri()+'?mode=ro',uri=True)
copy=sqlite3.connect(a.output/'cache.sqlite');seed.backup(copy);seed.close()
copy.execute("DELETE FROM rpc_cache WHERE method != 'getTransaction'");copy.commit();copy.close()
cache=c.RpcCache(a.output/'cache.sqlite');position=0
class Response:
    def __init__(self,body):self.body=body
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,limit=None):return self.body if limit is None else self.body[:limit]
def captured(request,timeout=None):
    global position
    expected,body,e=responses[position]
    assert request.data==expected and request.full_url=='https://captured.invalid/rpc'
    clock.seconds=max(clock.seconds,datetime.fromisoformat(e['started_at_utc']).timestamp()-initial)+e['elapsed_seconds']
    position+=1
    if e['http_status']!=200:raise CapturedSourceStop('SAME_FIRST_SOURCE_FAILURE')
    return Response(body)
rpc=c.SolanaReadOnlyRPC(endpoint='https://captured.invalid/rpc',fallback_endpoints=[],open_url=captured,
                       cache=cache,sleep=clock.sleep,monotonic=clock.monotonic,max_wire_attempts=1200,max_elapsed_seconds=1800)
opts=dict(CLUSTER_PRESETS['standard'])
opts.update(enumerate_holder_ranks=False,read_pool_vaults=False,audit_holder_binary=False,
            market_client=None,independent_market_client=None,narrative_client=None,
            compare_market_sources=False,collect_narrative=False)
mint=json.loads(responses[0][0])['params'][0]
collector=c.WalletClusterAnalyzer(mint,rpc=rpc,
    special_registry=c.load_registry(a.source/'config/meme_special_addresses.json'),**opts)
report=None
try:report=collector.analyze()
except CapturedSourceStop:
    assert stopped and position==len(entries)
if stopped:
    assert report is None and not (a.capture/'report.json').exists()
    partial={'scope':'STOPPED_CAPTURE_PREFIX_NOT_A_SUCCESS_REPORT',
             'snapshot_slots':collector._snapshot_slots,
             'planned_adaptive_owners':collector.adaptive_deepened_owners,
             'history_attempts':collector.history_attempts,'history_windows':list(collector.history_coverage.values()),
             'trades':collector.trades,'funding':collector.funding,'consolidations':collector.consolidations,
             'edges':collector.edges,'transaction_errors':collector.tx_errors}
    (a.output/'partial-evidence.json').write_text(json.dumps(partial,ensure_ascii=False,indent=2)+'\n')
else:
    actual=json.loads((a.capture/'report.json').read_bytes())
    assert digest((a.capture/'report.json').read_bytes())==receipt['report_sha256']
    rpc.assert_can_publish();assert position==len(entries)
    left=json.loads(json.dumps(report));right=json.loads(json.dumps(actual))
    for value in (left,right):
        value.pop('observed_at',None)
        value['coverage'].pop('rpc_elapsed_seconds',None)
    assert left==right,'REPLAY_REPORT_MISMATCH'
cache.close()
if report is not None:(a.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
result={'status':'PASS_STOPPED_PREFIX_REPLAY' if stopped else 'PASS','mode':'STRICT_REQUEST_SEQUENCE',
        'actual_network_attempts':attempted_network,'validated_capture_entries':len(entries),
        'replayed_wire_requests':position,'cache_hits':rpc.cache_hits,
        'capture_manifest_sha256':receipt['manifest_sha256'],'live_report_sha256':receipt['report_sha256'],
        'replay_report_sha256':digest((a.output/'report.json').read_bytes()) if report else None,
        'partial_evidence_sha256':digest((a.output/'partial-evidence.json').read_bytes()) if stopped else None,
        'source_stop_reproduced':stopped,'success_report_written':report is not None,
        'excluded_volatile_fields':[] if stopped else ['observed_at','coverage.rpc_elapsed_seconds'],
        'history_complete':False,'real_rpc':0}
(a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
