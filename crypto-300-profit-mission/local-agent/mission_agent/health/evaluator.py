from ..clock import parse_utc

SOURCE_FIELDS=('clock_offset_ms','network_status','github_sync_lag_sec','price_assets_live','price_max_age_sec',
               'frank_rpc_last_success_age_sec','frank_cursor_gap','monster_universe_age_sec','nft_required_source_success_ratio')


def evaluate(snapshot,now,budget_bytes):
    if now>parse_utc(snapshot['valid_until']):
        return {'overall':'UNHEALTHY','reason':'UNHEALTHY_STALE_HOST'}
    used=snapshot.get('storage_used_bytes')
    if isinstance(used,int) and used>budget_bytes*95//100:
        return {'overall':'UNHEALTHY','reason':'UNHEALTHY_DISK'}
    if snapshot.get('sqlite_writable') is False:
        return {'overall':'UNHEALTHY','reason':'SQLITE_NOT_WRITABLE'}
    if isinstance(used,int) and used>budget_bytes*80//100:
        return {'overall':'DEGRADED','reason':'DEGRADED_DISK'}
    if any(snapshot.get(k) in (None,'UNKNOWN') for k in SOURCE_FIELDS):
        return {'overall':'UNKNOWN','reason':'COLLECTORS_NOT_IMPLEMENTED'}
    return {'overall':'HEALTHY','reason':'ALL_CONFIGURED_FIXTURE_METRICS_PRESENT'}
