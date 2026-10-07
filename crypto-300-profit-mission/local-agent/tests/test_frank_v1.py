import copy,json
from pathlib import Path
import pytest
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy,USDC
from mission_agent.signals.store import Ledger
from mission_agent.signals.evaluator import evaluate
from test_frank_local_signals import active,put,FIXTURES,WALLET

POLICY=Path(__file__).parents[1]/'config/frank_local_signal_v1.json'

def engine(tmp_path,dry=True):
    l=Ledger(tmp_path/'db');return l,Engine(l,load_policy(POLICY),dry_run=dry)

def buy(l,eng,sig,at,quote,amount=100,asset=USDC):
    e=active(sig,amount,quote);e['block_time']=at;e['slot']=at;e['trade']['quote_amount_raw']=str(int(quote)*10**6);e['trade']['quote_asset']=asset;e['trade']['quote_decimals']=6
    e['trade']['amount_predicate']='USDC_DIRECT_NUMERIC' if asset==USDC else 'UNDETERMINED'
    e['trade']['amount_predicate_reason']=None if asset==USDC else 'NON_USDC_QUOTE'
    put(l,e);return eng.drain()

def signals(l):return [json.loads(r[0]) for r in l.db.execute('select body from signals order by created_at,signal_type')]

def fixture_multiple(tmp_path,dry=True):
    l,eng=engine(tmp_path,dry);buy(l,eng,'first',100000,13000);buy(l,eng,'second',101200,13000);buy(l,eng,'third',102700,5000);return l,eng

def test_path_c_behavior_only_maps_to_accumulation(tmp_path):
    l,eng=engine(tmp_path);buy(l,eng,'first',100000,13000);buy(l,eng,'second',100600,13000);assert [s['signal_type'] for s in signals(l)]==['FRANK_ACCUMULATION_SIGNAL']

def test_single_large_buy_is_not_accumulation(tmp_path):
    l,eng=engine(tmp_path);buy(l,eng,'single',100000,50000);assert signals(l)==[]

@pytest.mark.parametrize('absent',['social','price','liquidity','gpt'])
def test_missing_enrichment_does_not_block_accumulation(tmp_path,absent):
    l,eng=engine(tmp_path);buy(l,eng,'one',100000,13000);buy(l,eng,'two',100600,13000);assert signals(l)[0]['signal_type']=='FRANK_ACCUMULATION_SIGNAL'

def test_suspected_conviction_behavior_core_maps_to_multiple(tmp_path):
    l,eng=fixture_multiple(tmp_path);multiple=signals(l)[-1];assert multiple['signal_type']=='FRANK_MULTIPLE_SIGNAL';assert 'PERSISTENCE_PATH_B_GE_3_BUYS_SPAN_GE_45M' in multiple['reason_codes']

@pytest.mark.parametrize('absent',['social','price_chase','liquidity','gpt'])
def test_missing_enrichment_does_not_block_multiple(tmp_path,absent):
    l,eng=fixture_multiple(tmp_path);assert len(signals(l))==2

def test_same_accumulation_stage_notified_once(tmp_path):
    l,eng=engine(tmp_path);buy(l,eng,'one',100000,13000);buy(l,eng,'two',100600,13000);buy(l,eng,'three',101200,13000);assert len(signals(l))==1

def test_multiple_stage_notified_once(tmp_path):
    l,eng=fixture_multiple(tmp_path);buy(l,eng,'four',103900,13000);assert len(signals(l))==2;assert eng.summary()['same_stage_duplicate_suppressed']>0

def test_multiple_generates_local_and_email_outbox(tmp_path):
    l,eng=fixture_multiple(tmp_path,False);sid=signals(l)[-1]['signal_id'];assert {r[0] for r in l.db.execute('select channel from outbox where signal_id=?',(sid,))}=={'local','gmail'}

