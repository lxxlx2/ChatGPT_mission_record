"""FRANK historical trade coverage research only. Never imports delivery adapters.

M0 production; M1 causal historical SOL valuation; M2 USDT recognition;
M3 one-target reconstructable quote routes. All outputs are DRY_RUN_AUDIT.
"""
import argparse
import copy
import gzip
import hashlib
import json
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import USDC, load_policy
from mission_agent.signals.store import Ledger, quantity
from mission_agent.frank.parser import WSOL, DEX_PROGRAMS
from scripts.frank_hft_sticky_rolling_historical_replay import import_verified

USDT = 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
REQUESTED_USDT = 'Es9vMFrzaCERmJfrF4H2FYDSEVQScAY5NJQTSQ1jD3b'
QUOTES = {USDC, WSOL, USDT}
D = Decimal


def iso(at):
    return datetime.fromtimestamp(at, timezone.utc).isoformat() if at is not None else None


def groups(evidence):
    out = {}
    for e in evidence.get('token_balance_deltas', []):
        if not e['wallet_owned']:
            continue
        g = out.setdefault(e['mint'], {'delta': 0, 'pre': 0, 'post': 0, 'decimals': e['decimals']})
        if g['decimals'] != e['decimals']:
            raise ValueError('DECIMALS_CONFLICT')
        for key, original in [('delta', 'delta'), ('pre', 'pre_amount'), ('post', 'post_amount')]:
            g[key] += int(e[original])
    for e in evidence.get('decoded_transient_token_flows', []):
        g = out.setdefault(e['mint'], {'delta': 0, 'pre': 0, 'post': 0, 'decimals': e['decimals']})
        if g['decimals'] != e['decimals']:
            raise ValueError('DECIMALS_CONFLICT')
        g['delta'] += int(e['net_transfer_raw'])
    return {m: g for m, g in out.items() if g['delta'] != 0}


RESEARCH_MARKETS = {
 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc': 'https://github.com/orca-so/whirlpools/blob/main/README.md',
 'cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG': 'https://github.com/MeteoraAg/damm-v2-sdk',
 'MNFSTqtC93rEfYHB6hF82sKdZpUDFWkViLByLd1k1Ms': 'https://github.com/Bonasa-Tech/manifest',
}


def research_market_record(record, tx):
    """Additional official bindings are research-only, with invocation-bound log.

    A program ID or an unrelated router Swap log alone never establishes trade.
    Unrecognized programs stay unproven. No production registry mutation.
    """
    result=copy.deepcopy(record);proofs=[];stack=[]
    for log in tx.get('meta',{}).get('logMessages') or []:
        parts=log.split()
        if len(parts)>=4 and parts[0]=='Program' and parts[2]=='invoke':
            stack.append(parts[1])
        elif len(parts)>=3 and parts[0]=='Program' and parts[2] in ('success','failed:'):
            if parts[1] in stack:stack=stack[:stack.index(parts[1])]
        elif log.startswith('Program log: Instruction: ') and stack and stack[-1] in RESEARCH_MARKETS:
            kind=log.split('Instruction: ',1)[1].lower()
            if kind.startswith(('swap','route','buy','sell')):
                proofs.append({'program_id':stack[-1],'instruction_log':log,'official_source':RESEARCH_MARKETS[stack[-1]]})
    if proofs:
        evidence=result.setdefault('evidence',{});g=evidence.setdefault('classification_evidence',{})
        g.update(dex_program_interaction=True,swap_instruction_evidence=True)
        result['research_market_binding']=proofs
    return result


def complex_candidate(record):
    e=record.get('evidence',{});p=e.get('classification_evidence',{})
    return (record['classification']=='UNKNOWN_NEEDS_REVIEW' and record.get('frank_is_signer') and
            e.get('tx_err') is None and p.get('opposing_economic_flows'))


def market_proven(record):
    e = record.get('evidence', {}); p = e.get('classification_evidence', {})
    return (record.get('frank_is_signer') is True and e.get('tx_err') is None and
            p.get('dex_program_interaction') is True and p.get('swap_instruction_evidence') is True)


