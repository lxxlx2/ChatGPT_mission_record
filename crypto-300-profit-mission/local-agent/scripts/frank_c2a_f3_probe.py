"""F3 read-only OS/file/GET sampler. No lifecycle commands or product imports.

Private contracts pin expected artifacts; they are not permission or signatures.
A subprocess worker bounds a sampling attempt. It never writes production paths.
"""
from __future__ import annotations
import ctypes
import hashlib
import http.client
import json
import math
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import stat
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
F2_FILE_SHA = 'aa010235d30dec625847bb5ae132f25e830cecb2ffa0c30f5591dc2edc55446a'
PRODUCT = '296f35a8b6dffe1b2384f77b8768aa799a68ed0d'
OLD = '914e9e47fed2e60bc24690fcb083413a64d4e681'
AUTHORITIES = {
    PRODUCT: (448, '9e749869826c02db2986a133fd7c90801e1452a842cde14e9cc09fadc4ee2860'),
    OLD: (446, 'eb30010e4973f2d886c2fd7e0054b248c8f041864a5dc545fe8a032de2d1195f'),
}
LABELS = {'dashboard': 'com.jerson.frank-meme.dashboard',
          'loop': 'com.jerson.frank-meme.loop',
          'v1': 'com.jerson.crypto-monitor-frank-local'}
D2_HASH = 'a1c3fcce95a8271baf585e30ea7348424eb4799cb2a26d513a142270253890d0'
STATIC = {'/': 'index.html', '/static/app.js': 'app.js', '/static/styles.css': 'styles.css'}
COUNTERS = {'v1': ('gmail_blocked', 'gmail_failed', 'gmail_pending', 'gmail_sent_unverified', 'gmail_sent_verified'),
            'loop': ('manual_review_gmail_count', 'manual_review_local_count', 'manual_review_total_count')}

class ProbeError(RuntimeError):
    pass
class NotReady(ProbeError):
    pass

def need(ok, code):
    if not ok:
        raise ProbeError(code)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def load_f2():
    p = Path(__file__).with_name('frank_c2a_f2_one_shot.py')
    need(digest(p.read_bytes()) == F2_FILE_SHA, 'F2_BYTES_UNAPPROVED')
    import frank_c2a_f2_one_shot
    need(Path(frank_c2a_f2_one_shot.__file__).resolve() == p.resolve(), 'F2_MODULE_ORIGIN')
    return frank_c2a_f2_one_shot

def canonical(path):
    p = Path(path)
    need(p.is_absolute() and p == p.resolve(strict=True), 'NONCANONICAL_PATH')
    return p

def read_file(path, limit=4*1024*1024, mode=None):
    p = canonical(path)
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and not before.st_mode & 0o7000, 'FILE_IDENTITY')
        need(before.st_size <= limit and not before.st_mode & 0o022, 'FILE_SIZE_OR_WRITABLE')
        if mode is not None:
            need(stat.S_IMODE(before.st_mode) == mode, 'FILE_MODE')
        with os.fdopen(fd, 'rb', closefd=False) as f:
            data = f.read(limit+1)
        after = os.fstat(fd)
        need(len(data) <= limit and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'FILE_READ_RACE')
        return data, after
    finally:
        os.close(fd)

