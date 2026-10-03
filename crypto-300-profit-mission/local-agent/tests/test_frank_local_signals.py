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
