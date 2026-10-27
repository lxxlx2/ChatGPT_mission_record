"""Synthetic contracts + real read-only collector; no production service inputs."""
import ctypes
import http.server
import http.client
import threading
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import frank_c2a_f3_probe as p
import frank_c2a_f3_binding as b
f2=p.load_f2()

class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.sources={}
        for name,sha in [('old',p.OLD),('new',p.PRODUCT)]:
            root=self.root/name; folder=root/'mission_agent/mission_control/static';folder.mkdir(parents=True)
            rows=[]
            for file in ['index.html','app.js','styles.css']:
                data=(name+file).encode();q=folder/file;q.write_bytes(data);q.chmod(0o444);os.utime(q,(1,1));relative=q.relative_to(root).as_posix()
                rows.append({'path':relative,'git_mode':'100644','sha256':p.digest(data),'size_bytes':len(data),
                             'git_blob_sha1':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
            for q in sorted([root,*[q for q in root.rglob('*') if q.is_dir()]],key=lambda x:len(x.parts),reverse=True):q.chmod(0o555)
            manifest=self.root/(name+'-manifest.json');raw=json.dumps(rows).encode();manifest.write_bytes(raw);manifest.chmod(0o400)
            self.sources[name]={'sha':sha,'root':str(root),'manifest':str(manifest),'manifest_sha256':p.digest(raw),'count':3}
        image=self.root/'python-image';image.write_bytes(b'fixture executable');image.chmod(0o555);os.utime(image,(1,1))
        venv=self.root/'venv';(venv/'bin').mkdir(parents=True);(venv/'bin/python').symlink_to(image)
        self.services={}
        launchers=self.root/'launchers';launchers.mkdir()
        prod=self.root/'prod';prod.mkdir();control=self.root/'control';control.mkdir()
        for key,label in p.LABELS.items():
            runner=launchers/(key+'.sh');raw=f'#!/bin/sh\nVENV="{venv}"\nLOCAL_AGENT="{self.sources["old"]["root"]}"\n'.encode();runner.write_bytes(raw);runner.chmod(0o700);os.utime(runner,(1,1))
            plist=self.root/(label+'.plist');pl=plistlib.dumps({'Label':label,'ProgramArguments':[str(runner)],'RunAtLoad':True});plist.write_bytes(pl);plist.chmod(0o600);os.utime(plist,(1,1))
            self.services[key]={'label':label,'runner':str(runner),'runner_sha256':p.digest(raw),'runner_mode':0o700,
                'plist':str(plist),'plist_sha256':p.digest(pl),'plist_mode':0o600,'launch_argv':[str(runner)],
                'argv':[str(image),key],'executable':str(image),'executable_sha256':p.digest(image.read_bytes()),
                'interpreter':str(image),'interpreter_sha256':p.digest(image.read_bytes()),'source':self.sources['old']}
        evidence=self.root/'evidence';evidence.mkdir(mode=0o700)
        private=control/'frank-d2-private';private.mkdir(mode=0o700);d2=private/'frank-d2-owner-at-slot.json';d2.write_bytes(b'fixture dated balances');d2.chmod(0o600)
        self.health={}
        for key,fields in p.COUNTERS.items():
            q=(prod/'health.json' if key=='v1' else control/'mission-control-health.json');health={f:0 for f in fields}
            health.update({'pid':103 if key=='v1' else 102,'consecutive_errors':0,'candidate_error_count':0,'outcome_error_count':0});q.write_text(json.dumps(health));q.chmod(0o600);self.health[key]=str(q)
        policy=self.root/'policy';policy.write_bytes(b'fixture frozen policy');policy.chmod(0o644)
        self.c={'services':self.services,**self.sources,'protected_files':[{'path':str(policy),'sha256':p.digest(policy.read_bytes()),'mode':0o644}],
                'd2':str(d2),'d2_sha256':p.digest(d2.read_bytes()),'health':self.health,'evidence_dir':str(evidence)}
        self.c['protected_files']=[]
        for role,key,flag in [('loop_policy','loop','--policy'),('v1_policy','v1','--policy'),('v1_registry','v1','--registry'),('v1_authority','v1','--authority-lock')]:
            file=self.root/role;file.write_bytes(('fixture '+role).encode());file.chmod(0o600)
            self.c['protected_files'].append({'role':role,'path':str(file),'sha256':p.digest(file.read_bytes()),'mode':0o600})
            self.services[key]['argv'] += [flag,str(file)]
        self.services['dashboard']['argv'] += ['--production-root',str(prod),'--control-root',str(control)]
        self.services['loop']['argv'] += ['--production-root',str(prod),'--control-root',str(control)]
        self.services['v1']['argv'] += ['--root',str(prod)]
        self.old_bytes=Path(self.services['dashboard']['runner']).read_bytes()
        self.addCleanup(patch.stopall)
        # Only test trust roots are replaced. Production constants remain fixed in
        # committed code; a separate test proves caller-supplied hashes cannot override them.
        patch.object(p,'AUTHORITIES',{sha:(3,s['manifest_sha256']) for s in self.sources.values() for sha in [s['sha']]}).start()
        patch.object(p,'D2_HASH',self.c['d2_sha256']).start()
        self.io=FakeOS(self)
    def snapshot(self,phase='G0'):
        return p.collect(self.c,phase,self.io)

class FakeOS:
    def __init__(self,h):self.h=h;self.state='old';self.calls=[];self.ready=True;self.late_restart=False;self.birth={}
    def command(self,argv,timeout=2):
        self.calls.append(argv)
        if argv[:2]==['/bin/launchctl','print-disabled']:return '{}'
        if argv[0]=='/bin/launchctl':
            key=next(k for k,s in self.h.services.items() if argv[2].endswith(s['label']))
            pid={'dashboard':201 if self.state=='new' else 101,'loop':102,'v1':103}[key]
            return f' state = running\n pid = {pid}\n'
        if '-a' in argv:
            pid=int(argv[3]);name='new' if pid==201 else 'old'
            root=self.h.sources[name]['root'] if pid in (101,201) else self.h.services['loop' if pid==102 else 'v1']['source']['root']
            return 'p'+str(pid)+'\nn'+root+'\n'
        pid=201 if self.state=='new' else 101
        return f'p{pid}\nn127.0.0.1:8766\np999\nn*:7000\nn*:7000\n'
    def process(self,pid):
        key={101:'dashboard',201:'dashboard',102:'loop',103:'v1'}[pid];spec=self.h.services[key]
        return {'pid':pid,'birth_us':self.birth.get(pid,1_700_000_000_000_000)+(1 if self.late_restart and pid==201 else 0),
                'executable':spec['executable'],'argv':spec['argv']}
    def get(self,path):
        if not self.ready:raise p.NotReady('fixture starting')
        if path=='/api/runtime':return json.dumps({'status':'LIVE','pid':103,'production_db_readable':True,'pid_alive':True}).encode()
        if path.startswith('/api/cluster-latest'):
            return json.dumps({'mint':'2'*32,'observed_at':1700000000,'coverage':{'special_normalization_complete':False}}).encode()
        return (Path(self.h.sources[self.state]['root'])/'mission_agent/mission_control/static'/p.STATIC[path]).read_bytes()

class TestCollector(Fixture):
    def test_real_files_and_os_outputs_build_fresh_snapshot(self):
        a=self.snapshot();z=self.snapshot();self.assertNotEqual(a['sample_id'],z['sample_id']);self.assertEqual(a['protected'],z['protected'])
        self.assertEqual(a['browser'],'NOT_VERIFIED');self.assertGreaterEqual(len(self.io.calls),14)
    def test_production_authority_not_overridable_by_contract(self):
        with patch.object(p,'AUTHORITIES',{p.OLD:(446,'e'*64),p.PRODUCT:(448,'9'*64)}):
            with self.assertRaisesRegex(p.ProbeError,'MANIFEST_AUTHORITY'):self.snapshot()
    def test_no_arbitrary_get_or_command(self):
        io=p.NativeIO()
        for path in ['/api/cluster-analysis?job_id=x','http://external.invalid','/api/cluster-latest?mint=x&foo=y']:
            with self.assertRaisesRegex(p.ProbeError,'GET_NOT_WHITELISTED'):io.get(path)
        with self.assertRaisesRegex(p.ProbeError,'WHITELIST'):io.command(['/bin/launchctl','bootstrap','fake'])
    def test_source_mutation_is_fatal(self):
        q=Path(self.c['old']['root'])/'mission_agent/mission_control/static/app.js';q.chmod(0o644);q.write_bytes(b'bad');q.chmod(0o444)
        with self.assertRaisesRegex(p.ProbeError,'SOURCE_BYTES'):self.snapshot()
    def test_extra_file_is_fatal(self):
        root=Path(self.c['old']['root']);root.chmod(0o755);q=root/'extra';q.write_bytes(b'extra');q.chmod(0o444);root.chmod(0o555)
        with self.assertRaisesRegex(p.ProbeError,'SOURCE_FILE_SET'):self.snapshot()
    def test_source_symlink_rejected(self):
        root=Path(self.c['old']['root']);root.chmod(0o755);(root/'alias').symlink_to(self.root/'policy');root.chmod(0o555)
        with self.assertRaisesRegex(p.ProbeError,'SYMLINK'):self.snapshot()
    def test_process_argv_is_not_ps_text_guess(self):
        orig=self.io.process
        def bad(pid):
            d=orig(pid);d['argv']=d['argv']+['unexpected'];return d
        self.io.process=bad
        with self.assertRaisesRegex(p.ProbeError,'PROCESS_ARGV'):self.snapshot()
    def test_restart_during_safe_get_is_rejected(self):
        orig=self.io.get
        def late(path):
            data=orig(path)
            if path=='/api/runtime':self.io.state='new'
            return data
        self.io.get=late
        with self.assertRaisesRegex(p.ProbeError,'PROCESS_CHANGED'):self.snapshot()
    def test_port_collision_is_rejected(self):
        orig=self.io.command
        self.io.command=lambda a,timeout=2:orig(a,timeout)+('p999\nn127.0.0.1:8766\n' if '-iTCP' in a else '')
        with self.assertRaisesRegex(p.ProbeError,'DASHBOARD_LISTENER'):self.snapshot()
    def test_static_http_source_mismatch(self):
        self.io.get=lambda path:b'wrong'
        with self.assertRaisesRegex(p.ProbeError,'HTTP_STATIC'):self.snapshot()
    def test_d2_permission_and_hash_gates(self):
        Path(self.c['d2']).chmod(0o644)
        with self.assertRaisesRegex(p.ProbeError,'FILE_MODE'):self.snapshot()
        Path(self.c['d2']).chmod(0o600);Path(self.c['d2']).write_bytes(b'wrong')
        with self.assertRaisesRegex(p.ProbeError,'D2_HASH'):self.snapshot()
    def test_missing_or_stale_notifications_fail_closed(self):
        q=Path(self.health['loop']);d=json.loads(q.read_text());del d['manual_review_gmail_count'];q.write_text(json.dumps(d))
        with self.assertRaisesRegex(p.ProbeError,'COUNTERS'):self.snapshot()
        os.utime(q,(1,1))
        with self.assertRaisesRegex(p.ProbeError,'HEALTH_STALE'):self.snapshot()
    def test_history_is_not_new_completion(self):
        self.c['history']={'mint':'2'*32};r=self.snapshot();self.assertEqual(r['cache']['state'],'HISTORICAL_NOT_NEW_ANALYSIS');self.assertFalse(r['cache']['job_match']);self.assertFalse(r['cache']['normalization_complete'])
    def test_known_job_report_mismatch_is_rejected(self):
        self.c['history']={'mint':'2'*32,'job_id':'a'*32}
        with self.assertRaisesRegex(p.ProbeError,'CACHE_JOB_MISMATCH'):self.snapshot()
    def test_disabled_existing_service_cannot_be_assumed_restartable(self):
        old=self.io.command
        self.io.command=lambda a,timeout=2:'{ "com.jerson.frank-meme.dashboard" => true }' if a[1]=='print-disabled' else old(a,timeout)
        with self.assertRaisesRegex(p.ProbeError,'SERVICE_DISABLED'):self.snapshot()
    def test_running_process_does_not_prove_interpreter_execute_permission(self):
        Path(self.services['dashboard']['executable']).chmod(0o444)
        with self.assertRaisesRegex(p.ProbeError,'EXECUTABLE_ACCESS'):self.snapshot()
    def test_protected_owned_source_profile_never_weakens_dashboard(self):
        import shutil
        src=Path(self.c['old']['root']);target=self.root/'protected-working-source'
        shutil.copytree(src,target)
        for q in [target,*target.rglob('*')]:
            q.chmod(0o755 if q.is_dir() else 0o644)
            os.utime(q,(1,1))
        spec=dict(self.c['old'],root=str(target),physical_profile='OWNED_SOURCE')
        for key in ('loop','v1'):
            self.services[key]['source']=spec
            runner=Path(self.services[key]['runner']);data=runner.read_bytes().replace(str(src).encode(),str(target).encode());runner.write_bytes(data);os.utime(runner,(1,1));self.services[key]['runner_sha256']=p.digest(data)
        self.assertEqual(self.snapshot()['source'],p.OLD)
        self.c['old']['physical_profile']='OWNED_SOURCE'
        with self.assertRaisesRegex(p.ProbeError,'DASHBOARD_MUST_BE_IMMUTABLE'):self.snapshot()
    def test_same_bytes_d2_copy_cannot_replace_actual_control_source(self):
        copy=self.root/'copy-private';copy.mkdir(mode=0o700);file=copy/'d2.json'
        file.write_bytes(Path(self.c['d2']).read_bytes());file.chmod(0o600);self.c['d2']=str(file)
        with self.assertRaisesRegex(p.ProbeError,'RUNTIME_DATA_ROOT_BINDING'):self.snapshot()
    def test_policy_and_authority_sources_cannot_be_omitted(self):
        self.c['protected_files']=[]
        with self.assertRaisesRegex(p.ProbeError,'PROTECTED_FILE_ROLES'):self.snapshot()
    def test_policy_file_must_match_real_argv_pointer(self):
        self.c['protected_files'][0]['path']=str(self.root/'different')
        with self.assertRaisesRegex(p.ProbeError,'PROTECTED_ARGV_BINDING'):self.snapshot()
    def test_worker_rejects_untrusted_contract_without_contacting_service(self):
        # Unpatched child retains actual production authority constants: our synthetic
        # manifest must fail before OS or localhost access. This is a real worker.
        caller=b.ReadOnlySampler(self.c)
        with self.assertRaisesRegex(p.ProbeError,'OBSERVER_REJECTED'):caller.sample('G0',2)

class TestBinding(Fixture):
    def caller(self):
        x=b.BoundCaller(self.c);h=self
        class Sampler:
            def sample(self,phase,seconds):return p.collect(x.contract,phase,h.io)
        x._sampler=Sampler()
        # prepare recreates NativeSampler only after G0; substitute after prepare.
        x.prepare();x._sampler=Sampler();x._valid_lifecycle=lambda life:True;return x
    def lifecycle(self,fail=False):
        h=self
        class Lifecycle:
            stops=0
            starts=0
            def bootout(self):self.stops+=1;return f2.Captured('COMPLETE',0,b'',b'',0,0,'','',True,True,False,False)
            def bootstrap(self):
                self.starts+=1;h.io.state='new' if self.stops==1 else 'old';h.io.birth[201 if h.io.state=='new' else 101]=time.time_ns()//1000
                return f2.Captured('COMPLETE',5 if fail and self.stops==1 else 0,b'',b'',0,0,'','',True,True,False,False)
        return Lifecycle()
    def test_f2_bound_end_to_end_fresh_g0_g3_g4(self):
        x=self.caller();v=x.execute(self.lifecycle(),owner_authorized=True,unknown_f0_risk_accepted=True)
        self.assertEqual(v.status,'CUTOVER_PROBE_PASS_NOT_DEPLOY_AUTH');self.assertEqual([s['phase'] for s in x.samples],['G0','G0','G3','G4']);self.assertEqual(len(x.seen),4)
        with self.assertRaisesRegex(p.ProbeError,'ALREADY_USED'):x.execute(self.lifecycle(),owner_authorized=True,unknown_f0_risk_accepted=True)
    def test_failed_bootstrap_has_independent_restore_observation(self):
        x=self.caller();life=self.lifecycle(fail=True);v=x.execute(life,owner_authorized=True,unknown_f0_risk_accepted=True)
        self.assertEqual(v.status,'ROLLED_BACK_STOP');self.assertEqual(x.samples[-1]['phase'],'RESTORE');self.assertEqual(life.starts,2)
    def test_restore_does_not_depend_on_failed_candidate_integrity(self):
        x=self.caller();life=self.lifecycle();orig=life.bootstrap
        def boot():
            result=orig()
            if life.stops==1:
                q=Path(self.c['new']['root'])/'mission_agent/mission_control/static/app.js'
                q.chmod(0o644);q.write_bytes(b'candidate corrupt');q.chmod(0o444)
            return result
        life.bootstrap=boot
        verdict=x.execute(life,owner_authorized=True,unknown_f0_risk_accepted=True)
        self.assertEqual(verdict.status,'ROLLED_BACK_STOP')
        self.assertEqual(x.samples[-1]['phase'],'RESTORE')
    def test_native_lifecycle_must_match_exact_bound_domain_and_plist(self):
        x=self.caller();del x._valid_lifecycle
        # Constructor reads only this fixture plist, never invokes launchctl.
        with patch.object(f2.os,'uname',return_value=type('U',(),{'sysname':'Darwin'})()):
            life=f2.MacDashboardLifecycle(x.plan)
        self.assertTrue(x._valid_lifecycle(life))
        life.plist=str(self.root/'different.plist');self.assertFalse(x._valid_lifecycle(life))
        life.plist=str(x.plan.plist);life.domain='gui/999999';self.assertFalse(x._valid_lifecycle(life))
    def test_public_caller_rejects_unbound_lifecycle_before_any_command(self):
        x=self.caller();del x._valid_lifecycle;life=self.lifecycle()
        # This protocol object has no verified F2 domain/plist binding.
        with self.assertRaisesRegex(p.ProbeError,'LIFECYCLE_NOT_BOUND'):
            x.execute(life,owner_authorized=True,unknown_f0_risk_accepted=True)
        self.assertEqual((life.stops,life.starts),(0,0))
    def test_no_authorization_or_risk_acceptance(self):
        x=b.BoundCaller(self.c)
        with self.assertRaisesRegex(p.ProbeError,'NO_OWNER'):x.execute(self.lifecycle())
        self.assertIsNone(x.started)
    def test_protected_drift_never_becomes_pass(self):
        x=self.caller();q=Path(self.health['v1']);d=json.loads(q.read_text());d['gmail_sent_verified']=1;q.write_text(json.dumps(d))
        with self.assertRaisesRegex(p.ProbeError,'PROTECTED_STATE_DRIFT'):x.probe()
    def test_reused_sample_is_rejected(self):
        x=self.caller();sample=x.samples[0]
        class Reuse:
            def sample(self,*a):return sample
        x._sampler=Reuse()
        with self.assertRaisesRegex(p.ProbeError,'REUSED'):x.probe()
    def test_restore_failure_is_unverified(self):
        x=self.caller();life=self.lifecycle(fail=True);original=life.bootstrap
        def boot():
            r=original()
            if life.stops>1:self.io.ready=False
            return r
        life.bootstrap=boot;clock=[0.];x._clock=lambda:clock[0];x.started=0.;x._sleep=lambda n:clock.__setitem__(0,clock[0]+n)
        v=x.execute(life,owner_authorized=True,unknown_f0_risk_accepted=True);self.assertEqual(v.status,'ROLLBACK_UNVERIFIED_STOP');self.assertLessEqual(clock[0],b.RESTORE_SECONDS);self.assertGreater(clock[0],0)
    def test_g4_same_pid_new_birth_is_rejected(self):
        x=self.caller();life=self.lifecycle();original=x._sampler.sample
        def sample(phase,seconds):
            if phase=='G4':self.io.late_restart=True
            return original(phase,seconds)
        x._sampler.sample=sample
        v=x.execute(life,owner_authorized=True,unknown_f0_risk_accepted=True);self.assertEqual(v.status,'ROLLED_BACK_STOP')
    def test_readiness_wait_is_bounded_not_global_command_claim(self):
        x=self.caller();clock=[0.];x._clock=lambda:clock[0];x.started=0.;x._sleep=lambda n:clock.__setitem__(0,clock[0]+n)
        class Pending:
            def sample(self,*a):raise p.NotReady('not yet')
        x._sampler=Pending()
        with self.assertRaisesRegex(p.ProbeError,'STAGE_DEADLINE'):x._observe('G3',1.)
        self.assertLessEqual(clock[0],1.01)
    def test_fresh_nonce_does_not_legitimize_old_snapshot(self):
        x=self.caller();saved=dict(x.samples[0]);saved['sample_id']='f'*32
        class Replay:
            def sample(self,*a):return saved
        x._sampler=Replay()
        with self.assertRaisesRegex(p.ProbeError,'STALE_OR_REUSED'):x.probe()
    def test_dashboard_restart_between_prepare_and_f2_g0_is_rejected(self):
        x=self.caller();self.io.birth[101]=time.time_ns()//1000
        with self.assertRaisesRegex(p.ProbeError,'G0_BASELINE_RESTARTED'):x.probe()
    def test_hung_readonly_worker_is_bounded_and_reaped(self):
        helper=self.root/'worker.py';fifo=self.root/'blocked-fifo';os.mkfifo(fifo)
        helper.write_text("import os,json,sys\nc=json.load(open(sys.argv[2]));os.open(c['test_fifo'],os.O_RDONLY)\n")
        sampler=b.ReadOnlySampler({'test_fifo':str(fifo)})
        started=time.monotonic()
        with patch.object(p,'__file__',str(helper)),patch.object(p,'load_f2',return_value=f2),patch.object(b,'ATTEMPT_SECONDS',.2):
            with self.assertRaisesRegex(p.NotReady,'TIMEOUT'):sampler.sample('G0',1)
        self.assertLess(time.monotonic()-started,2.)
    def test_f2_adapter_digest_is_fixed(self):
        with patch.object(p,'F2_FILE_SHA','0'*64):
            with self.assertRaisesRegex(p.ProbeError,'F2_BYTES_UNAPPROVED'):b.BoundCaller(self.c)

class TestHTTPTransport(unittest.TestCase):
    def setUp(self):
        self.requests=[];self.code=200;self.body=b'{"status":"LIVE"}';self.length=None;owner=self
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                owner.requests.append((self.command,self.path,self.headers.get('Host')))
                self.send_response(owner.code)
                self.send_header('Content-Length',str(len(owner.body) if owner.length is None else owner.length))
                if owner.code==302:self.send_header('Location','http://forbidden.invalid/')
                self.end_headers();self.wfile.write(owner.body)
            def log_message(self,*a):pass
        self.server=http.server.HTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever);self.thread.start()
        self.addCleanup(self.close)
        real=http.client.HTTPConnection
        def connect(host,port,timeout):
            self.assertEqual((host,port),('127.0.0.1',8766))
            return real('127.0.0.1',self.server.server_port,timeout=timeout)
        self.patch=patch.object(p.http.client,'HTTPConnection',side_effect=connect);self.patch.start()
    def close(self):
        self.patch.stop();self.server.shutdown();self.server.server_close();self.thread.join(2)
    def test_real_random_port_fixture_get_only(self):
        self.assertEqual(p.NativeIO().get('/api/runtime'),self.body)
        self.assertEqual(self.requests,[('GET','/api/runtime','127.0.0.1:8766')])
    def test_redirect_never_followed(self):
        self.code=302
        with self.assertRaisesRegex(p.ProbeError,'GET_STATUS'):p.NativeIO().get('/api/runtime')
        self.assertEqual(len(self.requests),1)
    def test_short_body_is_not_success(self):
        self.length=len(self.body)+5
        with self.assertRaises(p.ProbeError):p.NativeIO().get('/api/runtime')
    def test_oversize_declared_body_rejected(self):
        self.length=4*1024*1024+1
        with self.assertRaisesRegex(p.ProbeError,'GET_LENGTH'):p.NativeIO().get('/api/runtime')

class TestDarwinKernel(unittest.TestCase):
    @unittest.skipUnless(sys.platform=='darwin','real Darwin ABI check only')
    def test_own_process_only_no_production_visit(self):
        result=p.kernel_process(os.getpid());self.assertEqual(result['pid'],os.getpid());self.assertGreater(result['birth_us'],0);self.assertTrue(result['argv']);self.assertTrue(Path(result['executable']).is_file())

if __name__=='__main__':unittest.main()
