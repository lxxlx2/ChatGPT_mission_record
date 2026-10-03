"""Source fixtures reject a behavioral family; they never train thresholds or provide replay truth."""
import re
UNSAFE_ONLY={'buys_5m','buys_15m','buys_30m','buys_1h','buys_6h','buys_24h','position_growth_ratio','gross_buy_5m','gross_buy_15m','gross_buy_30m','gross_buy_1h','net_buy_5m','net_buy_15m','net_buy_30m','net_buy_1h','no_major_sell','buy_velocity','buy_velocity_acceleration','time_since_first_buy'}
def evaluate_family(feature_names,fixtures):
    unsafe=set(feature_names).issubset(UNSAFE_ONLY)
    controls=[]
    for row in fixtures:
        label=row.get('data_status',row.get('record_type',''))
        raw=row.get('snapshot_total_pnl_usd',row.get('ROI',''))
        severe_loss=bool(re.search(r'-\s*\d',str(raw)))
        buys=re.match(r'\d+',str(row.get('buy_count','')))
        if severe_loss and buys and int(buys.group())>1:
            controls.append({'mint':row.get('CA',row.get('ca')),'symbol':row['symbol'],'research_label':label,'source_pnl_canonical':False,'test_result':'FAIL_BEHAVIOR_ONLY' if unsafe else 'UNTESTED_NEEDS_CAUSAL_REPLAY'})
    return {'status':'FAIL' if unsafe and controls else 'UNAVAILABLE','controls':controls,'reason':'ACCUMULATION_ALONE_HAS_OBSERVED_LOSING_COUNTEREXAMPLES' if unsafe and controls else 'POINT_IN_TIME_CONTROL_FEATURES_AND_EXECUTABLE_REPLAY_REQUIRED'}
