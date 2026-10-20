#!/usr/bin/env python3
"""Fixed-scope, one-shot BSC getCode probe. OFFLINE by default; NO AUTHORITY to run live.

No polling, retries, WS, trade, quote, transaction, account credentials or side effects
beyond explicitly approved local audit files. Live execution needs a separately
approved *concrete* permit, matching reviewed commit and a fresh one-use nonce.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from f0_bounded_smoke import (ENDPOINT, https_sender, verify_code_binding,
                              consume_nonce, permit_audit_fields, utc)
from f0_l1_preflight import (SCHEMA as PREFLIGHT_SCHEMA, audit_frozen_raw,
                             audit_offline, official_router_addresses,
                             decode_code_observation)
from f0_l1_window import (FROZEN_PR116_BLOB, load_frozen_cohort,
                          cohort_watchlist, git_blob_sha1)
from f0_rpc_adapter import address

SCHEMA = 'bsc-f0-l1-one-shot-code-qualification-probe-v1'
SCOPE = 'ONE_TIME_BSC_F0_24_PUBLIC_HTTP_GETCODE_QUALIFICATION_ONLY'
METHODS = ('eth_chainId', 'eth_blockNumber', 'eth_getCode')
MAX_CALLS = 24
MAX_WALLETS = 20
MAX_ROUTERS = 2
MAX_BYTES = 2_000_000
MAX_FAILURE_STREAK = 3
DEPENDENCIES = ('f0_l1_preflight.py', 'f0_l1_window.py', 'f0_offline_collector.py',
                'f0_rpc_adapter.py',
                'f0_bounded_smoke.py', 'F0_COHORT_PRESELECTION.json',
                'F0_ROUTER_SOURCE_CANDIDATES.json')
TRANSPORT_ERRORS = frozenset(('NETWORK_TIMEOUT', 'NETWORK_ERROR',
                              'HTTP_ERROR', 'RESPONSE_TOO_LARGE'))


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_qualification_permit(permit: dict, now: datetime) -> None:
    """Programmatic restrictions, NOT proof of user approval."""
    require(isinstance(permit, dict), 'PERMIT_REQUIRED')
    require(permit.get('scope') == SCOPE and permit.get('user_authorized') is True,
            'QUALIFICATION_AUTHORIZATION_REQUIRED')
    require(permit.get('approved_endpoint') == ENDPOINT and
            permit.get('methods') == list(METHODS), 'QUALIFICATION_SOURCE_NOT_APPROVED')
    require(permit.get('chain_id') == 56 and
            permit.get('cost_policy') == 'FREE_ONLY_NO_PAYMENT' and
            permit.get('local_environment') == 'USER_MAC_LOCAL_ONLY',
            'QUALIFICATION_COST_OR_ENVIRONMENT_NOT_APPROVED')
    require(type(permit.get('max_total_rpc_calls')) is int and
            permit['max_total_rpc_calls'] == MAX_CALLS and
            type(permit.get('max_wallet_getcode_calls')) is int and
            permit['max_wallet_getcode_calls'] == MAX_WALLETS and
            type(permit.get('max_router_getcode_calls')) is int and
            permit['max_router_getcode_calls'] == MAX_ROUTERS,
            'QUALIFICATION_BUDGET_NOT_APPROVED')
    require(type(permit.get('max_response_bytes')) is int and
            0 < permit['max_response_bytes'] <= MAX_BYTES, 'QUALIFICATION_RESPONSE_CAP')
    require(permit.get('no_retries') is True and permit.get('no_ws') is True and
            permit.get('store_raw_payloads') is False and
            permit.get('background') is False,
            'QUALIFICATION_UNAPPROVED_FEATURE')
    require(type(permit.get('retention_hours')) is int and
            1 <= permit['retention_hours'] <= 24, 'QUALIFICATION_RETENTION_INVALID')
    root = permit.get('storage_root')
    require(isinstance(root, str) and root.startswith('/tmp/') and
            '..' not in Path(root).parts, 'QUALIFICATION_STORAGE_INVALID')
    start, end = utc(permit.get('window_start_utc')), utc(permit.get('window_end_utc'))
    require(timedelta(0) < end-start <= timedelta(minutes=10) and
            start <= now <= end, 'QUALIFICATION_WINDOW_INVALID')
    # Reuse reviewed script + SHA + nonce field validation, without inheriting
    # the unrelated old 4-call smoke scope, which is permanently spent.
    from f0_bounded_smoke import HASH40, HASH64, NONCE
    require(isinstance(permit.get('approved_commit_sha'), str) and
            HASH40.fullmatch(permit['approved_commit_sha']) is not None,
            'QUALIFICATION_REVIEWED_COMMIT_REQUIRED')
    require(isinstance(permit.get('approved_source_sha256'), str) and
            HASH64.fullmatch(permit['approved_source_sha256']) is not None,
            'QUALIFICATION_REVIEWED_SOURCE_REQUIRED')
    require(isinstance(permit.get('run_nonce'), str) and
            NONCE.fullmatch(permit['run_nonce']) is not None,
            'QUALIFICATION_ONE_TIME_NONCE_REQUIRED')
    require(permit.get('approved_manifest_blob') == FROZEN_PR116_BLOB,
            'QUALIFICATION_FROZEN_MANIFEST_REQUIRED')
    require(type(permit.get('min_interval_ms')) is int and
            100 <= permit['min_interval_ms'] <= 1000,
            'QUALIFICATION_RATE_CAP_INVALID')


def verify_loaded_sources(permit: dict, script: Path) -> None:
    """Verify all actual imported code and registries equal *reviewed* Git bytes.

    A script-only check is insufficient because Python imports can change.
    No fetch, no network, no Git mutation. This intentionally rejects archives
    outside a real Git checkout and rejects altered dependency working files.
    """
    verify_code_binding(permit, script)
    try:
        root = Path(subprocess.run(
            ['git', '-C', str(script.parent), 'rev-parse', '--show-toplevel'],
            check=True, capture_output=True, text=True, timeout=5,
        ).stdout.strip()).resolve()
        for filename in DEPENDENCIES:
            path = (script.parent / filename).resolve(strict=True)
            relative = path.relative_to(root).as_posix()
            reviewed = subprocess.run(['git', '-C', str(root), 'show',
                                       'HEAD:' + relative], check=True,
                                      capture_output=True, timeout=5).stdout
            require(path.read_bytes() == reviewed, 'UNREVIEWED_PROBE_DEPENDENCY')
    except (OSError, subprocess.SubprocessError, ValueError):
        raise ValueError('QUALIFICATION_DEPENDENCY_CHECK_FAILED') from None


def bounded_report_path(out: Path, root: Path, *, expected_name: str = 'report.json') -> Path:
    """Distinct reserved filenames prevent a final report replacing an attempt journal.

    The default is for the final report; journal usage must name the role
    explicitly. This validation runs before nonce consumption or any RPC.
    """
    require(expected_name in ('report.json', 'journal.json') and
            out.name == expected_name and
            out.parent.resolve() == root.resolve() and
            not out.is_symlink(),
            'QUALIFICATION_REPORT_OUTSIDE_APPROVED_STORAGE')
    return out


def fsync_directory(directory: Path) -> None:
    """Commit directory entries before a persisted attempt may reach a sender."""
    flags = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0)
    fd = os.open(directory, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(out: Path, data: dict) -> None:
    """Fsync + atomic replace, no readable credentials, no raw RPC errors."""
    require(not out.is_symlink(), 'OUTPUT_SYMLINK_FORBIDDEN')
    temp = out.with_name(out.name + '.tmp.' + str(os.getpid()))
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    fd = os.open(temp, flags, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as dest:
            json.dump(data, dest, sort_keys=True, indent=2)
            dest.write('\n')
            dest.flush()
            os.fsync(dest.fileno())
        os.replace(temp, out)
        fsync_directory(out.parent)
    finally:
        if temp.exists():
            temp.unlink()


def transport_error(exc: Exception) -> str:
    if isinstance(exc, (TimeoutError,)):
        return 'NETWORK_TIMEOUT'
    if isinstance(exc, urllib.error.HTTPError):
        return 'HTTP_ERROR'
    if isinstance(exc, (urllib.error.URLError, ConnectionError, OSError)):
        return 'NETWORK_ERROR'
    if isinstance(exc, ValueError) and str(exc) == 'RESPONSE_TOO_LARGE':
        return 'RESPONSE_TOO_LARGE'
    return 'INVALID_SOURCE_RESPONSE'


class AttemptJournal:
    def __init__(self, path: Path | None, max_calls: int, *, mode: str):
        self.path = path
        self.limit = max_calls
        self.rows: list[dict] = []
        self.mode = mode

    def persist(self) -> None:
        if self.path is not None:
            atomic_json(self.path, {'schema': SCHEMA, 'mode': self.mode,
                                    'attempted_rpc_calls': len(self.rows),
                                    'attempts': self.rows,
                                    'provider_billed': 'UNVERIFIED'})

    def begin(self, method: str, params: list, category: str) -> int:
        require(len(self.rows) < self.limit, 'QUALIFICATION_REQUEST_CAP_REACHED')
        require(method in METHODS, 'QUALIFICATION_METHOD_FORBIDDEN')
        if method == 'eth_getCode':
            require(category in ('PRIMARY_CODE', 'ROUTER_CODE'),
                    'QUALIFICATION_METHOD_CATEGORY_MISMATCH')
        else:
            require(category == 'SOURCE_IDENTITY',
                    'QUALIFICATION_METHOD_CATEGORY_MISMATCH')
        item = {'index': len(self.rows) + 1, 'method': method,
                'category': category, 'params': params,
                'requested_utc': datetime.now(timezone.utc).isoformat(),
                'requested_monotonic_ns': time.monotonic_ns(),
                'state': 'ATTEMPTED_OUTCOME_UNKNOWN'}
        self.rows.append(item)
        self.persist()  # BEFORE sender - ensures failed and interrupted calls count.
        return item['index']

    def end(self, index: int, state: str, response_sha: str | None = None,
            failure_code: str | None = None) -> None:
        entry = self.rows[index-1]
        entry.update(state=state, response_sha256=response_sha,
                     failure_code=failure_code,
                     completed_utc=datetime.now(timezone.utc).isoformat(),
                     completed_monotonic_ns=time.monotonic_ns())
        self.persist()


class QualificationClient:
    def __init__(self, sender: Callable, journal: AttemptJournal,
                 cap: int, *, interval_ms: int = 0, sleep: Callable = time.sleep,
                 deadline: datetime | None = None, now: Callable = lambda: datetime.now(timezone.utc)):
        self.sender, self.journal = sender, journal
        self.cap, self.interval_ms, self.sleep = cap, interval_ms, sleep
        self.deadline, self.now = deadline, now

    def call(self, method: str, params: list, category: str) -> tuple[dict | None, str | None, int]:
        if self.interval_ms and self.journal.rows:
            self.sleep(self.interval_ms / 1000)
        require(self.deadline is None or self.now() <= self.deadline,
                'QUALIFICATION_WINDOW_EXPIRED_BEFORE_REQUEST')
        idx = self.journal.begin(method, params, category)
        payload = {'jsonrpc': '2.0', 'id': idx, 'method': method, 'params': params}
        try:
            row = self.sender(ENDPOINT, payload, self.cap)
        except Exception as exc:
            code = transport_error(exc)
            self.journal.end(idx, 'TRANSPORT_FAILED', failure_code=code)
            return None, code, idx
        if (not isinstance(row, dict) or row.get('jsonrpc') != '2.0' or
                row.get('id') != idx or
                ('error' not in row and 'result' not in row)):
            self.journal.end(idx, 'INVALID_RESPONSE', failure_code='INVALID_RPC_ENVELOPE')
            return None, 'INVALID_SOURCE_RESPONSE', idx
        from f0_rpc_adapter import digest
        self.journal.end(idx, 'RPC_RESPONSE', response_sha=digest(row))
        return row, None, idx


def source_quantity(response: dict | None, failure: str | None,
                    expected: str) -> int:
    require(response is not None and failure is None and response.get('error') is None,
            'QUALIFICATION_IDENTITY_SOURCE_UNAVAILABLE')
    result = response.get('result')
    require(isinstance(result, str) and result.startswith('0x') and
            len(result) > 2 and all(ch in '0123456789abcdefABCDEF' for ch in result[2:]),
            'QUALIFICATION_INVALID_SOURCE_QUANTITY')
    n = int(result, 16)
    if expected == 'chain':
        require(n == 56, 'QUALIFICATION_WRONG_CHAIN')
    else:
        require(n > 0, 'QUALIFICATION_NO_HEAD')
    return n


def source_count(journal: AttemptJournal, category: str) -> int:
    return sum(item['category'] == category for item in journal.rows)


def probe(sender: Callable, cohort: dict, registry: dict,
          *, manifest_raw: bytes | None = None, cap: int = MAX_BYTES,
          journal: AttemptJournal | None = None, interval_ms: int = 0,
          sleep: Callable = time.sleep, strict_frozen: bool = False,
          deadline: datetime | None = None, now: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    """Deterministic plan with injectable sender; no network unless caller injects it."""
    if strict_frozen:
        require(manifest_raw is not None and
                load_frozen_cohort(manifest_raw) == cohort,
                'QUALIFICATION_REAL_COHORT_MISSING_OR_CHANGED')
    else:
        require(cohort.get('synthetic_fixture_only') is True,
                'QUALIFICATION_OFFLINE_FIXTURE_REQUIRED')
    watched, meta = cohort_watchlist(cohort)
    routers = official_router_addresses(registry)
    require(len(watched) == MAX_WALLETS and len(routers) == MAX_ROUTERS,
            'QUALIFICATION_SCOPE_MISMATCH')
    journal = journal or AttemptJournal(None, MAX_CALLS, mode='OFFLINE_INJECTED_SENDER')
    client = QualificationClient(sender, journal, cap, interval_ms=interval_ms,
                                 sleep=sleep, deadline=deadline, now=now)
    snapshot = {'schema': PREFLIGHT_SCHEMA, 'mode': 'SAVED_RPC_USER_ORIGIN_UNVERIFIED'
                if strict_frozen else 'OFFLINE_SYNTHETIC_ONLY',
                'chain_id': 56, 'store_raw_payloads': False, 'actual_rpc_calls': 0,
                'checked_block': 1, 'observations': []}
    router_rows = []
    stop = 'QUALIFICATION_READS_COMPLETE_NOT_LIVE_MONITORING'
    fatal_code = None
    # Only a validated eth_blockNumber is an observed height. The offline saved
    # parser uses an internal placeholder for early-stop reports; never expose
    # that placeholder as the actually confirmed block height.
    confirmed_height = None
    try:
        row, err, _ = client.call('eth_chainId', [], 'SOURCE_IDENTITY')
        source_quantity(row, err, 'chain')
        row, err, _ = client.call('eth_blockNumber', [], 'SOURCE_IDENTITY')
        height = source_quantity(row, err, 'height')
        confirmed_height = height
        snapshot['checked_block'] = height
        failure_streak = 0
        for category, wallets in [('PRIMARY_CODE', sorted(watched)),
                                  ('ROUTER_CODE', sorted(routers))]:
            for wallet in wallets:
                require(source_count(journal, category) < (MAX_WALLETS if category == 'PRIMARY_CODE'
                                                           else MAX_ROUTERS),
                        'QUALIFICATION_CATEGORY_CAP_REACHED')
                row, err, idx = client.call('eth_getCode', [wallet, hex(height)], category)
                obs = {'wallet': wallet, 'method': 'eth_getCode',
                       'params': [wallet, hex(height)], 'chain_id': 56, 'id': idx,
                       'rpc': row}
                if err:
                    if err not in TRANSPORT_ERRORS:
                        stop, fatal_code = 'BLOCKED_SOURCE', 'INVALID_SOURCE_RESPONSE'
                        break
                    obs.update(attempted=True, transport_error_code=err)
                try:
                    decoded = decode_code_observation(obs, height=height, wallet=wallet)
                except (ValueError, KeyError, TypeError):
                    stop, fatal_code = 'BLOCKED_SOURCE', 'INVALID_SAVED_CODE_OBSERVATION'
                    break
                if category == 'PRIMARY_CODE':
                    snapshot['observations'].append(obs)
                else:
                    router_rows.append({'router': wallet, 'code_state': decoded['observed_code_state'],
                                        'response_sha256': decoded['response_sha256'],
                                        'failure_code': decoded.get('failure_code'),
                                        'code_at_sampled_block_only': True,
                                        'control_eligible': False})
                failure_streak = failure_streak + 1 if decoded['observed_code_state'] in (
                    'RPC_ERROR_AT_SAMPLED_BLOCK', 'TRANSPORT_FAILED_AT_SAMPLED_BLOCK') else 0
                if failure_streak >= MAX_FAILURE_STREAK:
                    stop, fatal_code = 'BLOCKED_SOURCE', 'THREE_CONSECUTIVE_SOURCE_FAILURES'
                    break
            if stop == 'BLOCKED_SOURCE':
                break
    except (ValueError, KeyError, TypeError):
        stop, fatal_code = 'BLOCKED_SOURCE', 'QUALIFICATION_SOURCE_IDENTITY_OR_SCHEMA_FAILED'
    report = (audit_frozen_raw(manifest_raw, snapshot, registry) if strict_frozen
              else audit_offline(cohort, snapshot, registry))
    # audit_offline is deliberately a SAVED input parser, and does zero RPC of its own.
    report.update(schema=SCHEMA, mode='AUTHORIZED_READ_ONLY_QUALIFICATION'
                  if strict_frozen else 'OFFLINE_SYNTHETIC_READ_ONLY_QUALIFICATION',
                  checked_block=confirmed_height,
                  stop_state=stop, error_code=fatal_code,
                  attempt_ledger_status='DURABLE_BEFORE_EACH_SEND' if journal.path
                  else 'IN_MEMORY_OFFLINE_ONLY',
                  attempted_rpc_calls=len(journal.rows),
                  attempted_primary_getcode=source_count(journal, 'PRIMARY_CODE'),
                  attempted_router_getcode=source_count(journal, 'ROUTER_CODE'),
                  attempted_identity_reads=source_count(journal, 'SOURCE_IDENTITY'),
                  router_code_observations=router_rows,
                  router_onchain_code_verified=False,
                  live_watchlist_enabled=False, live_control_enabled=False,
                  first_actionable_latency='NOT_MEASURED',
                  independent_control_denominator='NOT_MEASURED',
                  e1_finality='UNRESOLVED_F1_POLICY', e2_attested=False,
                  e3_actual_count=0, quoted_actual_count=0,
                  paper_profit_labels=0, provider_billed='UNVERIFIED')
    report['unreconciled_attempts'] = (
        report['attempted_rpc_calls'] - report['attempted_identity_reads'] -
        report['saved_getcode_attempts'] - len(router_rows))
    return report


def fixture_sender(responses: dict) -> Callable:
    require(isinstance(responses, dict) and
            responses.get('mode') == 'OFFLINE_SYNTHETIC_ONLY' and
            responses.get('trial') is True, 'UNMARKED_FIXTURE_FORBIDDEN')
    items = responses['responses']
    require(isinstance(items, list), 'INVALID_FIXTURE_RESPONSES')
    i = 0
    def send(endpoint: str, payload: dict, cap: int) -> dict:
        nonlocal i
        require(endpoint == ENDPOINT and i < len(items), 'FIXTURE_EXHAUSTED')
        expected = items[i]
        i += 1
        require(expected['method'] == payload['method'] and
                expected['params'] == payload['params'], 'FIXTURE_SEQUENCE_MISMATCH')
        value = expected.get('result')
        row = {'jsonrpc': '2.0', 'id': payload['id']}
        if 'error' in expected:
            row['error'] = expected['error']
        else:
            row['result'] = value
        require(len(json.dumps(row).encode()) <= cap, 'RESPONSE_TOO_LARGE')
        return row
    return send


def main() -> None:
    parser = argparse.ArgumentParser(description='BSC getCode 24-read qualification; OFFLINE unless independent approval')
    parser.add_argument('--fixture', type=Path)
    parser.add_argument('--execute-live', action='store_true')
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--router-registry', type=Path, required=True)
    parser.add_argument('--permit', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    require(bool(args.fixture) != bool(args.execute_live), 'EXACTLY_ONE_MODE_REQUIRED')
    manifest = args.manifest.read_bytes()
    registry = json.loads(args.router_registry.read_text())
    if args.fixture:
        require(args.permit is None, 'PERMIT_NOT_ALLOWED_OFFLINE')
        cohort = json.loads(manifest)
        result = probe(fixture_sender(json.loads(args.fixture.read_text())),
                       cohort, registry)
        result['actual_rpc_calls'] = 0
    else:
        require(args.permit is not None and args.report is not None,
                'QUALIFICATION_PERMIT_AND_REPORT_REQUIRED')
        permit = json.loads(args.permit.read_text())
        validate_qualification_permit(permit, datetime.now(timezone.utc))
        root = Path(permit['storage_root']).resolve()
        require(root.is_relative_to(Path('/tmp').resolve()),
                'QUALIFICATION_STORAGE_OUTSIDE_TMP')
        out = bounded_report_path(args.report, root)
        journal_path = bounded_report_path(root / 'journal.json', root,
                                           expected_name='journal.json')
        require(out.resolve(strict=False) != journal_path.resolve(strict=False),
                'QUALIFICATION_REPORT_JOURNAL_CONFLICT')
        script = Path(__file__).resolve()
        require(args.manifest.resolve() == script.parent / 'F0_COHORT_PRESELECTION.json' and
                args.router_registry.resolve() == script.parent / 'F0_ROUTER_SOURCE_CANDIDATES.json',
                'QUALIFICATION_INPUT_PATH_NOT_APPROVED')
        require(git_blob_sha1(manifest) == FROZEN_PR116_BLOB,
                'QUALIFICATION_FROZEN_MANIFEST_REQUIRED')
        cohort = load_frozen_cohort(manifest)
        official_router_addresses(registry)
        verify_loaded_sources(permit, script)
        require(not journal_path.exists() and not out.exists(),
                'QUALIFICATION_REPORT_ALREADY_EXISTS')
        consume_nonce(permit, root)
        journal = AttemptJournal(journal_path, MAX_CALLS, mode='ONE_SHOT_USER_APPROVED')
        try:
            result = probe(https_sender, cohort, registry,
                           manifest_raw=manifest,
                           cap=permit['max_response_bytes'],
                           journal=journal,
                           interval_ms=permit['min_interval_ms'],
                           strict_frozen=True,
                           deadline=utc(permit['window_end_utc']))
        except Exception:
            # Unexpected errors must not erase a durable pre-send attempt journal.
            result = {'schema': SCHEMA, 'mode': 'AUTHORIZED_SOURCE_FAILED_CLOSED',
                      'attempted_rpc_calls': len(journal.rows),
                      'error_code': 'QUALIFICATION_UNEXPECTED_ERROR',
                      'stop_state': 'BLOCKED_SOURCE',
                      'provider_billed': 'UNVERIFIED',
                      'live_watchlist_enabled': False,
                      'live_control_enabled': False}
        result.update(permit_audit_fields(permit))
        # Number of attempts, NOT provider-billed calls.
        result['actual_rpc_calls'] = len(journal.rows)
        atomic_json(out, result)
        if result['stop_state'] != 'QUALIFICATION_READS_COMPLETE_NOT_LIVE_MONITORING':
            raise SystemExit(1)
    text = json.dumps(result, sort_keys=True, indent=2) + '\n'
    if args.report and args.fixture:
        args.report.write_text(text)
    elif not args.execute_live:
        print(text, end='')


if __name__ == '__main__':
    main()
