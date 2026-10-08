#!/bin/bash
set -euo pipefail

WORKTREE="${WORKTREE:-/Users/jerson/Documents/ChatGPT/frank-meme-ca-v3}"
LOCAL_AGENT="${LOCAL_AGENT:-$WORKTREE/crypto-300-profit-mission/local-agent}"
PROD="${PROD:-/Users/jerson/Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1}"
VENV="${VENV:-$HOME/.venvs/frank-meme-review}"
PY="$VENV/bin/python"
APP_SUPPORT="${APP_SUPPORT:-$HOME/Library/Application Support/FrankMeme}"
RPC_FILE="$APP_SUPPORT/solana_rpc_urls"
PORT="${PORT:-8877}"
CONTROL="${CONTROL:-$HOME/.frank_meme_ca_v3_accept_$(date +%Y%m%d_%H%M%S)}"

RACE="RACEyWiM2ztEZcJx2AHXU2eWjhxU57x3vXn92b39dLD"
FRANK_TOKEN2022="3Dgwn5E7H5a8k6iGrz3qirkaJqUaJrKHEZ2xPcLRpump"
FRANK_CLASSIC_SPL="2AVjqmGbMqg7rSyHVv2deVdggsBgBtu1Bi69BUvE5WRv"

die(){ echo "ERROR: $*" >&2; exit 1; }

[ -d "$LOCAL_AGENT" ] || die "LOCAL_AGENT_NOT_FOUND"
[ -f "$PROD/forward.sqlite" ] || die "PRODUCTION_DB_NOT_FOUND"
[ -f "$PROD/health.json" ] || die "PRODUCTION_HEALTH_NOT_FOUND"

# Hash the original DB, health and LaunchAgent definitions before starting the
# isolated acceptance. A concurrent production write is a FAIL, never "untouched".
LOOP_PLIST="$HOME/Library/LaunchAgents/com.$(id -un).frank-meme.loop.plist"
DASH_PLIST="$HOME/Library/LaunchAgents/com.$(id -un).frank-meme.dashboard.plist"
integrity_snapshot() {
  local file
  for file in "$PROD/forward.sqlite" "$PROD/health.json" "$LOOP_PLIST" "$DASH_PLIST"; do
    if [ -f "$file" ]; then
      shasum -a 256 "$file"
    else
      printf 'MISSING %s\n' "$file"
    fi
  done
}
INTEGRITY_BEFORE="$(integrity_snapshot)"
[ -x "$PY" ] || die "VENV_PYTHON_NOT_FOUND"
[ -s "$RPC_FILE" ] || die "AUTHENTICATED_SOLANA_RPC_NOT_CONFIGURED"

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  die "PORT_IN_USE:$PORT"
fi

mkdir -m 700 "$CONTROL"
SOLANA_RPC_URLS="$(cat "$RPC_FILE")"
[ -n "$SOLANA_RPC_URLS" ] || die "AUTHENTICATED_SOLANA_RPC_EMPTY"
export SOLANA_RPC_URLS

echo "===== ISOLATED REAL-CA ACCEPTANCE ====="
echo "Worktree: $WORKTREE"
echo "Control root: $CONTROL"
echo "Port: $PORT"
echo "Authenticated Solana RPC: CONFIGURED (secret not printed)"
echo "Mission Meme loop: NOT STARTED"
echo "Live delivery: OFF"
echo "LaunchAgents: UNTOUCHED"

cd "$LOCAL_AGENT"

nohup env PYTHONPATH=. "$PY" scripts/mission_meme_v1.py serve \
  --production-root "$PROD" \
  --control-root "$CONTROL" \
  --host 127.0.0.1 \
  --port "$PORT" \
  >"$CONTROL/server.log" 2>&1 &

SERVER_PID=$!
printf '%s\n' "$SERVER_PID" > "$CONTROL/server.pid"

