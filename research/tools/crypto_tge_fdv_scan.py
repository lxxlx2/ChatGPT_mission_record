#!/usr/bin/env python3
"""One-shot, READ-ONLY TGE/FDV venue market audit. No orders, no schedules, no secrets on disk.

Sources: Polymarket Gamma+CLOB, Kalshi public API, Myriad public markets,
Predict.fun and OPINION keyed market APIs, Limitless active markets API.

Real-time completeness is explicitly measured. One failed venue => NOT exhaustive.
Outputs JSON and CSV; no trade execution and no API credentials in saved artifacts.
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

try:
    import requests
except ImportError as exc:
    raise SystemExit('Install requests: python -m pip install requests') from exc

UTC = dt.timezone.utc
TERMS = re.compile(r'\b(?:fdv|fully\s*diluted|token\s*(?:launch|generation|issuance)|launch\s+(?:a\s+)?token|tge|token\s+by|listing\s+after\s+(?:tge|launch)|listed\s+(?:on|within).*tge|airdrop|governance\s+token)\b', re.I)
KNOWN = {
    'printr': 'OFFICIAL_TOKEN_CANCELLATION',
    'standx': 'OFFICIAL_TOKEN_CANCELLATION',
    'ventuals': 'OFFICIAL_TOKEN_CANCELLATION',
    'abstract': 'OFFICIAL_SUNSET',
    'linera': 'OFFICIAL_SHUTDOWN_POSSIBLE_REVIVAL',
    'neutrl': 'INCIDENT_TOKEN_CANCEL_UNVERIFIED',
}


def d(x, default='0'):
    try:
        return Decimal(str(x)) if x is not None else Decimal(default)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def num(x):
    return float(x) if x is not None else None


def match_text(row):
    return bool(TERMS.search(' '.join(str(row.get(k, '') or '') for k in ('title', 'question', 'description', 'slug', 'event_title'))))


def issuer_status(row):
    s = ' '.join(str(row.get(k, '') or '') for k in ('title', 'question', 'slug', 'event_title')).lower()
    hits = [v for k, v in KNOWN.items() if re.search(r'(?<![a-z])' + re.escape(k) + r'(?![a-z])', s)]
    return hits[0] if hits else 'REQUIRES_OFFICIAL_VERIFICATION'


def order_levels(book, key='asks'):
    """Parse CLOB [price,size] or {price,size} levels, price in dollars, shares as size."""
    out = []
    for level in book.get(key, []):
        if isinstance(level, dict):
            p, q = level.get('price'), level.get('size', level.get('amount'))
        elif isinstance(level, (list, tuple)) and len(level) >= 2:
            p, q = level[:2]
        else:
            continue
        pp, qq = d(p), d(q)
        if Decimal(0) < pp < Decimal(1) and qq > 0:
            out.append((pp, qq))
    return sorted(out, key=lambda x: x[0])


def fill_budget(asks, budget):
    """Return None when requested capital is not fully fillable; never extrapolate depth."""
    original = d(budget)
    remaining, spent, shares = original, Decimal(0), Decimal(0)
    for p, q in sorted(asks, key=lambda x: x[0]):
        amount = min(q, remaining / p)
        spent += p * amount
        shares += amount
        remaining -= p * amount
        if remaining < Decimal('0.0000001'):
            return {'budget':num(original), 'fully_fillable':True,
                    'shares':num(shares), 'vwap':num(spent / shares),
                    'gross_profit_if_no':num(shares-spent),
                    'gross_roi_if_no':num(shares / spent-1)}
    return {'budget':num(original), 'fully_fillable':False,
            'fillable_spend':num(spent), 'fillable_shares':num(shares),
            'vwap_partial':num(spent/shares) if shares else None}


class APIError(Exception):
    pass


class Reader:
    def __init__(self, timeout=12, retries=2, pause=.12):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent':'MissionResearch/1.0 (+read-only; tge-fdv-audit)'})
        self.timeout, self.retries, self.pause = timeout, retries, pause
        self.request_count = 0

    def get(self, base, params=None, headers=None):
        for attempt in range(self.retries + 1):
            self.request_count += 1
            try:
                resp = self.session.get(base,params=params,headers=headers,timeout=self.timeout)
                if resp.status_code in (429,500,502,503,504) and attempt < self.retries:
                    time.sleep(max(self.pause, min(float(resp.headers.get('Retry-After','1') or '1'),4)))
                    continue
                if resp.status_code != 200:
                    raise APIError(f'HTTP_{resp.status_code} {base}')
                time.sleep(self.pause)
                return resp.json()
            except (requests.RequestException,ValueError) as e:
                if attempt >= self.retries:
                    raise APIError(f'{type(e).__name__} {base}: {str(e)[:110]}') from e
                time.sleep(self.pause)
        raise APIError(f'Failed {base}')


def page_result(name, completed, pages, seen, matched, error=None):
    return {'venue': name, 'enumeration_completed': bool(completed),
            'pages_read': pages, 'raw_rows': seen, 'relevant_rows': matched,
            'error':error}


def row(venue, event, question, slug, market_id, end, volume, liquidity,
        market_link=None, yes_id=None, no_id=None, raw_rule='', book=None):
    r = {'venue':venue, 'event_title':event, 'question':question,
         'title':question or event, 'slug':slug, 'market_id':str(market_id),
         'end_date':str(end or ''), 'historical_volume':num(d(volume)),
         'displayed_liquidity':num(d(liquidity)), 'url':market_link or '',
         'raw_rule':(raw_rule or '')[:5000], 'yes_token':str(yes_id or ''),
         'no_token':str(no_id or ''), 'book_checked': False,
         'orderbook_error': None, 'best_no_ask':None,
         'available_no_ask_spend':None, 'no_depth':None,
         'issuer_status':None}
    r['issuer_status'] = issuer_status(r)
    return r


def apply_book(r, book, budgets):
    asks=order_levels(book)
    r['book_checked']=True
    r['best_no_ask']=num(asks[0][0]) if asks else None
    r['available_no_ask_spend']=num(sum((p*q for p,q in asks),Decimal(0)))
    r['no_depth']={str(x):fill_budget(asks,x) for x in budgets}


def polymarket(client, max_pages, page_size):
    result=[]; seen=0; pages=0; seen_ids=set(); error=None; completed=False
    for page in range(max_pages):
        try:
            events=client.get('https://gamma-api.polymarket.com/events',
                              {'limit':page_size,'offset':page*page_size,'active':'true','closed':'false'})
            if not isinstance(events,list): raise APIError('Invalid Gamma event list schema')
        except APIError as e:
            error=str(e);break
        pages+=1;seen+=len(events)
        for e in events:
            for m in e.get('markets') or []:
                if m.get('closed') is True or m.get('active') is False:continue
                combined={'event_title':e.get('title'),'title':m.get('question'),'question':m.get('question'),
                          'description':(e.get('description') or '')+' '+(m.get('description') or ''),
                          'slug':e.get('slug')}
                if not match_text(combined):continue
                ident=str(m.get('id') or m.get('conditionId'))
                if ident in seen_ids:continue
                seen_ids.add(ident)
                tokens=m.get('clobTokenIds') or []
                if isinstance(tokens,str):
                    try:tokens=json.loads(tokens)
                    except json.JSONDecodeError:tokens=[]
                if not isinstance(tokens,list):tokens=[]
                outcome=m.get('outcomes') or ['Yes','No']
                if isinstance(outcome,str):
                    try:outcome=json.loads(outcome)
                    except json.JSONDecodeError:outcome=['Yes','No']
                yes=no=None
                for idx,x in enumerate(outcome):
                    if idx < len(tokens):
                        if str(x).lower()=='yes':yes=tokens[idx]
                        if str(x).lower()=='no':no=tokens[idx]
                result.append(row('Polymarket',e.get('title'),m.get('question'),e.get('slug'),ident,
                         m.get('endDate') or e.get('endDate'),m.get('volumeNum'),m.get('liquidityNum'),
                         'https://polymarket.com/event/'+str(e.get('slug')),yes,no,
                         m.get('description') or e.get('description') or ''))
        if len(events) < page_size:completed=True;break
    if not completed and not error:error='MAX_PAGES_REACHED'
    return result,page_result('Polymarket',completed,pages,seen,len(result),error)


def kalshi(client, max_pages):
    rows=[];seen=0;pages=0;cursor='';error=None;complete=False;visited=set()
    for _ in range(max_pages):
        params={'status':'open','limit':200}
        if cursor:params['cursor']=cursor
        try:
            data=client.get('https://api.elections.kalshi.com/trade-api/v2/markets',params)
            markets=data['markets']
            if not isinstance(markets,list):raise APIError('Invalid Kalshi markets schema')
        except (APIError,KeyError,TypeError) as e:error=str(e);break
        pages+=1;seen+=len(markets)
        for m in markets:
            combined={'title':m.get('title'),'question':m.get('subtitle'),
                      'description':str(m.get('rules_primary',''))+' '+str(m.get('rules_secondary','')),
                      'slug':m.get('event_ticker','')}
            if not match_text(combined):continue
            ticker=m.get('ticker');
            rows.append(row('Kalshi',m.get('event_ticker'),m.get('title'),ticker,ticker,
                 m.get('close_time') or m.get('expected_expiration_time'),m.get('volume_fp',0),0,
                 'https://kalshi.com/markets/'+str(ticker),raw_rule=combined['description']))
        nxt=data.get('cursor')
        if not nxt:complete=True;break
        if nxt in visited:error='REPEATED_CURSOR';break
        visited.add(nxt);cursor=nxt
    if not complete and not error:error='MAX_PAGES_REACHED'
    return rows,page_result('Kalshi',complete,pages,seen,len(rows),error)


def myriad(client, max_pages):
    rows=[];seen=0;pages=0;error=None;complete=False
    for i in range(1,max_pages+1):
        try:
            data=client.get('https://api-v2.myriadprotocol.com/markets',
                {'page':i,'limit':100,'state':'open','trading_model':'all'})
            markets=data['data'];p=data.get('pagination',{})
            if not isinstance(markets,list):raise APIError('Invalid Myriad schema')
        except (APIError,KeyError,TypeError) as e:error=str(e);break
        pages+=1;seen+=len(markets)
        for m in markets:
            combined={'title':m.get('title'),'description':m.get('description'),'slug':m.get('slug')}
            if not match_text(combined):continue
            rows.append(row('Myriad',m.get('title'),m.get('title'),m.get('slug'),m.get('id'),
                m.get('expiresAt') or m.get('expires_at'),m.get('volume'),m.get('liquidity'),
                'https://myriad.markets/markets/'+str(m.get('slug')),raw_rule=m.get('description')))
        if p.get('hasNext') is False or (not p and len(markets)<100):complete=True;break
    if not complete and not error:error='MAX_PAGES_REACHED'
    return rows,page_result('Myriad',complete,pages,seen,len(rows),error)


def predict(client,max_pages):
    key=os.getenv('PREDICT_API_KEY')
    if not key:return [],page_result('Predict.fun',False,0,0,0,'API_KEY_REQUIRED (PREDICT_API_KEY)')
    rows=[];seen=0;pages=0;cursor=None;error=None;complete=False;visited=set()
    for _ in range(max_pages):
        params={'first':100}
        if cursor:params['after']=cursor
        try:
            data=client.get('https://api.predict.fun/v1/markets',params,{'x-api-key':key})
            markets=data['data']
            if not isinstance(markets,list):raise APIError('Invalid Predict markets schema')
        except (APIError,KeyError,TypeError) as e:error=str(e);break
        pages+=1;seen+=len(markets)
        for m in markets:
            combined={'title':m.get('title'),'question':m.get('question'),
                      'description':m.get('description'),'slug':m.get('seriesSlug')}
            if not match_text(combined):continue
            mid=m.get('id')
            rows.append(row('Predict.fun',m.get('title'),m.get('question'),m.get('seriesSlug'),mid,
                '',(m.get('stats') or {}).get('volumeTotalUsd',0),
                (m.get('stats') or {}).get('totalLiquidityUsd',0),
                'https://predict.fun/market/'+str(m.get('seriesSlug') or mid),raw_rule=m.get('description')))
        nxt=data.get('cursor')
        if not nxt:complete=True;break
        if nxt in visited:error='REPEATED_CURSOR';break
        visited.add(nxt);cursor=nxt
    if not complete and not error:error='MAX_PAGES_REACHED'
    return rows,page_result('Predict.fun',complete,pages,seen,len(rows),error)


def opinion(client,max_pages):
    key=os.getenv('OPINION_API_KEY')
    if not key:return [],page_result('OPINION',False,0,0,0,'API_KEY_REQUIRED (OPINION_API_KEY)')
    rows=[];seen=0;pages=0;error=None;complete=False
    for i in range(1,max_pages+1):
        try:
            data=client.get('https://openapi.opinion.trade/openapi/market',
                {'page':i,'limit':20,'status':'activated','marketType':2}, {'apikey':key})
            datum=data.get('result',data.get('data',{}))
            markets=datum.get('list',datum.get('items',datum)) if isinstance(datum,dict) else datum
            if not isinstance(markets,list):raise APIError('Unrecognized OPINION list response; no data accepted')
        except (APIError,ValueError,KeyError,TypeError) as e:error=str(e);break
        pages+=1;seen+=len(markets)
        for m in markets:
            combined={'title':m.get('marketTitle') or m.get('title'),
                      'description':m.get('rules'),'slug':m.get('marketId')}
            if not match_text(combined):continue
            mid=m.get('marketId')
            rows.append(row('OPINION',combined['title'],combined['title'],mid,mid,
                m.get('endTime'),m.get('volume'),m.get('liquidity'),
                'https://app.opinion.trade/market/'+str(mid),
                yes_id=m.get('yesTokenId'),no_id=m.get('noTokenId'),raw_rule=m.get('rules')))
        if len(markets)<20:complete=True;break
    if not complete and not error:error='MAX_PAGES_REACHED'
    return rows,page_result('OPINION',complete,pages,seen,len(rows),error)


def limitless(client,max_pages):
    rows=[];seen=0;pages=0;error=None;complete=False
    for i in range(1,max_pages+1):
        try:
            data=client.get('https://api.limitless.exchange/markets/active',{'limit':100,'page':i})
            markets=data.get('data')
            if not isinstance(markets,list):raise APIError('Unrecognized Limitless markets schema')
        except (APIError,ValueError,TypeError) as e:error=str(e);break
        pages+=1;seen+=len(markets)
        for m in markets:
            combined={'title':m.get('title'),'description':m.get('description'),'slug':m.get('slug')}
            if not match_text(combined):continue
            rows.append(row('Limitless',m.get('title'),m.get('title'),m.get('slug'),m.get('id'),
                m.get('resolutionDate'),m.get('volume24h'),m.get('liquidity'),
                'https://limitless.exchange/markets/'+str(m.get('slug')),raw_rule=m.get('description')))
        total=int(data.get('totalMarketsCount') or 0)
        if len(markets)<100 or (total and seen>=total):complete=True;break
    if not complete and not error:error='MAX_PAGES_REACHED'
    return rows,page_result('Limitless',complete,pages,seen,len(rows),error)


def enrich_orderbooks(client,rows,budgets,max_books):
    """Fetch only known high-priority issuer statuses. 403/404/429 remain errors, never zeros."""
    interesting=[r for r in rows if r['issuer_status'] in {'OFFICIAL_TOKEN_CANCELLATION','OFFICIAL_SUNSET','OFFICIAL_SHUTDOWN_POSSIBLE_REVIVAL'}]
    visited=0
    for r in interesting:
        if visited>=max_books:r['orderbook_error']='MAX_BOOKS_REACHED';continue
        if r['venue']=='Polymarket':
            if not r['no_token']:r['orderbook_error']='NO_TOKEN_ID_UNAVAILABLE';continue
            url='https://clob.polymarket.com/book';params={'token_id':r['no_token']};headers={}
        elif r['venue']=='OPINION':
            if not r['no_token']:r['orderbook_error']='NO_TOKEN_ID_UNAVAILABLE';continue
            url='https://openapi.opinion.trade/openapi/token/orderbook';params={'token_id':r['no_token']};headers={'apikey':os.getenv('OPINION_API_KEY','')}
        elif r['venue']=='Predict.fun':
            # Predict keeps a YES-referenced book; its bids imply NO asks at 1 - YES bid.
            url='https://api.predict.fun/v1/markets/'+str(r['market_id'])+'/orderbook';params={};headers={'x-api-key':os.getenv('PREDICT_API_KEY','')}
        elif r['venue']=='Limitless':
            url='https://api.limitless.exchange/markets/'+str(r['slug'])+'/orderbook';params={};headers={}
        else:
            r['orderbook_error']='ORDERBOOK_ADAPTER_REQUIRES_OUTCOME_MAPPING';continue
        visited+=1
        try:
            data=client.get(url,params,headers)
            book=data.get('data',data)
            if r['venue']=='Predict.fun':
                bids=book.get('bids') or []
                book={'asks':[(str(Decimal(1)-d(v[0])),v[1]) for v in bids if isinstance(v,(list,tuple)) and len(v)>=2]}
            elif r['venue']=='Limitless':
                # A generic Limitless book is YES-referenced unless the market response explicitly says outcome=No.
                r['orderbook_error']='OUTCOME_MAPPING_UNVERIFIED';continue
            elif r['venue']=='OPINION' and 'result' in book:
                book=book['result'].get('data',book['result'])
            if not isinstance(book,dict):raise APIError('Invalid orderbook schema')
            apply_book(r,book,budgets)
        except (APIError,KeyError,TypeError,ValueError) as e:
            r['orderbook_error']=str(e)[:200]
    return visited


def write_outputs(outdir,rows,coverage,summary):
    outdir.mkdir(parents=True,exist_ok=True)
    obj={'summary':summary,'coverage':coverage,'markets':rows}
    (outdir/'audit.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    columns=['venue','event_title','question','slug','market_id','end_date','url','historical_volume',
             'displayed_liquidity','issuer_status','book_checked','orderbook_error','best_no_ask',
             'available_no_ask_spend','no_depth','raw_rule']
    with (outdir/'markets.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader()
        for r in rows:
            drow={k:(json.dumps(r.get(k),ensure_ascii=False) if isinstance(r.get(k),dict) else r.get(k)) for k in columns}
            w.writerow(drow)
    with (outdir/'coverage.json').open('w',encoding='utf-8') as f:
        json.dump({'summary':summary,'coverage':coverage},f,ensure_ascii=False,indent=2)


def main():
    a=argparse.ArgumentParser(description='One-shot read-only multi-PM TGE/FDV market audit')
    a.add_argument('--out',default='tge-fdv-scan-output')
    a.add_argument('--max-pages',type=int,default=2000,help='Safety cap, truncation => incomplete')
    a.add_argument('--max-books',type=int,default=600)
    a.add_argument('--max-venues',nargs='*',default=['polymarket','kalshi','myriad','predict','opinion','limitless'])
    a.add_argument('--budgets',nargs='+',type=int,default=[100,500,1000])
    a.add_argument('--timeout',type=int,default=10)
    args=a.parse_args()
    adapters={'polymarket':lambda c:polymarket(c,args.max_pages,500),'kalshi':lambda c:kalshi(c,args.max_pages),
              'myriad':lambda c:myriad(c,args.max_pages),'predict':lambda c:predict(c,args.max_pages),
              'opinion':lambda c:opinion(c,args.max_pages),'limitless':lambda c:limitless(c,args.max_pages)}
    client=Reader(timeout=args.timeout)
    rows,coverage=[],[]
    for venue in args.max_venues:
        if venue not in adapters:
            raise SystemExit('Unknown venue: '+venue)
        try:
            rr, cc=adapters[venue](client)
            rows.extend(rr);coverage.append(cc)
        except Exception as e:
            coverage.append(page_result(venue,False,0,0,0,f'ADAPTER_EXCEPTION {type(e).__name__}: {str(e)[:120]}'))
    checked=enrich_orderbooks(client,rows,args.budgets,args.max_books)
    completeness=all(v['enumeration_completed'] for v in coverage) and len(coverage)==6
    summary={'run_at_utc':dt.datetime.now(UTC).isoformat(), 'read_only':True,
             'configured_venues':args.max_venues,'all_6_venues_complete':completeness,
             'total_relevant_contracts':len(rows),'book_attempts':checked,
             'verified_usable_books':sum(1 for r in rows if r['book_checked'] and r['best_no_ask'] is not None),
             'by_venue':dict(Counter(r['venue'] for r in rows)),
             'by_issuer_status':dict(Counter(r['issuer_status'] for r in rows)),
             'warnings':['A market catalog is not independently verified issuer cancellation.',
                         'Historical volume and displayed liquidity are NOT executable No size.',
                         'Never trade from stale or partial data; fees/collateral/oracle risk unpriced.']}
    write_outputs(Path(args.out),rows,coverage,summary)
    print(json.dumps({'summary':summary,'coverage':coverage},indent=2,ensure_ascii=False))
    if not completeness:sys.exit(2)


if __name__=='__main__':main()