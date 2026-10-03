import copy,csv,json,tempfile,unittest
from pathlib import Path
from meme_person_validation.wallet_graph import PersonWalletGraph
from meme_person_validation.event_classifier import classify,dedupe,decode_transaction
from meme_person_validation.episode_builder import build_episodes
from meme_person_validation.feature_builder import snapshot
from meme_person_validation.replay import replay,FileQuoteProvider,HistoricalQuoteProvider
from meme_person_validation.robustness import robustness,STONK
from meme_person_validation.qualification import qualify,REQUIRED
from meme_person_validation.solana_export import Exporter,CachedFixtureProvider,DataSourceUnavailable
from meme_person_validation.split import chronological,freeze,ForwardInterface
from meme_person_validation.signal_discovery import discover,trigger
ROOT=Path(__file__).resolve().parents[1]
SEEDS=json.loads((ROOT/'config/persons.json').read_text());POLICY=json.loads((ROOT/'config/validation-policy.json').read_text())
def event(n,kind='MARKET_BUY',qty=10,usd=100,mint='mint',time=None):
 return {'event_id':str(n),'signature':str(n),'block_time':n if time is None else time,'wallet':'a','mint':mint,'event_type':kind,'token_delta':qty,'usd_notional':usd}
def economics(n,pnl,mint=None):
 return {'episode_id':str(n),'mint':mint or str(n),'realized_pnl_usd':pnl,'realized_roi':pnl/100,'full_exit':True,'reconstruction_status':'FULLY_RECONSTRUCTED'}
class WalletTests(unittest.TestCase):
 def transfer(self,mint,reverse=False):
  g=PersonWalletGraph(SEEDS['ethermonk']);a,b=[w['address'] for w in g.seed['wallets']];src,dst=(a,b) if reverse else (b,a)
  e=classify({'source_owner':src,'destination_owner':dst,'mint':mint,'raw_event_type':'TRANSFER'},g)
  self.assertEqual(e['event_type'],'EXTERNAL_TRANSFER');self.assertTrue(e['qualification_blocked'])
 def test_ethermonk_cate_internal_transfer_not_buy(self): self.transfer('CATE')
 def test_ethermonk_fone_internal_transfer_not_buy(self): self.transfer('FONE')
 def test_ethermonk_stonk_transfer_not_sell(self): self.transfer(STONK,True)
 def test_fomo_fee_payer_not_person_wallet(self):
  g=PersonWalletGraph(SEEDS['ethermonk']);self.assertNotIn(g.seed['platform_addresses'][0]['address'],g.accepted)
 def test_pointfarm_unresolved_wallet_no_auto_merge(self):
  g=PersonWalletGraph(SEEDS['point-farm']);self.assertNotIn('6cerGp…615t',g.accepted);self.assertEqual(g.status(),'QUALIFICATION_BLOCKED')
 def test_internal_transfer_preserves_cost_basis(self):
  es=[event(1),{'event_id':'2','signature':'2','block_time':2,'mint':'mint','event_type':'INTERNAL_TRANSFER'},event(3)]
  ep=build_episodes(es,'p')[0];self.assertEqual(ep['buy_count'],2);self.assertEqual(ep['net_cost_basis_usd'],200)
 def test_one_transfer_does_not_resolve_ownership(self):
  g=PersonWalletGraph(SEEDS['ethermonk']);g.seed['relationships'].append({'source':'a','destination':'b'});self.assertEqual(len(g.accepted),1)
 def test_balance_delta_not_trade(self):
  g=PersonWalletGraph(SEEDS['point-farm']);self.assertEqual(classify({'wallet':next(iter(g.accepted)),'token_delta':10},g)['event_type'],'UNKNOWN')
 def test_aggregator_dedupe(self):
  e={**event(1),'verified_swap':True,'route_id':'route'};self.assertEqual(len(dedupe([e,e])),1)
 def test_conflicting_pool_legs_fail_closed(self):
  a={**event(1),'verified_swap':True,'route_id':'route'};b={**a,'token_delta':100};self.assertFalse(dedupe([a,b])[0]['verified_swap'])
