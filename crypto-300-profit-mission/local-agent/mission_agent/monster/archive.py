"""Checksum-verified, immutable official Binance 1h archives for frozen GT V1."""
import csv,math,hashlib,io,json,time,urllib.request,urllib.parse,urllib.error,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
from ..frank.archive import publish
S3='https://s3-ap-northeast-1.amazonaws.com/data.binance.vision'
BASE='https://data.binance.vision/'
NS={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
HOUR=3600000

def fetch(url):
    parts=urllib.parse.urlsplit(url)
    url=urllib.parse.urlunsplit((parts.scheme,parts.netloc,urllib.parse.quote(parts.path,safe='/%'),parts.query,parts.fragment))
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'crypto-monitor-shadow-archive/1'}),timeout=25) as r:return r.read()
        except urllib.error.HTTPError as e:
            if e.code==404:raise
            if e.code not in (429,500,502,503,504) or attempt==2:raise
        except (TimeoutError,urllib.error.URLError):
            if attempt==2:raise
        time.sleep(2**attempt)

def list_keys(prefix):
    keys=[];marker='';pages=[]
    while True:
        raw=fetch(S3+'?'+urllib.parse.urlencode({'prefix':prefix,'max-keys':1000,'marker':marker}))
        pages.append(raw);root=ET.fromstring(raw)
        page=[x.text for x in root.findall('s:Contents/s:Key',NS)];keys.extend(page)
        if root.findtext('s:IsTruncated',namespaces=NS)=='false':return keys,pages
        if not page:raise ValueError('TRUNCATED_EMPTY_ARCHIVE_LIST')
        marker=page[-1]

def parse_zip(raw,interval_ms=HOUR):
    if interval_ms not in (HOUR,300000,60000):raise ValueError('ARCHIVE_INTERVAL_NOT_ALLOWED')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        if len(names)!=1 or not names[0].endswith('.csv'):raise ValueError('ARCHIVE_MEMBER_INVALID')
        rows=csv.reader(io.StringIO(z.read(names[0]).decode('utf-8-sig')));bars=[]
        for row in rows:
            if row[0] in ('open_time','Open time'):continue
            t=int(row[0]);t=t//1000 if t>10**14 else t
            o,h,l,c,v,q=map(float,[row[1],row[2],row[3],row[4],row[5],row[7]]);trades=int(row[8])
            if not all(math.isfinite(x) for x in (o,h,l,c,v,q)) or t%interval_ms or min(o,h,l,c)<=0 or h<max(o,c) or l>min(o,c) or min(v,q,trades)<0:raise ValueError('CANDLE_CONTRACT_INVALID')
            bars.append([t,o,h,l,c,v,q,trades])
        return bars

def _publish_same(path,data):
    try:publish(path,data)
    except FileExistsError:
        if path.read_bytes()!=data:raise ValueError('ARCHIVE_CACHE_CONTENT_CONFLICT')

def retrieve(key,root,interval_ms=HOUR):
    root=Path(root);p=root/'archives'/key;p.parent.mkdir(parents=True,exist_ok=True)
    check_path=p.with_suffix(p.suffix+'.CHECKSUM')
    raw=p.read_bytes() if p.exists() else fetch(BASE+key)
    check=check_path.read_text() if check_path.exists() else fetch(BASE+key+'.CHECKSUM').decode()
    if not check.split() or hashlib.sha256(raw).hexdigest()!=check.split()[0]:raise ValueError('CHECKSUM_FAILURE')
    bars=parse_zip(raw,interval_ms)
    if not p.exists():_publish_same(p,raw)
    if not check_path.exists():_publish_same(check_path,check.encode())
    p.chmod(0o600);check_path.chmod(0o600)
    return bars,len(raw),hashlib.sha256(raw).hexdigest()
