import copy,gzip,json
from pathlib import Path
import pytest
from mission_agent.signals.classifier import classify
from mission_agent.signals.store import Ledger
from mission_agent.signals.scanner import Scanner
from mission_agent.signals.delivery import drain
from mission_agent.signals.registry import load
from test_frank_fm import tx
from mission_agent.frank.rpc import WALLET
from mission_agent.frank.parser import WSOL
from mission_agent.signals.classifier import USDT

USDC='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
FIXTURES=Path(__file__).parent/'fixtures/frank_local'

def active(sig='buy',amount=100,quote=20):
    t=tx();t['meta']['preTokenBalances'][0]['uiTokenAmount']['amount']='0'
    t['meta']['postTokenBalances'][0]['uiTokenAmount']['amount']=str(abs(amount))
    for field in ['preTokenBalances','postTokenBalances']:t['meta'][field][1]['mint']=USDC
    t['meta']['preTokenBalances'][1]['uiTokenAmount']['amount']=str(quote)
    t['meta']['postTokenBalances'][1]['uiTokenAmount']['amount']='0'
    if amount<0:
        t['meta']['preTokenBalances'],t['meta']['postTokenBalances']=t['meta']['postTokenBalances'],t['meta']['preTokenBalances']
    return classify(sig,t,WALLET)

def put(l,e,**kwargs):return l.put('frank',e,e['signature'],'raw',**kwargs)


def add_owned_asset(t,mint,pre,post,decimals=6):
    index=len(t['transaction']['message']['accountKeys'])
    t['transaction']['message']['accountKeys'].append({'pubkey':'owned-'+str(index),'signer':False})
    t['meta']['preBalances'].append(2000000);t['meta']['postBalances'].append(2000000)
    def row(amount):
        return {'accountIndex':index,'mint':mint,'owner':WALLET,
                'uiTokenAmount':{'amount':str(amount),'decimals':decimals,'uiAmount':None}}
    t['meta']['preTokenBalances'].append(row(pre));t['meta']['postTokenBalances'].append(row(post))
    return t

def test_third_party_ata_create_is_not_trade():
    result=classify('ata',json.loads(gzip.decompress((FIXTURES/'ata.json.gz').read_bytes())),WALLET)
    assert result['classification']=='ATA_CREATE' and result['trade'] is None

def test_passive_sol_transfer_is_not_trade():
    result=classify('sol',json.loads(gzip.decompress((FIXTURES/'sol.json.gz').read_bytes())),WALLET)
    assert result['classification']=='PASSIVE_TRANSFER' and result['trade'] is None

def test_passive_token_transfer_is_not_buy():
    result=classify('token',json.loads(gzip.decompress((FIXTURES/'token.json.gz').read_bytes())),WALLET)
    assert result['classification']=='PASSIVE_TRANSFER' and result['trade'] is None

def test_active_swap_requires_frank_authority():
    t=tx(False);assert classify('no',t,WALLET)['trade'] is None

def test_active_buy_creates_position(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active());p=json.loads(l.db.execute('select body from positions').fetchone()[0]);assert p['state']=='OPEN' and p['buy_count']==1 and p['current_token_position']=='100'

def test_ledger_position_separates_unknown_quote_out_from_known_target_cost(tmp_path):
    l=Ledger(tmp_path/'db')
    e=active('unknown-cost',100,5000 * 10**6)
    e['trade']['amount_predicate']='UNDETERMINED'
    e['trade']['amount_predicate_reason']='ROUTED_RESIDUAL_ASSETS'
    e['trade']['route_amount_semantics']='GROSS_QUOTE_OUT_NOT_EXACT_FINAL_TARGET_COST'
    put(l,e)
    p=json.loads(l.db.execute('select body from positions').fetchone()[0])
    assert p['gross_quote_spent']=={}
    assert p['gross_quote_out_observed']=={USDC:'5000'}
    assert len(p['quote_cost_unknown_contributions'])==1
    assert p['quote_cost_unknown_contributions'][0]['signature']=='unknown-cost'


