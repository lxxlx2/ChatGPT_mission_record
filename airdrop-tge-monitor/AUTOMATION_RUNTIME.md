# Airdrop / TGE Automatic Runtime

Updated: 2026-09-26 19:55 Asia/Bangkok
Timezone: Asia/Bangkok

Authority for the existing :14 task.

## Audit

The only mandatory persistence artifact is:
`airdrop-tge-monitor/runs/YYYY-MM-DD/HHMMSS-final.md`.

Do not require or attempt a start file in the automatic path. Older start files remain valid historical artifacts.

A final audit is mandatory whenever monitoring work can execute.

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


## Missed-run recovery

Before choosing the current shard, inspect the newest final audit.

If the prior scheduled run is missing:
- process the current shard;
- also process the one missed shard, capped at two shards total for the recovery run;
- record `recovered_missed_run: true` and the recovered shard index;
- do not create a separate automation.

## Source fallback

For each project, use the canonical identity/domain/handle from REGISTRY.

If a direct page fails:
1. search the canonical official domain or official social handle;
2. use a recent official-domain search result/snippet or official social result when it is enough to determine whether a new TGE/claim/KYC/registration/allocation/distribution action exists;
3. only keep `source_unavailable` when current action status still cannot be determined.

Do not downgrade a run merely because one presentation surface is unavailable when equivalent current official evidence is available.
