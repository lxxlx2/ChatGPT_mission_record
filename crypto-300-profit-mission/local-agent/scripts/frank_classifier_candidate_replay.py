"""Read-only production-vs-candidate Frank classifier replay.

The source SQLite file is opened read-only. All replay databases and the report
must live in one brand-new isolated workspace outside the production directory.
No live delivery path is enabled.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path

from mission_agent.signals.classifier import classify
from mission_agent.market.sol_usd import _simple_sol_quote_eligible
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy
from mission_agent.signals.store import Ledger

_HEX64=re.compile(r"^[0-9a-fA-F]{64}$")
_RESERVED={"baseline.sqlite","candidate.sqlite"}


def canonical_hash(tx: dict) -> str:
    return hashlib.sha256(
        json.dumps(tx, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _existing_file(path: Path, label: str) -> Path:
    try:
        resolved=path.expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(label+"_UNAVAILABLE") from exc
    if not resolved.is_file():
        raise ValueError(label+"_NOT_FILE")
    return resolved


def _new_workspace(path: Path, source: Path) -> Path:
    raw=path.expanduser()
    parent=_existing_dir(raw.parent, "WORKSPACE_PARENT")
    resolved=parent/raw.name
    if resolved.exists():
        raise ValueError("NEW_ISOLATED_WORKSPACE_REQUIRED")
    source_parent=source.parent.resolve()
    if resolved==source_parent or source_parent in resolved.parents:
        raise ValueError("WORKSPACE_INSIDE_SOURCE_DIRECTORY")
    return resolved


def _existing_dir(path: Path, label: str) -> Path:
    try:
        resolved=path.expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(label+"_UNAVAILABLE") from exc
    if not resolved.is_dir():
        raise ValueError(label+"_NOT_DIRECTORY")
    return resolved


def _exclusive_write_text(path: Path, value: str) -> None:
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    if hasattr(os,"O_NOFOLLOW"):flags|=os.O_NOFOLLOW
    fd=os.open(path,flags,0o600)
    try:
        with os.fdopen(fd,"w") as handle:
            handle.write(value)
    except Exception:
        try:path.unlink()
        except OSError:pass
        raise


def _output_in_workspace(path: Path, work: Path) -> Path:
    raw=path.expanduser()
    if raw.is_absolute():
        candidate=Path(os.path.abspath(raw))
    else:
        candidate=Path(os.path.abspath(Path.cwd()/raw))
    try:
        candidate.relative_to(work)
    except ValueError as exc:
        raise ValueError("OUTPUT_MUST_BE_INSIDE_WORKSPACE") from exc
    if candidate==work or candidate.name in _RESERVED:
        raise ValueError("OUTPUT_PATH_RESERVED")
    if candidate.exists():
        raise ValueError("OUTPUT_MUST_NOT_EXIST")
    return candidate


def raw_transaction(row: sqlite3.Row, source: Path) -> tuple[dict | None, str | None]:
    expected=row["raw_hash"]
    if not isinstance(expected,str) or not _HEX64.fullmatch(expected):
        return None, "RAW_HASH_MISSING_OR_INVALID"
    reference=row["raw_reference"]
    if not reference:
        return None, "RAW_REFERENCE_MISSING"
    path=Path(reference)
    if not path.is_absolute():
        path=source.parent/path
    try:
        path=path.resolve(strict=True)
    except (OSError,RuntimeError):
        return None, "RAW_FILE_MISSING"
    if not path.is_file():
        return None, "RAW_FILE_MISSING"
    try:
        tx=json.loads(gzip.decompress(path.read_bytes()))
    except (OSError,EOFError,ValueError,TypeError):
        return None, "RAW_FILE_INVALID"
    if canonical_hash(tx)!=expected.lower():
        return None, "RAW_HASH_MISMATCH"
    return tx,None


def _epoch(value, fallback: int | None = None) -> int | None:
    if value in (None,""):
        return fallback
    try:
        return int(datetime.fromisoformat(str(value)).timestamp())
    except (ValueError,TypeError,OverflowError,OSError):
        return fallback


def _source_active_eval_clock(db: sqlite3.Connection) -> dict[tuple[str,str],int]:
    clocks={}
    try:
        rows=db.execute("SELECT person_id,signature,at,body FROM v1_evaluations").fetchall()
    except sqlite3.Error:
        return clocks
    for row in rows:
        try:body=json.loads(row["body"])
        except (TypeError,ValueError):continue
        if body.get("kind")!="ACTIVE_TRADE":continue
        key=(row["person_id"],row["signature"])
        clocks[key]=max(int(row["at"]),clocks.get(key,0))
    return clocks


def _terminal_clock(db: sqlite3.Connection, rows: list[sqlite3.Row]) -> int | None:
    try:
        row=db.execute("SELECT value FROM v1_meta WHERE key='last_time'").fetchone()
        if row and row[0] not in (None,""):return int(row[0])
    except (sqlite3.Error,ValueError,TypeError):
        pass
    values=[int(r["block_time"]) for r in rows if r["block_time"] is not None]
    return max(values) if values else None


def insert_signature(ledger: Ledger, row: sqlite3.Row, body: dict) -> sqlite3.Row:
    ledger.db.execute(
        """INSERT INTO signatures(
             wallet,signature,person_id,slot,block_time,seen_at,classified_at,
             raw_hash,raw_reference,body,alert_state,alert_reason
           ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            row["wallet"],row["signature"],row["person_id"],row["slot"],
            row["block_time"],row["seen_at"],row["classified_at"],
            row["raw_hash"],row["raw_reference"],json.dumps(body,sort_keys=True),
            row["alert_state"],row["alert_reason"],
        ),
    )
    return ledger.db.execute(
        "SELECT * FROM signatures WHERE wallet=? AND signature=?",
        (row["wallet"],row["signature"]),
    ).fetchone()


