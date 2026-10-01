# User Rights / Action Calendar

Updated: 2026-10-01 Asia/Bangkok
Timezone: Asia/Bangkok

Purpose: durable source of truth for user-specific date-sensitive actions that must not live only in chat memory. The airdrop/TGE/rights monitor must read this file before discovery on every run.

## Operating rules

- Any user-confirmed future claim, unstake, vesting unlock, refund deadline, opt-in deadline, NFT unlock, settlement or other date-sensitive rights action must be registered here when the date/time is known.
- Each entry must include: event_key, project/asset, action, due_at_bkk (or explicit date window), status, source_type, and delivery/reminder state.
- Default reminder windows for unresolved entries are the first monitor run inside T-24h and T-2h. If an unresolved due time passes, allow one overdue reminder. Deduplicate by event_key + reminder_window.
- Completed/cancelled events are never backfilled as reminders; mark status and suppress unchanged repeats.
- Portfolio ownership alone does not create a date; do not invent due times. But material portfolio/NFT positions must be cross-checked against this calendar so known date-sensitive rights cannot fall out of scope.

## Incident record

### UNICRED #230 unstake / unlock reminder
- event_key: unicred:230:unstake_unlock:2026-10-01
- project_asset: UNICRED #230 / Unichain
- action: unstake / unlock NFT when eligible
- due_at_bkk: 2026-10-01 (exact time was not durably registered)
- status: COMPLETED_BY_USER_AFTER_MISSED_REMINDER
- source_type: user-confirmed prior chat instruction + current completion confirmation
- reminder_expected: yes
- reminder_delivered: no
- backfill: forbidden
- root_cause: event existed only in conversational context and was never written into durable registry/calendar, so the scheduled rights monitor had no event key or due time to evaluate
- remediation: future date-sensitive user rights must be registered here immediately; the rights monitor must read this file before project discovery

## Active unresolved entries

- none currently registered in this calendar

