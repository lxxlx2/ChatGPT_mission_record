from pathlib import Path
import tempfile,sys,json,subprocess,os,stat
from unittest.mock import patch
root=Path('/tmp/frank178-private-child-review');agent=root/'crypto-300-profit-mission/local-agent';sys.path[:0]=[str(agent),str(agent/'tests')]
from mission_agent.mission_control.wallet_d2_ingress import *
from test_frank_d2_owner_at_slot import source
out=Path(__file__).resolve().parent;doc=build_d2_document_from_verified_pr60_replay(source());results={}
with tempfile.TemporaryDirectory(prefix='d2-private-child-probes-') as tmp:
 base=Path(tmp).resolve();control=base/'control';control.mkdir(mode=0o755);private=control/SOURCE_SUBDIR;private.mkdir(mode=0o700);file=private/SOURCE_NAME;file.write_text(json.dumps(doc));file.chmod(0o600)
 def status(p):return query_d2(p,page=0)['status']
 results['legitimate_0755_0700_0600']=status(control)
 real_lstat=Path.lstat
 for name,targetpath in [('root',control),('child',private),('source',file)]:
  def fake(p,*a,**k):
   st=real_lstat(p,*a,**k)
   if p==targetpath:
    vals=list(st);vals[4]=st.st_uid+1;return os.stat_result(vals)
   return st
  with patch.object(Path,'lstat',fake):results['wrong_owner_'+name]=status(control)
 # A symlink in an ancestor is traversed even though final root is ordinary.
 alias=base/'alias';alias.symlink_to(base,target_is_directory=True);results['ancestor_symlink']=status(alias/'control')
 # An actual unrelated Git repo surrounding source, not Mission checkout.
 git=subprocess.run(['/Library/Developer/CommandLineTools/usr/bin/git','init','-q',str(base)],capture_output=True)
 if git.returncode==0:results['inside_real_git_checkout']=status(control)
 else:results['inside_real_git_checkout']='SETUP_FAILED'
 results['shared_mode_after']=format(stat.S_IMODE(control.stat().st_mode),'04o')
results['no_socket_or_production']=True
(out/'probes.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