def replay(
    path: Path,
    rows: list[sqlite3.Row],
    bodies: dict[str,dict],
    policy: dict,
    *,
    source_eval_clock: dict[tuple[str,str],int],
    terminal_clock: int | None,
) -> dict:
    ledger=Ledger(path)
    engine=Engine(ledger,policy,dry_run=True)
    timing_sources=Counter()
    ordered=[]
    for row in rows:
        source_clock=source_eval_clock.get((row["person_id"],row["signature"]))
        fallback=int(row["block_time"]) if row["block_time"] is not None else None
        classified_clock=_epoch(row["classified_at"],fallback)
        arrival=source_clock if source_clock is not None else classified_clock
        if terminal_clock is not None and arrival is not None:
            arrival=min(arrival,terminal_clock)
        timing_sources["SOURCE_ACTIVE_EVALUATION_AT" if source_clock is not None else "CLASSIFIED_AT_SURROGATE"]+=1
        ordered.append((arrival if arrival is not None else -1,int(row["block_time"] or -1),int(row["slot"] or -1),row["signature"],row))
    ordered.sort(key=lambda x:x[:4])
    for arrival,_,_,_,row in ordered:
        inserted=insert_signature(ledger,row,bodies[row["signature"]])
        if arrival>=0:engine.tick(arrival)
        engine.process(inserted)
    if terminal_clock is not None:engine.tick(terminal_clock)

    def body_map(sql: str, key_fields: tuple[str,...]) -> dict:
        out={}
        for row in ledger.db.execute(sql):
            key="|".join(str(row[k]) for k in key_fields)
            try:body=json.loads(row["body"])
            except (TypeError,ValueError):body={"__invalid_body__":row["body"]}
            out[key]=body
        return out

    signals=body_map("SELECT signal_id,body FROM signals ORDER BY signal_id",("signal_id",))
    states=body_map("SELECT person_id,mint,body FROM v1_states ORDER BY person_id,mint",("person_id","mint"))
    evaluations=body_map("SELECT evaluation_id,body FROM v1_evaluations ORDER BY evaluation_id",("evaluation_id",))
    emails={
        row["signal_id"]:{
            "subject":row["subject"],"body":row["body"],"content_hash":row["content_hash"]
        }
        for row in ledger.db.execute("SELECT signal_id,subject,body,content_hash FROM email_content ORDER BY signal_id")
    }
    summary=engine.summary()
    verify_dry_run_outbox(ledger.db)
    ledger.db.close()
    return {
        "signals":signals,"states":states,"evaluations":evaluations,"emails":emails,
        "summary":summary,"timing_sources":dict(timing_sources),
    }


