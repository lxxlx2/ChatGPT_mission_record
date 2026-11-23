#!/usr/bin/env python3
"""FLOP local scheduled testnet Agent (2026-11).

Safe by default: only probes network and sends authorized email. Direct sessions
require a private config, a real Testnet release and matching finalized genesis.
An uncertain CLI result is NOT a passed paid session and is NEVER retried.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import zoneinfo

from agent import DATA, db, utc
from mail import enqueue, pump, mail_status

BKK = zoneinfo.ZoneInfo('Asia/Bangkok')
LAUNCH_UTC = datetime(2026, 11, 24, 7, 0, tzinfo=timezone.utc)
STATUS_URL = 'https://docs.flop.network/networks/testnet'
CONF = DATA / 'private-testnet.json'
MONITOR = DATA / 'monitor.sqlite3'
LAST_ALARM_INTERVAL = 3600
HTTP_TIMEOUT = 15
CLI_TIMEOUT = 750

def now():
    return datetime.now(timezone.utc)

def now_bkk():
    return now().astimezone(BKK)

def ensure_state(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS session_attempts (
      attempt_id TEXT PRIMARY KEY,
      phase TEXT NOT NULL,
      started_utc TEXT NOT NULL, ended_utc TEXT,
      wallet TEXT NOT NULL, expected_genesis TEXT NOT NULL,
      miner TEXT NOT NULL, max_flop TEXT NOT NULL,
      cli_result TEXT, chain_verified INTEGER NOT NULL DEFAULT 0,
      final_spent_flop TEXT, chain_tx TEXT, last_error TEXT);
    CREATE TABLE IF NOT EXISTS runtime_events (
      event_id TEXT PRIMARY KEY, at_utc TEXT NOT NULL,
      severity TEXT NOT NULL, code TEXT NOT NULL,
      details TEXT NOT NULL);
    """)
    conn.commit()

def get(conn, key, fallback=None):
    row=conn.execute('SELECT value FROM kv WHERE key=?',(key,)).fetchone()
    return row[0] if row else fallback

def put(conn, key, value):
    conn.execute('INSERT OR REPLACE INTO kv VALUES (?,?)',(key,str(value)))
    conn.commit()

def log(conn, severity, code, details='', *, event_id=None):
    stamp=utc()
    ident=event_id or hashlib.sha256((stamp+code).encode()).hexdigest()[:28]
    conn.execute('INSERT OR IGNORE INTO runtime_events VALUES (?,?,?,?,?)',
                 (ident,stamp,severity,code,str(details)[:300]))
    conn.commit()

def notify_error(conn, code, detail, *, urgent=True):
    """Errors: notify on transition and repeat no faster than 1h while ongoing."""
    stamp=now()
    bucket=int(stamp.timestamp()) // LAST_ALARM_INTERVAL
    old=get(conn,'current_error')
    if old==code:
        key=f'error-{code}-{bucket}'
    else:
        key=f'error-new-{code}-{bucket}'
    put(conn,'current_error',code)
    log(conn,'ERROR',code,detail,event_id=key)
    safe_detail=str(detail)[:350].replace('\x00','')
    enqueue(conn,key,'[FLOP] 异常告警｜'+code,
            f'曼谷时间：{stamp.astimezone(BKK).isoformat(timespec="seconds")}\n'
            f'异常代码：{code}\n详情：{safe_detail}\n'
            '当前动作：停止涉及未知结算或异常配置的自动推理；只进行只读核验。\n'
            '真实余额与空投权益：未确认。')

def clear_error(conn):
    if get(conn,'current_error'):
        put(conn,'current_error','')
        log(conn,'INFO','ERROR_CLEARED','')

def _json_response(url):
    req=Request(url,headers={'User-Agent':'flop-local-gate/0.1',
                             'Accept':'text/html,application/json'})
    with urlopen(req,timeout=HTTP_TIMEOUT) as response:
        if response.status != 200:
            raise RuntimeError('STATUS_HTTP_NOT_200')
        return response.read(700000).decode('utf-8',errors='replace')

