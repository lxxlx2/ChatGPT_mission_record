"""Historical association/closure needs transaction-bound source evidence."""
import copy
import pytest
from mission_agent.meme.historical_accounts import observe_token_accounts,HistoricalAccountEvidenceError
from test_meme_holder_ranks import key,MINT,P

OWNER=key(301);OTHER=key(302);ACCOUNT=key(600);SIG='fixture-transaction'


def tx(*,post=True,close=False):
    row={'accountIndex':1,'mint':MINT,'owner':OWNER,'programId':P,
         'uiTokenAmount':{'amount':'10','decimals':0}}
    value={'slot':100,'blockTime':1000,'transaction':{'signatures':[SIG],
        'message':{'accountKeys':[{'pubkey':OWNER,'source':'transaction'},{'pubkey':ACCOUNT,'source':'lookupTable'},{'pubkey':P,'source':'transaction'}],
                   'instructions':[]}},
        'meta':{'err':None,'preTokenBalances':[row],'postTokenBalances':[copy.deepcopy(row)] if post else [],
                'preBalances':[100,2039280,1],'postBalances':[100,2039280 if post else 0,1],'innerInstructions':[]}}
    if close:value['transaction']['message']['instructions']=[{'programId':P,'parsed':{'type':'closeAccount','info':{'account':ACCOUNT,'owner':OTHER,'destination':OTHER}}}]
    return value


def observe(value):return observe_token_accounts(value,SIG,MINT,OWNER,0)


def test_pre_and_post_balances_preserve_transaction_owner_and_source_hash():
    rows=observe(tx())
    assert [r['balance_phase'] for r in rows]==['pre','post']
    assert all(r['owner']==OWNER and r['account']==ACCOUNT and r['raw']=='10' for r in rows)
    assert all(r['slot']==100 and r['signature']==SIG and len(r['response_sha256'])==64 for r in rows)
    assert all(r['closure_at_transaction_end']=='NOT_PROVEN' for r in rows)


def test_absent_post_balance_alone_does_not_prove_closure():
    assert observe(tx(post=False))[0]['closure_at_transaction_end']=='NOT_PROVEN'


def test_successful_token_close_with_zero_end_lamports_proves_only_that_transaction_end():
    row=observe(tx(post=False,close=True))[0]
    assert row['closure_at_transaction_end']=='CONFIRMED_CLOSED_AT_TRANSACTION_END'
    assert row['balance_phase']=='pre'
    assert 'current_owner' not in row and 'currently_closed' not in row


@pytest.mark.parametrize('mutation',['wrong_program','mismatched_token_program','nonzero_end','missing_lamports','post_recreated','wrong_account'])
def test_close_instruction_without_matching_end_state_is_not_confirmed(mutation):
    value=tx(post=False,close=True)
    ix=value['transaction']['message']['instructions'][0]
    if mutation=='wrong_program':ix['programId']=OWNER
    elif mutation=='mismatched_token_program':ix['programId']='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
    elif mutation=='nonzero_end':value['meta']['postBalances'][1]=1
    elif mutation=='missing_lamports':value['meta'].pop('postBalances')
    elif mutation=='post_recreated':value['meta']['postTokenBalances']=copy.deepcopy(value['meta']['preTokenBalances'])
    elif mutation=='wrong_account':ix['parsed']['info']['account']=OWNER
    assert observe(value)[0]['closure_at_transaction_end']=='NOT_PROVEN'


def test_owner_change_is_not_merged_into_lifetime_ownership():
    value=tx();value['meta']['postTokenBalances'][0]['owner']=OTHER
    assert [r['balance_phase'] for r in observe(value)]==['pre']
    rows=observe_token_accounts(value,SIG,MINT,OTHER,0)
    assert [r['balance_phase'] for r in rows]==['post']


@pytest.mark.parametrize('mutation',['failed','missing_err','wrong_signature','missing_slot','bool_index','negative_index','out_of_range','wrong_decimals','invalid_amount','missing_owner','duplicate_row','ambiguous_lookup'])
def test_invalid_or_ambiguous_context_never_yields_verified_association(mutation):
    value=tx();row=value['meta']['preTokenBalances'][0]
    if mutation=='failed':value['meta']['err']={'InstructionError':[0,'Custom']}
    elif mutation=='missing_err':value['meta'].pop('err')
    elif mutation=='wrong_signature':value['transaction']['signatures']=['another']
    elif mutation=='missing_slot':value.pop('slot')
    elif mutation=='bool_index':row['accountIndex']=True
    elif mutation=='negative_index':row['accountIndex']=-1
    elif mutation=='out_of_range':row['accountIndex']=99
    elif mutation=='wrong_decimals':row['uiTokenAmount']['decimals']=9
    elif mutation=='invalid_amount':row['uiTokenAmount']['amount']='-1'
    elif mutation=='missing_owner':row.pop('owner')
    elif mutation=='duplicate_row':value['meta']['preTokenBalances'].append(copy.deepcopy(row))
    elif mutation=='ambiguous_lookup':
        value['transaction']['message']['accountKeys']=[OWNER,ACCOUNT,P]
        value['transaction']['message']['addressTableLookups']=[{'accountKey':OTHER}]
    with pytest.raises(HistoricalAccountEvidenceError):observe(value)


def test_missing_block_time_keeps_slot_evidence_without_inventing_time():
    value=tx();value['blockTime']=None
    assert observe(value)[0]['block_time'] is None


def test_other_mint_and_other_owner_are_not_adopted():
    value=tx();value['meta']['preTokenBalances'][0]['mint']=OTHER
    value['meta']['postTokenBalances'][0]['owner']=OTHER
    assert observe(value)==[]


def test_inner_close_instruction_is_bound_to_same_successful_transaction():
    value=tx(post=False,close=True);ix=value['transaction']['message']['instructions'].pop()
    value['meta']['innerInstructions']=[{'index':0,'instructions':[ix]}]
    assert observe(value)[0]['closure_at_transaction_end']=='CONFIRMED_CLOSED_AT_TRANSACTION_END'


def test_signature_window_slot_conflict_is_not_silently_reconciled():
    with pytest.raises(HistoricalAccountEvidenceError,match='TRANSACTION_SLOT_CONFLICT'):
        observe_token_accounts(tx(),SIG,MINT,OWNER,0,expected_slot=99)