def source(spec):
    root = canonical(spec['root'])
    raw, _ = read_file(spec['manifest'], 1024*1024)
    need(digest(raw) == spec['manifest_sha256'], 'MANIFEST_HASH')
    rows = json.loads(raw)
    # G1 canonical list; legacy protected-service manifests may use path->hash/mode.
    if isinstance(rows, dict):
        rows = [dict(value, path=path) for path, value in sorted(rows.items())]
    need(isinstance(rows, list) and len(rows) == spec['count'] > 0, 'MANIFEST_COUNT')
    profile=spec.get('physical_profile','IMMUTABLE')
    need(profile in ('IMMUTABLE','OWNED_SOURCE'),'SOURCE_PHYSICAL_PROFILE')
    expected = set(); latest_ns = 0
    for row in rows:
        name = row['path']; parts = PurePosixPath(name)
        need(name and not parts.is_absolute() and str(parts) == name and
             not set(parts.parts) & {'.', '..', '.git'} and name not in expected, 'MANIFEST_PATH')
        expected.add(name)
        need(row['git_mode'] in ('100644', '100755'), 'GIT_MODE')
        mode = (0o555 if row['git_mode'] == '100755' else 0o444) if profile=='IMMUTABLE' else (0o755 if row['git_mode']=='100755' else 0o644)
        data, st = read_file(root / name, mode=mode)
        need(digest(data) == row['sha256'], 'SOURCE_BYTES')
        if 'git_blob_sha1' in row:
            blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            need(blob == row['git_blob_sha1'] and len(data) == row['size_bytes'], 'SOURCE_GIT_BLOB')
        latest_ns = max(latest_ns, st.st_mtime_ns)
    actual = set()
    for p in [root, *root.rglob('*')]:
        need(not p.is_symlink(), 'SOURCE_SYMLINK')
        if p.is_dir():
            need(p.stat().st_uid == os.getuid() and stat.S_IMODE(p.stat().st_mode) == (0o555 if profile=='IMMUTABLE' else 0o755), 'SOURCE_DIR_MODE')
        elif p.is_file():
            actual.add(p.relative_to(root).as_posix())
        else:
            raise ProbeError('SOURCE_SPECIAL_FILE')
    need(actual == expected, 'SOURCE_FILE_SET')
    return {'sha': spec['sha'], 'manifest': digest(raw), 'latest_ns': latest_ns}

# Apple XNU public proc_bsdinfo ABI, matching PR39's precise-start technique.
class BSD(ctypes.Structure):
    _fields_ = ([(n, ctypes.c_uint32) for n in ('flags','status','xstatus','pid','ppid','uid','gid','ruid','rgid','svuid','svgid','reserved')] +
                [('comm',ctypes.c_char*16),('name',ctypes.c_char*32)] +
                [(n,ctypes.c_uint32) for n in ('nfiles','pgid','pjobc','tdev','tpgid')] +
                [('nice',ctypes.c_int32),('sec',ctypes.c_uint64),('usec',ctypes.c_uint64)])

def kernel_process(pid):
    need(sys.platform == 'darwin' and type(pid) is int and pid > 0, 'DARWIN_KERNEL_REQUIRED')
    lib = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
    lib.proc_pidinfo.argtypes = (ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int)
    lib.proc_pidinfo.restype = ctypes.c_int
    b = BSD(); size = ctypes.sizeof(b)
    need(lib.proc_pidinfo(pid,3,0,ctypes.byref(b),size) == size and b.pid == pid and
         b.uid == os.getuid() and b.status not in (4,5) and b.sec > 0 and b.usec < 1_000_000, 'KERNEL_BIRTH')
    image = ctypes.create_string_buffer(4096)
    lib.proc_pidpath.argtypes = (ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32)
    lib.proc_pidpath.restype = ctypes.c_int
    need(lib.proc_pidpath(pid,image,4096) > 0, 'KERNEL_EXECUTABLE')
    # KERN_PROCARGS2=49 (Apple sys/sysctl.h). Parse argc/argv only; never decode,
    # persist or return the remaining environment area from the kernel buffer.
    libc = ctypes.CDLL(None, use_errno=True)
    libc.sysctl.argtypes = (ctypes.POINTER(ctypes.c_int),ctypes.c_uint,ctypes.c_void_p,
                           ctypes.POINTER(ctypes.c_size_t),ctypes.c_void_p,ctypes.c_size_t)
    libc.sysctl.restype = ctypes.c_int
    mib = (ctypes.c_int*3)(1,49,pid); count = ctypes.c_size_t(0)
    need(libc.sysctl(mib,3,None,ctypes.byref(count),None,0) == 0 and 4 < count.value <= 2*1024*1024, 'KERNEL_ARG_SIZE')
    buf = ctypes.create_string_buffer(count.value)
    need(libc.sysctl(mib,3,buf,ctypes.byref(count),None,0) == 0, 'KERNEL_ARG_READ')
    raw = buf.raw[:count.value]; argc = int.from_bytes(raw[:4],sys.byteorder,signed=True)
    need(0 < argc <= 512, 'KERNEL_ARGC')
    pos = raw.index(b'\0',4)+1
    while pos < len(raw) and raw[pos] == 0:
        pos += 1
    args = []
    for _ in range(argc):
        end = raw.index(b'\0',pos); args.append(raw[pos:end].decode('utf-8')); pos = end+1
    return {'pid':pid, 'birth_us':b.sec*1_000_000+b.usec,
            'executable':image.value.decode(), 'argv':args}

