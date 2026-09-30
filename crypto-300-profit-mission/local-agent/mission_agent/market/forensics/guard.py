"""Read-only baseline checks and audit/network/V3 access denial for forensic runners."""
import json,hashlib,subprocess,os
from pathlib import Path
from ..calibration.contract import MODULE

FREEZE='e30dd63c262d9575aec5be799de14fd6036eac09'
BASE='92634ee5b11a6555ddc74ff9d069f277ecab514b'


def protected_hashes():
    repo=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=MODULE,text=True).strip())
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','crypto-300-profit-mission/local-agent'],cwd=repo,text=True).splitlines()
    result={}
    for name in names:
        path=repo/name
        result[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        frozen=subprocess.check_output(['git','show',BASE+':'+name],cwd=repo)
        if hashlib.sha256(frozen).hexdigest()!=result[str(path)]:raise ValueError('FROZEN_BASELINE_CHANGED')
    plan='docs/PRICE_V2_FAILURE_FORENSICS_PLAN.md'
    original=subprocess.check_output(['git','show',FREEZE+':crypto-300-profit-mission/local-agent/'+plan],cwd=repo)
    if (MODULE/plan).read_bytes()!=original:raise ValueError('FORENSICS_PLAN_CHANGED')
    return result


def preservation(before):
    changed=[p for p,h in before.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    if changed:raise ValueError('FROZEN_ARTIFACT_MUTATION')
    return {'protected_files':len(before),'changed':0,'hashes':before}


class ForensicGuard:
    def __init__(self,input_root,protected):
        self.root=Path(input_root).resolve();self.protected=set(protected);self.reads=set();self.violations=[]

    def check(self,event,args):
        if event=='socket.connect':raise ValueError('FORENSICS_NETWORK_FORBIDDEN')
        if event!='open' or not isinstance(args[0],(str,bytes,Path)):return
        path=Path(args[0]).resolve();mode=args[1] or '';flags=args[2] or 0
        write=any(letter in str(mode) for letter in 'wax+') or bool(flags & (os.O_WRONLY|os.O_RDWR))
        if write and (str(path) in self.protected or 'v3' in path.name.lower()):raise ValueError('FROZEN_OR_V3_WRITE_FORBIDDEN')
        try:relative=path.relative_to(self.root)
        except ValueError:return
        if relative.parts and relative.parts[0]=='audit':
            self.violations.append(str(relative));raise ValueError('AUDIT_ACCESS_FORBIDDEN')
        if write:raise ValueError('BASELINE_EVIDENCE_WRITE_FORBIDDEN')
        self.reads.add(str(relative))

    def install(self):
        import sys
        sys.addaudithook(self.check)
