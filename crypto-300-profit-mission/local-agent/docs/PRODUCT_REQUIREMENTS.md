# Crypto Opportunity Monitor — Product requirements

Design baseline: 2026-09-30 Asia/Bangkok. Status: APPROVED_FOR_PHASE_1_ONLY. This is a specification, not implementation or operational evidence.

## Authority and compatibility

Current user handoff (2026-09-30) > root MAC_MONITOR_HANDOFF_REVIEWED.md > reviewed v2 addendum in MAC_MONITOR_FEASIBILITY_HANDOFF.md > MISSION_SPEC.md > AUTOMATION_RUNTIME.md > token/meme principles. New design applies only to runtime-v2. Legacy files and automation prompts remain unchanged. The user has resolved hourly judgement acceptance, official-only Solana, private transport direction, and limited NFT discovery; do not ask these again.

Legacy conflicts are explicit: Alchemy primary/backup is prohibited in the new Frank collector; legacy WATCH/19:29 daily-summary delivery does not authorize runtime-v2 mail; only final GPT ACTION enters mail. Legacy runtime single-file write restrictions are observed scheduler limitations to test in PHASE 2, not evidence that new private transport works. Legacy portfolio display thresholds conflict ($0.10 vs $1); this refactor does not reconcile or modify portfolio. Legacy trading principles constrain GPT research quality and evidence provenance, not permission for local semantic classification or automated trades.

## User goal and business problem

Continuously find potential profitable opportunities on the user's Mac, retain facts durably, and let GPT make the final investment judgement. Send Gmail only when the judgement requires user action. Profit or reaching the historical $3,000 Mission objective is not an engineering acceptance metric or promised outcome.

The scheduled runtime previously combined raw collection, transaction ETL, state, reasoning, persistence and delivery. Reviewed history reports approximately 8KB transaction connector truncation, missing scheduled completion, deferred Monster starvation and send/receipt gaps. Those incidents motivate separation; they were not reproduced in this design audit.

## Responsibilities and non-goals

| Component | Responsibility | Boundary |
|---|---|---|
| Mac | eyes + memory + deterministic ETL; timestamps, indicators, factual authorities/deltas, dedup, RAW_CANDIDATE, health, cursors, retry | No BUY/SELL/LONG/SHORT, IGNITION/EXHAUSTION, FORMAL_ENTRY/FORMAL_EXIT, ACTIONABLE_RISK/OPPORTUNITY or worth-buying conclusions |
| SQLite | sole authoritative local event, queue, cursor, reconciliation and delivery mirror | GitHub success does not erase an event |
| GitHub | compact transport and audit in a separate PRIVATE runtime repository | no raw ticks/HTML/transaction archives; no primary queue |
| GPT | sole final semantic/investment judge; IGNORE/WATCH/ACTIONABLE_RISK/ACTIONABLE_OPPORTUNITY, optional bounded verification | never generates or rewrites event_id; no bulk raw ETL |
| Gmail | ACTION delivery, Sent search and readback | no WATCH, infrastructure-health or historical per-token mail; no exactly-once promise |

Non-goals: auto trading, portfolio/order mutation, a local investment AI, paid/API GPT trigger added for latency, Solana fallback, full free X firehose, collectors while Mac is asleep/off, guaranteed upstream/scheduler SLA. Existing protected state/history/tools remain intact.

## Scope

CORE PRICE: BTC/ETH/SOL/BNB Binance official spot USDT prices; HYPE official Hyperliquid perpetual mid/candle series (market type and reference explicitly labeled; not interchangeable with spot). These are technical v1 reference choices for review. Futures Monster uses its own market namespace. Completed UTC 1m OHLCV is canonical for features; ticks/current bars are provisional and cannot trigger v1.

Frozen v1 prefilters: 15m absolute return >=3%; 1h >=5%; 4h >=8%; 24h >=12%; 15m reversal >=4%; breakout beyond prior 24h high/low >=1% for two completed samples; 5m realized volatility >=3x trailing same-scale 24h median AND absolute 5m return >=2%; non-BTC return difference against BTC >=4 percentage points/1h or >=6 percentage points/4h. All yield RAW_PRICE_CANDIDATE only. Freeze formula and threshold manifest before replay; any revision gets new price_rule_version and a complete replay.

