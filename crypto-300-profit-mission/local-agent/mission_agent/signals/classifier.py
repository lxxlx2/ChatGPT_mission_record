"""Conservative user-level classification over immutable jsonParsed chain evidence."""
from collections import defaultdict
import re
from ..frank.parser import normalize, IncompleteTransaction, WSOL, INFRA_PROGRAMS, DEX_PROGRAMS, _program_id
from ..meme.holder_ranks import valid_pubkey
from .policy import USDC
from .multi_buy_proof import prove_direct_buys

USDT='Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
QUOTE_MINTS = frozenset({WSOL, USDC, USDT})
CHAIN_METADATA_REASONS = frozenset({
    'UNAVAILABLE_ON_PUBLIC_RPC','UNSUPPORTED_VERSION','MISSING_META_MESSAGE','JSON_PARSED_KEYS_REQUIRED',
    'WALLET_NOT_REFERENCED','BALANCE_VECTOR_INCOMPLETE','TOKEN_BALANCE_METADATA_MISSING',
    'INSTRUCTION_METADATA_MISSING','TOKEN_IDENTITY_CHANGED','TOKEN_OWNER_CHANGED','TOKEN_OWNER_MISSING',
    'FEE_MISSING','PROGRAM_INDEX_INVALID',
})

_BUY_INSTRUCTION_PREFIXES = ("swap", "route", "sharedaccountsroute", "buy")
_INVOKE = re.compile(r"Program ([1-9A-HJ-NP-Za-km-z]{32,44}) invoke \[([1-9][0-9]*)\]")
_SUCCESS = re.compile(r"Program ([1-9A-HJ-NP-Za-km-z]{32,44}) success")


def _outer_buy_indices(outer, names, logs):
    programs = [_program_id(ix, names) for ix in outer]
    explicit = {
        index for index, ix in enumerate(outer)
        if programs[index] in DEX_PROGRAMS and isinstance(ix.get("parsed"), dict)
        and str(ix["parsed"].get("type", "")).lower().startswith(_BUY_INSTRUCTION_PREFIXES)
    }
    roots, stack, observed = [], [], set()
    for log in logs:
        if not isinstance(log, str):
            return explicit
        if match := _INVOKE.fullmatch(log):
            program, depth = match.groups()
            if int(depth) != len(stack) + 1:
                return explicit
            if not stack:
                roots.append(program)
            stack.append(program)
        elif match := _SUCCESS.fullmatch(log):
            if not stack or stack.pop() != match[1]:
                return explicit
        elif (len(stack) == 1 and stack[0] in DEX_PROGRAMS
              and log.startswith("Program log: Instruction: ")
              and log.removeprefix("Program log: Instruction: ").lower().startswith(_BUY_INSTRUCTION_PREFIXES)):
            observed.add(len(roots) - 1)
    # Logs from incomplete or unaligned invocations cannot identify an outer index.
    return explicit | observed if not stack and roots == programs else explicit


def event_trades(event):
    """Return the independently attributed legs, including old single-trade events."""
    multi = event.get("trade_legs")
    if isinstance(multi, list):
        return multi
    trade = event.get("trade")
    return [trade] if isinstance(trade, dict) else []


def transaction_market_trades(event):
    """One model event for a Mint and transaction, with each purchase kept in evidence."""
    grouped = defaultdict(list)
    for trade in event_trades(event):
        grouped[trade["mint"]].append(trade)
    output = []
    for legs in grouped.values():
        if len(legs) == 1:
            output.append(legs[0])
            continue
        first = legs[0]
        paid = {(leg["quote_asset"], leg["quote_decimals"]) for leg in legs}
        same_quote = len(paid) == 1
        combined = {
            **first,
            "leg_index": None,
            "leg_indices": [leg["leg_index"] for leg in legs],
            "token_amount_raw": str(sum(int(leg["token_amount_raw"]) for leg in legs)),
        }
        if same_quote:
            raw = str(sum(int(leg["quote_amount_raw"]) for leg in legs))
            combined["quote_amount_raw"] = raw
            combined["quote_legs"] = [{"asset": first["quote_asset"], "raw_delta": "-" + raw,
                                      "decimals": first["quote_decimals"]}]
        else:
            combined["amount_predicate"] = "UNDETERMINED"
            combined["amount_predicate_reason"] = "MULTIPLE_SEGMENT_QUOTE_ASSETS"
            combined["quote_legs"] = [part for leg in legs for part in leg["quote_legs"]]
        output.append(combined)
    return output


