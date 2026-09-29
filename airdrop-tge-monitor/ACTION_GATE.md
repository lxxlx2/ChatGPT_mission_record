# TGE / Airdrop Action Gate

Updated: 2026-09-29 Asia/Bangkok
Status: canonical pre-notification gate

Purpose: prevent secondary-source alerts, stale/expired alerts, duplicate user-known events, already-completed actions, closed/refunded deal noise, and generic company-news alerts that do not change the user's rights.

Every candidate must pass ALL mandatory gates before Gmail/ChatGPT notification.

## Gate 0 — Active scope

The project/deal must still have one of:
- unresolved entitlement;
- capital at risk;
- pending claim/distribution;
- open registration/KYC/wallet-link/signature/opt-in;
- future TGE/listing/distribution event within monitored scope;
- active allocation/settlement/refund process.

If project/deal state is CLOSED, FULLY_REFUNDED, COMPLETED_NO_REMAINING_ACTION, or explicitly excluded, return NO_ACTION.

## Gate 1 — Canonical identity

The candidate must match the monitored project's canonical identity tuple.

Hard fail on unresolved:
- official handle mismatch;
- root-domain mismatch;
- ticker mismatch;
- chain/contract mismatch;
- same-name project collision;
- source account belongs to another project.

Space @intodotspace vs Spacecoin @spacecoin remains the regression control.

## Gate 2 — Evidence tier

Evidence tiers:

A — project first-party:
- canonical official X/social account;
- canonical official root domain/docs/blog/help/app;
- official project action page directly anchored from a canonical first-party source.

B — user-rights first-party:
- the exact platform/SPV/syndicate/group lead through which the user's deal/right is held, but only when that source is explicitly mapped in REGISTRY.

C — independent corroboration:
- reputable English news/research source.

D — discovery only:
- KOL/community post;
- search-engine summary without a first-party origin;
- repost/quote from an unrelated account;
- aggregator.

A user-facing ACTION requires Tier A or Tier B evidence.

Tier C and Tier D can discover or corroborate a candidate, but can NEVER by themselves authorize an ACTION.

If a first-party page is unavailable and only C/D evidence exists:
- persist candidate as UNVERIFIED_CANDIDATE;
- do not notify;
- retry in later scheduled runs.

An official-domain search result/snippet can support discovery, but for ACTION it must resolve to a canonical official URL and preserve publication/update date plus exact event identity. A bare search snippet is insufficient.

## Gate 3 — Event freshness

Persist:
- source_published_at when available;
- source_updated_at when available;
- event_effective_at / deadline when applicable;
- first_discovered_at.

Rules:
1. A past deadline/closed action is NO_ACTION unless a NEW Tier A/B update explicitly reopens or extends it.
2. An old announcement resurfaced by search is NO_ACTION when no material event field changed.
3. An undated/static page can confirm current state but cannot by itself create a NEW ACTION event.
4. Late-discovery recovery is allowed only when:
   - Tier A/B proves the action is still open/current; AND
   - the user still has a plausible unresolved right/action; AND
   - either deadline/effective time is within the next 7 days, or missing prior delivery would materially risk entitlement.
5. Generic historical pages with no current deadline, no new update and no unresolved user action are archived only, not notified.

## Gate 4 — User-known state

Read:
- `state/known-events.md`;
- recent event archives;
- recent authoritative finals;
- Gmail Sent when delivery proof is relevant.

If the same stable event is already user-known, user-confirmed, completed, claimed, opted-in, refunded, or delivered:
- NO_ACTION unless a material delta exists.

User-confirmed state outranks later secondary reports.

When the user tells ChatGPT that they already completed, claimed, refunded, closed, sold, or otherwise resolved an event, that state must be persisted to `state/known-events.md` before future monitoring decisions rely on it.

## Gate 5 — Stable event key and material delta

Stable event key:
`<canonical_project_id>:<event_type>:<effective_date_or_version>`

Before sending, check whether the key or its superseded predecessor is already known/delivered.

Material delta examples:
- deadline/time changed;
- eligibility changed;
- allocation/amount changed;
- claim/distribution route replaced;
- tokenomics materially changed;
- listing venue/time changed;
- refund/settlement amount/status changed;
- action reopened/extended;
- project/deal changed from pending to completed/cancelled/refunded.

Not material by itself:
- another media article;
- another KOL post;
- unchanged webpage;
- repeated official reminder with identical terms;
- price/valuation commentary unrelated to user rights;
- generic financing round/valuation announcement when the user's mapped SPV/allocation/fees/rights did not change.

## Gate 6 — Rights relevance

For private-company/SPV/deal monitoring, distinguish:
- underlying-company news;
- user-facing deal-rights changes.

A company financing/valuation announcement is ACTION only when Tier B or mapped deal documentation shows a material effect on the user's own allocation, security, fees, conversion terms, transfer/redemption, settlement/distribution, or another stored right.

If no user-level effect is confirmed:
- record as research/background if useful;
- NO_ACTION in the TGE/rights notifier.

## Gate 7 — Delivery

Only after Gates 0-6 PASS:
1. persist event archive/stage state;
2. dedupe exact event key and Gmail subject;
3. send Gmail + ChatGPT;
4. Gmail Sent id + readback + event archive = delivered.

If delivery fails:
- persist PENDING_DELIVERY;
- retry delivery before evaluating a duplicate new alert;
- later NO_ACTION cannot erase pending delivery.

## Required audit fields for every candidate

- project_id
- candidate_source_url
- candidate_source_account/domain
- evidence_tier
- source_published_at
- source_updated_at
- event_effective_at
- event_deadline
- identity_match
- freshness_result
- user_known_state_result
- prior_event_key_match
- material_delta
- rights_relevance
- gate_result
- rejection_reason
- notification_decision

If a candidate cannot populate enough fields to pass safely, default is NO_ACTION / UNVERIFIED_CANDIDATE.
