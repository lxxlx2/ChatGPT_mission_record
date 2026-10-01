"""Bounded manual resource sampling for the explicitly invoked FM2 processes."""
import argparse,json,os,subprocess,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--seconds',type=int,default=7500);a=p.parse_args();start=time.monotonic();log=a.root/'resource-shadow.jsonl'
 while time.monotonic()-start<a.seconds:
  rows=[]
  for line in subprocess.check_output(['ps','-ax','-o','pid=,pcpu=,rss=,command='],text=True).splitlines():
   parts=line.split(None,3)
   if len(parts)!=4:continue
   pid,cpu,rss,command=parts
   if 'Python' not in command.split(' -m ',1)[0] and '/python ' not in command:continue
   owned=[name for name in ('frank_forward_shadow','frank_backfill','monster_archive_stage_a','monster_d1_frozen','monster_archive_finalize','monster_archive_contract_supplement') if 'scripts.'+name in command or '/scripts/'+name+'.py' in command]
   if owned:rows.append({'pid':int(pid),'script':owned[0],'cpu_percent':cpu,'rss_kib':int(rss)})
  disk=int(subprocess.check_output(['du','-sk',str(a.root)],text=True).split()[0])*1024
  with log.open('a') as f:f.write(json.dumps({'wall_ns':time.time_ns(),'disk_bytes':disk,'processes':rows})+'\n');f.flush();os.fsync(f.fileno())
  log.chmod(0o600)
  time.sleep(30)
if __name__=='__main__':main()
