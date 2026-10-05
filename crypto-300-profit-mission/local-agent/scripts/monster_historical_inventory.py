"""Complete paginated official archive directory inventory, including inactive symbols."""
import argparse,json,urllib.request,urllib.parse,xml.etree.ElementTree as ET
from pathlib import Path
from scripts.frank_probe import store

def run(root):
    result={}
    for market,prefix in [('spot','data/spot/monthly/klines/'),('futures','data/futures/um/monthly/klines/')]:
        names=[];marker=None;pages=0
        while True:
            query={'delimiter':'/','prefix':prefix}
            if marker:query['marker']=marker
            url='https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?'+urllib.parse.urlencode(query)
            path=root/f'{market}-directory-page-{pages:03d}.xml'
            if path.exists():raw=path.read_bytes()
            else:
                with urllib.request.urlopen(url,timeout=20) as response:raw=response.read()
                with path.open('xb') as f:f.write(raw)
            doc=ET.fromstring(raw);ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
            prefixes=[x.text for x in doc.findall('s:CommonPrefixes/s:Prefix',ns)];names.extend(x[len(prefix):].strip('/') for x in prefixes);pages+=1
            if doc.findtext('s:IsTruncated',namespaces=ns)!='true':break
            nxt=doc.findtext('s:NextMarker',namespaces=ns) or (prefixes[-1] if prefixes else None)
            if not nxt or nxt==marker or pages>=20:raise ValueError('HISTORICAL_INVENTORY_PAGINATION_FAILED')
            marker=nxt
        current=json.loads((root/(market+'_universe.json')).read_text())['symbols'];active={s['symbol'] for s in current if s['status']=='TRADING'}
        historical=set(names);inactive=historical-active
        result[market]={'historical_symbols':len(historical),'pages':pages,'inventory_complete':True,'current_active_symbols':len(active),'historical_not_current_active':len(inactive),'inactive_archive_symbols':sorted(inactive),'all_historical_symbols':sorted(historical),'delisted_semantics':'Historical not active includes removed pairs, quote changes, inactive contracts; not proven delisted token identities. Raw archive availability does not yet prove candle completeness.'}
    store(root/'historical-universe-complete.json',result);print(json.dumps({k:{a:b for a,b in v.items() if not isinstance(b,list)} for k,v in result.items()}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
