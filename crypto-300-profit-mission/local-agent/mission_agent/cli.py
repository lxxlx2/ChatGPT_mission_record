import argparse
import json
import os
from pathlib import Path
from .config import Config
from .clock import Clock
from .models import Event
from .hashing import loads,canonical
from .db.repository import Repository
from .queue.batch import build_batch,publish
from .queue.reconciliation import reconcile
from .transport.local_file import LocalTransport
from .decision.fixture_consumer import consume
from .delivery.mock_gmail import MockGmail
from .delivery.state_machine import DeliveryEngine
from .health.model import snapshot


def default_root():
    return Path.home()/'Library'/'Application Support'/'CryptoMission'/'phase1-synthetic'


def main(argv=None):
    parser=argparse.ArgumentParser(description='Synthetic-only LOCAL_FILE/mock Gmail; no real collectors/send')
    parser.add_argument('--runtime-root',type=Path,default=default_root())
    sub=parser.add_subparsers(dest='command',required=True)
    event=sub.add_parser('synthetic-event')
    event.add_argument('--event-type',required=True);event.add_argument('--asset')
    event.add_argument('--observed-time',required=True);event.add_argument('--priority',type=int,choices=[0,1],default=0)
    event.add_argument('--payload',required=True);event.add_argument('--seed',default='0')
    sub.add_parser('cycle');sub.add_parser('health')
    demo=sub.add_parser('synthetic-e2e');demo.add_argument('--events',type=int,default=60);demo.add_argument('--seed',type=int,default=1729)
    sub.add_parser('cleanup')
    args=parser.parse_args(argv)
    os.umask(0o077)
    config=Config(args.runtime_root)
    config.runtime_root.mkdir(parents=True,exist_ok=True,mode=0o700)
    if args.command=='synthetic-e2e':
        from .synthetic import run
        print(json.dumps(run(config,args.events,args.seed),sort_keys=True));return 0
    repo=Repository(config.runtime_root/'mission.sqlite',policy=config.delivery_policy,disk_budget_bytes=config.disk_budget_bytes)
    transport=LocalTransport(config.runtime_root/'runtime-local',config.disk_budget_bytes)
    provider=None
    try:
        if args.command=='synthetic-event':
            event=Event.synthetic(args.event_type,args.asset,args.observed_time,args.priority,loads(args.payload),args.seed)
            print(json.dumps({'event_id':event.event_id,'result':repo.ingest(event)}))
        elif args.command=='cycle':
            provider=MockGmail(config.runtime_root/'mock-gmail.sqlite',repo.clock)
            # Resume immutable built/published batches before adding a new page.
            ids=[r[0] for r in repo.db.execute("SELECT batch_id FROM batches WHERE state IN('BUILT','PUBLISHED') ORDER BY created_at,batch_id")]
            if not ids:
                batch=build_batch(repo,config);ids=[batch['batch_id']] if batch else []
            for id in ids:
                from .clock import parse_utc
                row=repo.db.execute('SELECT * FROM batches WHERE batch_id=?',(id,)).fetchone()
                # A persisted receipt can be valid even if local recovery occurs after TTL.
                # Replay exact bytes rather than regenerate timestamp-bearing immutable receipts.
                try:
                    receipt=transport.read_receipt(id)
                except FileNotFoundError:
                    if repo.clock.now()>parse_utc(row['valid_until']):
                        repo.expire_batch(id);continue
                    publish(repo,transport,id)
                    receipt=consume(transport.read_batch(id),repo.clock)
                    transport.publish_receipt(receipt)
                if not reconcile(repo,receipt):
                    raise ValueError('receipt rejected')
            engine=DeliveryEngine(repo,provider,config)
            for r in repo.db.execute("SELECT event_id FROM deliveries WHERE state IN('DELIVERY_PENDING','DELIVERY_SENDING','DELIVERY_UNCERTAIN')").fetchall():
                engine.run(r[0])
            transport.publish_delivery({'schema_version':1,'mode':'MOCK','states':[dict(r) for r in repo.db.execute('SELECT event_id,state,provider_message_id FROM deliveries ORDER BY event_id')]})
            print(json.dumps(repo.counts(),sort_keys=True))
        elif args.command=='health':
            value=snapshot(repo,config);transport.publish_health(value);print(json.dumps(value,sort_keys=True))
        elif args.command=='cleanup':
            from .retention import compress_terminal
            print(json.dumps({'compressed_acknowledged_artifacts':compress_terminal(repo,transport)}))
    finally:
        if provider:provider.close()
        repo.close()
    return 0


if __name__=='__main__':
    raise SystemExit(main())
