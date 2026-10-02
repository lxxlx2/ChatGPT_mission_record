"""Bounded manual FM3 sampling; no scheduler installation."""
import argparse,json,os,subprocess,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--seconds',type=int,default=10800);a=p.parse_args();end=time.monotonic()+a.seconds
 owned=('frank_shadow_service','frank_backfill','monster_v2_history','monster_v2_replay')
 while time.monotonic()<end:
  rows=[]
  for line in subprocess.check_output(['ps','-axo','pid=,pcpu=,rss=,command='],text=True).splitlines():
   parts=line.split(None,3)
   if len(parts)!=4:continue
   pid,cpu,rss,command=parts
   match=next((n for n in owned if 'scripts.'+n in command),None)
   if match:rows.append({'pid':int(pid),'script':match,'cpu_percent':float(cpu),'rss_kib':int(rss)})
  disk=int(subprocess.check_output(['du','-sk',str(a.root),'/Users/jerson/Documents/ChatGPT/crypto-monitor-fm2-evidence-20260930'],text=True).splitlines()[0].split()[0])*1024
  sample={'epoch':time.time(),'processes':rows,'fm3_disk_bytes':disk}
  with (a.root/'fm3-resources.jsonl').open('a') as f:f.write(json.dumps(sample)+'\n');f.flush();os.fsync(f.fileno())
  time.sleep(30)
if __name__=='__main__':main()
