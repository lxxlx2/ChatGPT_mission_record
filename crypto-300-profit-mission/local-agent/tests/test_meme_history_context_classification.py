import copy
import pytest
from mission_agent.signals.classifier import classify

try:
    from mission_agent.meme.history_classification import resolve_history_classification
except ModuleNotFoundError as exc:
    if exc.name != 'mission_agent.meme.history_classification': raise
    # Also run these counterexamples against the fixed pre-change checkout.
    resolve_history_classification = lambda result, *args: result

TOKEN='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
DEX='JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4'
OWNER='owner';TARGET='mint';OTHER='other'

def balance(index,owner,mint,raw):
    return {'accountIndex':index,'owner':owner,'mint':mint,'uiTokenAmount':{'amount':str(raw),'decimals':6}}

def passive():
    keys=['sender','source','destination',TOKEN,TARGET]
    before=[balance(1,'sender',TARGET,10),balance(2,OWNER,TARGET,20)]
    after=[balance(1,'sender',TARGET,5),balance(2,OWNER,TARGET,25)]
    ix={'programId':TOKEN,'parsed':{'type':'transferChecked','info':{'source':'source','destination':'destination','authority':'sender','mint':TARGET,'tokenAmount':{'amount':'5','decimals':6}}}}
    return {'slot':10,'blockTime':10,'version':0,'transaction':{'signatures':['s'],'message':{'accountKeys':[{'pubkey':k,'signer':k=='sender'} for k in keys],'instructions':[ix]}},'meta':{'err':None,'fee':1,'preBalances':[10]*len(keys),'postBalances':[10]*len(keys),'preTokenBalances':before,'postTokenBalances':after,'innerInstructions':[]}}

def pair():
    keys=[OWNER,'owned-a','owned-b','pool-a','pool-b',TOKEN,DEX]
    before=[balance(1,OWNER,TARGET,10),balance(2,OWNER,OTHER,20),balance(3,'pool',TARGET,100),balance(4,'pool',OTHER,100)]
    after=[balance(1,OWNER,TARGET,15),balance(2,OWNER,OTHER,13),balance(3,'pool',TARGET,95),balance(4,'pool',OTHER,107)]
    def transfer(src,dst,mint,n):return {'programId':TOKEN,'parsed':{'type':'transferChecked','info':{'source':src,'destination':dst,'authority':OWNER,'mint':mint,'tokenAmount':{'amount':str(n),'decimals':6}}}}
    return {'slot':10,'blockTime':10,'version':0,'transaction':{'signatures':['s'],'message':{'accountKeys':[{'pubkey':k,'signer':k==OWNER} for k in keys],'instructions':[{'programId':DEX,'parsed':{'type':'swap','info':{}}}]}},'meta':{'err':None,'fee':1,'preBalances':[10]*len(keys),'postBalances':[10]*len(keys),'preTokenBalances':before,'postTokenBalances':after,'innerInstructions':[{'index':0,'instructions':[transfer('pool-a','owned-a',TARGET,5),transfer('owned-b','pool-b',OTHER,7)]}]}}

def resolve(tx):return resolve_history_classification(classify('s',tx,OWNER),'s',tx,OWNER,TARGET)

def test_owner_absent_but_conserved_account_receipt_is_passive_not_a_buy():
    tx=passive();original=copy.deepcopy(tx);strict=classify('s',tx,OWNER)
    assert strict['classification_details']['chain_metadata_reason']=='WALLET_NOT_REFERENCED'
    result=resolve(tx)
    assert result['classification']=='PASSIVE_TRANSFER' and result['trade'] is None
    assert result['frank_is_signer'] is result['frank_is_authority'] is False
    assert result['classification_details']['native_balance']=='UNAVAILABLE'
    assert tx==original and classify('s',tx,OWNER)==strict

