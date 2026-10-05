import copy,json,threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from mission_agent.hashing import seal,canonical,loads,verify
from mission_agent.db.repository import Repository
from mission_agent.frank.store import FrankStore
from mission_agent.frank.parser import normalize
from mission_agent.frank.rpc import WALLET
from mission_agent.meme.registry import Registry
from mission_agent.meme.schema import fact,candidates,run_bundle,validate_run,iso,epoch
from mission_agent.meme.state import migrate,SignalStore
from mission_agent.meme.mail import render,decision,MailOutbox
from mission_agent.meme.transport import MemeTransport
from mission_agent.transport.github import Conflict,RemoteError
from test_frank_fm import tx
from test_phase2a import MemoryAPI

BASE=1791003600
NOW=iso(BASE+20)
POLICY=json.loads((Path(__file__).parents[1]/'config/meme_shadow_policy.json').read_text())

def registry(pattern_a='SIGNAL_ENABLED'):
 return Registry({'schema_version':1,'namespace':'TEST','persons':[{'person_id':'frank','display_name':'Frank','person_pattern_state':'SIGNAL_ENABLED','wallets':[{'chain':'solana','address':WALLET,'verified':True},{'chain':'solana','address':'frank-wallet2','verified':True}]},{'person_id':'persona','display_name':'PersonA','person_pattern_state':pattern_a,'wallets':[{'chain':'solana','address':'personA-wallet','verified':True}]}]},namespace='TEST')

def buy(reg,mint='TOKEN_Z',wallet=WALLET,sig='new',at=BASE):
 t=tx();t['blockTime']=at;t['transaction']['message']['accountKeys'][0]['pubkey']=wallet
 t['transaction']['message']['instructions'][0]['parsed']['info']['authority']=wallet
 for k in ['preTokenBalances','postTokenBalances']:
  for b in t['meta'][k]:b['owner']=wallet
  t['meta'][k][0]['mint']=mint
 e=normalize(sig,t,wallet)
 return fact(e,{'detected_at':str(at+1),'normalized_at':str(at+2)},iso(at+3),reg,mint)

def run(reg,facts):return run_bundle(candidates(facts,reg,POLICY),'TEST')
def inputs(bundle,now=NOW):
 ds=[decision(c,bundle,send=True,now=now,text='current') for c in bundle['candidates']]
 return ds,{'run_id':bundle['run_id'],'status':'SUCCESS','by_signal':{}}

def state(tmp_path,reg=None):
 r=Repository(tmp_path/'meme.sqlite');FrankStore(r);reg=reg or registry();migrate(r.db,iso(BASE),reg,legacy_wallet=WALLET);return r,reg

# Permanent RUN_A/RUN_B regression; never remove or weaken.
def test_run_a_run_b_stale_content_regression(tmp_path):
 reg=registry();a=run(reg,[buy(reg,'TOKEN_X',sig='ax'),buy(reg,'TOKEN_X',wallet='personA-wallet',sig='ap'),buy(reg,'TOKEN_Y',sig='ay')]);da,ea=inputs(a);old=render(a,da,ea,NOW)
 assert 'Frank + PersonA' in old['html']
 for name in ['old.html','previous.json','cache.txt']:(tmp_path/name).write_text(old['html'])
 b=run(reg,[buy(reg,'TOKEN_Z',wallet='personA-wallet',sig='bz')]);db,eb=inputs(b);new=render(b,db,eb,NOW)
 for stale in ['TOKEN_X','TOKEN_Y','Frank + PersonA','TOKEN_CONSENSUS']:assert stale not in new['html']
 assert new['html'].count('TOKEN_Z')==1 and new['html'].count('<article ')==1

def test_previous_signal_current_none_no_mail():
 reg=registry();b=run(reg,[]);ds,en=inputs(b);assert render(b,ds,en,NOW) is None

