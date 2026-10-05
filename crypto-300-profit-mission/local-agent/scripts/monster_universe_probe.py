"""Read-only M1 source inventory; no anomaly judgment or survivor-only backtest."""
import argparse,json,time,xml.etree.ElementTree as ET,urllib.request,urllib.parse
from pathlib import Path
from mission_agent.monster.source import BinanceSource,ENDPOINTS,universe
from scripts.frank_probe import store

def run(root):
    root.mkdir(exist_ok=True,parents=True,mode=0o700);api=BinanceSource();summary={}
    for kind in ('spot_universe','futures_universe','alpha_universe','alpha_tokens'):
        path=root/(kind+'.json')
        try:
            value=api.get(kind);store(path,value)
            rows=universe(value,kind.split('_')[0]) if kind!='alpha_tokens' else value.get('data',[])
            summary[kind]={'status':'AVAILABLE','rows':len(rows),'active':sum(x.get('status')=='TRADING' for x in rows),'source':ENDPOINTS[kind]}
        except Exception as e:summary[kind]={'status':'UNAVAILABLE','error':type(e).__name__,'http_status':getattr(e,'code',None),'source':ENDPOINTS[kind]}
    # Official public-data bucket directory inventory, not market data from an explorer.
    for market,prefix in [('spot','data/spot/monthly/klines/'),('futures','data/futures/um/monthly/klines/')]:
        url='https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?'+urllib.parse.urlencode({'delimiter':'/','prefix':prefix})
        try:
            with urllib.request.urlopen(url,timeout=20) as response:raw=response.read()
            doc=ET.fromstring(raw);ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
            names=[x.text[len(prefix):].strip('/') for x in doc.findall('s:CommonPrefixes/s:Prefix',ns)]
            truncated=doc.findtext('s:IsTruncated',namespaces=ns)=='true'
            with (root/(market+'-historical-directory.xml')).open('xb') as f:f.write(raw)
            summary[market+'_historical']={'symbols':names,'count':len(names),'listing_truncated':truncated,'source':url}
        except Exception as e:summary[market+'_historical']={'status':'UNAVAILABLE','error':type(e).__name__,'http_status':getattr(e,'code',None),'source':url}
    summary['survivor_bias_status']='SURVIVOR_BIAS_LIMITATION';summary['delisted_available_bars']='NOT_PROBED';summary['delisted_unavailable_bars']='NOT_PROBED';summary['calls']=api.calls
    store(root/'universe-summary.json',summary);print(json.dumps({k:{a:b for a,b in v.items() if a!='symbols'} if isinstance(v,dict) else v for k,v in summary.items()}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
