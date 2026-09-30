from dataclasses import replace
import pytest
from mission_agent.delivery.canary import Canary, recipient_hash, subject, body, verify_message
from mission_agent.models import Event
from mission_agent.clock import stamp

RUN='unit-canary'
EMAIL='self'+'@'+'example.invalid'
HASH=recipient_hash(EMAIL)


def setup_event(repo, ordinal='normal'):
    id='phase2b:gmail:'+RUN+':'+ordinal
    e=replace(Event.synthetic('TEST_ACTION_CANDIDATE','SYNTH',stamp(repo.clock.now()),0,{'fixture_decision':'ACTIONABLE_RISK'},ordinal),event_id=id)
    repo.ingest(e)
    repo.db.execute("UPDATE deliveries SET state='DELIVERY_PENDING' WHERE event_id=?",(id,))
    return id


def message(repo,id,provider_id='fixture-only-provider'):
    return {'id':provider_id,'label_ids':['SENT'],'internal_date':str(int(repo.clock.now().timestamp()*1000)),
            'payload':{'mime_type':'text/plain','headers':[{'name':'Subject','value':subject(id)},
                       {'name':'To','value':EMAIL},{'name':'From','value':EMAIL}],
                       'body':{'content':body(id,RUN,'normal',stamp(repo.clock.now()))}}}


def prepared(repo, ordinal='normal'):
    c=Canary(repo,RUN,HASH);id=setup_event(repo,ordinal)
    c.prepare(id,HASH,[],True,True,True)
    return c,id


def test_budget_persistent_across_restart(repo,clock):
    c,id=prepared(repo);c.invoke(id,True,True,True)
    path=repo.path;repo.close()
    from mission_agent.db.repository import Repository
    reopened=Repository(path,clock)
    assert Canary(reopened,RUN,HASH).budget()=={'authorized':3,'used':1,'remaining':2}
    reopened.close()


@pytest.mark.parametrize('classification',['SUCCESS','EXPLICIT_REJECT','TIMEOUT','AMBIGUOUS','UNKNOWN'])
def test_invocation_consumes_every_result(repo,classification):
    c,id=prepared(repo);assert c.budget()['used']==0
    c.invoke(id,True,True,True);c.result(id,classification)
    assert c.budget()['used']==1


@pytest.mark.parametrize('enabled,explicit,private,hash_value',[(False,True,True,HASH),(True,False,True,HASH),(True,True,False,HASH),(True,True,True,'0'*64)])
def test_pre_invocation_failure_uses_no_budget(repo,enabled,explicit,private,hash_value):
    c=Canary(repo,RUN,HASH);id=setup_event(repo)
    with pytest.raises(ValueError):c.prepare(id,hash_value,[],private,enabled,explicit)
    assert c.budget()['used']==0 and c.intent(id) is None


def test_exhausted_budget_blocks_new_send(repo):
    for i in range(3):
        c,id=prepared(repo,str(i));c.invoke(id,True,True,True)
    assert c.budget()['remaining']==0
    id=setup_event(repo,'fourth')
    with pytest.raises(ValueError,match='EXHAUSTED'):c.prepare(id,HASH,[],True,True,True)


def test_same_event_cannot_reuse_slot_and_uncertain_no_resend(repo):
    c,id=prepared(repo);c.invoke(id,True,True,True);c.result(id,'TIMEOUT')
    with pytest.raises(ValueError):c.prepare(id,HASH,[],True,True,True)
    with pytest.raises(ValueError):c.invoke(id,True,True,True)
    assert c.budget()['used']==1


def test_lookup_recovery_and_replay_delivered(repo):
    c,id=prepared(repo);c.invoke(id,True,True,True);c.result(id,'AMBIGUOUS')
    for _ in range(4):assert c.recover(id,[message(repo,id)])=='DELIVERED'
    assert c.budget()['used']==1
    with pytest.raises(ValueError):c.invoke(id,True,True,True)


def test_multiple_exact_matches_require_manual_review(repo):
    c,id=prepared(repo);c.invoke(id,True,True,True)
    assert c.recover(id,[message(repo,id,'one'),message(repo,id,'two')])=='FAILED_MANUAL_REVIEW'
    with pytest.raises(ValueError):c.invoke(id,True,True,True)


