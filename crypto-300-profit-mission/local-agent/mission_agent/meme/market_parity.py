"""Bounded same-pool independent indexer reads; never a chain parity verdict.

Public service: https://support.coingecko.com/articles/6867086195-does-geckoterminal-have-an-api
Pool schema: https://docs.coingecko.com/reference/pool-address
Only the keyless GeckoTerminal public host is used, never the paid Pro host.
"""
import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from decimal import Decimal,InvalidOperation,localcontext
from .holder_ranks import valid_pubkey

MAX_RESPONSE_BYTES=1024*1024
BASE='https://api.geckoterminal.com/api/v2/networks/solana/pools/'


class NoMarketRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise urllib.error.HTTPError('MARKET_SOURCE',code,'REDIRECT_REJECTED',headers,None)


def _open(request,timeout):
    return urllib.request.build_opener(NoMarketRedirect()).open(request,timeout=timeout)


def number(value):
    if isinstance(value,bool) or value is None or not isinstance(value,(str,int,float,Decimal)):return None
    text=str(value)
    if len(text)>128:return None
    try:
        parsed=Decimal(text)
        if not parsed.is_finite() or parsed<0 or (parsed and abs(parsed.adjusted())>100):return None
        return str(parsed)
    except (InvalidOperation,ValueError,TypeError):return None


class GeckoTerminalMarketClient:
    def __init__(self,*,open_url=_open,clock=time.time,monotonic=time.monotonic):
        self.open_url=open_url;self.clock=clock;self.monotonic=monotonic
    def pool_snapshot(self,mint,pool,quote):
        out={'source':'GECKOTERMINAL_PUBLIC_API','status':'UNAVAILABLE','attempted':False,'observed_at':self.clock()}
        if not all(valid_pubkey(v) for v in (mint,pool,quote)) or mint==quote:
            return {**out,'reason':'IDENTITY_INVALID'}
        out['attempted']=True
        request=urllib.request.Request(BASE+pool,headers={'Accept':'application/json','User-Agent':'mission-meme-research/3'},method='GET')
        try:
            with self.open_url(request,timeout=8) as response:
                if hasattr(response,'read1'):
                    chunks=[];size=0;deadline=self.monotonic()+8
                    while size<=MAX_RESPONSE_BYTES:
                        if self.monotonic()>=deadline:raise TimeoutError('SOURCE_READ_DEADLINE')
                        chunk=response.read1(min(65536,MAX_RESPONSE_BYTES+1-size))
                        if not chunk:break
                        chunks.append(chunk);size+=len(chunk)
                    raw=b''.join(chunks)
                else:raw=response.read(MAX_RESPONSE_BYTES+1)
            if not isinstance(raw,bytes):return {**out,'reason':'NETWORK_OR_RESPONSE_INVALID'}
            out['observed_at']=self.clock()
            if len(raw)>MAX_RESPONSE_BYTES:return {**out,'reason':'RESPONSE_LIMIT'}
            payload=json.loads(raw)
        except urllib.error.HTTPError as exc:return {**out,'reason':'HTTP_'+str(exc.code)}
        except (urllib.error.URLError,OSError,TimeoutError,ValueError,TypeError,RecursionError):return {**out,'reason':'NETWORK_OR_RESPONSE_INVALID'}
        data=payload.get('data') if isinstance(payload,dict) else None
        attrs=data.get('attributes') if isinstance(data,dict) else None
        relations=data.get('relationships') if isinstance(data,dict) else None
        if not isinstance(attrs,dict) or not isinstance(relations,dict) or data.get('id')!='solana_'+pool or data.get('type')!='pool' or attrs.get('address')!=pool:
            return {**out,'reason':'POOL_IDENTITY_MISMATCH'}
        tokens=[]
        for side in ('base_token','quote_token'):
            relation=relations.get(side);token=relation.get('data') if isinstance(relation,dict) else None
            if not isinstance(token,dict) or token.get('type')!='token':return {**out,'reason':'TOKEN_MEMBERSHIP_MISMATCH'}
            tokens.append(token.get('id'))
        if tokens==['solana_'+mint,'solana_'+quote]:price='base_token_price_usd';orientation='BASE'
        elif tokens==['solana_'+quote,'solana_'+mint]:price='quote_token_price_usd';orientation='QUOTE'
        else:return {**out,'reason':'TOKEN_MEMBERSHIP_MISMATCH'}
        return {**out,'status':'OK','pool_address':pool,'mint':mint,'quote_address':quote,
                'target_orientation':orientation,'price_usd':number(attrs.get(price)),
                'pool_liquidity_usd':number(attrs.get('reserve_in_usd')),
                'response_sha256':hashlib.sha256(raw).hexdigest(),
                'provider_asof':'UNVERIFIED'}


def attach_market_comparison(mint,primary,client):
    """Return a new report section. Values stay historical independent readings.

    Retrieval times are not provider observation times. Even identical numbers
    do not establish raw-pool, holder, same-slot, liquidity-lock or tradeability
    parity. Never substitute a different pool after identity failure.
    """
    pair=primary.get('main_pair') or {}
    comparison={'status':'INCOMPLETE_EVIDENCE','metrics':{},'same_chain_snapshot':False,
                'provider_asof':'UNVERIFIED','retrieval_gap_seconds':None}
    verified=(primary.get('status')=='OK' and primary.get('source')=='DEXSCREENER_API'
              and primary.get('mint')==mint and pair.get('base_address')==mint
              and all(valid_pubkey(v) for v in (mint,pair.get('pair_address'),pair.get('quote_address')))
              and pair.get('quote_address')!=mint)
    if not verified:
        independent={'status':'UNAVAILABLE','source':'GECKOTERMINAL_PUBLIC_API','attempted':False,'reason':'PRIMARY_POOL_IDENTITY_UNVERIFIED'}
    else:
        independent=client.pool_snapshot(mint,pair['pair_address'],pair['quote_address'])
    if independent.get('status')=='OK':
        comparison.update({'pool_address':pair['pair_address'],'mint':mint,'quote_address':pair['quote_address']})
        a=primary.get('observed_at');b=independent.get('observed_at')
        if all(type(v) in (float,int) and math.isfinite(v) and v>0 for v in (a,b)):
            comparison['retrieval_gap_seconds']=abs(b-a)
        for name,left,right in [('price_usd',primary.get('price_usd'),independent.get('price_usd')),
                                ('pool_liquidity_usd',pair.get('liquidity_usd'),independent.get('pool_liquidity_usd'))]:
            left=number(left);right=number(right)
            row={'status':'UNAVAILABLE','primary':left,'independent':right,'difference':None,'difference_pct_of_primary':'UNRESOLVED'}
            if left is not None and right is not None:
                with localcontext() as ctx:
                    ctx.prec=400
                    difference=Decimal(right)-Decimal(left)
                    row.update(status='COMPARED',difference=str(difference))
                    if Decimal(left)>0:row['difference_pct_of_primary']=str((difference*100/Decimal(left)).quantize(Decimal('0.0001')))
            comparison['metrics'][name]=row
        comparison['status']='INDEXER_SNAPSHOTS_COMPARED' if all(r['status']=='COMPARED' for r in comparison['metrics'].values()) else 'PARTIAL_INDEXER_SNAPSHOTS'
    return {**primary,'independent_market':independent,'comparison':comparison}
