"""Deterministic standalone multiple-email content; no sender or credential access."""
import json
from datetime import datetime,timedelta,timezone
from ..hashing import digest
from .policy import USDC

BKK=timezone(timedelta(hours=7))
def timestamp(at):return datetime.fromtimestamp(at,BKK).isoformat() if at is not None else 'unavailable'
def label(asset):return 'USDC' if asset==USDC else asset

def content(signal):
    if signal['signal_type']!='FRANK_MULTIPLE_SIGNAL':raise ValueError('MULTIPLE_EMAIL_ONLY')
    p=signal['position'];mint=signal['mint'];subject=f"[Frank 多倍信号] {mint[:8]}…{mint[-6:]} | {signal['stage']} | {timestamp(signal['triggered_at'])[:10]}"
    cumulative='; '.join(f'{value} {label(asset)}' for asset,value in sorted(p['gross_quote_spent'].items()))
    body='\n'.join(['Frank 多倍信号 — FRANK_LOCAL_SIGNAL_V1 链上行为模型触发','',f'Token: {mint[:8]}…{mint[-6:]}',f'CA / mint: {mint}',f"触发阶段: {signal['stage']}",f"触发时间: {timestamp(signal['triggered_at'])}",f"首次买入: {timestamp(p['first_buy_at'])}",f"最新买入: {timestamp(p['last_buy_at'])}",f"当前 buy_count: {p['buy_count']}",f"本次买入: {signal['latest_quote_amount']} {label(signal['quote_asset'])}; {signal['latest_buy']} token",f'累计买入: {cumulative}',f"当前持仓: {p.get('current_token_quantity','unavailable')} token (OBSERVED_ACTIVE_SEQUENCE)",'USD estimate: unavailable; USDC quote => direct numeric comparison','LIFETIME_POSITION_UNKNOWN; CURRENT_ACCUMULATION_SEQUENCE_KNOWN','', '模型触发原因:']+['- '+r for r in signal['reason_codes']]+['','最新交易:',signal['latest_trade_signature'],'',f"signal_id: {signal['signal_id']}",f"policy_hash: {signal['policy_hash']}"])
    return {'signal_id':signal['signal_id'],'subject':subject,'body':body,'content_hash':digest({'subject':subject,'body':body})}
