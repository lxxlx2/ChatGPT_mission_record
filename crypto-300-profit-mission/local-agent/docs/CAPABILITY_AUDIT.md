# Capability audit — PHASE 0

Date: 2026-09-30 Asia/Bangkok. This document publishes sanitized capability results only. No private runtime payload, Gmail id/body, secret, wallet transaction JSON or operational host identifier is included. Tools were used in this real macOS session; production/reliability gates remain untested.

Status vocabulary: AVAILABLE_VERIFIED means the precisely scoped operation below actually succeeded; AVAILABLE_UNTESTED means a callable/interface exists but the relevant operation was not exercised; UNAVAILABLE means absent in inspected runtime/surface; PERMISSION_REQUIRED means the next meaningful test requires explicit later authorization. Point probes are not uptime/retention/production evidence.

| # | Capability | Status | Actual evidence and limit |
|---|---|---|---|
| 1 | filesystem read/write | AVAILABLE_VERIFIED | Python temporary-file write/separate read/assert passed; design files written/read in worktree |
| 2 | shell | AVAILABLE_VERIFIED | exec_command executed cwd/status/probes with successful exit |
| 3 | Python 3.11+ | AVAILABLE_VERIFIED | system Python 3.14.6 and bundled 3.12.14 launched; production lockfile not built |
| 4 | git | AVAILABLE_VERIFIED | git 2.54.0; fetch and isolated branch/worktree creation passed |
| 5 | GitHub authenticated read | AVAILABLE_VERIFIED | gh api repo returned private=false, default_branch=main, push/admin permission true; authenticated metadata not anonymous page |
| 6 | GitHub authenticated write | AVAILABLE_UNTESTED | repo metadata grants push/admin and connector mutations exist; no remote write probe performed |
| 7 | GitHub branch create/push | AVAILABLE_UNTESTED | local codex branch create verified; remote branch create/push not exercised; docs-only local commit is authorized, push not necessary |
| 8 | network | AVAILABLE_VERIFIED | HTTPS JSON read from all four official API hosts HTTP 200 |
| 9 | Solana public RPC | AVAILABLE_VERIFIED | finalized getSlot HTTP200/no RPC error; target newest signature read and getTransaction finalized/maxSupportedTransactionVersion=1 FETCHED. Four-rank archival gate NOT_RUN |
| 10 | Binance public REST | AVAILABLE_VERIFIED | spot /api/v3/time and futures /fapi/v1/time HTTP200, valid JSON |
| 11 | Binance WebSocket | AVAILABLE_VERIFIED | Node native WebSocket opened spot aggTrade and futures /market/ws/btcusdt@kline_1m; valid first JSON data frames, 168/303 bytes. Not 24h/reconnect test |
| 12 | Hyperliquid API/WebSocket | AVAILABLE_VERIFIED | allMids REST HTTP200 valid JSON, 19,426 bytes; WS subscribe returned JSON frame. First frame can be subscription acknowledgement, sustained HYPE candle data NOT_RUN |
| 13 | Gmail plugin | AVAILABLE_VERIFIED | connector tools present and Sent query succeeded |
| 14 | Gmail Sent search | AVAILABLE_VERIFIED | in:sent max_results=1 returned one real SENT-labelled mail; exact event-token search/delay/concurrency NOT_RUN |
| 15 | Gmail readback | AVAILABLE_VERIFIED | returned mail read_email succeeded with structured content; no content/id copied into Git |
| 16 | Gmail send action | AVAILABLE_UNTESTED | send_email/send_draft callable inventory present; not invoked; real canary requires explicit user authorization |
| 17 | ChatGPT automation management | UNAVAILABLE | desktop automation_update exists for local cron/heartbeat; it is not evidence of ChatGPT scheduled-task list/manage capability. Requested cloud tasks absent from local automation inventory; no matching cloud management tool found |
| 18 | macOS Keychain CLI/access | AVAILABLE_UNTESTED | security CLI and user keychain enumeration succeeded; secret add/read/access in selected launch context not tested, so aggregate credential capability unverified |
| 19 | launchctl | AVAILABLE_VERIFIED | launchctl print gui/<uid> succeeded; no install/bootstrap/kill/reboot test |
| 20 | pmset | AVAILABLE_VERIFIED | pmset -g read succeeded: sleep=0, standby=1, hibernatemode=3; no setting changed; closed lid/reboot not proven |
| 21 | SQLite | AVAILABLE_VERIFIED | sqlite3 3.54.0; Python in-memory create/insert/commit/separate SELECT assertion PASS; WAL/disk durability not tested |
| 22 | pytest | UNAVAILABLE | python3 -m pytest failed No module named pytest; bundled Python import probe also absent. No install performed |
| 23 | curl | AVAILABLE_VERIFIED | curl 8.7.1 --version executed; HTTPS API probes used Python urllib |
| 24 | websocket client | AVAILABLE_VERIFIED | bundled Node native WebSocket executed real connections; Python websocket/websockets absent in both checked runtimes |

## Reproducible probe scope

