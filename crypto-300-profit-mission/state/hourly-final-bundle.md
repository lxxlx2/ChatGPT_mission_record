# $300 Mission Hourly Durable Bundle

purpose: single-file rolling durable checkpoint for the existing hourly :29 automation
timezone: Asia/Bangkok
write_policy: existing-file update only
history_policy: every successful update is preserved by Git commit history
status: BOOTSTRAP
manual_existing_file_update_probe: PASS
manual_probe_time: 2026-09-29 17:35 Asia/Bangkok
bootstrap_time: 2026-09-29 17:34 Asia/Bangkok

## CORE
bootstrap_only: true
note: first scheduled successful cycle replaces this section with current CORE facts.

## FRANK
bootstrap_only: true
target_wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`
authoritative_cursor_signature: `5TCVznw1fF2d7Be5LMBjn1J7C8zdY2ByZNLMn3Y38Y5zKGixScuq5JXHwS2crP4zvYh6FmSYntHFadz4WXjV1Ehc`
authoritative_cursor_slot: 451550987
authoritative_cursor_time: 2026-09-29 12:44:13 Asia/Bangkok
cursor_source: `state/frank-live-cursor.md`
note: bootstrap does not advance live Frank state.

## NFT
bootstrap_only: true
note: first scheduled successful cycle replaces this section with bounded discovery receipt.

## MONSTER
bootstrap_only: true
last_known_successful_full_scan_at: 2026-09-29 12:33 Asia/Bangkok
note: first scheduled successful cycle replaces this section with current due/not-due receipt.

## COMPLETION
run_status: BOOTSTRAP
authoritative_for_new_cycle: false
notification: none

## Recovery semantics
- A scheduled cycle reads this existing file before work.
- After all mandatory lanes complete in memory, it performs exactly one GitHub mutation by updating this same file with the current SHA.
- If that update is blocked or fails, this file remains unchanged and therefore the prior durable cursor/state remains authoritative.
- The next cycle replays from the last durable Frank cursor recorded here.
- Do not create a per-run GitHub file inside the scheduled cycle while this rolling-state override is active.
