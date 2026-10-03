# Frank-only local signal refactor — FRANK_LOCAL_SIGNAL_V1

Target: `FRANK_ONLY`, `LOCAL_DETERMINISTIC_SIGNAL`. Deployment status: `FRANK_LOCAL_SIGNAL_V1_LIVE`, activated 2026-10-04 00:29:01 Asia/Bangkok. Historical and shadow delivery remain disabled.

Only Frank is enabled. Other persons and TOKEN_CONSENSUS are DEFERRED. Production trading is NO_GO. No wallet mutation or new scheduled automation is introduced. The existing launchd scanner was replaced once after checkpoint verification.

## Frozen behavior authority

[FRANK_LOCAL_SIGNAL_V1_POLICY.md](FRANK_LOCAL_SIGNAL_V1_POLICY.md) and `local-agent/config/frank_local_signal_v1.json` contain 78 source-bound extracted predicates. Policy SHA256 is `83ebab1fbb8ec7e03950626137c5597a38b81b8a4085d9150610018cc78cedab`.

Provenance: `DERIVED_FROM_EXISTING_FRANK_BEHAVIOR_MODEL`; `NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT`. Canonical PRECONFIRM has S/C, not A/B. User resolved MAPPING_SEMANTIC_MISMATCH by selecting only Path C repeated buys: >=2 confirmed ACTIVE BUY in 60 minutes and >=25,000 raw USDC quote quantity. `PATH_C_SINGLE_LARGE_BUY = NOT_ACCUMULATION`; original >=15,000 branch remains provenance and has no new visible signal type. Path S is not mapped.

MULTIPLE requires accumulation, canonical T0 (>=2 buys and >=3,000 in 60 minutes OR >=5,000 followed by another buy within 60 minutes), persistence A (prior hourly :29 WATCH continuing to qualify) OR B (>=3 buys spanning >=45 minutes), cumulative >=10,000, materially open observed inventory (>=50% episode peak or resumed net buying in last 60 minutes), no >35% rolling-hour distribution without re-accumulation, and no HFT. HFT includes >=3 swaps within 60 seconds; the approximate 20-minute roundtrip reference is kept distinct from an exact source threshold. If T0 is >3 hours old, require a fresh buy within 60 minutes and open inventory. No numeric dust, relative-size percentile or additional ADD threshold is invented.

USDC quote => direct numeric comparison. Non-USDC quote without reliable conversion => amount gate undetermined. Numbers 3,000/5,000/10,000 remain unchanged; raw USDC is not independently verified USD valuation. SOL conversions are not improvised. Other predicates, trades and chronology remain auditable.

Social, current price, chase, liquidity, executability, followability and GPT decisions do not veto signals. Evaluator inputs are durable verified active chronology, observed sequence state and frozen policy only. No model recalibration uses 7Vert or STONK.

## Durable runtime and delivery

`mission_agent.signals` classifies signed, proven swaps conservatively; passive transfers/ATA creation never count as BUY. UNKNOWN fails closed. Finalized scanner stores RAW_PENDING detections before fetch, raw before classification, and advances cursor atomically. Registry supports multiple wallets per person. SQLite migration and replay remain independent of old history.

Observed positions are explicitly `LIFETIME_POSITION_UNKNOWN` / `CURRENT_ACCUMULATION_SEQUENCE_KNOWN`. Unresolvable or excess sells invalidate inventory without inventing EXIT. Exact zero observed active inventory closes an observed sequence; no dust threshold is invented.

Signal/model state and outboxes commit atomically. Identity includes policy, person, mint, observed episode and stage. Same-stage ADD does not redeliver. ACCUMULATION has local delivery only; MULTIPLE has local and standalone Gmail content/hash/outbox. Gmail is CREDENTIAL_BLOCKED in this environment; no fake receipt. Local notifier uses a stable OS identifier plus content-bound durable receipt for restart recovery. Command acceptance does not prove visual receipt by a user.

Two real macOS `[TEST]` notifications (one for each stage) were accepted by osascript/AppKit. Repeated delivery reused receipts. Historical rows stay DRY_RUN_AUDIT and are never promoted for backfill delivery.

## Validation and replay

Full tests: 462 passed, 3 skipped (unrelated Monster modules lack numpy). Available historical subset: 6,874 classified records, 634 ACTIVE_TRADE, 203 active mints, 180 observed episodes; 21 ACCUMULATION, 10 MULTIPLE, 124 duplicate-stage suppressions. UNKNOWN/incomplete blocked union: 732; undetermined predicate evaluations: 26. This is not an exhaustive 30-day wallet history. Historical notifications/mail: zero.

7Vert five genuine buys total 71,079.393003 USDC. First accumulation is buy #2 at 2026-10-03 23:26:43 Asia/Bangkok; buys #3–#5 remain same stage. No MULTIPLE: first-to-last span is 14m37s, below 45 minutes; buys #2–#4 also establish HFT. Identical replay inputs yield identical IDs/reasons. Thresholds remain frozen.

Private evidence and runtime databases remain outside the public repository. Query CLI `python -m mission_agent.signals --db /absolute/path/forward.sqlite audit-frank --last 50` and `inspect-tx SIGNATURE` opens SQLite read-only. Replay requires an isolated new ledger.

## Legacy GPT authority

`SUPERSEDED_FOR_FRANK_SIGNAL_AUTHORITY`: the new service imports no GPT or Git handoff worker. Old runtime facts/history are preserved; old writer is stopped at cutover. The legacy ChatGPT consumer may remain configured (`LEGACY_GPT_CONSUMER_STILL_PRESENT`) because this session has no dedicated ChatGPT scheduled-task administration capability. It has no authority to veto or send new local Frank signals. Private mac-data supersession marker records the transition; gpt-data ownership is preserved.

## Controlled cutover verification — 2026-10-04

Old PID 23182 stopped at 00:29:00.875 Asia/Bangkok; new PID 12188 started at 00:29:01.147. New startup implementation commit: `8f91d890913103ce2900bf97aac830a1c9aec140`. Exactly one scanner/delivery authority verified. One controlled cutover; new process restart_count=0. Old LaunchAgent was booted out and its plist preserved with a disabled suffix; history/raw/SQLite snapshots were retained.

Final old durable cursor was retained at slot 452991464. Restart-window catch-up signatures=0 because no new wallet signature occurred. Independent finalized baseline reconciliation: chain=35, old observations=35, new ledger=35, missing/extra/gap=0. Baseline starts 2026-10-03 05:02:49.509370 Asia/Bangkok, from durable first_started_at, not a Git commit time. Health RUNNING; raw pending=0, model unprocessed=0, consecutive_errors=0, lag_seconds=0, source_drift=false. Imported accumulation stays DRY_RUN_AUDIT; no 7Vert historical notification was backfilled.

Private mac-data manifest and authority marker were marked SUPERSEDED_FOR_FRANK_SIGNAL_AUTHORITY with exact readback; old current handoff was expired. gpt-data/main were not changed. The legacy consumer configuration remains outside available task-administration capabilities and is explicitly LEGACY_GPT_CONSUMER_STILL_PRESENT.
