import copy,socket
import pytest
from mission_agent.signals.email import content,REASON_ZH
from mission_agent.hashing import digest
from mission_agent.signals.gmail import GmailOutbox
from mission_agent.signals.store import Ledger
from test_frank_v1 import fixture_multiple,signals

@pytest.fixture
def signal(tmp_path):
    ledger,engine=fixture_multiple(tmp_path)
    return signals(ledger)[-1]

def test_mobile_summary_and_full_audit(signal):
    mail=content(signal);first=mail['body'].split('链上事实')[0]
    assert '状态：疑似高确信度' in first and 'BUY 5,000 USDC' in first
    assert '本轮观察到 Frank 主动买入 3 次；主动卖出 0 次' in first and '累计投入 31,000 USDC' in first
    assert '此前已形成持续建仓行为' in first
    assert '本轮至少 3 次主动买入，首笔到最新买入持续 ≥45 分钟' in first
    assert signal['signal_id'] not in first and 'LIFETIME_POSITION_UNKNOWN' not in first
    audit=mail['body'].split('审计信息')[1]
    for key in ('signal_id','episode_id','policy_id','policy_hash','stage','latest_trade_signature','triggering_signature','delivery_mode'):
        assert key+': '+str(signal[key]) in audit
    for code in signal['reason_codes']:assert '- '+code in audit
    assert 'USD 估值：暂无可靠数据' in mail['body']

def test_optional_fields_can_be_missing_without_invention(signal):
    for key in ('symbol','triggering_signature','delivery_mode','policy_id','policy_hash','usd','reason_codes','episode_id','latest_buy_signature','latest_trade_signature','latest_quote_amount','quote_asset','latest_buy','triggered_at'):signal.pop(key,None)
    signal['position']={}
    mail=content(signal)
    assert 'UNAVAILABLE' in mail['body'] and mail['subject'].endswith('unavailable')
    assert '获得 ' not in mail['body'] and '本次触发交易方向：UNAVAILABLE' in mail['body']
    assert 'signal_id: '+signal['signal_id'] in mail['body']

def test_unknown_inventory_and_amount_remain_unknown(signal):
    signal['position']['current_token_quantity']=None
    signal['usd']='unknown';signal['latest_quote_amount']=None
    body=content(signal)['body']
    assert '当前观察库存：UNAVAILABLE token' in body
    assert 'USD 估值：暂无可靠数据' in body
    assert 'BUY UNAVAILABLE USDC' in body

def test_long_mint_and_signatures_are_shortened_only_in_overview(signal):
    signal['mint']='m'*8+'middle'*40+'x'*6
    signal['latest_trade_signature']='a'*180
    signal['latest_buy_signature']='a'*180
    signal['triggering_signature']='b'*180
    mail=content(signal);first=mail['body'].split('链上事实')[0]
    assert 'mmmmmmmm…xxxxxx' in mail['subject'] and 'CA：'+signal['mint'] in first
    audit=mail['body'].split('审计信息')[1]
    assert signal['mint'] in audit and 'a'*180 in audit and 'b'*180 in audit

def test_supplied_unicode_symbol_and_reason_are_preserved(signal):
    signal['symbol']='测试币🪙';signal['reason_codes'].append('NEW_RULE_新条件')
    mail=content(signal)
    assert '测试币🪙' in mail['subject']
    assert mail['body'].count('NEW_RULE_新条件')>=2

def test_missing_symbol_never_uses_price_market_cap_or_other_unapproved_fields(signal):
    signal['symbol']='UNKNOWN';signal['price']='FAKE_PRICE_SENTINEL';signal['market_cap']='FAKE_MARKET_CAP_SENTINEL';signal['pnl']='FAKE_PNL_SENTINEL'
    mail=content(signal)
    assert 'UNKNOWN' not in mail['subject'] and 'mint1' in mail['subject']
    assert 'SENTINEL' not in mail['body']

def test_render_is_deterministic_does_not_mutate_input_or_access_network(signal,monkeypatch):
    original=copy.deepcopy(signal)
    def denied(*args,**kwargs):raise AssertionError('network forbidden')
    monkeypatch.setattr(socket,'socket',denied)
    assert content(signal)==content(signal) and signal==original
    mail=content(signal)
    assert mail['body_hash']==digest(mail['body'])
    assert mail['content_hash']==digest({'subject':mail['subject'],'body':mail['body']})

