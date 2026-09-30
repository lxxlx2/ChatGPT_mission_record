"""History-scoped active observations; never asserts first lifetime entry or PnL."""
from datetime import datetime,timezone
from ..hashing import seal,digest
from .rpc import WALLET,RPC

def build(evidence,delta,cluster=None,recent_count=0):
    if evidence['mechanical_classification']!='ACTIVE_SWAP_LIKE' or not delta['wallet_owned'] or not int(delta['delta']):return None
    if evidence['block_time'] is None:return None
    if cluster and cluster['mechanical_classification']=='HIGH_FREQUENCY_CLUSTER':return None
    if recent_count and not (int(delta['delta'])<0 and int(delta['post_amount'])==0):return None
    reason='FULL_EXIT_IN_OBSERVED_ACCOUNT' if int(delta['delta'])<0 and int(delta['post_amount'])==0 else 'FIRST_ACTIVE_TOKEN_IN_OBSERVED_SAMPLE'
    return seal({'event_id':'frank:v1:'+digest({'signature':evidence['signature'],'mint':delta['mint'],'reason':reason}),'event_type':'RAW_FRANK_CANDIDATE','wallet':WALLET,'signature':evidence['signature'],'block_time':evidence['block_time'],'observed_at':datetime.fromtimestamp(evidence['block_time'],timezone.utc).isoformat(),'asset':delta['mint'],'token_mint':delta['mint'],'token_symbol':None,'candidate_reason':reason,'active_evidence':{'signer':evidence['wallet_is_signer'],'fee_payer':evidence['wallet_is_fee_payer'],'authority_refs':[[a['scope'],a['instruction'],a['field']] for a in evidence['authority_accounts'] if a['matches_wallet'] and a['is_authority_evidence']][:2],'evidence_sha256':evidence['evidence_sha256']},'SOL_delta':evidence['SOL_delta_lamports'],'token_delta':delta['delta'],'token_decimals':delta['decimals'],'cluster_id':cluster['cluster_id'] if cluster else None,'historical_context':{'scope':'RECENT_500_ONLY','lifetime_entry_proven':False},'first_seen_token':recent_count==0,'recent_activity_count':recent_count,'source_rpc':RPC,'source':'solana_official_rpc'})
