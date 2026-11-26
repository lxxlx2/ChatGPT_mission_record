"""Pinned Testnet D10 first grant using the official CLI 0.9.0.
Persist the nonce before signing. Reconcile only that nonce. Never create a
second grant until an independent finalized spend/eligibility verifier exists.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from agent import DATA, utc
from mail import enqueue

IDENTITY=DATA/'agent-identity.json'
GENESIS='0x918abd58fb16306b30ef3886514cfaebffecb4de43e82b6f8ec4795c43cfd800'
RECHECK_SECONDS=900

def request_initial(conn, confirmed_genesis, *, cli_runner=subprocess.run, clock=time.time):
    if confirmed_genesis!=GENESIS:
        return {'status':'BLOCKED_NETWORK_GENESIS_NOT_VERIFIED'}
    keyfile=IDENTITY.parent/'agent-key.json'
    pwfile=IDENTITY.parent/'agent-password'
    if any(not p.is_file() or p.stat().st_mode & 0o077 for p in (IDENTITY,keyfile,pwfile)):
        return {'status':'BLOCKED_AGENT_IDENTITY_NOT_READY'}
    try:
        obj=json.loads(IDENTITY.read_text())
        address=obj.get('address')
        if not isinstance(address,str) or not re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{42,55}',address):
            return {'status':'BLOCKED_AGENT_ADDRESS_INVALID'}
        if obj.get('purpose')!='FLOP_TESTNET_ONLY' or json.loads(keyfile.read_text()).get('address')!=address:
            return {'status':'BLOCKED_AGENT_IDENTITY_NOT_READY'}
        password=pwfile.read_text().strip()
        if not password:
            return {'status':'BLOCKED_AGENT_IDENTITY_NOT_READY'}
    except (OSError,ValueError,TypeError,AttributeError):
        return {'status':'BLOCKED_AGENT_IDENTITY_NOT_READY'}
    key='initial-faucet-'+hashlib.sha256((confirmed_genesis+':'+address).encode()).hexdigest()[:24]
    old=conn.execute('SELECT value FROM kv WHERE key=?',(key,)).fetchone()
    now=int(clock())
    if old:
        attempt=json.loads(old[0])
        if not attempt.get('nonce'):
            return {'status':'BLOCKED_LEGACY_ATTEMPT'}
        if attempt.get('status') in ('CLI_FINALIZED_REPORTED','REFUSED_NO_AUTO_RETRY'):
            return {'status':attempt['status'],'receipt':attempt}
        if now < attempt.get('retry_at',0):
            return {'status':'SAME_NONCE_BACKOFF'}
    else:
        attempt={'status':'OUTCOME_UNKNOWN_PRECOMMITTED','at':utc(),
                 'network':'testnet','genesis':confirmed_genesis,'address':address,
                 'nonce':str(int(clock()*1000))}
    cli=shutil.which('flop')
    if not cli:
        return {'status':'BLOCKED_CLI_NOT_INSTALLED'}
    try:
        version=cli_runner([cli,'--version'],capture_output=True,text=True,timeout=20,check=False)
        if version.returncode or version.stdout.strip()!='0.9.0':
            return {'status':'BLOCKED_CLI_VERSION_REVIEW_REQUIRED'}
    except (OSError,subprocess.TimeoutExpired):
        return {'status':'BLOCKED_CLI_VERSION_REVIEW_REQUIRED'}
    attempt.update(status='OUTCOME_UNKNOWN_PRECOMMITTED',retry_at=now+RECHECK_SECONDS)
    conn.execute('INSERT OR REPLACE INTO kv(key,value) VALUES (?,?)',(key,json.dumps(attempt)))
    conn.commit()
    env=dict(os.environ,FLOP_KEY_PASSWORD=password)
    try:
        cp=cli_runner([cli,'--network','testnet','--keystore',str(keyfile),
                       '--password-env','FLOP_KEY_PASSWORD','--json','faucet','request',
                       '--nonce',attempt['nonce']],env=env,capture_output=True,text=True,
                       timeout=150,check=False)
        attempt['return_code']=cp.returncode
        response={}
        for raw in (cp.stdout,cp.stderr):
            try:
                parsed=json.loads(raw)
                if isinstance(parsed,dict):
                    response=parsed
                    break
            except (ValueError,TypeError):
                pass
        tx=response.get('tx_hash') or response.get('txHash')
        if isinstance(tx,str) and re.fullmatch(r'0x[0-9a-fA-F]{64}',tx):
            attempt['tx_hash']=tx
        if cp.returncode==0 and response.get('finalized') is True and attempt.get('tx_hash'):
            attempt['status']='CLI_FINALIZED_REPORTED'
        elif response.get('action') in ('fix_request','report_to_operator'):
            attempt['status']='REFUSED_NO_AUTO_RETRY'
        else:
            attempt['status']='SAME_NONCE_RECONCILIATION_PENDING'
            delay=response.get('retryAfterSeconds')
            if type(delay) is int and delay>0:
                attempt['retry_at']=now+max(RECHECK_SECONDS,delay)
    except (OSError,subprocess.TimeoutExpired):
        attempt['status']='SAME_NONCE_RECONCILIATION_PENDING'
    finally:
        env.pop('FLOP_KEY_PASSWORD',None)
        password=''
    conn.execute('UPDATE kv SET value=? WHERE key=?',(json.dumps(attempt),key))
    conn.commit()
    if attempt['status']=='CLI_FINALIZED_REPORTED':
        enqueue(conn,'faucet-finalized-'+hashlib.sha256(key.encode()).hexdigest()[:15],
                '[FLOP] 首次 Testnet Faucet 返回 finalized',
                'CLI reported finalized; independent chain verification still required. '
                'Testnet grant is not voucher credit. Transaction: '+attempt['tx_hash'])
    return attempt