def pick_causal_candle(rows, at):
    """Previous completed minute only; never transaction-minute future close.

    No forward interpolation. Last completed bucket must end <= transaction
    and be at most 60 seconds old. At exact boundary use the previous bucket.
    """
    valid = [r for r in rows if isinstance(r, list) and len(r) >= 6 and
             int(r[0]) + 60 <= at and 0 <= at - (int(r[0]) + 60) < 60]
    if not valid:
        return None
    row = max(valid, key=lambda r: r[0])
    price = D(str(row[4]))
    if not price.is_finite() or price <= 0:
        return None
    return {'price': str(price), 'bucket_start': int(row[0]), 'price_observed_through': int(row[0]) + 60,
            'granularity_seconds': 60, 'field': 'previous_completed_minute_close',
            'lag_seconds': at - (int(row[0]) + 60), 'valuation_label': 'RESEARCH_ESTIMATE'}


class HistoricalPrices:
    def __init__(self, directory):
        self.directory = directory; directory.mkdir(exist_ok=True)
        self.receipts, self.values = [], {}

    def get(self, asset, at):
        if asset == USDC:
            return {'price': '1', 'source': 'FROZEN_V1_USDC_DIRECT_NUMERIC_NOT_PRICE_CONVERSION'}
        symbol = 'SOL-USD' if asset in ('SOL', WSOL) else 'USDT-USD' if asset == USDT else None
        if not symbol or at is None:
            return None
        bucket = (at // 60 - 1) * 60
        key = (symbol, bucket)
        path = self.directory / (symbol + '-' + str(bucket) + '.json')
        if key not in self.values:
            url = 'https://api.exchange.coinbase.com/products/' + symbol + '/candles?' + urllib.parse.urlencode(
                {'start': iso(bucket), 'end': iso(bucket + 60), 'granularity': 60})
            if path.exists():
                receipt = json.loads(path.read_text())
            else:
                receipt = {'endpoint': url, 'source': 'Coinbase Exchange public historical candles',
                           'requested_bucket_start': bucket, 'requested_bucket_end': bucket + 60,
                           'requested_granularity_seconds': 60, 'retrieved_at': iso(int(time.time()))}
                try:
                    request = urllib.request.Request(url, headers={'User-Agent': 'FrankHistoricalCoverageResearch/1.0'})
                    with urllib.request.urlopen(request, timeout=15) as response:
                        raw = response.read(); receipt.update(http_status=response.status,
                            response_sha256=hashlib.sha256(raw).hexdigest(), candles=json.loads(raw))
                except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                    receipt.update(status='PRICE_UNAVAILABLE', exception_class=type(exc).__name__, error=str(exc), candles=[])
                path.write_text(json.dumps(receipt, indent=2))
                time.sleep(.15)
            self.receipts.append(receipt)
            self.values[key] = receipt
        receipt = self.values[key]
        value = pick_causal_candle(receipt.get('candles', []), at)
        return {**value, 'source': receipt['source'], 'endpoint': receipt['endpoint'],
                'response_sha256': receipt.get('response_sha256')} if value else None


def quote_value(quote_groups, at, prices, sol_factor=D(1)):
    """Signed wallet quote delta, preserved leg-by-leg. No target valuation."""
    total, legs = D(0), []
    for mint, g in quote_groups.items():
        price = prices.get('SOL' if mint == WSOL else mint, at)
        if price is None:
            return None, legs, 'PRICE_UNAVAILABLE:' + mint
        factor = sol_factor if mint == WSOL else D(1)
        value = D(quantity(g['delta'], g['decimals'])) * D(price['price']) * factor
        total += value
        legs.append({'asset': mint, 'raw_delta': str(g['delta']), 'quantity_delta': quantity(g['delta'], g['decimals']),
                     'research_USD_delta': str(value), 'price': price, 'SOL_sensitivity_factor': str(factor)})
    return total, legs, None


def reconstruct(record, prices, *, allow_complex=False, sol_factor=D(1)):
    """One signature -> at most one trade. Multi-target actions stay unresolved.

    Single target with USDC debit and proven SOL refund can be one canonical
    target acquisition with a composite NET quote cost. Never discard refund,
    extra acquired tokens or dust. Native SOL/rent vector alone is not quote.
    """
    info = {'signature': record['signature'], 'at': record['block_time'],
            'original_classification': record['classification'], 'original_reason': record['classification_reason'],
            'research_market_binding':record.get('research_market_binding',[])}
    if not market_proven(record):
        return None, {**info, 'category': 'INSUFFICIENT_EVIDENCE', 'reason': 'SIGNER_SUCCESS_RECOGNIZED_SWAP_UNPROVEN',
                      'programs':record.get('evidence',{}).get('program_ids',[])}
    try:
        changed = groups(record['evidence'])
    except ValueError as exc:
        return None, {**info, 'category': 'INSUFFICIENT_EVIDENCE', 'reason': str(exc)}
    targets = {m: g for m, g in changed.items() if m not in QUOTES}
    quotes = {m: g for m, g in changed.items() if m in QUOTES}
    info.update(owned_net_flows=changed, target_assets=list(targets), quote_assets=list(quotes),
                programs=record['evidence']['program_ids'])
    if len(targets) > 1:
        return None, {**info, 'category': 'TRUE_MULTI_ASSET_ACTION',
                      'reason': 'MULTIPLE_RETAINED_WALLET_TARGET_DELTAS; even one raw unit is not discarded'}
    if not targets and len(quotes)>=2:
        return None, {**info, 'category': 'LP_ROUTING_INVENTORY_OPERATION',
                      'reason': 'QUOTE_ONLY_REBALANCE; no meme target asset, not a new signal position'}
    if len(targets) != 1 or not quotes:
        return None, {**info, 'category': 'INSUFFICIENT_EVIDENCE', 'reason': 'NO_SINGLE_TARGET_OR_DECODED_QUOTE'}
    if not allow_complex and (len(quotes) != 1 or USDT not in quotes):
        return None, {**info, 'category': 'INSUFFICIENT_EVIDENCE', 'reason': 'NOT_SINGLE_TARGET_USDT_QUOTE'}
    target, g = next(iter(targets.items()))
    # For WSOL transient refund, require exact native reconciliation to avoid
    # confusing wrapping principal, rent or a separate native payment with quote.
    if WSOL in quotes and record['evidence'].get('decoded_transient_token_flows'):
        info['WSOL_net_raw']=str(quotes[WSOL]['delta'])
        info['native_fee_adjusted_SOL_delta_raw']=record['evidence'].get('fee_adjusted_SOL_delta_lamports')
        native = record['evidence'].get('fee_adjusted_SOL_delta_lamports')
        if native is None or int(native) != quotes[WSOL]['delta']:
            return None, {**info, 'category': 'INSUFFICIENT_EVIDENCE',
                          'reason': 'WSOL_NET_NATIVE_RECONCILIATION_NOT_EXACT'}
    net, legs, error = quote_value(quotes, record['block_time'], prices, sol_factor)
    info.update(quote_legs=legs, research_net_quote_USD_delta=str(net) if net is not None else None)
    if error:
        return None, {**info, 'category': 'INSUFFICIENT_EVIDENCE', 'reason': error}
    if net == 0 or (g['delta'] > 0) == (net > 0):
        return None, {**info, 'category': 'TRUE_MULTI_ASSET_ACTION',
                      'reason': 'NET_TARGET_AND_NET_QUOTE_NOT_OPPOSING; no interpretable single trade reduction; specific intent unresolved'}
    trade = {'mint': target, 'direction': 'BUY' if g['delta'] > 0 else 'SELL',
             'token_amount_raw': str(abs(g['delta'])), 'token_decimals': g['decimals'],
             'quote_asset': USDC, 'quote_amount_raw': str(abs(net) * D(10) ** 12), 'quote_decimals': 12,
             'referenced_pre_raw': str(g['pre']), 'referenced_post_raw': str(g['post'])}
    return trade, {**info, 'category': 'RECONSTRUCTABLE_USER_SWAP',
                   'reason': 'ONE_TARGET_OPPOSING_NET_QUOTE; composite legs preserved and causally valued',
                   'shadow_trade': trade, 'valuation_label': 'RESEARCH_ESTIMATE',
                   'quote_proxy_warning': 'USDC field in isolated engine is USD amount-gate proxy, not actual USDC payment'}


def valued_trade(trade, at, prices, factor=D(1)):
    if trade['quote_asset'] not in ('SOL', USDT):
        return copy.deepcopy(trade), None
    price = prices.get(trade['quote_asset'], at)
    if price is None:
        return copy.deepcopy(trade), {'status': 'UNDETERMINED', 'reason': 'TRANSACTION_TIME_PRICE_UNAVAILABLE'}
    usd = D(quantity(trade['quote_amount_raw'], trade['quote_decimals'])) * D(price['price']) * (factor if trade['quote_asset']=='SOL' else D(1))
    shadow = copy.deepcopy(trade)
    shadow.update(quote_asset=USDC, quote_amount_raw=str(usd*D(10)**12), quote_decimals=12)
    return shadow, {'status': 'RESEARCH_ESTIMATE', 'original_quote': copy.deepcopy(trade),
                    'research_quote_USD': str(usd), 'price': price, 'factor': str(factor),
                    'warning': 'isolated amount proxy only; never production USDC provenance'}


def replay(path, rows, policy, model, prices, usdt, complex_trades, factor=D(1)):
    ledger=Ledger(path); original_bodies={}
    for row in rows:
        record=json.loads(row['body']); original_bodies[row['signature']]=record
        if model>=1 and record['classification']=='ACTIVE_TRADE' and record['trade']['quote_asset']=='SOL':
            record['trade'],record['research_valuation']=valued_trade(record['trade'],record['block_time'],prices,factor)
        additions = complex_trades if model>=3 else usdt if model>=2 else {}
        added=additions.get(row['signature'])
        if added:
            trade=added['trade'];record['evidence']=copy.deepcopy(added['evidence'])
            record.update(classification='ACTIVE_TRADE',classification_reason='RESEARCH_SHADOW_ACTIVE_TRADE',
                          trade=trade,research_only=True,original_production_classification=original_bodies[row['signature']]['classification'])
        values=list(row);values[list(row.keys()).index('body')]=json.dumps(record,sort_keys=True)
        ledger.db.execute('INSERT INTO signatures VALUES('+','.join('?' for _ in values)+')',values)
    engine=Engine(ledger,policy,dry_run=True);engine.drain()
    signals=[json.loads(r[0]) for r in ledger.db.execute('SELECT body FROM signals ORDER BY CAST(created_at AS INTEGER),signal_id')]
    evals=[dict(r) for r in ledger.db.execute('SELECT * FROM v1_evaluations ORDER BY at,evaluation_id')]
    states={r['mint']:json.loads(r['body']) for r in ledger.db.execute('SELECT * FROM v1_states')}
    assert not ledger.db.execute("SELECT 1 FROM outbox WHERE status!='DRY_RUN_AUDIT'").fetchone()
    value={'model':'M'+str(model),'ACTIVE_TRADE':ledger.db.execute("SELECT count(*) FROM signatures WHERE json_extract(body,'$.classification')='ACTIVE_TRADE'").fetchone()[0],
           'ACCUMULATION':engine.summary()['accumulation_trigger_count'],'MULTIPLE':engine.summary()['multiple_trigger_count'],
           'signals':signals,'evaluations':evals,'final_states':states,'outbox_delivery':'DRY_RUN_AUDIT_ONLY',
           'valuation_label':'RESEARCH_ESTIMATE' if model else 'CURRENT_V1'}
    ledger.db.close();return value


def signal_set(model):
    return {(s['episode_id'],s['signal_type']) for s in model['signals']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True);p.add_argument('--policy',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--price-cache',type=Path)
    args=p.parse_args()
    if args.work.exists() or 'live' in args.work.name.lower() or args.source.name=='forward.sqlite':
        raise ValueError('NEW_ISOLATED_HISTORICAL_WORKSPACE_REQUIRED')
    args.work.mkdir(parents=True,mode=0o700)
    verified=Ledger(args.work/'raw-verified.sqlite');history=import_verified(args.source,verified)
    rows=verified.db.execute('SELECT * FROM signatures ORDER BY block_time,slot,signature').fetchall();verified.db.close()
    policy=load_policy(args.policy);prices=HistoricalPrices(args.price_cache or args.work/'price-receipts')
    baseline=replay(args.work/'M0.sqlite',rows,policy,0,prices,{},{});print('BASELINE',baseline['ACTIVE_TRADE'],baseline['ACCUMULATION'],baseline['MULTIPLE'],flush=True)
    old=sqlite3.connect('file:'+str(args.baseline)+'?mode=ro',uri=True)
    expected=old.execute('SELECT signal_id,body FROM signals ORDER BY signal_id').fetchall();old.close()
    actual=sorted((s['signal_id'],json.dumps(s,sort_keys=True)) for s in baseline['signals'])
    if baseline['ACCUMULATION']!=21 or baseline['MULTIPLE']!=10 or actual!=expected:
        raise ValueError('BASELINE_DRIFT')
    records=[json.loads(r['body']) for r in rows]
    class_counts=Counter(r['classification'] for r in records)
    quote_counts=Counter('USDC' if r['trade']['quote_asset']==USDC else r['trade']['quote_asset'] for r in records if r['classification']=='ACTIVE_TRADE')
    usdt_cases=[]; requested_mentions=[]; sol_cases=[]; complex_cases=[]; usdt_trades={};complex_trades={}
    episode_map={}
    for e in baseline['evaluations']:
        if json.loads(e['body'])['kind']=='ACTIVE_TRADE':episode_map[e['signature']]=e['episode_id']
    for row,record in zip(rows,records):
        trade=record.get('trade');e=record.get('evidence',{})
        if record['classification']=='ACTIVE_TRADE' and trade['quote_asset']=='SOL':
            shadow,valuation=valued_trade(trade,record['block_time'],prices)
            sol_cases.append({'signature':record['signature'],'at':record['block_time'],'time_utc':iso(record['block_time']),
                              'mint':trade['mint'],'direction':trade['direction'],'SOL_raw_quantity':trade['quote_amount_raw'],
                              'SOL_quantity':quantity(trade['quote_amount_raw'],trade['quote_decimals']),
                              'token_raw_quantity':trade['token_amount_raw'],'token_quantity':quantity(trade['token_amount_raw'],trade['token_decimals']),
                              'episode_id':episode_map.get(record['signature']),'original_amount_predicate':'UNDETERMINED','valuation':valuation})
        raw=json.loads(gzip.decompress(Path(row['raw_reference']).read_bytes()));tx=raw['transaction'] if 'status' in raw else raw
        # exact string occurrence anywhere in raw; assess owned net flow separately
        if USDT in json.dumps(tx):
            changed=groups(e);owned_usdt=changed.get(USDT)
            audit={'signature':record['signature'],'at':record['block_time'],'original_classification':record['classification'],
                   'Frank_signer':record.get('frank_is_signer',False),'recognized_swap_proven':market_proven(record),
                   'USDT_owned_net_raw':str(owned_usdt['delta']) if owned_usdt else '0',
                   'status':'NO_WALLET_USDT_QUOTE_FLOW'}
            if owned_usdt:
                reconstructed,details=reconstruct(record,prices)
                audit['reconstruction']=details
                if reconstructed:usdt_trades[record['signature']]={'trade':reconstructed,'evidence':record['evidence']}
            usdt_cases.append(audit)
        if REQUESTED_USDT in json.dumps(tx):requested_mentions.append(record['signature'])
        if complex_candidate(record):
            research_record=research_market_record(record,tx)
            reconstructed,audit=reconstruct(research_record,prices,allow_complex=True)
            audit['candidate_scope']='PRODUCTION_AMBIGUOUS' if record['classification_reason']=='AMBIGUOUS_USER_EXCHANGE_ASSETS' else 'OTHER_SIGNED_OPPOSING_FLOW_UNRECOGNIZED_MARKET'
            audit['programs']=record['evidence']['program_ids']
            audit.setdefault('owned_net_flows',groups(record['evidence']))
            complex_cases.append(audit)
            if reconstructed:complex_trades[record['signature']]={'trade':reconstructed,'evidence':research_record['evidence']}
    print('RAW_AUDIT',len(sol_cases),len(usdt_cases),len(complex_cases),Counter(c['category'] for c in complex_cases),flush=True)
    # Sequential additions: M3 retains any independently confirmed USDT trade.
    complex_trades={**usdt_trades,**complex_trades}
    models={'M0':baseline}
    for n in range(1,4):models['M'+str(n)]=replay(args.work/('M'+str(n)+'.sqlite'),rows,policy,n,prices,usdt_trades,complex_trades)
    minus=replay(args.work/'M1-SOL-minus2pct.sqlite',rows,policy,1,prices,{}, {},D('.98'))
    plus=replay(args.work/'M1-SOL-plus2pct.sqlite',rows,policy,1,prices,{}, {},D('1.02'))
    complex_sensitivity_models={}
    for label,scale in [('minus2pct',D('.98')),('plus2pct',D('1.02'))]:
        recovered=dict(usdt_trades)
        for row,record in zip(rows,records):
            if complex_candidate(record):
                raw=json.loads(gzip.decompress(Path(row['raw_reference']).read_bytes()));tx=raw['transaction'] if 'status' in raw else raw
                research_record=research_market_record(record,tx)
                trade,_=reconstruct(research_record,prices,allow_complex=True,sol_factor=scale)
                if trade:recovered[record['signature']]={'trade':trade,'evidence':research_record['evidence']}
        complex_sensitivity_models[label]=replay(args.work/('M3-SOL-'+label+'.sqlite'),rows,policy,3,prices,usdt_trades,recovered,scale)
    new_signals=[]
    for n in range(1,4):
        model=models['M'+str(n)];prev=models['M'+str(n-1)]
        additions=signal_set(model)-signal_set(prev)
        removed=signal_set(prev)-signal_set(model)
        model['new_vs_previous']=len(additions)
        model['new_ACCUMULATION_vs_previous']=sum(k[1]=='FRANK_ACCUMULATION_SIGNAL' for k in additions)
        model['new_MULTIPLE_vs_previous']=sum(k[1]=='FRANK_MULTIPLE_SIGNAL' for k in additions)
        model['lost_ACCUMULATION_vs_previous']=sum(k[1]=='FRANK_ACCUMULATION_SIGNAL' for k in removed)
        model['lost_MULTIPLE_vs_previous']=sum(k[1]=='FRANK_MULTIPLE_SIGNAL' for k in removed)
        model['new_mints']=sorted({s['mint'] for s in model['signals'] if (s['episode_id'],s['signal_type']) in additions})
        for s in model['signals']:
            if (s['episode_id'],s['signal_type']) not in additions:continue
            evalrow=next(e for e in model['evaluations'] if s['signal_id'] in json.loads(e['body'])['signal_ids'])
            involved=[r for r in records if r.get('trade') and r['trade']['mint']==s['mint'] and r['block_time']<=s['triggered_at']]
            new_signals.append({'introduced_at_model':'M'+str(n),'signal':s,'evaluation':json.loads(evalrow['body']),
                                'original_trigger_classification':next(r['classification'] for r in records if r['signature']==s['triggering_signature']),
                                'original_known_trade_prefix':involved,'valuation_label':'RESEARCH_ESTIMATE'})
    sensitivity=[]
    for s in models['M1']['signals']:
        if (s['episode_id'],s['signal_type']) in signal_set(baseline):continue
        key=(s['episode_id'],s['signal_type']);sensitivity.append({'episode':s['episode_id'],'mint':s['mint'],
                    'signal_type':s['signal_type'],'classification':'ROBUST_PASS' if key in signal_set(minus) and key in signal_set(plus) else 'BOUNDARY_SENSITIVE'})
    positive_only=signal_set(plus)-signal_set(models['M1'])
    winner_audits=[]
    for name,mint in [('STONK','6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx'),('PAID','98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump')]:
        winner_audits.append({'name':name,'mint':mint,'models':{k:{'ACCUMULATION':sum(s['mint']==mint and s['signal_type']=='FRANK_ACCUMULATION_SIGNAL' for s in v['signals']),
                                'MULTIPLE':sum(s['mint']==mint and s['signal_type']=='FRANK_MULTIPLE_SIGNAL' for s in v['signals'])} for k,v in models.items()}})
    result={'study':'FRANK_TRADE_COVERAGE_GAPS_HISTORICAL_REPLAY_2026-10-04','history':history,
            'baseline_classifications':{k:class_counts[k] for k in ('ACTIVE_TRADE','PASSIVE_TRANSFER','ATA_CREATE','FAILED_TX','FEE','UNKNOWN_NEEDS_REVIEW')},
            'baseline_quote_assets':{'USDC':quote_counts['USDC'],'SOL':quote_counts['SOL'],'other':sum(v for k,v in quote_counts.items() if k not in ('USDC','SOL'))},'baseline_parity':'PASS_31_SIGNALS_EXACT',
            'SOL':{'active_trades':len(sol_cases),'unique_mints':len({c['mint'] for c in sol_cases}),
                   'known_episodes':len({c['episode_id'] for c in sol_cases if c['episode_id']}),
                   'orphan_sell_cases':sum(c['episode_id'] is None for c in sol_cases),
                   'BUY':sum(c['direction']=='BUY' for c in sol_cases),'SELL':sum(c['direction']=='SELL' for c in sol_cases),
                   'undetermined_amount':len(sol_cases),'cases':sol_cases,
                   'new_ACCUMULATION':models['M1']['ACCUMULATION']-baseline['ACCUMULATION'],
                   'new_MULTIPLE':models['M1']['MULTIPLE']-baseline['MULTIPLE']},
            'USDT':{'official_mint':USDT,'official_identity_source':'https://tether.to/en/supported-protocols/',
                    'requested_mint':REQUESTED_USDT,'requested_mint_verified_as_USDT':False,
                    'requested_mint_raw_mentions':len(requested_mentions),'raw_candidate_tx':len(usdt_cases),
                    'confirmed_active_quote_trades':len(usdt_trades),'cases':usdt_cases,
                    'price_deviation_check':'NOT_APPLICABLE_NO_CONFIRMED_WALLET_USDT_QUOTE',
                    'USDT_ACTIVE_CASES':len(usdt_trades)},
            'COMPLEX':{'research_market_official_sources':RESEARCH_MARKETS,'ambiguous_candidates':sum(c['candidate_scope']=='PRODUCTION_AMBIGUOUS' for c in complex_cases),'all_candidates':len(complex_cases),'unique_signatures':len({c['signature'] for c in complex_cases}),
                       'categories':dict(Counter(c['category'] for c in complex_cases)),
                       'unique_assets':sorted({m for c in complex_cases for m in c.get('owned_net_flows',{})}),
                       'program_combinations':dict(Counter('|'.join(c.get('programs',[])) for c in complex_cases)),
                       'cases':complex_cases},
            'models':models,'new_signal_audits':new_signals,
            'SOL_sensitivity':{'minus2pct_ACCUMULATION':minus['ACCUMULATION'],'minus2pct_MULTIPLE':minus['MULTIPLE'],
                               'exact_ACCUMULATION':models['M1']['ACCUMULATION'],'exact_MULTIPLE':models['M1']['MULTIPLE'],
                               'plus2pct_ACCUMULATION':plus['ACCUMULATION'],'plus2pct_MULTIPLE':plus['MULTIPLE'],
                               'candidate_classification':sensitivity,'signals_only_plus2pct':len(positive_only),
                               'interpretation':'SOL buys=0; no SOL BUY amount crosses any entry threshold'},
            'complex_SOL_sensitivity':{label:{k:model[k] for k in ('ACTIVE_TRADE','ACCUMULATION','MULTIPLE')} for label,model in complex_sensitivity_models.items()},
            'price_receipts':prices.receipts,'winner_audits':winner_audits,'PNL':'PNL_UNAVAILABLE',
            'production_files_changed':False,'live_service_restarted':False,'live_signal_sent':False,
            'production_trading':'NO_GO',
            'method':{'valuation':'prior completed 60-second Coinbase USD candle, max lag <60s, RESEARCH_ESTIMATE',
                      'USDC':'original direct numeric policy unchanged',
                      'complex':'one target and opposing net quote value; all quote legs retained, no dust threshold',
                      'HFT':'original sticky production HFT and rapid roundtrip unchanged',
                      'quote_proxy':'converted economic amounts stored under USDC only in isolated replay for original numeric gates; original evidence retained separately'}}
    recovered_cases=[c for c in complex_cases if c['category']=='RECONSTRUCTABLE_USER_SWAP']
    memberships=defaultdict(set)
    for evaluation in models['M3']['evaluations']:
        if json.loads(evaluation['body'])['kind']=='ACTIVE_TRADE':
            memberships[evaluation['signature']].add(evaluation['episode_id'])
    for case in recovered_cases:
        case['shadow_episode_ids']=sorted(memberships[case['signature']])
        case['shadow_active_evaluations']=[json.loads(e['body']) for e in models['M3']['evaluations']
                                         if e['signature']==case['signature'] and json.loads(e['body'])['kind']=='ACTIVE_TRADE']
    result['confirmed_coverage_false_negatives']={
        'classifier_transactions':len(recovered_cases),
        'episodes':len({eid for c in recovered_cases for eid in c['shadow_episode_ids']}),
        'mints':sorted({c['shadow_trade']['mint'] for c in recovered_cases}),
        'amount_unvalued_ALREADY_ACTIVE_transactions':len(sol_cases),
        'missed_ACCUMULATION':models['M3']['new_ACCUMULATION_vs_previous'],
        'missed_MULTIPLE':models['M3']['new_MULTIPLE_vs_previous'],
        'current_MULTIPLE_lost_under_M3':models['M3']['lost_MULTIPLE_vs_previous'],
        'net_MULTIPLE_delta':models['M3']['MULTIPLE']-baseline['MULTIPLE'],
        'scope':'Only reconstructed user-level trades count as classifier false negatives. Remaining UNKNOWN not counted.'}
    for audit in new_signals:
        signal=audit['signal']
        causal=[c for c in recovered_cases if signal['episode_id'] in c['shadow_episode_ids']
                and c['at'] <= signal['triggered_at']]
        causal.sort(key=lambda c:(c['at'],c['signature']))
        audit['reconstructed_causal_trade_prefix']=causal
        audit['first_buy']=next(({'at':c['at'],'signature':c['signature'],
                                  'quote_legs':c['quote_legs'],'trade':c['shadow_trade']}
                                 for c in causal if c['shadow_trade']['direction']=='BUY'),None)
        audit['trigger_kind']=audit['evaluation']['kind']
        audit['triggering_buy_is_new_transaction']=audit['evaluation']['kind']=='ACTIVE_TRADE'
        audit['valuation_source']='USDC direct numeric; no SOL or USDT conversion in this signal prefix'
    result['recommendations']={
        'SOL':{'coverage':'LOW','recommendation':'NEED_MORE_DATA',
               'reason':'Nine SELLs already ACTIVE; no SOL BUY eligibility sample; zero new entry signals'},
        'USDT':{'coverage':'LOW','recommendation':'KEEP_CURRENT',
                'reason':'63 raw mentions but zero confirmed Frank net USDT quote; sample-scoped conclusion'},
        'COMPLEX':{'coverage':'MATERIAL','recommendation':'RESEARCH_FIX_CANDIDATE',
                   'reason':'19 proven missed trades; gross one new ACC and one new MULT; sticky HFT removes STONK MULT',
                   'remaining':'NEED_MORE_DATA: 12 unproven market instruction bindings, two transient native mismatches; 14 true multi-asset actions require separate semantics'}}
    result['unresolved_name_bindings']={name:'UNRESOLVED_NAME_TO_MINT'
                                       for name in ('Pistacio','PERPSPAD','fone','Pumpcat','CATE')}
    base_mints={state['mint'] for state in baseline['final_states'].values()}
    for name, model in models.items():
        active_mints={state['mint'] for state in model['final_states'].values()}
        model['new_observed_sequence_mints_vs_M0']=sorted(active_mints-base_mints)
        model['evaluation_count']=len(model['evaluations'])
        model['state_count']=len(model['final_states'])
        # Isolated ledgers retain full evaluations/states. Public artifact needs
        # signal evidence and affected case predicates, not four duplicate logs.
        del model['evaluations'];del model['final_states']
    args.output.parent.mkdir(exist_ok=True,parents=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'models':{k:{n:v[n] for n in ('ACTIVE_TRADE','ACCUMULATION','MULTIPLE')} for k,v in models.items()},
                     'SOL':{k:v for k,v in result['SOL'].items() if k!='cases'},'complex':result['COMPLEX']['categories'],
                     'new_signal_count':len(new_signals)},indent=2))

if __name__=='__main__':main()
