"""One-shot existing delivery component; no scanner, automation or credentials created."""
import argparse,fcntl,json
from pathlib import Path
from mission_agent.signals.store import Ledger
from mission_agent.signals.gmail import GmailOutbox,CredentialBlocked
from mission_agent.signals.gmail_api import existing_provider

def delivery_flags(ledger):
    # Read projection: explicit forbidden bit for EVERY historical signal without
    # rewriting immutable signal bodies, hashes or the frozen state machine.
    ledger.db.execute("""CREATE VIEW IF NOT EXISTS signal_delivery_flags AS
        SELECT signal_id,json_extract(body,'$.delivery_mode') AS delivery_mode,
        CASE WHEN json_extract(body,'$.delivery_mode')='LIVE'
             AND COALESCE(json_extract(body,'$.delivery_forbidden'),0)=0
             THEN 0 ELSE 1 END AS delivery_forbidden FROM signals""")

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    with a.db.with_suffix('.gmail-delivery.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);ledger=Ledger(a.db);delivery_flags(ledger);outbox=GmailOutbox(ledger);provider=existing_provider(a.db.parent/'gmail-existing-source.json');outbox.sync()
        if a.check:
            ready=False
            if provider:
                try:provider.ready();ready=True
                except CredentialBlocked:pass
            print(json.dumps({'credential_source_exists':provider is not None,'credential_ready':ready,'sender_implementation_exists':True,'sent_readback_implementation_exists':True,'outbox':outbox.summary(),'gmail_status':'DELIVERY_READY' if ready else 'CREDENTIAL_BLOCKED'}))
        else:print(json.dumps(outbox.drain(provider)))
        ledger.db.close()
if __name__=='__main__':main()
