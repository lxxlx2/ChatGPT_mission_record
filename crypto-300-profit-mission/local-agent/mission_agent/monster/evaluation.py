"""Future-dependent audit quantities; never imported into live candidate features."""
import bisect,math
from .ground_truth import HOUR

def noise_audit(candidates,data):
    rows=[]
    indexed={k:([b[0]+HOUR for b in bars],bars) for k,bars in data.items()}
    for venue,symbol,t in candidates:
        times,bars=indexed[(venue,symbol)];i=bisect.bisect_left(times,t)
        if i==len(times) or times[i]!=t:raise ValueError('CANDIDATE_PRICE_MISSING')
        b=bars[i];row={'venue':venue,'symbol':symbol,'activation_time':t,'event_id':f'{venue}:{symbol}:{t}','activation_close':b[4],'preceding_1h_return':b[4]/bars[i-1][4]-1 if i and times[i]-times[i-1]==HOUR else None}
        for hours in (24,72,168):
            window=bars[i+1:i+hours+1];complete=len(window)==hours and all(x[0]==b[0]+(j+1)*HOUR for j,x in enumerate(window))
            row[f'{hours}h_status']='COMPLETE' if complete else 'CENSORED'
            row[f'{hours}h_max_multiple']=max(x[2] for x in window)/b[4] if complete else None
            row[f'{hours}h_non2x']=bool(row[f'{hours}h_max_multiple']<2) if complete else None
        rows.append(row)
    summary={}
    for hours in (24,72,168):
        complete=[r for r in rows if r[f'{hours}h_status']=='COMPLETE'];summary[str(hours)]={'complete':len(complete),'censored':len(rows)-len(complete),'non2x_count':sum(r[f'{hours}h_non2x'] for r in complete),'non2x_rate':sum(r[f'{hours}h_non2x'] for r in complete)/len(complete) if complete else None}
    noise=sorted([r for r in rows if r['168h_non2x']],key=lambda r:(-(r['preceding_1h_return'] or 0),r['event_id']))
    return rows,summary,noise

def attach_prices(metric,data):
    indexed={k:({b[0]+HOUR:b[4] for b in bars}) for k,bars in data.items()}
    for r in metric['records']:
        t=r['first_candidate_time'];r['first_candidate_multiple']=None
        if t is not None:
            close=indexed[(r['venue'],r['symbol'])][t]
            # Ground truth event ID uses its original open time.
            anchor_open=int(r['event_id'].rsplit(':',1)[1]);anchor=indexed[(r['venue'],r['symbol'])][anchor_open+HOUR]
            r['first_candidate_multiple']=close/anchor