def test_second_active_buy_is_add(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active());put(l,active('add'));assert l.db.execute("select side from trades where signature='add'").fetchone()[0]=='ADD'

def test_partial_sell_does_not_exit(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active());put(l,active('sell',-30));assert l.db.execute("select side from trades where signature='sell'").fetchone()[0]=='SELL'

def test_full_exit_closes_episode(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active());put(l,active('exit',-100));assert json.loads(l.db.execute('select body from positions').fetchone()[0])['state']=='CLOSED'

def test_buy_after_exit_is_reentry(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active());put(l,active('exit',-100));put(l,active('again'));assert l.db.execute("select side from trades where signature='again'").fetchone()[0]=='REENTRY'

def test_multi_hop_swap_dedupes_to_one_trade(tmp_path):
    l=Ledger(tmp_path/'db');t=tx();t['transaction']['message']['instructions']*=3
    for field in ['preTokenBalances','postTokenBalances']:t['meta'][field][1]['mint']=USDC
    e=classify('multi',t,WALLET);put(l,e);put(l,e);assert l.db.execute('select count(*) from trades').fetchone()[0]==1



def test_usdt_is_preserved_as_non_usdc_quote_without_amount_gate():
    t=tx()
    for field in ['preTokenBalances','postTokenBalances']:t['meta'][field][1]['mint']=USDT
    e=classify('usdt',t,WALLET)
    assert e['classification']=='ACTIVE_TRADE'
    assert e['trade']['quote_asset']==USDT
    assert e['trade']['amount_predicate']=='UNDETERMINED'


def test_single_target_with_auxiliary_quote_refund_is_trade_but_amount_is_undetermined():
    t=tx()
    for field in ['preTokenBalances','postTokenBalances']:t['meta'][field][1]['mint']=USDC
    add_owned_asset(t,WSOL,0,250000000,9)
    e=classify('refund',t,WALLET)
    assert e['classification']=='ACTIVE_TRADE'
    assert e['trade']['quote_asset']==USDC
    assert e['trade']['amount_predicate']=='UNDETERMINED'
    assert len(e['trade']['quote_legs'])==2


def test_two_opposing_quote_payments_remain_ambiguous():
    t=tx()
    for field in ['preTokenBalances','postTokenBalances']:t['meta'][field][1]['mint']=USDC
    add_owned_asset(t,WSOL,250000000,0,9)
    e=classify('two-payments',t,WALLET)
    assert e['classification']=='UNKNOWN_NEEDS_REVIEW'
    assert e['classification_reason']=='AMBIGUOUS_USER_EXCHANGE_ASSETS'
    assert set(e['classification_details']['opposing_quote_assets'])=={USDC,WSOL}


def test_multiple_target_assets_remain_ambiguous_without_dust_guess():
    t=tx()
    for field in ['preTokenBalances','postTokenBalances']:t['meta'][field][1]['mint']=USDC
    add_owned_asset(t,'second-target',0,1,9)
    e=classify('multi-target',t,WALLET)
    assert e['classification']=='UNKNOWN_NEEDS_REVIEW'
    assert set(e['classification_details']['target_assets'])=={'mint1','second-target'}