def test_same_person_two_wallets_count_one():
 reg=registry();cs=candidates([buy(reg,sig='a'),buy(reg,wallet='frank-wallet2',sig='b')],reg,POLICY)
 assert all(c['unique_person_count']==1 for c in cs);assert not any(c['signal_family_candidate']=='TOKEN_CONSENSUS' for c in cs)

def test_two_people_and_observe_only_consensus():
 reg=registry('OBSERVE_ONLY');cs=candidates([buy(reg,sig='a'),buy(reg,wallet='personA-wallet',sig='b')],reg,POLICY)
 cons=[c for c in cs if c['signal_family_candidate']=='TOKEN_CONSENSUS'];assert len(cons)==1 and cons[0]['unique_person_count']==2
 assert not any(c['signal_family_candidate']=='PERSON_PATTERN' and c['person_id']=='persona' for c in cs)

def test_dual_family_one_token_block_two_tokens_retained():
 reg=registry();b=run(reg,[buy(reg,'TOKEN_X',sig='x'),buy(reg,'TOKEN_X',wallet='personA-wallet',sig='ax'),buy(reg,'TOKEN_Y',sig='y')]);ds,en=inputs(b);mail=render(b,ds,en,NOW)
 assert mail['html'].count('TOKEN_X')==1 and mail['html'].count('TOKEN_Y')==1 and mail['html'].count('<article ')==2
 assert mail['html'].count('data-family="TOKEN_CONSENSUS"')==1

def test_enrichment_failure_no_old_enrichment():
 reg=registry();b=run(reg,[buy(reg)]);ds,en=inputs(b);assert render(b,ds,None,NOW) is None
 with pytest.raises(ValueError,match='OLD_ENRICHMENT'):render(b,ds,{**en,'by_signal':{'old':'TOKEN_X'}},NOW)
 assert render(b,ds,{**en,'run_id':'old'},NOW) is None

def test_renderer_crash_clean_rebuild(tmp_path):
 reg=registry();b=run(reg,[buy(reg)]);ds,en=inputs(b)
 with pytest.raises(RuntimeError,match='RENDER_CRASH'):render(b,ds,en,NOW,fail=True)
 assert render(b,ds,en,NOW)==render(b,ds,en,NOW)

def test_expired_candidate_no_artifact_and_claim(tmp_path):
 r,reg=state(tmp_path);b=run(reg,[buy(reg)]);ds,en=inputs(b);box=MailOutbox(r.db);a=box.prepare(b,ds,en,NOW)
 assert render(b,ds,en,iso(BASE+900)) is None;assert not box.claim(a['mail_run_id'],iso(BASE+900));assert r.db.execute('SELECT state FROM meme_mail_outbox').fetchone()[0]=='EXPIRED_NO_SEND';r.close()

def test_same_run_twice_one_outbox_identity(tmp_path):
 r,reg=state(tmp_path);b=run(reg,[buy(reg)]);ds,en=inputs(b);box=MailOutbox(r.db);assert box.prepare(b,ds,en,NOW)==box.prepare(b,ds,en,NOW);assert r.db.execute('SELECT count(*) FROM meme_mail_outbox').fetchone()[0]==1;r.close()

class MockSent:
 namespace='TEST'
 def __init__(self):self.sent={};self.accepts=0
 def accept(self,mid,sha,body):self.accepts+=1;self.sent[mid]=(sha,'message-1');return 'message-1'
 def search_sent(self,mid,sha):return [self.sent[mid][1]] if mid in self.sent and self.sent[mid][0]==sha else []
 def readback(self,message,mid,sha):return self.sent.get(mid)==(sha,message)

