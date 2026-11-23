#!/usr/bin/env python3
"""One-shot, existing-FLOP-only dashboard port migration + live HTTP acceptance.

Purpose: previous FLOP launchctl task has exit=1 while ports 8765 and 8766
are occupied by unknown or other services. Never kill or modify those PIDs.
Only the existing com.<uid>.flop-agent.dashboard launchd plist is touched.
The testnet-wallet, Gmail, and FLOP tick job remain unchanged.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import plistlib
import re
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ.get('FLOP_AGENT_DATA_DIR','~/.local/share/flop-agent')).expanduser()
LABEL='com.'+str(os.getuid())+'.flop-agent.dashboard'
PLIST=Path.home()/'Library/LaunchAgents'/(LABEL+'.plist')
PORTS=range(18766,18796)
SERVICE='flop-dashboard'
BUILD='flop-dashboard-dynamic-port-v3'
HOST='127.0.0.1'

def proc(args, *, timeout=18):
    return subprocess.run(args, capture_output=True, text=True,
                          check=False, timeout=timeout)

def head_sha():
    result=proc(['git','-C',str(ROOT),'rev-parse','HEAD'])
    out=result.stdout.strip()
    if result.returncode or not re.fullmatch('[0-9a-f]{40}',out):
        raise RuntimeError('FIXED_GIT_SHA_UNVERIFIED')
    return out

def existing_plist():
    if not PLIST.is_file():
        raise RuntimeError('EXISTING_FLOP_DASHBOARD_JOB_NOT_FOUND')
    value=plistlib.loads(PLIST.read_bytes())
    args=value.get('ProgramArguments')
    if (value.get('Label')!=LABEL or
        not isinstance(args,list) or len(args)!=3 or
        Path(args[1]).resolve()!=ROOT/'agent.py' or args[2]!='dashboard'):
        raise RuntimeError('EXISTING_JOB_NOT_FLOP_DASHBOARD')
    env=value.get('EnvironmentVariables')
    if not isinstance(env,dict):
        raise RuntimeError('EXISTING_LAUNCHD_ENV_INVALID')
    if Path(value.get('WorkingDirectory','')).resolve()!=ROOT.resolve():
        raise RuntimeError('EXISTING_JOB_WORKDIR_DIFFERENT')
    return value

def choose_port(candidates=PORTS):
    """Best-effort localhost bind probe; actual identity HTTP check is final."""
    for port in candidates:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((HOST,port))
            except OSError:
                continue
            return port
    raise RuntimeError('NO_FREE_FLOP_DASHBOARD_PORT_18766_TO_18795')

def get_http(port, route, timeout=2):
    url='http://'+HOST+':'+str(port)+route
    try:
        with urlopen(url,timeout=timeout) as r:
            body=r.read(16384)
            return {'status':r.status, 'body':body}
    except HTTPError as exc:
        exc.close()
        return {'status':exc.code,'body':b''}
    except (URLError,OSError,TimeoutError):
        return {'status':None,'body':b''}

def live_probe(port, sha):
    health=get_http(port,'/api/health?utm_source=chatgpt.com')
    home=get_http(port,'/?utm_source=chatgpt.com')
    if health['status']!=200 or home['status']!=200:
        return {'verified':False,'health_status':health['status'],
                'home_status':home['status'],'port':port}
    try:
        data=json.loads(health['body'].decode('utf-8'))
    except (UnicodeError,ValueError):
        return {'verified':False,'reason':'HEALTH_NOT_JSON','port':port}
    expected_source=str(ROOT.resolve())
    passed=(data.get('service')==SERVICE and
            data.get('build')==BUILD and
            data.get('git_head_sha')==sha and
            data.get('source_path')==expected_source and
            data.get('host')==HOST and
            data.get('port')==port and
            isinstance(data.get('pid'),int) and
            data['pid']>0 and
            data['pid']!=os.getpid())
    return {'verified':passed,'port':port,'http':home['status'],
            'service':data.get('service'),'build':data.get('build'),
            'git_head_sha':data.get('git_head_sha'),
            'pid':data.get('pid'),
            'source_path':data.get('source_path')}

def wait_health(port,sha,checks=24):
    last={}
    for _ in range(checks):
        last=live_probe(port,sha)
        if last.get('verified'):
            return last
        time.sleep(0.25)
    return last

def write_0600(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    import tempfile
    fd,temp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'wb') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def command_status(label=LABEL):
    r=proc(['/bin/launchctl','print','gui/'+str(os.getuid())+'/'+label])
    return {'loaded':r.returncode==0,'exit':r.returncode}

def launchctl_bootout():
    # Pass service label only, never affect other user LaunchAgents.
    return proc(['/bin/launchctl','bootout',
                 'gui/'+str(os.getuid())+'/'+LABEL])

def launchctl_bootstrap():
    return proc(['/bin/launchctl','bootstrap','gui/'+str(os.getuid()),str(PLIST)])

def diagnostics():
    """Expose only what is required to diagnose managed job, not passwords."""
    status=command_status()
    stderr=DATA/'logs/dashboard.stderr.log'
    tail=[]
    if stderr.is_file():
        try:
            tail=[line[:300] for line in stderr.read_text(errors='replace').splitlines()[-6:]]
        except OSError:
            pass
    return {'launchd':status,'dashboard_stderr_tail':tail}

def migrate(apply=False):
    if sys.platform!='darwin':
        raise RuntimeError('MAC_OS_REQUIRED')
    expected=(Path.home()/'Library/Application Support/FLOPAgent/mission/'
              'research/projects/flop-network/agent')
    if ROOT.resolve()!=expected.resolve():
        raise RuntimeError('NOT_FIXED_FLOP_GIT_CHECKOUT')
    sha=head_sha()
    original=existing_plist()
    oldport=(original['EnvironmentVariables'].get('FLOP_DASHBOARD_PORT')
             or 8766)
    try:
        oldport=int(oldport)
    except (TypeError,ValueError):
        oldport=None
    if oldport and oldport in PORTS:
        current=live_probe(oldport,sha)
        if current.get('verified'):
            return {'status':'ALREADY_VERIFIED','port':oldport,
                    'url':'http://127.0.0.1:'+str(oldport)+'/',
                    'health':current}
    # Do not inspect or stop unrelated 8765/8766 listeners. Choose an
    # independent, currently free loopback port for this existing service.
    port=choose_port()
    plan={'status':'READY_FOR_EXISTING_JOB_PORT_MIGRATION',
          'selected_port':port,'new_url':'http://127.0.0.1:'+str(port)+'/',
          'git_sha':sha,'launchd_label':LABEL,
          'old_plist_port':oldport,
          'unchanged':['FLOP wallet','Gmail/outbox','FLOP tick','Technocore',
                       'other 8765/8766 listeners']}
    if not apply:
        return plan
    copy=dict(original)
    copy['EnvironmentVariables']=dict(original['EnvironmentVariables'])
    copy['EnvironmentVariables']['FLOP_DASHBOARD_PORT']=str(port)
    data=plistlib.dumps(copy)
    backup=DATA/'dashboard-port-migration-backup.plist'
    # Persistent overwrite-free audit: backup only once if previous repair.
    if backup.is_file() and backup.read_bytes()!=PLIST.read_bytes():
        # Preserve original backup and continue; previous restoration may be
        # possible from it. Never overwrite earlier known-good evidence.
        pass
    elif not backup.exists():
        write_0600(backup,PLIST.read_bytes())
    running=command_status()['loaded']
    if running:
        exit_status=launchctl_bootout()
        if exit_status.returncode:
            raise RuntimeError('EXISTING_DASHBOARD_BOOTOUT_FAILED')
    write_0600(PLIST,data)
    restarted=launchctl_bootstrap()
    if restarted.returncode:
        # Try to restore old job; do not declare success or touch other jobs.
        write_0600(PLIST,plistlib.dumps(original))
        if running:
            launchctl_bootstrap()
        return {**plan,'status':'FAILED_NEW_DASHBOARD_BOOTSTRAP_ROLLED_BACK',
                'diagnostics':diagnostics()}
    result=wait_health(port,sha)
    if not result.get('verified'):
        launchctl_bootout()
        write_0600(PLIST,plistlib.dumps(original))
        if running:
            launchctl_bootstrap()
        return {**plan,'status':'FAILED_HTTP_IDENTITY_VALIDATION_ROLLED_BACK',
                'probe':result,'diagnostics':diagnostics()}
    manifest={'url':'http://127.0.0.1:'+str(port)+'/',
              'port':port,'git_sha':sha,
              'verified_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'service_label':LABEL,
              'health':result}
    write_0600(DATA/'dashboard-bind.json',
               json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
    return {**plan,'status':'LIVE_HTTP_VERIFIED',
            'health':result,'manifest':str(DATA/'dashboard-bind.json')}

def main(argv=None):
    p=argparse.ArgumentParser(description='FLOP existing dashboard only: port migration + real HTTP acceptance')
    p.add_argument('--apply',action='store_true')
    args=p.parse_args(argv)
    result=migrate(args.apply)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result['status'] in ('ALREADY_VERIFIED','LIVE_HTTP_VERIFIED',
                            'READY_FOR_EXISTING_JOB_PORT_MIGRATION'):
        return 0
    return 1

if __name__=='__main__':
    sys.exit(main())
