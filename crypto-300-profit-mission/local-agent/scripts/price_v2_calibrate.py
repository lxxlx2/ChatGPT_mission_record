"""Explicit offline calibration; accepts no validation/audit paths or alternate thresholds."""
import argparse,time,resource
from pathlib import Path
from mission_agent.market.calibration.contract import CalibrationOnly,immutable_json,budget,LeakageGuard
from mission_agent.market.calibration.optimizer import optimize


def run(directory,result,winner):
    capability=CalibrationOnly(directory)
    if result.exists() or winner.exists():raise ValueError('CALIBRATION_RESULT_OR_WINNER_ALREADY_FROZEN')
    wall=time.monotonic();cpu=time.process_time()
    guard=LeakageGuard(capability.root);guard.install()
    values,candidate=optimize(capability)
    values['held_out_io_audit']={'held_out_reads':0,'rejected':guard.rejected,'allowed_private_paths':sorted(guard.reads)}
    if candidate:
        from mission_agent.hashing import seal,digest
        candidate=seal({k:v for k,v in candidate.items() if k!='payload_sha256'}|{'calibration_result_hash':digest(values)})
    values['resource']={'wall_seconds':str(time.monotonic()-wall),'cpu_seconds':str(time.process_time()-cpu),
                        'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    # Resource instrumentation is not part of the deterministic winner-result hash.
    immutable_json(result,values)
    if candidate:immutable_json(winner,candidate)
    print(values['status'], 'passing',values['configs_passing'],'of',values['configs_evaluated'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--calibration',type=Path,required=True)
    p.add_argument('--result',type=Path,required=True);p.add_argument('--winner',type=Path,required=True)
    a=p.parse_args();run(a.calibration,a.result,a.winner)
