"""F3 binding to immutable F2; default-deny, no deployment CLI.

All release observations come from the real read-only sampler, not caller Identity.
No production probe or lifecycle is run by import or construction.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
import time
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import frank_c2a_f3_probe as p

G0_SECONDS = 30.0
STARTUP_SECONDS = 45.0
G4_SECONDS = 30.0
RESTORE_SECONDS = 45.0
TOTAL_OBSERVER_SECONDS = 180.0
ATTEMPT_SECONDS = 10.0
MAX_READINESS_ATTEMPTS = 8

class ReadOnlySampler:
    """All OS/files/HTTP run inside a bounded, production-read-only child.

    Private scratch creation/removal is outside the child; kernel hangs there,
    F2 fsync, or uncatchable signals still need an external emergency supervisor.
    This is not a global hard-termination guarantee for a future release.
    """
    def __init__(self, contract):
        self.contract = contract

    def sample(self, phase, seconds):
        f2 = p.load_f2()
        with tempfile.TemporaryDirectory(prefix='frank-f3-private-observer-') as tmp:
            os.chmod(tmp,0o700)
            path=Path(tmp).resolve()/'contract.json'
            raw=json.dumps(self.contract,sort_keys=True).encode()
            p.need(len(raw)<=128*1024,'CONTRACT_TOO_LARGE')
            fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as f:
                f.write(raw)
            result=f2.bounded_command((sys.executable,'-I','-B',str(Path(p.__file__).resolve()),
                                       '--sample',str(path),phase),timeout=min(seconds,ATTEMPT_SECONDS))
        if result.status=='TIMEOUT':
            raise p.NotReady('OBSERVER_ATTEMPT_TIMEOUT')
        p.need(result.status=='COMPLETE' and result.stdout_eof and result.stderr_eof and
               not result.stdout_truncated and not result.stderr_truncated and not result.stderr,
               'OBSERVER_TRANSPORT_UNVERIFIED')
        try:
            message=json.loads(result.stdout)
        except (ValueError,TypeError) as exc:
            raise p.ProbeError('OBSERVER_INVALID_JSON') from exc
        if not message.get('ok'):
            if message.get('retryable') is True:
                raise p.NotReady('OBSERVER_NOT_READY')
            raise p.ProbeError('OBSERVER_REJECTED')
        p.need(result.returncode==0,'OBSERVER_EXIT')
        return message['sample']

class BoundCaller:
    """Future caller: prepare G0, then bind F2 Plan and fresh phase-specific probe.

    No API accepts Identity or arbitrary network URL. Private contract values pin
    expected local evidence; they do not constitute owner authorization.
    """
    def __init__(self, contract):
        p.validate_contract(contract)
        # Freeze JSON input so later caller mutation cannot change release scope.
        self.contract=json.loads(json.dumps(contract))
        self.f2=p.load_f2()
        self._sampler=ReadOnlySampler(self.contract)
        self._clock=time.monotonic
        self._sleep=time.sleep
        self.started=None
        self.seen=set()
        self.samples=[]
        self.prepared=False
        self.calls=0
        self.plan=None
        self.baseline=None
        self.used=False
        self.old_pid=None
        self.new_pid=None
        self._phase='G0'

    def _observe(self, phase, budget):
        stop=self._clock()+budget
        if phase!='RESTORE':
            stop=min(stop,self.started+TOTAL_OBSERVER_SECONDS)
        attempts=0
        while self._clock()<stop and attempts<MAX_READINESS_ATTEMPTS:
            attempts+=1
            remaining=stop-self._clock()
            try:
                sample=self._sampler.sample(phase,min(ATTEMPT_SECONDS,remaining))
            except p.NotReady:
                if phase in ('G0','G4'):
                    raise
                self._sleep(min(5.0,budget/MAX_READINESS_ATTEMPTS,max(0,stop-self._clock())))
                continue
            p.need(self._clock()<=stop,'STAGE_DEADLINE')
            p.need(sample['phase']==phase and sample['sample_id'] not in self.seen and
                   sample['evidence']=='OS_FILES_SAFE_GET_FRESH' and
                   sample['finished_ns']>=sample['started_ns'] and
                   (not self.samples or sample['started_ns']>=self.samples[-1]['finished_ns']), 'STALE_OR_REUSED_OBSERVATION')
            self.seen.add(sample['sample_id']);self.samples.append(sample)
            return sample
        raise p.ProbeError('STAGE_DEADLINE' if self._clock()>=stop else 'READINESS_ATTEMPT_LIMIT')

    def prepare(self):
        p.need(not self.prepared and self.started is None,'CALLER_ALREADY_PREPARED')
        self.started=self._clock()
        old=self._observe('G0',G0_SECONDS)
        spec=self.contract['services']['dashboard']
        raw,_=p.read_file(spec['runner'],mode=spec['runner_mode'])
        p.need(p.digest(raw)==spec['runner_sha256']==old['runner'],'G0_RUNNER_RACE')
        before=b'LOCAL_AGENT="'+str(p.canonical(self.contract['old']['root'])).encode()+b'"'
        after=b'LOCAL_AGENT="'+str(p.canonical(self.contract['new']['root'])).encode()+b'"'
        p.need(raw.count(before)==1,'RUNNER_BINDING_LINE')
        new=raw.replace(before,after,1)
        p.need(self.f2._one_line_change(raw,new),'RUNNER_BINDING_DELTA')
        self.contract['new_runner_sha256']=p.digest(new)
        self._sampler=ReadOnlySampler(self.contract)
        self.plan=self.f2.Plan(Path(spec['runner']),Path(spec['plist']),spec['label'],
                               Path(self.contract['evidence_dir']),new,p.digest(raw),p.digest(new))
        self.baseline=old['protected'];self.old_pid=old['dashboard']['pid'];self.old_birth=old['dashboard']['birth_us']
        self.prepared=True
        return self.plan

    def probe(self):
        p.need(self.prepared,'G0_REQUIRED')
        spec=self.contract['services']['dashboard']
        phase=self._phase
        budgets={'G0':G0_SECONDS,'G3':STARTUP_SECONDS,'G4':G4_SECONDS,'RESTORE':RESTORE_SECONDS}
        sample=self._observe(phase,budgets[phase])
        p.need(sample['protected']==self.baseline,'PROTECTED_STATE_DRIFT')
        expected=p.OLD if phase in ('G0','RESTORE') else p.PRODUCT
        expected_runner=self.plan.old_runner_sha256 if expected==p.OLD else self.plan.new_runner_sha256
        p.need(sample['source']==expected and sample['runner']==expected_runner,'PHASE_SOURCE_BINDING')
        pid=sample['dashboard']['pid']
        if phase=='G0':
            p.need((pid,sample['dashboard']['birth_us'])==(self.old_pid,self.old_birth),'G0_BASELINE_RESTARTED')
        if phase=='G3':
            p.need(pid!=self.old_pid,'NEW_PROCESS_NOT_ESTABLISHED');self.new_pid=pid;self.new_birth=sample['dashboard']['birth_us'];self._phase='G4'
        elif phase=='G4':
            p.need((pid,sample['dashboard']['birth_us'])==(self.new_pid,self.new_birth),'G4_DASHBOARD_RESTARTED')
        self.calls+=1
        return self.f2.Identity(expected,expected_runner,spec['label'],'127.0.0.1:8766',True,sample['protected'])

    def _valid_lifecycle(self, lifecycle):
        return (type(lifecycle) is self.f2.MacDashboardLifecycle and
                lifecycle.domain==f'gui/{os.getuid()}' and
                lifecycle.plist==str(self.plan.plist))

    def execute(self, lifecycle, *, owner_authorized=False, unknown_f0_risk_accepted=False):
        """Future authorization must exist outside Python; neither bool is a permit.

        lifecycle is explicitly supplied; never instantiate real Mac lifecycle by
        default. Tests supply only synthetic lifecycle. At most one F2 invocation.
        """
        p.need(owner_authorized is True and unknown_f0_risk_accepted is True,'NO_OWNER_AUTH_OR_RISK_DECISION')
        p.need(not self.used,'CALLER_ALREADY_USED')
        if not self.prepared:
            self.prepare()
        p.need(self._valid_lifecycle(lifecycle),'LIFECYCLE_NOT_BOUND')
        self.used=True
        owner=self
        class ScopedLifecycle:
            stops=0
            def bootout(self):
                self.stops+=1
                if self.stops>1:
                    owner._phase='RESTORE'
                return lifecycle.bootout()
            def bootstrap(self):
                owner._phase='G3' if self.stops==1 else 'RESTORE'
                return lifecycle.bootstrap()
        return self.f2.execute_once(self.plan,ScopedLifecycle(),self.probe,authorized=True)
