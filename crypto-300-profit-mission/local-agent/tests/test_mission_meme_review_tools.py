import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).parents[1]


def load_script(name):
    path=ROOT/'scripts'/name
    spec=importlib.util.spec_from_file_location(name.replace('.py',''),path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


threshold=load_script('mission_meme_threshold_replay.py')
fixture=load_script('capture_jupiter_quote_fixtures.py')
shadow=load_script('frank_sol_usd_shadow_replay.py')


def test_threshold_outcome_marks_no_route_as_censored():
    rows=[{'bucket_start':1000,'route_exists':0,'execution_price_usdc':None}]
    result=threshold.outcome(rows,1000)
    assert result['status']=='NO_ROUTE' and result['row'] is None


def test_threshold_metrics_apply_minus_100_only_to_no_route():
    samples=[
        {'candidate_decision':'BUY','return_15m_pct':10.0,'return_60m_pct':20.0,'outcome_15m_status':'OBSERVED','outcome_60m_status':'OBSERVED'},
        {'candidate_decision':'BUY','return_15m_pct':None,'return_60m_pct':None,'outcome_15m_status':'NO_ROUTE','outcome_60m_status':'NO_ROUTE'},
    ]
    result=threshold.metrics(samples,'BUY',min_samples=2)
    assert result['sample_count']==2
    assert result['return_60m_count']==1
    assert result['censored_60m_count']==1
    assert result['no_route_60m_count']==1
    assert result['route_failure_bound_worst_60m_pct']==-100.0
    assert result['status']=='EVALUABLE_WITH_ROUTE_FAILURE_BOUND'


def test_no_observation_stays_unknown_and_is_not_forced_to_minus_100():
    samples=[
        {'candidate_decision':'BUY','return_15m_pct':5.0,'return_60m_pct':10.0,'outcome_15m_status':'OBSERVED','outcome_60m_status':'OBSERVED'},
        {'candidate_decision':'BUY','return_15m_pct':None,'return_60m_pct':None,'outcome_15m_status':'NO_OBSERVATION','outcome_60m_status':'NO_OBSERVATION'},
    ]
    result=threshold.metrics(samples,'BUY',min_samples=2)
    assert result['unknown_censored_60m_count']==1
    assert result['no_route_60m_count']==0
    assert result['route_failure_bound_worst_60m_pct']==10.0
    assert result['status']=='EVALUABLE_WITH_UNKNOWN_CENSORING'


def test_threshold_metrics_require_larger_default_sample_gate():
    assert threshold.replay.__defaults__==(30,)


def test_fixture_amount_uses_exact_decimal_not_float():
    assert fixture.usdc_raw('30')=='30000000'
    assert fixture.usdc_raw('0.000001')=='1'


def test_fixture_amount_rejects_more_than_six_decimals():
    try:fixture.usdc_raw('0.0000001')
    except ValueError as exc:assert str(exc)=='USDC_AMOUNT_REQUIRES_AT_MOST_6_DECIMALS'
    else:raise AssertionError('expected ValueError')


def test_shadow_cli_abort_cleans_target_and_writes_failure_report(tmp_path,monkeypatch):
    target=tmp_path/'shadow.sqlite';report=tmp_path/'report.json';source=tmp_path/'source.sqlite'
    source.write_text('unused')

    def fail_replay(source_path,target_path,policy_path,client=None,reference_cache_db=None):
        Path(target_path).write_text('partial')
        for suffix in ('-wal','-shm','-journal'):
            Path(str(target_path)+suffix).write_text('partial')
        raise RuntimeError('simulated replay abort')

    monkeypatch.setattr(shadow,'replay',fail_replay)
    monkeypatch.setattr(sys,'argv',[
        'frank_sol_usd_shadow_replay.py','--source',str(source),'--target',str(target),'--report',str(report)
    ])
    with pytest.raises(SystemExit) as exc:
        shadow.main()
    assert 'SHADOW_REPLAY_ABORTED' in str(exc.value)
    assert not any(Path(str(target)+suffix).exists() for suffix in ('','-wal','-shm','-journal'))
    body=json.loads(report.read_text())
    assert body['status']=='ABORTED'
    assert body['target_cleaned'] is True
    assert body['error_type']=='RuntimeError'


def test_shadow_cli_keyboard_interrupt_cleans_target_and_preserves_interrupt_semantics(tmp_path,monkeypatch):
    target=tmp_path/'shadow.sqlite';report=tmp_path/'report.json';source=tmp_path/'source.sqlite'
    source.write_text('unused')

    def interrupt_replay(source_path,target_path,policy_path,client=None,reference_cache_db=None):
        Path(target_path).write_text('partial')
        Path(str(target_path)+'-wal').write_text('partial')
        raise KeyboardInterrupt()

    monkeypatch.setattr(shadow,'replay',interrupt_replay)
    monkeypatch.setattr(sys,'argv',[
        'frank_sol_usd_shadow_replay.py','--source',str(source),'--target',str(target),'--report',str(report)
    ])
    with pytest.raises(KeyboardInterrupt):
        shadow.main()
    assert not any(Path(str(target)+suffix).exists() for suffix in ('','-wal','-shm','-journal'))
    body=json.loads(report.read_text())
    assert body['status']=='ABORTED'
    assert body['target_cleaned'] is True
    assert body['error_type']=='KeyboardInterrupt'


def test_shadow_cli_refuses_existing_report_without_overwrite_or_replay(tmp_path,monkeypatch):
    target=tmp_path/'shadow.sqlite';report=tmp_path/'report.json';source=tmp_path/'source.sqlite'
    source.write_text('unused');report.write_text('KEEP_ME')
    called={'replay':0}

    def should_not_run(*args,**kwargs):
        called['replay']+=1
        raise AssertionError('replay should not run')

    monkeypatch.setattr(shadow,'replay',should_not_run)
    monkeypatch.setattr(sys,'argv',[
        'frank_sol_usd_shadow_replay.py','--source',str(source),'--target',str(target),'--report',str(report)
    ])
    with pytest.raises(SystemExit) as exc:
        shadow.main()
    assert str(exc.value)=='REPORT_MUST_NOT_EXIST'
    assert report.read_text()=='KEEP_ME'
    assert called['replay']==0
    assert not shadow._target_artifacts_exist(target)
