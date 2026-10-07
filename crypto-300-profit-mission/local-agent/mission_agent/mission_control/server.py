"""Localhost-only Mission Meme V1 dashboard server."""
from __future__ import annotations

import ipaddress
import json
import mimetypes
import os
import re
import socket
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from ..meme.cluster import RpcCache, SolanaReadOnlyRPC, WalletClusterAnalyzer, load_registry, markdown
from ..meme.market import DexScreenerMarketClient
from .db import open_control_ro
from .frank import FrankReader
from .jupiter import JupiterQuoteClient


def _host_is_loopback(host: str, port: int) -> bool:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    if not infos:
        return False
    for _, _, _, _, sockaddr in infos:
        address = str(sockaddr[0]).split("%", 1)[0]
        try:
            if not ipaddress.ip_address(address).is_loopback:
                return False
        except ValueError:
            return False
    return True


def _host_header_is_loopback(value: str | None) -> bool:
    value = (value or "").strip().lower()
    if not value:
        return False
    if value.startswith("["):
        end = value.find("]")
        host = value[1:end] if end >= 0 else value
    else:
        host = value.rsplit(":", 1)[0] if ":" in value else value
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _origin_is_loopback(value: str | None) -> bool:
    if not value:
        return True
    try:
        parsed=urlparse(value)
    except ValueError:
        return False
    if parsed.scheme not in {"http","https"} or not parsed.hostname:
        return False
    host=parsed.hostname.lower()
    if host=="localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _content_type_is_json(value: str | None) -> bool:
    return (value or "").split(";",1)[0].strip().lower()=="application/json"


def _decode_json_object(raw: bytes) -> dict:
    try:
        body=json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("INVALID_JSON") from exc
    if not isinstance(body,dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return body


def _atomic_write_text(path: Path, text_value: str):
    path = Path(path)
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}-{uuid.uuid4().hex}")
    try:
        tmp.write_text(text_value)
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


SOLANA_PUBKEY_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
CLUSTER_PRESETS = {
    "quick": {
        "deep_holders": 6, "history_per_holder": 8, "funding_lookback": 4,
        "adaptive_history_per_holder": None, "adaptive_funding_lookback": None,
    },
    "standard": {
        "deep_holders": 6, "history_per_holder": 12, "funding_lookback": 8,
        "adaptive_history_per_holder": 30, "adaptive_funding_lookback": 12,
    },
    "deep": {
        "deep_holders": 20, "history_per_holder": 100, "funding_lookback": 50,
        "adaptive_history_per_holder": None, "adaptive_funding_lookback": None,
    },
}


