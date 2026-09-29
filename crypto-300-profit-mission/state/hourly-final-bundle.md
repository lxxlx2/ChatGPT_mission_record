# $300 Mission Hourly Rolling State

schema_version: 2
canonical_repository: lxxlx2/ChatGPT_mission_record
timezone: Asia/Bangkok
status: READY
authoritative_for_completed_cycle: false
updated_at_bkk: 2026-09-29 19:51
persistence_mode: SINGLE_READ_SINGLE_UPDATE
git_reads_required_before_market_work: 1
git_writes_allowed_per_cycle: 1

## CORE_STATE
last_successful_cycle: null
last_core_status: bootstrap
notification_gate: material_action_only

## FRANK_STATE
target_wallet: 498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ
authoritative_cursor_signature: 5TCVznw1fF2d7Be5LMBjn1J7C8zdY2ByZNLMn3Y38Y5zKGixScuq5JXHwS2crP4zvYh6FmSYntHFadz4WXjV1Ehc
authoritative_cursor_slot: 451550987
authoritative_cursor_time_bkk: 2026-09-29 12:44:13
classification: NO_ACTION
watch_mints: []
hft_filtered_mints: []
formal_signal: NONE
pending_email_subject: null
gmail_message_id: null
gmail_readback_ok: false

## NFT_STATE
last_status: bootstrap
last_candidate: null
last_alert_key: null
last_scan_time_bkk: null

## MONSTER_STATE
last_successful_full_scan_at_bkk: 2026-09-29 12:33:00
deferred_shortlist: []
active_ignition: []
last_exhaustion: []
last_daily_summary_date: null

## LAST_CYCLE
scheduled_cycle: null
run_status: BOOTSTRAP
core_status: bootstrap
frank_signatures_seen: 0
frank_active_swaps: 0
frank_passive_filtered: 0
frank_unresolved: 0
frank_cursor_advanced: false
nft_status: bootstrap
monster_status: bootstrap
data_gaps: []
user_visible_event: NONE

## Embedded execution contract
- The scheduled task reads only this file from GitHub before market/source work.
- Frank active swap means Frank is signer/authority in a DEX/aggregator/pool value exchange. Plain transfers, ATA, airdrops, claims, rewards, DepositToken/WithdrawToken and unsolicited receipts are filtered.
- Frank HFT filter: >=3 same-mint active swaps in <=60s, rapid round-trip <=20m, or repeated routing/arbitrage means HFT_EXECUTION and silent.
- Frank WATCH is silent. Formal entry requires persistence, cumulative episode active buys >=10000 USD, material open exposure, price near Frank VWAP, sufficient liquidity, bounded token-control safety, no HFT, and freshness. Formal Frank delivery is Gmail only.
- NFT lane uses one bounded current English discovery query pack plus candidate-driven official verification. Source failure is PARTIAL_SOURCE_GAP, never healthy zero.
- Monster full scan due when >=3h since last successful full scan or at 19:29 BKK. Frozen IGNITION gates: 1h close > prior24h high by >=1%, 6h gain >=10%, 3h avg quote volume >=1.5x prior24h hourly median, taker buy >=51%, price >= setup*1.05. At most 5 deep checks, oldest deferred first.
- Every successful scheduled cycle performs exactly one existing-file update of this file. Git commit history is the per-cycle audit trail.
- Failed source/runtime/persistence cycle leaves this file unchanged and is silent to the user.
- No scheduled cycle creates per-run GitHub files while schema_version 2 is active.
