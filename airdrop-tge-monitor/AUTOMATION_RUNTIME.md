# Airdrop / TGE Automatic Runtime

**Active execution override 2026-10-10:** Existing task now runs at HH:00 Asia/Bangkok, once each hour (24 per day), as expressly authorized. The legacy HH:50 and HH:14 references are superseded for future runs. Shard is still local hour % 4, urgent set every hour, exactly one shard per run and existing stale-shard recovery. Do not classify genuine historic HH:50 run artifacts as invalid merely due to the new schedule. Never change title, monitoring scope or notification gate.

Updated: 2026-09-28 19:34 Asia/Bangkok
Timezone: Asia/Bangkok

Authority for the existing hourly :00 task (Asia/Bangkok), user approved on 2026-10-10. Earlier :50 is historical.

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

## 2026-10-08 terminal-audit and pending-delivery health correction (latest override)

1. Each invocation checks the canonical known-events and pending-undelivered finals BEFORE new discovery. A recorded `PENDING_DELIVERY` is only a candidate: before resend require fresh Tier A/B proof that the relevant action is currently open/reopened and materially changes user rights. Do not resend unchanged/expired opt-in reminders; do not convert a past post date into a new event date. Keep earlier pending candidates in audit until independently resolved.
2. Write one append-only `HHMMSS-attempt.md` at the start. Then perform only the current urgent set plus one shard. At the end write exactly one terminal `HHMMSS-final.md`; if this write fails, one compact `HHMMSS-final-retry.md`. DO NOT create provisional `run_status: started` in any final artifact; attempt does not count as final. No multiple updates to the same final.
3. Minimize terminal audit payload: clock time, scheduled/executed shard, authoritative source receipt counts, candidate/action/notification outcome, delivery proof or exact blocking reason, and uncovered gaps. If an early operation fails, still try to write a truthful compact terminal audit. Never label a failed write/sent email as a success.
4. On completion update existing `state/current.md` with the latest authoritative success, most recent attempted/partial run, missing final windows, and unresolved pending delivery. A state update is cache synchronization, not a substitute for run final. Maintain user suppression of Abstract and CLOSED status of humans&.
5. Health regression confirmed on 2026-10-08: runs at 07:53, 08:50, 09:48 and 11:47 had attempts without terminal final as of 11:53 Asia/Bangkok. The 06:47 Cambria candidate referenced an X status posted 2026-09-30 after the previously announced Sep 29 deadline, but no reliable direct readback establishes reopened opt-in. The existing Cambria opt-in reminder was already sent on Sep 27; do not duplicate without newly verified Tier A/B material delta.
6. Do not change the newly authorized :00 schedule, task title, scope or recipient; no new automation, delivery-only monitor, or extra user notification for runtime health. English primary sources only for actionable claims.

## 2026-10-13 stale-shard starvation fix — latest override
The old criterion `oldest last FULLY successful shard` must not be used as the scheduler cursor while all shards have partial/source gaps: it repeats the same stale shard indefinitely and starves other project groups. Preserve both distinct clocks: `last_verified_complete_at[shard]` for coverage honesty and `last_meaningful_attempt_at[shard]` for scheduling fairness. A PARTIAL never updates verified-complete timestamps; it DOES update last-meaningful-attempt only when the terminal final proves that named projects and actual Tier A/B sources were attempted, with gaps explicitly listed.

At each real Asia/Bangkok HH:00: urgent set first, then exactly one deep shard. Default shard = local `hour % 4`. To recover a genuinely skipped group, override at most ONCE in any four consecutive recorded invocations and choose the shard with the oldest `last_meaningful_attempt_at`, NOT oldest `last_verified_complete_at`. Same executed shard must not occur more than twice consecutively while any other group has missed its ordinary rotation. If last-attempt evidence cannot be reconstructed, use default hour % 4 rather than looping an imagined stale group. Maintain a persistent separate per-shard `verified_complete` flag: partial remains PARTIAL even if all groups were attempted within four hours. Failed provider endpoints remain open `SOURCE_GAP` and are revisited when ordinary rotation returns or new official evidence makes them urgent, without crowding out unrelated groups.

Final receipt fields (all real): `scheduled_shard`, `executed_shard`, `override_reason`, `last_meaningful_attempt_at`, `last_verified_complete_at`, `consecutive_same_shard`, `last_four_executed_shards`, `source_unavailable`, `action_gate_pass`, `gmail_sent_readback`. If final cannot be persisted, do not count the run as a verified attempt. Keep one fallback final-retry write, no shadow tasks, unchanged urgent set and source policy. This fixes fairness, NOT missing first-party sources or external Gmail/GitHub safety blocks.

Operational priority during unresolved write blocks: one compact attempt write when feasible; official ACTION verification is the substantive task; dedupe Gmail Sent before any action; only confirmed ACTION calls Gmail. After Gmail Sent/readback, persist event receipt before nonessential state cache. Failed attempt/final writes cannot justify duplicate alerts or fabricated last-success stamps.

## 2026-10-15 Surf/StandX first-party lifecycle, cross-shard emergency and Gmail contract — latest
Two actual omissions prove that hourly invocation alone is not an SLA: Surf official issuer blog on Oct 15 established 03:00 UTC claim-open, 2026-11-13 deadline and annual-member eligibility, yet existing 04:00/09:13 runs kept `SOURCE_GAP/NO_ACTION` after checking only a JS claim shell. StandX was legitimately scanned at 04:00 BEFORE the new Oct15 shutdown announcement, but no later cross-shard emergency sweep elevated a venue wind-down and DUSD redemption deadline from shard0 before its next regular turn. These are discovery/fallback defects distinct from Gmail connector execution blocks.

