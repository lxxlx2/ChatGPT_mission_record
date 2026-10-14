# Frank F02-R2 Mac isolated real-browser acceptance

Updated: 2026-10-15 Asia/Bangkok. Stage: `READY_FOR_USER_MAC_BROWSER_EXECUTION`, **not yet executed in user's browser**, production `NO_GO`.

## Frozen identity and external acceptance

- [Approved fixed-SHA F02-R2 TTL repair Draft PR #65](https://github.com/lxxlx2/ChatGPT_mission_record/pull/65): `a59e423304cb2081aef359c0649245c7e1d05b48`, base old rejected #64 `13a2594e222f8425239f39b71170d35aadb4d47c`. **External other-AI limited verdict `APPROVE`**, including *real* browser no-interaction 5s crossing, naturally elapsed standard 300s, Chrome background return, actual localhost HTTP and Node supplemental tests. [User-forwarded reviewer findings archived in PR #65](https://github.com/lxxlx2/ChatGPT_mission_record/pull/65#issuecomment-6179551424).
- Confirmed exact [CI #38643786913](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38643786913) SUCCESS: F02/A05 78 targeted, local-agent full 1,633; joint F01/C02/A05/F02 112 targeted and 1,685 all; virtual Node TTL and browser interactions pass. The external reviewer reported its first two independent full runs had 3 `REQUIRED_REAL_FRANK_EVIDENCE_REF_NOT_FETCHED` failures from missing historical Git references; subsequently obtained evidence and reran to green **without source modifications**. Do not hide failed setup attempts.
- User previously **approved** creating a distinct research-only Sidecar and ran it **once**, Mac stdout `SOURCE_REPLAY=PASS`, `ISOLATED_SIDECAR_IMPORT=PASS`, `F02_MAC_PROBE=PASS`; age 7397s, all 32 `SOURCE_UNAVAILABLE`, slots 456895319/456895320. Existing **private research-only SQLite**: `$HOME/.local/share/frank-f02-research/owner-456895319-456895320.sqlite`. **Never rerun the import** and never alter that file for browser QA. Original archive-only wire bundle: `$HOME/.local/share/frank-owner-full-rpc-evidence/owner-f537013b8a094e608cf9657622b627d6`. Frozen source SHA `a91fed6fae63f51557ab88fb9ae892247cc32deccd26c631d765ff27aff03261`.
- A05-R2 verified archived target snapshot on 2026-10-14 22:54 Asia/Bangkok: 9 positive /23 zero among frozen 32. This **does not mean current holdings**; F02 API after TTL correctly masks all 32 as unavailable. A "current 9 holdings" panel in F02-R2 would be a defect.

## User-executed isolated Mac browser test

In a *single* Mac zsh terminal, run this entire command. It clones **separate frozen-reviewed code** under `~/.local/share/frank-f02-r2-review`, checks the immutable SHA, refuses to overwrite/reimport Sidecar, refuses if localhost:18765 is already listening, starts ONLY a temporary research HTTP listener bound to `127.0.0.1`, makes same-origin requests and opens the page in the user's default browser. Press Enter after inspecting it: the shell trap stops its **own** temporary HTTP process; it does not change/stop any production Frank listener. Git clone/fetch uses GitHub, **no fresh Solana RPC is requested**.

```zsh
(
set -e
set -o pipefail
umask 077
repo="$HOME/.local/share/frank-f02-r2-review"
bundle="$HOME/.local/share/frank-owner-full-rpc-evidence/owner-f537013b8a094e608cf9657622b627d6"
sidecar="$HOME/.local/share/frank-f02-research/owner-456895319-456895320.sqlite"
pin="a59e423304cb2081aef359c0649245c7e1d05b48"
if [ ! -d "$repo/.git" ]; then
  git clone --filter=blob:none --single-branch --branch fix/frank-f02-r2-ttl-live-expiry-20261015 https://github.com/lxxlx2/ChatGPT_mission_record.git "$repo"
else
  git -C "$repo" fetch origin fix/frank-f02-r2-ttl-live-expiry-20261015
fi
git -C "$repo" checkout --detach "$pin"
test "$(git -C "$repo" rev-parse HEAD)" = "$pin"
test -f "$bundle/manifest.json"
test -f "$sidecar"
test ! -L "$sidecar"
if lsof -nP -iTCP:18765 -sTCP:LISTEN | grep -q .; then
  echo "F02_R2_PORT_OCCUPIED_NO_ACTION"
  exit 1
fi
cd "$repo/crypto-300-profit-mission/local-agent"
python3 -m scripts.frank_f02_readonly_positions_api --person-id frank --bundle "$bundle" --sidecar "$sidecar" --max-age-seconds 300 --serve --port 18765 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true' EXIT
ready=0
for i in {1..40}; do
  if ! kill -0 "$server_pid" 2>/dev/null; then
    echo "F02_R2_SERVER_START_FAILED"
    exit 1
  fi
  if curl -fsS -o /dev/null http://127.0.0.1:18765/research/positions; then
    ready=1
    break
  fi
  sleep 0.25
done
test "$ready" = 1
python3 - <<'PY'
import json
from urllib.request import urlopen
base = "http://127.0.0.1:18765"
with urlopen(base + "/api/research/positions", timeout=10) as res:
    assert res.status == 200
    data = json.load(res)
assert data["target_mint_count"] == 32, data["target_mint_count"]
assert data["verified_full_wire_capture_sha256"] == "a91fed6fae63f51557ab88fb9ae892247cc32deccd26c631d765ff27aff03261"
assert data["latest_capture_sha256"] == data["verified_full_wire_capture_sha256"]
assert data["readiness"] == "STALE_ARCHIVED_SOURCE", data["readiness"]
assert data["state_counts"] == {"SOURCE_UNAVAILABLE": 32}, data["state_counts"]
assert all(x["state"] == "SOURCE_UNAVAILABLE" and x["observed_raw_amount"] is None and x["observed_quantity"] is None for x in data["mints"])
for endpoint, expect in (("/research/positions", b'id="position-rows"'), ("/research/positions.js", b'localSourceExpired'), ("/research/positions.css", b'.stats')):
    with urlopen(base + endpoint, timeout=10) as res:
        payload = res.read()
        assert res.status == 200 and res.headers.get("Cache-Control") == "no-store"
        assert expect in payload, endpoint
print(json.dumps({"F02_R2_MAC_LOCAL_HTTP": "PASS", "readiness": data["readiness"], "target_mint_count": 32, "state_counts": data["state_counts"], "capture_age_seconds": data["capture_age_seconds"], "slot_min": data["slot_min"], "slot_max": data["slot_max"]}, ensure_ascii=False))
PY
open http://127.0.0.1:18765/research/positions
echo "F02_R2_BROWSER_OPENED=http://127.0.0.1:18765/research/positions"
read -r "done_check?浏览器检查完成后按回车结束临时只读服务："
)
```

**Browser steps, actual human verification** (after local HTTP script prints PASS): page says **来源已过期**, 32 targets, **非零 0 / 已观察零余额 0 / 来源不可用 32**, all quantity and token account numbers displayed as **—**; source is archived and age>300s, original SHA prefix and slots visible; the registered wallet matches replayed source; copy CA succeeds, search exact frozen target filters, and changing status filter to `来源不可用` shows 32, to `已核实非零` shows no eligible rows. The page `重新读取本地档案` must not create fresh positions. Capture a screenshot if willing (do not publish full private raw RPC bundle). Press Enter in terminal to stop the temporary F02 listener. **Do not confuse shell HTTP PASS with browser-interaction PASS**; Mac browser acceptance only when user reports real UI behavior or evidence.

## What is still pending

- Independent review `APPROVE` on PR #65 code is complete. This user Mac browser check is **not yet evidenced**.
- This archived-source Mac acceptance tests the honest stale path, source metadata and browser actionability. It cannot independently prove a fresh real Frank current balance or verified USD/PnL. New current real source requires separately user-initiated complete dual program original-wire RPC collection, source replay and explicit new research Sidecar import; do not reuse the old Sidecar import command.
- F02-R3 Mac cross-module acceptance and final independent integration/system reviews remain separate gates. Source meta exact UTC tie remains API P3 with UI fail-closed; age text not continuously ticking and detailed per-token account listing are **nonblocking** UX P3 and must not prevent current business flow.

`NO_MERGE / NO_DEPLOY / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_NEW_RPC_AUTO / NO_NEW_AUTOMATION`.


## 2026-10-15 actual user Mac screenshots + terminal — archived stale view visually accepted; live query not in scope

- User Mac successfully cloned immutable reviewed PR #65 `a59e423304cb2081aef359c0649245c7e1d05b48`; launched temporary loopback-only F02 HTTP listener and returned `F02_R2_MAC_LOCAL_HTTP=PASS` from same-origin real request. Actual `readiness=STALE_ARCHIVED_SOURCE`, 32 `SOURCE_UNAVAILABLE`, age **22605s**, exact existing SHA and prior 2026-10-14 non-atomic slot archive. A transient first `curl(7)` before `LOCAL_RESEARCH_HTTP_READY` is a normal startup race handled by script's bounded wait. Exit/status of the temporary process not supplied.
- Actual Safari screenshots show authenticated-looking exact registered `frank·PRIMARY` research identity, source age/TTL and historical hash/slots, correct 32/0/0/32 status grid, frozen rows 1–32 with visible `来源不可用` and `—` for amounts/account counts; real page layout and fixed CA utilities visibly rendered. No screenshot of actual search typed, filtered result or clipboard content; classify **visual+HTTP stale-path PASS**, **search/filter/copy on user's Mac NOT VERIFIED**. No fresh balance confirmation.
- Search on this page means **filter already fetched 32 Mints by text**, not an arbitrary contract scan; the `重新读取本地档案` button only rereads an existing 300s-TTL research Sidecar; it does not query Solana. True current owner account lookups require new complete original owner RPC evidence, offline replay/32-Mint reconciliation and a separate explicitly approved research Sidecar update path. Generic arbitrary CA diligence is separately covered by C01/C02 `CA 链上查询` in the existing control dashboard. These two requirements cannot be scored as done based on this research page alone.
- Next acceptance: user may separately test Mint filter/clipboard if needed; do not block entire research stale-path proof on missing screenshot of a filter. For F02-R3 product acceptance prioritize **fresh manual source pipeline and the existing actual CA research workflow** so final interface genuinely facilitates trading decisions, rather than polishing age text or adding speculative repeated edge fixes. No new automatic collector, prod write, Gmail, trades, deploy, merge or automation.
