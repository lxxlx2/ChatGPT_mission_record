"""Compact sealed mechanical evidence; offline outputs never become forward observations."""
import math
from datetime import datetime,timezone
from ..hashing import seal,digest,canonical

def number(value):
 return format(float(value),'.8g') if value is not None and math.isfinite(float(value)) else None

def build(entity,symbols,venues,observed_ms,first_activation_ms,pathways,priority,feature,*,context):
 if context not in ('HISTORICAL_REPLAY','FORWARD_SHADOW'):raise ValueError('MONSTER_CONTEXT_REQUIRED')
 if type(priority) is not int or not 0<=priority<=100:raise ValueError('MECHANICAL_PRIORITY_RANGE')
 identity={'entity':entity,'observed_ms':int(observed_ms),'paths':sorted(set(pathways)),'context':context,'version':'D1_V2_D2_V1'}
 payload=seal({'event_id':'monster:v2:'+digest(identity),'event_type':'RAW_MONSTER_CANDIDATE','source':'binance_official','asset':entity,'monster_entity_id':entity,'symbols':sorted(set(symbols)),'venues':sorted(set(venues)),'observed_at':datetime.fromtimestamp(observed_ms/1000,timezone.utc).isoformat(),'first_activation':datetime.fromtimestamp(first_activation_ms/1000,timezone.utc).isoformat(),'active_pathways':identity['paths'],'mechanical_priority':priority,'priority_meaning':'ANOMALY_EVIDENCE_STRENGTH_ONLY','returns':{str(h)+'h':number(feature[i]) for h,i in [(1,0),(4,1),(6,2),(24,3)]},'volume_anomaly':number(feature[4]),'BTC_relative':{str(h)+'h':number(feature[i]) for h,i in [(1,7),(4,8),(24,9)]},'old_shell_state':bool(feature[12]==1),'new_listing_state':bool(math.isfinite(float(feature[13])) and 0<=feature[13]<168),'age_scope':'VERIFIED_INSTRUMENT_HISTORY_OR_AGE_LOWER_BOUND','derivatives_evidence':{'status':'NOT_USED_CHEAP_STRUCTURE_ONLY'},'liquidity_proxy_quote_1h':number(feature[14]),'historical_prior_spikes':None,'data_gaps':['DERIVATIVES_NOT_COLLECTED_FOR_ENTITY','PRIOR_SPIKES_NOT_COMPUTED'],'observation_context':context})
 if len(canonical(payload))>1500:raise ValueError('MONSTER_PAYLOAD_SIZE')
 return payload
