# TGE / Airdrop Known User State

Updated: 2026-10-08 Asia/Bangkok

Purpose: durable dedupe/state input for events already known, delivered, completed, refunded, explicitly closed, user-suppressed, or explicitly scheduled by the user within the existing rights monitor. This file is an input to ACTION_GATE.md.

Hard scope rule: do not create a new monitor/task/file for a user-specific future action. If the user explicitly gives a date/time for an action already within this existing rights-monitor scope, record it here as an unresolved known event so the existing monitor can act on it. No new monitoring scope may be added without explicit user authorization.

## Merger-resolved TGE scope — historical / no active independent TGE

### Loopscale / Orca / Formation
- event_key: formation:orca_loopscale_merger:2026-10-08
- project_ids: loopscale, orca, formation
- evidence: issuer-level merger announcement; combined entity is Formation; ORCA/xORCA remain the stated token network
- confirmed_first_party: https://www.prnewswire.com/news-releases/orca-and-loopscale-merge-to-build-capital-markets-for-ai-and-the-frontier-economy-302901726.html
- independent_loopscale_tge: NOT_CONFIRMED
- new_formation_token: NOT_ANNOUNCED
- orca_or_xorca_tge: ALREADY_EXISTING_TOKEN; NOT_NEW_TGE
- delivery_status: NO_TGE_ACTION; NO_GMAIL
- user_rights: no verified new entitlement/claim/airdrop from this merger; personal holdings/entitlements not established
- monitor_action: SUPPRESS_INDEPENDENT_TGE_DISCOVERY; remove Loopscale from Shard 1, do not add Orca or Formation. Maintain history for audit; do not create new automation. A separately proven new user right or fresh token launch requires new first-party evidence and explicit user direction.
- daily_lane: Crypto Daily Section 6 (merger + ORCA tokenholder governance), not TGE Section 7
- current_governance: proposal not proven passed; vote ends 2026-10-10 19:42 UTC, cooldown ends 2026-10-12 19:42 UTC; do not assert enactment

## CLOSED / no remaining rights

### humans&
- project_id: humansand
- state: CLOSED_FULLY_REFUNDED
- effective_date: 2026-09-24
- source_type: user_confirmed + stored deal history
- remaining_entitlement: none known
- monitor_action: suppress unless user explicitly re-enters a new exposure

## User-suppressed / excluded from active monitoring

### Abstract / ABS
- project_id: abstract
- state: USER_SUPPRESSED
- effective_date: 2026-10-07
- source_type: user_confirmed
- remaining_entitlement: not evaluated; user explicitly requested removal from TGE monitoring
- monitor_action: suppress Abstract / @AbstractChain / ABS from active discovery and notifications; reactivate only on explicit user request

## Completed / suppress

### UNICRED #230 unstake/unlock
- event_key: unicred:unstake_unlock:230:2026-10-01
- state: COMPLETED_NO_REMAINING_ACTION
- effective_date: 2026-10-01
- source_type: user_confirmed
- remaining_entitlement: no unresolved unstake/unlock action known
- monitor_action: suppress; do not send T-24h/T-2h/overdue or backfill reminders

## Delivered / known event keys

### Concrete CT claim-open
- event_key: concrete:ct_claim_open:2026-09-30
- delivery_status: delivered_once_late_discovery
- gmail_message_id: 1a0fb623103c8948
- user_policy: one notification is acceptable even if first discovery is late, provided Tier A/B confirms the action is still current/open and plausibly relevant
- repeat_policy: suppress unchanged CT claim-open reminders after this delivery; only a genuinely new Tier A/B material delta may re-alert

### HEEBOO claim open
- event_key: heeboo:claim_open:2026-09-10
- delivery_status: delivered
- gmail_message_id: 1a087e5f1a908034
- repeat_policy: suppress unchanged claim-open reminders

### Reflect USDC+ recovery claim
- event_key: reflect:recovery_claim_open:2026-09-12
- delivery_status: delivered
- gmail_message_id: 1a09250f1088fcc6
- repeat_policy: suppress unchanged recovery-portal reminders

### Surf Season 1 referral rewards claim
- event_key: surf:season1_referral_claim_open:2026-09-12
- delivery_status: delivered
- gmail_message_id: 1a09260ad0c0ca4
- repeat_policy: suppress unchanged claim reminders

### MetaMask Money Sweepstakes registration
- event_key: metamask:money_sweepstakes_registration:2026-09-17
- delivery_status: delivered
- gmail_message_id: 1a0b836c33c1039f
- note: two GitHub archives exist for the same Gmail message; this is one logical delivered event
- repeat_policy: suppress unchanged reminders; only deadline/eligibility/rules material delta may re-alert

### Cambria RSGP Genesis opt-in
- event_key: cambria:rsgp_genesis_opt_in:2026-09-30
- delivery_status: delivered_recovery
- gmail_message_id: 1a0e149fa6d9718a
- repeat_policy: suppress unchanged reminder; new official extension/reopen may alert once

## Historical-only / no current ACTION baseline

### Crusoe Series F valuation
- event_key: crusoe:series_f_valuation:2026-09-17
- delivery_status: delivered_historical
- rights_effect_confirmed: false
- current_policy_reclassification: background_only_unless_mapped_spv_terms_change
- repeat_policy: suppress generic valuation/funding repeats