Frank: target 498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ; exclusively https://api.mainnet.solana.com; finalized; getTransaction maxSupportedTransactionVersion=1. Local emits signer/fee-payer/token-owner/authority accounts/inner-instruction evidence/programs/pre/post SOL and tokens/deltas/error/slot/block_time/signature. GPT interprets swap/passive/HFT/entry/exit. Archive/live jobs isolated. Newest/25th-age-percentile/median/oldest target probe precedes consecutive 500; 500 precedes 7,106 replay. Missing oldest required transaction proves FULL_HISTORY_NOT_FEASIBLE_WITH_PUBLIC_RPC_ONLY. Timeouts/429 alone establish temporary inability, not missing archival history.

Monster: lightweight entire active Binance futures universe, in-memory rolling state, compact 5m snapshots; deep fetch klines/OI/funding/taker/top-trader only for candidates. Durable deferred fairness; local only RAW_MONSTER_CANDIDATE. GPT owns frozen V2.1 STRUCTURAL/PRESSURE/IGNITION/EXHAUSTION. D1 price/volume recall, D2 forward derivatives preservation, D3 full model evaluation; unavailable history and delisted symbols are explicit coverage/survivor-bias gaps.

NFT: configured known creator/project/mint/contract sources. REQUIRED_DETERMINISTIC alone enters hard health gate; BEST_EFFORT and DISCOVERY_ONLY feed coverage gaps. Local extracts page hash/diff, supply/price/mint count/velocity and bounded untrusted excerpts. GPT verifies identity, participation path, risk and value; no capture is never evidence of no opportunity. Existing third-party scanners/X are not automatically REQUIRED.

## SLOs and success criteria

| Class | Target under normal awake/network/source availability | Evidence |
|---|---|---|
| Collection | BTC/ETH/SOL/BNB quote age <10s; HYPE <15s; candidate durable write <=5s after eligible completed bar observation | source timestamps + monotonic latency histogram |
| Collection | Frank signature discovery p95 <=30s, evidence p95 <=60s, cursor gap=0 | known-event timings and contiguous ledger |
| Collection | Monster universe age <=60s, candidate latency <=120s; required NFT source success >=95% rolling 24h | coverage/freshness logs |
| Transport | sync p95 <=60s, no unsynced event older than 5min in normal availability | outbox/receipt timestamps |
| Decision | hourly nominal consumer; next successful cycle target; worst case close to 1h in nominal operation accepted by user | cycle inventory and valid receipts |
| Delivery | engineering target p95 <=5min after committed ACTION while provider/runtime available, subject to canary validation and chosen policy | ACTION/send/readback timestamps |
| Shadow | >=48h, >=95% scheduled success, silent loss=0, missed-cycle recovery=100%, oldest pending <=2 nominal cycles; no backlog growth >2 consecutive cycles | acceptance report |

Collection freshness <10s is NOT a 10-second GPT/mail SLA. Scheduling jitter, missed cycles, backlog, or uncertain send can extend nominal one-hour judgement/delivery; expose measured delays, never guarantee an upper bound from hourly schedule alone. Unknown metrics do not pass. Delivery p95 is a proposed target, not an already accepted or measured product guarantee.

Every batch <=100,000 UTF-8 bytes; every complete candidate item <=2,000 bytes; <=40 normal items plus urgent within total byte bound. All deferred items remain queued. Resource development targets aggregate average CPU <10% of one logical core, aggregate RSS <500MB, confirmed total local storage budget 5GB. Budget accounts for DB/WAL/raw/logs/backups; >80% DEGRADED_DISK, >95% UNHEALTHY_DISK. Actual measurements required before production.

## Privacy and confirmed decisions

