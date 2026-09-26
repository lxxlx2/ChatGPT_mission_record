# Airdrop / TGE Automatic Runtime

Updated: 2026-09-26 15:10 Asia/Bangkok
Timezone: Asia/Bangkok

Authority for the existing hourly :14 scheduler.

## Append-only audit

At start create:
`airdrop-tge-monitor/runs/YYYY-MM-DD/HHMMSS-start.md`

with run_status: started.

Do not update that file.

At end create:
`airdrop-tge-monitor/runs/YYYY-MM-DD/HHMMSS-final.md`

with:
- run_time
- automation_id
- run_status
- urgent_checked
- shard_index
- shard_projects_checked
- candidate_count
- triggered_events
- identity_failures
- source_failures
- gmail status
- state_cache_status
- tool_errors

A run is complete only when the final file exists. Full urgent+shard coverage with no real source/tool failure is `success` even if the optional mutable state cache cannot be updated.

## Hourly work

1. Read `REGISTRY.md`.
2. Read `state/current.md`.
3. Check always-hourly urgent set.
4. Check current Bangkok hour % 4 shard.
5. For an actual candidate only, follow official action links and apply canonical identity + two-anchor. Read README/MONITOR_SPEC only when needed for candidate validation.
6. ACTION only when official evidence creates a real eligibility/deadline/claim/KYC/registration/allocation/distribution requirement.
7. NO_ACTION stays silent.
8. Use recent `*-final.md` run files plus `reports/events/` for dedupe/history. Do not require a mutable state file for correctness.
9. `state/current.md` is an optional cache. Attempt at most once only when useful; a cache-write failure must not downgrade an otherwise complete run.
10. Create final audit regardless of cache-write outcome.

## Classification

- checked_no_update: source worked, no new action
- checked_action: verified action
- source_unavailable: real access/tool error
- identity_fail: evidence exists but identity unresolved

Only source_unavailable is a source failure.

## Daily summary

First successful run after 00:00 summarizes the previous local day from real run files only.

Temporary failures never disable/pause the existing task.
No Chinese-language websites as evidence.
