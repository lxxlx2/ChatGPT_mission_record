"""Offline delayed-entry evaluator; never substitutes wallet fill for user executable quote."""
from decimal import Decimal
HORIZONS=(60,120,300,600,900,1800,3600,21600,86400)

def evaluate(available_at,quotes):
    """Quotes must be actual executable, same-notional historical bid/ask observations."""
    valid=sorted([q for q in quotes if q.get('executable') is True and q.get('source') and q['at']>=available_at],key=lambda q:q['at'])
    result={str(h):{'status':'UNAVAILABLE','reason':'NO_EXECUTABLE_DELAYED_ENTRY_QUOTE'} for h in HORIZONS}
    if not valid:return result
    entry=valid[0];ask=Decimal(entry['ask'])
    if entry['at']>available_at+60 or ask<=0:return result
    for h in HORIZONS:
        targets=[q for q in valid if available_at+h<=q['at']<=available_at+h+60]
        if not targets:continue
        end=targets[0];window=[q for q in valid if entry['at']<=q['at']<=end['at']];prices=[Decimal(q['bid']) for q in window];peak=ask;drawdown=Decimal(0)
        for v in prices:peak=max(peak,v);drawdown=min(drawdown,v/peak-1)
        result[str(h)]={'status':'MEASURED','delayed_entry_return':str(Decimal(end['bid'])/ask-1),'MFE':str(max(prices)/ask-1),'MAE':str(min(prices)/ask-1),'max_drawdown':str(drawdown),'entry_at':entry['at'],'notional':entry.get('notional'),'source':entry['source']}
    return result