def test_gmail_accepted_sent_lost_restart_no_duplicate(tmp_path):
 r,reg=state(tmp_path);b=run(reg,[buy(reg)]);ds,en=inputs(b);box=MailOutbox(r.db);a=box.prepare(b,ds,en,NOW);provider=MockSent()
 with pytest.raises(SystemExit):box.simulate_delivery(a['mail_run_id'],provider,NOW,crash=True)
 r.close();r=Repository(tmp_path/'meme.sqlite');box=MailOutbox(r.db);box.simulate_delivery(a['mail_run_id'],provider,iso(BASE+950));box.simulate_delivery(a['mail_run_id'],provider,iso(BASE+950))
 assert provider.accepts==1 and r.db.execute('SELECT state FROM meme_mail_outbox').fetchone()[0]=='SENT';r.close()

def test_uncertain_no_search_match_never_blind_retry(tmp_path):
 r,reg=state(tmp_path);b=run(reg,[buy(reg)]);ds,en=inputs(b);box=MailOutbox(r.db);a=box.prepare(b,ds,en,NOW);assert box.claim(a['mail_run_id'],NOW);provider=MockSent();box.simulate_delivery(a['mail_run_id'],provider,NOW);assert provider.accepts==0 and r.db.execute('SELECT state FROM meme_mail_outbox').fetchone()[0]=='UNCERTAIN';r.close()

def test_concurrent_prepare_and_claim_one_worker(tmp_path):
 r,reg=state(tmp_path);r.close();b=run(reg,[buy(reg)]);ds,en=inputs(b);barrier=threading.Barrier(4)
 def worker(_):
  q=Repository(tmp_path/'meme.sqlite');box=MailOutbox(q.db);barrier.wait();a=box.prepare(b,ds,en,NOW);claimed=box.claim(a['mail_run_id'],NOW);q.close();return claimed
 with ThreadPoolExecutor(max_workers=4) as pool:assert sum(pool.map(worker,range(4)))==1
 q=Repository(tmp_path/'meme.sqlite');assert q.db.execute('SELECT count(*) FROM meme_mail_outbox').fetchone()[0]==1;q.close()

def test_migration_idempotent_old_candidate_no_replay(tmp_path):
 r,reg=state(tmp_path);e=normalize('old',tx());FrankStore(r).put(e,advance=True,observation={'detected_at':'1','normalized_at':'2'})
 # Separate fresh database migration captures every existing observation as baseline excluded.
 r.db.execute("DELETE FROM meme_meta WHERE key='migration_cutoff'");r.db.execute("DELETE FROM meme_meta WHERE key='registry_at_migration'")
 migrate(r.db,iso(BASE),reg,legacy_wallet=WALLET);migrate(r.db,iso(BASE+20),reg,legacy_wallet=WALLET)
 assert r.db.execute("SELECT state FROM meme_source_observations WHERE signature='old'").fetchone()[0]=='BASELINE_EXCLUDED';assert r.db.execute('SELECT count(*) FROM meme_runs').fetchone()[0]==0;assert FrankStore(r).cursor()['signature']=='old';r.close()

def test_signal_state_restart_no_loss_no_duplicate(tmp_path):
 r,reg=state(tmp_path);store=SignalStore(r.db,reg,POLICY);f=buy(reg);b=store.stage([f],NOW,observation=(WALLET,'new'));r.close();r=Repository(tmp_path/'meme.sqlite');store=SignalStore(r.db,reg,POLICY);assert store.stage([f],NOW) is None;assert r.db.execute('SELECT count(*) FROM meme_signals').fetchone()[0]==1;assert r.db.execute('SELECT count(*) FROM meme_runs').fetchone()[0]==1;r.close()

@pytest.mark.parametrize('kind',['schema','hash','namespace'])
def test_schema_hash_namespace_fail_closed(kind):
 reg=registry();b=run(reg,[buy(reg)])
 if kind=='hash':b['run_id']='wrong'
 else:
  b={k:v for k,v in b.items() if k!='payload_sha256'};b['schema_version']=3 if kind=='schema' else 2;b['namespace']='LIVE' if kind=='namespace' else 'TEST';b=seal(b)
 with pytest.raises(ValueError):validate_run(b,namespace='TEST')

