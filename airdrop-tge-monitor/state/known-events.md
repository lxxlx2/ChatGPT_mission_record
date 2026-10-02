# TGE / Airdrop Known User State

Updated: 2026-10-02 Asia/Bangkok

Purpose: durable dedupe/state input for events already known, delivered, completed, refunded, explicitly closed, user-suppressed, or explicitly scheduled by the user within the existing rights monitor. This file is an input to ACTION_GATE.md.

Hard scope rule: do not create a new monitor/task/file for a user-specific future action. If the user explicitly gives a date/time for an action already within this existing rights-monitor scope, record it here as an unresolved known event so the existing monitor can act on it. No new monitoring scope may be added without explicit user authorization.

## CLOSED / no remaining rights

### humans&
- project_id: humansand
- state: CLOSED_FULLY_REFUNDED
- effective_date: 2026-09-24
- source_type: user_confirmed + stored deal history
- remaining_entitlement: none known
- monitor_action: suppress unless user explicitly re-enters a new exposure

## Completed / suppress

### UNICRED #230 unstake/unlock
- event_key: unicred:unstake_unlock:230:2026-10-01
- state: COMPLETED_NO_REMAINING_ACTION
- effective_date: 2026-10-01
- source_type: user_confirmed
- remaining_entitlement: no unresolved unstake/unlock action known
- monitor_action: suppress; do not send T-24h/T-2h/overdue or backfill reminders

### Concrete CT claim-open
- event_key: concrete:ct_claim_open:2026-09-30
- state: USER_SUPPRESSED_STALE_ALERT
- effective_date: 2026-10-02
- source_type: user_confirmed feedback after late alert
- delivery_status: delivered_late_then_suppressed
- gmail_message_id: 1a0fb623103c8948
- reason: claim had already been live for many hours before the monitor notified; user explicitly requested this stale claim-open alert be removed
- monitor_action: suppress unchanged CT claim-open reminders permanently; only a genuinely new Tier A material delta may be evaluated under ACTION_GATE, and late discovery cannot itself become ACTION

## Delivered / known event keys

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
