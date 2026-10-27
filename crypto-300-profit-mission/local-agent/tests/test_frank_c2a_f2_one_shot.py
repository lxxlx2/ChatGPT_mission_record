import hashlib
import threading
import time
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

# Works from both standalone candidate bundle and repository tests/ layout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import frank_c2a_f2_one_shot as f


def ok():
    return f.Captured('COMPLETE', 0, b'', b'', 0, 0, hashlib.sha256(b'').hexdigest(), hashlib.sha256(b'').hexdigest(), True, True, False, False)


def bad():
    return f.Captured('COMPLETE', 5, b'first-out', b'first-error', 9, 11, hashlib.sha256(b'first-out').hexdigest(), hashlib.sha256(b'first-error').hexdigest(), True, True, False, False)


class Harness:
    def __init__(self, path, calls, first=None, final=None):
        self.path = path
        self.calls = calls
        self.first = first or bad()
        self.final = final or ok()
        self.bootouts = 0
        self.bootstraps = 0

    def bootout(self):
        self.bootouts += 1
        return ok()

    def bootstrap(self):
        self.bootstraps += 1
        if self.bootstraps == 1:
            if isinstance(self.first, BaseException):
                raise self.first
            return self.first
        if isinstance(self.final, BaseException):
            raise self.final
        return self.final


