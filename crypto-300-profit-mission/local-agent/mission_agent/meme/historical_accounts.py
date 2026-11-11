"""Transaction-bound historical token accounts, never lifetime owner claims.

Primary references: https://solana.com/docs/rpc/http/gettransaction
https://solana.com/docs/rpc/json-structures
https://solana.com/docs/tokens/basics/close-account
All inputs come from already requested finalized jsonParsed transactions.
"""
import hashlib
import json
from .holder_ranks import PROGRAMS,valid_pubkey

MAX_OBSERVATIONS=200
MAX_BALANCE_ROWS=512


class HistoricalAccountEvidenceError(ValueError):
    pass


def observe_token_accounts(tx,signature,mint,owner,decimals,*,expected_slot=None):
    def reject(code):raise HistoricalAccountEvidenceError(code)
    if not isinstance(tx,dict) or type(tx.get('slot')) is not int or tx['slot']<=0:
        reject('TRANSACTION_CONTEXT_UNAVAILABLE')
    if expected_slot is not None and (type(expected_slot) is not int or expected_slot!=tx['slot']):reject('TRANSACTION_SLOT_CONFLICT')
    meta=tx.get('meta');transaction=tx.get('transaction')
    if not isinstance(meta,dict) or 'err' not in meta or meta['err'] is not None:
        reject('TRANSACTION_SUCCESS_UNVERIFIED')
    if not isinstance(transaction,dict) or not isinstance(transaction.get('signatures'),list) or not transaction['signatures'] or transaction['signatures'][0]!=signature:
        reject('TRANSACTION_IDENTITY_MISMATCH')
    message=transaction.get('message')
    if not isinstance(message,dict) or not isinstance(message.get('accountKeys'),list):reject('ACCOUNT_KEYS_UNAVAILABLE')
    keys=message['accountKeys']
    if message.get('addressTableLookups') and any(not isinstance(k,dict) for k in keys):reject('LOOKUP_KEYS_UNRESOLVED')
    names=[k.get('pubkey') if isinstance(k,dict) else k for k in keys]
    if not names or any(not valid_pubkey(k) for k in names) or len(set(names))!=len(names):reject('ACCOUNT_KEYS_INVALID')
    phases={}
    for phase,field in [('pre','preTokenBalances'),('post','postTokenBalances')]:
        rows=meta.get(field)
        if not isinstance(rows,list):reject('TOKEN_BALANCES_UNAVAILABLE')
        if len(rows)>MAX_BALANCE_ROWS:reject('TOKEN_BALANCE_ROW_LIMIT')
        parsed={}
        for row in rows:
            if not isinstance(row,dict):reject('TOKEN_BALANCE_ROW_INVALID')
            index=row.get('accountIndex')
            if type(index) is not int or not 0<=index<len(names) or index in parsed:reject('TOKEN_BALANCE_INDEX_INVALID')
            if not valid_pubkey(row.get('owner')) or not valid_pubkey(row.get('mint')):reject('TOKEN_BALANCE_IDENTITY_UNAVAILABLE')
            if row.get('programId') is not None and row['programId'] not in PROGRAMS:reject('TOKEN_BALANCE_PROGRAM_INVALID')
            amount=row.get('uiTokenAmount')
            raw=amount.get('amount') if isinstance(amount,dict) else None
            if not isinstance(raw,str) or not 1<=len(raw)<=20 or not raw.isascii() or not raw.isdigit() or int(raw)>2**64-1:reject('TOKEN_BALANCE_AMOUNT_INVALID')
            if type(amount.get('decimals')) is not int or not 0<=amount['decimals']<=255:reject('TOKEN_BALANCE_DECIMALS_INVALID')
            if row['mint']==mint and amount['decimals']!=decimals:reject('TOKEN_BALANCE_DECIMALS_INVALID')
            parsed[index]=row
        phases[phase]=parsed
    instructions=message.get('instructions') or []
    if not isinstance(instructions,list):reject('TRANSACTION_INSTRUCTIONS_INVALID')
    instructions=list(instructions)
    inner=meta.get('innerInstructions') or []
    if not isinstance(inner,list):reject('TRANSACTION_INSTRUCTIONS_INVALID')
    for group in inner:
        if not isinstance(group,dict) or not isinstance(group.get('instructions'),list):reject('TRANSACTION_INSTRUCTIONS_INVALID')
        instructions.extend(group['instructions'])
    closed={}
    for ix in instructions:
        if not isinstance(ix,dict) or ix.get('programId') not in PROGRAMS:continue
        parsed=ix.get('parsed')
        if not isinstance(parsed,dict) or parsed.get('type')!='closeAccount':continue
        info=parsed.get('info')
        if isinstance(info,dict) and valid_pubkey(info.get('account')):closed.setdefault(info['account'],set()).add(ix['programId'])
    digest=hashlib.sha256(json.dumps(tx,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    when=tx.get('blockTime')
    when=when if type(when) is int and when>0 else None
    out=[]
    for phase in ('pre','post'):
        for index,row in phases[phase].items():
            if row['owner']!=owner or row['mint']!=mint:continue
            before=meta.get('preBalances');after=meta.get('postBalances')
            closure=(phase=='pre' and names[index] in closed and (row.get('programId') is None or row['programId'] in closed[names[index]]) and index not in phases['post']
                     and isinstance(before,list) and isinstance(after,list) and len(before)==len(names)==len(after)
                     and type(before[index]) is int and before[index]>0
                     and type(after[index]) is int and after[index]==0)
            out.append({'account':names[index],'owner':owner,'mint':mint,
                        'raw':row['uiTokenAmount']['amount'],'decimals':decimals,
                        'balance_phase':phase,'signature':signature,'slot':tx['slot'],'block_time':when,
                        'closure_at_transaction_end':'CONFIRMED_CLOSED_AT_TRANSACTION_END' if closure else 'NOT_PROVEN',
                        'response_sha256':digest})
    return out
