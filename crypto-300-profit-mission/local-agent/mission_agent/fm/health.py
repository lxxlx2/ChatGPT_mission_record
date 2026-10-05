"""Data-plane health with unknowns explicit; no model or investment conclusions."""
def disk_state(used,budget=5_000_000_000):
    if used<0 or budget<=0:raise ValueError('INVALID_DISK_INPUT')
    return 'UNHEALTHY_DISK' if used*100>=budget*95 else 'DEGRADED_DISK' if used*100>=budget*80 else 'HEALTHY_DISK'

def snapshot(frank=None,monster=None,used=0):
    return {'frank':{'rpc_available':None,'last_signature_age':None,'cursor_gap':None,'last_normalized_tx_age':None,'unavailable_history_count':None,'queue_pending':None,**(frank or {})},'monster':{'universe_size':None,'market_data_age':None,'symbols_failed':None,'candidate_scan_age':None,'derivatives_enrichment_age':None,'queue_pending':None,**(monster or {})},'disk':{'bytes':used,'soft_budget':5_000_000_000,'state':disk_state(used)}}
