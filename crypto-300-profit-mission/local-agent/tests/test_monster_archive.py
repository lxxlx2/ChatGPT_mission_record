import hashlib,io,zipfile
from unittest.mock import patch
import pytest
from mission_agent.monster.archive import retrieve

def archive():
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w') as z:z.writestr('bars.csv','0,1,2,0.5,1.5,10,3599999,15,3,0,0,0\n')
 return b.getvalue()

def test_cached_archive_recovers_missing_sidecar_without_refetch(tmp_path):
 raw=archive();p=tmp_path/'archives'/'a.zip';p.parent.mkdir();p.write_bytes(raw)
 with patch('mission_agent.monster.archive.fetch',return_value=(hashlib.sha256(raw).hexdigest()+' a.zip').encode()) as fetch:
  bars,n,sha=retrieve('a.zip',tmp_path)
 assert len(bars)==1 and n==len(raw) and p.read_bytes()==raw
 assert fetch.call_count==1 and fetch.call_args.args[0].endswith('.CHECKSUM')
 assert p.with_suffix('.zip.CHECKSUM').is_file()

def test_bad_existing_cache_is_preserved_and_not_published(tmp_path):
 p=tmp_path/'archives'/'a.zip';p.parent.mkdir();p.write_bytes(b'')
 with patch('mission_agent.monster.archive.fetch',return_value=(hashlib.sha256(archive()).hexdigest()+' a.zip').encode()):
  with pytest.raises(ValueError,match='CHECKSUM_FAILURE'):retrieve('a.zip',tmp_path)
 assert p.read_bytes()==b'' and not p.with_suffix('.zip.CHECKSUM').exists()