class EpisodeTests(unittest.TestCase):
 def test_partial_sell_rebuy_same_episode(self):
  es=[event(1),event(2,'MARKET_SELL',-5,75),event(3)];ep=build_episodes(es,'p');self.assertEqual(len(ep),1);self.assertEqual(ep[0]['realized_pnl_usd'],25)
 def test_full_exit_reentry_new_episode(self): self.assertEqual(len(build_episodes([event(1),event(2,'MARKET_SELL',-10,150),event(3)],'p')),2)
 def test_dust_exit(self): self.assertTrue(build_episodes([event(1),event(2,'MARKET_SELL',-9.99,100)],'p','0.02')[0]['full_exit'])
 def test_open_episode_realized_unrealized_separate(self):
  ep=build_episodes([event(1),event(2,'MARKET_SELL',-5,75)],'p')[0];self.assertEqual(ep['realized_pnl_usd'],25);self.assertIsNone(ep['unrealized_pnl_usd']);self.assertIsNone(ep['full_exit_time'])
 def test_missing_usd_does_not_impute(self):
  ep=build_episodes([event(1,usd=None)],'p')[0];self.assertIsNone(ep['realized_pnl_usd']);self.assertIsNone(ep['net_cost_basis_usd'])
 def test_same_symbol_different_mint(self): self.assertEqual(len(build_episodes([event(1,mint='x'),event(2,mint='y')],'p')),2)
 def test_inbound_airdrop_not_buy(self): self.assertEqual(build_episodes([event(1,'AIRDROP')],'p'),[])
class FeatureTests(unittest.TestCase):
 def test_no_lookahead_feature_leakage(self):
  es=[event(1),event(2),event(1000,usd=999999)];before=snapshot(es,2);self.assertEqual(before,snapshot(es[:2],2));self.assertNotIn('realized_pnl_usd',before)
 def test_future_holder_data_excluded(self): self.assertIsNone(snapshot([event(1)],1,[{'timestamp':2,'holder_count':999}])['holder_count'])
 def test_late_available_market_data_excluded(self): self.assertIsNone(snapshot([event(1)],1,[{'timestamp':0,'available_at':2,'holder_count':999}])['holder_count'])
 def test_lookahead_trigger_rejected(self):
  with self.assertRaises(ValueError): trigger({'feature':'final_pnl','threshold':0},{'final_pnl':99})
 def test_discovery_train_only_distribution(self): self.assertEqual(discover([{'position_growth_ratio':2,'gross_buy_15m':1},{'position_growth_ratio':4,'gross_buy_15m':3}])[0]['thresholds']['position_growth_ratio'],3)
class NegativeControls(unittest.TestCase):
 def reject(self,person,symbol):
  path=ROOT.parent/'validation'/person/(person+'-episodes.csv');rows=list(csv.DictReader(path.read_text(encoding='utf-8-sig').splitlines()));row=next(r for r in rows if r['symbol'].upper()==symbol)
  from meme_person_validation.negative_controls import evaluate_family
  result=evaluate_family(['position_growth_ratio','buys_24h'],[row]);self.assertEqual(result['status'],'FAIL');self.assertEqual(result['controls'][0]['symbol'].upper(),symbol)
 def test_thesolstice_market_repeated_adds_must_not_auto_pass(self): self.reject('thesolstice','MARKET')
 def test_pointfarm_purr_accumulation_failure(self): self.reject('point-farm','PURR')
 def test_pointfarm_ubi_accumulation_failure(self): self.reject('point-farm','UBI')
 def test_pointfarm_toerogan_no_sell_failure(self): self.reject('point-farm','TOEROGAN')
class ReplayTests(unittest.TestCase):
 def setUp(self): self.s={'signal_id':'s','episode_id':'e','person_id':'p','mint':'m','T_signal':100}
 def quote(self,t=160,**changes): return dict({'mint':'m','timestamp':t,'notional_usd':25,'price':1,'quantity':25,'route':'r','liquidity':100,'slippage':.01,'price_impact':.01,'fees':1,'historical_pool_evidence':'fixture','executable':True},**changes)
 def test_replay_uses_future_execution_only(self):
  self.assertEqual(replay(self.s,60,FileQuoteProvider([self.quote(100)]),POLICY)['status'],'UNAVAILABLE');self.assertEqual(replay(self.s,60,FileQuoteProvider([self.quote()]),POLICY)['entry_time'],160)
 def test_insufficient_liquidity_is_unfollowable(self): self.assertEqual(replay(self.s,60,FileQuoteProvider([self.quote(liquidity=1)]),POLICY)['status'],'UNFOLLOWABLE')
 def test_missing_price_is_unavailable(self): self.assertEqual(replay(self.s,60,HistoricalQuoteProvider(),POLICY)['failure_reason'],'HISTORICAL_PRICE_MISSING')
 def test_canonical_horizons_present(self): self.assertEqual(POLICY['canonical_horizons'],[300,900,3600,21600,86400])
 def test_open_exit_is_censored(self): self.assertIsNone(replay(self.s,60,FileQuoteProvider([self.quote()]),POLICY)['return_to_source_full_exit'])
 def test_candle_without_pool_evidence_rejected(self): self.assertFalse(replay(self.s,60,FileQuoteProvider([self.quote(historical_pool_evidence=None)]),POLICY)['followable'])
