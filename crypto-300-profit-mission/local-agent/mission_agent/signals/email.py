"""Standalone deterministic MULTIPLE template; does not change signal identity."""
from datetime import datetime,timedelta,timezone
from ..hashing import digest
from .policy import USDC

BKK=timezone(timedelta(hours=7))
def timestamp(at):return datetime.fromtimestamp(at,BKK).isoformat() if at is not None else 'unavailable'
def label(asset):return 'USDC' if asset==USDC else asset

def content(signal):
    if signal['signal_type']!='FRANK_MULTIPLE_SIGNAL':raise ValueError('MULTIPLE_EMAIL_ONLY')
    p=signal['position'];mint=signal['mint'];short=f'{mint[:8]}…{mint[-6:]}'
    when=datetime.fromtimestamp(signal['triggered_at'],BKK).strftime('%Y-%m-%d %H:%M')
    subject=f"[Frank 多倍信号] {short} | {signal['stage']} | {when}"
    cumulative='; '.join(f'{value} {label(asset)}' for asset,value in sorted(p['gross_quote_spent'].items()))
    body='\n'.join(['Frank 多倍信号 — FRANK_LOCAL_SIGNAL_V1 链上行为模型触发','',f"Signal ID: {signal['signal_id']}",f"触发时间: {timestamp(signal['triggered_at'])}",f'Token: {short}',f'CA / Mint: {mint}',f"Stage: {signal['stage']}",f"Episode ID: {signal['episode_id']}",f"首次主动买入时间: {timestamp(p['first_buy_at'])}",f"最新主动买入时间: {timestamp(p['last_buy_at'])}",f"当前 buy_count: {p['buy_count']}",f"当前 sell_count: {p['sell_count']}",f"本次 BUY: {signal['latest_quote_amount']} {label(signal['quote_asset'])}; {signal['latest_buy']} token",f'累计 BUY: {cumulative}',f"当前观察库存: {p.get('current_token_quantity','unavailable')} token (OBSERVED_ACTIVE_SEQUENCE)",'USD estimate: unavailable; USDC quote => direct numeric comparison','LIFETIME_POSITION_UNKNOWN; CURRENT_ACCUMULATION_SEQUENCE_KNOWN','', '触发规则:']+['- '+r for r in signal['reason_codes']]+['','最新触发交易:',signal['latest_trade_signature'],'',f"policy_hash: {signal['policy_hash']}"])
    return {'signal_id':signal['signal_id'],'subject':subject,'body':body,'body_hash':digest(body),'content_hash':digest({'subject':subject,'body':body})}