def test_accumulation_generates_local_only(tmp_path):
    l,eng=fixture_multiple(tmp_path);sid=signals(l)[0]['signal_id'];assert [r[0] for r in l.db.execute('select channel from outbox where signal_id=?',(sid,))]==['local']

def test_historical_replay_never_delivers(tmp_path):
    from mission_agent.signals.delivery import drain
    l,eng=fixture_multiple(tmp_path);assert all(r[0]=='DRY_RUN_AUDIT' for r in l.db.execute('select status from outbox'));drain(l,lambda _:pytest.fail('historical delivery attempted'))

def test_amount_non_usdc_undetermined_preserves_active_trade(tmp_path):
    l,eng=engine(tmp_path);buy(l,eng,'first',100000,13000,asset='SOL');buy(l,eng,'second',101200,13000,asset='SOL');buy(l,eng,'third',102700,13000,asset='SOL')
    assert len(l.db.execute('select * from trades').fetchall())==3 and signals(l)==[]
    e=json.loads(l.db.execute('select body from v1_evaluations order by at desc limit 1').fetchone()[0]);assert e['predicates']['cumulative_amount']=='UNDETERMINED' and e['predicates']['persistence']=='PASS'



def test_composite_usdc_quote_never_satisfies_frozen_amount_gate(tmp_path):
    l,eng=engine(tmp_path)
    for sig,at in [('first',100000),('second',100600)]:
        e=active(sig,100,13000);e['block_time']=at;e['slot']=at
        e['trade']['quote_amount_raw']='13000000000';e['trade']['quote_decimals']=6
        e['trade']['quote_asset']=USDC;e['trade']['amount_predicate']='UNDETERMINED'
        e['trade']['amount_predicate_reason']='COMPOSITE_QUOTE_LEGS'
        put(l,e);eng.drain()
    assert signals(l)==[]
    evaluation=json.loads(l.db.execute('select body from v1_evaluations order by at desc limit 1').fetchone()[0])
    assert evaluation['predicates']['accumulation_amount']=='UNDETERMINED'


def test_hft_behavior_blocks_multiple_but_not_selected_accumulation(tmp_path):
    l,eng=engine(tmp_path);buy(l,eng,'first',100000,13000);buy(l,eng,'second',100010,13000);buy(l,eng,'third',100020,13000);buy(l,eng,'fourth',102700,13000)
    assert len(signals(l))==1;state=json.loads(l.db.execute('select body from v1_states').fetchone()[0]);assert evaluate(state,102700,eng.policy)['predicates']['hft']=='FAIL'

def test_distribution_not_hidden_by_old_accumulation(tmp_path):
    l,eng=engine(tmp_path);buy(l,eng,'first',100000,13000);buy(l,eng,'second',101200,13000);buy(l,eng,'sell',102000,5000,amount=-150);eng.tick(104000);assert len(signals(l))==1

def test_restart_signal_identity_and_outbox_do_not_duplicate(tmp_path):
    l,eng=fixture_multiple(tmp_path);ids=[s['signal_id'] for s in signals(l)];l.db.close();l=Ledger(tmp_path/'db');eng=Engine(l,load_policy(POLICY));eng.drain();assert [s['signal_id'] for s in signals(l)]==ids and l.db.execute('select count(*) from outbox').fetchone()[0]==3

def test_failure_rolls_back_model_ack_and_signal(tmp_path,monkeypatch):
    l,eng=engine(tmp_path);buy(l,eng,'first',100000,13000);e=active('second');e['block_time']=100600;e['trade']['quote_amount_raw']='13000000000';e['trade']['quote_decimals']=6;put(l,e)
    original=eng._emit
    def fail(*a):original(*a);raise RuntimeError('crash after signal insert')
    monkeypatch.setattr(eng,'_emit',fail)
    with pytest.raises(RuntimeError):eng.drain()
    assert len(signals(l))==0 and l.db.execute("select count(*) from v1_seen where signature='second'").fetchone()[0]==0
    monkeypatch.setattr(eng,'_emit',original);eng.drain();assert len(signals(l))==1

