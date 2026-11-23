#!/usr/bin/env python3
"""Explicit user-run macOS LaunchAgent installer for FLOP.
No writes to Frank, Monster, other emails, cron or existing schedules.
Default invocation is a no-side-effect plan. --apply performs a mail Sent test
BEFORE launchctl. Unverified mail prevents installation.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ.get('FLOP_AGENT_DATA_DIR','~/.local/share/flop-agent')).expanduser()
LABEL='com.'+str(os.getuid())+'.flop-agent'
LAUNCH_DIR=Path('~/Library/LaunchAgents').expanduser()
TICK=LAUNCH_DIR/(LABEL+'.tick.plist')
UI=LAUNCH_DIR/(LABEL+'.dashboard.plist')


def _write_private(path, payload):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    import tempfile
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'wb') as f:
            f.write(payload)
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def config_mail(oauth_path=None, recipient=None):
    if not oauth_path or not Path(oauth_path).expanduser().is_file():
        raise RuntimeError('EXISTING_AUTHORIZED_GMAIL_OAUTH_NOT_FOUND')
    oauth=Path(oauth_path).expanduser().resolve()
    if not oauth.is_file():
        raise RuntimeError('OAUTH_FILE_MISSING')
    cfg={'existing_oauth_file':str(oauth)}
    if recipient:cfg['recipient']=recipient
    _write_private(DATA/'private-mail.json',json.dumps(cfg).encode())
    return {'config_file':str(DATA/'private-mail.json'),'oauth_pointer_only':True}


def plist_args(script, args, *, every=0, keepalive=False):
    prop={'Label':LABEL+'.'+('tick' if every else 'dashboard'),
          'ProgramArguments':[sys.executable,str(ROOT/script),*args],
          'WorkingDirectory':str(ROOT),
          'RunAtLoad':True,
          'EnvironmentVariables':{'FLOP_AGENT_DATA_DIR':str(DATA)},
          'StandardOutPath':str(DATA/'logs'/('tick.log' if every else 'dashboard.log')),
          'StandardErrorPath':str(DATA/'logs'/('tick-error.log' if every else 'dashboard-error.log'))}
    if every:prop['StartInterval']=every
    if keepalive:prop['KeepAlive']=True
    return plistlib.dumps(prop)


def install(oauth_file=None, recipient=None):
    if sys.platform!='darwin':
        raise RuntimeError('MAC_OS_REQUIRED')
    if oauth_file:
        config_mail(oauth_file,recipient)
    DATA.mkdir(parents=True,exist_ok=True,mode=0o700)
    (DATA/'logs').mkdir(parents=True,exist_ok=True,mode=0o700)
    # Test from the exact local code, require Gmail Sent + body/marker readback.
    mailtest=subprocess.run([sys.executable,str(ROOT/'runtime.py'),'mail-test'],
                            cwd=ROOT,capture_output=True,text=True,timeout=60)
    try:result=json.loads(mailtest.stdout.strip())
    except ValueError:result={}
    if mailtest.returncode or result.get('status')!='SENT_VERIFIED':
        raise RuntimeError('MAIL_SENT_READBACK_TEST_NOT_PASSED_NO_DAEMON_INSTALL')
    tick_data=plist_args('runtime.py',['tick'],every=300)
    ui_data=plist_args('agent.py',['dashboard'],keepalive=True)
    LAUNCH_DIR.mkdir(parents=True,exist_ok=True)
    if TICK.exists() or UI.exists():
        raise RuntimeError('EXISTING_FLOP_LAUNCH_AGENT_REQUIRES_MANUAL_REVIEW')
    for path,payload in ((TICK,tick_data),(UI,ui_data)):
        _write_private(path,payload)
    gui='gui/'+str(os.getuid())
    started=[]
    try:
        for path in (TICK,UI):
            cp=subprocess.run(['/bin/launchctl','bootstrap',gui,str(path)],capture_output=True,text=True,timeout=20)
            if cp.returncode:
                raise RuntimeError('LAUNCHCTL_BOOTSTRAP_FAILED_'+path.name)
            started.append(path)
    except Exception:
        for path in started:
            subprocess.run(['/bin/launchctl','bootout',gui,str(path)],capture_output=True,timeout=15)
        raise
    return {'status':'LAUNCHCTL_BOOTSTRAP_ACCEPTED_HEALTH_NOT_YET_VERIFIED','gmail_test':'SENT_VERIFIED',
            'tick_seconds':300,'summary_bangkok':'08:00 & 20:00',
            'dashboard':'http://127.0.0.1:18766',
            'wallet_payment':'PRIVATE_CONFIG_AND_ACTUAL_TESTNET_GATES_ONLY',
            'plists':[str(TICK),str(UI)]}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--apply',action='store_true')
    p.add_argument('--existing-oauth-file')
    p.add_argument('--recipient')
    args=p.parse_args()
    if not args.apply:
        result={'status':'DRY_RUN_NO_INSTALL','launch_target':'2026-11-24T07:00:00Z',
                'tick_seconds':300,'summary_bangkok':'08:00,20:00',
                'must_pass_email_test':True,'requires_real_testnet_readiness':True,
                'private_wallet_config_required_for_real_session':True,
                'plists':[str(TICK),str(UI)]}
    else:
        result=install(args.existing_oauth_file,args.recipient)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