Every hour, after existing urgent+one-shard discovery, run a bounded one-batch English headline check for NEW material lifecycle changes affecting projects ALREADY IN Registry: venue shutdown/ceasing token launch, deposit freeze, reduce-only, forced settlement, user balance withdrawal/redemption deadline, airdrop eligibility checker or live claim, and issuer post-mortems. This batch does NOT count as a second deep shard, does NOT add new projects, and does NOT change schedule. If a new official material lifecycle lead concerns a project outside the selected shard, immediately promote its existing registry identity to DYNAMIC_URGENT and verify the actual first-party source or explicitly mark SOURCE_GAP for source text, not `checked_no_update`. StandX shutdown is a mandatory regression case. A one-line English headline is DISCOVERY only, not proven user eligibility or confirmed private allocation.

First-party sources are not limited to JavaScript claim pages. For Surf, `https://asksurf.ai/blog/en/surfboard-nft-launch` is direct primary dated issuer publication with claim-open, qualifying purchases, onchain network and deadline; checking `nft.asksurf.ai` JS shell alone is NOT meaningful coverage when the linked blog is indexed and accessible. For all existing issuers, check official English dated blogs/FAQs/announcements and crosslink to claim page. Separate claim-open (issuer public rule proved) from individual wallet entitlement (may remain unknown): Gate 6 permits a materially relevant timely eligibility-check action for users engaged with this already tracked project without fabricating their allocation. Actual first-time event needs only credible relevant user exposure, not confirmation they definitely have a claim.

Delivery: one confirmed fresh ACTION -> Gmail on existing authorized recipient ONLY; Sent ID+readback+archive required. Do not use App/task natural-language notification as an alternate or substitute delivery. Task's visible result should be silent for successful NO_ACTION and successful ACTION (sent through Gmail). If platform unexpectedly shows a user App push, treat that as a separate possible platform-surface artifact; do not claim origin without actual notification audit. Existing task app_notifications_enabled is false. Stop sending explanatory App output as an action proxy.

For late discovery, send a first *currently actionable* notification immediately when verified, explicitly marking that the claim opened earlier. If action expired or already claimed, keep silent. All failures: preserve original blocked reason, source gaps and current deadline (do not invent completed checks). Triage latest urgent deadline items before general shard research, without starvation or redundant state writes. No change in task name, hours, alert volume policy or registry membership; preserve old known-state dedupe.

## 2026-10-16 cross-project rights discovery regression — NeoSoul DNA to StandX

Within the EXISTING StandX Registry Shard 0 identity and existing once-per-hour bounded lifecycle headline pass, inspect newly announced third-party issuer compensation or distribution to beneficiaries of **existing registered projects**. This is a relationship lookup, not a new issuer/coin project shard. Query English official/issuer announcement and Binance Wallet/Alpha authenticated announcement sources with StandX as BENEFICIARY, including project aliases and `compensation|allocation|airdrop|holder|points|snapshot|claim`. A partner token may be important even when the monitored project's own website remains unchanged or its old planned token was canceled.

Regression evidence: On 2026-10-15 Binance News published `NeoSoul Plans Dedicated DNA Airdrop for StandX Community` (https://www.binance.com/en/square/post/10-15-2026-neosoul-plans-dedicated-dna-airdrop-for-standx-community-377570746498100 ), attributing a proposed DNA allocation to NeoSoul / NS3.AI for longstanding StandX contributors, with eligibility and claim site not yet announced until after TGE. Binance Wallet's first-party verified profile (https://www.binance.com/en-IA/square/profile/binancewallet ) announced NeoSoul DNA's Binance Alpha launch on 2026-10-16 and a separate Alpha Points campaign subject to eligibility. These are TWO events, not the same payout:
- `neosoul:dna_standx_community_allocation:2026-10-15`  => `BENEFICIARY_RELATIONSHIP_DISCOVERED`, exact eligibility/snapshot/amount/claim `UNVERIFIED`; issuer original social full text `SOURCE_GAP` until direct readback. Binance News attribution is a secondary lead, not a qualifying Tier A or registry-mapped Tier B ACTION proof.
- `neosoul:dna_binance_alpha_release:2026-10-16` => Binance Wallet official platform-listing announcement. This does NOT by itself confirm StandX entitlement. Check the official Alpha activity details when available, and do not assume the standard Alpha Points threshold equals a StandX compensation entitlement.

If no firsthand issuer commitment can be retrieved, classify as HIGH_MATERIALITY `VERIFYING_PARTNER_RIGHTS` in the internal state/next scheduled retry; do NOT falsely mark checked_no_update, silently drop, invent a new claim URL, declare the user eligible, or send an ACTION Gmail. After actual Tier A issuer evidence or mapped Tier B rights evidence confirms a currently relevant unnotified user action, use the existing ACTION_GATE and same original Gmail delivery/known-events archive semantics; keep precise amounts/status unverified until proven.

This bounded cross-project relationship discovery may not promote every issuer mentioning StandX to the Registry, may not add an extra shard, automation or Gmail health notification, and must not make partial provider/source coverage a fully verified success. Existing user suppression and completed-event silent behavior remain in force.