def test_frozen_policy_drift_is_rejected(tmp_path):
    p=tmp_path/'policy';p.write_text(POLICY.read_text()+' ')
    with pytest.raises(ValueError,match='FROZEN_POLICY_DRIFT'):load_policy(p)

def test_prior_hourly_watch_path_a_is_local_and_deterministic(tmp_path):
    l,eng=engine(tmp_path);buy(l,eng,'first',3600,13000);buy(l,eng,'second',4200,13000);eng.tick(5340);eng.tick(8940);assert signals(l)[-1]['signal_type']=='FRANK_MULTIPLE_SIGNAL';assert 'PERSISTENCE_PATH_A_PRIOR_HOURLY_WATCH' in signals(l)[-1]['reason_codes']

def replay_sevenvert(tmp_path):
    import gzip,hashlib
    from mission_agent.signals.classifier import classify
    l,eng=engine(tmp_path);root=FIXTURES/'sevenvert';manifest=json.loads((root/'manifest.json').read_text());steps=[]
    for row in manifest:
        tx=json.loads(gzip.decompress((root/(row['signature']+'.json.gz')).read_bytes()));e=classify(row['signature'],tx,WALLET);assert e['classification']=='ACTIVE_TRADE';l.put('frank',e,hashlib.sha256(json.dumps(tx,sort_keys=True).encode()).hexdigest(),'fixture',dry_run=True);eng.drain()
        result=json.loads(l.db.execute('select body from v1_evaluations where signature=? and json_extract(body,\'$.kind\')=\'ACTIVE_TRADE\' order by at desc limit 1',(row['signature'],)).fetchone()[0]);steps.append({'signature':row['signature'],'result':result,'signals':signals(l)})
    return l,eng,steps

def test_sevenvert_replay_is_deterministic(tmp_path):
    l1,e1,a=replay_sevenvert(tmp_path/'one');l2,e2,b=replay_sevenvert(tmp_path/'two');assert a==b
    assert len(signals(l1))==1 and signals(l1)[0]['signal_type']=='FRANK_ACCUMULATION_SIGNAL'
    assert signals(l1)[0]['triggering_signature']==a[1]['signature'];assert a[-1]['result']['predicates']['persistence']=='FAIL' and a[-1]['result']['predicates']['hft']=='FAIL'

def test_multiple_email_is_standalone_content_hash_bound_and_usdc_not_usd_claim(tmp_path):
    from mission_agent.signals.email import content
    l,eng=fixture_multiple(tmp_path);s=signals(l)[-1];mail=content(s)
    assert mail['subject'].startswith('[Frank 多倍信号]') and s['mint'] in mail['body'];assert 'USD estimate: unavailable' in mail['body']
    stored=l.db.execute('select content_hash from email_content where signal_id=?',(s['signal_id'],)).fetchone()[0];assert stored==mail['content_hash']

def test_model_clock_can_advance_without_rejecting_next_durable_transaction(tmp_path):
    l,eng=engine(tmp_path);buy(l,eng,'first',100000,13000);eng.tick(100100);buy(l,eng,'second',100050,13000);assert len(signals(l))==1

def test_historical_delivery_adapter_refuses_non_test_dispatch(tmp_path):
    from mission_agent.signals.delivery import LocalNotifier
    l,eng=fixture_multiple(tmp_path)
    with pytest.raises(ValueError,match='HISTORICAL_DELIVERY_FORBIDDEN'):LocalNotifier()(signals(l)[0])

def test_receipt_recovery_does_not_dispatch_again(tmp_path):
    from mission_agent.signals.delivery import LocalNotifier,drain
    l,eng=fixture_multiple(tmp_path,False);root=tmp_path/'receipts';calls=[]
    class Result:returncode=0;stdout='REQUEST_ACCEPTED'
    n=LocalNotifier(run=lambda *args,**kwargs:(calls.append(args) or Result()),receipt_root=root)
    drain(l,n);assert len(calls)==2
    l.db.execute("UPDATE outbox SET status='IN_FLIGHT' WHERE channel='local'");drain(l,n);assert len(calls)==2

