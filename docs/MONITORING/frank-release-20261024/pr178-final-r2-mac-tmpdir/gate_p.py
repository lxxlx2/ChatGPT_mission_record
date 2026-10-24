import os,sys,socket,errno,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;ipc=R/'ipc';child='--child' in sys.argv;rows=[];failed=False

def deny(name,family,kind,op,address):
 global failed
 s=None;stage='create'
 try:
  s=socket.socket(family,kind);s.settimeout(1);stage=op;getattr(s,op)(address);row={'case':name,'result':'FAIL','reason':'OPERATION_NOT_DENIED'};failed=True
 except OSError as e:
  ok=e.errno==errno.EPERM;row={'case':name,'result':'PASS' if ok else 'FAIL','errno':e.errno,'symbol':'EPERM' if ok else errno.errorcode.get(e.errno,'UNKNOWN'),'stage':stage};failed|=not ok
 finally:
  if s:s.close()
 rows.append(row)
 if row['result']!='PASS':raise RuntimeError('NETWORK_POLICY_NOT_PROVEN')
try:
 env_ok=all(os.environ.get(k)==str(ipc) for k in ['MAC_CHROMIUM_TMPDIR','TMPDIR','TMP','TEMP']);rows.append({'case':'ENV_FOUR_VARIABLES_UNDER_ALLOWLIST','result':'PASS' if env_ok else 'FAIL'});
 if not env_ok:raise RuntimeError('ENV_NOT_INHERITED')
 path=ipc/('child-probe.sock' if child else 'parent-probe.sock');server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);client=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
 try:
  server.settimeout(1);client.settimeout(1);server.bind(str(path));server.listen(1);client.connect(str(path));accepted,_=server.accept()
  try:client.sendall(b'SYNTHETIC');assert accepted.recv(9)==b'SYNTHETIC';accepted.sendall(b'OK');assert client.recv(2)==b'OK'
  finally:accepted.close()
  rows.append({'case':'IN_ROOT_UDS_BIND_LISTEN_CONNECT_ECHO','result':'PASS'})
 finally:client.close();server.close();path.unlink(missing_ok=True)
 outside=str(R.parent/(R.name+'-outside.sock'))
 for op in ['bind','connect']:deny('OUT_ROOT_UDS_'+op.upper(),socket.AF_UNIX,socket.SOCK_STREAM,op,outside)
 for family,label in [(socket.AF_INET,'IPV4'),(socket.AF_INET6,'IPV6')]:
  for kind,proto in [(socket.SOCK_STREAM,'TCP'),(socket.SOCK_DGRAM,'UDP')]:
   for op in ['bind','connect']:
    addr=(('127.0.0.1',0) if family==socket.AF_INET else ('::1',0)) if op=='bind' else (('192.0.2.1',9) if family==socket.AF_INET else ('2001:db8::1',9))
    deny(label+'_'+proto+'_'+op.upper(),family,kind,op,addr)
 if not child:
  p=subprocess.run([sys.executable,'-I','-B',str(Path(__file__)), '--child'],capture_output=True,text=True,timeout=12);data=json.loads(p.stdout);rows.append({'case':'CHILD_INHERITS_FULL_MATRIX','result':'PASS' if p.returncode==0 and data['verdict']=='PASS' else 'FAIL','child_cases':data.get('cases',[])})
  if p.returncode or data['verdict']!='PASS':raise RuntimeError('CHILD_POLICY_FAILURE')
 verdict='PASS'
except Exception as e:verdict='BLOCKED_NETWORK_POLICY_NOT_PROVEN';rows.append({'case':'STOP_FIRST_FAILURE','result':'FAIL','reason':type(e).__name__})
out={'verdict':verdict,'child':child,'cases':rows,'production_targets_used':False,'all_IP_connect_targets_TEST_NET_port9':True,'socket_policy_errors_required':'EPERM not timeout/refusal'}
print(json.dumps(out));sys.exit(0 if verdict=='PASS' else 2)
