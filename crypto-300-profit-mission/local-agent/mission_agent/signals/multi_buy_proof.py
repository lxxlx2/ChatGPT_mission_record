"""Offline proof for two or more independently bound, direct CPMM buys."""
from collections import Counter
from hashlib import sha256
import re

from ..frank.parser import WSOL
from .policy import USDC

PROGRAM = "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"
SPL = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
COMPUTE = "ComputeBudget111111111111111111111111111111"
QUOTES = frozenset({USDC, WSOL, "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"})
BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
SWAP_INPUT = sha256(b"global:swap_base_input").digest()[:8]
SWAP_OUTPUT = sha256(b"global:swap_base_output").digest()[:8]
MAX_U64 = 2**64 - 1


class _Unproven(ValueError):
    pass


def _check(value):
    if not value:
        raise _Unproven()


def _b58(value, size):
    _check(isinstance(value, str) and size <= len(value) <= (size*139+99)//100)
    integer = 0
    for char in value:
        integer = integer * 58 + BASE58.index(char)
    raw = bytes(len(value)-len(value.lstrip("1"))) + integer.to_bytes((integer.bit_length()+7)//8, "big")
    _check(len(raw)==size)
    return raw


def _amount(value):
    _check(isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]{0,19}", value))
    n = int(value)
    _check(n <= MAX_U64)
    return n


def _balances(rows, names):
    _check(isinstance(rows, list) and len(rows) <= len(names))
    result = {}
    for row in rows:
        i = row["accountIndex"]
        _check(type(i) is int and 0 <= i < len(names) and names[i] not in result)
        mint, owner, token = row["mint"], row["owner"], row["uiTokenAmount"]
        decimals = token["decimals"]
        _b58(mint,32)
        _b58(owner,32)
        _check(type(decimals) is int and 0 <= decimals <= 255)
        result[names[i]] = (mint, owner, row.get("programId"), decimals, _amount(token["amount"]))
    return result


def _transfer(ix, src, dst, mint, decimals, authority):
    _check(ix["programId"]==SPL and type(ix["stackHeight"]) is int and ix["stackHeight"]==2)
    obj = ix["parsed"]
    info = obj["info"]
    _check(info["source"]==src and info["destination"]==dst and info["authority"]==authority)
    if obj["type"]=="transferChecked":
        amount = info["tokenAmount"]
        _check(info["mint"]==mint and type(amount["decimals"]) is int and amount["decimals"]==decimals)
        raw = _amount(amount["amount"])
    else:
        _check(obj["type"]=="transfer" and ("mint" not in info or info["mint"]==mint))
        raw = _amount(info["amount"])
    _check(raw>0)
    return raw


def prove_direct_buys(signature, tx, wallet, evidence):
    """Return ordered research-only legs, or no proof; never infer from net deltas."""
    try:
        return _prove(signature, tx, wallet, evidence)
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError):
        return []


def _prove(signature, tx, wallet, evidence):
    meta, transaction = tx["meta"], tx["transaction"]
    message = transaction["message"]
    keys = message["accountKeys"]
    _check(0 < len(keys) <= 256)
    names = [k["pubkey"] for k in keys]
    _check(len(set(names))==len(names) and names[0]==wallet and keys[0]["signer"] is True)
    _b58(wallet,32)
    _b58(signature,64)
    _check(transaction["signatures"][0]==signature and evidence["wallet_is_signer"] is True)
    _check(meta["err"] is None and type(meta["fee"]) is int and meta["fee"]>=0)
    _check(meta["preBalances"][0]-meta["postBalances"][0]==meta["fee"])
    _check(not evidence["decoded_transient_token_flows"])

    before = _balances(meta["preTokenBalances"], names)
    after = _balances(meta["postTokenBalances"], names)
    _check(before.keys()==after.keys() and all(before[k][:4]==after[k][:4] for k in before))
    outer = message["instructions"]
    _check(isinstance(outer,list) and 2 <= len(outer) <= 20)
    inner = {}
    for group in meta["innerInstructions"]:
        i = group["index"]
        _check(type(i) is int and 0 <= i < len(outer) and i not in inner)
        inner[i] = group["instructions"]

    deltas, legs, targets = Counter(), [], set()
    for i, ix in enumerate(outer):
        pid = ix["programId"]
        if pid==COMPUTE:
            _check(not inner.get(i))
            continue
        _check(pid==PROGRAM and i in inner and len(inner[i])==2 and len(legs)<8)
        payload = _b58(ix["data"],24)
        _check(payload[:8] in (SWAP_INPUT,SWAP_OUTPUT))
        first = int.from_bytes(payload[8:16],"little")
        second = int.from_bytes(payload[16:24],"little")
        accounts = ix["accounts"]
        _check(isinstance(accounts,list) and len(accounts)==13 and all(k in names for k in accounts))
        payer, authority, _, pool, source, dest, vault_in, vault_out, in_program, out_program, quote, target, _ = accounts
        _check(payer==wallet and authority!=wallet and in_program==out_program==SPL)
        _check(len({wallet,authority,pool,source,dest,vault_in,vault_out,quote,target})==9)
        _check(quote in QUOTES and target not in QUOTES and target not in targets)
        for addr in (authority,pool,source,dest,vault_in,vault_out,target):
            _b58(addr,32)
        q_dec,t_dec=before[source][3],before[dest][3]
        for addr, mint, owner, decimals in ((source,quote,wallet,q_dec),(dest,target,wallet,t_dec),
                                             (vault_in,quote,authority,q_dec),(vault_out,target,authority,t_dec)):
            _check(before[addr][:4]==(mint,owner,SPL,decimals))
        paid = _transfer(inner[i][0],source,vault_in,quote,q_dec,wallet)
        received = _transfer(inner[i][1],vault_out,dest,target,t_dec,authority)
        if payload[:8]==SWAP_INPUT:
            _check(paid==first and received>=second)
        else:
            _check(paid<=first and received==second)
        deltas.update({source:-paid, vault_in:paid, vault_out:-received, dest:received})
        targets.add(target)
        legs.append({"leg_id":sha256(f"{signature}:{i}:RAYDIUM_CPMM_DIRECT".encode()).hexdigest(),
                     "outer_index":i,"mint":target,"token_raw":str(received),"token_decimals":t_dec,
                     "quote_mint":quote,"quote_raw":str(paid),"quote_decimals":q_dec,"pool":pool,
                     "protocol":"RAYDIUM_CPMM_DIRECT_CLASSIC_SPL"})
    _check(len(legs)>=2)
    _check(all(after[a][4]-v[4]==deltas[a] for a,v in before.items()))
    return legs
