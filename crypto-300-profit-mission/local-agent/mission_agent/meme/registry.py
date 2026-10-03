"""Explicit user registry; wallet multiplicity never becomes person multiplicity."""
from ..hashing import digest

class Registry:
    def __init__(self, value, *, namespace='LIVE'):
        if value.get('schema_version') != 1 or value.get('namespace') != namespace:
            raise ValueError('REGISTRY_SCHEMA_NAMESPACE')
        if namespace not in ('LIVE', 'TEST'): raise ValueError('NAMESPACE')
        self.namespace, self.persons, self.wallets = namespace, {}, {}
        for original in value['persons']:
            p = {**original, 'person_pattern_state': original.get('person_pattern_state', 'OBSERVE_ONLY')}
            if not p.get('person_id') or p['person_id'] in self.persons: raise ValueError('PERSON_ID')
            if p['person_pattern_state'] not in ('OBSERVE_ONLY', 'SIGNAL_ENABLED'): raise ValueError('PATTERN_STATE')
            if namespace == 'LIVE' and not p.get('approval', '').startswith('USER_CONFIRMED'):
                raise ValueError('EXPLICIT_USER_APPROVAL_REQUIRED')
            if namespace=='LIVE' and p['person_id']!='frank' and p['person_pattern_state']=='SIGNAL_ENABLED':
                acceptance=p.get('pattern_acceptance',{})
                if acceptance.get('status')!='USER_ACCEPTED_HISTORY_REPLAY' or len(acceptance.get('evidence_sha256',''))!=64:raise ValueError('PERSON_PATTERN_HISTORY_ACCEPTANCE_REQUIRED')
            self.persons[p['person_id']] = p
            for w in p['wallets']:
                if w.get('chain') != 'solana' or not w.get('address'): raise ValueError('WALLET_CHAIN')
                key = (w['chain'], w['address'])
                if key in self.wallets: raise ValueError('WALLET_PERSON_AMBIGUOUS')
                self.wallets[key] = (p['person_id'], w.get('verified') is True)
        self.sha256 = digest(value)
    def person(self, chain, wallet):
        p, verified = self.wallets[(chain, wallet)]
        if not verified: raise ValueError('VERIFIED_WALLET_REQUIRED')
        return self.persons[p]
