import argparse,csv,hashlib,json,os
from pathlib import Path
from .wallet_graph import PersonWalletGraph
from .solana_export import configured_provider,Exporter,DataSourceUnavailable
from .event_classifier import decode_transaction,classify,dedupe
from .episode_builder import build_episodes,FIELDS
from .feature_builder import snapshot
from .split import chronological,freeze
from .signal_discovery import discover
from .robustness import robustness
from .qualification import qualify,REQUIRED
from .report import json_file,csv_file,report
from .negative_controls import evaluate_family
from .reconciliation import import_events,reconcile
from .evaluation import run
from .replay import FileQuoteProvider,HistoricalQuoteProvider
from .segmentation import infer_dormant_gap
ROOT=Path(__file__).resolve().parents[1]
def validate(person,args):
    policy=json.loads(Path(args.policy).read_text());seed=json.loads(Path(args.persons).read_text())[person];graph=PersonWalletGraph(seed)
    if policy['minimum_episode_count']<30: raise ValueError('MINIMUM_SAMPLE_BELOW_CANONICAL_POLICY')
    out=Path(args.output)/person;out.mkdir(parents=True,exist_ok=True)
    provider,source=configured_provider();provider.page_size=args.page_size;exporter=Exporter(out/'raw-events.sqlite',provider);errors=[]
    if not args.cache_only:
        for w in seed['wallets']:
            try: exporter.export(w['address'],args.max_pages)
            except DataSourceUnavailable as e: errors.append({'wallet':w['address'],'reason':str(e)})
    transactions=exporter.transactions();events=[]
    for sig,tx in transactions: events.extend(decode_transaction(sig,tx))
    assertions=[];import_hash=None
    if args.events:
        imported,assertions,import_hash=import_events(Path(args.events),graph,transactions)
        # Preserve raw decoder audit rows, substitute route-normalized indexer events per covered signature.
        covered={e['signature'] for e in imported};events=[e for e in events if e['signature'] not in covered]+imported
    classified=dedupe([classify(e,graph) for e in events if not e.get('failed')]);cp=exporter.checkpoint()
    complete=bool(cp) and len(cp)==len(seed['wallets']) and all(c['complete'] for c in cp)
    times=[tx['blockTime'] for _,tx in transactions if tx.get('blockTime') is not None]
    availability={'source':source,'available':bool(transactions) or not errors and not args.cache_only,'blocked_reason':errors or ('HISTORY_EXPORT_INCOMPLETE' if not complete else 'RAW_ACCOUNT_COVERAGE_AND_ECONOMIC_RECONCILIATION_REQUIRED'),'required_env_var':['SOLANA_RPC_URL','ALCHEMY_API_KEY','HELIUS_API_KEY','HISTORICAL_QUOTES_FILE'],'last_successful_checkpoint':cp,'raw_transaction_count':len(transactions),'normalized_event_count':len(classified),'history_complete':complete,'history_start':min(times,default=None),'history_end':max(times,default=None),'history_span_days':(max(times)-min(times))/86400 if times else None,'account_history_scope':'WALLET_REFERENCED_TRANSACTIONS_ONLY','token_account_coverage_complete':False,'lossless_import_sha256':import_hash}
    episodes=build_episodes(classified,person,policy['dust_quantity'],complete);reconciled=reconcile(classified,assertions)
    for ep in episodes:
        if complete and reconciled.get(ep['mint']) and ep['reconstruction_status']=='RECONSTRUCTED_PENDING_BALANCE_RECONCILIATION': ep['reconstruction_status']='FULLY_RECONSTRUCTED'
    valid=[e for e in episodes if e['reconstruction_status']=='FULLY_RECONSTRUCTED'];splits=chronological(valid,policy['split_fractions'])
    source_dir=ROOT.parent/'validation'/person;fixture_rows=list(csv.DictReader((source_dir/(person+'-episodes.csv')).read_text(encoding='utf-8-sig').splitlines()))
    manifest=[{'path':str(p.relative_to(ROOT.parent)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(source_dir.iterdir()) if p.is_file()]
    json_file(out/'source-research-manifest.json',manifest);json_file(out/'source-research-fixtures.json',fixture_rows)
    market=json.loads(Path(args.market).read_text()) if args.market else []
    features=[]
    for ep in valid:
        rows=[e for e in classified if e.get('mint')==ep['mint'] and e['signature'] in ep['source_signatures']]
        for e in rows:
            if e['event_type']=='MARKET_BUY': features.append({'episode_id':ep['episode_id'],**snapshot(rows,e['block_time'],[m for m in market if m['mint']==ep['mint']])})
    training_ids={e['episode_id'] for e in splits['TRAIN']};patterns=discover([f for f in features if f['episode_id'] in training_ids])
    train_events=[e for e in classified if any(ep['episode_id'] in training_ids and e['signature'] in ep['source_signatures'] for ep in valid)]
    gap=infer_dormant_gap([e for e in train_events if e.get('mint') and e['event_type'] in {'MARKET_BUY','MARKET_SELL'}])
    quotes_path=args.quotes or os.environ.get('HISTORICAL_QUOTES_FILE');quote_provider=FileQuoteProvider(json.loads(Path(quotes_path).read_text())) if quotes_path else HistoricalQuoteProvider()
    signals=[];replays=[];evaluations={}
    if patterns:
        freeze(out/'frozen-config.json',{'policy':policy,'seed':seed,'patterns':patterns,'segmentation':gap,'train_ids':sorted(training_ids),'code_sha256':hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'meme_person_validation').glob('*.py')))).hexdigest()})
    else: json_file(out/'freeze-status.json',{'status':'NOT_FROZEN_NO_TRAIN_DATA','holdout_consumed':False})
    for split in ['TRAIN','VALIDATION','HOLDOUT']:
        sig,rp,results=run(splits[split],features,patterns,quote_provider,policy,fixture_rows);signals.extend(sig);replays.extend(rp);evaluations[split]=results
        json_file(out/(split.lower()+'-report.json'),{'status':'EVALUATED_RESEARCH_ONLY' if results else 'NOT_EVALUATED','reason':None if results else 'CANONICAL_DATA_OR_GATES_MISSING','episode_count':len(splits[split]),'results':results,'thresholds_retuned':False})
    gates={k:False for k in REQUIRED};gates.update(wallet_graph=graph.status()=='RESOLVED',history=complete and availability['token_account_coverage_complete'],reconciliation=bool(valid) and len(valid)==len(episodes),causality=bool(features),frozen_config=(out/'frozen-config.json').exists())
    qualification=qualify(gates,len(valid),policy['minimum_episode_count'])
    json_file(out/'wallet-map.json',seed);csv_file(out/'wallet-relationship-evidence.csv',seed['relationships'],['source','destination','mint','evidence_id','source_document','relationship_conclusion','ownership_conclusion'])
    json_file(out/'data-availability.json',availability);csv_file(out/'normalized-events.csv',classified);csv_file(out/'transfer-classification.csv',classified);csv_file(out/'episodes.csv',episodes,FIELDS);json_file(out/'episodes.json',episodes);json_file(out/'features.json',features);json_file(out/'signal-candidates.json',signals);json_file(out/'replay.json',replays)
    json_file(out/'robustness.json',{'all_episodes':robustness(valid),'by_pattern':{pattern['pattern_id']:robustness([e for e in valid if any(s['episode_id']==e['episode_id'] and s['trigger_version']['pattern_id']==pattern['pattern_id'] for s in signals)]) for pattern in patterns}})
    json_file(out/'pattern-candidates.json',{'status':'NO_VALIDATED_PATTERN','patterns':[],'research_candidates':patterns});json_file(out/'qualification.json',qualification);json_file(out/'segmentation-research.json',gap)
    json_file(out/'negative-control-report.json',evaluate_family(['position_growth_ratio','buys_24h','no_major_sell'],fixture_rows));json_file(out/'forward-state.json',{'state':'NOT_STARTED','interface':'ForwardInterface','scheduler':False})
    report(out,person,availability,qualification,len(fixture_rows),graph)
    exporter.db.close();print(json.dumps({'person':person,'status':qualification['status'],'raw_transactions':len(transactions),'valid_episodes':len(valid),'output':str(out)},ensure_ascii=False),flush=True)
def main():
    p=argparse.ArgumentParser(description='Offline PERSON_PATTERN research; checkpoint resume is automatic')
    p.add_argument('command',choices=['validate','validate-all']);p.add_argument('--person');p.add_argument('--page-size',type=int,default=100);p.add_argument('--max-pages',type=int,default=1);p.add_argument('--output',default=str(ROOT/'output'));p.add_argument('--policy',default=str(ROOT/'config/validation-policy.json'));p.add_argument('--persons',default=str(ROOT/'config/persons.json'));p.add_argument('--cache-only',action='store_true');p.add_argument('--events');p.add_argument('--quotes');p.add_argument('--market')
    args=p.parse_args();people=json.loads(Path(args.persons).read_text())
    if args.max_pages<1 or not 1<=args.page_size<=1000: p.error('positive max-pages and page-size 1..1000 required')
    if args.command=='validate' and args.person not in people: p.error('--person must identify a configured person')
    if args.command=='validate-all' and args.events: p.error('--events requires a single configured person')
    for person in ([args.person] if args.command=='validate' else people): validate(person,args)
if __name__=='__main__': main()
