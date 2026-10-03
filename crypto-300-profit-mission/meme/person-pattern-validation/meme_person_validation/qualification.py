REQUIRED={'wallet_graph','history','reconciliation','causality','executable_replay','robustness','negative_controls','base_rate','train','validation','holdout','frozen_config','preregistered_profitability'}
def qualify(gates,count,minimum=30):
    if minimum<30: raise ValueError('MINIMUM_SAMPLE_BELOW_CANONICAL_POLICY')
    failed=sorted(k for k in REQUIRED if gates.get(k) is not True)
    if not gates.get('history'): status='DATA_BLOCKED'
    elif not gates.get('wallet_graph'): status='QUALIFICATION_BLOCKED'
    elif count<minimum: status='INSUFFICIENT_SAMPLE'
    elif failed: status='NO_VALIDATED_PATTERN'
    else: status='RESEARCH_QUALIFICATION_PASSED'
    return {'status':status,'failed_gates':failed,'valid_episode_count':count,'minimum_episode_count':minimum,'PERSON_PATTERN':'OBSERVE_ONLY','production_trading':'NO_GO','validated_pattern_count':int(status=='RESEARCH_QUALIFICATION_PASSED'),'production_enablement':'SEPARATE_USER_AUTHORIZATION_AND_REAL_FORWARD_REQUIRED'}
