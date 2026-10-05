from datetime import datetime,timezone
from ..clock import stamp
from ..hashing import digest
from .rules import VERSION,hits

def candidate(bar,f):
 rules=hits(f,bar.asset)
 if not bar.is_closed or f['missing_data'] or not rules:return None
 end=bar.close_time_utc
 value={'event_id':f'price:{bar.asset}:{VERSION}:{end}:'+','.join(rules),'event_type':'RAW_PRICE_CANDIDATE','rule_version':VERSION,'rule_ids':rules,'asset':bar.asset,
        'observed_at':stamp(datetime.fromtimestamp(end/1000,timezone.utc)),'window_end':end,'price':bar.close,
        'returns':{k:f['return_'+k] for k in ('5m','15m','1h','4h','24h')},
        'reference_btc_returns':f['reference_btc_returns'],
        'high_24h':f['high_24h'],'low_24h':f['low_24h'],'reversal_15m':f['reversal_15m'],'realized_vol_5m':f['realized_vol_5m'],
        'vol_median_24h':f['trailing_24h_vol_median'],'source':bar.venue,'source_freshness':'CANONICAL_CLOSED_1M','missing_data':False,'evidence_version':'PRICE_FEATURE_V1'}
 return {**value,'payload_sha256':digest(value)}