@pytest.mark.parametrize('mutation',['recipient','subject','event','label','timestamp','provider_id'])
def test_wrong_readback_rejected(repo,mutation):
    c,id=prepared(repo);c.invoke(id,True,True,True)
    m=message(repo,id)
    if mutation=='recipient':m['payload']['headers'][1]['value']='third-party'+'@'+'example.invalid'
    elif mutation=='subject':m['payload']['headers'][0]['value']='wrong'
    elif mutation=='event':m['payload']['body']['content']=body('wrong',RUN,'normal',stamp(repo.clock.now()))
    elif mutation=='label':m['label_ids']=[]
    elif mutation=='timestamp':m['internal_date']='0'
    else:c.result(id,'SUCCESS','another-id')
    with pytest.raises(ValueError):c.recover(id,[m])
    assert c.budget()['used']==1


def test_private_revalidation_blocks_invocation_without_consumption(repo):
    c,id=prepared(repo)
    with pytest.raises(ValueError):c.invoke(id,True,True,False)
    assert c.budget()['used']==0


def test_post_acceptance_persistence_failure_rolls_back_and_recovers(repo):
    c,id=prepared(repo);c.invoke(id,True,True,True)
    c.result(id,'SUCCESS','fixture-only-provider',True)
    assert c.intent(id)['provider_message_id'] is None
    assert c.intent(id)['provider_result_class']=='UNKNOWN'
    assert c.intent(id)['recovery_state']=='DELIVERY_UNCERTAIN'
    assert c.recover(id,[message(repo,id)])=='DELIVERED'
    receipt=c.receipt(id,'ACTIONABLE_RISK','test-batch','0'*64)
    from mission_agent.hashing import digest
    assert receipt['receipt_sha256']==digest({k:v for k,v in receipt.items() if k!='receipt_sha256'})
    assert EMAIL not in str(receipt) and 'fixture-only-provider' not in str(receipt)


def test_no_match_uncertain_no_retry(repo):
    c,id=prepared(repo);c.invoke(id,True,True,True)
    assert c.recover(id,[])=='DELIVERY_UNCERTAIN'
    with pytest.raises(ValueError):c.invoke(id,True,True,True)


def test_budget_grant_cannot_be_replaced_with_another_run(repo):
    Canary(repo,RUN,HASH)
    with pytest.raises(ValueError,match='GRANT'):Canary(repo,'another-run',HASH)


def test_delivered_replay_keeps_immutable_receipt_hash(repo,clock):
    c,id=prepared(repo);c.invoke(id,True,True,True);c.result(id,'SUCCESS')
    m=message(repo,id);c.recover(id,[m])
    first=c.receipt(id,'ACTIONABLE_RISK','test-batch','0'*64)
    clock.advance(1);c.recover(id,[m])
    assert c.receipt(id,'ACTIONABLE_RISK','test-batch','0'*64)==first


def test_identity_conflict_persists_global_send_stop(repo):
    c,id=prepared(repo);c.invoke(id,True,True,True)
    wrong=message(repo,id);wrong['payload']['headers'][1]['value']='wrong'+'@'+'example.invalid'
    with pytest.raises(ValueError):c.recover(id,[wrong])
    another=setup_event(repo,'another')
    with pytest.raises(ValueError,match='ABORTED'):c.prepare(another,HASH,[],True,True,True)
    assert c.budget()['used']==1


@pytest.mark.parametrize('enabled,explicit',[(False,False),(False,True),(True,False)])
def test_invoke_double_gate_blocks_even_with_existing_intent(repo,enabled,explicit):
    c,id=prepared(repo)
    with pytest.raises(ValueError,match='DOUBLE_GATE'):c.invoke(id,enabled,explicit,True)
    assert c.budget()['used']==0


def test_pending_validation_failure_before_intent_uses_no_slot(repo):
    c=Canary(repo,RUN,HASH)
    with pytest.raises(ValueError,match='PENDING'):c.prepare('phase2b:gmail:'+RUN+':missing',HASH,[],True,True,True)
    assert c.budget()['used']==0
    assert repo.db.execute('SELECT COUNT(*) FROM canary_intents').fetchone()[0]==0


def test_grant_recipient_identity_cannot_change_across_restart(repo):
    Canary(repo,RUN,HASH)
    with pytest.raises(ValueError,match='RECIPIENT_GRANT'):Canary(repo,RUN,'0'*64)
