"""Explicit official network acquisition; does not run optimization or open V1 evidence."""
import argparse
import hashlib
import json
import resource
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from mission_agent.market.calibration.contract import contract, FREEZE, budget, immutable_json
from mission_agent.market.sources.official import Official, parse_rest
from mission_agent.market.cache import save
from mission_agent.market.bar import MINUTE
from mission_agent.hashing import digest, seal
from mission_agent.clock import Clock, stamp


def run(root):
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    baseline = root.parent / 'crypto-monitor-phase3-evidence-20260930'
    cfg = contract(); begin = time.monotonic(); cpu = time.process_time()
    budget(root, baseline)
    history = {}
    for role, (start, end) in cfg['partitions'].items():
        directory = root / role.lower(); directory.mkdir(exist_ok=True, mode=0o700)
        receipt = directory / 'partition.json'
        if receipt.exists():
            history[role] = json.loads(receipt.read_text()); continue
        def download(asset):
            api = Official(); warm = start - cfg['warmup_bars'] * MINUTE
            rows = api.history(asset, warm, end)
            now = int(time.time() * 1000)
            bars = [parse_rest(asset, row, now) for row in rows]
            unique = {b.open_time_utc: b for b in bars if b.is_closed and warm <= b.open_time_utc < end}
            duplicates = len(bars) - len(unique)
            missing = [t for t in range(warm, end, MINUTE) if t not in unique]
            if len(missing) > 120:
                raise ValueError('BOUNDED_REPAIR_LIMIT_EXCEEDED')
            for t in missing:
                for row in api.history(asset, t, t + MINUTE):
                    bar = parse_rest(asset, row, now)
                    if bar.open_time_utc == t and bar.is_closed: unique[t] = bar
            unresolved = sum(t not in unique for t in range(warm, end, MINUTE))
            metadata = {'role': role, 'source': 'binance_spot', 'symbol': asset + 'USDT', 'from': warm, 'to': end,
                        'evaluation_range': [start, end], 'retrieved_at': stamp(Clock().now()),
                        'expected': (end-start)//MINUTE, 'actual': sum(start<=t<end for t in unique),
                        'warmup_bars': cfg['warmup_bars'], 'duplicates': duplicates, 'missing_before_repair': len(missing),
                        'repair_calls': len(missing), 'unresolved_gaps': unresolved, 'requests': api.calls,
                        'rx_body_bytes': api.rx, 'tx_body_bytes': api.tx}
            if unresolved: raise ValueError('UNRESOLVED_HISTORY_GAP')
            ordered = [unique[t].value() for t in sorted(unique)]
            save(directory / (asset+'-raw.json.gz'), rows, {**metadata, 'kind':'RAW_OFFICIAL'})
            manifest = save(directory / (asset+'-canonical.json.gz'), ordered, {**metadata, 'kind':'CANONICAL'})
            print(json.dumps({'role':role, 'asset':asset, 'bars':len(ordered), 'gaps':unresolved}), flush=True)
            return asset, manifest
        with ThreadPoolExecutor(max_workers=2) as pool:
            manifests = dict(pool.map(download, cfg['assets']))
        history[role] = seal({'role':role,'range':[start,end],'freeze_commit':FREEZE,
                             'manifest_hashes':{a:digest(m) for a,m in manifests.items()},'coverage':manifests})
        immutable_json(receipt, history[role]); budget(root, baseline)
    result = {'partitions':history,'wall_seconds':str(time.monotonic()-begin),'cpu_seconds':str(time.process_time()-cpu),
              'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'total_private_bytes':budget(root, baseline)}
    immutable_json(root/'history-summary.json',result)
    print(json.dumps({'history_status':'COMPLETE','wall_seconds':result['wall_seconds'],'peak_rss_bytes':result['peak_rss_bytes']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    run(parser.parse_args().root)
