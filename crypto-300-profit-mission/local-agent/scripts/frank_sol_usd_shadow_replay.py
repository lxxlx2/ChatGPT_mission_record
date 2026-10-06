"""Replay Frank V1 with durable SOL->USD event-time normalization.

REVIEW/RESEARCH ONLY. This script never edits the source forward.sqlite, never
sends notifications, and always runs Engine(dry_run=True). Historical SOL/USD
references are persisted in the target DB before they are consumed by the model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from mission_agent.market.sol_usd import BinanceSolUsdHistoryClient, SOL_QUOTE_ASSETS, normalize_classification, reference_key
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy
from mission_agent.signals.store import Ledger
from mission_agent.mission_control.db import open_production_ro, utc

ROOT=Path(__file__).parents[1]
DEFAULT_POLICY=ROOT/'config'/'frank_local_signal_v1.json'


def _ensure_reference_table(db):
    db.execute('''CREATE TABLE IF NOT EXISTS sol_usd_references(
        reference_key TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        status TEXT NOT NULL,
        block_time INTEGER NOT NULL,
        content_hash TEXT NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')


def _hash(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def _reference(db,client,block_time:int):
    key=reference_key(block_time)
    row=db.execute('SELECT body FROM sol_usd_references WHERE reference_key=?',(key,)).fetchone()
    if row:return json.loads(row[0])
    value=client.reference(block_time)
    encoded=json.dumps(value,sort_keys=True,separators=(',',':'))
    db.execute('INSERT INTO sol_usd_references VALUES(?,?,?,?,?,?,?)',(key,value.get('source','UNAVAILABLE'),value.get('status','UNAVAILABLE'),int(block_time),_hash(value),encoded,utc()))
    return value


def _signal_index(db):
    rows=db.execute('SELECT person_id,mint,episode_id,signal_type,stage,triggered_at,body FROM (SELECT person_id,mint,episode_id,signal_type,stage,CAST(created_at AS INTEGER) triggered_at,body FROM signals) ORDER BY triggered_at,signal_type').fetchall()
    result=[]
    for row in rows:
        item=dict(row);body=json.loads(item.pop('body'));item['triggering_signature']=body.get('triggering_signature') or body.get('latest_trade_signature');result.append(item)
    return result


def _mint_has_sol(source_db):
    result=set()
    for row in source_db.execute("SELECT mint,body FROM signatures WHERE json_extract(body,'$.classification')='ACTIVE_TRADE'"):
        body=json.loads(row['body']);trade=body.get('trade') or {}
        if trade.get('quote_asset') in SOL_QUOTE_ASSETS:result.add(row['mint'] if 'mint' in row.keys() else trade.get('mint'))
    return result


def replay(source_path:Path,target_path:Path,policy_path:Path,client=None):
    source=open_production_ro(source_path);target=Ledger(target_path);_ensure_reference_table(target.db);engine=Engine(target,load_policy(policy_path),dry_run=True);client=client or BinanceSolUsdHistoryClient()
    counters={'signatures':0,'active_trades':0,'sol_trades':0,'sol_resolved':0,'sol_unresolved':0,'usdc_trades':0}
    sol_mints=set()
    rows=source.execute('SELECT wallet,signature,person_id,slot,block_time,raw_hash,raw_reference,body FROM signatures ORDER BY block_time,slot,signature').fetchall()
    for row in rows:
        counters['signatures']+=1;classified=json.loads(row['body']);trade=classified.get('trade') or {}
        if classified.get('classification')=='ACTIVE_TRADE':
            counters['active_trades']+=1
            if trade.get('quote_asset') in SOL_QUOTE_ASSETS:
                counters['sol_trades']+=1;sol_mints.add(trade.get('mint'))
                ref=_reference(target.db,client,int(row['block_time'])) if row['block_time'] is not None else {'status':'UNAVAILABLE','reason':'BLOCK_TIME_MISSING'}
                classified=normalize_classification(classified,ref,for_model=True)
                if (classified.get('trade') or {}).get('quote_normalization')=='SOL_TO_USD_SHADOW_EQUIVALENT':counters['sol_resolved']+=1
                else:counters['sol_unresolved']+=1
            else:counters['usdc_trades']+=1
        target.put(row['person_id'],classified,row['raw_hash'] or row['signature'],row['raw_reference'] or 'SOURCE_FORWARD_SQLITE',dry_run=True)
        engine.drain()
    source_signals=_signal_index(source);shadow_signals=_signal_index(target.db)
    def key(x):return (x['person_id'],x['mint'],x['episode_id'],x['signal_type'],x['stage'],x.get('triggering_signature'))
    source_keys={key(x) for x in source_signals};shadow_keys={key(x) for x in shadow_signals}
    added=[x for x in shadow_signals if key(x) not in source_keys];missing=[x for x in source_signals if key(x) not in shadow_keys]
    source_usdc={key(x) for x in source_signals if x['mint'] not in sol_mints};shadow_usdc={key(x) for x in shadow_signals if x['mint'] not in sol_mints}
    report={'schema_version':1,'mode':'SHADOW_REPLAY_ONLY','source_db':str(source_path),'target_db':str(target_path),'policy_path':str(policy_path),'counters':counters,'source_signal_count':len(source_signals),'shadow_signal_count':len(shadow_signals),'sol_mints':sorted(x for x in sol_mints if x),'sol_added_signals':added,'missing_source_signals':missing,'usdc_regression_pass':source_usdc==shadow_usdc,'usdc_source_only':[list(x) for x in sorted(source_usdc-shadow_usdc)],'usdc_shadow_only':[list(x) for x in sorted(shadow_usdc-source_usdc)],'production_trading':'NO_GO'}
    source.close();target.db.commit();target.db.close();return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--target',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--policy',type=Path,default=DEFAULT_POLICY);a=p.parse_args()
    if a.target.exists():raise SystemExit('TARGET_MUST_NOT_EXIST')
    a.target.parent.mkdir(parents=True,exist_ok=True);result=replay(a.source,a.target,a.policy);a.report.write_text(json.dumps(result,indent=2,sort_keys=True));print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