def _independent_buy_legs(tx, evidence, outer, names, indices):
    if len(indices) < 2 or len(set(names)) != len(names):
        return None
    instructions = {}
    for group in tx["meta"]["innerInstructions"]:
        index = group["index"]
        if type(index) is not int or not 0 <= index < len(outer) or index in instructions:
            return None
        instructions[index] = group["instructions"]
    deltas = evidence["token_balance_deltas"]
    if any(type(row["account_index"]) is not int or not 0 <= row["account_index"] < len(names)
           for row in deltas):
        return None
    owned = {names[row["account_index"]]: row for row in deltas if row["wallet_owned"]}
    amounts = {address: int(row["pre_amount"]) for address, row in owned.items()}
    returned_to_wallet = {
        account["account"] for account in evidence["closed_token_accounts"]
        if account["destination"] == evidence["wallet"]
    }
    temporary = {
        account["account"]: account for account in evidence["decoded_transient_token_flows"]
        if account["account"] in returned_to_wallet and account["mint"] == WSOL
    }
    temporary_debits = defaultdict(list)
    wallet_flows = evidence.get("wallet_token_transfer_flows")
    if not isinstance(wallet_flows, list):
        return None
    flows = defaultdict(list)
    for flow in wallet_flows:
        index = flow.get("outer_index") if isinstance(flow, dict) else None
        if index not in indices or flow.get("scope") != "inner":
            return None
        flows[index].append(flow)

    trades = []
    for index in sorted(indices):
        legs = flows[index]
        direction = {flow["direction"]: flow for flow in legs}
        if len(legs) != 2 or set(direction) != {"IN", "OUT"}:
            return None
        bought, spent = direction["IN"], direction["OUT"]
        mint, quote = bought["mint"], spent["mint"]
        if not valid_pubkey(mint) or mint in QUOTE_MINTS or quote not in QUOTE_MINTS:
            return None
        target, source = bought["destination"], spent["source"]
        for flow, address, sign in ((bought, target, 1), (spent, source, -1)):
            token = owned.get(address)
            raw = int(flow["raw_amount"])
            if raw <= 0 or any(name not in names for name in (flow["source"], flow["destination"])):
                return None
            if sign == -1 and token is None and address in temporary and flow["mint"] == WSOL:
                if flow["decimals"] != 9:
                    return None
                temporary_debits[address].append({
                    "scope": "inner", "instruction": flow["instruction"], "delta": "-" + flow["raw_amount"],
                })
            elif (not token or token["mint"] != flow["mint"] or token["decimals"] != flow["decimals"]
                  or amounts[address] + sign * raw < 0):
                return None
        debit = instructions[index][spent["inner_index"]].get("parsed", {}).get("info", {})
        if debit.get("authority", debit.get("owner")) != evidence["wallet"]:
            return None
        before = amounts[target]
        amounts[target] += int(bought["raw_amount"])
        if source in amounts:
            amounts[source] -= int(spent["raw_amount"])
        quote_label = "SOL" if quote == WSOL else quote
        trades.append({
            "leg_index": index, "mint": mint, "direction": "BUY",
            "token_amount_raw": bought["raw_amount"], "token_decimals": bought["decimals"],
            "quote_asset": quote_label, "quote_amount_raw": spent["raw_amount"],
            "quote_decimals": spent["decimals"], "referenced_pre_raw": str(before),
            "referenced_post_raw": str(amounts[target]),
            "amount_predicate": "USDC_DIRECT_NUMERIC" if quote == USDC else "UNDETERMINED",
            "amount_predicate_reason": None if quote == USDC else "NON_USDC_QUOTE",
            "quote_legs": [{"asset": quote_label, "raw_delta": "-" + spent["raw_amount"],
                            "decimals": spent["decimals"]}],
            "route_intermediate_assets": [],
            "route_intermediate_evidence_status": "NO_INTERMEDIATE_TRANSFER_OBSERVED",
            "route_amount_semantics": "DIRECT_OR_SINGLE_TARGET_QUOTE",
            "instruction_evidence": {
                "program": _program_id(outer[index], names),
                "target_transfer": bought["instruction"], "payment_transfer": spent["instruction"],
            },
        })
    # Reconcile each wallet-owned account. Fees, internal transfers, or omitted
    # instructions may not silently be attributed to one of the independent buys.
    if any(amounts[address] != int(row["post_amount"]) for address, row in owned.items()):
        return None
    for row in evidence["decoded_transient_token_flows"]:
        debits = temporary_debits.get(row["account"], [])
        if debits != row["transfer_refs"] or sum(int(flow["delta"]) for flow in debits) != int(row["net_transfer_raw"]):
            return None
    return trades


