"""Frozen partition and winner capability checks; no configurable optimizer paths."""
import json
import hashlib
import subprocess
from pathlib import Path
from ...hashing import canonical, digest, verify
from ..cache import load

FREEZE = '15753ad1092cc2b1b9bd36270dd770916c50aec0'
MODULE = Path(__file__).resolve().parents[3]
REPO_PATH = 'crypto-300-profit-mission/local-agent/'
FILES = ('config/price_rule_v2_search.json', 'docs/PRICE_RULE_V2_CALIBRATION_PLAN.md',
         'docs/PRICE_GT_V2_EPISODES.md', 'docs/PRICE_RULE_V2_SEARCH_SPACE.md')

def contract():
    for name in FILES:
        frozen = subprocess.check_output(['git', 'show', FREEZE + ':' + REPO_PATH + name], cwd=MODULE)
        if (MODULE / name).read_bytes() != frozen:
            raise ValueError('V2_FREEZE_MUTATED')
    return json.loads((MODULE / FILES[0]).read_text())


def budget(root, baseline=None):
    roots = [Path(root)] + ([Path(baseline)] if baseline else [])
    size = sum(p.stat().st_size for r in roots for p in r.rglob('*') if p.is_file())
    if size > 5 * 1024**3:
        raise ValueError('LOCAL_SOFT_BUDGET_EXCEEDED')
    return size


class Partition:
    def __init__(self, root, role):
        self.root = Path(root).resolve()
        self.role = role
        self.config = contract()
        if role not in self.config['partitions']:
            raise ValueError('unknown partition')
        self.path = self.root / role.lower()
        self.start, self.end = self.config['partitions'][role]
        self.receipt = json.loads((self.path / 'partition.json').read_text())
        verify(self.receipt)
        if self.receipt['role'] != role or self.receipt['range'] != [self.start, self.end] or self.receipt['freeze_commit'] != FREEZE:
            raise ValueError('PARTITION_ROLE_RANGE_MISMATCH')

    def bars(self, asset):
        from ..bar import Bar, MINUTE
        if asset not in self.config['assets']:
            raise ValueError('asset not in optimization universe')
        path = self.path / (asset + '-canonical.json.gz')
        rows, manifest = load(path)
        if digest(manifest) != self.receipt['manifest_hashes'][asset]:
            raise ValueError('PARTITION_MANIFEST_CHANGED')
        expected_start = self.start - self.config['warmup_bars'] * MINUTE
        if manifest['role'] != self.role or manifest['evaluation_range'] != [self.start, self.end]:
            raise ValueError('CACHE_ROLE_RANGE_MISMATCH')
        if manifest['row_count'] != (self.end - expected_start) // MINUTE:
            raise ValueError('INCOMPLETE_HISTORY')
        for index, row in enumerate(rows):
            row = dict(row); row.pop('close_time_utc')
            bar = Bar(**row)
            if bar.asset != asset or not bar.is_closed or bar.open_time_utc != expected_start + index * MINUTE:
                raise ValueError('CANONICAL_CONTINUITY_FAILURE')
            yield bar


class CalibrationOnly(Partition):
    def __init__(self, directory):
        path = Path(directory).resolve()
        if path.name != 'calibration':
            raise ValueError('OPTIMIZER_CALIBRATION_ONLY')
        super().__init__(path.parent, 'CALIBRATION')
        if self.path.resolve() != path:
            raise ValueError('OPTIMIZER_CALIBRATION_ONLY')


def immutable_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('xb') as stream:
        stream.write(canonical(value) + b'\n')
    path.chmod(0o600)


def read_winner(path):
    path = Path(path)
    value = json.loads(path.read_text()); verify(value)
    if value['event_type'] != 'PRICE_RULE_V2_CANDIDATE' or value['freeze_commit'] != FREEZE:
        raise ValueError('INVALID_WINNER')
    if value['search_config_hash'] != digest(contract()):
        raise ValueError('WINNER_CONTRACT_CHANGED')
    relative = str(path.resolve().relative_to(MODULE))
    blob = subprocess.check_output(['git', 'show', 'HEAD:' + REPO_PATH + relative], cwd=MODULE)
    if blob != path.read_bytes():
        raise ValueError('WINNER_NOT_COMMITTED_OR_MUTATED')
    commits = subprocess.check_output(['git', 'log', '--diff-filter=A', '--format=%H', '--', relative], cwd=MODULE, text=True).strip().splitlines()
    if len(commits)!=1:raise ValueError('WINNER_MUST_HAVE_ONE_ORIGINAL_COMMIT')
    original=subprocess.check_output(['git','show',commits[0]+':'+REPO_PATH+relative],cwd=MODULE)
    if original!=path.read_bytes():raise ValueError('WINNER_CHANGED_AFTER_ORIGINAL_COMMIT')
    result_path=MODULE/'config/price_rule_v2_calibration_result.json'
    if result_path.exists():
        result=json.loads(result_path.read_text());result.pop('resource',None)
        if digest(result)!=value['calibration_result_hash']:raise ValueError('WINNER_CALIBRATION_HASH_MISMATCH')
        committed_result=subprocess.check_output(['git','show',commits[0]+':'+REPO_PATH+'config/price_rule_v2_calibration_result.json'],cwd=MODULE)
        if committed_result!=result_path.read_bytes():raise ValueError('CALIBRATION_RESULT_CHANGED_AFTER_WINNER_COMMIT')
    return value, commits[0]


class LeakageGuard:
    """Process-local audit hook rejects held-out I/O during calibration."""
    def __init__(self, root):
        self.root=Path(root).resolve();self.reads=set();self.rejected=[]

    def check(self,event,args):
        if event!='open' or not isinstance(args[0],(str,bytes,Path)):return
        path=Path(args[0]).resolve()
        try:relative=path.relative_to(self.root)
        except ValueError:return
        if relative.parts and relative.parts[0] in ('validation','audit'):
            self.rejected.append(str(relative));raise ValueError('PHASE_3B_FAIL_DATA_LEAKAGE_HELD_OUT_IO')
        self.reads.add(str(relative))

    def install(self):
        import sys
        sys.addaudithook(self.check)
