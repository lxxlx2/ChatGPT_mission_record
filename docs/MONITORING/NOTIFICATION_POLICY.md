# Crypto Monitoring Notification Policy

Updated: 2026-09-26 21:05 Asia/Bangkok
Status: canonical notification policy for the three existing Crypto automations

Destination:
- Gmail: lxx.run688@gmail.com
- ChatGPT: user-visible alert in the same task conversation when an alert is required

## Global rules

Default is **silent**.

Routine successful runs, ordinary market snapshots, unchanged known news, unchanged WATCH state, NO_ACTION and recovered warnings do not send Gmail and do not produce a user-visible ChatGPT message.

GitHub persistence remains the normal record for healthy hourly work.

A notification is sent only for a new alert-worthy state.

## Monitor health alerts

Send **Gmail + ChatGPT** for a new monitor-health incident:
- a scheduled run has no final/final-retry audit;
- a required lane remains unavailable after fallback;
- a required research/report/event write fails;
- a Gmail delivery required by the task fails;
- a run is failed or partial_failure because of a real coverage/persistence gap;
- repeated partial_success leaves a real monitoring-coverage gap.

Do not alert for:
- recovered_warning;
- optional enrichment unavailable;
- cache/current-pointer write failure when final audit and required lanes succeeded;
- normal no_update.

### Health alert dedupe

Each incident gets a stable incident key:
`<task>-<failure-class>-<first-detected-local-hour>`

Before sending, search Gmail Sent for:
`[Crypto监控异常][<task>][<incident-key>]`

If that exact incident was already sent, do not resend it every hour.

When an emailed incident later recovers, send one recovery email:
`[Crypto监控恢复][<task>][<incident-key>]`

Then close the incident. No more mail unless a genuinely new incident appears.

## Crypto Daily

Ordinary hourly collector:
- GitHub research + final audit only;
- **no user-visible ChatGPT output**;
- **no Gmail**, even when research contains material but already-known market/security items.

09:00 formal daily:
- Gmail delivery as specified by REPORT_SPEC / DELIVERY_RUNBOOK.

Hourly monitor-health incident:
- Gmail + ChatGPT once per deduped incident.

Fresh research that affects an active Mission threshold/security rule is surfaced by the $300 Mission monitor, not by duplicate Crypto Daily hourly chatter.

## Airdrop / TGE

NO_ACTION / checked_no_update:
- silent.

Verified ACTION:
- Gmail + ChatGPT.

Monitor-health incident:
- Gmail + ChatGPT once per deduped incident.

## $300 Mission

Unchanged state:
- silent.

New stored-rule trigger:
- Gmail + ChatGPT.

Includes:
- stop/TP/event threshold crossing;
- ETH setup qualified;
- new/materially changed WATCH;
- Monster IGNITION / relevant EXHAUSTION;
- material active-position security/deadline event;
- wallet anomaly;
- MONITOR_HEALTH_GAP;
- MONITOR_LANE_FAILURE.

19:29 Monster factual daily summary:
- Gmail + ChatGPT once.

## User-visible task response

When no alert is required, the automation's final user-visible response must be empty.

The existence of research or an audit file is not itself a reason to notify the user.