def parse_listeners(text):
    result = []; pid = None
    for line in text.splitlines():
        if line.startswith('p'):
            need(line[1:].isdigit(), 'LISTENER_PID'); pid = int(line[1:])
        elif line.startswith('n'):
            need(pid is not None, 'LISTENER_OWNER'); result.append([pid,line[1:]])
    return sorted(result)

class NativeIO:
    def command(self, argv, timeout=2):
        # No caller-controlled verbs: all callers below construct these exact forms.
        allowed = ((argv[:2] == ['/bin/launchctl','print'] and len(argv)==3 and
                    argv[2] in [f'gui/{os.getuid()}/{x}' for x in LABELS.values()]) or
                   (argv == ['/bin/launchctl','print-disabled',f'gui/{os.getuid()}']) or
                   (argv[:2] == ['/usr/sbin/lsof','-a'] and len(argv)==8 and argv[2:3]==['-p'] and
                    argv[3].isdigit() and argv[4:] == ['-d','cwd','-Fn','-nP']) or
                   argv == ['/usr/sbin/lsof','-nP','-iTCP','-sTCP:LISTEN','-Fpn'])
        need(allowed, 'COMMAND_NOT_READONLY_WHITELIST')
        r = load_f2().bounded_command(tuple(argv),timeout=timeout)
        if not r.ok or r.stdout_truncated or r.stderr_truncated or r.stderr or not r.stdout_eof or not r.stderr_eof:
            if argv[:2] == ['/bin/launchctl','print']:
                raise NotReady('SERVICE_NOT_OBSERVED')
            raise ProbeError('READONLY_COMMAND_INCOMPLETE')
        return r.stdout.decode('utf-8')

    def process(self, pid):
        return kernel_process(pid)

    def get(self, path):
        allowed = path in {*STATIC, '/api/runtime'} or re.fullmatch(
            r'/api/cluster-latest\?mint=[1-9A-HJ-NP-Za-km-z]{32,44}(?:&job_id=[0-9a-f]{32})?',path)
        need(allowed, 'GET_NOT_WHITELISTED')
        conn = http.client.HTTPConnection('127.0.0.1',8766,timeout=2)
        try:
            conn.request('GET',path,headers={'Host':'127.0.0.1:8766','Origin':'http://127.0.0.1:8766'})
            r = conn.getresponse()
            need(r.status == 200 and r.getheader('Transfer-Encoding') is None, 'GET_STATUS_OR_FRAMING')
            length = r.getheader('Content-Length')
            need(length is not None and length.isdigit() and int(length) <= 4*1024*1024, 'GET_LENGTH')
            data = r.read(int(length)+1)
            need(len(data)==int(length), 'GET_BODY_INCOMPLETE')
            return data
        except (OSError, http.client.HTTPException) as exc:
            raise NotReady('DASHBOARD_GET_UNAVAILABLE') from exc
        finally:
            conn.close()