def test_sqlite_migration_preserves_cursor_signals_and_restarts(tmp_path):
    l,eng=fixture_multiple(tmp_path);from mission_agent.signals.gmail import GmailOutbox;GmailOutbox(l).sync();l.checkpoint(WALLET,'seed',1);before=l.cursor(WALLET);ids=[s['signal_id'] for s in signals(l)];l.db.execute('DROP TABLE email_content');l.db.close();l=Ledger(tmp_path/'db');eng=Engine(l,load_policy(POLICY));assert l.cursor(WALLET)==before and [s['signal_id'] for s in signals(l)]==ids and l.db.execute('select count(*) from email_content').fetchone()[0]==1

def test_preimported_chain_transaction_advances_cursor_without_duplicate_position(tmp_path):
    l,eng=engine(tmp_path);e=active('cached');e['slot']=12;put(l,e);l.checkpoint(WALLET,'seed',11);before=l.db.execute('select body from positions').fetchone()[0]
    assert l.put('frank',e,e['signature'],'raw',advance=True) is False
    assert l.cursor(WALLET)['signature']=='cached' and l.db.execute('select body from positions').fetchone()[0]==before

def test_gpt_and_network_unavailable_do_not_enter_model_critical_path(tmp_path,monkeypatch):
    import urllib.request
    def unavailable(*args,**kwargs):raise RuntimeError('all external GPT/network services unavailable')
    monkeypatch.setattr(urllib.request,'urlopen',unavailable);l,eng=fixture_multiple(tmp_path);assert [s['signal_type'] for s in signals(l)]==['FRANK_ACCUMULATION_SIGNAL','FRANK_MULTIPLE_SIGNAL']

def test_non_behavior_veto_fields_cannot_change_model_output(tmp_path):
    l,eng=fixture_multiple(tmp_path);state=json.loads(l.db.execute('select body from v1_states').fetchone()[0]);before=evaluate(state,102700,eng.policy)
    state.update(social=None,price_chase_blocked=True,liquidity_pass=False,gpt_decision='NO_SEND');assert evaluate(state,102700,eng.policy)==before

def test_unresolved_excess_sell_invalidates_known_inventory_without_false_exit(tmp_path):
    l,eng=engine(tmp_path);buy(l,eng,'buy',100000,13000,amount=100);buy(l,eng,'excess',100600,5000,amount=-150)
    position=json.loads(l.db.execute('select body from positions').fetchone()[0]);assert position['state']=='INVENTORY_UNDETERMINED' and position['current_token_position'] is None
    buy(l,eng,'new_known_sequence',101200,13000);position=json.loads(l.db.execute('select body from positions').fetchone()[0]);assert position['state']=='OPEN' and position['current_token_position']=='100'

def test_raw_rpc_failure_is_seen_durable_inspectable_and_cursor_stalls(tmp_path):
    from mission_agent.signals.scanner import Scanner
    from mission_agent.signals.__main__ import inspect,audit
    class RPC:
        def signatures(self,**kwargs):return [{'signature':'unavailable','slot':12,'blockTime':100000},{'signature':'seed','slot':11}]
        def transaction(self,sig):return None
    l,eng=engine(tmp_path);l.checkpoint(WALLET,'seed',11);scanner=Scanner(l,{WALLET:'frank'},tmp_path/'raw',{WALLET:RPC()})
    with pytest.raises(ValueError,match='RAW_UNAVAILABLE'):scanner.cycle(WALLET)
    assert l.cursor(WALLET)['signature']=='seed';assert inspect(l.db,'unavailable')[0]['classification_reason']=='RAW_PENDING_CURSOR_NOT_ADVANCED';assert audit(l.db,50)[0][2]=='unavailable'
