"""Bounded official read-only endpoint/archive capability receipts."""
import argparse,json,hashlib,time,urllib.request,urllib.error,zipfile,io,csv
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();a.root.mkdir(parents=True,exist_ok=True);out=[]
 checks=[('open_interest','https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT'),('oi_history','https://fapi.binance.com/futures/data/openInterestHist?symbol=BTCUSDT&period=1h&limit=2'),('funding_2021','https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1609459200000&endTime=1609545600000&limit=100'),('taker_ratio','https://fapi.binance.com/futures/data/takerlongshortRatio?symbol=BTCUSDT&period=1h&limit=2'),('global_ratio','https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=1h&limit=2'),('top_account_ratio','https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=BTCUSDT&period=1h&limit=2'),('top_position_ratio','https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol=BTCUSDT&period=1h&limit=2'),('mark_2021','https://fapi.binance.com/fapi/v1/markPriceKlines?symbol=BTCUSDT&interval=1h&startTime=1609459200000&endTime=1609466400000&limit=2'),('index_2021','https://fapi.binance.com/fapi/v1/indexPriceKlines?pair=BTCUSDT&interval=1h&startTime=1609459200000&endTime=1609466400000&limit=2')]
 for label,url in checks:
  rec={'feature':label,'url':url,'observed_epoch':time.time()}
  try:
   with urllib.request.urlopen(url,timeout=20) as f:raw=f.read()
   value=json.loads(raw);(a.root/(label+'.json')).write_bytes(raw);rec.update(status='AVAILABLE',records=len(value) if isinstance(value,list) else 1,sha256=hashlib.sha256(raw).hexdigest())
  except Exception as e:rec.update(status='ACCESS_ERROR',error=type(e).__name__,http_status=getattr(e,'code',None))
  out.append(rec);time.sleep(.5)
 for label,key in [('metrics_2021','data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2021-01-01.zip'),('metrics_2024','data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-2024-01-01.zip'),('funding_archive_2021','data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2021-01.zip'),('mark_archive_2021','data/futures/um/monthly/markPriceKlines/BTCUSDT/1h/BTCUSDT-1h-2021-01.zip'),('index_archive_2021','data/futures/um/monthly/indexPriceKlines/BTCUSDT/1h/BTCUSDT-1h-2021-01.zip')]:
  url='https://data.binance.vision/'+key;rec={'feature':label,'url':url}
  try:
   with urllib.request.urlopen(url,timeout=20) as f:raw=f.read()
   with urllib.request.urlopen(url+'.CHECKSUM',timeout=20) as f:check=f.read()
   assert hashlib.sha256(raw).hexdigest()==check.decode().split()[0]
   with zipfile.ZipFile(io.BytesIO(raw)) as z:rows=list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())))
   (a.root/(label+'.zip')).write_bytes(raw);(a.root/(label+'.CHECKSUM')).write_bytes(check);rec.update(status='CHECKSUM_VALID',rows=len(rows),first_row=rows[0],first_data=rows[1],last_data=rows[-1])
  except Exception as e:rec.update(status='ARCHIVE_ERROR',error=type(e).__name__,http_status=getattr(e,'code',None))
  out.append(rec)
 (a.root/'endpoint-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps([{k:v for k,v in x.items() if k not in ['first_row','first_data','last_data','url']} for x in out]))
if __name__=='__main__':main()
