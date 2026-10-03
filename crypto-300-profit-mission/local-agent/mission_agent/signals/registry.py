"""Future multiple wallets per person, currently Frank is the sole enabled person."""
import json
from pathlib import Path

def load(path):
    value=json.loads(Path(path).read_text())
    persons=[p for p in value['persons'] if p.get('enabled',False)]
    if [p['person_id'] for p in persons]!=['frank']: raise ValueError('FRANK_ONLY_ENABLED_REQUIRED')
    wallets={}
    for p in persons:
        for w in p['wallets']:
            if w['chain']!='solana':raise ValueError('SOLANA_ONLY')
            if w['address'] in wallets:raise ValueError('DUPLICATE_WALLET')
            wallets[w['address']]=p['person_id']
    if not wallets:raise ValueError('ENABLED_WALLET_REQUIRED')
    return value, wallets
