# TGE / Airdrop Action Gate

Updated: 2026-10-02 Asia/Bangkok
Status: canonical pre-notification gate

Purpose: prevent secondary-source alerts, expired alerts, duplicate user-known events, already-completed actions, closed/refunded deal noise, and generic company-news alerts that do not change the user's rights.

Every candidate must pass ALL mandatory gates before Gmail notification.

## Gate 0 — Active scope

The project/deal must still have one of:
- unresolved entitlement;
- capital at risk;
- pending claim/distribution;
- open registration/KYC/wallet-link/signature/opt-in;
- future TGE/listing/distribution event within monitored scope;
- active allocation/settlement/refund process.

If project/deal state is CLOSED, FULLY_REFUNDED, COMPLETED_NO_REMAINING_ACTION, USER_SUPPRESSED, or explicitly excluded, return NO_ACTION.

## Gate 1 — Canonical identity

The candidate must match the monitored project's canonical identity tuple.
Hard fail on unresolved official handle/root-domain/ticker/chain/contract identity mismatch or same-name collision.

## Gate 2 — Evidence tier

A — project first-party canonical source.
B — mapped user-rights first-party source in REGISTRY.
C — reputable English independent corroboration.
D — discovery-only community/KOL/aggregator.

A user-facing ACTION requires Tier A or Tier B. Tier C/D can discover or corroborate but cannot authorize ACTION by themselves.

## Gate 3 — Event freshness and first-alert policy

Persist:
- source_published_at;
- source_updated_at;
- event_effective_at/deadline;
- first_discovered_at;
- discovery_lag_minutes when calculable.

Rules:
1. Past deadline/closed action is NO_ACTION unless a NEW Tier A/B update explicitly reopens or extends it.
2. Old announcements resurfaced by search are NO_ACTION when the action is no longer current/open or no plausible unresolved user right remains.
3. Undated/static pages can confirm state but cannot by themselves create a NEW ACTION event unless another Tier A/B source establishes that the action is currently open.
4. For claim-open / registration-open / TGE-live / listing-live / unlock-live events, late discovery does NOT by itself suppress the first alert. If Tier A/B confirms the action is still current/open and the user may still have an unresolved right/action, one user-facing notification is allowed even when discovery lag exceeds 2 hours.
5. The first alert must disclose the actual status without pretending it just opened. If source timing is known, include that it opened earlier / was announced earlier and give the source time/date where useful.
6. After the first delivered notification for a stable event key, unchanged reminders are permanently suppressed. A second notification requires a material Tier A/B delta such as deadline/time change, eligibility change, allocation/amount change, route replacement, tokenomics change, listing venue/time change, refund/settlement status change, reopen/extension, or another user-rights change.
7. A stale-recovery shard/run may send the one allowed first alert only if Rules 1-5 pass and no prior delivered notification exists for that stable event key.
8. Generic historical pages with no current/open action and no unresolved user relevance are archive-only.

## Gate 4 — User-known state

Read `state/known-events.md`, recent event archives/finals, and Gmail Sent when delivery proof matters.
If the stable event is already user-known, completed, claimed, opted-in, refunded, delivered, or user-suppressed: NO_ACTION unless a new material delta exists.
User-confirmed state outranks later secondary reports.

## Gate 5 — Stable event key and material delta

Stable event key:
`<canonical_project_id>:<event_type>:<effective_date_or_version>`

Material deltas include deadline/time, eligibility, allocation/amount, route, tokenomics, listing venue/time, refund/settlement status, reopen/extension, or user-rights change.
Not material: another article/KOL post, unchanged webpage, repeated official reminder, price commentary, generic financing/valuation unrelated to user rights.

## Gate 6 — Rights relevance

For private-company/SPV/deal monitoring, distinguish underlying-company news from user-facing rights changes. Company financing/valuation alone is NO_ACTION unless mapped Tier B evidence changes the user's allocation, security, fees, conversion, transfer/redemption, settlement/distribution or another stored right.

## Gate 7 — Delivery

Only after Gates 0-6 PASS:
1. persist event archive/stage state;
2. dedupe event key and Gmail subject;
3. send Gmail;
4. Gmail Sent id + readback + event archive = delivered.

If delivery fails, persist PENDING_DELIVERY and retry delivery before evaluating a duplicate new alert.

## Required audit fields

- project_id
- candidate_source_url
- candidate_source_account/domain
- evidence_tier
- source_published_at
- source_updated_at
- event_effective_at
- event_deadline
- first_discovered_at
- discovery_lag_minutes
- identity_match
- freshness_result
- user_known_state_result
- prior_event_key_match
- material_delta
- rights_relevance
- gate_result
- rejection_reason
- notification_decision

If fields are insufficient to pass safely, default NO_ACTION / UNVERIFIED_CANDIDATE.
