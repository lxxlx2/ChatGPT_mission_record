# Crypto Monitoring Notification Policy

Updated: 2026-09-26 21:12 Asia/Bangkok
Status: canonical notification policy for the three existing Crypto automations

Destination:
- Gmail: lxx.run688@gmail.com
- ChatGPT: user-visible alert only when user action or a material portfolio/opportunity event requires attention

## Global rule

Default is **silent**.

Monitoring infrastructure problems are operational noise and are logged to GitHub only. They do **not** generate Gmail or ChatGPT alerts.

Do not email or notify for:
- missing final/final-retry audit;
- scheduler/persistence/runtime failure;
- source/tool/provider failure;
- required lane unavailable;
- cache/current-pointer write failure;
- recovered_warning;
- partial_success / partial_failure caused only by monitor infrastructure;
- normal no_update;
- unchanged known news;
- ordinary price snapshots;
- unchanged WATCH state.

The user receives notifications for **substantive crypto information**, not for the monitor's internal plumbing.

## Crypto Daily

Ordinary hourly collector:
- write GitHub research/audit;
- no Gmail;
- no user-visible ChatGPT reply.

09:00 formal daily:
- send the official Crypto Daily Gmail according to REPORT_SPEC / DELIVERY_RUNBOOK.

Do not send hourly emails for repeated known stories or for monitor-health problems.

A genuinely new major market/security development discovered by Crypto Daily is stored in research and may be surfaced by the $300 Mission only when it is relevant to an active position, stored rule or actionable opportunity state.

## Airdrop / TGE

Silent:
- NO_ACTION;
- checked_no_update;
- source_unavailable / monitoring failure;
- identity_fail without a verified user action.

Notify with **Gmail + ChatGPT** only for a new verified material ACTION that can affect the user's entitlement, eligibility, timing or ability to participate, including:
- claim opens/closes;
- KYC / registration / wallet-linking / signature/form deadline;
- snapshot / eligibility checker / allocation;
- TGE / token distribution;
- exchange listing or launch timing when materially actionable under the stored monitor scope;
- material tokenomics / eligibility change that requires review.

Do not notify merely because a source failed.

## $300 Mission

Silent:
- unchanged position state;
- ordinary volatility;
- monitoring/runtime/provider errors;
- cache/audit failures;
- optional enrichment unavailable.

Notify with **Gmail + ChatGPT** only for a new material portfolio/opportunity event already within stored rules:
- stored stop/TP/event threshold crossed;
- ETH stored setup becomes qualified;
- new/materially changed WATCH that could merit user review;
- Monster IGNITION / relevant EXHAUSTION state transition;
- material wallet balance anomaly involving real assets;
- material security/solvency/deadline event affecting an active holding or reserved participation;
- a verified launch/NFT/TGE opportunity state that materially changes participation timing;
- 19:29 Monster factual daily summary.

## Deduplication

For substantive alerts, use a stable event key:
`<task>-<project/asset>-<event-type>-<event-version/date>`

Before sending, check prior event/audit state and Gmail Sent when practical.

Do not repeatedly send the same substantive fact unless:
- the event materially changes;
- a threshold transitions to a new state;
- a new deadline/action appears.

## User-visible task response

When no substantive alert is required, final user-visible output must be empty.

GitHub remains the audit trail for monitoring health, failures, retries and recoveries.