def test_missing_facts_unavailable_not_guessed():
 reg=registry();f=buy(reg);assert f['USD_estimate']['value'] is None and f['USD_estimate']['reason'];assert f['features']['liquidity']['value'] is None;assert not f['features']['lifetime_first_entry_proven']

def test_live_registry_approval_and_wallet_mapping():
 with pytest.raises(ValueError,match='USER_APPROVAL'):Registry({'schema_version':1,'namespace':'LIVE','persons':[{'person_id':'invented','display_name':'x','wallets':[]}]})
 reg=registry();value={'schema_version':1,'namespace':'TEST','persons':list(reg.persons.values())};value['persons'][1]['wallets'].append({'chain':'solana','address':WALLET,'verified':True})
 with pytest.raises(ValueError,match='AMBIGUOUS'):Registry(value,namespace='TEST')

def test_synthetic_run_cannot_publish_live_before_network():
 reg=registry();b=run(reg,[buy(reg)]);api=MemoryAPI();t=MemeTransport('LIVE',api=api,live_validator=lambda _:None)
 with pytest.raises(ValueError):t.publish_run(b,1)
 assert not api.calls

def test_private_exact_readback_idempotent_restart_and_pointer_no_rollback():
 reg=registry();b=run(reg,[buy(reg)]);api=MemoryAPI();t=MemeTransport('TEST',test_id='unit',api=api);t.publish_run(b,1);puts=api.puts;t.publish_run(b,1);assert api.puts==puts
 other=run(reg,[buy(reg,sig='later',at=BASE+30)]);MemeTransport('TEST',test_id='unit',api=api).publish_run(other,2)
 with pytest.raises(Conflict,match='ROLLBACK'):t.publish_run(b,1)

def test_private_partial_publish_no_pointer(tmp_path):
 reg=registry();b=run(reg,[buy(reg)]);api=MemoryAPI();t=MemeTransport('TEST',test_id='partial',api=api);api.faults=[('PUT',RemoteError(403),False)]
 with pytest.raises(RemoteError):t.publish_run(b,1)
 assert not any('/manifest/' in p for p in api.files)

def test_followability_requires_executable_entry_not_wallet_fill():
 from mission_agent.meme.followability import evaluate
 assert all(x['status']=='UNAVAILABLE' for x in evaluate(100,[{'at':0,'bid':'1','ask':'1','executable':True,'source':'wallet-fill'}]).values())
 q=[{'at':100,'bid':'99','ask':'100','executable':True,'source':'test-orderbook','notional':'10'},{'at':160,'bid':'110','ask':'111','executable':True,'source':'test-orderbook'}]
 assert evaluate(100,q)['60']['delayed_entry_return']=='0.1'

def test_local_rollback_tool_restores_one_original_plist(tmp_path,monkeypatch):
 from scripts import meme_local_migration as m
 old=tmp_path/'old.plist';new=tmp_path/'new.plist';new.write_bytes(b'new');calls=[]
 monkeypatch.setattr(m,'command',lambda *a,**k:calls.append(a));monkeypatch.setattr(m,'scanner_processes',lambda:[])
 m.restore_agent(old,new,b'known-good',domain='gui/test')
 assert old.read_bytes()==b'known-good' and not new.exists()
 assert calls[0][0:2]==('launchctl','bootout') and calls[-1][0:2]==('launchctl','bootstrap')

def test_additive_migration_retains_source_cursor_counts_and_backup(tmp_path):
 import sqlite3
 r=Repository(tmp_path/'source.sqlite');s=FrankStore(r);e=normalize('original',tx());s.put(e,advance=True,observation={'detected_at':'1','normalized_at':'2'});before=s.cursor();backup=sqlite3.connect(tmp_path/'backup.sqlite');r.db.backup(backup);assert backup.execute('PRAGMA integrity_check').fetchone()[0]=='ok';backup.close();reg=registry();migrate(r.db,NOW,reg,legacy_wallet=WALLET);migrate(r.db,NOW,reg,legacy_wallet=WALLET)
 assert s.cursor()==before and r.db.execute('SELECT COUNT(*) FROM frank_transactions').fetchone()[0]==1 and r.db.execute('SELECT COUNT(*) FROM frank_observations').fetchone()[0]==1;r.close()