class TestOneShot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir(mode=0o700)
        self.runner = self.root / 'dashboard.sh'
        self.old = b'#!/bin/sh\nLOCAL_AGENT=/old\nMODE=safe\n'
        self.new = b'#!/bin/sh\nLOCAL_AGENT=/candidate\nMODE=safe\n'
        self.runner.write_bytes(self.old)
        self.runner.chmod(0o700)
        self.label = 'com.test.frank-meme.dashboard'
        self.plist = self.root / (self.label + '.plist')
        self.plist.write_text('synthetic - never executed')
        self.plan = f.Plan(self.runner, self.plist, self.label, self.evidence, self.new,
                           f._sha(self.old), f._sha(self.new))

    def probe(self, *, tamper=False):
        candidate = self.runner.read_bytes() == self.new
        if candidate:
            source, digest = f.APPROVED_SOURCE, f._sha(self.new)
        else:
            source, digest = f.OLD_SOURCE, f._sha(self.old)
        return f.Identity(source, digest, self.label, '127.0.0.1:8766', True,
                          'changed' if tamper else 'protected-fixed')

    def go(self, first=None, final=None, probe=None):
        lifecycle = Harness(self.runner, [], first=first, final=final)
        out = f.execute_once(self.plan, lifecycle, probe or self.probe, authorized=True)
        return out, lifecycle

    def test_not_authorized(self):
        with self.assertRaisesRegex(f.GateError, 'NOT_AUTHORIZED'):
            f.execute_once(self.plan, Harness(self.runner, []), self.probe)
        self.assertEqual(self.runner.read_bytes(), self.old)

    def test_first_bootstrap_nonzero_capture_then_one_rollback(self):
        verdict, lifecycle = self.go(first=bad())
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(verdict.rollback_attempts, 1)
        self.assertEqual(lifecycle.bootstraps, 2)
        self.assertEqual(self.runner.read_bytes(), self.old)
        receipt = json.loads((self.evidence / f.FIRST_ATTEMPT_RECORD).read_text())
        self.assertEqual(receipt['returncode'], 5)
        self.assertEqual(receipt['status'], 'COMPLETE')
        self.assertEqual(f.base64.b64decode(receipt['stderr']['captured_base64']), b'first-error')
        self.assertFalse(receipt['command_arguments_saved'])
        self.assertEqual((self.evidence / f.FIRST_ATTEMPT_RECORD).stat().st_mode & 0o777, 0o600)

    def test_post_replace_fsync_exception_always_restores(self):
        orig = os.fsync
        once = [False]
        def fail(fd):
            if not once[0] and self.runner.read_bytes() == self.new:
                once[0] = True
                raise OSError('fault-after-replace')
            return orig(fd)
        with patch.object(f.os, 'fsync', side_effect=fail):
            verdict, lifecycle = self.go(first=ok())
        self.assertTrue(once[0])
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(lifecycle.bootstraps, 1)  # only restoring old service
        self.assertEqual(self.runner.read_bytes(), self.old)
        self.assertEqual(verdict.first_attempt_evidence, 'NOT_ATTEMPTED')

    def test_interrupt_at_bootstrap_returns_explicit_rollback(self):
        verdict, lifecycle = self.go(first=KeyboardInterrupt())
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(verdict.bootstrap_status, 'INTERRUPTED')
        self.assertEqual(lifecycle.bootstraps, 2)
        self.assertEqual(self.runner.read_bytes(), self.old)
        record = json.loads((self.evidence / f.FIRST_ATTEMPT_RECORD).read_text())
        self.assertIsNone(record['returncode'])
        self.assertEqual(record['status'], 'UNOBSERVED')
        self.assertEqual(record['stderr']['state'], 'NOT_CAPTURED')

    def test_failure_to_persist_attempt_still_rolls_back(self):
        with patch.object(f, 'save_first_attempt', side_effect=OSError('disk-full')):
            verdict, lifecycle = self.go(first=bad())
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(verdict.first_attempt_evidence, 'PERSIST_FAILED')
        self.assertEqual(lifecycle.bootstraps, 2)
        self.assertEqual(self.runner.read_bytes(), self.old)

    def test_rollback_bootstrap_fails_without_retry(self):
        verdict, lifecycle = self.go(first=bad(), final=bad())
        self.assertEqual(verdict.status, 'ROLLBACK_FAILED_STOP')
        self.assertEqual(lifecycle.bootstraps, 2)
        self.assertFalse(verdict.rollback_verified)

    def test_rollback_verification_fails_closed(self):
        calls = [0]
        def check():
            calls[0] += 1
            return self.probe(tamper=calls[0] > 1)
        verdict, lifecycle = self.go(first=bad(), probe=check)
        self.assertEqual(verdict.status, 'ROLLBACK_UNVERIFIED_STOP')
        self.assertEqual(lifecycle.bootstraps, 2)

    def test_success_needs_independent_live_probe(self):
        verdict, lifecycle = self.go(first=ok())
        self.assertEqual(verdict.status, 'CUTOVER_PROBE_PASS_NOT_DEPLOY_AUTH')
        self.assertEqual(lifecycle.bootstraps, 1)
        self.assertEqual(self.runner.read_bytes(), self.new)
        self.assertEqual(json.loads((self.evidence / f.FIRST_ATTEMPT_RECORD).read_text())['returncode'], 0)

    def test_success_rc_zero_but_health_fail_rolls_back(self):
        def probe():
            obj = self.probe()
            if obj.source_sha == f.APPROVED_SOURCE:
                return f.Identity(obj.source_sha, obj.runner_sha256, obj.dashboard_label,
                                  obj.listener, False, obj.protected_fingerprint)
            return obj
        verdict, lifecycle = self.go(first=ok(), probe=probe)
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(lifecycle.bootstraps, 2)

    def test_timeout_requires_rollback(self):
        t = f.Captured('TIMEOUT', None, b'a', b'', 1, 0, f._sha(b'a'), f._sha(b''), False, False, False, False)
        verdict, _ = self.go(first=t)
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(verdict.bootstrap_status, 'TIMEOUT')

    def test_private_evidence_no_clobber(self):
        self.go()
        first = (self.evidence / f.FIRST_ATTEMPT_RECORD).read_bytes()
        with self.assertRaises(FileExistsError):
            f.save_first_attempt(self.evidence, bad(), phase='BOOTSTRAP_RESULT')
        self.assertEqual((self.evidence / f.FIRST_ATTEMPT_RECORD).read_bytes(), first)

    def test_malformed_candidate_rejected_before_bootout(self):
        plan = f.Plan(self.runner, self.plist, self.label, self.evidence,
                      b'#!/bin/sh\nLOCAL_AGENT=/candidate\nBAD=1\n',
                      f._sha(self.old), f._sha(b'#!/bin/sh\nLOCAL_AGENT=/candidate\nBAD=1\n'))
        lifecycle = Harness(self.runner, [])
        with self.assertRaisesRegex(f.GateError, 'SINGLE_LOCAL_AGENT'):
            f.execute_once(plan, lifecycle, self.probe, authorized=True)
        self.assertEqual(lifecycle.bootouts, 0)

    def test_late_protected_drift_at_g4_rolls_back(self):
        calls = [0]
        def check():
            calls[0] += 1
            return self.probe(tamper=calls[0] == 3)
        verdict, lifecycle = self.go(first=ok(), probe=check)
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(lifecycle.bootstraps, 2)
        self.assertEqual(self.runner.read_bytes(), self.old)

    def test_bootout_failure_keeps_or_restores_old(self):
        lifecycle = Harness(self.runner, [])
        lifecycle.bootout = lambda: bad()
        verdict = f.execute_once(self.plan, lifecycle, self.probe, authorized=True)
        self.assertEqual(verdict.status, 'ROLLBACK_FAILED_STOP')  # fixture's first bootstrap is bad
        self.assertEqual(self.runner.read_bytes(), self.old)
        self.assertEqual(lifecycle.bootstraps, 1)

    def test_evidence_dir_not_private_blocks_all_service_changes(self):
        self.evidence.chmod(0o755)
        lifecycle = Harness(self.runner, [])
        with self.assertRaisesRegex(f.GateError, 'EVIDENCE_DIR_NOT_PRIVATE'):
            f.execute_once(self.plan, lifecycle, self.probe, authorized=True)
        self.assertEqual(lifecycle.bootouts, 0)

    def test_first_attempt_timeout_does_not_fake_original_returncode(self):
        c = f.bounded_command((sys.executable, '-c', 'import time;time.sleep(10)'), timeout=0.1)
        self.assertEqual(c.status, 'TIMEOUT')
        self.assertIsNone(c.returncode)
        f.save_first_attempt(self.evidence, c, phase='BOOTSTRAP_RESULT')
        saved = json.loads((self.evidence / f.FIRST_ATTEMPT_RECORD).read_text())
        self.assertIsNone(saved['returncode'])
        self.assertEqual(saved['status'], 'TIMEOUT')

    def test_post_replace_unknown_third_party_change_stops_without_overwrite(self):
        original = f.atomic_runner
        injected = [False]
        third = b'#!/bin/sh\nLOCAL_AGENT=/unexpected\n'
        def mutate(path, old, new, mode, arm):
            if not injected[0]:
                injected[0] = True
                arm()
                path.write_bytes(third)
                raise OSError('external-race-after-risk-armed')
            return original(path, old, new, mode, arm)
        with patch.object(f, 'atomic_runner', side_effect=mutate):
            result, lifecycle = self.go(first=ok())
        self.assertEqual(result.status, 'ROLLBACK_FAILED_STOP')
        self.assertEqual(self.runner.read_bytes(), third)
        self.assertEqual(lifecycle.bootstraps, 0)

    def test_real_os_bounded_output_truncates(self):
        command = (sys.executable, '-c', "import sys;sys.stdout.buffer.write(b'A'*1000000);sys.stderr.buffer.write(b'B'*1000000)")
        result = f.bounded_command(command, timeout=8)
        self.assertEqual(result.status, 'COMPLETE')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(result.stdout), f.CAP)
        self.assertEqual(len(result.stderr), f.CAP)
        self.assertEqual(result.stdout_total, 1000000)
        self.assertEqual(result.stderr_total, 1000000)
        self.assertTrue(result.stdout_truncated and result.stderr_truncated)
        self.assertTrue(result.stdout_eof and result.stderr_eof)
        self.assertEqual(result.stdout_sha256, f._sha(b'A'*1000000))

    def test_real_os_timeout(self):
        result = f.bounded_command((sys.executable, '-c', 'import time;time.sleep(10)'), timeout=0.25)
        self.assertEqual(result.status, 'TIMEOUT')
        self.assertFalse(result.ok)

    def test_real_os_kills_pipe_holding_child(self):
        code = 'import os,time; p=os.fork(); os._exit(0) if p else time.sleep(10)'
        result = f.bounded_command((sys.executable, '-c', code), timeout=0.3)
        self.assertEqual(result.status, 'TIMEOUT')
        self.assertFalse(result.ok)


