"""Explicit immutable local-index captures; no transport or source-ledger write.

The private artifact retains the complete consistent source database, including
raw trade legs, plus frozen canonical activity rows. This is not chain coverage,
a new classifier, a cost ledger, or evidence that an indexed trade is correct.
"""
from contextlib import contextmanager
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time
import uuid

from .wallet_activity import activity, connect
from .wallet_activity_paging import _where, _encode, _decode, KINDS
from .wallet_facts import build_fact
from .archived_wallet_facts import read_archived_fact


class ManifestError(ValueError):
    def __init__(self, code, http_status=400):
        self.code, self.http_status = code, http_status
        super().__init__(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            result.update(chunk)
    return result.hexdigest()


def count_archived_replay(summary, replay):
    reason = replay["reason"]
    counts = summary["reason_counts"]
    counts[reason] = counts.get(reason, 0) + 1
    if replay["status"] != "VERIFIED":
        if reason == "ARCHIVE_NOT_FOUND":
            summary["missing"] += 1
        elif reason in {"ARCHIVE_HASH_MISMATCH", "ARCHIVE_SIGNATURE_MISMATCH", "ARCHIVE_SLOT_MISMATCH",
                        "ARCHIVE_TIME_MISMATCH", "ARCHIVE_WALLET_MISMATCH"}:
            summary["mismatched"] += 1
        else:
            summary["other_unresolved"] += 1
        return
    summary["verified"] += 1
    summary["reclassified"] += int(replay["indexed_class"] != replay["replayed_class"])
    fact = replay["fact"]
    for name, executed in (("token_transfers", "executed_token_transfers"),
                           ("native_transfers", "executed_native_transfers")):
        for instruction in fact[name] or []:
            effect = instruction["instruction_effect"]
            if effect == "EXECUTED":
                summary[executed] += 1
            elif effect == "ATTEMPT_ONLY":
                summary["attempted_transfers"] += 1
    summary["confirmed_initial_fundings"] += sum(
        item["status"] == "CONFIRMED_INITIAL_FUNDING" for item in fact["account_funding"]["items"])


def load_metadata(raw):
    try:
        value = json.loads(raw)
        expected = {"schema_version","manifest_id","kind","state","scope","full_chain_verified",
                    "as_of","created_at","code_sha","parser_sha256","source_binding",
                    "source_snapshot_sha256","artifact_sha256","counts","canonical_rows_sha256",
                    "raw_source_tables_preserved","immutable_source_snapshot","manifest_sha256"}
        if isinstance(value, dict) and value.get("schema_version") in (2, 3):
            expected |= {"supersedes_manifest_id", "fact_revision_counts"}
        if isinstance(value, dict) and value.get("schema_version") == 3:
            expected.add("archive_replay_summary")
        if (not isinstance(value,dict) or type(value.get("schema_version")) is not int or
                value.get("schema_version") not in {1, 2, 3} or set(value)!=expected or
                value["manifest_sha256"] != digest({k:v for k,v in value.items() if k!="manifest_sha256"})):
            raise ValueError
        return value
    except (ValueError,TypeError,UnicodeError,RecursionError):
        raise ManifestError("MANIFEST_METADATA_INTEGRITY_FAILED",503) from None


class EvidenceManifests:
    def __init__(self, root, source_path, *, archive_root=None, clock=time.time, code_sha="UNPINNED"):
        self.root, self.source = Path(root), Path(source_path)
        self.archive_root = Path(archive_root) if archive_root is not None else None
        self.path = self.root / "frank-evidence-manifests.sqlite"
        self.artifacts = self.root / "frank-evidence-artifacts"
        self.clock = clock
        self.code_sha = code_sha if re.fullmatch(r"[a-f0-9]{40}", code_sha) else "UNPINNED"

    @contextmanager
    def _db(self, write=False):
        db = None
        try:
            if self.path.is_symlink() or self.artifacts.is_symlink():
                raise ManifestError("MANIFEST_STORAGE_UNAVAILABLE", 503)
            if not write and not self.path.exists():
                yield None
                return
            if write:
                self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
                self.artifacts.mkdir(mode=0o700, exist_ok=True)
                db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
                self.path.chmod(0o600)
                db.execute("PRAGMA synchronous=FULL")
                db.execute("BEGIN IMMEDIATE")
                db.execute("CREATE TABLE IF NOT EXISTS manifests(seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, kind TEXT NOT NULL, request_key TEXT UNIQUE NOT NULL, binding TEXT NOT NULL, body TEXT NOT NULL)")
            else:
                db = connect(self.path)
                db.execute("BEGIN")
                if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='manifests'").fetchone() is None:
                    yield None
                    return
            db.row_factory = sqlite3.Row
            yield db
            if write:
                db.commit()
        except (OSError, sqlite3.Error):
            raise ManifestError("MANIFEST_STORAGE_UNAVAILABLE", 503) from None
        finally:
            if db is not None:
                db.close()

    @staticmethod
    def _id(value):
        if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
            raise ManifestError("INVALID_MANIFEST_ID")
        return value

    @staticmethod
    def _limit(limit):
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ManifestError("INVALID_MANIFEST_PAGE_SIZE")

    def _binding(self):
        try:
            if self.source.is_symlink() or not self.source.is_file():
                raise OSError
            stat = self.source.stat()
            return digest([str(self.source.resolve()), stat.st_dev, stat.st_ino])
        except OSError:
            raise ManifestError("MANIFEST_SOURCE_UNAVAILABLE", 503) from None

    def _parent_facts(self, db, parent_id, binding):
        if parent_id is None:
            return {}
        saved = db.execute("SELECT body FROM manifests WHERE id=?", (parent_id,)).fetchone()
        if saved is None:
            raise ManifestError("PARENT_MANIFEST_NOT_FOUND", 404)
        parent = load_metadata(saved["body"])
        if parent["kind"] != "facts" or parent["schema_version"] not in (2, 3):
            raise ManifestError("PARENT_FACTS_NOT_AVAILABLE", 409)
        if parent["source_binding"] != binding:
            raise ManifestError("PARENT_MANIFEST_SOURCE_CHANGED", 409)
        path = self.artifacts / (parent_id + ".sqlite")
        if path.is_symlink() or not path.is_file() or file_hash(path) != parent["artifact_sha256"]:
            raise ManifestError("MANIFEST_ARTIFACT_INTEGRITY_FAILED", 503)
        source = connect(path)
        try:
            rows = source.execute("SELECT s.wallet, s.signature, p.body "
                                  "FROM signatures s JOIN frank_manifest_activity p ON p.index_rowid=s.rowid")
            facts = {}
            for row in rows:
                value = json.loads(row["body"])["transaction_fact"]
                facts[(row["wallet"], row["signature"])] = (value["fact_id"], value["supersedes_id"])
        finally:
            source.close()
        if file_hash(path) != parent["artifact_sha256"]:
            raise ManifestError("MANIFEST_ARTIFACT_INTEGRITY_FAILED", 503)
        return facts

    def create(self, kind, idempotency_key, supersedes_manifest_id=None):
        if not isinstance(kind, str) or kind not in {"activity", "facts"}:
            raise ManifestError("INVALID_MANIFEST_KIND")
        if (not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 256 or
                any(ord(c)<32 or 0xD800<=ord(c)<=0xDFFF for c in idempotency_key)):
            raise ManifestError("INVALID_MANIFEST_IDEMPOTENCY_KEY")
        if supersedes_manifest_id is not None:
            self._id(supersedes_manifest_id)
            if kind != "facts":
                raise ManifestError("FACTS_REQUIRED_FOR_SUPERSESSION")
        binding = self._binding()
        artifact = None
        published = False
        try:
            with self._db(write=True) as db:
                prior = db.execute("SELECT * FROM manifests WHERE request_key=?", (idempotency_key,)).fetchone()
                if prior is not None:
                    metadata = load_metadata(prior["body"])
                    if (prior["kind"] != kind or prior["binding"] != binding or
                            metadata.get("supersedes_manifest_id") != supersedes_manifest_id):
                        raise ManifestError("IDEMPOTENCY_CONFLICT", 409)
                    return metadata
                parent_facts = self._parent_facts(db, supersedes_manifest_id, binding)
                revision_counts = {"new": 0, "revised": 0, "unchanged": 0, "parent_only": 0}
                replay_archive = kind == "facts" and self.archive_root is not None
                archive_summary = {"verified": 0, "missing": 0, "mismatched": 0, "other_unresolved": 0,
                                   "reason_counts": {}, "reclassified": 0, "executed_token_transfers": 0,
                                   "executed_native_transfers": 0, "attempted_transfers": 0,
                                   "confirmed_initial_fundings": 0}
                now = self.clock()
                if type(now) not in (int, float) or not 1_600_000_000 < now < 4_000_000_000:
                    raise ManifestError("INVALID_MANIFEST_TIMESTAMP")
                identity = uuid.uuid4().hex
                artifact = self.artifacts / (identity + ".sqlite")
                # A complete SQLite backup reads committed WAL content in a
                # single source snapshot. The source connection is mode=ro.
                source = connect(self.source)
                target = None
                try:
                    source.execute("BEGIN")
                    source.execute("SELECT count(*) FROM sqlite_master").fetchone()
                    target = sqlite3.connect(artifact)
                    artifact.chmod(0o600)
                    source.backup(target)
                finally:
                    source.close()
                    if target is not None:
                        target.close()
                if self._binding() != binding:
                    raise ManifestError("MANIFEST_SOURCE_CHANGED", 409)
                source_hash = file_hash(artifact)
                frozen = sqlite3.connect(artifact)
                frozen.row_factory = sqlite3.Row
                try:
                    # Reserved table collisions are never silently overwritten.
                    frozen.execute("CREATE TABLE frank_manifest_activity(index_rowid INTEGER PRIMARY KEY, body TEXT NOT NULL)")
                    projection = activity(artifact, int(now), "all", _connection=frozen)
                    legs = {}
                    for leg in frozen.execute("SELECT rowid AS source_trade_rowid,* FROM trades ORDER BY rowid"):
                        legs.setdefault((leg["wallet"],leg["signature"]),[]).append(dict(leg))
                    rows_hash = hashlib.sha256(b"[")
                    for offset, indexed in enumerate(projection["rows"]):
                        row = indexed.copy()
                        source_row = frozen.execute("SELECT wallet,signature,body FROM signatures WHERE rowid=?", (row["index_rowid"],)).fetchone()
                        key = (source_row["wallet"], source_row["signature"])
                        row["raw_trade_legs"] = legs.get(key, [])
                        row["raw_trade_legs_semantics"] = "SOURCE_ROWS_UNINTERPRETED_NOT_NEW_CLASSIFICATION"
                        if kind == "facts":
                            try:
                                source_body = json.loads(source_row["body"] or "{}")
                            except (ValueError, TypeError, RecursionError):
                                source_body = None
                            evidence = source_body.get("evidence") if isinstance(source_body, dict) else None
                            fact = build_fact(row, evidence, row["raw_trade_legs"])
                            if replay_archive:
                                replay = read_archived_fact(self.archive_root, row)
                                fact["archived_replay"] = replay
                                count_archived_replay(archive_summary, replay)
                            # Bind identity to the full source key without exposing
                            # raw values if the indexed wallet/signature is malformed.
                            payload_sha256 = digest([key, fact])
                            parent = parent_facts.pop(key, None)
                            if parent is None:
                                supersedes = None
                                fact_id = digest([payload_sha256, None])
                                revision_counts["new"] += 1
                            else:
                                old_id, old_predecessor = parent
                                if digest([payload_sha256, old_predecessor]) == old_id:
                                    supersedes = old_predecessor
                                    fact_id = old_id
                                    revision_counts["unchanged"] += 1
                                else:
                                    supersedes = old_id
                                    fact_id = digest([payload_sha256, supersedes])
                                    revision_counts["revised"] += 1
                            row["transaction_fact"] = {
                                **fact, "fact_id": fact_id, "supersedes_id": supersedes,
                                "superseded_reason": "LOCAL_FACT_PAYLOAD_CHANGED" if supersedes else None,
                            }
                            # The private artifact retains every original trade
                            # column. The new fact view publishes only exact
                            # references and the interpreted, allowlisted legs.
                            row["raw_trade_legs"] = [{"source_trade_rowid": leg["source_trade_rowid"]}
                                                     for leg in row["raw_trade_legs"]]
                            row["raw_trade_legs_semantics"] = "PRIVATE_SOURCE_ROW_REFERENCES"
                        encoded = canonical(row)
                        frozen.execute("INSERT INTO frank_manifest_activity VALUES(?,?)", (row["index_rowid"], encoded))
                        if offset:
                            rows_hash.update(b",")
                        rows_hash.update(encoded.encode())
                    rows_hash.update(b"]")
                    counts = {"all_source_signatures": frozen.execute("SELECT count(*) FROM signatures").fetchone()[0],
                              "all_source_trade_legs": frozen.execute("SELECT count(*) FROM trades").fetchone()[0],
                              "frank_activity_rows": len(projection["rows"])}
                    frozen.commit()
                finally:
                    frozen.close()
                with artifact.open("rb") as stream:
                    os.fsync(stream.fileno())
                parser_files = ["wallet_activity.py", "wallet_activity_paging.py", "evidence_manifests.py"]
                if kind == "facts":
                    parser_files.append("wallet_facts.py")
                if replay_archive:
                    parser_files.extend(["archived_wallet_facts.py", "archived_account_funding.py", "ata_backfill.py",
                                         "../frank/parser.py", "../signals/classifier.py", "../signals/policy.py",
                                         "../hashing.py", "../meme/holder_ranks.py"])
                parser_hash = digest({name:file_hash(Path(__file__).parent / name) for name in parser_files})
                metadata = {"schema_version":1, "manifest_id":identity, "kind":kind, "state":"COMPLETE",
                            "scope":"LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN", "full_chain_verified":False,
                            "as_of":int(now), "created_at":now, "code_sha":self.code_sha,
                            "parser_sha256":parser_hash, "source_binding":binding,
                            "source_snapshot_sha256":source_hash, "artifact_sha256":file_hash(artifact),
                            "counts":counts, "canonical_rows_sha256":rows_hash.hexdigest(),
                            "raw_source_tables_preserved":True, "immutable_source_snapshot":True}
                if kind == "facts":
                    revision_counts["parent_only"] = len(parent_facts)
                    metadata.update(schema_version=2, supersedes_manifest_id=supersedes_manifest_id,
                                    fact_revision_counts=revision_counts)
                    if replay_archive:
                        metadata.update(schema_version=3, archive_replay_summary=archive_summary)
                metadata["manifest_sha256"] = digest(metadata)
                db.execute("INSERT INTO manifests(id,kind,request_key,binding,body) VALUES(?,?,?,?,?)",
                           (identity, kind, idempotency_key, binding, canonical(metadata)))
            published = True
            return metadata
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            if isinstance(exc, ManifestError):
                raise
            raise ManifestError("MANIFEST_CAPTURE_FAILED", 503) from None
        finally:
            if artifact is not None and not published:
                # A crash can leave an unreferenced private artifact, but no
                # incomplete capture can become visible via the manifest API.
                for suffix in ("", "-journal", "-wal", "-shm"):
                    try:
                        artifact.with_name(artifact.name+suffix).unlink(missing_ok=True)
                    except OSError:
                        pass

    def manifests(self, manifest_id=None, kind=None, limit=100, cursor=None):
        self._limit(limit)
        if manifest_id is not None:
            self._id(manifest_id)
        if kind is not None and (not isinstance(kind,str) or kind not in {"activity", "facts"}):
            raise ManifestError("INVALID_MANIFEST_KIND")
        with self._db() as db:
            if db is None:
                if cursor is not None:
                    raise ManifestError("MANIFEST_CURSOR_SOURCE_CHANGED",409)
                rows, total = [], 0
            else:
                stat = self.path.stat()
                binding = digest([str(self.path.resolve()),stat.st_dev,stat.st_ino])
                fence = db.execute("SELECT coalesce(max(seq),0) FROM manifests").fetchone()[0]
                token = None
                if cursor is not None:
                    try:
                        if not isinstance(cursor,str) or not 1<=len(cursor)<=4096:
                            raise ValueError
                        token = json.loads(base64.b64decode(cursor+'='*(-len(cursor)%4),altchars=b'-_',validate=True))
                        if (not isinstance(token,dict) or set(token)!={"v","binding","fence","after","manifest_id","kind"} or
                                token["v"]!=1 or type(token["after"]) is not int or type(token["fence"]) is not int or
                                not 0<token["after"]<=token["fence"]<=2**63-1):
                            raise ValueError
                    except (ValueError,TypeError,UnicodeError,RecursionError):
                        raise ManifestError("INVALID_MANIFEST_CURSOR") from None
                    if (token["manifest_id"],token["kind"])!=(manifest_id,kind):
                        raise ManifestError("MANIFEST_CURSOR_QUERY_CHANGED",409)
                    if token["binding"]!=binding:
                        raise ManifestError("MANIFEST_CURSOR_SOURCE_CHANGED",409)
                    fence=token["fence"]
                clauses, args = [], []
                clauses.append("seq<=?"); args.append(fence)
                if manifest_id is not None:
                    clauses.append("id=?"); args.append(manifest_id)
                if kind is not None:
                    clauses.append("kind=?"); args.append(kind)
                where = " WHERE "+" AND ".join(clauses) if clauses else ""
                total = db.execute("SELECT count(*) FROM manifests"+where, args).fetchone()[0]
                if token is not None:
                    where += (" AND " if clauses else " WHERE ")+"seq<?"
                    args.append(token["after"])
                rows = db.execute("SELECT seq,body FROM manifests"+where+" ORDER BY seq DESC LIMIT ?", [*args,limit+1]).fetchall()
            page = rows[:limit]
            return {"status":"OK", "scope":"LOCAL_INDEX_ONLY_NOT_COMPLETE_CHAIN",
                    "rows":[load_metadata(r["body"]) for r in page], "returned":len(page), "total_matching":total,
                    "next_cursor":_encode({"v":1,"binding":binding,"fence":fence,"after":page[-1]["seq"],"manifest_id":manifest_id,"kind":kind}) if len(rows)>limit else None}

    def activity(self, manifest_id, *, days="all", kind="ALL", mint=None, limit=100, cursor=None):
        self._id(manifest_id); self._limit(limit)
        if days != "all" and (type(days) is not int or days not in {1,7,30}):
            raise ManifestError("INVALID_ACTIVITY_RANGE")
        if not isinstance(kind, str) or kind not in KINDS:
            raise ManifestError("INVALID_ACTIVITY_KIND")
        from ..meme.holder_ranks import valid_pubkey
        if mint is not None and not valid_pubkey(mint):
            raise ManifestError("INVALID_ACTIVITY_MINT")
        rows = self.manifests(manifest_id=manifest_id)["rows"]
        if not rows:
            raise ManifestError("MANIFEST_NOT_FOUND", 404)
        metadata = rows[0]
        path = self.artifacts / (manifest_id+".sqlite")
        try:
            if path.is_symlink() or file_hash(path) != metadata["artifact_sha256"]:
                raise ManifestError("MANIFEST_ARTIFACT_INTEGRITY_FAILED", 503)
            db = connect(path)
            try:
                at = metadata["as_of"]
                fence = db.execute("SELECT COALESCE(max(rowid),0) FROM signatures WHERE person_id='frank'").fetchone()[0]
                source = digest([manifest_id, metadata["artifact_sha256"]])
                try:
                    token = _decode(cursor) if cursor is not None else None
                except ValueError:
                    raise ManifestError("INVALID_MANIFEST_CURSOR") from None
                if token is not None and (token["source"],token["at"],token["days"],token["kind"],token["mint"],token["fence"]) != (source,at,days,kind,mint,fence):
                    raise ManifestError("MANIFEST_CURSOR_QUERY_CHANGED", 409)
                where,args = _where(at,days,fence,kind,mint)
                total = db.execute("SELECT count(*) FROM signatures s WHERE "+where,args).fetchone()[0]
                if token is not None:
                    where += " AND (COALESCE(s.block_time,0)<? OR (COALESCE(s.block_time,0)=? AND s.rowid<?))"
                    args.extend([token["after"][0],token["after"][0],token["after"][1]])
                selected = db.execute("SELECT s.rowid AS n,COALESCE(s.block_time,0) AS at,p.body FROM signatures s JOIN frank_manifest_activity p ON p.index_rowid=s.rowid WHERE "+where+" ORDER BY COALESCE(s.block_time,0) DESC,s.rowid DESC LIMIT ?",[*args,limit+1]).fetchall()
                page = selected[:limit]
                next_cursor = _encode({"v":1,"source":source,"at":at,"days":days,"fence":fence,"kind":kind,"mint":mint,"after":[page[-1]["at"],page[-1]["n"]]}) if len(selected)>limit else None
                result = {"status":"OK", "manifest_id":manifest_id,"manifest_sha256":metadata["manifest_sha256"],
                        "scope":metadata["scope"], "full_chain_verified":False,"immutable_source_snapshot":True,
                        "as_of":at,"rows":[json.loads(r["body"]) for r in page],"returned":len(page),
                        "total_signatures":total,"next_cursor":next_cursor,"kind":kind,"mint":mint,"days":days}
                if "archive_replay_summary" in metadata:
                    result["archive_replay_summary"] = metadata["archive_replay_summary"]
                if file_hash(path) != metadata["artifact_sha256"]:
                    raise ManifestError("MANIFEST_ARTIFACT_INTEGRITY_FAILED",503)
                return result
            finally:
                db.close()
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            if isinstance(exc, ManifestError):
                raise
            raise ManifestError("MANIFEST_READ_FAILED", 503) from None