Public lxxlx2/ChatGPT_mission_record holds code/design/rules/tests/non-sensitive reports only. No new runtime wallet activity, queue, Gmail id, delivery/private-health state, sensitive asset data or archive is written there. Existing historical exposure is recorded for owner review; neither copying nor deleting it is authorized here. Configure MISSION_RUNTIME_REPO and verify private visibility before every transport session; unset/public/unverified destination forces LOCAL_ONLY/DRY_RUN. Private repo is not automatically created; visibility unchanged. Secrets never enter either Git repository. Private receipts may contain minimum provider ids; public reports redact them.

Keep enabled: 美股每日晨报, Crypto 每日情报, 全项目空投与TGE监控. Keep disabled: $300 Crypto资产状态监控, Frank 30D 全量回测. No create/rename/enable/disable actions in this round. Current desired configuration is authoritative user instruction; live ChatGPT scheduler state has not been independently verified by the desktop automation API.

## Confirmed product decisions — PHASE 1 approval

Status: APPROVED_FOR_PHASE_1_ONLY, not PRODUCTION_READY. User design review approved synthetic local E2E only.

- Gmail policy: AT_LEAST_ONCE (config value `at_least_once`). Stable id, lease/fencing, Sent lookup, immediate provider id persistence, readback, cooldown and DELIVERY_UNCERTAIN remain mandatory; no blind resend. Retry horizon is not implicitly approved. PHASE 1 uses mock only, real send OFF.
- Future runtime target: `lxxlx2/crypto-monitor-runtime`, required PRIVATE; no automatic creation or runtime push in PHASE 1. Public code/design branch push is authorized; main merge is not.
- Host policy: post-login LaunchAgent recovery accepted. Continuous collection applies only while powered on, logged in, network available and not asleep. Shutdown, prelogin, sleep or lid-induced sleep are explicit health gaps. No LaunchDaemon/pre-FileVault recovery requirement for v1; no launchd install now.
- Total local budget: 5 GB (5,000,000,000 bytes), DB/WAL/raw/transport/logs/backups included. Usage >80% DEGRADED_DISK, >95% UNHEALTHY_DISK. Retention, compression, cleanup and measured sizes required; unresolved items cannot be silently removed.
- HYPE official-only gate: B-HYPE-1 replays all available official 1m history; B-HYPE-2 saves canonical 1m bars from later local collector shadow; B-HYPE-3 automatically repeats complete 30d replay once enough completed history plus warm-up exists. Until then FORWARD_DATA_ACCUMULATING, never 30D_REPLAY_PASS. No third-party history. This accepted partial-history boundary does not block PHASE 1, the other four assets'30d replay, or HYPE live shadow.

These four former OPEN_PRODUCT_DECISION entries are closed. Capability, integration/canary, deployment and other phase gates remain separate blockers. Stop after PHASE 1 for review; no PHASE 2 authorization.

Production additionally requires verified private scheduler transport/write/fencing, source gates, resource results, real Gmail canary authorization and deployment authorization.

## NOT_FEASIBLE and unresolved feasibility

NOT_FEASIBLE: <=5min GPT final judgement with current hourly free consumer; free reliable full X firehose; local collection during host sleep/power-off; strict exactly-once Gmail without provider idempotency.

HYPE 30-day 1m replay via current official candleSnapshot alone is NOT_FEASIBLE: official API retains only latest 5,000 candles, whereas 30d requires 43,200 (+warm-up). Approved HYPE gates B-HYPE-1/2/3 below replace the retrospective full30d prerequisite; use official history only, then forward accumulation. Never substitute 5m bars, third-party history or fabricated history.

Frank full-history feasibility remains UNDETERMINED: audit fetched newest transaction only, not the four archival target positions. Monster derivative/delisted retention likewise UNDETERMINED until PHASE 7 probes. Insufficient source data blocks its gate; it does not silently lower required coverage.

## HYPE availability evidence refinement

The read-only 31-day 1m probe returned 5,220 rows / 3.624 days, while official documentation states most recent5,000. Treat retention as approximately this scale, not an exact enforced row maximum. This real response does not supply 30 days and does not pass the replay gate; full retrospective30d remains unavailable; approved partial+forward gate permits live shadow while FORWARD_DATA_ACCUMULATING.
