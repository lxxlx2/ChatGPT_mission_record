import json,time,urllib.request,urllib.error,urllib.parse
from decimal import Decimal
from ..bar import Bar,dec,MINUTE
BINANCE_REST='https://data-api.binance.vision/api/v3/klines'
BINANCE_WS='wss://data-stream.binance.vision/stream'
HYPE_REST='https://api.hyperliquid.xyz/info'
HYPE_WS='wss://api.hyperliquid.xyz/ws'

class Official:
 def __init__(self,request=urllib.request.urlopen,sleep=time.sleep):self.request=request;self.sleep=sleep;self.calls=self.rx=self.tx=0
 def get(self,url,payload=None):
  if not (url.startswith(BINANCE_REST+'?') or url==HYPE_REST or url=='https://data-api.binance.vision/api/v3/time'):raise ValueError('source endpoint not allowlisted')
  raw=json.dumps(payload).encode() if payload else None
  for attempt in range(3):
   self.calls+=1;self.tx+=len(raw or b'')
   try:
    with self.request(urllib.request.Request(url,data=raw,headers={'Content-Type':'application/json'}),timeout=20) as response:
     data=response.read();self.rx+=len(data);return json.loads(data,parse_float=Decimal)
   except urllib.error.HTTPError as error:
    if error.code!=429 or attempt==2:raise
    wait=float(error.headers.get('Retry-After','1'))
    if wait>30:raise
    self.sleep(max(1,wait))
   except (TimeoutError,urllib.error.URLError):
    if attempt==2:raise
    self.sleep(2**attempt)
 def history(self,asset,start,end):
  if asset=='HYPE':return self.get(HYPE_REST,{'type':'candleSnapshot','req':{'coin':'HYPE','interval':'1m','startTime':start,'endTime':end-1}})
  rows=[];cursor=start
  while cursor<end:
   page=self.get(BINANCE_REST+'?'+urllib.parse.urlencode({'symbol':asset+'USDT','interval':'1m','startTime':cursor,'endTime':end-1,'limit':1000}))
   if not isinstance(page,list):raise ValueError('invalid historical response')
   if not page:break
   if page[-1][0]<cursor:raise ValueError('nonadvancing historical cursor')
   rows.extend(page);cursor=page[-1][0]+MINUTE;self.sleep(.05)
  return rows

def parse_rest(asset,row,received):
 if asset=='HYPE':
  return Bar(asset,'hyperliquid_perp',row['s'],int(row['t']),*[dec(row[k]) for k in ('o','h','l','c','v')],trade_count=int(row['n']),is_closed=int(row['t'])+MINUTE<=received,source_event_time=int(row['T']),received_at=received)
 return Bar(asset,'binance_spot',asset+'USDT',int(row[0]),*[dec(row[i]) for i in range(1,6)],quote_volume=dec(row[7]),trade_count=int(row[8]),is_closed=int(row[0])+MINUTE<=received,source_event_time=int(row[6]),received_at=received)

def parse_ws(frame,received):
 data=frame.get('data',frame)
 if frame.get('channel')=='candle':
  rows=data if isinstance(data,list) else [data]
  return [Bar('HYPE','hyperliquid_perp',r['s'],int(r['t']),*[dec(r[k]) for k in ('o','h','l','c','v')],trade_count=int(r['n']),is_closed=False,source_event_time=int(r['T']),received_at=received) for r in rows]
 if isinstance(data,dict) and data.get('e')=='kline':
  k=data['k'];asset=k['s'].removesuffix('USDT')
  return [Bar(asset,'binance_spot',k['s'],int(k['t']),*[dec(k[key]) for key in ('o','h','l','c','v')],quote_volume=dec(k['q']),trade_count=int(k['n']),is_closed=bool(k['x']),source_event_time=int(data['E']),received_at=received)]
 return []
