"""TEMP-ONLY process rehearsal; never an installer or production rollback tool.

Requires a read-only old package and an existing interpreter. No launchctl,
production data, runner, plist, policy, or shared release writes. All launched
processes use fixture data under a newly created TemporaryDirectory.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tarfile
import tempfile
import time
from urllib.request import build_opener, ProxyHandler

APPROVED = '31dd598df248ca15f731913a5cbf82e88b981874'
PREFIX = 'crypto-300-profit-mission/local-agent/'
REPO = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_manifest(root, manifest):
    for name, expected in manifest.items():
        p = root / name
        if not p.resolve().is_relative_to(root.resolve()) or p.is_symlink() or not p.is_file() or sha(p) != expected:
            raise ValueError('PACKAGE_HASH_MISMATCH')


def atomic_pointer(root, target):
    pending = root / 'pending'
    pending.symlink_to(target, target_is_directory=True)
    os.replace(pending, root / 'active')
    assert (root / 'active').resolve() == target.resolve()


def stop(process):
    if process is not None and process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def rehearse(old_source, interpreter):
    old_source = old_source.resolve(strict=True)
    interpreter = interpreter.absolute()
    if not interpreter.is_file():
        raise ValueError("INTERPRETER_MISSING")
    old_meta = json.loads((old_source / '.pr39-release-manifest.json').read_text())
    checked_manifest(old_source, old_meta['files'])
    archive = subprocess.check_output(['git', '-C', str(REPO), 'archive', APPROVED, PREFIX])
    with tempfile.TemporaryDirectory(prefix='frank-dashboard-release-temp-only-') as temp:
        root = Path(temp)
        candidate, old = root / 'candidate', root / 'old'
        candidate.mkdir(); old.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                name = member.name.removeprefix(PREFIX)
                dest = candidate / name
                if not name or not dest.resolve().is_relative_to(candidate.resolve()):
                    raise ValueError('UNSAFE_ARCHIVE_MEMBER')
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(tar.extractfile(member).read())
        manifest = {str(p.relative_to(candidate)): sha(p) for p in candidate.rglob('*') if p.is_file()}
        # Copy only manifest-verified old bytes. Never copy a database or runtime log.
        for name in old_meta['files']:
            src, dest = old_source / name, old / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
        checked_manifest(old, old_meta['files']); checked_manifest(candidate, manifest)
        manifest_digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        guard = root / 'guard'; guard.mkdir()
        (guard / 'sitecustomize.py').write_text('''import socket, os
_original = socket.socket.connect
def restricted(self, address):
    if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', '::1'):
        with open(os.environ['LAB_NETWORK_DENIED'], 'a') as f: f.write('DENIED\\n')
        raise RuntimeError('LAB_NON_LOOPBACK_NETWORK_DENIED')
    return _original(self, address)
socket.socket.connect = restricted
''')
        fixture = root / 'fixture'; fixture.mkdir()
        env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(root),
               'PYTHONDONTWRITEBYTECODE': '1', 'MISSION_EVIDENCE_EXPORT_ENABLED': '0',
               'SOLANA_RPC_URLS': 'http://127.0.0.1:1',
               'LAB_NETWORK_DENIED': str(root / 'network-denied')}
        # OS-selected isolated port; no probing or replacement of occupied services.
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0)); port = reserve.getsockname()[1]
        opener = build_opener(ProxyHandler({}))
        processes = []
        def start(target, phase):
            control = root / ('control-' + phase); control.mkdir()
            local_env = {**env, 'PYTHONPATH': str(guard) + os.pathsep + str(target)}
            log = open(root / (phase + '.log'), 'wb')
            try:
                p = subprocess.Popen([str(interpreter), '-B', 'scripts/mission_meme_v1.py', 'serve',
                    '--production-root', str(fixture), '--control-root', str(control),
                    '--host', '127.0.0.1', '--port', str(port)], cwd=target, env=local_env,
                    stdout=log, stderr=log)
            finally:
                log.close()
            processes.append(p)
            return p
        def verify(p, target, new=False):
            for _ in range(100):
                if p.poll() is not None:
                    raise RuntimeError('TEMP_SERVER_EXITED')
                try:
                    with opener.open(f'http://127.0.0.1:{port}/', timeout=.3) as r:
                        assert r.read() == (target / 'mission_agent/mission_control/static/index.html').read_bytes()
                    break
                except OSError:
                    time.sleep(.05)
            else:
                raise RuntimeError('TEMP_SERVER_NOT_READY')
            for path in ['/api/runtime'] + (['/api/frank-intelligence', '/api/frank-activity-watch'] if new else []):
                with opener.open(f'http://127.0.0.1:{port}' + path, timeout=2) as r:
                    assert r.status == 200
                    json.load(r)
            return True
        try:
            atomic_pointer(root, old)
            p = start((root / 'active').resolve(), 'old'); verify(p, old); stop(p)
            checked_manifest(candidate, manifest)
            atomic_pointer(root, candidate)
            p = start((root / 'active').resolve(), 'candidate'); verify(p, candidate, True); stop(p)
            # Actual candidate startup failure: bind the lab port, never any production port.
            with socket.socket() as conflict:
                conflict.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                conflict.bind(('127.0.0.1', port)); conflict.listen()
                failed = start(candidate, 'fault')
                failed.wait(timeout=8)
                assert failed.returncode != 0
            atomic_pointer(root, old)
            p = start((root / 'active').resolve(), 'rollback'); verify(p, old); stop(p)
            # Directional negative test: corrupt one staged file; reject before switching.
            victim = candidate / 'mission_agent/mission_control/server.py'
            victim.write_bytes(victim.read_bytes() + b'\n# staged corruption\n')
            try:
                checked_manifest(candidate, manifest)
            except ValueError:
                pass
            else:
                raise AssertionError('CORRUPT_PACKAGE_ACCEPTED')
            assert (root / 'active').resolve() == old.resolve()
            assert not (root / 'network-denied').exists()
            checked_manifest(old_source, old_meta['files'])
            return {'verdict': 'PASS', 'source_sha': APPROVED,
                'candidate_files': len(manifest), 'candidate_manifest_sha256': manifest_digest,
                'old_source_sha_claim': old_meta['expected'], 'old_verified_files': len(old_meta['files']),
                'checks': {'old_package_actual_start': True, 'candidate_actual_start_and_three_gets': True,
                    'bind_failure_detected': True, 'old_package_restarted_and_http_verified': True,
                    'corruption_rejected_before_switch': True, 'old_source_bytes_unchanged': True},
                'non_loopback_network_attempts': 0, 'fixture_data_only': True,
                'production_changes': 0, 'real_service_rollback_proven': False,
                'launchctl_operations': 0}
        finally:
            for p in processes:
                stop(p)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-source', type=Path, required=True)
    parser.add_argument('--python', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(rehearse(args.old_source, args.python), sort_keys=True))
