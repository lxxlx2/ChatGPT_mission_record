"""Connected-capability bridge. No send implementation/credential in this process.

Commands prepare/invoke require REAL_GMAIL_ENABLED=true plus --real-gmail-canary.
invoke durably claims a slot immediately before the orchestrator calls the connected
Gmail action exactly once. Do not use a fresh DB to bypass an existing authorization.
"""
import argparse
import json
import os
import subprocess
import signal
from dataclasses import replace
from pathlib import Path
from mission_agent.db.repository import Repository
from mission_agent.config import Config
from mission_agent.clock import stamp
from mission_agent.models import Event
from mission_agent.hashing import canonical,loads,digest
from mission_agent.queue.batch import build_batch
from mission_agent.queue.remote import publish_remote
from mission_agent.queue.reconciliation import reconcile
from mission_agent.decision.fixture_consumer import consume
from mission_agent.transport.github import GitHubTransport,Conflict
from mission_agent.delivery.canary import Canary,subject,body


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['flow','prepare','invoke','result','recover','receipt','status'])
    p.add_argument('--root',type=Path,required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--recipient-hash',required=True);p.add_argument('--scenario',default='normal',choices=['normal','receipt-failure','optional-extra'])
    p.add_argument('--real-gmail-canary',action='store_true');p.add_argument('--input',type=Path)
    p.add_argument('--inject-persistence-failure',action='store_true');p.add_argument('--kill-after-failure',action='store_true')
    a=p.parse_args();a.root.mkdir(parents=True,exist_ok=True,mode=0o700);a.root.chmod(0o700)
    check=subprocess.run(['git','-C',str(a.root),'rev-parse','--is-inside-work-tree'],capture_output=True)
    if check.returncode==0:raise ValueError('PRIVATE_EVIDENCE_MUST_BE_OUTSIDE_GIT')
    repo=Repository(a.root/'mission.sqlite');c=Canary(repo,a.run_id,a.recipient_hash)
    id='phase2b:gmail:'+a.run_id+':'+a.scenario
    def emit(value):print(canonical(value).decode(),flush=True)
    enabled=os.environ.get('REAL_GMAIL_ENABLED')=='true'
    if a.command=='flow':
        event=replace(Event.synthetic('TEST_ACTION_CANDIDATE','SYNTH',stamp(repo.clock.now()),0,{'fixture_decision':'ACTIONABLE_RISK','test_only':True},a.scenario),event_id=id)
        repo.ingest(event);batch=build_batch(repo,Config.for_remote(a.root))
        if batch is None:raise ValueError('NO_NEW_PENDING_BATCH')
        mac=GitHubTransport('mac',a.run_id);gpt=GitHubTransport('gpt',a.run_id)
        publish_remote(repo,mac,batch['batch_id'])
        remote=gpt.read_batch(batch['batch_id']);receipt=consume(remote,repo.clock)
        key='phase2b-decision-current-sha'
        prior=repo.db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone()
        proof=gpt.publish_receipt(receipt,prior[0] if prior else None)
        repo.db.execute('INSERT INTO meta VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,proof.blob_sha))
        assert reconcile(repo,mac.read_receipt(batch['batch_id']))
        assert repo.db.execute('SELECT state FROM deliveries WHERE event_id=?',(id,)).fetchone()[0]=='DELIVERY_PENDING'
        emit({'event_id':id,'batch_id':batch['batch_id'],'state':'DELIVERY_PENDING'})
    elif a.command in ('prepare','invoke'):
        t=GitHubTransport('gpt',a.run_id);t._private()
        if a.command=='prepare':
            if not a.input:raise ValueError('FRESH_EXACT_SENT_PRECHECK_REQUIRED')
            pre=loads(a.input.read_bytes())
            from mission_agent.clock import parse_utc
            if pre['event_id']!=id or pre['exact_count']!=0 or (repo.clock.now()-parse_utc(pre['checked_at'])).total_seconds()>60:
                raise ValueError('INVALID_OR_STALE_PRECHECK')
            slot=c.prepare(id,a.recipient_hash,[],True,enabled,a.real_gmail_canary)
            emit({'slot':slot,'state':'DELIVERY_SENDING','budget':c.budget()})
        else:
            result=c.invoke(id,enabled,a.real_gmail_canary,True)
            result.update({'event_id':id,'run_id':a.run_id,'scenario':a.scenario,'to':'me','subject':subject(id),
                           'body':body(id,a.run_id,a.scenario,result['invoked_at']),'budget':c.budget()})
            emit(result)
    elif a.command=='result':
        value=loads(a.input.read_bytes());a.input.unlink()
        c.result(id,value['classification'],value.get('provider_id'),a.inject_persistence_failure)
        emit({'state':c.intent(id)['recovery_state'],'budget':c.budget(),'injected_failure':a.inject_persistence_failure})
        if a.kill_after_failure:
            if not a.inject_persistence_failure:raise ValueError('KILL_ONLY_AFTER_CONTROLLED_FAILURE')
            os.kill(os.getpid(),signal.SIGKILL)
    elif a.command=='recover':
        if not a.input:raise ValueError('FULL_GMAIL_READBACK_REQUIRED')
        try:value=loads(a.input.read_bytes());state=c.recover(id,value['messages'])
        finally:a.input.unlink(missing_ok=True)  # No raw Gmail address/body retained in runtime.
        emit({'state':state,'budget':c.budget()})
    elif a.command=='receipt':
        row=repo.db.execute('SELECT b.* FROM batches b JOIN batch_items i USING(batch_id) WHERE i.event_id=?',(id,)).fetchone()
        decision=repo.db.execute('SELECT decision FROM decisions WHERE event_id=?',(id,)).fetchone()[0]
        receipt=c.receipt(id,decision,row['batch_id'],row['payload_sha256'])
        gpt=GitHubTransport('gpt',a.run_id)
        path=gpt._path('delivery',id);gpt.write('gpt-data',path,receipt,immutable=True)
        key='phase2b-delivery-current-sha';prior=repo.db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone()
        proof=gpt.write('gpt-data',gpt._path('delivery'),receipt,prior[0] if prior else None)
        read=gpt.read('gpt-data',path)
        assert read.data==canonical(receipt) and receipt['receipt_sha256']==digest({k:v for k,v in receipt.items() if k!='receipt_sha256'})
        repo.db.execute('INSERT INTO meta VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,proof.blob_sha))
        (a.root/(a.scenario+'-receipt-safe.json')).write_bytes(canonical(receipt));(a.root/(a.scenario+'-receipt-safe.json')).chmod(0o600)
        emit({'receipt_remote_verified':True,'receipt_hash_verified':True,'state':'DELIVERED','budget':c.budget()})
    else:
        rows=[{'slot':r['slot'],'invoked':r['invoked_at'] is not None,'state':r['recovery_state'],'result':r['provider_result_class']} for r in repo.db.execute('SELECT * FROM canary_intents ORDER BY slot')]
        emit({'budget':c.budget(),'slots':rows})
    repo.close()


if __name__=='__main__':main()