def validate_contract(c):
    need(set(c['services']) == set(LABELS), 'SERVICE_SET')
    for key, label in LABELS.items():
        need(c['services'][key]['label'] == label, 'LABEL_AUTHORITY')
    for name, sha in [('old',OLD),('new',PRODUCT)]:
        s=c[name]; need(s.get('physical_profile','IMMUTABLE')=='IMMUTABLE','DASHBOARD_MUST_BE_IMMUTABLE'); need((s['sha'],s['count'],s['manifest_sha256']) == (sha,*AUTHORITIES[sha]), 'MANIFEST_AUTHORITY')
    need(c['d2_sha256'] == D2_HASH, 'D2_AUTHORITY')
    required={'loop_policy':('loop','--policy'),'v1_policy':('v1','--policy'),
              'v1_registry':('v1','--registry'),'v1_authority':('v1','--authority-lock')}
    files={item['role']:item for item in c['protected_files']}
    need(len(files)==len(c['protected_files']) and set(required)<=set(files),'PROTECTED_FILE_ROLES')
    for role,(service,flag) in required.items():
        argv=c['services'][service]['argv']
        need(argv.count(flag)==1 and argv.index(flag)+1<len(argv) and
             Path(argv[argv.index(flag)+1])==Path(files[role]['path']),'PROTECTED_ARGV_BINDING')
    def root_arg(key, flag):
        argv=c['services'][key]['argv']
        need(argv.count(flag)==1 and argv.index(flag)+1<len(argv),'RUNTIME_ROOT_ARG')
        return canonical(argv[argv.index(flag)+1])
    production=root_arg('dashboard','--production-root');control=root_arg('dashboard','--control-root')
    need(root_arg('loop','--production-root')==production and root_arg('loop','--control-root')==control and
         root_arg('v1','--root')==production,'RUNTIME_ROOTS_DISAGREE')
    need(Path(c['health']['v1'])==production/'health.json' and
         Path(c['health']['loop'])==control/'mission-control-health.json' and
         Path(c['d2'])==control/'frank-d2-private/frank-d2-owner-at-slot.json','RUNTIME_DATA_ROOT_BINDING')
    evidence=canonical(c['evidence_dir'])
    forbidden=[production,control,canonical(c['old']['root']),canonical(c['new']['root']),
               canonical(Path(c['services']['dashboard']['runner']).parent)]
    need(not any(evidence==x or evidence.is_relative_to(x) for x in forbidden),'EVIDENCE_IN_LIVE_PATH')
    if c.get('history'):
        h=c['history']
        need(set(h) <= {'mint','job_id'} and re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{32,44}',h['mint']) and
             (not h.get('job_id') or re.fullmatch(r'[0-9a-f]{32}',h['job_id'])), 'HISTORY_SCOPE')

