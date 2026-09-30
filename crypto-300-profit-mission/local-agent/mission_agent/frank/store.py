"""Separate Frank tables on existing WAL repository; atomic evidence/cursor transactions."""
from ..db.connection import transaction
from ..clock import stamp
from ..hashing import canonical,digest,loads

class FrankStore:
    def __init__(self,repo):
        self.repo,self.db=repo,repo.db
        with transaction(self.db):
            self.db.execute('CREATE TABLE IF NOT EXISTS frank_transactions(signature TEXT PRIMARY KEY, slot INTEGER NOT NULL, block_time INTEGER, evidence_sha TEXT NOT NULL, evidence_json TEXT NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS frank_cursor(name TEXT PRIMARY KEY, signature TEXT, slot INTEGER, updated_at TEXT NOT NULL)')
    def put(self,evidence,advance=False,fail=False):
        body={k:v for k,v in evidence.items() if k!='evidence_sha256'}
        if digest(body)!=evidence['evidence_sha256']:raise ValueError('FRANK_EVIDENCE_HASH_MISMATCH')
        with transaction(self.db):
            old=self.db.execute('SELECT evidence_sha FROM frank_transactions WHERE signature=?',(evidence['signature'],)).fetchone()
            if old:
                if old[0]!=evidence['evidence_sha256']:raise ValueError('FRANK_SIGNATURE_CONTENT_CONFLICT')
            else:
                self.db.execute('INSERT INTO frank_transactions VALUES(?,?,?,?,?)',(evidence['signature'],evidence['slot'],evidence['block_time'],evidence['evidence_sha256'],canonical(evidence).decode()))
            if fail:raise RuntimeError('INJECTED_PARTIAL_PARSER_COMMIT')
            if advance:
                prior=self.db.execute("SELECT slot FROM frank_cursor WHERE name='latest'").fetchone()
                if prior and evidence['slot']<prior[0]:raise ValueError('CURSOR_BACKWARD')
                self.db.execute("INSERT INTO frank_cursor VALUES('latest',?,?,?) ON CONFLICT(name) DO UPDATE SET signature=excluded.signature,slot=excluded.slot,updated_at=excluded.updated_at",(evidence['signature'],evidence['slot'],stamp(self.repo.clock.now())))
        return 'DUPLICATE' if old else 'INSERTED'
    def evidence(self):
        return [loads(r[0]) for r in self.db.execute('SELECT evidence_json FROM frank_transactions ORDER BY block_time,slot,signature')]
    def cursor(self):
        row=self.db.execute("SELECT signature,slot FROM frank_cursor WHERE name='latest'").fetchone()
        return dict(row) if row else None
