# Frank 30D Compact Checkpoint

schema_version: 1
mode: HISTORICAL_REPLAY_ONLY
canonical_repository: lxxlx2/ChatGPT_mission_record
target_wallet: 498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ
window_start_bkk: 2026-08-30 14:50:00
window_end_bkk: 2026-09-29 14:50:00
total_signatures: 7106
phase: PHASE_2
classification_status: RUNNING
classified_signature_count: 180
classification_before: 3NDs39T3gWSftvQz227EhgqcDyU8C7EF6Uc4JDy5UcZZUtNC5s7n6U9kLFb18A7XzriU76qx5JbGSc9PsCpbBJg2
classification_oldest_time_utc: 2026-09-28T08:21:25Z
classification_oldest_time_bkk: 2026-09-28 15:21:25
active_swaps_verified: 26
passive_filtered: 154
unresolved_tx_count: 0
unique_active_tokens: 14
live_cursor_mutation: FORBIDDEN
last_chunk_size: 10
last_chunk_status: DURABLE
last_chunk_active: 0
last_chunk_passive: 10
last_chunk_unresolved: 0
last_chunk_note: checkpoint imported from frank-30d-replay-state.md at 180/7106
updated_at_bkk: 2026-09-29 19:49

## Persistence contract
- This file is the only scheduled-run PHASE 2 checkpoint.
- Each scheduled run reads this file once, processes exactly 10 contiguous signatures, then updates this same existing file once.
- Git commit history is the durable per-chunk audit trail. Each update must include the 10 short signature prefixes and classifications in last_chunk_note.
- A failed or partial 10-signature chunk performs zero mutation.
- The large research/frank-30d-replay-state.md remains archival and is not rewritten by the scheduler.
- PHASE 3 must aggregate scheduled chunk history from Git commits plus existing archival/manual checkpoints before simulation.