class RobustnessTests(unittest.TestCase):
 def setUp(self): self.es=[economics(1,100,'other'),economics(2,80,STONK),economics(3,50),economics(4,-20)]
 def test_exclude_top1_dynamic(self): self.assertEqual(robustness(self.es)['EX_TOP1']['realized_pnl'],110)
 def test_exclude_top3_dynamic(self): self.assertEqual(robustness(self.es)['EX_TOP3']['realized_pnl'],-20)
 def test_exclude_stonk_by_mint(self): self.assertEqual(robustness(self.es)['EX_STONK_IF_MATERIAL']['realized_pnl'],130)
 def test_largest_theme_requires_validated_labels(self): self.assertEqual(robustness(self.es)['EX_LARGEST_THEME']['status'],'UNAVAILABLE')
 def test_open_unrealized_excluded(self):
  es=self.es+[dict(economics(5,999999),full_exit=False)];self.assertEqual(robustness(es)['ALL']['sample_count'],4)
class ExportTests(unittest.TestCase):
 def test_checkpoint_resume(self):
  with tempfile.TemporaryDirectory() as d:
   provider=CachedFixtureProvider({('a',None):[{'signature':'s','slot':10}]},{'s':{'slot':10}});e=Exporter(Path(d)/'raw.sqlite',provider);e.export('a');self.assertEqual(e.checkpoint()[0]['last_signature'],'s');e.export('a');self.assertEqual(e.checkpoint()[0]['complete'],1);self.assertEqual(len(e.transactions()),1);e.db.close()
 def test_failed_page_no_cursor_advance(self):
  with tempfile.TemporaryDirectory() as d:
   provider=CachedFixtureProvider({('a',None):[{'signature':'s','slot':10},{'signature':'t','slot':9}]},{'s':{'slot':10}});e=Exporter(Path(d)/'raw.sqlite',provider)
   with self.assertRaises(DataSourceUnavailable): e.export('a')
   self.assertEqual(e.checkpoint(),[]);self.assertEqual(len(e.transactions()),1);provider.transactions['t']={'slot':9};e.export('a');self.assertEqual(e.checkpoint()[0]['last_signature'],'t');e.db.close()
