# 2026-09-28 monitoring and delivery audit

timezone: Asia/Bangkok
status: confirmed_delivery_and_coverage_failures

## Daily delivery state at 09:04

Gmail Sent:
- Crypto Daily Brief｜2026-09-28: missing
- 美股每日晨报｜2026-09-28: missing
- no Sep-28 sent message from the monitored report workflows

Crypto Daily:
- scheduler metadata advanced near 09:00;
- no Sep-28 official report;
- no delivery-pending body;
- no 09:00 durable publisher audit;
- earlier collector research directory was absent because research writes repeatedly failed.

US Stock Daily:
- 08:00 and 09:00 scheduler metadata advanced;
- no Sep-28 run directory;
- no Sep-28 official report;
- no Gmail.
This is an execution/persistence failure before durable audit.

## Other monitor health

Airdrop/TGE:
- Sep-28 contains attempt files only and no normal final/final-retry completion evidence;
- therefore silence cannot be interpreted as 'no events';
- one attempt carries a future-looking 15:15 timestamp relative to the 09:04 audit time and is not accepted as evidence of a real completed run.

$300 Mission:
- multiple final/final-retry artifacts exist;
- several runs are partial_success with wallet lane unavailable;
- PONS did not cross stored 0.498 stop or 0.668/0.704/0.739 TP thresholds in sampled completed runs, so no position alert was warranted from those facts;
- Sep-27 19:29 Monster summary did not produce a completion artifact or Gmail and is a missed scheduled summary.

## Humans& / Echo regression

Known user exposure:
- humans& via Echo, 1,000 USDC.

On 2026-09-24 the user provided direct Echo evidence that Alpen Capital processed a full 1,000-USDC refund to the user's Echo wallet.

The TGE/rights monitor did include humans& in the whitelist on Sep-24, but its completed scans relied on underlying-project first-party sources and explicitly rejected items without project-level first-party evidence. It did not include Echo/Alpen as a rights-source layer.

Root cause:
- source model was project-centric instead of entitlement/deal-channel-centric;
- refund/cancellation from a syndicate/platform could be invisible when the underlying company made no public announcement.

Remediation:
- REGISTRY now maps humans& -> Echo / Alpen Capital;
- deal-host refunds/cancellations/allocation/settlement changes are ACTION-class rights events;
- TGE runtime now creates a provisional durable final before bounded work;
- Crypto Daily now has an explicit private-market deal lifecycle lane.
