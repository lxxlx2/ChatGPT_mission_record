"""LOCAL_FILE only. Roles are fixed methods, not caller-supplied paths."""
import os
import tempfile
from pathlib import Path
from ..hashing import canonical,loads,verify


class LocalTransport:
    def __init__(self,root,disk_budget_bytes=5_000_000_000):
        self.root=Path(root)
        self.disk_budget_bytes=disk_budget_bytes
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.root.chmod(0o700)

    def _write(self,relative,value,immutable=False):
        path=self.root/relative
        path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        data=canonical(value)
        from ..storage import admit
        admit(self.root.parent,len(data)*2+65536,self.disk_budget_bytes)
        if immutable and not path.exists():
            archive=Path(str(path)+'.gz')
            if archive.exists():
                import gzip
                if gzip.decompress(archive.read_bytes())!=data:
                    raise ValueError('immutable compressed artifact conflict')
                return path
        fd,name=tempfile.mkstemp(dir=path.parent,prefix='.tmp-')
        try:
            with os.fdopen(fd,'wb') as f:
                f.write(data);f.flush();os.fsync(f.fileno())
            if immutable:
                try:
                    os.link(name,path)
                except FileExistsError:
                    if path.read_bytes()!=data:
                        raise ValueError('immutable artifact conflict')
            else:
                os.replace(name,path)
            directory=os.open(path.parent,os.O_RDONLY)
            try:os.fsync(directory)
            finally:os.close(directory)
        finally:
            if os.path.exists(name):os.unlink(name)
        return path

    @staticmethod
    def _filename(batch_id):
        import hashlib
        return hashlib.sha256(batch_id.encode()).hexdigest()+'.json'

    def publish_batch(self,batch):
        verify(batch)
        if len(canonical(batch))>100_000:
            raise ValueError('batch exceeds byte limit')
        self._write('mac-data/ingest/batches/'+self._filename(batch['batch_id']),batch,True)
        self._write('mac-data/ingest/current-batch.json',batch)

    def publish_receipt(self,receipt):
        self._write('gpt-data/decisions/batches/'+self._filename(receipt['input_batch_id']),receipt,True)
        self._write('gpt-data/decisions/current.json',receipt)

    def publish_delivery(self,summary):
        self._write('gpt-data/delivery/current.json',summary)

    def publish_health(self,health):
        self._write('mac-data/health/current.json',health)

    def read_batch(self,batch_id=None):
        path='mac-data/ingest/current-batch.json' if batch_id is None else 'mac-data/ingest/batches/'+self._filename(batch_id)
        return self._read(path)

    def read_receipt(self,batch_id):
        return self._read('gpt-data/decisions/batches/'+self._filename(batch_id))

    def _read(self,relative):
        import gzip
        path=self.root/relative
        try:
            data=path.read_bytes()
        except FileNotFoundError:
            data=gzip.decompress(Path(str(path)+'.gz').read_bytes())
        return loads(data)
