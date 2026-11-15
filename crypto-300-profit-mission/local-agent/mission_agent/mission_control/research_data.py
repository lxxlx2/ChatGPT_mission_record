"""User-triggered wallet/market research jobs. GETs never write or fetch.

Private derived storage is separate from the source ledger and old delivery DB.
No timers, notifications, quotes, scanner writes or additional listeners.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

from .db import open_production_ro
from .wallet_refresh import capture_owner
from .source_evidence import safe_source_error
from ..meme.cluster import RPCError


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class ResearchData:
    def __init__(self, root, *, wallet, rpc_factory, market_client, observed_mints,
                 model_positions=lambda: {}, signal_mints=lambda: [], binding="UNPINNED", code_sha="UNPINNED", clock=time.time):
        self.root = Path(root)
        self.path = self.root / "frank-research.sqlite"
        self.wallet = wallet
        self.rpc_factory = rpc_factory
        self.market_client = market_client
        self.observed_mints = observed_mints
        self.model_positions = model_positions
        self.signal_mints = signal_mints
        self.binding, self.code_sha, self.clock = binding, code_sha, clock
        self.lock = threading.RLock()
        self.active = set()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="frank-research")

    @contextmanager
    def _write(self):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("PRAGMA busy_timeout=5000")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS frank_refresh_jobs(
              id TEXT PRIMARY KEY, kind TEXT NOT NULL, key TEXT NOT NULL,
              request_hash TEXT NOT NULL, binding TEXT NOT NULL, body TEXT NOT NULL,
              UNIQUE(kind,key));
            CREATE TABLE IF NOT EXISTS frank_research_results(
              id TEXT PRIMARY KEY, kind TEXT NOT NULL, completed_at REAL NOT NULL, body TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS frank_research_results_latest ON frank_research_results(kind,completed_at);
            CREATE TABLE IF NOT EXISTS frank_refresh_keys(
              kind TEXT NOT NULL,key TEXT NOT NULL,job_id TEXT NOT NULL,
              request_hash TEXT NOT NULL,binding TEXT NOT NULL,PRIMARY KEY(kind,key));
            CREATE TABLE IF NOT EXISTS frank_market_stage(
              job_id TEXT NOT NULL,mint TEXT NOT NULL,body TEXT NOT NULL,PRIMARY KEY(job_id,mint));
        """)
        self.path.chmod(0o600)
        try:
            with db:
                yield db
        finally:
            db.close()

    def _query(self, sql, params=()):
        if not self.path.exists():
            return []
        db = open_production_ro(self.path)
        try:
            return [dict(row) for row in db.execute(sql, params)]
        finally:
            db.close()

    def _save(self, job):
        job["updated_at"] = self.clock()
        with self._write() as db:
            db.execute("UPDATE frank_refresh_jobs SET body=? WHERE id=?", (canonical(job), job["job_id"]))

    def job(self, job_id, kind=None):
        if not isinstance(job_id, str) or not re.fullmatch(r"[a-f0-9]{32}", job_id):
            raise ValueError("INVALID_JOB_ID")
        rows = self._query("SELECT body FROM frank_refresh_jobs WHERE id=?", (job_id,))
        if not rows:
            return None
        job = json.loads(rows[0]["body"])
        if kind is not None and job["kind"] != kind:
            return None
        with self.lock:
            if job["state"] in {"QUEUED", "RUNNING"} and job_id not in self.active:
                job.update(state="PAUSED", reason="PROCESS_INTERRUPTED", resume_allowed=True)
        return job

    def submit(self, kind, request):
        if kind not in {"balance", "market"}:
            raise ValueError("INVALID_JOB_KIND")
        key = request.get("idempotency_key")
        if not isinstance(key, str) or not 1 <= len(key) <= 256 or any(ord(c) < 32 for c in key):
            raise ValueError("INVALID_IDEMPOTENCY_KEY")
        request_hash = digest({"kind": kind, "wallet": self.wallet, **request})
        with self.lock:
            with self._write() as db:
                old = db.execute("SELECT id,request_hash,binding FROM frank_refresh_jobs WHERE kind=? AND key=?", (kind,key)).fetchone()
                if old is None:
                    old=db.execute("SELECT job_id,request_hash,binding FROM frank_refresh_keys WHERE kind=? AND key=?",(kind,key)).fetchone()
                if old:
                    if old[2] != self.binding:
                        raise ValueError("SOURCE_BINDING_CHANGED")
                    if old[1] != request_hash:
                        raise ValueError("IDEMPOTENCY_CONFLICT")
                    return self.job(old[0], kind)
                # A different retry key must not create concurrent duplicate source work.
                for active in self.active:
                    job = self.job(active)
                    if job and job["kind"] == kind and job["request"] == {k:v for k,v in request.items() if k != "idempotency_key"}:
                        db.execute("INSERT INTO frank_refresh_keys VALUES(?,?,?,?,?)",(kind,key,active,request_hash,self.binding))
                        return job
                job_id = uuid.uuid4().hex
                job = {"schema_version": 1, "job_id": job_id, "kind": kind, "state": "QUEUED",
                       "binding": self.binding, "code_sha": self.code_sha, "created_at": self.clock(),
                       "request": {k:v for k,v in request.items() if k != "idempotency_key"},
                       "progress": {"stage": "QUEUED", "completed_items": 0}, "errors": [],
                       "result_ref": None, "resume_allowed": True}
                db.execute("INSERT INTO frank_refresh_jobs VALUES(?,?,?,?,?,?)", (job_id,kind,key,request_hash,self.binding,canonical(job)))
            self.active.add(job_id)
            self.executor.submit(self._run, job_id)
            return job

    def resume(self, job_id, kind="balance", idempotency_key=None):
        with self.lock:
            job = self.job(job_id, kind)
            if job is None:
                raise ValueError("JOB_NOT_FOUND")
            if job["binding"] != self.binding:
                raise ValueError("SOURCE_BINDING_CHANGED")
            if idempotency_key is not None:
                request_hash=digest({"job_id":job_id,"kind":kind})
                with self._write() as db:
                    old=db.execute("SELECT job_id,request_hash,binding FROM frank_refresh_keys WHERE kind=? AND key=?",(kind+"_resume",idempotency_key)).fetchone()
                    if old:
                        if old!=(job_id,request_hash,self.binding):
                            raise ValueError("IDEMPOTENCY_CONFLICT")
                        return job
                    db.execute("INSERT INTO frank_refresh_keys VALUES(?,?,?,?,?)",(kind+"_resume",idempotency_key,job_id,request_hash,self.binding))
            if job_id in self.active or job["state"] == "DONE":
                return job
            # Recapture the small dual-program snapshot; never combine an old program
            # capture with a newly observed program and claim a fresh snapshot.
            job.update(state="QUEUED", errors=[], resume_allowed=True, progress={"stage":"QUEUED","completed_items":0})
            self._save(job)
            self.active.add(job_id)
            self.executor.submit(self._run, job_id)
            return job

    def _receipt(self, source, raw):
        if hashlib.sha256(raw).hexdigest() != source["response_sha256"]:
            raise ValueError("RECEIPT_HASH_MISMATCH")
        folder = self.root / "frank-research-private"
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = folder / (source["receipt_id"] + ".json")
        with path.open("xb") as stream:
            path.chmod(0o600)
            stream.write(raw)
            stream.flush()
            import os
            os.fsync(stream.fileno())

    def _run(self, job_id):
        try:
            job = self.job(job_id)
            job["state"] = "RUNNING"
            self._save(job)
            if job["kind"] == "balance":
                def progress(section):
                    job["progress"] = {"stage": "PROGRAM_CAPTURED", "completed_items": job["progress"]["completed_items"] + 1,
                                       "last_program": section}
                    self._save(job)
                result = capture_owner(self.wallet, self.rpc_factory(), clock=self.clock,
                                       save_receipt=self._receipt, checkpoint=progress)
                result_id = result["snapshot_id"]
                state = "DONE"
            else:
                from .market_observations import capture_market
                request = job["request"]
                if request["scope"] == "mint":
                    mints = [request["mint"]]
                elif request["scope"] == "positions":
                    snapshot = self.latest("balance")
                    if snapshot is None:
                        raise ValueError("BALANCE_SNAPSHOT_REQUIRED")
                    mints = [r["mint"] for r in snapshot["rows"] if int(r["raw_amount"]) > 0]
                    mints.append("So11111111111111111111111111111111111111112")
                    job["selection_scope"] = "ALL_NONZERO_MINTS_IN_CAPTURED_OWNER_SNAPSHOT"
                    job["zero_balance_mints_not_priced"] = sum(int(r["raw_amount"]) == 0 for r in snapshot["rows"])
                elif request["scope"] == "signals":
                    mints=self.signal_mints()
                else:
                    mints = self.observed_mints()
                result_id = str(uuid.uuid4())
                observations = []
                unique_mints=sorted(set(mints))
                for mint in unique_mints:
                    # Existing token-pairs endpoint documents 300 requests/minute.
                    # Pace wire work; never limit the number of selected mints.
                    if observations:
                        time.sleep(.21)
                    row = capture_market([mint], self.market_client, clock=self.clock)[0]
                    evidence = getattr(self.market_client, "last_response_evidence", None)
                    if evidence and evidence.get("source_ref"):
                        self._receipt(evidence["source_ref"], evidence["response_bytes"])
                    observations.append(row)
                    job["progress"] = {"stage": "MARKET_CAPTURED", "completed_items": len(observations), "total_items": len(unique_mints)}
                    # Persist per-Mint progress; interrupted jobs leave recoverable verified observations.
                    with self._write() as db:
                        db.execute("INSERT OR REPLACE INTO frank_market_stage VALUES(?,?,?)", (job_id,mint,canonical(row)))
                    self._save(job)
                result = {"snapshot_id": result_id, "rows": observations, "observed_at": self.clock(),
                          "scope": request["scope"], "complete": True}
                state = "DONE" if all(r.get("status") == "OK" for r in observations) else "PARTIAL"
                result["status"] = state
            result["code_sha"] = self.code_sha
            result["source_binding"] = self.binding
            with self._write() as db:
                db.execute("INSERT OR REPLACE INTO frank_research_results VALUES(?,?,?,?)", (result_id,job["kind"],self.clock(),canonical(result)))
                job.update(state=state, result_ref=result_id, finished_at=self.clock(), resume_allowed=state != "DONE")
                db.execute("UPDATE frank_refresh_jobs SET body=? WHERE id=?", (canonical(job),job_id))
        except Exception as exc:
            # Only safe source codes reach public jobs, never arbitrary exception text.
            try:
                job.update(state="ERROR", errors=[{"code":safe_source_error(str(exc) if isinstance(exc,RPCError) else exc)}], resume_allowed=True, finished_at=self.clock())
                self._save(job)
            except Exception:
                pass  # A disk error cannot erase the preceding durable checkpoint.
        finally:
            with self.lock:
                self.active.discard(job_id)

    def latest(self, kind, result_id=None):
        if result_id is None:
            rows = self._query("SELECT body FROM frank_research_results WHERE kind=? ORDER BY completed_at DESC,rowid DESC LIMIT 1", (kind,))
        else:
            rows = self._query("SELECT body FROM frank_research_results WHERE kind=? AND id=?", (kind,result_id))
        return json.loads(rows[0]["body"]) if rows else None

    def market_rows(self):
        # Merge latest observations per Mint across explicit refresh scopes. A failed
        # newer observation remains failed; it must not silently select an old price.
        rows = self._query("SELECT body FROM frank_research_results WHERE kind='market' ORDER BY completed_at,rowid")
        result = {}
        for saved in rows:
            for row in json.loads(saved["body"])["rows"]:
                result[row["mint"]] = row
        return result

    def latest_attempt(self, kind):
        rows=self._query("SELECT id FROM frank_refresh_jobs WHERE kind=? ORDER BY rowid DESC LIMIT 1",(kind,))
        return self.job(rows[0]["id"],kind) if rows else None

    def positions(self, *, snapshot_id=None, mint=None, limit=100, cursor=None):
        snapshot = self.latest("balance", snapshot_id)
        if cursor:
            token = self._cursor(cursor)
            if snapshot_id is not None and snapshot_id != token["binding"]:
                raise ValueError("CURSOR_QUERY_CHANGED")
            snapshot = self.latest("balance", token["binding"])
        if snapshot is None:
            return {"status":"UNAVAILABLE", "reason":"BALANCE_SNAPSHOT_NOT_PRESENT", "rows":None, "current_balance_verified":False}
        if snapshot.get("source_binding") != self.binding and snapshot_id is None and not cursor:
            raise ValueError("SOURCE_BINDING_CHANGED")
        rows = [dict(r) for r in snapshot["rows"] if mint is None or r["mint"] == mint]
        models = self.model_positions()
        for row in rows:
            row["model_state"] = models.get(row["mint"], "UNKNOWN")
            row["chain_state"] = "NONZERO" if int(row["raw_amount"]) else "ZERO"
            row["reconciliation"] = "DIFFERENT" if ((row["model_state"] == "CLOSED" and int(row["raw_amount"]) > 0) or
                (row["model_state"] == "OPEN" and int(row["raw_amount"]) == 0)) else "NOT_ASSESSED"
        age = Decimal(str(self.clock())) - Decimal(snapshot["observed_at"])
        fresh = Decimal(0) <= age <= 300 and snapshot.get("source_binding") == self.binding
        page = self.page(rows, "positions", snapshot["snapshot_id"], mint, limit, cursor)
        from .market_observations import portfolio_valuation
        marks=self.market_rows()
        valuation = portfolio_valuation([r for r in snapshot["rows"] if int(r["raw_amount"])>0], marks, as_of=self.clock(), max_age_seconds=60)
        valuation["scope"]="ALL_NONZERO_TOKEN_BALANCES_NATIVE_SOL_SEPARATE"
        valuation["zero_balance_mints_excluded"]=sum(int(r["raw_amount"])==0 for r in snapshot["rows"])
        valuation["native_sol_valuation"]=portfolio_valuation([{"mint":"So11111111111111111111111111111111111111112",**snapshot["native_sol"]}],marks,as_of=self.clock(),max_age_seconds=60)
        valuation["native_sol_valuation"]["scope"]="NATIVE_SOL_USING_WRAPPED_SOL_USD_REFERENCE"
        return {**page, "status":"OK" if fresh else "STALE_ARCHIVED", "snapshot_id":snapshot["snapshot_id"],
                "wallet":self.wallet, "scope":snapshot["scope"], "sources":snapshot["sources"], "programs":snapshot["programs"],
                "observed_at":snapshot["observed_at"], "age_seconds":str(age), "expires_at":snapshot["expires_at"],
                "current_balance_verified":fresh, "same_slot_atomic":False, "native_sol":snapshot["native_sol"],
                "account_count":snapshot["account_count"], "mint_count":snapshot["mint_count"], "valuation":valuation,
                "latest_refresh_attempt":self.latest_attempt("balance"),
                "snapshot_code_sha":snapshot.get("code_sha"), "code_sha":self.code_sha}

    @staticmethod
    def _cursor(cursor):
        try:
            if not isinstance(cursor,str) or len(cursor)>4096:
                raise ValueError
            value=json.loads(base64.b64decode(cursor + '='*(-len(cursor)%4),altchars=b'-_',validate=True))
            if set(value)!={"kind","binding","mint","offset"} or type(value["offset"]) is not int or value["offset"]<0:
                raise ValueError
            return value
        except (ValueError,TypeError,KeyError):
            raise ValueError("INVALID_CURSOR") from None

    @classmethod
    def page(cls, rows, kind, binding, mint, limit, cursor):
        if type(limit) is not int or not 1<=limit<=1000:
            raise ValueError("INVALID_PAGE_SIZE")
        offset=0
        if cursor:
            token=cls._cursor(cursor)
            if (token["kind"],token["binding"],token["mint"])!=(kind,binding,mint):
                raise ValueError("CURSOR_QUERY_CHANGED")
            offset=token["offset"]
        part=rows[offset:offset+limit]
        following=offset+len(part)
        token={"kind":kind,"binding":binding,"mint":mint,"offset":following}
        next_cursor=base64.urlsafe_b64encode(canonical(token).encode()).decode().rstrip('=') if following<len(rows) else None
        return {"rows":part,"total_matching":len(rows),"returned":len(part),"next_cursor":next_cursor,"limit":limit}