Read-only shell: git fetch origin; git status --short; git branch --show-current; git remote -v; gh api repos/lxxlx2/ChatGPT_mission_record with filtered metadata; python3 --version; git --version; curl --version; sqlite3 :memory: version; python3 -m pytest --version; command -v security launchctl pmset; security list-keychains -d user; launchctl print gui/<uid> (output discarded); pmset -g. No credential dumps or environment listing.

Network: bounded HTTPS requests timeout=15s. Solana getSlot(finalized), then getSignaturesForAddress target limit=1(finalized), then getTransaction for returned newest signature with encoding=json/finalized/maxSupportedTransactionVersion=1. No alternate RPC or full pagination. Binance GET spot/futures time. Hyperliquid POST info type=allMids. WebSocket clients timeout=15s, close after first JSON frame; futures path read from current official migration docs. No collector daemon/ongoing subscription started.

Gmail: search_emails(in:sent,max_results=1), read_email of returned id. Response successful; audit only records presence and SENT label. Send not tested. No message sent/draft created. No automation mutation attempted.

## Environment / repository audit

Primary checkout was codex/x-revenue-vertical-slice with existing modified/untracked X-revenue artifacts. Preserved unchanged; no stash/reset/clean. Fetched origin/main at 1334234, then isolated local worktree /Users/jerson/Documents/ChatGPT/crypto-monitor-design-20260930, branch codex/crypto-monitor-design-20260930. Repository metadata currently PUBLIC. No AGENTS.md found in inspected project paths. This commit adds design documents only, no collector or dependency installation.

Canonical fully read: root MAC_MONITOR_HANDOFF_REVIEWED.md (64 lines), MAC_MONITOR_FEASIBILITY_HANDOFF.md (985), MISSION_SPEC.md (333), AUTOMATION_RUNTIME.md (870), token_trading_principles.md (564), meme_trading_principles.md (426). Root and mission README read. Initial concatenated output truncated; canonical files subsequently read in smaller ranges.

Directory inventory at baseline: state 13 files, watchlists 13, tests 8, tools 4, reports 3, research 3, portfolio 1, positions 12. Representative contents inspected: latest/hourly bundle/Frank checkpoint, NFT/Monster models, priority regression/Frank acceptance, replay methodology/first-pass report, latest Monster report, portfolio/current and position authorities/README, tools README. tests currently Markdown acceptance/smoke reports, not the new Python automated suite. tools/technocore-close-call is a separate execution helper, not a monitor collector; it was not executed. Frank compact checkpoint reports 180/7,106, while first-pass replay explicitly says incomplete; no full replay PASS claimed. Rolling hourly bundle is bootstrap/non-authoritative for completed cycle. Legacy public tree contains user asset snapshots and historical Gmail identifiers; this design does not reproduce or delete them. Future private runtime must not extend that exposure.

## Resource evidence and limits

Measured only audit baseline: shell process instantaneous CPU 0.0%, RSS 2,896KiB; mission directory allocated 1,456KiB; volume 48% used with 496,816,372KiB available. These are real snapshots but not collector averages. Network response bytes recorded above, not bytes/day. A separate read-only HYPE candleSnapshot request spanning31days returned HTTP 200, 5,220 1m rows covering 3.624 days. Official docs say latest 5,000; the observed response is slightly larger, so do not assume an exact cap. Both document and actual coverage are far below 30 days. No raw response saved to public Git. New runtime SQLite size, events/day and GitHub writes/day have no implementation to measure; NOT_RUN. CPU<10% / RSS<500MB / 2GB budget gate remains NOT_RUN. PHASE 1 benchmark measures synthetic workload, collector aggregates later; no theory-derived PASS.

## Missing tests and feasibility

Authenticated remote write/create/push, private test-repo access, scheduled GPT branch reads/CAS receipts, real Gmail send/readback/delay, credential access, launchd lifecycle, reboot/FileVault/closed-lid, 24h WS, Frank four-rank archive and Monster retention probes NOT_RUN. Avoid disruptive remote write just to mark a box verified. HYPE official candleSnapshot documented recent 5,000 limit means current official 1m-only 30d retrospective gate NOT_FEASIBLE; preserve gate through forward accumulation/approved source. Newest Frank fetch is not proof of oldest 7,106 availability.

Local docs commit does not prove GitHub authenticated write or branch push. No push performed. Architecture CONDITIONAL_GO for design; production NO_GO until acceptance/blockers clear. Audit statuses must be re-probed in the actual scheduled/deployment context, not inherited from this interactive Codex session.

## Cross-document design review evidence

Manual review checked authority precedence, local-vs-GPT enums, public/private separation, SQLite/cursor atomicity, immutable batches, TTL-vs-durability, exact-set receipts, Gmail uncertainty/policy, stage prerequisites and four open owner decisions. Source-specific history limits remain blockers, not waivers. Script verification: five canonical docs;71 unique testcase records each with all ten required fields; all explicit acceptance TEST_ID references resolve. Staged git diff --check passed. This is structural/design consistency review, not independent design approval or runtime test PASS. Only six Markdown additions staged (five docs plus compatibility pointer). No push/send/automation/system install or legacy-state edit.