class ClusterJobManager:
    def __init__(self, control_root: Path, production_root: Path | None = None):
        self.control_root = Path(control_root)
        self.report_root = self.control_root / "cluster-reports"
        self.report_root.mkdir(parents=True, exist_ok=True)
        self.cache_path = self.control_root / "wallet-cluster-rpc-cache.sqlite"
        self.registry_path = Path(__file__).resolve().parents[2] / "config" / "meme_special_addresses.json"
        configured=os.environ.get("SOLANA_RPC_URLS")
        if configured:
            self.rpc_endpoints=[x.strip() for x in configured.split(",") if x.strip()]
        else:
            primary=os.environ.get("SOLANA_RPC_URL","https://api.mainnet.solana.com")
            self.rpc_endpoints=[
                primary,
                "https://solana-rpc.publicnode.com",
                "https://api.mainnet-beta.solana.com",
                "https://rpc.ankr.com/solana",
            ]
        self.rpc_endpoints=list(dict.fromkeys(self.rpc_endpoints))
        self.rpc_endpoint=self.rpc_endpoints[0]
        self.market_client=DexScreenerMarketClient()
        self.jupiter=JupiterQuoteClient(os.environ.get("JUPITER_API_KEY"))
        self.frank=FrankReader(production_root) if production_root is not None else None
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="meme-cluster")
        self.lock = threading.Lock()
        self.jobs: dict[str, dict] = {}
        self.max_retained_jobs = 64

    @staticmethod
    def validate_mint(mint: str) -> str:
        value = (mint or "").strip()
        if not SOLANA_PUBKEY_RE.fullmatch(value):
            raise ValueError("INVALID_SOLANA_CA")
        return value

    def _public_job(self, job: dict) -> dict:
        return {k: v for k, v in job.items() if k not in {"future"}}

    def _prune_jobs_locked(self):
        finished=[
            job for job in self.jobs.values()
            if job["status"] in {"DONE","ERROR"}
        ]
        finished.sort(key=lambda x: x.get("finished_at") or x.get("created_at") or 0, reverse=True)
        keep={x["job_id"] for x in finished[:self.max_retained_jobs]}
        active={x["job_id"] for x in self.jobs.values() if x["status"] in {"QUEUED","RUNNING"}}
        for job_id in list(self.jobs):
            if job_id not in keep and job_id not in active:
                self.jobs.pop(job_id,None)

    def submit(self, mint: str, preset: str = "standard") -> dict:
        mint = self.validate_mint(mint)
        if preset not in CLUSTER_PRESETS:
            raise ValueError("INVALID_CLUSTER_PRESET")
        with self.lock:
            self._prune_jobs_locked()
            for job in self.jobs.values():
                if job["mint"] == mint and job["preset"] == preset and job["status"] in {"QUEUED", "RUNNING"}:
                    return self._public_job(job)
            job_id = uuid.uuid4().hex
            job = {
                "job_id": job_id,
                "mint": mint,
                "preset": preset,
                "status": "QUEUED",
                "created_at": time.time(),
                "started_at": None,
                "finished_at": None,
                "error": None,
                "progress": {"stage":"QUEUED","updated_at":time.time()},
            }
            self.jobs[job_id] = job
            job["future"] = self.executor.submit(self._run, job_id)
            return self._public_job(job)

    def _frank_snapshot(self, mint: str) -> dict:
        if self.frank is None:
            return {"status":"UNAVAILABLE","reason":"PRODUCTION_ROOT_NOT_CONFIGURED","mint":mint}
        try:
            return self.frank.mint_snapshot(mint)
        except (OSError,ValueError,sqlite3.Error) as exc:
            # CA research must remain usable when the optional production
            # Frank read-only database is temporarily unavailable.
            return {
                "status":"UNAVAILABLE","reason":"FRANK_READ_ERROR","mint":mint,
                "error_class":type(exc).__name__,
            }

    def _set_progress(self, job_id: str, stage: str, details: dict | None = None):
        details=details or {}
        progress={"stage":stage,"updated_at":time.time()}
        if stage=="BASE_READY":
            profile=details.get("token_profile") or {}
            market=details.get("market") or {}
            pair=market.get("main_pair") or {}
            progress.update({
                "token_program":profile.get("token_program"),
                "mint_authority":profile.get("mint_authority"),
                "freeze_authority":profile.get("freeze_authority"),
                "market_status":market.get("status"),
                "name":market.get("name"),
                "symbol":market.get("symbol"),
                "market_cap_usd":market.get("market_cap_usd"),
                "liquidity_usd":pair.get("liquidity_usd"),
            })
        else:
            for key in ("top_accounts_resolved","scanned","target","owner","mode","deep_holders_scanned","adaptive_deepened"):
                if key in details:progress[key]=details.get(key)
            if details.get("owners"):progress["owners"]=list(details.get("owners") or [])[:10]
        with self.lock:
            job=self.jobs.get(job_id)
            if job is not None and job.get("status") in {"QUEUED","RUNNING"}:
                job["progress"]=progress

    @staticmethod
    def _assessment_snapshot(report: dict) -> dict:
        assessment=report.get("assessment") or {}
        metrics=report.get("metrics") or {}
        profile=report.get("token_profile") or {}
        narrative=assessment.get("narrative_status")
        structure=assessment.get("trading_status") or "UNRESOLVED"
        investment="PENDING_NARRATIVE" if narrative=="NOT_AUTOMATICALLY_VERIFIED" else structure
        return {
            "structure_rating":structure,
            "investment_rating":investment,
            "chain_permission_status":assessment.get("chain_permission_status"),
            "cluster_status":assessment.get("cluster_status"),
            "largest_control_cluster_pct":metrics.get("LARGEST_PROBABLE_CONTROL_CLUSTER_PCT"),
            "unresolved_material_holder_pct":metrics.get("UNRESOLVED_MATERIAL_HOLDER_PCT"),
            "mint_authority_active":bool(profile.get("mint_authority")),
            "freeze_authority_active":bool(profile.get("freeze_authority")),
            "narrative_status":narrative,
        }

    def _attach_assessment_history(self, out: Path, report: dict, preset: str):
        history_path=out/"assessment-history.json"
        try:
            history=json.loads(history_path.read_text()) if history_path.is_file() else []
            if not isinstance(history,list):history=[]
        except (OSError,ValueError):
            history=[]
        snapshot=self._assessment_snapshot(report)
        previous=(history[-1].get("snapshot") or {}) if history else {}
        changed=[key for key,value in snapshot.items() if previous.get(key)!=value]
        if not history or changed:
            new_risk=[]
            removed_uncertainty=[]
            if snapshot.get("chain_permission_status")=="RISK" and previous.get("chain_permission_status")!="RISK":
                new_risk.append("CHAIN_PERMISSION_RISK")
            if snapshot.get("cluster_status")=="PROBABLE_CONTROL_CLUSTER_PRESENT" and previous.get("cluster_status")!="PROBABLE_CONTROL_CLUSTER_PRESENT":
                new_risk.append("PROBABLE_CONTROL_CLUSTER_PRESENT")
            if previous.get("cluster_status")=="WALLET_CLUSTER_UNRESOLVED" and snapshot.get("cluster_status")!="WALLET_CLUSTER_UNRESOLVED":
                removed_uncertainty.append("WALLET_CLUSTER_UNRESOLVED")
            if previous.get("chain_permission_status")=="UNRESOLVED" and snapshot.get("chain_permission_status") in {"PASS","RISK"}:
                removed_uncertainty.append("CHAIN_PERMISSION_UNRESOLVED")
            entry={
                "observed_at":report.get("observed_at") or time.time(),
                "preset":preset,
                "structure_rating":snapshot["structure_rating"],
                "investment_rating":snapshot["investment_rating"],
                "changed_fields":changed if history else list(snapshot),
                "new_evidence":changed if history else ["INITIAL_OBSERVATION"],
                "removed_uncertainty":removed_uncertainty,
                "new_risk":new_risk,
                "reason":"首次观测" if not history else "关键结论字段变化：" + ", ".join(changed),
                "snapshot":snapshot,
            }
            history.append(entry)
            history=history[-100:]
            _atomic_write_text(history_path,json.dumps(history,ensure_ascii=False,indent=2,sort_keys=True))
        report["assessment_history"]=[
            {k:v for k,v in row.items() if k!="snapshot"} for row in history[-20:]
        ]

    def _run(self, job_id: str):
        with self.lock:
            job = self.jobs[job_id]
            job["status"] = "RUNNING"
            job["started_at"] = time.time()
            mint = job["mint"]
            preset = job["preset"]
        cache = RpcCache(self.cache_path)
        try:
            rpc = SolanaReadOnlyRPC(
                self.rpc_endpoint,
                fallback_endpoints=self.rpc_endpoints[1:],
                cache=cache,
            )
            registry = load_registry(self.registry_path)
            opts = CLUSTER_PRESETS[preset]
            report = WalletClusterAnalyzer(
                mint,
                rpc=rpc,
                special_registry=registry,
                deep_holders=opts["deep_holders"],
                history_per_holder=opts["history_per_holder"],
                funding_lookback=opts["funding_lookback"],
                adaptive_history_per_holder=opts.get("adaptive_history_per_holder"),
                adaptive_funding_lookback=opts.get("adaptive_funding_lookback"),
                market_client=self.market_client,
                progress_callback=lambda stage,details:self._set_progress(job_id,stage,details),
            ).analyze()
            report["frank"]=self._frank_snapshot(mint)
            try:
                report["execution_quote_30_usdc"]=self.jupiter.quote_usdc_to_token(
                    mint,
                    int(report["decimals"]),
                    usdc_amount=Decimal("30"),
                    slippage_bps=100,
                )
            except Exception as exc:
                report["execution_quote_30_usdc"]={
                    "status":"UNAVAILABLE",
                    "source":"JUPITER_OFFICIAL",
                    "reason":type(exc).__name__,
                }
            self._set_progress(job_id,"REPORT_PERSISTING",{"deep_holders_scanned":(report.get("coverage") or {}).get("deep_holders_scanned"),"adaptive_deepened":len((report.get("coverage") or {}).get("adaptive_deepened_owners") or [])})
            stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            out = self.report_root / mint
            out.mkdir(parents=True, exist_ok=True)
            self._attach_assessment_history(out,report,preset)
            payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
            _atomic_write_text(out / f"{stamp}.json", payload)
            _atomic_write_text(out / f"{stamp}.md", markdown(report))
            _atomic_write_text(out / "latest.json", payload)
            with self.lock:
                job = self.jobs[job_id]
                job["status"] = "DONE"
                job["finished_at"] = time.time()
                job["progress"] = {"stage":"DONE","updated_at":job["finished_at"]}
                self._prune_jobs_locked()
        except Exception as exc:
            with self.lock:
                job = self.jobs[job_id]
                job["status"] = "ERROR"
                job["finished_at"] = time.time()
                job["error"] = {
                    "type": type(exc).__name__,
                    "message": str(exc)[:500],
                }
                job["progress"] = {"stage":"ERROR","updated_at":job["finished_at"]}
                self._prune_jobs_locked()
        finally:
            cache.close()

    def get(self, job_id: str) -> dict | None:
        with self.lock:
            job = self.jobs.get(job_id)
            return None if job is None else self._public_job(job)

    def latest(self, mint: str) -> dict | None:
        mint = self.validate_mint(mint)
        path = self.report_root / mint / "latest.json"
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return None


