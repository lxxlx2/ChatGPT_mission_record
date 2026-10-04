"""Deterministic plain-text MULTIPLE presentation; no state, network or identity changes."""
from datetime import datetime,timedelta,timezone
from decimal import Decimal,InvalidOperation
import json
from ..hashing import digest
from .policy import USDC

BKK=timezone(timedelta(hours=7))
UNAVAILABLE='UNAVAILABLE'
REASON_ZH={
    'ACCUMULATION_BEHAVIOR_STAGE_ESTABLISHED':'此前已形成持续建仓行为',
    'MEANINGFUL_ACCUMULATION_T0_ESTABLISHED':'已确认有效建仓起点',
    'EPISODE_USDC_QUOTE_GE_10000':'本轮累计 USDC 买入金额达到模型要求',
    'PERSISTENCE_PATH_A_PRIOR_HOURLY_WATCH':'此前观察周期已进入持续建仓 WATCH，本周期仍满足建仓条件',
    'PERSISTENCE_PATH_B_GE_3_BUYS_SPAN_GE_45M':'本轮至少 3 次主动买入，首笔到最新买入持续 ≥45 分钟',
    'OBSERVED_INVENTORY_RETAINED_OR_RESUMED_NET_BUYING':'观察到的仓位仍在保留，或近期重新转为净买入',
    'NO_UNRECOVERED_35PCT_ROLLING_DISTRIBUTION':'未触发模型的未恢复减仓否决条件',
    'NO_CONFIRMED_HFT_EXECUTION':'未触发模型的高频交易否决条件',
    'FRESHNESS_BEHAVIOR_PASSED':'该建仓行为仍满足模型的新鲜度要求',
    'NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT':'价格、流动性、GPT 判断等非 Frank 链上行为条件不参与阻止该信号',
}
STAGE_ZH={'SUSPECTED_CONVICTION':'疑似高确信度'}

def timestamp(at):
    if at is None:return 'unavailable'
    try:return datetime.fromtimestamp(at,BKK).isoformat()
    except (ValueError,TypeError,OverflowError,OSError):return 'unavailable'

def text(value):return UNAVAILABLE if value is None or value=='' else str(value)
def label(asset):return 'USDC' if asset==USDC else text(asset)
def short(value):
    value=text(value)
    return value if len(value)<=14 else value[:8]+'…'+value[-6:]
def amount(value):
    if value is None or value=='':return UNAVAILABLE
    try:
        number=Decimal(str(value))
        return format(number,',f') if number.is_finite() else UNAVAILABLE
    except InvalidOperation:return text(value)
def inline(value):return text(value).replace('\r',' ').replace('\n',' ')
def unavailable(value):return value is None or str(value).lower() in ('','unavailable','unknown','undetermined')
def quote_total(values):
    if not values:return UNAVAILABLE
    return '; '.join(amount(v)+' '+label(k) for k,v in sorted(values.items()))

