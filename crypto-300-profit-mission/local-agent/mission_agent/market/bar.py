from dataclasses import dataclass,asdict
from decimal import Decimal,localcontext
from ..hashing import digest

ASSETS=('BTC','ETH','SOL','BNB','HYPE')
MINUTE=60000

def dec(value):
 if isinstance(value,float):raise ValueError('binary float forbidden')
 d=Decimal(str(value))
 if not d.is_finite():raise ValueError('nonfinite numeric')
 text=format(d,'f')
 return text.rstrip('0').rstrip('.') if '.' in text else text

@dataclass(frozen=True)
class Bar:
 asset:str
 venue:str
 source_symbol:str
 open_time_utc:int
 open:str
 high:str
 low:str
 close:str
 volume:str
 quote_volume:str|None=None
 trade_count:int|None=None
 is_closed:bool=True
 source_event_time:int|None=None
 received_at:int|None=None
 interval:str='1m'
 schema_version:int=1
 bar_version:int=1

 def __post_init__(self):
  if self.asset not in ASSETS or self.venue not in ('binance_spot','hyperliquid_perp') or self.interval!='1m' or self.open_time_utc%MINUTE:
   raise ValueError('invalid canonical scope/time')
  values=[Decimal(getattr(self,k)) for k in ('open','high','low','close','volume')]
  if any(not d.is_finite() for d in values) or min(values[:4])<=0 or values[4]<0:
   raise ValueError('invalid OHLCV')
  o,h,l,c,v=values
  if l>min(o,c) or h<max(o,c) or l>h:raise ValueError('OHLC inconsistency')
  if self.source_symbol != (self.asset if self.asset=='HYPE' else self.asset+'USDT'):raise ValueError('wrong source symbol')
  if (self.asset=='HYPE') != (self.venue=='hyperliquid_perp'):raise ValueError('wrong asset venue')

 @property
 def close_time_utc(self):return self.open_time_utc+MINUTE
 def value(self):return {**asdict(self),'close_time_utc':self.close_time_utc}
 @property
 def source_hash(self):return digest({k:v for k,v in self.value().items() if k not in ('received_at','source_event_time','bar_version')})

 def same(self,other):return self.source_hash==other.source_hash