def test_received_then_spent_created_residual_remains_ambiguous_without_route_binding():
    t=tx()
    for field in ['preTokenBalances','postTokenBalances']:
        t['meta'][field][1]['mint']=USDC
    route='route-intermediate'
    add_owned_asset(t,route,0,10,6)
    route_index=len(t['transaction']['message']['accountKeys'])-1
    route_account=t['transaction']['message']['accountKeys'][route_index]['pubkey']
    token='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
    t['meta']['innerInstructions']=[{'index':0,'instructions':[
        {'programId':token,'parsed':{'type':'initializeAccount3','info':{
            'account':route_account,'owner':WALLET,'mint':route}}},
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':'quote_ata','destination':'pool-a','mint':USDC,
            'tokenAmount':{'amount':'500000','decimals':6},'authority':WALLET}}},
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':'pool-a','destination':route_account,'mint':route,
            'tokenAmount':{'amount':'1000','decimals':6},'authority':'pool'}}},
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':route_account,'destination':'pool-b','mint':route,
            'tokenAmount':{'amount':'990','decimals':6},'authority':WALLET}}},
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':'pool-b','destination':'ata','mint':'mint1',
            'tokenAmount':{'amount':'1000000','decimals':6},'authority':'pool'}}},
    ]}]
    e=classify('routed-residual',t,WALLET)
    assert e['classification']=='UNKNOWN_NEEDS_REVIEW'
    assert e['classification_reason']=='AMBIGUOUS_USER_EXCHANGE_ASSETS'
    assert e['trade'] is None
    candidates=e['classification_details']['residual_flow_candidates']
    assert len(candidates)==1 and candidates[0]['mint']==route
    assert candidates[0]['gross_in_raw']=='1000'
    assert candidates[0]['gross_out_raw']=='990'
    assert candidates[0]['net_delta']=='10'
    assert candidates[0]['route_binding']=='UNPROVEN'
    assert 'downstream_target' not in candidates[0]
    flows=e['evidence']['wallet_token_transfer_flows']
    assert [(x['mint'],x['direction']) for x in flows]==[
        (USDC,'OUT'),(route,'IN'),(route,'OUT'),('mint1','IN')
    ]


def test_split_route_can_receive_final_target_before_residual_intermediate_finishes():
    t=tx()
    for field in ['preTokenBalances','postTokenBalances']:
        t['meta'][field][1]['mint']=USDC
    route='route-split-intermediate'
    add_owned_asset(t,route,0,10,6)
    route_index=len(t['transaction']['message']['accountKeys'])-1
    route_account=t['transaction']['message']['accountKeys'][route_index]['pubkey']
    token='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
    t['meta']['innerInstructions']=[{'index':0,'instructions':[
        {'programId':token,'parsed':{'type':'initializeAccount3','info':{
            'account':route_account,'owner':WALLET,'mint':route}}},
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':'quote_ata','destination':'pool-a','mint':USDC,
            'tokenAmount':{'amount':'500000','decimals':6},'authority':WALLET}}},
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':'pool-a','destination':route_account,'mint':route,
            'tokenAmount':{'amount':'1000','decimals':6},'authority':'pool'}}},
        # A parallel route delivers part of the final target before this
        # intermediate leg is fully recycled.
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':'parallel-pool','destination':'ata','mint':'mint1',
            'tokenAmount':{'amount':'400000','decimals':6},'authority':'pool'}}},
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':route_account,'destination':'pool-b','mint':route,
            'tokenAmount':{'amount':'990','decimals':6},'authority':WALLET}}},
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':'pool-b','destination':'ata','mint':'mint1',
            'tokenAmount':{'amount':'600000','decimals':6},'authority':'pool'}}},
    ]}]
    e=classify('split-routed-residual',t,WALLET)
    assert e['classification']=='UNKNOWN_NEEDS_REVIEW'
    assert e['trade'] is None
    routed=e['classification_details']['residual_flow_candidates']
    assert len(routed)==1
    assert routed[0]['mint']==route
    assert routed[0]['proof']=='CREATED_ZERO_PRE_RECEIVED_THEN_SPENT_CONSERVED_RESIDUAL_ONLY'


def test_existing_partially_sold_second_asset_is_not_assumed_route_intermediate():
    t=tx()
    for field in ['preTokenBalances','postTokenBalances']:
        t['meta'][field][1]['mint']=USDC
    route='existing-second-target'
    add_owned_asset(t,route,100,110,6)
    route_index=len(t['transaction']['message']['accountKeys'])-1
    route_account=t['transaction']['message']['accountKeys'][route_index]['pubkey']
    token='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
    t['meta']['innerInstructions']=[{'index':0,'instructions':[
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':'pool-a','destination':route_account,'mint':route,
            'tokenAmount':{'amount':'1000','decimals':6},'authority':'pool'}}},
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':route_account,'destination':'pool-b','mint':route,
            'tokenAmount':{'amount':'990','decimals':6},'authority':WALLET}}},
        {'programId':token,'parsed':{'type':'transferChecked','info':{
            'source':'pool-b','destination':'ata','mint':'mint1',
            'tokenAmount':{'amount':'1000000','decimals':6},'authority':'pool'}}},
    ]}]
    e=classify('existing-two-targets',t,WALLET)
    assert e['classification']=='UNKNOWN_NEEDS_REVIEW'
    assert e['classification_reason']=='AMBIGUOUS_USER_EXCHANGE_ASSETS'


