# Airdrop / TGE Automatic Runtime

Updated: 2026-09-26 18:34 Asia/Bangkok
Timezone: Asia/Bangkok

Authority for the existing :14 task.

## Audit
The append-only final audit is canonical.

At run start, make one best-effort attempt to create:
`airdrop-tge-monitor/runs/YYYY-MM-DD/HHMMSS-start.md`.

If the start write is blocked, continue the monitoring work and record the warning in the final audit. A missing start marker alone is not a run failure.

At completion create matching `HHMMSS-final.md`.

## Hourly factual work
1. read REGISTRY.md;
2. read recent final audits/events for dedupe;
3. check always-hourly urgent set;
4. check current Bangkok hour % 4 shard;
5. only for a real candidate, perform official identity + action verification;
6. classify checked_no_update / checked_action / source_unavailable / identity_fail;
   - if a direct official page is inaccessible, use a fresh official-domain search result, official social account, official docs mirror, or another independent English source as fallback;
   - if fallback gives enough current evidence to determine there is no new action, classify checked_no_update;
   - keep source_unavailable only when the project cannot be meaningfully checked after fallback;
7. ACTION can use the already authorized notification path; NO_ACTION remains silent;
8. state/current.md is optional cache only;
9. create final audit regardless of cache outcome.

A cache-write failure alone does not downgrade a complete run.
Only an unresolved source/tool gap counts as a failure.
Temporary failures never disable/pause the task.
No Chinese-language websites as evidence.
