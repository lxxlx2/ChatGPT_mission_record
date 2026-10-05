import gzip,hashlib,json,os
from pathlib import Path
from ..hashing import canonical,loads

def save(path,value,metadata):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 data=canonical(value);compressed=gzip.compress(data,mtime=0)
 try:
  with path.open('xb') as f:f.write(compressed);f.flush();os.fsync(f.fileno())
 except FileExistsError:
  if gzip.decompress(path.read_bytes())!=data:raise ValueError('IMMUTABLE_CACHE_CONFLICT')
 manifest={**metadata,'sha256':hashlib.sha256(data).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'row_count':len(value)}
 m=Path(str(path)+'.manifest.json')
 if m.exists() and loads(m.read_bytes())!=manifest:raise ValueError('CACHE_METADATA_CONFLICT')
 m.write_bytes(canonical(manifest));path.chmod(0o600);m.chmod(0o600)
 return manifest

def load(path):
 path=Path(path);manifest=loads(Path(str(path)+'.manifest.json').read_bytes());compressed=path.read_bytes()
 if hashlib.sha256(compressed).hexdigest()!=manifest['compressed_sha256']:raise ValueError('CACHE_HASH_MISMATCH')
 data=gzip.decompress(compressed)
 if hashlib.sha256(data).hexdigest()!=manifest['sha256']:raise ValueError('CACHE_HASH_MISMATCH')
 value=loads(data)
 if len(value)!=manifest['row_count']:raise ValueError('CACHE_ROW_COUNT_MISMATCH')
 return value,manifest