STAGE={'signal_type':'FRANK_ACCUMULATION_SIGNAL','stage':'PRECONFIRM','reason_codes':['TEST_SUPPLIED_STAGE']}
MULTIPLE={'signal_type':'FRANK_MULTIPLE_SIGNAL','stage':'SUSPECTED_CONVICTION','reason_codes':['TEST_SUPPLIED_STAGE']}

def test_accumulation_signal_fires_once_per_supplied_stage(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active(),stages=[STAGE]);put(l,active('add'),stages=[STAGE]);assert l.db.execute('select count(*) from signals').fetchone()[0]==1

def test_same_stage_add_does_not_duplicate_alert(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active(),stages=[STAGE]);put(l,active('add'),stages=[STAGE]);assert l.inspect('add')[0]['body']['signal_ids']==[]

def test_stage_upgrade_creates_distinct_signal(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active(),stages=[STAGE]);put(l,active('add'),stages=[MULTIPLE]);assert l.db.execute('select count(*) from signals').fetchone()[0]==2

def test_multiple_signal_creates_email_outbox(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active(),stages=[MULTIPLE],dry_run=False);assert l.db.execute("select status from outbox where channel='gmail'").fetchone()[0]=='PENDING'

def test_email_failure_does_not_drop_signal(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active(),stages=[MULTIPLE],dry_run=False);drain(l,lambda s:{'signal_id':s['signal_id']});assert l.db.execute("select status from outbox where channel='gmail'").fetchone()[0]=='CREDENTIAL_BLOCKED';assert l.db.execute('select count(*) from signals').fetchone()[0]==1

def test_local_failure_is_pending_and_retries(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active(),stages=[STAGE],dry_run=False)
    def fail(s):raise RuntimeError('injected')
    drain(l,fail);assert l.db.execute('select status from outbox').fetchone()[0]=='RETRY_PENDING';drain(l,lambda s:{});assert l.db.execute('select status from outbox').fetchone()[0]=='COMMAND_ACCEPTED'

def test_restart_does_not_duplicate_signal(tmp_path):
    path=tmp_path/'db';l=Ledger(path);put(l,active(),stages=[STAGE]);l.db.close();l=Ledger(path);put(l,active(),stages=[STAGE]);assert l.db.execute('select count(*) from signals').fetchone()[0]==1

class RPC:
    def __init__(self,gap=False):self.gap=gap
    def signatures(self,before=None):return [] if self.gap else [{'signature':'new','slot':12},{'signature':'seed','slot':11}]
    def transaction(self,sig):return tx()

def test_cursor_does_not_advance_on_rpc_gap(tmp_path):
    l=Ledger(tmp_path/'db');l.checkpoint(WALLET,'seed',11);s=Scanner(l,{WALLET:'frank'},tmp_path/'raw',{WALLET:RPC(True)})
    with pytest.raises(ValueError,match='CURSOR_GAP'):s.cycle(WALLET)
    assert l.cursor(WALLET)['signature']=='seed'

def test_restart_catches_up_missed_signatures(tmp_path):
    l=Ledger(tmp_path/'db');l.checkpoint(WALLET,'seed',11);l.db.close();l=Ledger(tmp_path/'db');s=Scanner(l,{WALLET:'frank'},tmp_path/'raw',{WALLET:RPC()});s.cycle(WALLET);assert l.cursor(WALLET)['signature']=='new' and len(l.audit())==1

def test_unknown_is_durable_and_no_position(tmp_path):
    l=Ledger(tmp_path/'db');e=classify('broken',{'slot':12,'blockTime':123},WALLET);put(l,e);assert l.audit()[0]['alert_state']=='NO' and l.db.execute('select count(*) from positions').fetchone()[0]==0

