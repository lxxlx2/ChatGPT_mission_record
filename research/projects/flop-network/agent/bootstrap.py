#!/usr/bin/env python3
"""One-entry FLOP Mac setup / in-place upgrade.

- Uses current stable Git checkout (caller is responsible for pinning the SHA).
- Reuses existing Gmail OAuth and recorded SENT_VERIFIED test.
- Generates exactly one encrypted sr25519 test-only key and a local 0600
  high-entropy password, never prints the mnemonic or secret.
- Replaces only the two existing FLOP launchd jobs under the same labels.
- Never creates unrelated automation or assumes future Testnet is live.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import secrets
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime,timezone

from agent import DATA
from install import ROOT, LAUNCH_DIR, TICK, UI, LABEL, _write_private
from runtime import MONITOR, ensure_state, mail_test
from mail import mail_status

PRIVATE_KEY=DATA/'agent-key.json'
PRIVATE_PASSWORD=DATA/'agent-password'
PUBLIC_ID=DATA/'agent-identity.json'
LAST_MIGRATION=DATA/'installation.json'

def run_checked(args,*,env=None,timeout=45):
    cp=subprocess.run(args,env=env,capture_output=True,text=True,timeout=timeout,check=False)
    if cp.returncode:
        raise RuntimeError('COMMAND_FAILED_'+Path(args[0]).name+'_'+str(cp.returncode))
    return cp

def require_stable_source():
    source=str(ROOT.resolve())
    temp_candidates=['/var/folders/','/private/var/folders/','/tmp/','/private/tmp/']
    if any(source.startswith(t) for t in temp_candidates):
        raise RuntimeError('SOURCE_IN_TEMP_DIRECTORY_USE_STABLE_GIT_CHECKOUT')
    if not (ROOT.parents[3]/'.git').is_dir():
        # ROOT=.../research/projects/flop-network/agent, parents[3]=repo root.
        raise RuntimeError('NOT_A_GIT_CHECKOUT')
    return source

def cli_path():
    cli=shutil.which('flop')
    if not cli:
        for p in sorted((Path.home()/'.nvm/versions/node').glob('*/bin/flop'),reverse=True):
            if p.is_file():
                cli=str(p);break
    if not cli:raise RuntimeError('OFFICIAL_FLOP_CLI_0_8_0_REQUIRED')
    cli=os.path.abspath(cli)
    # node is usually alongside npm global bin symlink; preserve its parent PATH.
    return cli

def cli_env(cli):
    env=os.environ.copy()
    env['PATH']=str(Path(cli).parent)+os.pathsep+env.get('PATH','/usr/bin:/bin:/usr/sbin:/sbin')
    env['FLOP_AGENT_DATA_DIR']=str(DATA)
    return env

def offline_identity(cli):
    DATA.mkdir(parents=True,exist_ok=True,mode=0o700)
    version=run_checked([cli,'--version'],env=cli_env(cli),timeout=20).stdout.strip()
    if version!='0.8.0':
        raise RuntimeError('CLI_VERSION_UNEXPECTED_REVIEW_RELEASE_NOT_0_8_0')
    if PUBLIC_ID.is_file():
        item=json.loads(PUBLIC_ID.read_text())
        if not PRIVATE_KEY.is_file() or not PRIVATE_PASSWORD.is_file():
            raise RuntimeError('PERSISTENT_AGENT_IDENTITY_INCOMPLETE_NO_REGENERATION')
        if (PRIVATE_KEY.stat().st_mode & 0o077) or (PRIVATE_PASSWORD.stat().st_mode & 0o077):
            raise RuntimeError('AGENT_SECRET_FILE_PERMISSIONS_NOT_0600')
        if json.loads(PRIVATE_KEY.read_text()).get('address') != item.get('address'):
            raise RuntimeError('ENCRYPTED_KEYSTORE_ADDRESS_MISMATCH')
        return {'address':item['address'],'created_now':False,'cli':version}
    if PRIVATE_KEY.exists() or PRIVATE_PASSWORD.exists():
        raise RuntimeError('PARTIAL_EXISTING_AGENT_KEYS_REQUIRE_MANUAL_RECONCILIATION')
    password=base64.urlsafe_b64encode(secrets.token_bytes(48)).decode('ascii')
    _write_private(PRIVATE_PASSWORD,(password+'\n').encode('ascii'))
    env=cli_env(cli)
    env['FLOP_KEY_PASSWORD']=password
    try:
        generated=run_checked([cli,'keys','generate','--type','sr25519','--name',
                               'flop-agent-testnet','--out',str(PRIVATE_KEY),
                               '--password-env','FLOP_KEY_PASSWORD','--json'],
                              env=env,timeout=90)
        if not PRIVATE_KEY.is_file():
            raise RuntimeError('GENERATED_KEYSTORE_MISSING')
        os.chmod(PRIVATE_KEY,0o600)
        payload=json.loads(PRIVATE_KEY.read_text())
        address=payload.get('address')
        if not isinstance(address,str) or not re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{42,55}',address):
            raise RuntimeError('GENERATED_KEYSTORE_SS58_ADDRESS_MISSING')
        # Persist public metadata last; an interruption cannot create two wallets.
        public={'address':address,'keystore':str(PRIVATE_KEY),
                'key_type':'sr25519','purpose':'FLOP_TESTNET_ONLY',
                'created_utc':datetime.now(timezone.utc).isoformat(),
                'source':'encrypted_keystore_not_cli_stdout'}
        _write_private(PUBLIC_ID,json.dumps(public,ensure_ascii=False,indent=2).encode())
        return {'address':address,'created_now':True,'cli':version}
    finally:
        env['FLOP_KEY_PASSWORD']=''
        password=''

def verify_mail_test():
    if not MONITOR.is_file():
        raise RuntimeError('EXISTING_FLOP_MAIL_LEDGER_NOT_FOUND')
    c=sqlite3.connect(MONITOR)
    c.row_factory=sqlite3.Row
    try:
        ensure_state(c)
        row=c.execute("SELECT status FROM flop_mail WHERE mail_key='first-mail-setup-test'").fetchone()
        if row and row['status']=='SENT_VERIFIED':
            return {'mail':'SENT_VERIFIED','new_test_mail_sent':False}
    finally:c.close()
    # On an earlier partial install this may actually send ONE test message.
    proof=mail_test()
    if proof.get('status')!='SENT_VERIFIED':
        raise RuntimeError('GMAIL_SENT_READBACK_FAILED_NO_SERVICE_INSTALL')
    return {'mail':'SENT_VERIFIED','new_test_mail_sent':True}

def plist_for(kind,python_path,env):
    label=LABEL+'.'+kind
    if kind=='tick':
        args=[python_path,str(ROOT/'runtime.py'),'tick']
        interval=300
    elif kind=='dashboard':
        args=[python_path,str(ROOT/'agent.py'),'dashboard']
        interval=None
    else:raise ValueError('INVALID_LABEL')
    p={'Label':label,'ProgramArguments':args,'WorkingDirectory':str(ROOT),
       'EnvironmentVariables':{'PATH':env['PATH'],'FLOP_AGENT_DATA_DIR':str(DATA)},
       'RunAtLoad':True,
       'StandardOutPath':str(DATA/'logs'/(kind+'.stdout.log')),
       'StandardErrorPath':str(DATA/'logs'/(kind+'.stderr.log'))}
    if interval:p['StartInterval']=interval
    else:p['KeepAlive']=True
    return plistlib.dumps(p)

def verify_old_job(path,kind):
    if not path.is_file():raise RuntimeError('EXPECTED_EXISTING_FLOP_JOB_MISSING_'+kind)
    data=plistlib.loads(path.read_bytes())
    expected=LABEL+'.'+kind
    args=data.get('ProgramArguments')
    if data.get('Label')!=expected or not isinstance(args,list) or len(args)<2:
        raise RuntimeError('EXISTING_LAUNCHD_LABEL_NOT_OURS_'+kind)
    if not str(args[1]).endswith('/research/projects/flop-network/agent/'+('runtime.py' if kind=='tick' else 'agent.py')):
        raise RuntimeError('EXISTING_LAUNCHD_JOB_IS_NOT_FLOP_'+kind)
    return data

def launchd_upgrade(cli):
    if sys.platform!='darwin':raise RuntimeError('MACOS_REQUIRED')
    old={TICK:verify_old_job(TICK,'tick'),UI:verify_old_job(UI,'dashboard')}
    env=cli_env(cli)
    (DATA/'logs').mkdir(parents=True,exist_ok=True,mode=0o700)
    new={TICK:plist_for('tick',sys.executable,env),
         UI:plist_for('dashboard',sys.executable,env)}
    back=DATA/'launchd-backup'
    back.mkdir(parents=True,exist_ok=True,mode=0o700)
    before={p:p.read_bytes() for p in old}
    for p,raw in before.items():
        _write_private(back/(p.name+'.prior'),raw)
    gui='gui/'+str(os.getuid())
    booted=[]
    try:
        for p in (TICK,UI):
            subprocess.run(['/bin/launchctl','bootout',gui,str(p)],capture_output=True,text=True,timeout=25)
        for p,new_data in new.items():
            _write_private(p,new_data)
        for p in (TICK,UI):
            run_checked(['/bin/launchctl','bootstrap',gui,str(p)],timeout=30)
            booted.append(p)
    except Exception:
        for p in booted:
            subprocess.run(['/bin/launchctl','bootout',gui,str(p)],capture_output=True,timeout=15)
        for p,contents in before.items():
            _write_private(p,contents)
        for p in (TICK,UI):
            subprocess.run(['/bin/launchctl','bootstrap',gui,str(p)],capture_output=True,timeout=25)
        raise RuntimeError('FLOP_UPGRADE_FAILED_OLD_PLISTS_RESTORED')
    return {'task_labels':[LABEL+'.tick',LABEL+'.dashboard'],
            'source_dir':str(ROOT),'dashboard_url':'http://127.0.0.1:8766','task_install':'BOOTSTRAP_ACCEPTED_AWAIT_RUNTIME_HEALTH'}

def setup(apply=False):
    stable=require_stable_source()
    cli=cli_path()
    if not apply:
        return {'status':'PLAN_ONLY','stable_source':stable,'cli':cli,
                'reuse_gmail':True,'same_two_launchd_labels':True,
                'wallet':'create encrypted sr25519 only if no prior wallet'}
    mail=verify_mail_test()
    # Key is created offline, so no network dependency or faucet fund attempt.
    identity=offline_identity(cli)
    task=launchd_upgrade(cli)
    record={'source':stable,'cli':cli,'identity':identity,'mail':mail,'tasks':task,
            'updated_utc':datetime.now(timezone.utc).isoformat(),
            'real_testnet_payment':'NOT_EXECUTED','faucet':'NOT_EXECUTED',
            'chain_settlement':'NOT_VERIFIED'}
    _write_private(LAST_MIGRATION,json.dumps(record,ensure_ascii=False,indent=2).encode())
    return {'status':'PRELAUNCH_IDENTITY_AND_SERVICES_PREPARED',
            'mail':mail,'wallet_address':identity['address'],
            'wallet_created_this_run':identity['created_now'],
            'services':task,
            'live_paid_inference':'NOT_ENABLED_UNTIL_REAL_CHAIN_AND_MINER_PROVEN',
            'faucet':'WAIT_OFFICIAL_TESTNET'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    print(json.dumps(setup(args.apply),ensure_ascii=False,indent=2))
if __name__=='__main__':
    main()
