#!/usr/bin/env python3
"""Strictly offline F0 L1 readiness audit for frozen watchlist EOAs and Router provenance.

Never opens sockets. Archived or synthetic getCode is not current authorization,
can prove only code at a pinned block (not control of key, actual EOA, or swap).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from f0_l1_window import FROZEN_PR116_BLOB, load_frozen_cohort, cohort_watchlist
from f0_rpc_adapter import address, envelope, hexnum, digest

SCHEMA = 'bsc-f0-l1-eoa-router-preflight-v1'
CODE_METHOD = 'eth_getCode'
MODES = {'OFFLINE_SYNTHETIC_ONLY', 'SAVED_RPC_USER_ORIGIN_UNVERIFIED'}
ROUTER_MODE = 'OFFICIAL_DOCUMENTED_ADDRESSES_CODE_NOT_VERIFIED'


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def official_router_addresses(registry: dict) -> tuple[str, ...]:
    require(isinstance(registry, dict) and registry.get('schema') ==
            'bsc-f0-official-router-source-candidates-v1' and registry.get('chain_id') == 56,
            'ROUTER_REGISTRY_INVALID')
    require(registry.get('source_status') == ROUTER_MODE and
            registry.get('onchain_code_verified') is False and
            registry.get('control_eligible') is False, 'ROUTER_PREMATURE_APPROVAL')
    rows = registry.get('routers')
    require(isinstance(rows, list) and len(rows) == 2, 'ROUTER_REGISTRY_SCOPE')
    expected = {
        'v3_universal': '0x1a0a18ac4becddbd6389559687d1a73d8927e416',
        'infinity_universal': '0xd9c500dff816a1da21a48a732d3498bf09dc9aeb',
    }
    seen = set()
    for row in rows:
        require(isinstance(row, dict) and row.get('family') in expected and
                row.get('family') not in seen and
                address(row.get('address')) == expected[row['family']] and
                row.get('official_source') ==
                'https://developer.pancakeswap.finance/contracts/universal-router/addresses' and
                row.get('onchain_runtime_code_check') == 'NOT_PERFORMED' and
                row.get('swap_causality_attested') is False,
                'ROUTER_SOURCE_OR_ADDRESS_MISMATCH')
        seen.add(row['family'])
    require(seen == set(expected), 'ROUTER_REGISTRY_INCOMPLETE')
    return tuple(sorted(expected.values()))


def decode_code_observation(item: dict, *, height: int, wallet: str) -> dict:
    require(isinstance(item, dict), 'CODE_OBSERVATION_INVALID')
    require(item.get('method') == CODE_METHOD and item.get('params') ==
            [wallet, hex(height)] and item.get('chain_id') == 56,
            'CODE_REQUEST_IDENTITY_MISMATCH')
    require(type(item.get('id')) is int and item['id'] > 0,
            'CODE_REQUEST_ID_INVALID')
    if 'transport_error_code' in item:
        # A real sender may persist a failed attempt with no RPC envelope.
        # This is SAVED input, never proof the remote provider billed a call.
        require(item.get('rpc') is None and item.get('attempted') is True and
                item['transport_error_code'] in
                ('NETWORK_TIMEOUT', 'NETWORK_ERROR', 'HTTP_ERROR',
                 'RESPONSE_TOO_LARGE'), 'TRANSPORT_FAILURE_INVALID')
        return {
            'wallet': wallet,
            'observed_code_state': 'TRANSPORT_FAILED_AT_SAMPLED_BLOCK',
            'response_sha256': None, 'checked_block': height,
            'failure_code': item['transport_error_code'],
            'rpc_error_code': None,
            'real_eoa_attested': False, 'wallet_live_eligible': False,
        }
    resp = item.get('rpc')
    require(isinstance(resp, dict) and resp.get('id') == item['id'] and
            resp.get('jsonrpc') == '2.0', 'CODE_RESPONSE_IDENTITY_MISMATCH')
    if resp.get('error') is not None:
        err = resp['error']
        require(isinstance(err, dict) and type(err.get('code')) is int and
                ('result' not in resp or resp['result'] is None),
                'MALFORMED_RPC_ERROR_ENVELOPE')
        return {
            'wallet': wallet,
            'observed_code_state': 'RPC_ERROR_AT_SAMPLED_BLOCK',
            'response_sha256': digest(resp), 'checked_block': height,
            'failure_code': 'RPC_ERROR', 'rpc_error_code': err['code'],
            'real_eoa_attested': False, 'wallet_live_eligible': False,
        }
    code = envelope(resp)
    require(isinstance(code, str) and code.startswith('0x') and
            len(code) % 2 == 0 and all(v in '0123456789abcdefABCDEF' for v in code[2:]),
            'INVALID_RETURNED_CODE_HEX')
    return {
        'wallet': wallet,
        'observed_code_state': 'NO_CODE_AT_SAMPLED_BLOCK' if len(code) == 2
            else 'HAS_RUNTIME_CODE_AT_SAMPLED_BLOCK',
        'response_sha256': digest(resp),
        'checked_block': height,
        'failure_code': None, 'rpc_error_code': None,
        'real_eoa_attested': False,
        'wallet_live_eligible': False,
    }


def audit_offline(cohort: dict, code_snapshot: dict, registry: dict) -> dict:
    """Caller must explicitly label cohort as fixture vs proven blob. The CLI
    gates real-mode cohort bytes before entering this pure offline ledger.
    """
    routers = official_router_addresses(registry)
    watched, meta = cohort_watchlist(cohort)
    require(isinstance(code_snapshot, dict) and code_snapshot.get('schema') == SCHEMA and
            code_snapshot.get('mode') in MODES and code_snapshot.get('chain_id') == 56 and
            code_snapshot.get('store_raw_payloads') is False,
            'OFFLINE_SNAPSHOT_REQUIRED')
    require('user_authorized' not in code_snapshot and
            code_snapshot.get('actual_rpc_calls') == 0,
            'LIVE_NETWORK_CLAIM_FORBIDDEN')
    h = code_snapshot.get('checked_block')
    require(type(h) is int and h > 0, 'INVALID_FROZEN_HEIGHT')
    rows = code_snapshot.get('observations')
    require(isinstance(rows, list) and len(rows) <= 20, 'TOO_MANY_CODE_OBSERVATIONS')
    checked = {}
    for item in rows:
        w = address(item.get('wallet'))
        require(w in watched and w not in checked,
                'CODE_OUTSIDE_FROZEN_PRIMARY_OR_DUPLICATE')
        checked[w] = decode_code_observation(item, height=h, wallet=w)
    result = []
    for w in sorted(watched):
        result.append(checked.get(w, {
            'wallet': w, 'observed_code_state': 'NOT_CHECKED',
            'response_sha256': None, 'checked_block': None,
            'real_eoa_attested': False, 'wallet_live_eligible': False,
        }))
    cnt = {state: sum(x['observed_code_state'] == state for x in result)
           for state in ['NOT_CHECKED', 'NO_CODE_AT_SAMPLED_BLOCK',
                         'HAS_RUNTIME_CODE_AT_SAMPLED_BLOCK',
                         'RPC_ERROR_AT_SAMPLED_BLOCK',
                         'TRANSPORT_FAILED_AT_SAMPLED_BLOCK']}
    require(sum(cnt.values()) == meta['primary_count'] == 20,
            'CODE_ATTEMPT_DENOMINATOR_MISMATCH')
    return {
        'schema': SCHEMA,
        'mode': 'OFFLINE_PRECHECK_NOT_LIVE_ELIGIBILITY',
        'snapshot_source': code_snapshot['mode'],
        'cohort_source': 'CALLER_MUST_REPORT_FROZEN_BLOB_EVIDENCE',
        'frozen_pr116_manifest_blob': FROZEN_PR116_BLOB,
        'requested_height': h,
        'primary_count': meta['primary_count'],
        'per_primary': result,
        'counts': cnt,
        'saved_getcode_attempts': len(rows),
        'saved_getcode_rpc_errors': cnt['RPC_ERROR_AT_SAMPLED_BLOCK'],
        'saved_getcode_transport_failures': cnt['TRANSPORT_FAILED_AT_SAMPLED_BLOCK'],
        'saved_getcode_success_responses': cnt['NO_CODE_AT_SAMPLED_BLOCK'] +
            cnt['HAS_RUNTIME_CODE_AT_SAMPLED_BLOCK'],
        'saved_getcode_not_checked': cnt['NOT_CHECKED'],
        'saved_attempts_provider_billed': 'UNVERIFIED',
        'source_envelope_sha256': digest(code_snapshot),
        'router_documented_candidates': list(routers),
        'router_registry_source_only': True,
        'router_onchain_code_verified': False,
        'router_swap_causality_verified': False,
        'real_technical_eoa_eligibility': 'NOT_ESTABLISHED',
        'live_watchlist_enabled': False,
        'live_control_enabled': False,
        'actual_rpc_calls': 0,
        'stop_state': 'NO_RUN',
    }


def audit_frozen_raw(raw: bytes, snapshot: dict, registry: dict) -> dict:
    cohort = load_frozen_cohort(raw)
    report = audit_offline(cohort, snapshot, registry)
    report['cohort_source'] = 'VERIFIED_PR116_BLOB_OFFLINE'
    return report


def main() -> None:
    p = argparse.ArgumentParser(description='OFFLINE ONLY: audit archived getCode and official Router source list')
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--snapshot', type=Path, required=True)
    p.add_argument('--router-registry', type=Path, required=True)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    report = audit_frozen_raw(args.manifest.read_bytes(),
                              json.loads(args.snapshot.read_text()),
                              json.loads(args.router_registry.read_text()))
    out = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.report:
        args.report.write_text(out)
    else:
        print(out, end='')


if __name__ == '__main__':
    main()
