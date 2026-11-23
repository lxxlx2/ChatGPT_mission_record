"""Exactly-once first Testnet Faucet claim using official CLI only.

No repeated faucet calls on ambiguous outcomes. Run only AFTER runtime
establishes official Testnet status and matching pinned RPC/Faucet genesis.
Later daily-claim cadence is NOT guessed before official limits are published.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from agent import DATA,utc
from mail import enqueue

IDENTITY=DATA/'agent-identity.json'

def request_initial(conn, confirmed_genesis, *, cli_runner=subprocess.run):
    if not re.fullmatch(r'0x[0-9a-f]{64}',confirmed_genesis or ''):
        return {'status':'BLOCKED_NETWORK_GENESIS_NOT_VERIFIED'}
    if not IDENTITY.is_file() or (IDENTITY.stat().st_mode & 0o077):
        return {'status':'BLOCKED_AGENT_IDENTITY_NOT_READY'}
    obj=json.loads(IDENTITY.read_text())
    address=obj.get('address')
    if not isinstance(address,str) or not re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{42,55}',address):
        return {'status':'BLOCKED_AGENT_ADDRESS_INVALID'}
    key='initial-faucet-'+hashlib.sha256((confirmed_genesis+':'+address).encode()).hexdigest()[:24]
    old=conn.execute('SELECT value FROM kv WHERE key=?',(key,)).fetchone()
    if old:
        return {'status':'EXISTING_ATTEMPT_NO_AUTO_RESEND','receipt':json.loads(old[0])}
    cli=shutil.which('flop')
    if not cli:
        return {'status':'BLOCKED_CLI_NOT_INSTALLED'}
    attempt={'status':'OUTCOME_UNKNOWN_PRECOMMITTED','at':utc(),'network':'testnet',
             'genesis':confirmed_genesis,'address':address}
    conn.execute('INSERT OR IGNORE INTO kv(key,value) VALUES (?,?)',(key,json.dumps(attempt)))
    conn.commit()
    try:
        cp=cli_runner([cli,'--network','testnet','faucet','request',address,'--json'],
                      capture_output=True,text=True,timeout=100,check=False)
        response=None
        try:
            response=json.loads(cp.stdout.strip())
        except (ValueError,TypeError):
            pass
        attempt['return_code']=cp.returncode
        attempt['output_sha256']=hashlib.sha256(cp.stdout.encode()).hexdigest()
        attempt['stderr_sha256']=hashlib.sha256(cp.stderr.encode()).hexdigest()
        reported=(response or {}).get('status','UNKNOWN') if isinstance(response,dict) else 'UNKNOWN'
        affirmative=str(reported).lower() in ('ok','accepted','success','funded','granted')
        attempt['status']='CLI_ACCEPTED_UNVERIFIED' if cp.returncode==0 and affirmative else 'REJECTED_OR_UNKNOWN_NO_RETRY'
        attempt['response_status']=str(reported)[:65]
    except (OSError,subprocess.TimeoutExpired) as exc:
        attempt['status']='OUTCOME_UNKNOWN_NO_RETRY'
        attempt['reason']=type(exc).__name__
    conn.execute('UPDATE kv SET value=? WHERE key=?',(json.dumps(attempt),key))
    conn.commit()
    subject='[FLOP] 首次 Testnet Faucet 请求记录'
    body=('网络 Genesis：'+confirmed_genesis+'\n'
          '本地 Agent 钱包：'+address+'\n'
          '请求结果：'+attempt['status']+'\n'
          '说明：发送成功和实际余额不等同，仍需链上核验；任何不确定结果不会自动重复领取。')
    enqueue(conn,'faucet-first-'+hashlib.sha256(key.encode()).hexdigest()[:15],subject,body)
    return attempt