def content(signal):
    if signal['signal_type']!='FRANK_MULTIPLE_SIGNAL':raise ValueError('MULTIPLE_EMAIL_ONLY')
    p=signal.get('position') or {};mint=text(signal.get('mint'));stage=text(signal.get('stage'))
    symbol=signal.get('symbol');token=inline(symbol) if not unavailable(symbol) else short(mint)
    at=signal.get('triggered_at');when=timestamp(at)
    subject_time=when[:10]+' '+when[11:16] if when!='unavailable' else 'unavailable'
    subject=f'[Frank 多倍信号] {token} | {inline(stage)} | {subject_time}'
    codes=signal.get('reason_codes') or []
    explanations=[REASON_ZH.get(code,'未识别规则：'+code) for code in codes]
    priority=('ACCUMULATION_BEHAVIOR_STAGE_ESTABLISHED','EPISODE_USDC_QUOTE_GE_10000','PERSISTENCE_PATH_A_PRIOR_HOURLY_WATCH','PERSISTENCE_PATH_B_GE_3_BUYS_SPAN_GE_45M')
    overview=[REASON_ZH.get(c,'未识别规则：'+c) for c in codes if c in priority][:3]
    if not overview:overview=explanations[:3] or [UNAVAILABLE]
    quote=amount(signal.get('latest_quote_amount'))+' '+label(signal.get('quote_asset'))
    tokens=amount(signal.get('latest_buy'))+' token'
    cumulative=quote_total(p.get('gross_quote_spent'))
    inventory=amount(p.get('current_token_quantity'))+' token'
    # The Engine supplies latest-BUY amounts, not necessarily the triggering event's amounts.
    buy_known=not unavailable(signal.get('latest_buy_signature'))
    same_trade=buy_known and signal.get('latest_buy_signature')==signal.get('latest_trade_signature')
    trade_heading='本次：' if same_trade else '最近一次主动买入：' if buy_known else '买入数据：'
    direction='BUY' if buy_known else UNAVAILABLE
    mode=signal.get('delivery_mode')
    heading='Frank 多倍信号（历史 / 演练，非当前实时交易）' if mode is not None and mode!='LIVE' else 'Frank 多倍信号'
    body=[heading,'“多倍信号”是 Frank 持续建仓行为模型的阶段名称，不代表价格将上涨数倍。','',f'状态：{STAGE_ZH.get(stage,stage)}',f'Token：{token}',f'CA：{mint}',f'时间：{when}（Asia/Bangkok）','',trade_heading,f'{direction} {quote}',('获得 ' if buy_known else 'Token 数量：')+tokens,'','累计：',f"本轮观察到 Frank 主动买入 {text(p.get('buy_count'))} 次；主动卖出 {text(p.get('sell_count'))} 次",f'累计投入 {cumulative}',f"首次主动买入：{timestamp(p.get('first_buy_at'))}（Asia/Bangkok）",f"最新主动买入：{timestamp(p.get('last_buy_at'))}（Asia/Bangkok）",f'当前观察库存：{inventory}',('仅代表本轮已观察主动交易序列，不代表 Frank 的完整历史持仓。' if p.get('inventory_scope')=='OBSERVED_ACTIVE_SEQUENCE' else '库存观察范围：'+text(p.get('inventory_scope'))),'','为什么触发：']+['- '+str(x) for x in overview]
    body+=['','链上事实',f"首次主动买入时间：{timestamp(p.get('first_buy_at'))}（Asia/Bangkok）",f"最新主动买入时间：{timestamp(p.get('last_buy_at'))}（Asia/Bangkok）",f"当前 buy_count：{text(p.get('buy_count'))}",f"当前 sell_count：{text(p.get('sell_count'))}",f'最近一次主动买入 quote：{quote}',f'最近一次主动买入 token：{tokens}',f'累计 quote spent：{cumulative}',f'当前观察库存：{inventory}',f"最新触发交易：{short(signal.get('latest_trade_signature'))}"]
    if not same_trade:body+=['本次触发交易方向：UNAVAILABLE（不从最新 BUY 推断）']
    body+=['','触发说明（全部）：']+['- '+str(x) for x in explanations or [UNAVAILABLE]]
    body+=['','风险 / 不确定性']
    if p.get('lifetime_position')=='LIFETIME_POSITION_UNKNOWN':
        body+=['当前只能确认本轮观察到的建仓序列，无法保证这是 Frank 对该 Token 的完整历史仓位。']
    else:body+=['完整历史仓位状态：'+text(p.get('lifetime_position'))]
    body+=['USD 估值：暂无可靠数据' if unavailable(signal.get('usd')) else 'USD 估值：'+text(signal['usd']),'金额按原始 quote 记录；USDC quote 直接进行数值比较。','本邮件展示模型研究信号，不构成收益保证。']
    mode=signal.get('delivery_mode')
    if mode is not None and mode!='LIVE':body+=['投递模式：'+text(mode)+'；不是当前实时交易。']
    # Whitelist audit fields. Never serialize the input object, environment or credentials.
    body+=['','审计信息',f"signal_id: {signal['signal_id']}",f"episode_id: {text(signal.get('episode_id'))}",f"policy_id: {text(signal.get('policy_id'))}",f"policy_hash: {text(signal.get('policy_hash'))}",f'stage: {stage}',f'CA / Mint: {mint}',f"latest_trade_signature: {text(signal.get('latest_trade_signature'))}"]
    for key in ('triggering_signature','latest_buy_signature','delivery_mode'):
        if key in signal:body.append(key+': '+text(signal[key]))
    body+=['reason_codes:']+['- '+str(c) for c in codes or [UNAVAILABLE]]
    for key in ('inventory_scope','lifetime_position'):
        if key in p:body.append(key+': '+text(p[key]))
    if 'sequence' in signal:body.append('sequence: '+text(signal['sequence']))
    body += ['USD estimate: '+text(signal.get('usd')),f"latest_quote_amount_raw_quantity: {text(signal.get('latest_quote_amount'))}",f"quote_asset: {text(signal.get('quote_asset'))}",f"latest_buy_token_quantity: {text(signal.get('latest_buy'))}",f"current_token_position_raw: {text(p.get('current_token_position'))}",'gross_quote_spent: '+json.dumps(p.get('gross_quote_spent'),ensure_ascii=False,sort_keys=True)]
    body='\n'.join(body)
    return {'signal_id':signal['signal_id'],'subject':subject,'body':body,'body_hash':digest(body),'content_hash':digest({'subject':subject,'body':body})}
