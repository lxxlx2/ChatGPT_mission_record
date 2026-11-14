"""Lossless foreground transaction prefetch, consumed through normal RPC logging.

Only the current source page is scheduled. Every result still traverses the
ordinary call/checkpoint path in signature order. A lost volatile suffix is
re-read after a crash; its HTTP reservation remains spent. Unsupported or failed
batches fall back to the existing individual read path, never to an empty page.
"""
import json
import time
import urllib.error
import urllib.request

OPTIONS = {'commitment': 'finalized', 'encoding': 'jsonParsed', 'maxSupportedTransactionVersion': 1}


def prepare(rpc, signatures, ttl):
    if not rpc.supports_transaction_batches: return
    if any(not isinstance(s, str) or not s or len(s) > 128 for s in signatures):
        raise ValueError('TRANSACTION_SIGNATURE_INVALID')
    rpc._transaction_plan = list(dict.fromkeys(signatures))
    rpc._transaction_prefetched = {}
    rpc._transaction_plan_ttl = ttl


def consume(rpc, method, params, ttl):
    if not rpc.supports_transaction_batches or method != 'getTransaction': return False, None
    if len(params) != 2 or params[1] != OPTIONS or ttl != rpc._transaction_plan_ttl: return False, None
    signature = params[0]
    if signature not in rpc._transaction_prefetched and signature in rpc._transaction_plan:
        start = rpc._transaction_plan.index(signature); selected = []; end = start
        for end in range(start, len(rpc._transaction_plan)):
            item = rpc._transaction_plan[end]
            cached = rpc.cache.get(method, [item, OPTIONS], time.time()) if ttl and rpc.cache else None
            if cached is None: selected.append(item)
            if len(selected) == 4: break
        rpc._transaction_plan = rpc._transaction_plan[end+1:]
        if len(selected) > 1: _fetch(rpc, selected)
    if signature not in rpc._transaction_prefetched: return False, None
    result = rpc._transaction_prefetched.pop(signature)
    rpc._check_job_deadline()
    if ttl and rpc.cache: rpc.cache.put(method, params, result, ttl, time.time())
    return True, result


def _fetch(rpc, signatures):
    rpc._check_job_budget(); endpoint = rpc._next_endpoint(); rpc._check_job_budget()
    timeout = 20.0
    if rpc.max_elapsed_seconds is not None:
        timeout = min(timeout, rpc.max_elapsed_seconds - (rpc._monotonic() - rpc._budget_started_at))
        if timeout <= 0: rpc._stop_job_budget('RPC_JOB_TIME_BUDGET_EXHAUSTED')
    body = [{'jsonrpc': '2.0', 'id': i+1, 'method': 'getTransaction', 'params': [s, OPTIONS]}
            for i, s in enumerate(signatures)]
    request = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers={
        'Content-Type': 'application/json', 'User-Agent': 'mission-meme-cluster/2'})
    # Same durable reservation hook as an individual HTTP wire attempt. It must
    # succeed before transport; it is outside recoverable source error handling.
    if rpc.before_wire is not None: rpc.before_wire(endpoint)
    rpc._last_by_endpoint[endpoint] = rpc._monotonic()
    rpc.calls += 1; rpc.endpoint_calls[endpoint] += 1
    rpc._transaction_batch_stats['http_batch_attempts'] += 1
    rpc._transaction_batch_stats['transaction_subrequests'] += len(signatures)
    rpc._last_wire_succeeded = False; rpc.last_wire_error_code = None
    try:
        with rpc.open_url(request, timeout=timeout) as response: payload = json.loads(response.read())
        rpc._check_job_deadline()
        if not isinstance(payload, list) or len(payload) != len(body): raise ValueError('RPC_BATCH_ENVELOPE_INVALID')
        indexed = {}
        for row in payload:
            if not isinstance(row, dict) or row.get('jsonrpc') != '2.0' or type(row.get('id')) is not int:
                raise ValueError('RPC_BATCH_ENVELOPE_INVALID')
            if row['id'] in indexed or not 1 <= row['id'] <= len(body) or ('result' in row) == ('error' in row):
                raise ValueError('RPC_BATCH_ENVELOPE_INVALID')
            indexed[row['id']] = row
        failed = False
        for i, signature in enumerate(signatures, 1):
            row = indexed[i]
            if 'error' in row:
                failed = True
                if rpc._rpc_rate_limited(row['error']):
                    rpc._cooldown_until[endpoint] = max(rpc._cooldown_until[endpoint], rpc._monotonic()+1.5)
                continue
            # Nulls retain the existing individual fallback/recovery behavior.
            if row['result'] is not None: rpc._transaction_prefetched[signature] = row['result']
        if failed:
            rpc.endpoint_failures[endpoint] += 1
            rpc._transaction_batch_stats['fallbacks'] += 1
            if all(isinstance(row.get('error'),dict) and row['error'].get('code') in {-32600,-32601,-32602} for row in indexed.values()):
                rpc._transaction_batches_disabled = True
        rpc._last_wire_succeeded = not failed
    except urllib.error.HTTPError as exc:
        rpc.last_wire_error_code = 'HTTP_'+str(exc.code)
        rpc.endpoint_failures[endpoint] += 1; rpc._transaction_batch_stats['fallbacks'] += 1
        rpc._cooldown_until[endpoint] = max(rpc._cooldown_until[endpoint], rpc._monotonic()+max(rpc._retry_after(exc), 1.5))
        if exc.code in {400, 403, 404, 405}: rpc._transaction_batches_disabled = True
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        rpc.last_wire_error_code = rpc._safe_wire_error_code(exc)
        rpc.endpoint_failures[endpoint] += 1; rpc._transaction_batch_stats['fallbacks'] += 1
        rpc._cooldown_until[endpoint] = max(rpc._cooldown_until[endpoint], rpc._monotonic()+1.0)
        # Invalid envelopes cannot be used as transaction evidence. Disable this
        # optional optimization for the job and read every item individually.
        if isinstance(exc, ValueError): rpc._transaction_batches_disabled = True
