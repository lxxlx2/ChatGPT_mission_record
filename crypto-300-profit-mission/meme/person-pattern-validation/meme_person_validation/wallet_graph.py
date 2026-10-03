from dataclasses import dataclass
ROLES = {'HOLDING_WALLET','EXECUTION_WALLET','SOURCE_WALLET','TREASURY_WALLET','PLATFORM_FEE_PAYER','PLATFORM_COSIGNER','CEX_OR_BRIDGE','UNRESOLVED'}
@dataclass
class PersonWalletGraph:
    seed: dict
    def __post_init__(self):
        addresses=[w['address'] for w in self.seed['wallets']]
        if len(addresses)!=len(set(addresses)): raise ValueError('duplicate wallet')
        if any(w['role'] not in ROLES for w in self.seed['wallets']): raise ValueError('unknown role')
    @property
    def accepted(self):
        infra={w['address'] for w in self.seed['platform_addresses']}
        return {w['address'] for w in self.seed['wallets'] if w['ownership_conclusion']=='ACCEPTED_RESEARCH' and w['address'] not in infra and w['role'] not in {'PLATFORM_FEE_PAYER','PLATFORM_COSIGNER','CEX_OR_BRIDGE','UNRESOLVED'}}
    @property
    def unresolved(self):
        return set(self.seed['unresolved_wallets']) | {w['address'] for w in self.seed['wallets'] if w['ownership_conclusion']=='UNRESOLVED'}
    def accepts_at(self,address,t):
        return address in self.accepted and any(w['address']==address and (w.get('valid_from') is None or t>=w['valid_from']) and (w.get('valid_to') is None or t<w['valid_to']) for w in self.seed['wallets'])
    def status(self):
        return 'QUALIFICATION_BLOCKED' if self.unresolved or not self.seed['continuity_resolved'] else 'RESOLVED'
