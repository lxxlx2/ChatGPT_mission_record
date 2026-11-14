"""Prepare private Dashboard-only backups/plan; never deploy, listen or fetch.

The prior plan supplies path hints only. All identities/hashes are measured again.
An optional second invocation binds a newly published clean candidate checkout.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import sqlite3
import subprocess
import urllib.parse

os.umask(0o077)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(root):
    root = Path(root)
    assert not any(p.is_symlink() for p in root.rglob('*'))
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=30)


def git(path, *args):
    result = run(['git', '-C', str(path), *args])
    assert result.returncode == 0
    return result.stdout.strip()


def backup_sqlite(source, target):
    uri = 'file:' + urllib.parse.quote(str(source), safe='/') + '?mode=ro'
    db = sqlite3.connect(uri, uri=True)
    db.execute('PRAGMA query_only=ON')
    copy = sqlite3.connect(target)
    try:
        db.backup(copy)
        assert copy.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
        foreign_keys = copy.execute('PRAGMA foreign_key_check').fetchall()
        assert not foreign_keys
    finally:
        copy.close()
        db.close()
    return {'name': source.name, 'sha256': sha(target), 'integrity': 'ok', 'foreign_key_errors': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prior-plan', type=Path, required=True)
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--candidate-repository', type=Path)
    parser.add_argument('--candidate-sha')
    args = parser.parse_args()
    assert bool(args.candidate_repository) == bool(args.candidate_sha)
    prior = json.loads(args.prior_plan.read_text())
    backup = args.backup
    runner, plist, control = map(Path, (prior['runner'], prior['plist'], prior['control']))
    text = runner.read_text()
    match = re.search(r"^LOCAL_AGENT='([^']+)'$", text, flags=re.M)
    assert match
    old_agent = Path(match.group(1))
    assert old_agent.is_dir() and not old_agent.is_symlink()
    assert plistlib.loads(plist.read_bytes())['ProgramArguments'] == [str(runner)]
    assert plistlib.loads(plist.read_bytes())['Label'] == 'com.jerson.frank-meme.dashboard'
    assert Path(prior['protected_files']['control_pointer']).read_text().strip() == str(control)
    assert Path(prior['protected_files']['port_configuration']).read_text().strip() == '8766'
    assert Path(prior['protected_files']['rpc_configuration']).stat().st_size > 0
    label = 'gui/' + str(os.getuid()) + '/com.jerson.frank-meme.dashboard'
    loaded = run(['launchctl', 'print', label])
    dashboard_loaded = loaded.returncode == 0
    pid_match = re.search(r'\bpid = (\d+)', loaded.stdout) if dashboard_loaded else None
    assert not dashboard_loaded or pid_match
    old_pid = int(pid_match.group(1)) if pid_match else None
    assert run(['launchctl', 'print', 'gui/' + str(os.getuid()) + '/com.jerson.frank-meme.loop']).returncode != 0
    if dashboard_loaded:
        cwd = run(['/usr/sbin/lsof', '-a', '-p', str(old_pid), '-d', 'cwd', '-Fn'])
        assert cwd.returncode == 0 and any(line == 'n' + str(old_agent) for line in cwd.stdout.splitlines())
        opened = run(['/usr/sbin/lsof', '-a', '-p', str(old_pid), '-Fn'])
        assert opened.returncode == 0 and 'wallet-cluster-rpc-cache.sqlite' not in opened.stdout
    else:
        listening = run(['/usr/sbin/lsof','-nP','-iTCP:8766','-sTCP:LISTEN'])
        assert listening.returncode == 1 and not listening.stdout.strip()
        opened = run(['/usr/sbin/lsof','-t','--',str(control/'wallet-cluster-rpc-cache.sqlite')])
        assert opened.returncode == 1 and not opened.stdout.strip()
    old_files = manifest(old_agent)
    reports = manifest(control / 'cluster-reports')
    protected = {name: str(Path(path)) for name, path in prior['protected_files'].items()}
    assert all(Path(path).is_file() for path in protected.values())
    hashes = {name: sha(path) for name, path in protected.items()}
    if not backup.exists():
        backup.mkdir(parents=True)
        shutil.copytree(old_agent, backup / 'old-agent')
        write(backup / 'old-source-manifest.json', old_files)
        shutil.copytree(control / 'cluster-reports', backup / 'cluster-reports')
        copy = backup / 'control-copy'
        copy.mkdir()
        for source in control.iterdir():
            if source.name in {'logs', 'git-evidence-spool', 'cluster-reports'}:
                continue
            if source.name.endswith(('.sqlite', '.sqlite-wal', '.sqlite-shm')):
                continue
            if source.is_dir():
                shutil.copytree(source, copy / source.name)
            elif source.is_file():
                shutil.copy2(source, copy / source.name)
        shutil.copytree(backup / 'cluster-reports', copy / 'cluster-reports')
        sqlite_backups = [backup_sqlite(control / name, copy / name) for name in (
            'mission-control.sqlite', 'sol-normalized-v1.sqlite', 'wallet-cluster-rpc-cache.sqlite')]
        shutil.copytree(copy, backup / 'control-copy-candidate')
        shutil.copy2(runner, backup / 'runner-before.sh')
        write(backup / 'preparation-summary.json', {
            'prepared_at': datetime.now(timezone.utc).isoformat(), 'old_agent': str(old_agent),
            'old_dashboard_pid': old_pid, 'old_source_files': len(old_files), 'report_files': len(reports),
            'sqlite_backups': sqlite_backups, 'protected_hash_count': len(hashes),
            'protected_hashes': hashes, 'original_runner_sha256': sha(runner),
            'production_writes': 0, 'listeners_started': 0, 'source_requests': 0})
    else:
        previous = json.loads((backup / 'preparation-summary.json').read_text())
        assert previous['old_agent'] == str(old_agent) and previous['old_dashboard_pid'] == old_pid
        assert previous['protected_hashes'] == hashes and previous['original_runner_sha256'] == sha(runner)
    assert manifest(backup / 'old-agent') == old_files
    assert manifest(backup / 'cluster-reports') == reports
    assert manifest(old_agent) == old_files
    assert manifest(control / 'cluster-reports') == reports
    assert all(sha(path) == hashes[name] for name, path in protected.items())
    if not args.candidate_repository:
        print(json.dumps({'status': 'BACKUP_PREPARED', 'old_source_files': len(old_files),
                          'report_files': len(reports), 'candidate_bound': False,
                          'production_writes': 0, 'listeners_started': 0, 'source_requests': 0}))
        return
    candidate_repo, candidate_sha = args.candidate_repository, args.candidate_sha
    assert re.fullmatch(r'[0-9a-f]{40}', candidate_sha)
    assert git(candidate_repo, 'rev-parse', 'HEAD') == candidate_sha
    assert not git(candidate_repo, 'status', '--porcelain', '--untracked-files=all')
    assert run(['git', '-C', str(candidate_repo), 'symbolic-ref', '-q', 'HEAD']).returncode == 1
    candidate = candidate_repo / 'crypto-300-profit-mission/local-agent'
    tracked_files = git(candidate, 'ls-files', '-z').split('\0')
    tracked = {name: sha(candidate / name) for name in tracked_files if name}
    candidate_runner = text.replace(str(old_agent), str(candidate), 1)
    assert candidate_runner != text and candidate_runner.count(str(candidate)) == 1
    (backup / 'runner-candidate.sh').write_text(candidate_runner)
    side = dict(prior['narrative_note'])
    note = Path(side['target'])
    assert note.is_file() and sha(note) == side['sha256']
    staged = backup / 'existing-narrative-note.json'
    shutil.copy2(note, staged)
    side['staged'] = str(staged)
    # The no-listener helper will verify the fresh old backup and candidate;
    # the executor refuses apply before the combined PASS receipt exists.
    plan = {**prior, 'version': 2, 'old_sha': 'e7df038fa2bcc1a49add0019fb9a35718beed3a0',
            'candidate_sha': candidate_sha, 'authorization': 'USER_20261113_FREE_MAINLINE_LOCAL_DASHBOARD',
            'backup': str(backup), 'old_agent': str(old_agent), 'candidate_agent': str(candidate),
            'candidate_repository': str(candidate_repo), 'candidate_tracked_agent_manifest': tracked,
            'old_agent_manifest': old_files, 'reports': reports,
            'old_git_identity_trusted': git(old_agent,'rev-parse','HEAD')=='e7df038fa2bcc1a49add0019fb9a35718beed3a0' and not git(old_agent,'status','--porcelain','--untracked-files=all'),
            'candidate_runtime_manifest': manifest(candidate / 'mission_agent'),
            'runner_sha_before': sha(runner), 'runner_mode_before': runner.stat().st_mode & 0o777,
            'protected_files': protected, 'protected_hashes': hashes,
            'old_dashboard_pid': old_pid, 'old_dashboard_loaded': dashboard_loaded,
            'control_copy_old': str(backup / 'control-copy'),
            'control_copy_candidate': str(backup / 'control-copy-candidate'), 'narrative_note': side,
            'preflight_helper_sha256': sha(prior['preflight_helper']), 'old_backup_verified': True}
    write(backup / 'local-update-private-plan.json', plan)
    print(json.dumps({'status': 'PLAN_BOUND', 'candidate_sha': candidate_sha,
                      'tracked_agent_files': len(tracked), 'old_source_files': len(old_files),
                      'report_files': len(reports), 'production_writes': 0, 'listeners_started': 0,
                      'source_requests': 0}))


if __name__ == '__main__':
    main()