class QualificationTests(unittest.TestCase):
 def test_sample_17_insufficient(self): self.assertEqual(qualify({k:True for k in REQUIRED},17)['status'],'INSUFFICIENT_SAMPLE')
 def test_no_promotion_after_research_pass(self):
  q=qualify({k:True for k in REQUIRED},30);self.assertEqual(q['PERSON_PATTERN'],'OBSERVE_ONLY');self.assertEqual(q['production_trading'],'NO_GO')
 def test_missing_gate_blocks(self): self.assertNotEqual(qualify({'history':True,'wallet_graph':True},30)['status'],'RESEARCH_QUALIFICATION_PASSED')
 def test_lower_minimum_rejected(self):
  with self.assertRaises(ValueError): qualify({},17,17)
 def test_frozen_config_cannot_retune(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'freeze.json';freeze(p,{'x':1})
   with self.assertRaises(ValueError): freeze(p,{'x':2})
 def test_chronological_boundary_purge(self):
  eps=[{'episode_id':str(n),'first_market_buy_time':n,'full_exit_time':n+1} for n in range(10)];eps[0]['full_exit_time']=100;s=chronological(eps);self.assertIn(eps[0],s['PURGED']);self.assertTrue(all(e['first_market_buy_time']>=8 for e in s['HOLDOUT']))
 def test_forward_interface_no_scheduler(self):
  with self.assertRaises(RuntimeError): ForwardInterface().ingest_finalized({})
if __name__=='__main__': unittest.main()

class AdditionalEvidenceTests(unittest.TestCase):
 def test_matched_base_universe_missing_not_zero_fpr(self):
  from meme_person_validation.base_rate import compare
  self.assertIsNone(compare([],[],'young','small')['false_positive_rate'])
 def test_base_false_positive_denominator(self):
  from meme_person_validation.base_rate import compare
  rows=[{'sample_id':str(i),'age_bucket':'a','liquidity_bucket':'l','canonical_executable_replay':True,'return':v} for i,v in enumerate([-1,-.5,1])]
  r=compare([rows[0]],rows,'a','l');self.assertEqual(r['false_positive_rate'],.5);self.assertEqual(r['control_count'],3)
 def test_no_preregistered_cutoff_no_pass(self):
  from meme_person_validation.base_rate import profitability
  self.assertEqual(profitability({'mean_return':100},None)['status'],'UNAVAILABLE')
 def test_policy_missing_metric_unavailable(self):
  from meme_person_validation.base_rate import profitability
  self.assertEqual(profitability({}, {'preregistered':True,'evidence_id':'x','minimums':{'mean_return':0}})['status'],'UNAVAILABLE')
 def test_underwater_add_distinct_from_profitable_add(self):
  es=[dict(event(1),price_usd=10),dict(event(2,usd=50),price_usd=5)]
  f=snapshot(es,2);self.assertEqual(f['unrealized_pnl_before_add'],-50);self.assertEqual(f['adds_on_drawdown_count'],1);self.assertEqual(f['adds_on_green_count'],0)
 def test_complete_inventory_required(self):
  from meme_person_validation.reconciliation import reconcile
  self.assertEqual(reconcile([event(1)],[{'mint':'mint','final_quantity':'10'}]),{})
 def test_unknown_transfer_blocks_reconciliation(self):
  from meme_person_validation.reconciliation import reconcile
  es=[event(1),event(2,'EXTERNAL_TRANSFER')];a={'mint':'mint','initial_quantity':'0','final_quantity':'10','complete_owner_inventory':True,'evidence_id':'raw'}
  self.assertFalse(reconcile(es,[a])['mint'])
 def test_largest_theme_computed(self):
  es=[economics(1,10,'a'),economics(2,50,'b')];self.assertEqual(robustness(es,{'a':'t1','b':'t2'})['EX_LARGEST_THEME']['realized_pnl'],10)
 def test_dormant_gap_no_fixed_threshold_without_train(self):
  from meme_person_validation.segmentation import infer_dormant_gap
  self.assertIsNone(infer_dormant_gap([])['threshold_seconds'])
 def test_duplicate_wallet_rejected(self):
  seed=copy.deepcopy(SEEDS['point-farm']);seed['wallets'].append(seed['wallets'][0])
  with self.assertRaises(ValueError): PersonWalletGraph(seed)
 def test_primary_wallet_validity_interval(self):
  seed=copy.deepcopy(SEEDS['point-farm']);seed['wallets'][0]['valid_from']=10;g=PersonWalletGraph(seed)
  self.assertFalse(g.accepts_at(seed['wallets'][0]['address'],9))
 def test_profitable_family_not_passed_on_snapshot(self):
  from meme_person_validation.negative_controls import evaluate_family
  self.assertEqual(evaluate_family(['price_change_since_first_buy'],[{'symbol':'x','buy_count':22,'ROI':'-95.1%'}])['status'],'UNAVAILABLE')
 def test_cli_cache_only_end_to_end(self):
  import subprocess,sys
  with tempfile.TemporaryDirectory() as d:
   r=subprocess.run([sys.executable,'-m','meme_person_validation','validate-all','--cache-only','--output',d],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   for person in SEEDS:
    p=Path(d)/person;self.assertEqual(json.loads((p/'qualification.json').read_text())['status'],'DATA_BLOCKED');self.assertTrue((p/'raw-events.sqlite').exists());self.assertFalse((p/'frozen-config.json').exists())
 def test_ata_fee_parser_does_not_emit_trade(self):
  tx={'slot':1,'blockTime':1,'meta':{'err':None,'fee':5,'preTokenBalances':[],'postTokenBalances':[]},'transaction':{'message':{'accountKeys':[{'pubkey':'p','signer':True}],'instructions':[{'program':'spl-associated-token-account','programId':'ata','parsed':{'type':'create','info':{'wallet':'p'}}}]}}}
  events=decode_transaction('s',tx);self.assertEqual({e['raw_event_type'] for e in events},{'FEE','ATA_CREATE'})

class MemoRegression(unittest.TestCase):
 def test_jsonparsed_memo_string_not_code_failure(self):
  tx={'slot':1,'blockTime':1,'meta':{'err':None,'fee':5,'preTokenBalances':[],'postTokenBalances':[]},'transaction':{'message':{'accountKeys':[{'pubkey':'p','signer':True}],'instructions':[{'program':'spl-memo','programId':'memo','parsed':'memo text'}]}}}
  self.assertEqual(len(decode_transaction('memo',tx)),1)