def verify_dry_run_outbox(db: sqlite3.Connection) -> None:
    """Runtime safety check that also runs under python -O."""
    if db.execute("SELECT 1 FROM outbox WHERE status IS NOT 'DRY_RUN_AUDIT'").fetchone():
        raise RuntimeError("NON_DRY_RUN_OUTBOX")


def _source_snapshot(db: sqlite3.Connection) -> dict:
    def body_map(table: str, key_cols: tuple[str,...]) -> dict:
        cols=",".join(key_cols)
        try:rows=db.execute(f"SELECT {cols},body FROM {table}").fetchall()
        except sqlite3.Error:return {}
        out={}
        for row in rows:
            key="|".join(str(row[k]) for k in key_cols)
            try:body=json.loads(row["body"])
            except (TypeError,ValueError):body={"__invalid_body__":row["body"]}
            out[key]=body
        return out
    emails={}
    try:
        for row in db.execute("SELECT signal_id,subject,body,content_hash FROM email_content"):
            emails[row["signal_id"]]={"subject":row["subject"],"body":row["body"],"content_hash":row["content_hash"]}
    except sqlite3.Error:
        pass
    return {
        "signals":body_map("signals",("signal_id",)),
        "states":body_map("v1_states",("person_id","mint")),
        "evaluations":body_map("v1_evaluations",("evaluation_id",)),
        "emails":emails,
    }


def _flatten(value, prefix="") -> dict:
    if isinstance(value,dict):
        out={}
        for key in sorted(value):
            child=f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten(value[key],child))
        return out
    if isinstance(value,list):
        out={}
        for index,item in enumerate(value):
            child=f"{prefix}[{index}]"
            out.update(_flatten(item,child))
        if not value:out[prefix]=[]
        return out
    return {prefix:value}


def _field_diff(before,after) -> list[dict]:
    a=_flatten(before);b=_flatten(after);out=[]
    for key in sorted(set(a)|set(b)):
        if a.get(key)!=b.get(key):
            out.append({"field":key,"before":a.get(key),"after":b.get(key)})
    return out


def _mapping_deltas(before: dict,after: dict) -> list[dict]:
    out=[]
    for key in sorted(set(before)|set(after)):
        if key not in before:
            out.append({"key":key,"change":"ADDED","after":after[key]})
        elif key not in after:
            out.append({"key":key,"change":"REMOVED","before":before[key]})
        elif before[key]!=after[key]:
            out.append({"key":key,"change":"CHANGED","field_diffs":_field_diff(before[key],after[key])})
    return out


def semantic_classification(value: dict) -> tuple:
    """Exclude evidence-only metadata from signal-affecting transition counts.

    Complete field diffs are still retained separately for forensic review.
    The derived SOL route-eligibility predicate is a classification-relevant
    semantic; merely adding an audit field without changing eligibility is not.
    """
    trade=value.get("trade")
    projected=None
    if isinstance(trade,dict):
        important=("mint","direction","token_amount_raw","token_decimals",
                   "quote_asset","quote_amount_raw","quote_decimals",
                   "amount_predicate","amount_predicate_reason")
        projected=tuple((name,str(trade.get(name))) for name in important)
        if trade.get("quote_asset") in {"SOL","WSOL","So11111111111111111111111111111111111111112"}:
            projected+= (("simple_sol_quote_eligible",_simple_sol_quote_eligible(trade)),)
    return (value.get("classification"),value.get("classification_reason"),projected)


def _signal_identity(body: dict) -> tuple:
    return (
        body.get("person_id"),body.get("mint"),body.get("episode_id"),
        body.get("signal_type"),body.get("stage"),body.get("triggered_at"),
        body.get("triggering_signature"),body.get("latest_buy_signature"),
    )


def _signal_counter(signals: dict) -> Counter:
    return Counter(_signal_identity(body) for body in signals.values())


