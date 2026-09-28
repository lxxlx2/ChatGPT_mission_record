# Crypto Daily Automatic Runtime

Updated: 2026-09-28 09:12 Asia/Bangkok
Timezone: Asia/Bangkok
Mode: FACTUAL_NEWS_COLLECTOR

Authority for the existing hourly Crypto Daily task.

## Audit

The only mandatory persistence artifact is:
`crypto-daily/runs/YYYY-MM-DD/HHMMSS-final.md`.

Do not require or attempt a start file in the automatic path. Older start files remain valid historical artifacts.

The final audit must include run time, automation id, lane status, research path, source/tool warnings and final run status.

## Ordinary hour
1. core BTC/ETH/SOL + liquid-outlier + major security/exchange/protocol factual scan;
2. one Bangkok-hour rotating shard;
3. write at most 8 material candidates to research;
4. create final audit.

Use supported per-symbol market calls when a multi-symbol endpoint rejects the request. Do not repeat a known-invalid request shape.

## 09:00 / 10:00 / 11:00
09:00 delivery first. 10:00 and 11:00 recovery first.
Read REPORT_SPEC.md and DELIVERY_RUNBOOK.md only in these windows.
Deduplicate before Gmail.

## Status classification
- no material update = healthy;
- an initial request/write error that is fully recovered with equivalent coverage becomes recovered_warning;
- recovered_warning does not downgrade a complete run;
- partial_success / partial_failure only when a real data, persistence or delivery gap remains;
- temporary failures never disable or pause the task;
- no Chinese-language websites as evidence.


## Final persistence fallback

The ordinary-hour research file is durable evidence that collection occurred, but the run still attempts a final audit.

After research is written:
1. try `runs/YYYY-MM-DD/HHMMSS-final.md`;
2. if create fails, fetch that exact path;
3. if the path exists, update it using the fresh SHA;
4. if it does not exist or update is blocked, create one compact retry file:
   `HHMMSS-final-retry.md`.

Do not perform optional work after research write and before final persistence.

A successful research write plus successful final/final-retry = success.
If research exists but both final writes fail, the next run records the previous cycle as `audit_gap_recovered` and continues.


## Notification behavior

Use `docs/MONITORING/NOTIFICATION_POLICY.md`.

Ordinary hourly collection is fully silent:
- persist research;
- persist final/final-retry audit;
- return an empty user-visible response;
- do not send Gmail.

Monitoring/runtime/source/persistence problems are also GitHub-only and do not notify the user.

Only the 09:00 formal daily uses Gmail under REPORT_SPEC / DELIVERY_RUNBOOK.

Do not notify merely because an already-known market/security item remains material.


## Delivery fallback scheduler — 2026-09-27

The hourly collector remains the primary 09:00 publisher. The existing dedicated automation `Crypto 09:00 日报发布` is enabled as an idempotent delivery-only fallback at 09:10, 10:10 and 11:10 Asia/Bangkok.

Reason: on 2026-09-27 the 09:00 and later hourly recovery attempts completed research and QA but Gmail send was rejected repeatedly, leaving no delivered report until manual recovery.

Rules:
1. 09:00 hourly task checks Gmail Sent + official GitHub report before any expensive work.
2. If report is missing, build/QA the exact final body and attempt Gmail first.
3. If Gmail send fails after one normal retry, persist the exact QA-approved body to:
   `crypto-daily/delivery-pending/YYYY-MM-DD.md`
   plus the failure audit. Do not repeatedly regenerate different bodies.
4. The 09:10/10:10/11:10 fallback checks Gmail Sent and official GitHub report first.
5. If Gmail is missing and a pending body exists, send that exact body, read it back, archive it as the official report, then remove no history; the pending file remains audit evidence.
6. If Gmail exists but GitHub report is missing, reconstruct the official report from Gmail readback only.
7. If both sides exist, exit silently.
8. Never send more than one normal daily report for the same Bangkok date.
9. A provider/tool rejection is a delivery failure, not a reason to disable either automation.

