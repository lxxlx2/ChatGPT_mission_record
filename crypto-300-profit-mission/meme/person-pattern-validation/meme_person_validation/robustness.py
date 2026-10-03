from statistics import median,mean
STONK='6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx'
def metrics(rows):
    pnl=[e['realized_pnl_usd'] for e in rows];returns=[e['realized_roi'] for e in rows if e.get('realized_roi') is not None];positive=sum(p for p in pnl if p>0);negative=-sum(p for p in pnl if p<0)
    ordered=sorted((p for p in pnl if p>0),reverse=True)
    return {'sample_count':len(rows),'winner_count':sum(p>0 for p in pnl),'loser_count':sum(p<0 for p in pnl),'realized_pnl':sum(pnl),'median_return':median(returns) if returns else None,'mean_return':mean(returns) if returns else None,'win_rate':sum(p>0 for p in pnl)/len(pnl) if pnl else None,'profit_factor':positive/negative if negative else None,'MFE':None,'MAE':None,'false_positive_rate':None,'followable_rate':None,'pnl_concentration_top1':sum(ordered[:1])/positive if positive else None,'pnl_concentration_top3':sum(ordered[:3])/positive if positive else None}
def robustness(episodes,theme_labels=None):
    rows=[e for e in episodes if e.get('reconstruction_status')=='FULLY_RECONSTRUCTED' and e.get('full_exit') and e.get('realized_pnl_usd') is not None]
    ranked=sorted([e for e in rows if e['realized_pnl_usd']>0],key=lambda e:(-e['realized_pnl_usd'],e['episode_id']))
    def excluding(ids): return metrics([e for e in rows if e['episode_id'] not in ids])
    totals={}
    for e in rows: totals[e['mint']]=totals.get(e['mint'],0)+e['realized_pnl_usd']
    largest=max(totals,key=totals.get) if totals else None
    out={'accounting_mode':'CLOSED_REALIZED_ONLY','ALL':metrics(rows),'EX_TOP1':excluding({e['episode_id'] for e in ranked[:1]}),'EX_TOP3':excluding({e['episode_id'] for e in ranked[:3]}),'EX_LARGEST_TOKEN':metrics([e for e in rows if e['mint']!=largest]),'EX_STONK_IF_MATERIAL':metrics([e for e in rows if e['mint']!=STONK]),'EX_LARGEST_THEME':{'status':'UNAVAILABLE','reason':'VALIDATED_THEME_LABELS_MISSING'},'top1_episode_id':ranked[0]['episode_id'] if ranked else None,'top3_episode_ids':[e['episode_id'] for e in ranked[:3]]}
    if rows and theme_labels and all(e['mint'] in theme_labels for e in rows):
        themes={}
        for e in rows: themes[theme_labels[e['mint']]]=themes.get(theme_labels[e['mint']],0)+e['realized_pnl_usd']
        top=max(themes,key=themes.get);out['EX_LARGEST_THEME']=metrics([e for e in rows if theme_labels[e['mint']]!=top])
    if not rows: out['status']='UNAVAILABLE_NO_CANONICAL_EPISODES'
    return out