class DashboardState:
    def __init__(self, production_root: Path, control_root: Path):
        self.frank = FrankReader(production_root)
        self.control_root = Path(control_root)
        self.control_db = self.control_root / "mission-control.sqlite"
        self.control_health = self.control_root / "mission-control-health.json"
        self.cluster_jobs = ClusterJobManager(self.control_root, production_root)

    def _control_query(self, sql: str, params=()):
        if not self.control_db.is_file():
            return []
        db = open_control_ro(self.control_db)
        try:
            return [dict(row) for row in db.execute(sql, params).fetchall()]
        except sqlite3.DatabaseError:
            return []
        finally:
            db.close()

    def runtime(self):
        return self.frank.runtime()

    def mission_control_health(self):
        if not self.control_health.is_file():
            return {"status": "UNKNOWN", "reason": "MISSION_CONTROL_HEARTBEAT_MISSING"}
        try:
            return json.loads(self.control_health.read_text())
        except (OSError, ValueError):
            return {"status": "UNKNOWN", "reason": "MISSION_CONTROL_HEARTBEAT_UNREADABLE"}

    def candidates(self):
        candidates = self.frank.candidates()
        # candidate_latest is one mutable row per person/mint/episode, refreshed on
        # every evaluation. Immutable decision_events remain transition-only.
        latest = self._control_query(
            "SELECT person_id,mint,episode_id,decision,evaluated_at,body FROM candidate_latest ORDER BY evaluated_at DESC"
        )
        by_key = {(x["person_id"], x["mint"], x["episode_id"]): x for x in latest}
        seen = set()
        for item in candidates:
            key=(item["person_id"], item["mint"], item.get("episode_id"));seen.add(key)
            row = by_key.get(key)
            if row:
                body = json.loads(row["body"])
                item["decision"] = body["decision"]
                item["decision_created_at"] = row["evaluated_at"]
                item["metrics"] = body.get("metrics") or {}
                inputs = body.get("inputs") or {}
                item["decision_quote"] = inputs.get("quote") or {}
                item["reasons"] = body.get("reasons") or []
                item["missing"] = body.get("missing") or []
                item["invalidation"] = body.get("invalidation") or []
            else:
                item["decision"] = "UNASSESSED"
                item["metrics"] = {}
                item["decision_quote"] = {}
        # A SOL-normalized sidecar can legitimately create a follow candidate that
        # does not exist in the frozen production signal table. candidate_latest is
        # the canonical Mission Control view, so expose those rows without writing
        # anything back to Frank production.
        for key,row in by_key.items():
            if key in seen:
                continue
            body=json.loads(row["body"]);inputs=body.get("inputs") or {}
            item={k:inputs.get(k) for k in (
                "person_id","mint","episode_id","pattern","source_signal_id","source_signal_type","source_signal_at",
                "position_state","current_raw","buy_count","sell_count","latest_side","latest_signature","latest_at",
                "latest_buy_at","latest_buy_price_usdc","latest_buy_price_status","latest_buy_quote_asset",
                "latest_buy_quote_quantity","token_decimals"
            )}
            item.update({
                "decision":body["decision"],"decision_created_at":row["evaluated_at"],
                "metrics":body.get("metrics") or {},"decision_quote":inputs.get("quote") or {},
                "reasons":body.get("reasons") or [],"missing":body.get("missing") or [],
                "invalidation":body.get("invalidation") or [],"candidate_source":"MISSION_CONTROL_OVERLAY",
            })
            candidates.append(item)
        candidates.sort(key=lambda x:int(x.get("latest_at") or 0),reverse=True)
        return candidates

    def recent_trades(self):
        return self.frank.recent_trades(100)

    def review_activity(self):
        return self.frank.review_activity(30)

    def decisions(self):
        rows = self._control_query("SELECT * FROM decision_events ORDER BY rowid DESC LIMIT 100")
        for row in rows:
            row["body"] = json.loads(row["body"])
        return rows