def test_additional_wallet_collector_seed_and_restart_real_namespace_only(tmp_path):
 from mission_agent.meme.collector import WalletCollector
 reg=registry();wallet='frank-wallet2'
 def raw(sig,slot):
  value=tx();value['slot']=slot;value['transaction']['message']['accountKeys'][0]['pubkey']=wallet;value['transaction']['message']['instructions'][0]['parsed']['info']['authority']=wallet
  for k in ['preTokenBalances','postTokenBalances']:
   for b in value['meta'][k]:b['owner']=wallet
  return value
 class RPC:
  def __init__(self):self.new=False
  def signatures(self,**kw):return [{'signature':'new'},{'signature':'seed'}] if self.new else [{'signature':'seed'}]
  def transaction(self,sig):return raw(sig,13 if sig=='new' else 12)
 rpc=RPC();r=Repository(tmp_path/'wallet.sqlite');c=WalletCollector(r,tmp_path/'wallet',wallet,rpc);assert c.cycle()['normalized']==0;assert r.db.execute('SELECT COUNT(*) FROM frank_observations').fetchone()[0]==0;rpc.new=True;assert c.cycle()['normalized']==1;r.close();r=Repository(tmp_path/'wallet.sqlite');c=WalletCollector(r,tmp_path/'wallet',wallet,rpc);assert c.cycle()['normalized']==0;assert c.store.cursor()['signature']=='new';r.close()

def test_decision_cannot_rewrite_person_amount_or_use_old_run():
 reg=registry();b=run(reg,[buy(reg)]);ds,en=inputs(b);body={k:v for k,v in ds[0].items() if k!='payload_sha256'}
 for change in [{'person_ids':['invented']},{'mint':'wrong'},{'run_id':'previous'},{'candidate_age_seconds':999}]:
  with pytest.raises(ValueError):render(b,[seal({**body,**change})],en,NOW)

def test_live_mail_provider_is_forbidden(tmp_path):
 r,reg=state(tmp_path);b=run(reg,[buy(reg)]);ds,en=inputs(b);box=MailOutbox(r.db);mail=box.prepare(b,ds,en,NOW);provider=MockSent();provider.namespace='LIVE'
 with pytest.raises(ValueError,match='NO_REAL_GMAIL'):box.simulate_delivery(mail['mail_run_id'],provider,NOW)
 assert provider.accepts==0;r.close()

def test_no_send_decision_persisted_without_email(tmp_path):
 r,reg=state(tmp_path);b=run(reg,[buy(reg)]);ds=[decision(c,b,send=False,now=NOW) for c in b['candidates']];en={'run_id':b['run_id'],'status':'SUCCESS','by_signal':{}}
 assert MailOutbox(r.db).prepare(b,ds,en,NOW) is None;assert r.db.execute('SELECT COUNT(*) FROM meme_decisions').fetchone()[0]==1;assert r.db.execute('SELECT COUNT(*) FROM meme_mail_outbox').fetchone()[0]==0;r.close()

@pytest.mark.parametrize('field,value',[('expires_at',iso(BASE+99999)),('person_ids',['invented']),('tx_signatures',['invented']),('candidate_id','changed')])
def test_resealed_fact_identity_or_ttl_tampering_fails(field,value):
 reg=registry();b=run(reg,[buy(reg)]);body={k:v for k,v in b.items() if k!='payload_sha256'};c={k:v for k,v in b['candidates'][0].items() if k!='payload_sha256'};c[field]=value;body['candidates']=[seal(c)]
 with pytest.raises(ValueError):validate_run(seal(body),namespace='TEST')
