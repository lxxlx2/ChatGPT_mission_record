#!/usr/bin/env python3
"""Repair an existing FLOP localhost dashboard, without replacing other jobs.

The operator must run --apply. The script never touches the FLOP wallet, mail,
Faucet, tick/cron, or any other listener. It proves socket ownership before
terminating any stale dashboard python process.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import plistlib
import re
import signal
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
PORT = 8766
UID = os.getuid() if hasattr(os,'getuid') else None
LABEL = 'com.' + str(UID) + '.flop-agent.dashboard'
PLIST = Path.home() / 'Library/LaunchAgents' / (LABEL + '.plist')
API = 'http://127.0.0.1:8766'

def command(args, timeout=8):
    return subprocess.run(args,capture_output=True,text=True,timeout=timeout,check=False)

def git_sha():
    cp=command(['git','-C',str(ROOT),'rev-parse','HEAD'])
    if cp.returncode or not re.fullmatch('[0-9a-f]{40}',cp.stdout.strip()):
        raise RuntimeError('SOURCE_GIT_HEAD_UNVERIFIED')
    return cp.stdout.strip()

def stable_root():
    expected = Path.home()/'Library/Application Support/FLOPAgent/mission/research/projects/flop-network/agent'
    if ROOT.resolve()!=expected.resolve():
        raise RuntimeError('NOT_STABLE_FLOP_AGENT_SOURCE')

def active_plist():
    if not PLIST.is_file():
        raise RuntimeError('EXISTING_FLOP_DASHBOARD_PLIST_MISSING')
    data=plistlib.loads(PLIST.read_bytes())
    args=data.get('ProgramArguments')
    if data.get('Label')!=LABEL or not isinstance(args,list) or len(args)!=3:
        raise RuntimeError('FLOP_DASHBOARD_PLIST_IDENTITY_MISMATCH')
    if Path(args[1]).resolve()!=ROOT/'agent.py' or args[2]!='dashboard':
        raise RuntimeError('FLOP_DASHBOARD_PLIST_WRONG_SCRIPT')
    return data

def local_get(path):
    try:
        with urlopen(API+path,timeout=2) as r:
            return {'status':r.status,'json':json.loads(r.read(10000)) if path.startswith('/api/health') else None}
    except HTTPError as e:
        e.close()
        return {'status':e.code,'json':None}
    except (OSError,URLError,ValueError,TimeoutError):
        return {'status':None,'json':None}

def healthy(expected_sha):
    health=local_get('/api/health?utm_source=chatgpt.com')
    tracked=local_get('/?utm_source=chatgpt.com')
    j=health.get('json') if isinstance(health.get('json'),dict) else {}
    return (health['status']==200 and tracked['status']==200
            and j.get('service')=='flop-dashboard'
            and j.get('schema')=='flop-dashboard.v2'
            and j.get('git_head_sha')==expected_sha
            and Path(j.get('source_path','')).resolve()==ROOT.resolve()
            and isinstance(j.get('pid'),int))

def listener_pids():
    cp=command(['/usr/sbin/lsof','-nP','-t','-iTCP:'+str(PORT),'-sTCP:LISTEN'])
    if cp.returncode not in (0,1):
        raise RuntimeError('LISTENER_INSPECTION_FAILED')
    return sorted(set(int(s) for s in cp.stdout.split() if s.isdigit()))

def listener_info(pid):
    proc=command(['/bin/ps','-p',str(pid),'-o','uid=','-o','command='])
    if proc.returncode or not proc.stdout.strip():
        return {'pid':pid,'exists':False,'ours':False,'command':'UNKNOWN'}
    result=proc.stdout.strip().split(None,1)
    uid=int(result[0]) if result and result[0].isdigit() else None
    cmd=result[1] if len(result)>1 else ''
    matching=re.search(r'/research/projects/flop-network/agent/agent\.py\s+dashboard(?:\s|$)',cmd) is not None
    allowed_path=('/flop-agent.' in cmd or '/FLOPAgent/mission/' in cmd)
    return {'pid':pid,'exists':True,'ours':uid==UID and matching and allowed_path,
            'command':cmd[:500]}

def restart_managed():
    cp=command(['/bin/launchctl','kickstart','-k','gui/'+str(UID)+'/'+LABEL],timeout=16)
    return {'ok':cp.returncode==0,'exit':cp.returncode}

def await_health(sha,seconds=6):
    for _ in range(int(seconds*4)):
        if healthy(sha):return True
        time.sleep(0.25)
    return False

def run(apply=False):
    stable_root()
    sha=git_sha()
    active_plist()
    info={'status':'INSPECTED','expected_sha':sha,'label':LABEL,
          'tracked_http':local_get('/?utm_source=chatgpt.com')['status']}
    if healthy(sha):
        info['status']='ALREADY_HEALTHY'
        return info
    pids=listener_pids()
    details=[listener_info(pid) for pid in pids]
    info['listeners']=details
    if any(x['exists'] and not x['ours'] for x in details):
        info['status']='BLOCKED_UNRECOGNIZED_8766_OWNER'
        return info
    if not apply:
        info['status']='REPAIR_AVAILABLE_ONLY_FOR_VERIFIED_FLOP_DASHBOARD'
        return info
    # Reload only existing dashboard job first. Never restart tick or email.
    info['kickstart']=restart_managed()
    if await_health(sha):
        info['status']='REPAIRED_VERIFIED'
        return info
    pids=listener_pids()
    details=[listener_info(pid) for pid in pids]
    info['after_kickstart_listeners']=details
    if any(x['exists'] and not x['ours'] for x in details):
        info['status']='BLOCKED_UNRECOGNIZED_8766_OWNER'
        return info
    # A stale orphan from the prior temporary checkout is the most likely
    # 404 cause. Only send SIGTERM after inspecting PID, UID and exact script.
    terminated=[]
    for found in details:
        if found['exists'] and found['ours']:
            verified=listener_info(found['pid'])
            if verified['exists'] and verified['ours']:
                os.kill(found['pid'],signal.SIGTERM)
                terminated.append(found['pid'])
    info['terminated_verified_old_dashboard_pids']=terminated
    for _ in range(16):
        if not listener_pids():break
        time.sleep(0.25)
    info['second_kickstart']=restart_managed()
    if await_health(sha,seconds=8):
        info['status']='REPAIRED_VERIFIED'
    else:
        info['status']='REPAIR_UNVERIFIED_NEEDS_LOCAL_LOGS'
        info['final_http']=local_get('/?utm_source=chatgpt.com')['status']
        info['current_listeners']=[listener_info(pid) for pid in listener_pids()]
        stderr=Path.home()/'.local/share/flop-agent/logs/dashboard.stderr.log'
        if stderr.is_file():
            tail=stderr.read_text(errors='replace').splitlines()[-8:]
            info['dashboard_log_tail']=[line[:250] for line in tail]
    return info

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apply',action='store_true')
    args=p.parse_args()
    data=run(args.apply)
    print(json.dumps(data,ensure_ascii=False,indent=2))
    if data['status'] in ('REPAIRED_VERIFIED','ALREADY_HEALTHY',
                          'REPAIR_AVAILABLE_ONLY_FOR_VERIFIED_FLOP_DASHBOARD'):
        return 0
    return 2

if __name__=='__main__':
    sys.exit(main())
