# Airdrop / TGE Automatic Runtime

Updated: 2026-09-28 19:34 Asia/Bangkok
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


## Coverage continuity

Do not double the workload after a missed run.

If a prior final is missing:
- record the gap in the current final;
- process only the current urgent set + current shard;
- rely on the normal 4-hour rotation to restore shard coverage;
- do not add a second full shard to the same run.

## Source fallback

For each project, use the canonical identity/domain/handle from REGISTRY.

If a direct page fails:
1. search the canonical official domain or official social handle;
2. use a recent official-domain search result/snippet or official social result when it is enough to determine whether a new TGE/claim/KYC/registration/allocation/distribution action exists;
3. only keep `source_unavailable` when current action status still cannot be determined.

Do not downgrade a run merely because one presentation surface is unavailable when equivalent current official evidence is available.


## Bounded discovery

For the urgent set and current shard:
- use one compact/batched English search pass over canonical project names, official handles/domains and action keywords;
- deep-open official pages only for projects with a plausible current candidate;
- no-result on a healthy batched search is `checked_no_update`, not `source_unavailable`;
- reserve `source_unavailable` for actual request/access failures where current action status remains unresolved.

This keeps the hourly run bounded and prevents fallback work from exhausting the cycle.

## Final persistence fallback

At completion:
1. try `HHMMSS-final.md`;
2. on write failure, retry once with `HHMMSS-final-retry.md` using a compact audit.

No optional cache write may occur before the final/final-retry attempt.


## Notification behavior

Use `docs/MONITORING/NOTIFICATION_POLICY.md`.

- checked_no_update / NO_ACTION: silent.
- source/tool/runtime/audit failure: log to GitHub only, no Gmail/ChatGPT.
- verified substantive ACTION affecting eligibility, entitlement, claim, timing, allocation or distribution: Gmail + ChatGPT.
- recovered_warning / optional cache failure: silent.

When no substantive ACTION exists, return an empty user-visible response.


## Delivery proof and stale-shard recovery — 2026-09-27

### Event delivery proof

An event is considered notified only when:
- an event archive exists with a real Gmail message id;
- Gmail Sent contains the expected message;
- readback confirms recipient + subject.

A run audit saying `already notified`, a prior ChatGPT message, or a candidate mention does not satisfy delivery proof.

If an actionable event is still open and the deadline is within 7 days, and delivery proof is missing:
- treat it as `delivery_recovery_action` exactly once;
- send Gmail + ChatGPT;
- archive the event with message id/readback;
- then dedupe normally.

2026-09-27 recovery example:
- Cambria RSGP Genesis Event opt-in remained open;
- prior audits claimed it had been notified;
- Gmail Sent contained no formal Cambria alert;
- a recovery alert was sent and archived.

### Stale shard recovery

Keep each run bounded to urgent set + one shard.

Determine the scheduled shard from Bangkok hour modulo 4. Before executing it, read the latest successful shard timestamps.

If any shard is more than 6 hours stale:
- execute the oldest stale shard instead of the scheduled shard;
- do not execute two shards in one run;
- record `scheduled_shard`, `executed_shard`, and `stale_shard_recovery: true`.

This restores missed coverage without doubling a run.

### Attempt audit

Before network/search work, create a small append-only:
`runs/YYYY-MM-DD/HHMMSS-attempt.md`

It records run_time, scheduled_shard and status=started.

The final/final-retry remains the only completion proof. An attempt file only makes scheduler/runtime gaps diagnosable.


## Intermediary / deal-rights override — 2026-09-28

A whitelist project with a known investment/deal intermediary must be checked at both layers:
- project official source;
- platform/SPV/syndicate/group-lead source recorded in REGISTRY.

Do not filter out a refund/cancellation/allocation/settlement event merely because the underlying project did not announce it.

Closed/refunded deals must not consume monitoring. Once a full refund or complete exit is confirmed and no entitlement remains, remove the project/deal channel from active shards and rights checks. Preserve it only as historical audit state unless the user explicitly reactivates it.

Current closed example: humans& via Echo/Alpen Capital was fully refunded on 2026-09-24 and is excluded from active monitoring.

### Persistence survival

Today's attempt-only runs show that creating an attempt file is not enough.

Immediately after attempt creation, create a compact provisional `HHMMSS-final.md` with:
- run_status: started
- scheduled/executed shard
- urgent-set status: pending
- notification status: pending

Then perform only the bounded urgent set + one shard. Update that same final file to success/partial/failure. If update fails, write `final-retry.md`.

Never spend the remaining run budget on optional cache or deep enrichment before a durable final artifact exists.


## Clock integrity and pending-delivery override — 2026-09-28

A timestamp integrity failure was confirmed on 2026-09-28:
- `201500-final-retry.md` was committed at 10:13 Asia/Bangkok but claimed run_time 20:15;
- `221500-final.md` was committed at 18:18 Asia/Bangkok but claimed run_time 22:15.

These impossible future timestamps must not count as shard coverage or delivery evidence.

Rules:
- filename/run_time must use the actual current Asia/Bangkok wall clock;
- never write a run_time more than 5 minutes in the future;
- before using a prior final for shard freshness, reject any record whose run_time is materially later than its Git commit/current wall clock;
- impossible-time files are historical invalid artifacts, not authoritative coverage.

### Pending delivery recovery

Every run first scans recent authoritative finals for:
- `triggered_events > 0`;
- `gmail_sent: false`, missing Gmail message id, or missing event archive.

Any still-relevant undelivered event is promoted into the urgent set until one real Gmail Sent id + readback + event archive exists.

A later NO_ACTION run must not erase an earlier undelivered ACTION.

### State freshness

`state/current.md` is a convenience index but must not remain a day behind.

After a successful final, update its:
- last successful real run time;
- per-shard last successful real time;
- open urgent events;
- pending delivery events.

If cache update fails, the next run derives freshness from authoritative finals and ignores invalid future timestamps.


## ACTION gate is authoritative — 2026-09-29

Every run MUST read:
- `ACTION_GATE.md`
- `state/known-events.md`

Run order for each candidate:
1. discovery;
2. canonical identity;
3. evidence tier;
4. freshness;
5. user-known / delivered / completed state;
6. stable event-key dedupe;
7. material delta;
8. rights relevance;
9. notification decision.

The fallback wording elsewhere in this runtime does NOT permit secondary-only alerts. Independent English sources can keep discovery healthy or corroborate a candidate, but ACTION requires Tier A project-first-party or Tier B explicitly mapped user-rights evidence.

If Tier A/B cannot be obtained:
- write `UNVERIFIED_CANDIDATE`;
- remain silent;
- retry on a later scheduled run if still relevant.

Search snippets without a resolvable canonical first-party URL are never ACTION proof.

Expired deadline -> NO_ACTION unless a new Tier A/B update reopens or extends it.
Undated/static page -> current-state corroboration only, not a new event by itself.
Already user-known/delivered/completed/claimed/refunded -> NO_ACTION absent a material delta.
CLOSED_FULLY_REFUNDED -> skip before network work when possible.

For missed-delivery recovery, require:
- still-open/current Tier A/B proof;
- unresolved user action/right;
- missing Gmail+event delivery proof;
- material risk from not informing the user.
Do not backfill stale no-deadline historical events merely because they were absent from GitHub.

Generic underlying-company valuation/funding is background only unless a mapped user-rights source confirms user-level term impact.
