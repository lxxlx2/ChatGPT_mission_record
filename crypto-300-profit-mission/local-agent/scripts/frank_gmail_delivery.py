"""One-shot existing delivery component; no scanner, automation or credentials created."""
import argparse,fcntl,json
from pathlib import Path
from mission_agent.signals.store import Ledger
from mission_agent.signals.gmail import GmailOutbox,CredentialBlocked
from mission_agent.signals.gmail_api import existing_provider

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    with a.db.with_suffix('.gmail-delivery.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);ledger=Ledger(a.db);outbox=GmailOutbox(ledger);provider=existing_provider(a.db.parent/'gmail-existing-source.json');outbox.sync()
        if a.check:
            ready=False
            if provider:
                try:provider.ready();ready=True
                except CredentialBlocked:pass
            print(json.dumps({'credential_source_exists':provider is not None,'credential_ready':ready,'sender_implementation_exists':True,'sent_readback_implementation_exists':True,'outbox':outbox.summary(),'gmail_status':'DELIVERY_READY' if ready else 'CREDENTIAL_BLOCKED'}))
        else:print(json.dumps(outbox.drain(provider)))
        ledger.db.close()
if __name__=='__main__':main()