cleanup(){
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

READY=0
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:$PORT/" >/dev/null 2>&1; then READY=1; break; fi
  sleep 1
done
[ "$READY" = "1" ] || { cat "$CONTROL/server.log"; die "DASHBOARD_START_FAILED"; }

LISTEN="$(lsof -nP -a -p "$SERVER_PID" -iTCP -sTCP:LISTEN 2>/dev/null || true)"
echo "$LISTEN" | grep -q "127.0.0.1:$PORT" || die "DASHBOARD_NOT_LOOPBACK_BOUND"
echo "Dashboard HTTP / loopback binding: PASS"

BASE="http://127.0.0.1:$PORT" CONTROL="$CONTROL" \
RACE="$RACE" FRANK_TOKEN2022="$FRANK_TOKEN2022" FRANK_CLASSIC_SPL="$FRANK_CLASSIC_SPL" \
"$PY" - <<'PY'
import json,os,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path

BASE=os.environ["BASE"]
CONTROL=Path(os.environ["CONTROL"])
cases=[
    ("RACE_TOKEN2022",os.environ["RACE"],"SPL Token-2022",False),
    ("FRANK_TOKEN2022",os.environ["FRANK_TOKEN2022"],"SPL Token-2022",True),
    ("FRANK_CLASSIC_SPL",os.environ["FRANK_CLASSIC_SPL"],"SPL Token",True),
]

def get_json(path):
    req=urllib.request.Request(BASE+path,headers={"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)

def post_json(path,payload):
    req=urllib.request.Request(
        BASE+path,data=json.dumps(payload).encode(),method="POST",
        headers={"Content-Type":"application/json","Accept":"application/json","Origin":BASE},
    )
    with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)

try:
    post_json("/api/cluster-analysis",{"mint":"not-a-valid-solana-ca","preset":"standard"})
    raise AssertionError("INVALID_CA_WAS_ACCEPTED")
except urllib.error.HTTPError as exc:
    assert exc.code==400
print("invalid CA -> HTTP 400: PASS")

summaries=[]
for name,mint,expected_program,require_frank in cases:
    print("\n=====",name,"=====")
    job=post_json("/api/cluster-analysis",{"mint":mint,"preset":"standard"})
    job_id=job["job_id"];deadline=time.time()+1800;last=None
    while True:
        state=get_json("/api/cluster-analysis?"+urllib.parse.urlencode({"job_id":job_id}))
        stage=(state.get("progress") or {}).get("stage")
        if stage!=last:
            print("progress:",stage,json.dumps(state.get("progress") or {},ensure_ascii=False,sort_keys=True))
            last=stage
        if state.get("status")=="DONE":break
        if state.get("status")=="ERROR":
            raise RuntimeError(name+" JOB_ERROR: "+json.dumps(state.get("error"),ensure_ascii=False))
        if time.time()>deadline:raise TimeoutError(name+" ACCEPTANCE_TIMEOUT")
        time.sleep(2)

    report=get_json("/api/cluster-latest?"+urllib.parse.urlencode({"mint":mint}))
    profile=report.get("token_profile") or {}
    assessment=report.get("assessment") or {}
    coverage=report.get("coverage") or {}
    frank=report.get("frank") or {}
    execution=report.get("execution_quote_30_usdc") or {}

    assert report.get("schema_version")==2
    assert report.get("mint")==mint
    assert report.get("source")=="SOLANA_FINALIZED_JSON_RPC"
    assert profile.get("status")=="OK",profile
    assert profile.get("token_program")==expected_program,(name,profile.get("token_program"),expected_program)
    assert assessment.get("chain_permission_status") in {"PASS","RISK","UNRESOLVED"}
    assert assessment.get("cluster_status") in {
        "NO_MATERIAL_CONTROL_CLUSTER_FOUND","PROBABLE_CONTROL_CLUSTER_PRESENT","WALLET_CLUSTER_UNRESOLVED",
    }
    for detail in profile.get("sensitive_extension_details") or []:
        assert detail.get("status") in {"ACTIVE_RISK","INACTIVE","UNRESOLVED"},detail
    if require_frank:
        assert frank.get("status")=="OBSERVED",frank
        assert frank.get("person_id")=="frank",frank
        assert frank.get("mint")==mint,frank
    elif frank.get("status")=="OBSERVED":
        assert frank.get("person_id")=="frank",frank

    history=report.get("assessment_history")
    assert isinstance(history,list) and history
    report_dir=CONTROL/"cluster-reports"/mint
    assert (report_dir/"latest.json").is_file()
    assert list(report_dir.glob("*.md"))
    assert execution.get("status") in {"OK","UNAVAILABLE"},execution

    summaries.append({
        "case":name,"mint":mint,"token_program":profile.get("token_program"),
        "chain_permission_status":assessment.get("chain_permission_status"),
        "cluster_status":assessment.get("cluster_status"),
        "trading_status":assessment.get("trading_status"),
        "scan_mode":coverage.get("scan_mode"),
        "deep_holders_scanned":coverage.get("deep_holders_scanned"),
        "adaptive_deepened_count":len(coverage.get("adaptive_deepened_owners") or []),
        "frank_status":frank.get("status"),"frank_person_id":frank.get("person_id"),
        "frank_buy_count":frank.get("buy_count"),"frank_sell_count":frank.get("sell_count"),
        "execution_quote_status":execution.get("status"),
        "assessment_history_count":len(history),
    })

print("\n===== REAL-CA SUMMARY =====")
print(json.dumps(summaries,ensure_ascii=False,indent=2))
print("REAL_CA_SCHEMA_AND_SEMANTICS: PASS")
PY

[ ! -e "$CONTROL/mission-control.sqlite" ] || die "MISSION_CONTROL_DB_CREATED"
[ ! -e "$CONTROL/sol-normalized-v1.sqlite" ] || die "SOL_MIRROR_DB_CREATED"
INTEGRITY_AFTER="$(integrity_snapshot)"
[ "$INTEGRITY_BEFORE" = "$INTEGRITY_AFTER" ] || die "PRODUCTION_DB_HEALTH_OR_LAUNCHAGENT_INTEGRITY_CHANGED"
echo "Production DB / health.json / LaunchAgent plist before-after SHA256: PASS"

echo
echo "===== ACCEPTANCE RESULT ====="
echo "ISOLATED_REAL_CA_ACCEPTANCE: PASS"
echo "No Mission Control decision DB: PASS"
echo "No SOL-normalized sidecar: PASS"
echo "Production files unchanged during this acceptance: VERIFIED_BY_SHA256"
echo "No migration/backfill function invoked by this acceptance script"
echo "No Mission Control loop or delivery runner invoked by this acceptance script"
echo "LaunchAgent plists unchanged: VERIFIED_BY_SHA256"
echo "PRODUCTION_TRADING: NO_GO"
echo "Artifacts: $CONTROL"