@pytest.mark.parametrize('change',['failed','wrong_owner','wrong_mint','amount','decimals','fake_program','authority','missing_vectors','owner_change','invalid_index'])
def test_absent_owner_shortcuts_cannot_hide_unproved_or_conflicting_activity(change):
    tx=passive();info=tx['transaction']['message']['instructions'][0]['parsed']['info']
    if change=='failed':tx['meta']['err']={'InstructionError':[0,'failed']}
    elif change=='wrong_owner':
        for row in tx['meta']['preTokenBalances']+tx['meta']['postTokenBalances']:row['owner']='stranger'
    elif change=='wrong_mint':info['mint']='different'
    elif change=='amount':info['tokenAmount']['amount']='6'
    elif change=='decimals':info['tokenAmount']['decimals']=9
    elif change=='fake_program':tx['transaction']['message']['instructions'][0]['programId']='untrusted'
    elif change=='authority':info['authority']=OWNER
    elif change=='missing_vectors':tx['meta']['preBalances']=[]
    elif change=='owner_change':tx['meta']['postTokenBalances'][1]['owner']='stranger'
    elif change=='invalid_index':tx['meta']['postTokenBalances'][1]['accountIndex']=True
    assert resolve(tx)['classification']=='UNKNOWN_NEEDS_REVIEW'

def test_selected_mint_two_token_exchange_keeps_unvalued_counterasset():
    tx=pair();strict=classify('s',tx,OWNER);assert strict['classification']=='UNKNOWN_NEEDS_REVIEW'
    result=resolve(tx);assert result['classification']=='ACTIVE_TRADE'
    assert result['trade']['mint']==TARGET and result['trade']['direction']=='BUY'
    assert result['trade']['quote_asset']==OTHER and result['trade']['amount_predicate']=='UNDETERMINED'
    assert classify('s',tx,OWNER)==strict

def test_external_counterasset_outflow_is_not_discarded_or_called_exact_cost():
    tx=pair();tx['transaction']['message']['instructions'].append({'programId':TOKEN,'parsed':{'type':'transferChecked','info':{
        'source':'owned-b','destination':'pool-b','authority':OWNER,'mint':OTHER,'tokenAmount':{'amount':'1','decimals':6}}}})
    tx['meta']['postTokenBalances'][1]['uiTokenAmount']['amount']='12'
    tx['meta']['postTokenBalances'][3]['uiTokenAmount']['amount']='108'
    result=resolve(tx);assert result['classification']=='ACTIVE_TRADE'
    assert result['trade']['quote_amount_raw']=='8' and result['trade']['amount_predicate']=='UNDETERMINED'

def test_unrelated_external_incoming_cannot_be_misrepresented_as_market_buy():
    tx=pair();tx['transaction']['message']['instructions'].append({'programId':TOKEN,'parsed':{'type':'transferChecked','info':{
        'source':'pool-a','destination':'owned-a','authority':OWNER,'mint':TARGET,'tokenAmount':{'amount':'1','decimals':6}}}})
    tx['meta']['postTokenBalances'][0]['uiTokenAmount']['amount']='16'
    tx['meta']['postTokenBalances'][2]['uiTokenAmount']['amount']='94'
    assert resolve(tx)['classification']=='UNKNOWN_NEEDS_REVIEW'

@pytest.mark.parametrize('change',['bad_flow','two_market_groups','both_positive','wrong_target'])
def test_two_asset_scope_does_not_promote_unbound_or_ambiguous_exchange(change):
    tx=pair()
    if change=='bad_flow':tx['meta']['innerInstructions'][0]['instructions'][0]['parsed']['info']['tokenAmount']['amount']='6'
    elif change=='two_market_groups':tx['transaction']['message']['instructions'].append({'programId':DEX,'parsed':{'type':'swap','info':{}}})
    elif change=='both_positive':tx['meta']['postTokenBalances'][1]['uiTokenAmount']['amount']='27'
    if change=='wrong_target':result=resolve_history_classification(classify('s',tx,OWNER),'s',tx,OWNER,'absent')
    else:result=resolve(tx)
    assert result['classification']=='UNKNOWN_NEEDS_REVIEW'