def test_credentials_environment_and_extra_payload_fields_are_not_rendered(signal,monkeypatch):
    monkeypatch.setenv('FRANK_GMAIL_RECIPIENT','ENV_SENTINEL_DO_NOT_RENDER')
    monkeypatch.setenv('API_KEY','ENV_KEY_SENTINEL_DO_NOT_RENDER')
    signal.update(token='TOKEN_SENTINEL_DO_NOT_RENDER',refresh_token='REFRESH_SENTINEL_DO_NOT_RENDER',client_secret='CLIENT_SENTINEL_DO_NOT_RENDER',recipient='RECIPIENT_SENTINEL_DO_NOT_RENDER',credentials={'value':'OBJECT_SENTINEL_DO_NOT_RENDER'})
    signal['position']['secret']='POSITION_SENTINEL_DO_NOT_RENDER'
    mail=content(signal)
    assert 'SENTINEL' not in mail['subject']+mail['body']

def test_latest_buy_is_not_misrepresented_as_triggering_sell(signal):
    signal['latest_trade_signature']='later-classified-sell'
    signal['triggering_signature']='later-classified-sell'
    body=content(signal)['body']
    assert '最近一次主动买入：\nBUY 5,000 USDC' in body
    assert '\n本次：' not in body and '本次触发交易方向：UNAVAILABLE' in body
    assert 'SELL 5,000' not in body

def test_non_usdc_quote_remains_original_asset_without_usd_conversion(signal):
    signal['quote_asset']='SOL';signal['latest_quote_amount']='7.123'
    signal['position']['gross_quote_spent']={'SOL':'8.456'}
    body=content(signal)['body']
    assert 'BUY 7.123 SOL' in body and '累计投入 8.456 SOL' in body
    assert 'USD 估值：暂无可靠数据' in body

def test_existing_durable_content_is_not_rewritten_by_presentation(signal,tmp_path):
    box=GmailOutbox(Ledger(tmp_path/'delivery'))
    rendered=content(signal);old={**rendered,'body':'previous durable presentation'}
    box.enqueue(old,mode='LIVE')
    with pytest.raises(ValueError,match='IMMUTABLE_GMAIL_IDENTITY_CONFLICT'):box.enqueue(rendered,mode='LIVE')
    assert box.row(signal['signal_id'])['body']=='previous durable presentation'

def test_unknown_reason_fallback_is_not_silently_omitted(signal):
    signal['reason_codes']=['FUTURE_UNMAPPED_REASON']
    body=content(signal)['body']
    assert '- 未识别规则：FUTURE_UNMAPPED_REASON' in body.split('链上事实')[0]
    assert body.count('FUTURE_UNMAPPED_REASON')==3

def test_reason_mapping_covers_only_existing_multiple_codes(signal):
    assert set(signal['reason_codes'])<=set(REASON_ZH)
    assert 'PERSISTENCE_PATH_A_PRIOR_HOURLY_WATCH' in REASON_ZH

def test_accumulation_still_cannot_render_gmail(signal):
    signal['signal_type']='FRANK_ACCUMULATION_SIGNAL'
    with pytest.raises(ValueError,match='MULTIPLE_EMAIL_ONLY'):content(signal)

def test_dry_run_is_marked_as_non_live_at_top_without_changing_delivery_gate(signal):
    assert signal['delivery_mode']=='DRY_RUN_AUDIT'
    assert '历史 / 演练，非当前实时交易' in content(signal)['body'].splitlines()[0]
    signal['delivery_mode']='LIVE'
    assert content(signal)['body'].splitlines()[0]=='Frank 多倍信号'

def test_path_a_is_distinct_from_path_b_and_freshness_does_not_claim_recent_buy(signal):
    signal['reason_codes']=['PERSISTENCE_PATH_A_PRIOR_HOURLY_WATCH','FRESHNESS_BEHAVIOR_PASSED']
    body=content(signal)['body']
    assert '此前观察周期已进入持续建仓 WATCH，本周期仍满足建仓条件' in body
    assert '45 分钟' not in body and '至少 3 次主动买入' not in body
    assert '该建仓行为仍满足模型的新鲜度要求' in body
    assert '最近 60 分钟仍有新买入' not in body

def test_front_contains_complete_ca_times_scope_and_stage_name_explanation(signal):
    first=content(signal)['body'].split('链上事实')[0]
    assert 'CA：'+signal['mint'] in first
    assert '首次主动买入：' in first and '最新主动买入：' in first and 'Asia/Bangkok' in first
    assert '仅代表本轮已观察主动交易序列，不代表 Frank 的完整历史持仓。' in first
    assert '不代表价格将上涨数倍。' in first
    assert '连续买入 3 次' not in first
