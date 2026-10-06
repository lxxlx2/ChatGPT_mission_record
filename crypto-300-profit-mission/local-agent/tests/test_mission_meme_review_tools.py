import importlib.util
from pathlib import Path

ROOT=Path(__file__).parents[1]


def load_script(name):
    path=ROOT/'scripts'/name
    spec=importlib.util.spec_from_file_location(name.replace('.py',''),path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


threshold=load_script('mission_meme_threshold_replay.py')
fixture=load_script('capture_jupiter_quote_fixtures.py')


def test_threshold_outcome_marks_no_route_as_censored():
    rows=[{'bucket_start':1000,'route_exists':0,'execution_price_usdc':None}]
    result=threshold.outcome(rows,1000)
    assert result['status']=='NO_ROUTE' and result['row'] is None


def test_threshold_metrics_include_pessimistic_minus_100_for_censored():
    samples=[
        {'candidate_decision':'BUY','return_15m_pct':10.0,'return_60m_pct':20.0,'outcome_60m_status':'OBSERVED'},
        {'candidate_decision':'BUY','return_15m_pct':None,'return_60m_pct':None,'outcome_60m_status':'NO_ROUTE'},
    ]
    result=threshold.metrics(samples,'BUY',min_samples=2)
    assert result['sample_count']==2
    assert result['return_60m_count']==1
    assert result['censored_60m_count']==1
    assert result['no_route_60m_count']==1
    assert result['pessimistic_worst_60m_pct']==-100.0
    assert result['status']=='EVALUABLE_WITH_CENSORING'


def test_threshold_metrics_require_larger_default_sample_gate():
    assert threshold.replay.__defaults__==(30,)


def test_fixture_amount_uses_exact_decimal_not_float():
    assert fixture.usdc_raw('30')=='30000000'
    assert fixture.usdc_raw('0.000001')=='1'


def test_fixture_amount_rejects_more_than_six_decimals():
    try:fixture.usdc_raw('0.0000001')
    except ValueError as exc:assert str(exc)=='USDC_AMOUNT_REQUIRES_AT_MOST_6_DECIMALS'
    else:raise AssertionError('expected ValueError')
