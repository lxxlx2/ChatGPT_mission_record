"""Import one existing local CLI receipt, under the existing runtime lock.
No network access, signing, fresh wallet, or scheduler creation.
"""
import argparse,json,sqlite3
from pathlib import Path
import runtime,cycle,faucet

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--receipt',required=True,type=Path)
    p.add_argument('--opened-height',required=True,type=int)
    p.add_argument('--endpoint',required=True)
    p.add_argument('--model',required=True)
    p.add_argument('--escrow',required=True)
    a=p.parse_args()
    with runtime.exclusive():
        wallet=json.loads(faucet.IDENTITY.read_text())['address']
        receipt=json.loads(a.receipt.read_text())
        with sqlite3.connect(runtime.MONITOR,timeout=10) as conn:
            conn.row_factory=sqlite3.Row
            runtime.ensure_state(conn)
            result=cycle.stage_manual(conn,wallet,receipt,a.opened_height,a.endpoint,a.model,a.escrow)
        print(result)
if __name__=='__main__':main()