def official_testnet_state(fetch=_json_response):
    """A planned landing page never grants transaction authorization."""
    html=fetch(STATUS_URL)
    lower=html.lower()
    if 'testnet (planned)' in lower or 'status: planned' in lower or 'next (unreleased)' in lower:
        return {'ready':False,'status':'PLANNED','source':STATUS_URL}
    # No guessing network identity from marketing copy or a single string.
    if not re.search(r'network:\s*testnet\s*\((live|active|launched)\)',lower):
        return {'ready':False,'status':'UNVERIFIED_DOC_FORMAT','source':STATUS_URL}
    match=re.search(r'(?:expected genesis|genesis hash)\s*[:\s<>=a-z"\\/;]*?(0x[0-9a-f]{64})',lower)
    if not match:
        return {'ready':False,'status':'GENESIS_NOT_PUBLISHED','source':STATUS_URL}
    return {'ready':True,'status':'PUBLISHED_TESTNET','genesis':match.group(1),'source':STATUS_URL}

def private_config(path=CONF):
    if not path.is_file():
        return None
    if (path.stat().st_mode & 0o077):
        raise ValueError('PRIVATE_CONFIG_PERMISSIONS_MUST_BE_0600')
    obj=json.loads(path.read_text(encoding='utf-8'))
    if obj.get('network')!='testnet':
        raise ValueError('WRONG_NETWORK')
    g=obj.get('expected_genesis')
    if not isinstance(g,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',g):
        raise ValueError('EXPECTED_GENESIS_NOT_PINNED')
    if not isinstance(obj.get('wallet'),str) or not obj['wallet'].strip():
        raise ValueError('OWN_WALLET_NOT_CONFIGURED')
    keystore=Path(obj.get('keystore','')).expanduser()
    if not keystore.is_file():
        raise ValueError('WALLET_KEYSTORE_NOT_FOUND')
    if (keystore.stat().st_mode & 0o077):
        raise ValueError('KEYSTORE_PERMISSIONS_MUST_BE_0600')
    miner=obj.get('miner')
    if not isinstance(miner,str) or not re.fullmatch(r'[a-zA-Z0-9]{42,55}',miner):
        raise ValueError('MINER_SS58_NOT_VERIFIED')
    endpoint=obj.get('endpoint','')
    parts=urlparse(endpoint)
    if parts.scheme!='https' or not parts.hostname or parts.username or parts.password or parts.fragment or parts.query:
        raise ValueError('REACHABLE_INDEPENDENT_MINER_HTTPS_REQUIRED')
    model=obj.get('model')
    if not isinstance(model,str) or not re.fullmatch(r'[a-zA-Z0-9._/-]{5,125}',model):
        raise ValueError('MODEL_NOT_PINNED')
    try:
        ceiling=Decimal(str(obj.get('max_flop','')))
        daily=Decimal(str(obj.get('total_test_flop_budget','')))
    except InvalidOperation:
        raise ValueError('INVALID_WALLET_SPEND_LIMIT') from None
    if not (ceiling.is_finite() and daily.is_finite() and 0 < ceiling <= daily):
        raise ValueError('INVALID_SPEND_LIMIT')
    if not os.environ.get('FLOP_KEY_PASSWORD'):
        security='/usr/bin/security'
        if os.path.isfile(security):
            try:
                secret=subprocess.run([security,'find-generic-password','-s',
                                       'flop-agent-wallet-password','-w'],
                                      capture_output=True,text=True,timeout=10,check=False)
                if secret.returncode==0 and secret.stdout.strip():
                    os.environ['FLOP_KEY_PASSWORD']=secret.stdout.rstrip('\\r\\n')
            except (OSError,subprocess.TimeoutExpired):
                pass
    if not os.environ.get('FLOP_KEY_PASSWORD'):
        raise ValueError('WALLET_PASSWORD_MISSING_FROM_LOCAL_KEYCHAIN')
    obj['keystore']=str(keystore)
    obj['max_flop']=str(ceiling)
    obj['total_test_flop_budget']=str(daily)
    return obj

def cli_network_status():
    binpath=shutil.which('flop')
    if not binpath:
        return {'ready':False,'reason':'FLOP_CLI_NOT_INSTALLED'}
    cmd=[binpath,'--network','testnet','network','status','--json']
    cp=subprocess.run(cmd,capture_output=True,text=True,timeout=30,check=False)
    if cp.returncode or not cp.stdout.strip():
        return {'ready':False,'reason':'CLI_NETWORK_STATUS_UNAVAILABLE'}
    try:
        obj=json.loads(cp.stdout)
    except (ValueError,TypeError):
        return {'ready':False,'reason':'CLI_STATUS_NOT_JSON'}
    # Reject unknown schema; no testnet approval from a process return code.
    genesis=obj.get('genesis_hash') or obj.get('genesisHash') or obj.get('genesis')
    matches=obj.get('matches_expected') if 'matches_expected' in obj else obj.get('matchesExpected')
    finalized=obj.get('finalized_head') or obj.get('finalizedHead')
    if not (isinstance(genesis,str) and re.fullmatch(r'0x[0-9a-fA-F]{64}',genesis)
            and matches is True and finalized is not None):
        return {'ready':False,'reason':'CLI_CHAIN_FINALITY_NOT_VERIFIED'}
    return {'ready':True,'genesis':genesis.lower(),'finalized_head':str(finalized)}

def ready_to_send(conn, config=None, *, fetch=_json_response, cli_status=cli_network_status):
    if now()<LAUNCH_UTC:
        return {'ready':False,'reason':'BEFORE_OFFICIAL_LAUNCH_TARGET'}
    doc=official_testnet_state(fetch)
    put(conn,'network_status',doc['status'])
    if not doc['ready']:
        return {'ready':False,'reason':doc['status']}
    if config is None:
        return {'ready':False,'reason':'PRIVATE_CONFIG_NOT_CONFIGURED'}
    if doc['genesis'].lower()!=config['expected_genesis'].lower():
        return {'ready':False,'reason':'DOC_GENESIS_PIN_MISMATCH'}
    cli=cli_status()
    if not cli['ready']:
        return {'ready':False,'reason':cli.get('reason','CLI_NOT_READY')}
    if cli['genesis'].lower()!=doc['genesis'].lower():
        return {'ready':False,'reason':'RPC_GENESIS_PIN_MISMATCH'}
    return {'ready':True,'reason':'DOC_AND_RPC_FINALIZED_GENESIS_MATCH','genesis':cli['genesis']}

def do_direct_first(conn, config, *, run=subprocess.run):
    """Exactly one first capped test, UNKNOWN even for CLI rc0 until chain audit.

    Reserve attempt in SQLite *before* CLI may open escrow, preventing a crash
    from creating a second direct session. No auto-retry or recurring spends
    while chain finality and attribution remain unverified.
    """
    old=conn.execute('SELECT attempt_id FROM session_attempts LIMIT 1').fetchone()
    if old:
        return {'state':'BLOCKED_PRIOR_ATTEMPT_RECONCILE','attempt_id':old[0]}
    cli=shutil.which('flop')
    if not cli:
        return {'state':'BLOCKED_CLI_NOT_INSTALLED'}
    budget=Decimal(config['total_test_flop_budget'])
    if Decimal(config['max_flop'])>budget:
        raise ValueError('EXCEEDS_GLOBAL_BUDGET')
    eventid='first-live-direct'
    conn.execute("""INSERT INTO session_attempts
      (attempt_id,phase,started_utc,wallet,expected_genesis,miner,max_flop)
      VALUES (?,?,?,?,?,?,?)""",
      (eventid,'RESERVED_UNKNOWN_MAY_SUBMIT',utc(),config['wallet'],
       config['expected_genesis'],config['miner'],config['max_flop']))
    conn.commit()
    put(conn,'execution_mode','FIRST_TEST_IN_FLIGHT')
    cmd=[cli,'--network','testnet','--keystore',config['keystore'],'--password-env',
         'FLOP_KEY_PASSWORD','--json','session','run','--miner',config['miner'],
         '--model',config['model'],'--prompt',
         'Analyze FLOP Testnet official launch readiness and return one concise answer.',
         '--max-flop',config['max_flop'],'--via','auto','--endpoint',config['endpoint']]
    try:
        cp=run(cmd,capture_output=True,text=True,timeout=CLI_TIMEOUT,check=False)
        # Include no raw response or secret-bearing CLI outputs in mail / Git.
        # Store a bounded scrubbed summary, never treat rc==0 as settlement.
        parsed=None
        try:
            parsed=json.loads(cp.stdout.strip()) if cp.stdout.strip() else None
        except ValueError:
            pass
        result={'return_code':cp.returncode,
                'json_received':isinstance(parsed,dict),
                'output_sha256':hashlib.sha256(cp.stdout.encode()).hexdigest(),
                'stderr_sha256':hashlib.sha256(cp.stderr.encode()).hexdigest(),
                'has_channel':bool(isinstance(parsed,dict) and
                                   (parsed.get('channel') or parsed.get('channelId') or parsed.get('channel_id')))}
        phase='CLI_RESULT_NEEDS_CHAIN_FINALITY' if cp.returncode==0 and result['has_channel'] else 'UNKNOWN_MAY_HAVE_SUBMITTED'
        conn.execute("""UPDATE session_attempts SET phase=?,ended_utc=?,cli_result=?,last_error=? WHERE attempt_id=?""",
                     (phase,utc(),json.dumps(result,sort_keys=True),
                      None if phase.startswith('CLI_RESULT') else 'CLI_NO_VERIFIABLE_CHANNEL',eventid))
        conn.commit()
        put(conn,'execution_mode','RECONCILIATION_REQUIRED_NO_AUTO_RETRY')
        if phase!='CLI_RESULT_NEEDS_CHAIN_FINALITY':
            notify_error(conn,'DIRECT_SESSION_UNCERTAIN','CLI outcome cannot establish a finalized paid inference')
        else:
            enqueue(conn,'first-session-cli-pending','[FLOP] 首次测试已提交｜等待链上核验',
                    'CLI 返回了候选会话信息，但付款人、有效推理和最终结算尚未独立核实。\n'
                    '自动执行已暂停；不会将 CLI 返回码视为成功，也不会盲目再次付款。')
        return {'state':phase,'details':result}
    except (OSError,subprocess.TimeoutExpired) as exc:
        conn.execute('UPDATE session_attempts SET phase=?,ended_utc=?,last_error=? WHERE attempt_id=?',
                     ('UNKNOWN_MAY_HAVE_SUBMITTED',utc(),type(exc).__name__,eventid))
        conn.commit()
        put(conn,'execution_mode','RECONCILIATION_REQUIRED_NO_AUTO_RETRY')
        notify_error(conn,'DIRECT_SESSION_TIMEOUT_OR_OS_ERROR',type(exc).__name__)
        return {'state':'UNKNOWN_MAY_HAVE_SUBMITTED','reason':type(exc).__name__}

def mark_first_success_from_independent_verifier(conn, evidence):
    """Only called by a future, independently audited onchain verifier.

    This function is deliberately not reachable via CLI or imported JSON.
    No user-provided receipt, CLI stdout or test fixture can promote a session.
    """
    if evidence.get('verification_authority')!='DIRECT_CHAIN_VERIFIER_V1':
        raise ValueError('INDEPENDENT_VERIFIER_REQUIRED')
    row=conn.execute('SELECT * FROM session_attempts WHERE attempt_id=?',('first-live-direct',)).fetchone()
    if not row or row['chain_verified']:
        return False
    if evidence.get('network')!='testnet' or evidence.get('genesis')!=row['expected_genesis']:
        raise ValueError('NETWORK_GENESIS_MISMATCH')
    if evidence.get('payer')!=row['wallet'] or evidence.get('miner')!=row['miner']:
        raise ValueError('PARTY_MISMATCH')
    if evidence.get('verified_turns',0)<1 or evidence.get('finalized') is not True:
        raise ValueError('FINALIZED_TURN_MISSING')
    if not re.fullmatch(r'0x[0-9a-fA-F]{64}',str(evidence.get('settlement_tx',''))):
        raise ValueError('FINALIZED_SETTLEMENT_TX_MISSING')
    spent=Decimal(str(evidence.get('spent_flop','')))
    if not spent.is_finite() or not (Decimal('0')<spent<=Decimal(row['max_flop'])):
        raise ValueError('SPEND_OUT_OF_BOUNDS')
    conn.execute("""UPDATE session_attempts SET chain_verified=1,phase='DIRECT_CHAIN_VERIFIED',
        final_spent_flop=?,chain_tx=?,last_error=NULL WHERE attempt_id=?""",
        (str(spent),evidence['settlement_tx'],'first-live-direct'))
    conn.commit()
    put(conn,'last_verified_session_utc',utc())
    put(conn,'execution_mode','FIRST_TEST_VERIFIED_FURTHER_ADAPTER_REQUIRED')
    clear_error(conn)
    enqueue(conn,'first-real-test-success','[FLOP] 首次真实推理测试成功｜链上已核验',
            '测试网首次真实测试已经完成独立链上核验。\n'
            '钱包：'+row['wallet']+'\n'
            'Miner：'+row['miner']+'\n'
            '已结算有效消费：'+str(spent)+' Test FLOP\n'
            '链上结算交易：'+evidence['settlement_tx']+'\n'
            '当前状态：首测通过。长期自动消费仍需完成动态额度及归属验收。')
    return True

def digest_slot(now_local=None):
    d=now_local or now_bkk()
    # At 08:00 and 20:00 Bangkok. Missed mails catch up at next tick once.
    hour=8 if 8<=d.hour<20 else 20 if d.hour>=20 else -1
    effective_date=d.date() if hour!=-1 else d.date()-timedelta(days=1)
    if hour==-1: hour=20
    return effective_date.isoformat(),hour

def queue_summary(conn):
    if now_bkk().hour not in (8,20):
        return False
    today,hour=digest_slot()
    slot=f'{today}-{hour:02d}'
    key='summary-'+slot
    if conn.execute('SELECT 1 FROM flop_mail WHERE mail_key=?',(key,)).fetchone():
        return False
    rows=conn.execute('SELECT phase,COUNT(*) FROM session_attempts GROUP BY phase').fetchall()
    states=dict(rows)
    amounts=conn.execute("""SELECT final_spent_flop FROM session_attempts
             WHERE chain_verified=1 AND final_spent_flop IS NOT NULL""").fetchall()
    spent=sum((Decimal(row[0]) for row in amounts),Decimal(0))
    latest=get(conn,'last_verified_session_utc','无')
    mode=get(conn,'execution_mode','WAIT_FOR_TESTNET')
    net=get(conn,'network_status','UNVERIFIED')
    block=get(conn,'current_error') or '无'
    body=('\n'.join([
        '采样时区：Asia/Bangkok',
        '网络：'+net,
        '执行状态：'+mode,
        '已独立核验的 Testnet 推理消费：'+str(spent)+' FLOP',
        '已核验有效结算次数：'+str(sum(int(x['chain_verified']) for x in conn.execute('SELECT chain_verified FROM session_attempts'))),
        '尚未核验/可能已支付的会话：'+str(sum(v for k,v in states.items() if k not in ('DIRECT_CHAIN_VERIFIED',))),
        '最后一次成功：'+latest,
        '余额 / Faucet 可用配额：未核实',
        '当前异常：'+block,
        'FLOP 空投分配与 USD 收益：未确认',
        'Gmail SENT 必须独立回读才能视为送达。'
    ]))
    enqueue(conn,key,'[FLOP] 每12小时运行与有效消费报告｜'+slot,body)
    return True

def tick(*, fetch=_json_response, cli_status=cli_network_status, execution=do_direct_first):
    DATA.mkdir(parents=True,exist_ok=True,mode=0o700)
    conn=sqlite3.connect(MONITOR,timeout=10)
    conn.row_factory=sqlite3.Row
    ensure_state(conn)
    try:
        state={'ready':False,'reason':'NOT_CHECKED'}
        # Mail test is deliberately separate and mandatory before live auto-start.
        mail_preflight=conn.execute("SELECT status FROM flop_mail WHERE mail_key='first-mail-setup-test'").fetchone() if has_mail_table(conn) else None
        if now()<LAUNCH_UTC:
            put(conn,'network_status','WAITING_FOR_2026-11-24T07:00Z')
            put(conn,'execution_mode','PRELAUNCH_WAIT')
            state={'ready':False,'reason':'PRELAUNCH_WAIT'}
        else:
            try:
                try:
                    config=private_config()
                except (OSError,ValueError,KeyError) as exc:
                    config=None
                    notify_error(conn,'PRIVATE_CONFIG_NOT_READY',type(exc).__name__+': '+str(exc))
                state=ready_to_send(conn,config,fetch=fetch,cli_status=cli_status)
                if state['ready']:
                    if not mail_preflight or mail_preflight[0]!='SENT_VERIFIED':
                        notify_error(conn,'EMAIL_TEST_NOT_VERIFIED','Run mail-test and verify Gmail Sent before initiating paid Testnet session')
                    elif not conn.execute('SELECT 1 FROM session_attempts LIMIT 1').fetchone():
                        put(conn,'execution_mode','FIRST_SESSION_READY')
                        execution(conn,config)
                else:
                    if state['reason'] in ('PLANNED','UNVERIFIED_DOC_FORMAT','BEFORE_OFFICIAL_LAUNCH_TARGET'):
                        put(conn,'execution_mode','WAITING_FOR_CONFIRMED_TESTNET')
                    elif state['reason']!='PRIVATE_CONFIG_NOT_CONFIGURED':
                        notify_error(conn,'TESTNET_READINESS_GAP',state['reason'])
                    else:
                        put(conn,'execution_mode','WAITING_FOR_PRIVATE_CONFIG')
            except (OSError,TimeoutError,ValueError) as exc:
                notify_error(conn,'NETWORK_CHECK_FAILED',type(exc).__name__)
        queue_summary(conn)
        delivery=pump(conn)
        put(conn,'last_scheduler_tick_utc',utc())
        return {'ready':state,'delivery':delivery,'at':utc(),
                'mode':get(conn,'execution_mode','UNVERIFIED')}
    finally:
        conn.close()

def has_mail_table(conn):
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='flop_mail'").fetchone())

@contextmanager
def exclusive():
    DATA.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (DATA/'runtime.lock').open('a+') as f:
        try:
            fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('RUNTIME_ALREADY_ACTIVE')
        yield

def mail_test():
    conn=sqlite3.connect(MONITOR)
    conn.row_factory=sqlite3.Row
    ensure_state(conn)
    try:
        enqueue(conn,'first-mail-setup-test','[FLOP] 邮件通道首次验收',
                '这是 FLOP 本地 Agent 的一次真实邮件发送与 Gmail Sent 回读测试。\n'
                '不代表 Testnet 推理或空投资格已经通过。\n'
                '此测试邮件应当只出现一次。')
        result=pump(conn)
        row=conn.execute("SELECT status FROM flop_mail WHERE mail_key='first-mail-setup-test'").fetchone()
        return {'status':row['status'],'delivery':result,'actual_send_confirmed':row['status']=='SENT_VERIFIED'}
    finally:
        conn.close()

def snapshot():
    conn=sqlite3.connect(MONITOR)
    conn.row_factory=sqlite3.Row
    ensure_state(conn)
    try:
        results=dict(conn.execute('SELECT key,value FROM kv').fetchall())
        results['mail']=mail_status(conn)
        entry=conn.execute("SELECT status FROM flop_mail WHERE mail_key='first-mail-setup-test'").fetchone()
        results['mail_setup_test']=entry[0] if entry else 'NOT_EXECUTED'
        results['sessions']=[dict(x) for x in conn.execute(
            'SELECT attempt_id,phase,started_utc,ended_utc,wallet,max_flop,chain_verified,final_spent_flop,chain_tx,last_error FROM session_attempts')]
        results['errors']=[dict(x) for x in conn.execute(
            "SELECT at_utc,severity,code,details FROM runtime_events WHERE severity='ERROR' ORDER BY at_utc DESC LIMIT 10")]
        return results
    finally:
        conn.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['tick','mail-test','status','first-test'])
    args=parser.parse_args()
    with exclusive():
        if args.action=='mail-test': result=mail_test()
        elif args.action=='tick': result=tick()
        elif args.action=='first-test':
            from agent import offline_first_test
            result=offline_first_test()
        else: result=snapshot()
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':
    main()
