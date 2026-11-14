"""One authorized read-only GPA attempt from an existing frozen request.

Default only checks inputs. Explicit execution uses the first endpoint in the
existing Dashboard RPC configuration: no retry, redirect, fallback or new key.
Raw bodies/paths remain private; printed output contains counts and hashes only.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SHA='7aaf96a1524a9c6ae26749dae80a945097ac111e'
REPORT='1eac77caa84e5dc4d5c39cfb6a547a97358ffd437e10447a172dc42ef2498f51'
HEAD='066afaa66a3898305ab24fc5fbbc43bb26baffe714fd80db51fb69009d9809b0'
os.umask(0o077)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('agent','capture','rpc-config','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--execute-authorized-once',action='store_true');a=p.parse_args()
    assert subprocess.check_output(['git','-C',str(a.agent),'rev-parse','HEAD'],text=True).strip()==SHA
    sys.path.insert(0,str(a.agent.resolve()))
    from mission_agent.meme.holder_ranks import valid_enumeration_query,MAX_RESPONSE_BYTES
    report_bytes=(a.capture/'report.json').read_bytes();assert hashlib.sha256(report_bytes).hexdigest()==REPORT
    report=json.loads(report_bytes)
    with sqlite3.connect((a.capture/'checkpoint.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
        meta=json.loads(db.execute('SELECT body FROM metadata WHERE id=1').fetchone()[0]);assert meta['head']==HEAD
        entries=[json.loads(row[0]) for row in db.execute('SELECT body FROM reads ORDER BY seq')]
    previous=''
    for entry in entries:
        assert entry['previous_sha']==previous
        previous=hashlib.sha256(json.dumps(entry,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert previous==HEAD and len(entries)==meta['entry_count']==798
    requests=[e['request'] for e in entries if e['request']['channel']=='rpc' and e['request']['operation']=='getProgramAccounts']
    assert len(requests)==1;params=requests[0]['args'][0]
    assert valid_enumeration_query(params) and params[1]['filters'][-1]['memcmp']['bytes']==report['mint']
    endpoints=[x.strip() for x in a.rpc_config.read_text().strip().split(',') if x.strip()];assert endpoints
    endpoint=endpoints[0];url=urllib.parse.urlsplit(endpoint)
    assert url.scheme=='https' and url.hostname and not url.fragment
    body=json.dumps({'jsonrpc':'2.0','id':1,'method':'getProgramAccounts','params':params},separators=(',',':')).encode()
    result={'mode':'INPUT_PREFLIGHT','request_sha256':hashlib.sha256(body).hexdigest(),'attempts':0,'retries':0,'redirects_followed':0,'first_existing_configured_endpoint_only':True,'original_request_parameters_unchanged':True,'response_limit_bytes':MAX_RESPONSE_BYTES,'timeout_seconds':20,'new_CA_POST':0}
    if not a.execute_authorized_once:print(json.dumps(result));return
    a.output.mkdir(mode=0o700,parents=True,exist_ok=False)
    (a.output/'request.json').write_bytes(body)
    (a.output/'attempt-started.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'attempts':1})+'\n')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):raise RuntimeError('RPC_REDIRECT_FORBIDDEN')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    request=urllib.request.Request(endpoint,data=body,headers={'Content-Type':'application/json','User-Agent':'mission-meme-cluster/2'})
    started=time.monotonic();data=b'';status=None;headers={};transport_error=None
    try:
        try:response=opener.open(request,timeout=20)
        except urllib.error.HTTPError as error:response=error
        with response:
            status=response.status;headers=dict(response.headers);data=response.read(MAX_RESPONSE_BYTES+1)
    except Exception as error:transport_error=type(error).__name__
    complete=transport_error is None and len(data)<=MAX_RESPONSE_BYTES
    (a.output/'response.bin').write_bytes(data)
    (a.output/'response-headers.json').write_text(json.dumps(headers,indent=2)+'\n')
    value={}
    if complete:
        try:value=json.loads(data)
        except (ValueError,UnicodeDecodeError):pass
    if not isinstance(value,dict):value={}
    error=value.get('error');error=error if isinstance(error,dict) else {}
    result.update(mode='EXECUTED_AUTHORIZED_ONCE',attempts=1,recorded_at_utc=datetime.now(timezone.utc).isoformat(),HTTP_status=status,elapsed_seconds=time.monotonic()-started,transport_error_type=transport_error,response_bytes=len(data),response_complete=complete,response_sha256=hashlib.sha256(data).hexdigest(),RPC_error_code=error.get('code') if type(error.get('code')) is int else None,Retry_After_present=any(k.lower()=='retry-after' for k in headers),result_present='result' in value,full_mint_coverage_proven=False,production_reports_changed=False)
    (a.output/'sanitized-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
