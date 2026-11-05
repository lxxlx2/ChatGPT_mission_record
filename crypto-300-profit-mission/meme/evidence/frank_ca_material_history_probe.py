"""Opt-in, foreground same-Mint Top20 history acceptance; never a full CA run.

Default prints the plan without reading credentials or opening network sockets.
--execute requires the caller's existing-source read authorization. No GPA,
market/narrative providers, retries, fallback, service commands or product POST.
Raw output is private. Only a sanitized receipt belongs in the public repository.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request

os.umask(0o077)
MAX_WIRE, MAX_SECONDS, MAX_BODY = 1200, 1800, 8*1024*1024


def sha(data): return hashlib.sha256(data).hexdigest()


def write(path, value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    temporary.replace(path)


class SourceStop(BaseException):
    """Bypass analyzer best-effort catches; stop at the first source failure."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None


def worker(args):
    source=args.source.resolve()
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    dirty=subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True)
    if actual!=args.expected_sha or dirty: raise SourceStop('SOURCE_IDENTITY_REJECTED')
    sys.path.insert(0,str(source))
    from mission_agent.meme.cluster import WalletClusterAnalyzer,SolanaReadOnlyRPC,RpcCache,load_registry,markdown
    from mission_agent.mission_control.server import CLUSTER_PRESETS
    prior_bytes=args.mint_report.read_bytes();prior=json.loads(prior_bytes)
    # Only the existing FrankMeme file's first configured endpoint is permitted.
    config=Path.home()/'Library/Application Support/FrankMeme/solana_rpc_urls'
    endpoints=[s.strip() for s in config.read_text().splitlines() if s.strip().startswith('https://')]
    if len(endpoints)!=1: raise SourceStop('EXISTING_SINGLE_PROVIDER_REQUIRED')
    endpoint=endpoints[0]
    out=args.output;raw=out/'raw';raw.mkdir(mode=0o700)
    seed_hash=sha(args.seed_cache.read_bytes())
    seed=sqlite3.connect(args.seed_cache.resolve().as_uri()+'?mode=ro',uri=True)
    copied=sqlite3.connect(out/'rpc-cache.sqlite')
    try: seed.backup(copied)
    finally: seed.close()
    # Immutable transaction TTLs remain untouched. No old balance/signature pages.
    copied.execute("DELETE FROM rpc_cache WHERE method != 'getTransaction'")
    copied.commit();copied.close()
    cache=RpcCache(out/'rpc-cache.sqlite')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    entries=[];started=time.monotonic();epoch=time.time()
    def expired(*args): raise SourceStop('PARENT_TIME_LIMIT')
    signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,MAX_SECONDS-5)
    allowed=SolanaReadOnlyRPC.ALLOWED-{'getProgramAccounts'}

    def open_captured(request,timeout=None):
        payload=json.loads(request.data)
        if request.full_url!=endpoint or request.get_method()!='POST' or payload.get('method') not in allowed:
            raise SourceStop('SOURCE_METHOD_OR_ENDPOINT_REJECTED')
        if len(entries)>=MAX_WIRE or time.monotonic()-started>=MAX_SECONDS-5:
            raise SourceStop('CAPTURE_BUDGET_STOP')
        n=len(entries)+1
        (raw/f'{n:04d}-request.json').write_bytes(request.data)
        entry={'ordinal':n,'method':payload['method'],'request_sha256':sha(request.data),
               'started_at_utc':datetime.now(timezone.utc).isoformat()}
        entries.append(entry);write(out/'wire-manifest.json',entries)
        response=None;begin=time.monotonic()
        try:
            try: response=opener.open(request,timeout=min(float(timeout or 20),MAX_SECONDS-5-(time.monotonic()-started)))
            except urllib.error.HTTPError as error: response=error
            status=int(response.status)
            body=response.read(MAX_BODY+1)
            (raw/f'{n:04d}-response.bin').write_bytes(body)
            entry.update(http_status=status,response_sha256=sha(body),response_bytes=len(body),
                         body_within_limit=len(body)<=MAX_BODY,elapsed_seconds=time.monotonic()-begin,
                         retry_after_present=bool(response.headers.get('Retry-After')))
            if len(body)>MAX_BODY: raise SourceStop('RESPONSE_SIZE_LIMIT')
            value=json.loads(body)
            if status!=200 or not isinstance(value,dict) or value.get('error') or 'result' not in value or value.get('id')!=payload['id']:
                raise SourceStop('SOURCE_ENVELOPE_OR_HTTP_STOP')
            class CapturedResponse:
                def __enter__(self): return self
                def __exit__(self,*args): return False
                def read(self,limit=None): return body if limit is None else body[:limit]
            return CapturedResponse()
        except BaseException as error:
            entry['stop_type']=type(error).__name__
            if isinstance(error,SourceStop): entry['stop_reason']=str(error)
            raise SourceStop('SOURCE_STOP') from None
        finally:
            if response is not None: response.close()
            write(out/'wire-manifest.json',entries)

    rpc=SolanaReadOnlyRPC(endpoint=endpoint,fallback_endpoints=[],open_url=open_captured,cache=cache,
                          max_wire_attempts=MAX_WIRE,max_elapsed_seconds=MAX_SECONDS)
    opts=dict(CLUSTER_PRESETS['standard'])
    opts.update(enumerate_holder_ranks=False,read_pool_vaults=False,audit_holder_binary=False,
                market_client=None,independent_market_client=None,narrative_client=None,
                compare_market_sources=False,collect_narrative=False)
    def progress(stage,details):
        write(out/'progress.json',{'stage':stage,'wire_attempts':rpc.calls,'cache_hits':rpc.cache_hits,
                                  'elapsed_seconds':round(time.monotonic()-started,3)})
    opts['progress_callback']=progress
    status='STOPPED';report=None;stop_type=None
    try:
        registry=load_registry(source/'config/meme_special_addresses.json')
        report=WalletClusterAnalyzer(prior['mint'],rpc=rpc,special_registry=registry,**opts).analyze()
        rpc.assert_can_publish()
        if report['analysis_completeness']['status']!='INCOMPLETE_EVIDENCE': raise SourceStop('UNEXPECTED_COMPLETENESS')
        write(out/'report.json',report);(out/'report.md').write_text(markdown(report))
        status='BOUNDED_TOP20_HISTORY_COMPLETED_INCOMPLETE_EVIDENCE'
    except BaseException as error:
        stop_type=type(error).__name__;report=None
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);cache.close()
        result={'status':status,'stop_type':stop_type,'source_sha':actual,
                'scope':'CURRENT_TOP20_HISTORY_ONLY_NOT_FULL_CA_ACCEPTANCE',
                'started_at_utc':datetime.fromtimestamp(epoch,timezone.utc).isoformat(),
                'finished_at_utc':datetime.now(timezone.utc).isoformat(),
                'wire_attempts':len(entries),'adapter_wire_attempts':rpc.calls,'cache_hits':rpc.cache_hits,
                'methods':dict(Counter(e['method'] for e in entries)),
                'elapsed_seconds':round(time.monotonic()-started,3),'max_wire_attempts':MAX_WIRE,'max_elapsed_seconds':MAX_SECONDS,
                'prior_report_sha256':sha(prior_bytes),'seed_cache_sha256':seed_hash,
                'original_seed_unchanged':sha(args.seed_cache.read_bytes())==seed_hash,
                'script_sha256':sha(Path(__file__).read_bytes()),
                'manifest_sha256':sha((out/'wire-manifest.json').read_bytes()) if entries else None,
                'report_sha256':sha((out/'report.json').read_bytes()) if report else None,
                'retry_or_fallback':0,'product_ca_posts':0,'production_writes':0,'notifications_or_trades':0,
                'gpa_market_pool_narrative_reads':0,'new_sources':0}
        write(out/'result.json',result);print(json.dumps(result),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--expected-sha',required=True)
    p.add_argument('--mint-report',type=Path,required=True);p.add_argument('--seed-cache',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true')
    p.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    a=p.parse_args()
    if not a.execute:
        print(json.dumps({'status':'PLAN_ONLY_NO_CREDENTIAL_OR_NETWORK_ACCESS','max_wire':MAX_WIRE,'max_seconds':MAX_SECONDS}));return
    if a.worker: worker(a);return
    a.output.mkdir(mode=0o700)
    write(a.output/'execution-claim.json',{'scope':'SAME_MINT_CURRENT_TOP20_HISTORY_ONLY','max_wire':MAX_WIRE,'max_seconds':MAX_SECONDS})
    with (a.output/'private-console.txt').open('w') as log:
        child=subprocess.Popen([sys.executable,'-I','-B',str(Path(__file__).resolve()),*sys.argv[1:],'--worker'],stdout=log,stderr=log)
        try: code=child.wait(timeout=MAX_SECONDS)
        except subprocess.TimeoutExpired:
            child.kill();child.wait();code=child.returncode
            write(a.output/'parent-stop.json',{'status':'HARD_TIME_LIMIT','wire_count':'READ_PRIVATE_MANIFEST'})
    print(json.dumps({'child_exit_code':code,'result_available':(a.output/'result.json').exists()}))


if __name__=='__main__': main()