def collect(c, phase, io=None):
    """Every call reads OS/files/GET anew. Tests may inject OS I/O, never Identity."""
    need(phase in ('G0','G3','G4','RESTORE'), 'PHASE')
    validate_contract(c); io = io or NativeIO(); started = time.time_ns()
    expected = c['new'] if phase in ('G3','G4') else c['old']
    verified = {key:source(c[key]) for key in (('old',) if phase=='RESTORE' else ('old','new'))}
    observations = {}; latest = {}
    disabled=io.command(['/bin/launchctl','print-disabled',f'gui/{os.getuid()}'])
    need('{' in disabled and '}' in disabled,'DISABLED_STATE_UNVERIFIED')
    for key, spec in c['services'].items():
        text = io.command(['/bin/launchctl','print',f'gui/{os.getuid()}/{spec["label"]}'])
        found = re.findall(r'^\s*pid = (\d+)\s*$',text,re.M)
        if len(found) != 1:
            raise NotReady('SERVICE_PID_UNAVAILABLE')
        pid = int(found[0]); k = io.process(pid)
        need(k['pid']==pid and type(k['birth_us']) is int and 0<k['birth_us']<=started//1000 and k['argv']==spec['argv'] and k['executable']==spec['executable'], 'PROCESS_ARGV_OR_IMAGE')
        cwd_text = io.command(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn','-nP'])
        cwd = [x[1:] for x in cwd_text.splitlines() if x.startswith('n')]
        src = expected if key=='dashboard' else spec['source']
        need(cwd == [str(canonical(src['root']))], 'PROCESS_CWD')
        src_result = verified['new' if phase in ('G3','G4') else 'old'] if key=='dashboard' else source(src)
        runner, rst = read_file(spec['runner'],mode=spec['runner_mode'])
        runner_hash = c['new_runner_sha256'] if key=='dashboard' and phase in ('G3','G4') else spec['runner_sha256']
        need(digest(runner)==runner_hash, 'RUNNER_HASH')
        lines = re.findall(rb'^LOCAL_AGENT="([^"\r\n]+)"$',runner,re.M)
        if key in ('dashboard','loop'):
            need(lines == [str(canonical(src['root'])).encode()], 'RUNNER_SOURCE_LINE')
        plist, pst = read_file(spec['plist'],mode=spec['plist_mode'])
        need(digest(plist)==spec['plist_sha256'], 'PLIST_HASH')
        pl = plistlib.loads(plist)
        disabled_entry=re.findall(r'"'+re.escape(spec['label'])+r'"\s*=>\s*(true|false)',disabled)
        need(not (spec['label'] in disabled and len(disabled_entry)!=1) and disabled_entry!=['true'] and
             pl.get('Disabled') is not True,'SERVICE_DISABLED_OR_UNVERIFIED')
        need(pl.get('RunAtLoad') is True or pl.get('KeepAlive') is True,'NO_BOOTSTRAP_START_CONTRACT')
        need(pl.get('Label')==spec['label'] and pl.get('ProgramArguments')==spec['launch_argv'], 'PLIST_PROGRAM')
        need(pl.get('EnvironmentVariables',{})==spec.get('launch_environment',{}), 'PLIST_ENVIRONMENT')
        launch=pl['ProgramArguments']
        if spec['runner'] in launch:
            venv=re.findall(rb'^VENV="([^"\r\n]+)"$',runner,re.M)
            need(len(venv)==1 and (Path(venv[0].decode())/'bin/python').resolve()==canonical(spec['interpreter']), 'RUNNER_INTERPRETER_BINDING')
        else:
            need(Path(launch[0]).resolve()==canonical(spec['interpreter']), 'PLIST_INTERPRETER_BINDING')
        image, ist = read_file(spec['executable'])
        interpreter, vst = read_file(spec['interpreter'])
        need(ist.st_mode & 0o100 and vst.st_mode & 0o100 and os.access(spec['executable'],os.X_OK) and
             os.access(spec['interpreter'],os.X_OK) and rst.st_mode & 0o100,'EXECUTABLE_ACCESS')
        need(digest(image)==spec['executable_sha256'] and digest(interpreter)==spec['interpreter_sha256'], 'INTERPRETER_HASH')
        need(max(rst.st_mtime_ns,pst.st_mtime_ns,src_result['latest_ns'],ist.st_mtime_ns,vst.st_mtime_ns)//1000 < k['birth_us'], 'FILES_NEWER_THAN_PROCESS')
        observations[key] = {'pid':pid,'birth_us':k['birth_us'],'argv_sha256':digest(json.dumps(k['argv']).encode()),
                             'runner':digest(runner),'plist':digest(plist),'image':digest(image),
                             'interpreter':digest(interpreter),'source':src_result['sha'],'manifest':src_result['manifest']}
        latest[key] = (pid,k['birth_us'])
    listeners=parse_listeners(io.command(['/usr/sbin/lsof','-nP','-iTCP','-sTCP:LISTEN','-Fpn']))
    port=[x for x in listeners if re.search(r':8766$',x[1])]
    need(port==[[observations['dashboard']['pid'],'127.0.0.1:8766']], 'DASHBOARD_LISTENER')
    protected={'services':{k:v for k,v in observations.items() if k!='dashboard'},
               'listeners':[x for x in listeners if x not in port], 'files':[], 'notifications':{}}
    for item in c['protected_files']:
        data, st=read_file(item['path'],12*1024*1024,mode=item['mode'])
        need(digest(data)==item['sha256'], 'PROTECTED_FILE_HASH')
        protected['files'].append([digest(data),st.st_dev,st.st_ino,st.st_mtime_ns,stat.S_IMODE(st.st_mode)])
    d2, st=read_file(c['d2'],12*1024*1024,mode=0o600)
    parent=canonical(Path(c['d2']).parent)
    need(stat.S_IMODE(parent.stat().st_mode)==0o700 and digest(d2)==D2_HASH, 'D2_HASH_OR_PRIVACY')
    protected['d2']=[digest(d2),st.st_dev,st.st_ino,st.st_mtime_ns]
    for key, fields in COUNTERS.items():
        data, st=read_file(c['health'][key],1024*1024)
        need(-5 <= time.time()-st.st_mtime <= 90, 'HEALTH_STALE')
        health=json.loads(data)
        need(all(type(health.get(f)) is int and health[f]>=0 for f in fields), 'NOTIFICATION_COUNTERS_MISSING')
        if key=='v1':need(health.get('pid')==observations[key]['pid'] and health.get('consecutive_errors')==0, 'V1_HEALTH')
        else:need(health.get('candidate_error_count')==0 and health.get('outcome_error_count')==0, 'LOOP_HEALTH')
        protected['notifications'][key]={f:health[f] for f in fields}
    for path, name in STATIC.items():
        data=io.get(path); file, _=read_file(Path(expected['root'])/'mission_agent/mission_control/static'/name)
        need(data==file, 'HTTP_STATIC_SOURCE_MISMATCH')
    runtime=json.loads(io.get('/api/runtime'))
    need(runtime.get('status')=='LIVE' and runtime.get('pid')==observations['v1']['pid'] and
         runtime.get('production_db_readable') is True and runtime.get('pid_alive') is True, 'RUNTIME_UNVERIFIED')
    cache={'state':'NOT_REQUESTED'}
    if c.get('history'):
        h=c['history'];path='/api/cluster-latest?mint='+h['mint']
        if h.get('job_id'):path+='&job_id='+h['job_id']
        report=json.loads(io.get(path));observed=report.get('observed_at')
        need(report.get('mint')==h['mint'] and type(observed) in (int,float) and math.isfinite(observed) and 0<observed<=time.time()+5, 'CACHE_IDENTITY_OR_TIME')
        if h.get('job_id'):need(report.get('ca_job_id')==h['job_id'], 'CACHE_JOB_MISMATCH')
        need(isinstance(report.get('coverage'),dict) and type(report['coverage'].get('special_normalization_complete')) is bool,'CACHE_COVERAGE_UNKNOWN')
        cache={'state':'HISTORICAL_NOT_NEW_ANALYSIS','job_match':bool(h.get('job_id')),
               'observed_at':observed,'normalization_complete':report.get('coverage',{}).get('special_normalization_complete')}
    # Recheck PID + precise birth after file reads to reject restart/PID-reuse mixtures.
    for key, spec in c['services'].items():
        text=io.command(['/bin/launchctl','print',f'gui/{os.getuid()}/{spec["label"]}'])
        found=re.findall(r'^\s*pid = (\d+)\s*$',text,re.M)
        need(len(found)==1, 'SERVICE_CHANGED_DURING_SAMPLE')
        k=io.process(int(found[0]));need((k['pid'],k['birth_us'])==latest[key], 'PROCESS_CHANGED_DURING_SAMPLE')
    return {'sample_id':uuid.uuid4().hex,'phase':phase,'started_ns':started,'finished_ns':time.time_ns(),
            'source':expected['sha'],'runner':observations['dashboard']['runner'],
            'dashboard':observations['dashboard'],'protected':digest(json.dumps(protected,sort_keys=True).encode()),
            'manifest':verified['new' if phase in ('G3','G4') else 'old']['manifest'],
            'cache':cache,'browser':'NOT_VERIFIED','evidence':'OS_FILES_SAFE_GET_FRESH'}

if __name__ == '__main__':
    # Private one-attempt observer worker only; no release CLI.
    try:
        need(len(sys.argv)==4 and sys.argv[1]=='--sample', 'NO_RELEASE_ENTRYPOINT')
        raw,_=read_file(sys.argv[2],128*1024,mode=0o600)
        result=collect(json.loads(raw),sys.argv[3])
        data=json.dumps({'ok':True,'sample':result},separators=(',',':')).encode()
        need(len(data)<8192, 'SAMPLE_TOO_LARGE')
        sys.stdout.buffer.write(data)
    except BaseException as exc:
        code=str(exc) if isinstance(exc,ProbeError) else type(exc).__name__
        print(json.dumps({'ok':False,'retryable':isinstance(exc,NotReady),'code':code}),end='')
        raise SystemExit(2)