def sha256_file(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--policy",type=Path,required=True)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--integrity-file",type=Path,action="append",default=[],
                   help="Additional read-only files to hash before and after replay (health.json / plists)")
    args=p.parse_args()

    source=_existing_file(args.source,"SOURCE")
    policy_path=_existing_file(args.policy,"POLICY")
    work=_new_workspace(args.work,source)
    output=_output_in_workspace(args.output,work)
    baseline_path=work/"baseline.sqlite"
    candidate_path=work/"candidate.sqlite"
    verification_files=[source]
    for extra in args.integrity_file:
        path=_existing_file(extra,"INTEGRITY_FILE")
        if path not in verification_files:
            verification_files.append(path)
    before={str(path):sha256_file(path) for path in verification_files}

    # All path validation happens before the first write.
    work.mkdir(mode=0o700)
    output.parent.mkdir(parents=True,exist_ok=False) if output.parent!=work else None

    db=sqlite3.connect(f"file:{source}?mode=ro",uri=True)
    db.row_factory=sqlite3.Row
    rows=db.execute("SELECT * FROM signatures").fetchall()
    source_eval_clock=_source_active_eval_clock(db)
    terminal_clock=_terminal_clock(db,rows)
    stored={};candidate={};transitions=[];classification_body_deltas=[];unreclassified=[]

    for row in rows:
        try:old=json.loads(row["body"])
        except (TypeError,ValueError):
            raise ValueError("SOURCE_BODY_INVALID:"+row["signature"])
        stored[row["signature"]]=old
        tx,error=raw_transaction(row,source)
        if error:
            candidate[row["signature"]]=old
            unreclassified.append({"signature":row["signature"],"reason":error})
            continue
        new=classify(row["signature"],tx,row["wallet"])
        candidate[row["signature"]]=new
        if old!=new:
            classification_body_deltas.append({
                "signature":row["signature"],
                "block_time":row["block_time"],
                "field_diffs":_field_diff(old,new),
            })
        if semantic_classification(old)!=semantic_classification(new):
            transitions.append({
                "signature":row["signature"],"block_time":row["block_time"],
                "old_classification":old.get("classification"),"old_reason":old.get("classification_reason"),
                "new_classification":new.get("classification"),"new_reason":new.get("classification_reason"),
                "old_trade":old.get("trade"),"new_trade":new.get("trade"),
                "source_program_ids":(old.get("evidence") or {}).get("program_ids") or [],
                "candidate_program_ids":(new.get("evidence") or {}).get("program_ids") or [],
                "classification_details":new.get("classification_details"),
            })

    policy=load_policy(policy_path)
    source_snapshot=_source_snapshot(db)
    baseline=replay(
        baseline_path,rows,stored,policy,
        source_eval_clock=source_eval_clock,terminal_clock=terminal_clock,
    )
    revised=replay(
        candidate_path,rows,candidate,policy,
        source_eval_clock=source_eval_clock,terminal_clock=terminal_clock,
    )

    source_signal_identity=_signal_counter(source_snapshot["signals"])
    baseline_signal_identity=_signal_counter(baseline["signals"])
    candidate_signal_identity=_signal_counter(revised["signals"])

    source_baseline_state_deltas=_mapping_deltas(source_snapshot["states"],baseline["states"])
    candidate_state_deltas=_mapping_deltas(baseline["states"],revised["states"])
    source_baseline_signal_content_deltas=_mapping_deltas(source_snapshot["signals"],baseline["signals"])
    candidate_signal_content_deltas=_mapping_deltas(baseline["signals"],revised["signals"])
    source_baseline_evaluation_deltas=_mapping_deltas(source_snapshot["evaluations"],baseline["evaluations"])
    candidate_evaluation_deltas=_mapping_deltas(baseline["evaluations"],revised["evaluations"])
    source_baseline_email_deltas=_mapping_deltas(source_snapshot["emails"],baseline["emails"])
    candidate_email_deltas=_mapping_deltas(baseline["emails"],revised["emails"])

    source_identity_parity=source_signal_identity==baseline_signal_identity
    candidate_identity_parity=baseline_signal_identity==candidate_signal_identity
    baseline_state_parity=not source_baseline_state_deltas

    transition_counts=Counter(
        f"{x['old_classification']}->{x['new_classification']}" for x in transitions
    )
    if unreclassified:
        acceptance="BLOCKED_RAW_COVERAGE"
    elif not source_identity_parity or not baseline_state_parity:
        acceptance="BLOCKED_BASELINE_PARITY"
    else:
        acceptance="REVIEW_DELTAS"

    result={
        "study":"FRANK_CLASSIFIER_CANDIDATE_REPLAY_V2",
        "source":str(source),"source_open_mode":"READ_ONLY",
        "workspace":str(work),"report_output":str(output),
        "production_files_changed":"NOT_VERIFIED_FROM_SOURCE_COPY",
        "live_signal_sent":False,"production_trading":"NO_GO",
        "verified_integrity_files_sha256":before,
        "timing_equivalence":{
            "terminal_clock":terminal_clock,
            "per_signature_sources":baseline["timing_sources"],
            "status":"SOURCE_ACTIVE_EVAL_AT_ELSE_CLASSIFIED_AT_SURROGATE",
            "limitation":"Historical finalized-chain poll clocks are not stored for every scanner cycle; classified_at is used only when no source ACTIVE_TRADE evaluation clock exists.",
        },
        "signature_count":len(rows),"reclassified_count":len(rows)-len(unreclassified),
        "unreclassified_count":len(unreclassified),"unreclassified":unreclassified,
        "classification_transition_count":len(transitions),
        "classification_transition_counts":dict(sorted(transition_counts.items())),
        "classification_transitions":transitions,
        "classification_body_delta_count":len(classification_body_deltas),
        "classification_body_deltas":classification_body_deltas,
        "source_summary":{
            "signal_count":len(source_snapshot["signals"]),"state_count":len(source_snapshot["states"]),
            "evaluation_count":len(source_snapshot["evaluations"]),"email_count":len(source_snapshot["emails"]),
        },
        "baseline":baseline["summary"],"candidate":revised["summary"],
        "baseline_source_signal_identity_parity":source_identity_parity,
        "baseline_source_state_parity":baseline_state_parity,
        "candidate_signal_identity_parity":candidate_identity_parity,
        "source_baseline_state_deltas":source_baseline_state_deltas,
        "candidate_state_deltas":candidate_state_deltas,
        "source_baseline_signal_content_deltas":source_baseline_signal_content_deltas,
        "candidate_signal_content_deltas":candidate_signal_content_deltas,
        "source_baseline_evaluation_deltas":source_baseline_evaluation_deltas,
        "candidate_evaluation_deltas":candidate_evaluation_deltas,
        "source_baseline_email_deltas":source_baseline_email_deltas,
        "candidate_email_deltas":candidate_email_deltas,
        "new_signal_identities":[list(x) for x in (candidate_signal_identity-baseline_signal_identity).elements()],
        "lost_signal_identities":[list(x) for x in (baseline_signal_identity-candidate_signal_identity).elements()],
        "acceptance":acceptance,
    }
    db.close()
    after={str(path):sha256_file(path) for path in verification_files}
    if after!=before:
        raise RuntimeError("READ_ONLY_INPUT_INTEGRITY_CHANGED")
    result["integrity_check"]="PASS"
    result["integrity_verified_file_count"]=len(verification_files)
    # Snapshot check only: source is normally a copy, not proof about the live
    # production DB. Do not claim production unchanged from static strings.
    if output.exists():raise ValueError("OUTPUT_MUST_NOT_EXIST")
    _exclusive_write_text(output,json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({
        "signature_count":result["signature_count"],
        "reclassified_count":result["reclassified_count"],
        "unreclassified_count":result["unreclassified_count"],
        "transition_count":result["classification_transition_count"],
        "transition_counts":result["classification_transition_counts"],
        "classification_body_delta_count":result["classification_body_delta_count"],
        "baseline_source_signal_identity_parity":result["baseline_source_signal_identity_parity"],
        "baseline_source_state_parity":result["baseline_source_state_parity"],
        "candidate_signal_identity_parity":result["candidate_signal_identity_parity"],
        "candidate_state_delta_count":len(candidate_state_deltas),
        "candidate_signal_content_delta_count":len(candidate_signal_content_deltas),
        "candidate_evaluation_delta_count":len(candidate_evaluation_deltas),
        "candidate_email_delta_count":len(candidate_email_deltas),
        "acceptance":acceptance,"output":str(output),
        "integrity_check":result["integrity_check"],
        "integrity_verified_file_count":len(verification_files),
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
