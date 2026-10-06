"""Capture raw official Jupiter quote responses for review fixtures.

Read-only: GET /swap/v1/quote only. No wallet, transaction build, signing or send.
API key is read from JUPITER_API_KEY and never written to disk.
"""
from __future__ import annotations

import argparse,hashlib,json,os,time,urllib.error,urllib.parse,urllib.request
from decimal import Decimal,InvalidOperation
from pathlib import Path

USDC='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
ENDPOINT='https://api.jup.ag/swap/v1/quote'


def usdc_raw(value)->str:
    try:amount=Decimal(str(value))*Decimal(10**6)
    except (InvalidOperation,ValueError,TypeError):raise ValueError('INVALID_USDC_AMOUNT')
    integral=amount.to_integral_value()
    if amount<=0 or amount!=integral:raise ValueError('USDC_AMOUNT_REQUIRES_AT_MOST_6_DECIMALS')
    return str(int(integral))


def capture(name,mint,decimals,api_key,amount_usdc='30',slippage_bps=100):
    params={'inputMint':USDC,'outputMint':mint,'amount':usdc_raw(amount_usdc),'slippageBps':str(slippage_bps),'instructionVersion':'V2'}
    url=ENDPOINT+'?'+urllib.parse.urlencode(params);request=urllib.request.Request(url,headers={'x-api-key':api_key,'User-Agent':'mission-meme-v1/fixture-capture'})
    status=None
    try:
        with urllib.request.urlopen(request,timeout=10) as response:status=getattr(response,'status',200);raw=response.read()
    except urllib.error.HTTPError as exc:
        status=exc.code;raw=exc.read()
    try:body=json.loads(raw.decode())
    except (UnicodeDecodeError,ValueError):body={'_raw_text':raw.decode(errors='replace')}
    record={'schema_version':1,'case':name,'captured_at':time.time(),'source':'JUPITER_OFFICIAL','endpoint':ENDPOINT,'request':params,'token_decimals':int(decimals),'http_status':status,'response':body}
    encoded=json.dumps(record,sort_keys=True,separators=(',',':')).encode();record['fixture_sha256']=hashlib.sha256(encoded).hexdigest();return record


def main():
    p=argparse.ArgumentParser();p.add_argument('--case',action='append',required=True,help='NAME:MINT:DECIMALS');p.add_argument('--out',type=Path,required=True);p.add_argument('--amount-usdc',default='30');p.add_argument('--slippage-bps',type=int,default=100);a=p.parse_args()
    key=os.environ.get('JUPITER_API_KEY')
    if not key:raise SystemExit('JUPITER_API_KEY_REQUIRED')
    specs=[];names=set()
    for spec in a.case:
        name,mint,decimals=spec.split(':',2)
        if name in names:raise SystemExit('DUPLICATE_CASE:'+name)
        names.add(name);specs.append((name,mint,int(decimals)))
    # Preflight every destination before the first network call. A partial run must
    # never overwrite an immutable fixture or discover a conflict after requests.
    existing=[str(a.out/(name+'.json')) for name,_,__ in specs if (a.out/(name+'.json')).exists()]
    if (a.out/'manifest.json').exists():existing.append(str(a.out/'manifest.json'))
    if existing:raise SystemExit('FIXTURE_ALREADY_EXISTS:'+','.join(existing))
    usdc_raw(a.amount_usdc)
    a.out.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for name,mint,decimals in specs:
        record=capture(name,mint,decimals,key,a.amount_usdc,a.slippage_bps);path=a.out/(name+'.json')
        path.write_text(json.dumps(record,indent=2,sort_keys=True));manifest.append({'case':name,'file':path.name,'sha256':record['fixture_sha256'],'http_status':record['http_status']})
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True));print(json.dumps(manifest,sort_keys=True))

if __name__=='__main__':main()