class Handler(BaseHTTPRequestHandler):
    state: DashboardState = None
    static_root: Path = Path(__file__).with_name("static")

    def log_message(self, *_):
        return

    def _allowed_host(self):
        return _host_header_is_loopback(self.headers.get("Host"))

    def _json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _file(self, path: Path):
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._allowed_host():
            return self.send_error(421, "loopback Host required")
        path = urlparse(self.path).path
        if path == "/api/runtime":
            return self._json(self.state.runtime())
        if path == "/api/control-health":
            return self._json(self.state.mission_control_health())
        if path == "/api/candidates":
            return self._json(self.state.candidates())
        if path == "/api/trades":
            return self._json(self.state.recent_trades())
        if path == "/api/review-activity":
            return self._json(self.state.review_activity())
        if path == "/api/decisions":
            return self._json(self.state.decisions())
        if path == "/api/cluster-analysis":
            query = parse_qs(urlparse(self.path).query)
            job_id = (query.get("job_id") or [""])[0]
            job = self.state.cluster_jobs.get(job_id)
            return self._json(job if job is not None else {"error":"CLUSTER_JOB_NOT_FOUND"}, 200 if job is not None else 404)
        if path == "/api/cluster-latest":
            query = parse_qs(urlparse(self.path).query)
            mint = (query.get("mint") or [""])[0]
            try:
                report = self.state.cluster_jobs.latest(mint)
            except ValueError as exc:
                return self._json({"error":str(exc)},400)
            return self._json(report if report is not None else {"error":"CLUSTER_REPORT_NOT_FOUND"}, 200 if report is not None else 404)
        if path in {"/", "/index.html"}:
            return self._file(self.static_root / "index.html")
        if path.startswith("/static/"):
            candidate = (self.static_root / path.removeprefix("/static/")).resolve()
            if self.static_root.resolve() not in candidate.parents:
                return self.send_error(403)
            return self._file(candidate)
        self.send_error(404)


    def do_POST(self):
        if not self._allowed_host():
            return self.send_error(421, "loopback Host required")
        if not _origin_is_loopback(self.headers.get("Origin")):
            return self._json({"error":"CROSS_ORIGIN_POST_FORBIDDEN"},403)
        if not _content_type_is_json(self.headers.get("Content-Type")):
            return self._json({"error":"APPLICATION_JSON_REQUIRED"},415)
        path = urlparse(self.path).path
        if path != "/api/cluster-analysis":
            return self.send_error(404)
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            return self._json({"error":"INVALID_CONTENT_LENGTH"},400)
        if length <= 0 or length > 32768:
            return self._json({"error":"INVALID_REQUEST_SIZE"},400)
        try:
            body = _decode_json_object(self.rfile.read(length))
        except ValueError as exc:
            return self._json({"error":str(exc)},400)
        try:
            job = self.state.cluster_jobs.submit(body.get("mint",""), body.get("preset","standard"))
        except ValueError as exc:
            return self._json({"error":str(exc)},400)
        return self._json(job,202)


class IPv6ThreadingHTTPServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6


def serve(production_root: Path, control_root: Path, host: str = "127.0.0.1", port: int = 8765):
    if host not in {"127.0.0.1", "localhost", "::1"} or not _host_is_loopback(host, port):
        raise ValueError("MISSION_CONTROL_LOCALHOST_ONLY")
    Handler.state = DashboardState(production_root, control_root)
    server_cls = IPv6ThreadingHTTPServer if ":" in host else ThreadingHTTPServer
    server_cls((host, port), Handler).serve_forever()
