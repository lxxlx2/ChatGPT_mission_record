"""Install exactly the explicitly authorized Frank shadow LaunchAgent."""
import argparse,os,plistlib,subprocess
from pathlib import Path
from scripts.frank_shadow_service import IDENTIFIER

def configuration(module,root,manual,raw,processed):
 module=Path(module).resolve();root=Path(root).resolve()
 return {'Label':IDENTIFIER,'ProgramArguments':[str(module/'.venv/bin/python'),'-m','scripts.frank_shadow_service','--root',str(root),'--manual',str(Path(manual).resolve()),'--raw',str(Path(raw).resolve()),'--processed',str(Path(processed).resolve())], 'WorkingDirectory':str(module),'RunAtLoad':True,'KeepAlive':True,'ThrottleInterval':30,'ProcessType':'Background','Nice':5,'StandardOutPath':str(root/'service.stdout.log'),'StandardErrorPath':str(root/'service.stderr.log'),'EnvironmentVariables':{'PYTHONUNBUFFERED':'1','PATH':'/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin'}}

def main():
 p=argparse.ArgumentParser()
 for k in ('root','manual','raw','processed'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();a.root.mkdir(parents=True,exist_ok=True,mode=0o700);module=Path(__file__).resolve().parents[1];path=Path.home()/'Library/LaunchAgents'/(IDENTIFIER+'.plist');path.parent.mkdir(parents=True,exist_ok=True)
 data=plistlib.dumps(configuration(module,a.root,a.manual,a.raw,a.processed))
 if path.exists() and path.read_bytes()!=data:raise ValueError('EXISTING_LAUNCHAGENT_CONFIGURATION_DIFFERS')
 if not path.exists():
  with path.open('xb') as f:os.chmod(path,0o600);f.write(data);f.flush();os.fsync(f.fileno())
 subprocess.run(['plutil','-lint',str(path)],check=True)
 domain='gui/'+str(os.getuid());probe=subprocess.run(['launchctl','print',domain+'/'+IDENTIFIER],capture_output=True)
 if probe.returncode:subprocess.run(['launchctl','bootstrap',domain,str(path)],check=True)
 subprocess.run(['launchctl','enable',domain+'/'+IDENTIFIER],check=True)
 subprocess.run(['launchctl','print',domain+'/'+IDENTIFIER],check=True)
if __name__=='__main__':main()