# Independent cases use the same scratch fixture; no Mac lifecycle is constructed.
class TestAdapterRegressions(unittest.TestCase):
    def setUp(self):
        self.h = TestOneShot()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)

    def test_registered_candidate_is_stopped_before_old_bootstrap(self):
        h = self.h
        events = []
        class Registered(Harness):
            active = True
            def bootout(self):
                events.append('stop')
                self.active = False
                return super().bootout()
            def bootstrap(self):
                events.append('start')
                if self.active:
                    return bad()
                self.active = True
                return super().bootstrap()
        life = Registered(h.runner, [], first=ok())
        def probe():
            obj = h.probe()
            return replace(obj, dashboard_healthy=False) if obj.source_sha == f.APPROVED_SOURCE else obj
        verdict = f.execute_once(h.plan, life, probe, authorized=True)
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(events, ['stop', 'start', 'stop', 'start'])
        self.assertEqual(h.runner.read_bytes(), h.old)

    def test_different_evidence_directories_cannot_overlap_same_runner(self):
        h = self.h
        entered, release = threading.Event(), threading.Event()
        other = h.root / 'other-evidence'
        other.mkdir(mode=0o700)
        class Blocking(Harness):
            def bootout(self):
                entered.set()
                if not release.wait(3):
                    raise RuntimeError('TEST_TIMEOUT')
                return super().bootout()
        life = Blocking(h.runner, [], first=bad())
        outputs = []
        def task():
            try:
                outputs.append(f.execute_once(h.plan, life, h.probe, authorized=True))
            except BaseException as exc:
                outputs.append(exc)
        t = threading.Thread(target=task)
        t.start()
        try:
            self.assertTrue(entered.wait(2))
            second = Harness(h.runner, [])
            with self.assertRaisesRegex(f.GateError, 'ONE_SHOT_ALREADY_RUNNING'):
                f.execute_once(replace(h.plan, evidence_dir=other), second, h.probe, authorized=True)
            self.assertEqual(second.bootouts, 0)
            self.assertFalse((other / 'old-dashboard-runner.bin').exists())
        finally:
            release.set()
            t.join(4)
        self.assertFalse(t.is_alive())
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].status, 'ROLLED_BACK_STOP')

    def test_selector_initialization_failure_reaps_real_child(self):
        children = []
        real = subprocess.Popen
        def spawn(*a, **kw):
            p = real(*a, **kw)
            children.append(p)
            return p
        with patch.object(f.subprocess, 'Popen', side_effect=spawn), patch.object(
            f.selectors, 'DefaultSelector', side_effect=OSError('selector fault')
        ):
            with self.assertRaises(OSError):
                f.bounded_command((sys.executable, '-c', 'import time;time.sleep(20)'), timeout=1)
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].returncode)
        self.assertTrue(children[0].stdout.closed and children[0].stderr.closed)

    def test_systemexit_does_not_skip_emergency_recovery(self):
        verdict, life = self.h.go(first=SystemExit(7))
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(verdict.bootstrap_status, 'INTERRUPTED')
        self.assertEqual(life.bootouts, 2)

    def test_first_record_fsync_failure_still_restores_once(self):
        def write(directory, result, *, phase):
            with patch.object(f.os, 'fsync', side_effect=OSError('evidence fsync')):
                return original(directory, result, phase=phase)
        original = f.save_first_attempt
        with patch.object(f, 'save_first_attempt', side_effect=write):
            verdict, life = self.h.go(first=bad())
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(verdict.first_attempt_evidence, 'PERSIST_FAILED')
        self.assertEqual(life.bootouts, 2)
        self.assertEqual(self.h.runner.read_bytes(), self.h.old)

    def test_first_record_symlink_cannot_overwrite_target(self):
        h = self.h
        target = h.root / 'unrelated'
        target.write_bytes(b'KEEP')
        (h.evidence / f.FIRST_ATTEMPT_RECORD).symlink_to(target)
        verdict, life = h.go(first=bad())
        self.assertEqual(verdict.first_attempt_evidence, 'PERSIST_FAILED')
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        self.assertEqual(target.read_bytes(), b'KEEP')

    def test_incomplete_output_never_becomes_success(self):
        verdict, life = self.h.go(first=replace(ok(), status='INCOMPLETE', stdout_eof=False))
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')
        saved = json.loads((self.h.evidence / f.FIRST_ATTEMPT_RECORD).read_text())
        self.assertFalse(saved['stdout']['eof_seen'])

    def test_real_negative_signal_rc_and_missing_executable(self):
        result = f.bounded_command((sys.executable, '-c',
            'import os,signal;os.kill(os.getpid(),signal.SIGTERM)'), timeout=3)
        self.assertEqual(result.status, 'COMPLETE')
        self.assertEqual(result.returncode, -15)
        with self.assertRaises(FileNotFoundError):
            f.bounded_command((str(self.h.root / 'not-an-executable'),), timeout=1)

    def test_real_timeout_kills_descendant_not_only_group_leader(self):
        code = ('import os,time; pid=os.fork(); '
                'print(pid,flush=True) if pid else None; time.sleep(20)')
        result = f.bounded_command((sys.executable, '-c', code), timeout=.3)
        self.assertEqual(result.status, 'TIMEOUT')
        child = int(result.stdout.splitlines()[0])
        # A zombie is terminated, not a continuing background process. The host
        # init may reap the orphan asynchronously; do not send signals to it.
        status = subprocess.run(['ps', '-p', str(child), '-o', 'stat='],
                                capture_output=True, text=True, timeout=2)
        self.assertTrue(status.returncode != 0 or status.stdout.strip().startswith('Z'))

    def test_cross_process_parent_lock_stays_held_during_bootstrap(self):
        h = self.h
        class InspectLock(Harness):
            def bootstrap(self):
                code = """import os,fcntl,sys
fd=os.open(sys.argv[1],os.O_RDONLY)
try:
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
    sys.exit(3)
"""
                observed = subprocess.run([sys.executable, '-c', code, str(h.runner.parent)],
                                          capture_output=True, timeout=2)
                if observed.returncode != 3:
                    raise AssertionError('cross-process lock not held')
                return super().bootstrap()
        verdict = f.execute_once(h.plan, InspectLock(h.runner, [], first=bad()), h.probe, authorized=True)
        self.assertEqual(verdict.status, 'ROLLED_BACK_STOP')

    def test_uncanonical_runner_alias_remains_rejected(self):
        h = self.h
        alias = h.root / 'alias'
        alias.symlink_to(h.root, target_is_directory=True)
        plan = replace(h.plan, runner=alias / h.runner.name)
        life = Harness(h.runner, [])
        with self.assertRaisesRegex(f.GateError, 'RUNNER_PARENT_DRIFT'):
            f.execute_once(plan, life, h.probe, authorized=True)
        self.assertEqual(life.bootouts, 0)



if __name__ == '__main__':
    unittest.main()