At 11:10, if delivery still fails, persist a final delivery-failure audit. The next ordinary hourly collector must keep checking delivery state before normal collection until the same-date report is delivered or the date changes.


## Collector-survival override — 2026-09-27

Observed persistence gaps remain in ordinary collector hours, including a scheduler trigger around 12:00 with no automatic research/final artifact. Reliability therefore takes precedence over exhaustive hourly breadth.

### Attempt audit first

Every hourly run starts by creating:
`crypto-daily/runs/YYYY-MM-DD/HHMMSS-attempt.md`

Minimum:
- run_time
- automation_id
- mode
- status: started

This is diagnostic only. Final/final-retry remains completion proof.

### Bounded pre-final collector

For ordinary hours, complete only these pre-final lanes:
1. BTC/ETH/SOL and bounded liquid-outlier facts using per-symbol calls;
2. one bounded English discovery pass covering security/exchange/protocol + the current rotating shard, with X/Reddit included when available;
3. write one compact research file, or embed a compact research payload in final if research write fails;
4. immediately persist final/final-retry.

A source failure in one lane does not cancel the others.
Do not retry a failed source more than once before final.
Do not perform exhaustive multi-source cause research before final persistence.

After final exists, optional deeper X/Reddit/cause/cross-chain/NFT enrichment may write additional research, but its failure cannot erase the completed core audit.

### Publisher windows

At 09:00:
- attempt audit first;
- delivery dedupe and formal delivery take priority over fresh broad collection;
- if Gmail fails, persist the approved pending body and final audit.

At 10:00/11:00:
- recovery first;
- ordinary collector only after delivery state is resolved or a pending body/failure audit is safely persisted.

### Status

- core facts + final persisted, optional gaps only: success or recovered_warning.
- one core data lane unavailable but final persisted: partial_success.
- no meaningful core data and final persisted: partial_failure.
- no final/final-retry: scheduler persistence failure.

Never leave an ordinary scheduler trigger without at least an attempt file unless GitHub itself was unreachable.


## Security coverage receipts — 2026-09-27

Read and follow `crypto-daily/SECURITY_SOURCE_POLICY.md`.

The security lane may not be summarized as `checked_no_update` from a generic bounded search alone.

Every automatic run must persist source-level security receipts for the source families actually attempted. At minimum record:
- source/account/domain;
- query/page;
- candidate / no_update / unavailable;
- checked_at.

If X, Reddit or a specialist feed was not actually retrieved, mark it unavailable. Never convert an unavailable source into `checked_no_update`.

Run a bounded brand-impersonation query pack for currently launching/trending exchange/chain/wallet brands. Terms include scam, phishing, impersonation, fake token, fake chain, fake app and compromised.

The 09:00 publisher must inspect previous-24h receipt coverage and run a fresh security verification pack before Chapter 9.

No claim of global completeness is allowed. Report coverage ratio/gaps in the internal audit and state only what was found in the covered sources.


## Private-market deal lifecycle — 2026-09-28

The primary-market lane must include user-relevant deal hosts, not only underlying companies.

Explicit discovery sources include:
- Echo / @echodotxyz;
- known Echo syndicate/group-lead notices such as Alpen Capital when publicly retrievable;
- Legion;
- CoinList;
- Republic / RepublicX;
- other canonical deal platforms already represented in user-relevant research.

Material events:
- full/partial refund;
- cancellation / failed close;
- allocation change;
- SPV/issuer/structure change;
- SAFE/equity/token-warrant conversion change;
- settlement/distribution;
- secondary/transfer/redemption window;
- material valuation/fee/term change.

Humans& / Echo is a regression case. On 2026-09-24 a direct Echo/Alpen notice gave the user a full 1,000-USDC refund into the Echo wallet. Future platform-level rights events must be surfaced even if the portfolio company itself publishes nothing.

Do not treat 'company official source unchanged' as evidence that the investor's deal rights are unchanged.