def classify(signature, tx, wallet):
    base = {'signature': signature, 'wallet': wallet, 'slot': tx.get('slot'),
            'block_time': tx.get('blockTime'), 'classification': 'UNKNOWN_NEEDS_REVIEW',
            'classification_reason': 'INSUFFICIENT_MARKET_EXCHANGE_EVIDENCE',
            'frank_is_signer': False, 'frank_is_authority': False, 'trade': None}
    try:
        e = normalize(signature, tx, wallet)
    except (IncompleteTransaction, KeyError, TypeError, ValueError, IndexError) as exc:
        base['classification_reason'] = 'INCOMPLETE_CHAIN_METADATA:' + type(exc).__name__
        reason=str(exc) if isinstance(exc,IncompleteTransaction) and str(exc) in CHAIN_METADATA_REASONS else 'MALFORMED_CHAIN_METADATA'
        base['classification_details']={'chain_metadata_reason':reason}
        return base
    base.update(frank_is_signer=e['wallet_is_signer'],
                frank_is_authority=e['classification_evidence']['wallet_authority'], evidence=e)
    label = e['mechanical_classification']
    if e['tx_err'] is not None:
        base.update(classification='FAILED_TX', classification_reason='TRANSACTION_FAILED')
        return base
    groups = defaultdict(lambda: {'delta': 0, 'pre': 0, 'post': 0, 'decimals': None})
    for d in e['token_balance_deltas']:
        if not d['wallet_owned']: continue
        g = groups[d['mint']]
        if g['decimals'] is not None and g['decimals'] != d['decimals']:
            base['classification_reason']='WALLET_MINT_DECIMALS_CONFLICT'
            return base
        g.update(delta=g['delta']+int(d['delta']), pre=g['pre']+int(d['pre_amount']),
                 post=g['post']+int(d['post_amount']), decimals=d['decimals'])
    # Transient WSOL flow is decoded transfer evidence, never inferred from rent-inclusive SOL delta.
    for f in e['decoded_transient_token_flows']:
        g = groups[f['mint']]
        if g['decimals'] is not None and g['decimals'] != f['decimals']:
            base['classification_reason']='WALLET_MINT_DECIMALS_CONFLICT'
            return base
        g['delta'] += int(f['net_transfer_raw']); g['decimals'] = f['decimals']
    changed = {m:g for m,g in groups.items() if g['delta']}
    authority = e['wallet_is_signer']
    if label == 'ACTIVE_SWAP_LIKE' and authority:
        message = tx['transaction']['message']
        outer = message['instructions']
        names = [key['pubkey'] for key in message['accountKeys']]
        indices = _outer_buy_indices(outer, names, tx['meta'].get('logMessages') or [])
        if len(indices) > 1:
            legs = _independent_buy_legs(tx, e, outer, names, indices)
            if legs is not None:
                base.update(classification='ACTIVE_TRADE',
                            classification_reason='SIGNED_DEX_SEPARATELY_RECONCILED_BUY_INSTRUCTIONS',
                            trade_legs=legs)
                return base
    # Direct CPMM discriminator and CPI/account proof can still inform
    # research when the evidence for the ledger path is unavailable.
    buys = (prove_direct_buys(signature, tx, wallet, e)
            if authority and sum(m not in QUOTE_MINTS for m in changed)>1 else [])
    if (label == 'ACTIVE_SWAP_LIKE' or buys) and authority:
        tokens = [(m,g) for m,g in changed.items() if m not in QUOTE_MINTS]
        quotes = [(m,g) for m,g in changed.items() if m in QUOTE_MINTS]
        details={
            'changed_assets':[
                {'mint':m,'delta':str(g['delta']),'decimals':g['decimals']}
                for m,g in sorted(changed.items())
            ],
            'target_assets':[m for m,_ in tokens],
            'quote_assets':[m for m,_ in quotes],
        }
        # Multiple positive non-quote balances are economically multi-target at
        # the wallet boundary. Receive/spend conservation can identify a residual
        # flow candidate, but cannot prove user intent or bind that spend to the
        # other target without router/market-call level evidence. Keep such cases
        # fail-closed instead of collapsing them into a single ACTIVE_TRADE.
        if len(tokens)>1:
            # This evidence is intentionally not a single trade. The writer,
            # read model, and notifications retain their existing contract.
            if buys:
                details['independent_buy_legs'] = buys
                details['independent_buy_legs_scope'] = 'RESEARCH_ONLY_NO_LEDGER_TRADE_OR_DELIVERY'
            flow_by_mint=defaultdict(lambda:{'in_raw':0,'out_raw':0,'first_in':None,'first_out':None,'last_out':None})
            token_mints={m for m,_ in tokens}
            for flow in e.get('wallet_token_transfer_flows') or []:
                mint=flow.get('mint')
                if mint not in token_mints:continue
                try:raw=int(flow.get('raw_amount') or 0)
                except (TypeError,ValueError):continue
                order=(int(flow.get('outer_index',0)),int(flow.get('inner_index',-1)))
                item=flow_by_mint[mint]
                if flow.get('direction')=='IN':
                    item['in_raw']+=raw
                    if item['first_in'] is None or order<item['first_in']:item['first_in']=order
                elif flow.get('direction')=='OUT':
                    item['out_raw']+=raw
                    if item['first_out'] is None or order<item['first_out']:item['first_out']=order
                    if item['last_out'] is None or order>item['last_out']:item['last_out']=order
            created_mints={
                a.get('mint') for a in e.get('created_token_accounts') or []
                if a.get('owner')==wallet and a.get('mint')
            }
            residual_candidates=[]
            for mint,g in tokens:
                flow=flow_by_mint[mint]
                if (
                    mint in created_mints and g['pre']==0 and g['delta']>0
                    and flow['in_raw']>0 and flow['out_raw']>0
                    and flow['first_in'] is not None and flow['first_out'] is not None
                    and flow['first_in']<flow['first_out']
                    and flow['in_raw']-flow['out_raw']==g['delta']
                ):
                    residual_candidates.append({
                        'mint':mint,'net_delta':str(g['delta']),
                        'gross_in_raw':str(flow['in_raw']),'gross_out_raw':str(flow['out_raw']),
                        'first_in_order':list(flow['first_in']),'last_out_order':list(flow['last_out']),
                        'proof':'CREATED_ZERO_PRE_RECEIVED_THEN_SPENT_CONSERVED_RESIDUAL_ONLY',
                        'route_binding':'UNPROVEN',
                    })
            details['residual_flow_candidates']=residual_candidates
            base.update(
                classification_reason='AMBIGUOUS_USER_EXCHANGE_ASSETS',
                classification_details=details,
            )
            return base
        effective_tokens=tokens
        dex_indices = {index for index, instruction in enumerate(outer)
                       if _program_id(instruction, names) in DEX_PROGRAMS}
        observed_dex_indices = {flow.get('outer_index') for flow in e.get('wallet_token_transfer_flows') or []
                                if isinstance(flow, dict) and type(flow.get('outer_index')) is int
                                and flow['outer_index'] in dex_indices}
        if len(observed_dex_indices) > 1:
            base.update(classification_reason='AMBIGUOUS_USER_EXCHANGE_ASSETS',
                        classification_details={**details, 'candidate_buy_instruction_indices':sorted(observed_dex_indices)})
            return base
        if len(effective_tokens)==1 and quotes:
            mint,g=effective_tokens[0]
            opposing=[(m,q) for m,q in quotes if g['delta']*q['delta']<0]
            details['opposing_quote_assets']=[m for m,_ in opposing]
            if len(opposing)==1:
                quote,q=opposing[0]
                composite=len(quotes)>1
                amount_predicate='USDC_DIRECT_NUMERIC' if quote==USDC and not composite else 'UNDETERMINED'
                amount_reason=None
                if composite:amount_reason='COMPOSITE_QUOTE_LEGS'
                elif quote!=USDC:amount_reason='NON_USDC_QUOTE'
                quote_legs=[
                    {'asset':'SOL' if qm==WSOL else qm,'raw_delta':str(qg['delta']),'decimals':qg['decimals']}
                    for qm,qg in sorted(quotes,key=lambda x:x[0])
                ]
                # No observed wallet-owned transfer through an additional mint
                # supports a simple single-target quote for research. Missing
                # flow evidence or an additional non-target/quote mint is unresolved.
                flows=e.get('wallet_token_transfer_flows')
                route_mints=sorted({
                    flow.get('mint') for flow in (flows or [])
                    if isinstance(flow,dict) and flow.get('mint')
                    and flow['mint'] not in ({mint} | QUOTE_MINTS)
                })
                route_status=(
                    'UNVERIFIED' if flows is None or route_mints
                    else 'NO_INTERMEDIATE_TRANSFER_OBSERVED'
                )
                if route_status=='UNVERIFIED':
                    # Neither missing flow evidence nor an observed extra
                    # intermediate proves the final-target quote cost.
                    amount_predicate='UNDETERMINED'
                    amount_reason=('ROUTED_RESIDUAL_ASSETS' if route_mints
                                   else 'ROUTE_EVIDENCE_UNVERIFIED')
                base.update(
                    classification='ACTIVE_TRADE',
                    classification_reason=(
                        'SIGNED_DEX_SWAP_SINGLE_TARGET_PRIMARY_QUOTE_WITH_AUXILIARY_LEGS'
                        if composite else 'SIGNED_DEX_SWAP_OPPOSING_OWNED_FLOWS'
                    ),
                    classification_details=details,
                    trade={
                        'mint':mint,'direction':'BUY' if g['delta']>0 else 'SELL',
                        'token_amount_raw':str(abs(g['delta'])),'token_decimals':g['decimals'],
                        'quote_asset':'SOL' if quote==WSOL else quote,
                        'quote_amount_raw':str(abs(q['delta'])),'quote_decimals':q['decimals'],
                        'referenced_pre_raw':str(g['pre']),'referenced_post_raw':str(g['post']),
                        'amount_predicate':amount_predicate,'amount_predicate_reason':amount_reason,
                        'quote_legs':quote_legs,
                        'route_intermediate_assets':(
                            [{'mint':m} for m in route_mints] if route_mints
                            else None if flows is None else []
                        ),
                        'route_intermediate_evidence_status':route_status,
                        'route_amount_semantics':(
                            'GROSS_QUOTE_OUT_NOT_EXACT_FINAL_TARGET_COST'
                            if route_mints else 'DIRECT_OR_SINGLE_TARGET_QUOTE'
                        ),
                    },
                )
                return base
        base.update(
            classification_reason='AMBIGUOUS_USER_EXCHANGE_ASSETS',
            classification_details=details,
        )
        return base
    if label=='ACTIVE_SWAP_LIKE':
        base['classification_reason']='WALLET_NOT_SIGNER_AUTHORITY_UNPROVEN'
        return base
    passive = not e['wallet_is_signer'] and not e['classification_evidence']['wallet_authority']
    created = [a for a in e['created_token_accounts'] if a['owner']==wallet]
    keys=tx['transaction']['message']['accountKeys']
    owned_accounts={keys[d['account_index']]['pubkey'] for d in e['token_balance_deltas'] if d['wallet_owned']}
    instructions=list(tx['transaction']['message']['instructions'])
    for group in tx['meta']['innerInstructions']:instructions.extend(group['instructions'])
    inbound_transfer=False
    for ix in instructions:
        parsed=ix.get('parsed',{})
        if not isinstance(parsed,dict):continue
        info=parsed.get('info',{})
        if parsed.get('type') in ('transfer','transferChecked') and info.get('destination') in owned_accounts:
            inbound_transfer=True
    if passive and created and not changed and not e['native_incoming_transfer_evidence'] and set(e['program_ids'])<=INFRA_PROGRAMS:
        base.update(classification='ATA_CREATE',classification_reason='THIRD_PARTY_ATA_CREATE')
    elif passive and label=='PASSIVE_RECEIPT_LIKE' and (inbound_transfer or e['native_incoming_transfer_evidence']):
        base.update(classification='PASSIVE_TRANSFER',classification_reason='FRANK_NOT_SIGNER')
    elif label in ('TRANSFER_OUT_LIKE','TRANSFER_IN_LIKE'):
        base.update(classification='PASSIVE_TRANSFER',classification_reason='PLAIN_TRANSFER_NO_MARKET_EXCHANGE')
    elif e['wallet_is_fee_payer'] and not changed and set(e['program_ids'])<= {'ComputeBudget111111111111111111111111111111','MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'}:
        base.update(classification='FEE',classification_reason='FEE_ONLY')
    return base
