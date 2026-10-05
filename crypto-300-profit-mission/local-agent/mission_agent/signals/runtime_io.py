"""Small durable runtime metadata writer; no legacy service imports."""
import json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path

def utc():return datetime.now(timezone.utc).isoformat()

def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            os.fchmod(stream.fileno(),0o600);stream.write(json.dumps(value,sort_keys=True,ensure_ascii=False).encode());stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
