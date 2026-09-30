"""Explicit official-source network smoke. No trading/auth/private user endpoints."""
import asyncio,json,urllib.request,time
from datetime import datetime,timezone
from pathlib import Path
from websockets.asyncio.client import connect

async def main(root):
 root.mkdir(parents=True,exist_ok=True,mode=0o700)
 result={'checked_at':datetime.now(timezone.utc).isoformat(),'sources':{}}
 for name,url,subscriptions in [
  ('binance','wss://data-stream.binance.vision/stream',[{'method':'SUBSCRIBE','params':[a+'usdt@kline_1m' for a in ['btc','eth','sol','bnb']],'id':1}]),
  ('hyperliquid','wss://api.hyperliquid.xyz/ws',[{'method':'subscribe','subscription':{'type':'candle','coin':'HYPE','interval':'1m'}},{'method':'subscribe','subscription':{'type':'trades','coin':'HYPE'}}])]:
  start=time.monotonic();frames=[]
  try:
   async with connect(url,open_timeout=20,ping_interval=20,ping_timeout=20,proxy=None) as ws:
    for sub in subscriptions:await ws.send(json.dumps(sub))
    deadline=time.monotonic()+12
    while time.monotonic()<deadline:
     try:frames.append(json.loads(await asyncio.wait_for(ws.recv(),3)))
     except asyncio.TimeoutError:continue
   (root/(name+'-probe-raw.json')).write_text(json.dumps(frames));(root/(name+'-probe-raw.json')).chmod(0o600)
   data=[f for f in frames if f.get('data',f).get('e')=='kline'] if name=='binance' else [f for f in frames if f.get('channel')=='candle']
   result['sources'][name]={'endpoint':url,'connected':True,'frames':len(frames),'market_frames':len(data),'duration_seconds':round(time.monotonic()-start,3),'channels':sorted({(f.get('channel') or (f.get('data',f).get('e','ack') if isinstance(f.get('data',f),dict) else 'data')) for f in frames}),'status':'PASS' if data else 'NO_MARKET_DATA'}
  except Exception as e:result['sources'][name]={'endpoint':url,'status':'FAILED','error':type(e).__name__}
 (root/'source-probe.json').write_text(json.dumps(result));(root/'source-probe.json').chmod(0o600);print(json.dumps(result))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();asyncio.run(main(a.root))
