"""Frozen V1 objective episodes; no predictor features or tuning."""
from collections import deque
from statistics import median
HOUR=3600000
START=1735689600000
END=1790812800000
SPLITS={'TRAIN':(START,1767225600000),'VALIDATION':(1767225600000,1782864000000),'AUDIT':(1782864000000,END)}

def segments(bars):
    chunk=[]
    for b in bars:
        if chunk and b[0]-chunk[-1][0]!=HOUR:
            yield chunk;chunk=[]
        chunk.append(b)
    if chunk:yield chunk

def discover(bars,venue,symbol,earliest_archive_month=None,current_active=False):
    events=[];eligible=0;censored=0
    for seg in segments(bars):
        n=len(seg)
        dq=deque()
        for k in range(1,min(n,169)):
            while dq and seg[dq[-1]][2]<seg[k][2]:dq.pop()
            dq.append(k)
        skip=-1
        for i,b in enumerate(seg):
            if not START<=b[0]+HOUR<END:pass
            elif i+168>=n:censored+=1
            else:
                eligible+=1
                mx=seg[dq[0]][2]/b[4]
                if b[0]>skip and mx>=2:
                    window=seg[i+1:i+169];peak=max(x[2] for x in window);peakrow=next(x for x in window if x[2]==peak);cross={}
                    for threshold in (1.25,1.5,2,3,5,10,20):cross[str(threshold)]=next((x[0]+HOUR for x in window if x[2]/b[4]>=threshold),None)
                    past=seg[max(0,i-719):i+1];old=i>=2159 and len(past)==720 and median(x[6] for x in past)<10000 and max(x[4] for x in past)/min(x[4] for x in past)<2
                    # Independently verified first archive starts before the warm-up left edge only proves not new; observed left edge alone never proves listing.
                    first_observed=bars[0][0] if bars else None
                    import datetime
                    first_month=datetime.datetime.fromtimestamp(first_observed/1000,datetime.timezone.utc).strftime('%Y-%m') if first_observed else None
                    verified_first=first_observed if earliest_archive_month and earliest_archive_month>="2024-10" and earliest_archive_month==first_month else None
                    age='VERIFIED_FIRST_ARCHIVE_HISTORY' if verified_first is not None else 'VERIFIED_NOT_NEW' if earliest_archive_month and earliest_archive_month<'2024-10' else 'UNKNOWN'
                    tier=20 if mx>=20 else 10 if mx>=10 else 5 if mx>=5 else 3 if mx>=3 else 2
                    split=next((s for s,(lo,hi) in SPLITS.items() if lo<=b[0]+HOUR<hi),None)
                    full=split is not None and window[-1][0]+HOUR<SPLITS[split][1]
                    events.append({'event_id':f'{venue}:{symbol}:{b[0]}','venue':venue,'symbol':symbol,'anchor_time':b[0]+HOUR,'anchor_price':b[4],'anchor_quote_volume':b[6],'anchor_trades':b[7],'peak_quote_volume':peakrow[6],'peak_trades':peakrow[7],'quality_flags':(['EXTREME_INTRAHOUR_RANGE'] if peakrow[2]/peakrow[3]>=5 else [])+(['LOW_ANCHOR_LIQUIDITY'] if b[6]<10000 else []),'peak_time':peakrow[0]+HOUR,'max72h':max(x[2] for x in window[:72])/b[4],'max7d':mx,'exact_tier':tier,'crossings':cross,'hours_from_anchor_to_crossing':{k:(ct-b[0]-HOUR)/HOUR if ct is not None else None for k,ct in cross.items()},'duration_hours':(peakrow[0]-b[0])/HOUR,'drawdown_to_peak':min(x[3] for x in window if x[0]<=peakrow[0])/b[4]-1,'current_active':current_active,'age_status':age,'new_listing':(b[0]-verified_first<168*HOUR) if verified_first is not None else False if age=='VERIFIED_NOT_NEW' else None,'first_available_history_time':verified_first,'old_shell':old,'split':split,'split_future_complete':full})
                    skip=peakrow[0]+168*HOUR
            if dq and dq[0]==i+1:dq.popleft()
            k=i+169
            if k<n:
                while dq and seg[dq[-1]][2]<seg[k][2]:dq.pop()
                dq.append(k)
    return events,{'eligible_anchors':eligible,'right_censored_anchors':censored}