def test_passive_does_not_change_trade_state(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active());before=l.db.execute('select body from positions').fetchone()[0];e=classify('sol',json.loads(gzip.decompress((FIXTURES/'sol.json.gz').read_bytes())),WALLET);put(l,e);assert l.db.execute('select body from positions').fetchone()[0]==before

def test_registry_only_frank_enabled(tmp_path):
    p=tmp_path/'registry';p.write_text(json.dumps({'persons':[{'person_id':'other','enabled':True,'wallets':[]}]}))
    with pytest.raises(ValueError,match='FRANK_ONLY'):load(p)

@pytest.mark.parametrize('side',['BUY','ADD','SELL'])
def test_real_confirmed_positive_chronology(side,tmp_path):
    manifest=json.loads((FIXTURES/'positive_manifest.json').read_text())[side];l=Ledger(tmp_path/'db')
    for row in manifest['chronology']:
        raw=json.loads(gzip.decompress((FIXTURES/row['file']).read_bytes()));e=classify(row['signature'],raw,WALLET)
        assert e['classification']=='ACTIVE_TRADE';put(l,e)
        assert l.db.execute('select side from trades where signature=?',(row['signature'],)).fetchone()[0]==row['side']
    assert l.db.execute('select side from trades where signature=?',(manifest['signature'],)).fetchone()[0]==side

def test_confirmed_sell_with_missing_prehistory_is_never_lost_or_guessed_exit(tmp_path):
    l=Ledger(tmp_path/'db');put(l,active('sell',-100));assert l.inspect('sell')[0]['body']['classification']=='ACTIVE_TRADE';assert l.db.execute('select side from trades').fetchone()[0]=='SELL_POSITION_UNRESOLVED';assert l.db.execute('select count(*) from positions').fetchone()[0]==0


def test_synthetic_sol_usdc_cannot_satisfy_frozen_amount_predicates():
    from mission_agent.signals.evaluator import known_usdc_event, amount_gate
    real={"quote_asset":USDC,"quote_quantity":"25000",
          "amount_predicate":"USDC_DIRECT_NUMERIC"}
    shadow={"quote_asset":USDC,"quote_quantity":"100000",
            "amount_predicate":"SOL_EVENT_TIME_USDC_VERIFIED",
            "amount_predicate_reason":"CAUSAL_PREVIOUS_CLOSED_SOLUSDC_REFERENCE"}
    assert known_usdc_event(real)
    assert not known_usdc_event(shadow)
    assert amount_gate([shadow],"25000")=="UNDETERMINED"
    assert amount_gate([real],"25000")=="PASS"


def test_install_script_blocks_loop_restart_by_default():
    source=Path(__file__).parents[1]/"scripts"/"install_mission_meme_launchd.sh"
    text=source.read_text()
    guard='CONFIRM_MISSION_LOOP_RESTART:-'
    assert guard in text
    assert text.index(guard)<text.index('mkdir -p "$APP_SUPPORT"')
    assert text.index(guard)<text.index('launchctl bootout')


def test_state_and_evaluator_share_frozen_known_usdc_logic(tmp_path):
    from mission_agent.signals.store import _known_usdc_trade
    from mission_agent.signals.evaluator import known_usdc_event
    candidates=[
        {"quote_asset":USDC,"amount_predicate":"USDC_DIRECT_NUMERIC"},
        {"quote_asset":USDC,"amount_predicate":"SOL_EVENT_TIME_USDC_VERIFIED"},
        {"quote_asset":USDC,"amount_predicate":"UNDETERMINED"},
        {"quote_asset":USDC},
        {"quote_asset":USDT,"amount_predicate":"USDC_DIRECT_NUMERIC"},
    ]
    for row in candidates:
        assert _known_usdc_trade(row)==known_usdc_event(row)
    assert not _known_usdc_trade(candidates[1])


