"""Fixed e069 -> e977 Dashboard-only maintenance for the Nov6 user request.

Default is preflight only. --apply-authorized-dashboard-only reloads the existing
Dashboard LaunchAgent, preserving Scanner/Loop/data. A private prepared plan,
verified backups and isolated old/new HTTP preflight are mandatory. No source
fetch, CA POST, RPC, notification, database restore or trading operation.
"""
import argparse
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import socket
import subprocess
import time
import urllib.parse
import urllib.request

OLD='e069a925b71985c35b75cc8fd01eb75a9c97dd87'
NEW='e977cc09023bdfcc9ce80660aedf2d58d2febc5f'
LABEL='com.jerson.frank-meme.dashboard'
LOOP='com.jerson.frank-meme.loop'
AUTH='USER_20261106_REQUIRES_ACTUAL_LOCAL_FEATURES_LATEST_DASHBOARD_ONLY'
os.umask(0o077)


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def manifest(root):return {str(f.relative_to(root)):sha(f) for f in sorted(root.rglob('*')) if f.is_file()}
def write(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
def run(args):return subprocess.run(args,capture_output=True,text=True,timeout=20)
def git(path,*args):
    r=run(['git','-C',str(path),*args]);assert r.returncode==0
    return r.stdout.strip()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--apply-authorized-dashboard-only',action='store_true')
    args=parser.parse_args();p=json.loads(args.plan.read_text());backup=Path(p['backup'])
    assert p['version']==1 and p['candidate_sha']==NEW and p['old_sha']==OLD and p['authorization']==AUTH
    assert p['label']==LABEL and p['port']==8766 and p['old_backup_verified']
    target='gui/'+str(os.getuid())+'/'+LABEL
    loop='gui/'+str(os.getuid())+'/'+LOOP
    runner=Path(p['runner']);control=Path(p['control']);candidate=Path(p['candidate_agent'])
    assert plistlib.loads(Path(p['plist']).read_bytes())['ProgramArguments']==[str(runner)]
    assert plistlib.loads(Path(p['plist']).read_bytes())['Label']==LABEL
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def get(path,headers=None):
        assert path.startswith('/') and not path.startswith('//')
        with opener.open(urllib.request.Request('http://127.0.0.1:8766'+path,headers=headers or {}),timeout=5) as r:
            assert r.status==200;return r.read()
    def js(path,headers=None):return json.loads(get(path,headers))
    def pid():
        r=run(['launchctl','print',target]);assert r.returncode==0
        match=re.search(r'\bpid = (\d+)',r.stdout);assert match
        return int(match.group(1))
    def no_ca_worker(process):
        r=run(['/usr/sbin/lsof','-a','-p',str(process),'-Fn']);assert r.returncode==0
        assert not any('wallet-cluster-rpc-cache.sqlite' in x for x in r.stdout.splitlines())
    def verify_protected():
        assert all(sha(path)==p['protected_hashes'][name] for name,path in p['protected_files'].items())
        assert manifest(control/'cluster-reports')==p['reports']
    def scanner():
        r=js('/api/runtime')
        assert r['pid']==p['scanner_identity']['pid'] and r['code_commit']==p['scanner_identity']['code_commit']
        assert r['status']=='LIVE' and not r['source_drift'] and r['consecutive_errors']==0
        return r
    def verify_new():
        process=pid();assert process!=p['old_dashboard_pid']
        cwd=run(['/usr/sbin/lsof','-a','-p',str(process),'-d','cwd','-Fn'])
        assert any(x.startswith('n') and Path(x[1:]).resolve()==candidate.resolve() for x in cwd.stdout.splitlines())
        assert manifest(candidate/'mission_agent')==p['candidate_runtime_manifest']
        static=candidate/'mission_agent/mission_control/static'
        assert hashlib.sha256(get('/')).hexdigest()==sha(static/'index.html')
        assert hashlib.sha256(get('/static/app.js')).hexdigest()==sha(static/'app.js')
        f=js('/api/follow-opportunities')
        assert f['schema_version']==2 and f['status']=='SOURCE_ONLY' and f['eligible']==[] and not f['current_balance_verified']
        saved=0
        for file in (control/'cluster-reports/_jobs').glob('*.json'):
            if file.name.endswith('.done.json'):continue
            report=json.loads(file.read_text());job=report['ca_job_id'];mint=report['mint']
            status=js('/api/cluster-analysis?job_id='+job)
            assert status['status']=='DONE'
            same=js('/api/cluster-latest?mint='+urllib.parse.quote(mint,safe='')+'&job_id='+job)
            assert same['ca_job_id']==job and same['mint']==mint;saved+=1
        d1=js('/api/frank-signed-activity?days=1');assert d1['status']=='INDEXED_LOCAL_ONLY'
        d2=js('/api/frank-d2-at-slot',{'X-Frank-D2-Read':'1','Origin':'http://127.0.0.1:8766'})
        assert d2['status']=='BALANCE_AT_OBSERVED_FINALIZED_SLOTS_NOT_LIVE'
        current=scanner();verify_protected();assert run(['launchctl','print',loop]).returncode!=0
        return {'dashboard_pid':process,'saved_exact_jobs_read':saved,'scanner_status':current['status'],
                'scanner_pid_unchanged':True,'source_drift':False,'html_js_match_fixed_source':True,
                'source_recent_count':f['source_recent_count'],'history_count':len(f['not_followed']),
                'eligible_count':0,'d1_http':200,'d2_http':200,'d2_source_observed_at':d2['observed_at_utc']}

    assert git(candidate,'rev-parse','HEAD')==NEW and not git(candidate,'status','--porcelain')
    assert git(Path(p['old_agent']),'rev-parse','HEAD')==OLD and not git(Path(p['old_agent']),'status','--porcelain')
    assert (candidate/'mission_agent/meme/job_checkpoint.py').is_file()
    assert manifest(backup/'old-agent')==json.loads((backup/'old-source-manifest.json').read_text())
    assert manifest(backup/'cluster-reports')==p['reports']
    assert pid()==p['old_dashboard_pid'] and sha(runner)==p['runner_sha_before']
    assert run(['launchctl','print',loop]).returncode!=0
    verify_protected();scanner();no_ca_worker(p['old_dashboard_pid']);time.sleep(.3);no_ca_worker(p['old_dashboard_pid'])
    preflight={'status':'PASS','old_sha':OLD,'new_sha':NEW,'reports_preserved':len(p['reports']),
               'no_open_ca_worker_cache_twice':True,'scanner_unchanged':True,'loop_unloaded':True,'real_rpc_or_ca_post':0}
    write(backup/'switch-preflight.json',preflight)
    if not args.apply_authorized_dashboard_only:print(json.dumps(preflight));return
    smoke=json.loads((backup/'isolated-http-preflight.json').read_text())
    assert smoke['status']=='PASS' and smoke['old_backup']['status']=='PASS' and smoke['candidate']['status']=='PASS'
    lock=(backup/'switch.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    events=[];unloaded=False;changed=False
    def note(stage):
        events.append({'stage':stage,'at':datetime.now(timezone.utc).isoformat()});write(backup/'switch-journal.json',events)
    def command(args,name):
        r=run(args);(backup/(name+'.log')).write_text(r.stdout+r.stderr);return r
    def install(data):
        temp=runner.with_name(runner.name+'.nov6-local-update-tmp')
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,p['runner_mode_before'])
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.chmod(temp,p['runner_mode_before']);os.replace(temp,runner)
    try:
        note('READY_VERIFIED_BACKUP_AND_EXPLICIT_DASHBOARD_UPDATE_AUTHORIZATION')
        assert command(['launchctl','bootout',target],'dashboard-bootout').returncode==0
        unloaded=True;note('OLD_DASHBOARD_UNLOADED')
        deadline=time.monotonic()+10
        while True:
            absent=run(['launchctl','print',target]).returncode!=0
            alive=run(['ps','-p',str(p['old_dashboard_pid']),'-o','pid=']).stdout.strip()
            with socket.socket() as s:s.settimeout(.2);listening=s.connect_ex(('127.0.0.1',8766))==0
            if absent and not alive and not listening:break
            if time.monotonic()>deadline:raise RuntimeError('OLD_DASHBOARD_TEARDOWN_INCOMPLETE')
            time.sleep(.1)
        install((backup/'runner-candidate.sh').read_bytes());changed=True;note('RUNNER_SWITCHED')
        assert command(['launchctl','bootstrap','gui/'+str(os.getuid()),p['plist']],'dashboard-bootstrap').returncode==0
        note('NEW_DASHBOARD_BOOTSTRAPPED')
        deadline=time.monotonic()+18
        while True:
            try:result=verify_new();break
            except (AssertionError,OSError,ValueError):
                if time.monotonic()>deadline:raise RuntimeError('NEW_DASHBOARD_VERIFY_FAILED')
                time.sleep(.3)
        result.update(status='PASS',source_sha=NEW,previous_installed_sha=OLD,executor_sha256=sha(__file__),
                      preserved_report_files=len(p['reports']),protected_file_hashes_unchanged=True,
                      loop_remains_unloaded=True,real_rpc_or_ca_post=0,notification_or_trade=0,
                      dashboard_launchagent_only_reloaded=True,rollback_exercised=False)
        note('VERIFIED');write(backup/'switch-result.json',result);print(json.dumps(result))
    except BaseException as error:
        note('FAILED_'+type(error).__name__)
        if unloaded:
            command(['launchctl','bootout',target],'rollback-candidate-bootout')
            deadline=time.monotonic()+10
            while True:
                absent=run(['launchctl','print',target]).returncode!=0
                with socket.socket() as s:s.settimeout(.2);listening=s.connect_ex(('127.0.0.1',8766))==0
                if absent and not listening:break
                if time.monotonic()>deadline:raise RuntimeError('ROLLBACK_TEARDOWN_BLOCKED') from error
                time.sleep(.1)
            if changed:install((backup/'runner-before.sh').read_bytes())
            restored=command(['launchctl','bootstrap','gui/'+str(os.getuid()),p['plist']],'rollback-old-bootstrap')
            note('ROLLBACK_BOOTSTRAP_'+str(restored.returncode))
            deadline=time.monotonic()+18
            while True:
                try:
                    expected=Path(p['old_agent'])/'mission_agent/mission_control/static/app.js'
                    assert hashlib.sha256(get('/static/app.js')).hexdigest()==sha(expected)
                    scanner();verify_protected();note('ROLLBACK_OLD_HTTP_SOURCE_AND_SCANNER_VERIFIED');break
                except (AssertionError,OSError,ValueError):
                    if time.monotonic()>deadline:raise RuntimeError('ROLLBACK_HTTP_VERIFY_FAILED') from error
                    time.sleep(.3)
        write(backup/'switch-failure.json',{'error_type':type(error).__name__,'unloaded':unloaded,'changed':changed})
        raise


if __name__=='__main__':main()
