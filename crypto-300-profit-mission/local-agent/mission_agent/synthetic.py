"""Reproducible >=50-event workload; all payloads and decisions are fixtures."""
import copy
import random
import resource
import sys
import time
from datetime import timedelta
from .clock import FakeClock,stamp
from .models import Event
from .hashing import canonical
from .db.repository import Repository
from .queue.batch import build_batch,publish
from .queue.reconciliation import reconcile
from .transport.local_file import LocalTransport
from .decision.fixture_consumer import consume
from .delivery.mock_gmail import MockGmail
from .delivery.state_machine import DeliveryEngine
from .health.model import snapshot,storage_bytes


def run(config,count=60,seed=1729):
    if count<50:raise ValueError('synthetic E2E requires >=50 events')
    if (config.runtime_root/'mission.sqlite').exists():
        raise ValueError('use a fresh runtime directory for independent E2E evidence')
    config.runtime_root.mkdir(parents=True,exist_ok=True,mode=0o700)
    clock=FakeClock();start=time.perf_counter();cpu=time.process_time()
    repo=Repository(config.runtime_root/'mission.sqlite',clock)
    provider=MockGmail(config.runtime_root/'mock-gmail.sqlite',clock)
    transport=LocalTransport(config.runtime_root/'runtime-local')
    try:
        labels=['IGNORE','WATCH','ACTIONABLE_RISK','ACTIONABLE_OPPORTUNITY']
        types=['RAW_PRICE_CANDIDATE','RAW_FRANK_CANDIDATE','RAW_MONSTER_CANDIDATE','RAW_NFT_CANDIDATE','TEST_ACTION_CANDIDATE']
        events=[Event.synthetic(types[i%5],'SYNTH',stamp(clock.now()-timedelta(minutes=i)),int(i%5==0),
                                {'fixture_decision':labels[i%4],'ordinal':i,'padding':'x'*1400},f'{seed}:{i}') for i in range(count)]
        shuffled=events.copy();random.Random(seed).shuffle(shuffled)
        for event in shuffled:repo.ingest(event)
        duplicates=sum(repo.ingest(events[0])=='DUPLICATE' for _ in range(3))
        repo.ingest_json('{broken synthetic payload')
        original={e.event_id for e in events}
        before={r[0] for r in repo.db.execute('SELECT event_id FROM candidates')}
        repo.close();repo=Repository(config.runtime_root/'mission.sqlite',clock)
        after={r[0] for r in repo.db.execute('SELECT event_id FROM candidates')}
        restart_loss=len(before-after)
        rejected_accepts=[];batch_sizes=[];normal_max=urgent_max=0;backlog_snapshots=[]
        # A stale immutable batch is explicitly expired and requeued, never silently consumed.
        stale=build_batch(repo,config);publish(repo,transport,stale['batch_id'])
        clock.advance(config.batch_ttl_seconds+1)
        try:consume(stale,clock);stale_accepted=1
        except ValueError:stale_accepted=0
        repo.expire_batch(stale['batch_id'])
        while (batch:=build_batch(repo,config)) is not None:
            batch_sizes.append(len(canonical(batch)))
            normal_max=max(normal_max,sum(i['priority']==0 for i in batch['items']))
            urgent_max=max(urgent_max,sum(i['priority']==1 for i in batch['items']))
            publish(repo,transport,batch['batch_id']);receipt=consume(transport.read_batch(batch['batch_id']),clock)
            bad=copy.deepcopy(receipt);bad['input_payload_sha256']='0'*64
            rejected_accepts.append(reconcile(repo,bad))
            bad=copy.deepcopy(receipt);bad['decisions'][0]['event_id']='unknown-synthetic-id'
            rejected_accepts.append(reconcile(repo,bad))
            transport.publish_receipt(receipt)
            assert reconcile(repo,transport.read_receipt(batch['batch_id']))
            backlog_snapshots.append(repo.db.execute("SELECT COUNT(*) FROM outbox WHERE state='PENDING'").fetchone()[0])
        engine=DeliveryEngine(repo,provider,config)
        action_ids=[r[0] for r in repo.db.execute("SELECT event_id FROM deliveries WHERE state='DELIVERY_PENDING' ORDER BY event_id")]
        for i,id in enumerate(action_ids):
            engine.run(id,'TIMEOUT_AFTER_SEND' if i==0 else 'SENT_BUT_RECEIPT_FAIL' if i==1 else 'READBACK_RECOVERS_LATER' if i==2 else 'SUCCESS')
        for _ in range(3):
            for id in action_ids:engine.run(id)
        clock.advance(180)
        repo.close();provider.close()
        repo=Repository(config.runtime_root/'mission.sqlite',clock);provider=MockGmail(config.runtime_root/'mock-gmail.sqlite',clock)
        engine=DeliveryEngine(repo,provider,config)
        for id in action_ids:engine.run(id)
        value=snapshot(repo,config,last_e2e='UNKNOWN');transport.publish_health(value)
        transport.publish_delivery({'schema_version':1,'mode':'MOCK','states':[dict(r) for r in repo.db.execute('SELECT event_id,state,provider_message_id FROM deliveries')]})
        stored={r[0] for r in repo.db.execute('SELECT event_id FROM candidates')}
        accounted={r[0] for r in repo.db.execute("SELECT event_id FROM outbox WHERE state IN('PENDING','BATCHED','PUBLISHED','QUARANTINED')")}
        decision_ids={r[0] for r in repo.db.execute('SELECT event_id FROM decisions')}
        delivered=repo.db.execute("SELECT COUNT(*) FROM deliveries WHERE state='DELIVERED'").fetchone()[0]
        wall=time.perf_counter()-start;cpu_sec=time.process_time()-cpu
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform!='darwin':rss*=1024
        metrics={'synthetic_events_created':len(stored),'corrupt_inputs_quarantined':repo.db.execute("SELECT COUNT(*) FROM quarantine WHERE reason='CORRUPT_INPUT'").fetchone()[0],'duplicate_replays_suppressed':duplicates,
                 'silent_event_loss':len(original-stored)+len(original-(decision_ids|accounted)),
                 'duplicate_candidate':sum(r[0]-1 for r in repo.db.execute('SELECT COUNT(*) FROM candidates GROUP BY event_id HAVING COUNT(*)>1')),
                 'accepted_receipt_mismatch':sum(rejected_accepts),'unknown_receipt_accepted':sum(rejected_accepts[1::2]),
                 'hash_mismatch_accepted':sum(rejected_accepts[::2]),'restart_event_loss':restart_loss,
                 'over_100kb_batch_emitted':sum(x>100000 for x in batch_sizes),'max_batch_bytes':max(batch_sizes),
                 'normal_max_per_batch':normal_max,'urgent_max_per_batch':urgent_max,'batches_consumed':len(batch_sizes),
                 'unprocessed_backlog_silently_removed':len(original-(decision_ids|accounted)),
                 'uncertain_blind_resend':sum(max(0,provider.calls(id)-1) for id in action_ids),
                 'stale_batch_accepted':stale_accepted,'fixture_decisions':len(decision_ids),'mock_delivered':delivered,
                 'mock_sent_count':provider.count(),'final_backlog':backlog_snapshots[-1],'health_overall':value['overall'],
                 'input_candidate_bytes':sum(len(canonical(__import__('mission_agent.queue.batch',fromlist=['item']).item(r))) for r in repo.db.execute('SELECT * FROM candidates')),
                 'benchmark':{'events':count,'wall_seconds':format(wall,'.6f'),'cpu_seconds':format(cpu_sec,'.6f'),
                              'process_cpu_percent_of_one_core':format(100*cpu_sec/wall,'.2f'),'peak_rss_bytes':rss,
                              'runtime_storage_bytes':storage_bytes(config.runtime_root),
                              'sqlite_bytes':repo.path.stat().st_size,'wal_bytes':(config.runtime_root/'mission.sqlite-wal').stat().st_size,
                              'network_bytes':0,'github_runtime_writes':0,'real_gmail_sends':0}}
        from .health.evaluator import evaluate
        stale_health={**value,'overall':'HEALTHY'}
        metrics['stale_healthy_accepted_as_healthy']=int(evaluate(stale_health,clock.now()+timedelta(hours=1),config.disk_budget_bytes)['overall']=='HEALTHY')
        metrics['gate_pass']=all(metrics[k]==0 for k in ('silent_event_loss','duplicate_candidate','accepted_receipt_mismatch','unknown_receipt_accepted','hash_mismatch_accepted','restart_event_loss','over_100kb_batch_emitted','unprocessed_backlog_silently_removed','uncertain_blind_resend','stale_batch_accepted','stale_healthy_accepted_as_healthy')) and delivered==len(action_ids) and len(decision_ids)==count
        return metrics
    finally:
        provider.close();repo.close()
