"""Only acknowledged local transport JSON is eligible for gzip, never pending data."""
import gzip
import os
from pathlib import Path
from .hashing import loads


def compress_terminal(repo,transport,older_than_seconds=7*86400):
    from .clock import parse_utc
    if older_than_seconds<0:raise ValueError('invalid retention age')
    paths=[]
    for row in repo.db.execute("SELECT * FROM batches WHERE state='CONSUMED'").fetchall():
        if (repo.clock.now()-parse_utc(row['created_at'])).total_seconds()<older_than_seconds:
            continue
        for role in ('mac-data/ingest','gpt-data/decisions'):
            path=transport.root/role/'batches'/transport._filename(row['batch_id'])
            if path.exists() and not path.is_symlink():
                original=path.read_bytes();loads(original)
                dest=Path(str(path)+'.gz')
                compressed=gzip.compress(original,mtime=0)
                # Existing compressed file must exactly match. Retention has no overwrite loophole.
                if dest.exists() and gzip.decompress(dest.read_bytes())!=original:
                    raise ValueError('retention archive conflict')
                if not dest.exists():
                    fd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                    with os.fdopen(fd,'wb') as f:f.write(compressed);f.flush();os.fsync(f.fileno())
                if gzip.decompress(dest.read_bytes())!=original:
                    raise ValueError('retention verification failed')
                path.unlink();paths.append(str(path.relative_to(transport.root)))
    return paths