def test_actual_classifier_simple_sol_route_is_not_marked_unverified():
    t=tx()
    for field in ("preTokenBalances","postTokenBalances"):
        t["meta"][field][1]["mint"]=WSOL
    e=classify("simple-sol",t,WALLET)
    assert e["classification"]=="ACTIVE_TRADE"
    assert e["trade"]["quote_asset"]=="SOL"
    assert e["trade"]["route_intermediate_assets"]==[]
    assert e["trade"]["route_intermediate_evidence_status"]=="NO_INTERMEDIATE_TRANSFER_OBSERVED"
    from mission_agent.market.sol_usd import normalize_classification
    reference={"status":"VERIFIED","source":"BINANCE_OFFICIAL_SPOT_SOLUSDC",
               "sol_usdc":"120","evidence_sha256":"fixture"}
    trade=normalize_classification(e,reference,for_model=False)["trade"]
    assert trade["quote_asset"]=="SOL"
    assert trade["quote_usdc_status"]=="SOL_EVENT_TIME_USDC_VERIFIED"
    assert trade["amount_predicate"]=="UNDETERMINED"


def test_install_guard_is_behavioral_and_has_no_side_effects(tmp_path):
    import os,subprocess
    root=Path(__file__).parents[1]
    installer=root/"scripts"/"install_mission_meme_launchd.sh"
    home=tmp_path/"isolated-home"
    home.mkdir()
    env={**os.environ,"HOME":str(home),"WORKTREE":str(tmp_path/"does-not-exist")}
    env.pop("CONFIRM_MISSION_LOOP_RESTART",None)
    completed=subprocess.run(["bash",str(installer)],env=env,
                             capture_output=True,text=True)
    assert completed.returncode!=0
    assert "MISSION_LOOP_RESTART_NOT_AUTHORIZED" in completed.stderr
    assert not (home/"Library").exists()


def test_direct_usdc_with_extra_intermediate_flow_has_undetermined_cost():
    t=tx()
    for field in ("preTokenBalances","postTokenBalances"):
        t["meta"][field][1]["mint"]=USDC
    # The parser can see an owned token intermediate even if it nets to zero.
    original_normalize=__import__("mission_agent.signals.classifier",fromlist=["normalize"]).normalize
    import mission_agent.signals.classifier as cl
    def with_extra(*args,**kwargs):
        result=original_normalize(*args,**kwargs)
        result["wallet_token_transfer_flows"]=[
            {"mint":"EXTRA_RESIDUAL","direction":"IN","raw_amount":"10"}]
        return result
    from unittest.mock import patch
    with patch.object(cl,"normalize",with_extra):
        classified=cl.classify("extra-route",t,WALLET)
    assert classified["classification"]=="ACTIVE_TRADE"
    assert classified["trade"]["amount_predicate"]=="UNDETERMINED"
    assert classified["trade"]["amount_predicate_reason"]=="ROUTED_RESIDUAL_ASSETS"
    assert classified["trade"]["route_intermediate_evidence_status"]=="UNVERIFIED"


def test_direct_usdc_with_missing_flow_evidence_is_not_known_cost():
    from unittest.mock import patch
    import mission_agent.signals.classifier as cl
    from mission_agent.signals.evaluator import known_usdc_event
    from mission_agent.signals.store import _known_usdc_trade
    value=tx()
    for field in ("preTokenBalances","postTokenBalances"):
        value["meta"][field][1]["mint"]=USDC
    original=cl.normalize
    def without_flows(*args,**kwargs):
        evidence=original(*args,**kwargs)
        evidence["wallet_token_transfer_flows"]=None
        return evidence
    with patch.object(cl,"normalize",without_flows):
        event=cl.classify("missing-flows",value,WALLET)
    assert event["classification"]=="ACTIVE_TRADE"
    trade=event["trade"]
    assert trade["route_intermediate_evidence_status"]=="UNVERIFIED"
    assert trade["amount_predicate"]=="UNDETERMINED"
    assert trade["amount_predicate_reason"]=="ROUTE_EVIDENCE_UNVERIFIED"
    assert not known_usdc_event(trade)
    assert not _known_usdc_trade(trade)
