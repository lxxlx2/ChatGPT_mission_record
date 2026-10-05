from decimal import Decimal as D
VERSION='PRICE_RULE_V1'

def hits(f,asset):
 result=[]
 for rule,key,threshold in [('R1','return_15m','.03'),('R2','return_1h','.05'),('R3','return_4h','.08'),('R4','return_24h','.12')]:
  if f.get(key) is not None and abs(D(f[key]))>=D(threshold):result.append(rule)
 if f.get('reversal_15m') is not None and D(f['reversal_15m'])>=D('.04'):result.append('R5')
 if f.get('breakout_two'):result.append('R6')
 if all(f.get(k) is not None for k in ('realized_vol_5m','trailing_24h_vol_median','return_5m')):
  median=D(f['trailing_24h_vol_median'])
  if median>0 and D(f['realized_vol_5m'])>=median*3 and abs(D(f['return_5m']))>=D('.02'):result.append('R7')
 if asset!='BTC':
  for rule,key,threshold in [('R8','relative_return_vs_btc_1h','.04'),('R9','relative_return_vs_btc_4h','.06')]:
   if f.get(key) is not None and abs(D(f[key]))>=D(threshold):result.append(rule)
 return result

def ground_truth(f):
 result=[]
 for rule,key,threshold in [('GT1','return_1h','.04'),('GT2','return_4h','.07'),('GT3','reversal_15m','.05')]:
  if f.get(key) is not None and abs(D(f[key]))>=D(threshold):result.append(rule)
 if f.get('gt_breakout_three'):result.append('GT4')
 if all(f.get(k) is not None for k in ('realized_vol_5m','trailing_24h_vol_median','return_5m')):
  m=D(f['trailing_24h_vol_median'])
  if m>0 and D(f['realized_vol_5m'])>=m*4 and abs(D(f['return_5m']))>=D('.025'):result.append('GT5')
 return result
