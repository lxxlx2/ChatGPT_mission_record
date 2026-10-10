# Crypto Daily Automatic Runtime

Updated: 2026-09-28 19:34 Asia/Bangkok
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

Closed/refunded deals are excluded from user-specific deal monitoring. humans& via Echo/Alpen Capital was fully refunded on 2026-09-24, so it is historical only and must not consume ongoing user-specific monitoring unless the user re-enters the deal.

Do not treat 'company official source unchanged' as evidence that the investor's deal rights are unchanged.


## 09:00 on-time delivery override — 2026-09-28

Observed delivery history:
- 2026-09-26: ~09:17
- 2026-09-27: ~12:08 manual recovery
- 2026-09-28: ~09:16 manual recovery

This is not acceptable as normal operation.

### 08:00 prebuild

The 08:00 hourly collector must additionally prepare:
`crypto-daily/delivery-pending/YYYY-MM-DD.md`

The pending body is a complete QA-able daily draft assembled from:
- prior 24h research/finals;
- current BTC/ETH/SOL facts;
- current highest-priority security/exchange/protocol facts;
- active private-market rights lifecycle;
- current TGE/action carry-forward.

Do not send at 08:00.

The purpose is to make 09:00 a delivery operation, not a long research operation.

### 09:00 delivery first

At the 09:00 run:
1. check Gmail Sent exact subject;
2. if already delivered, do not duplicate;
3. if not delivered, read the pending body first;
4. refresh only time-sensitive top-line facts needed for correctness;
5. send Gmail before optional enrichment;
6. read back Gmail;
7. archive identical official report;
8. only then continue ordinary collector work.

A non-critical source being unavailable is not a reason to delay the report. State the gap explicitly.

Target: official Gmail sent by **09:10 Asia/Bangkok**.

### Recovery

The dedicated fallback remains idempotent. If 09:00 did not produce Gmail proof, its next run sends the existing QA-approved pending/report body before any new research.

Do not regenerate a longer report while a valid pending body already exists.

### Security source rotation

Ordinary hourly runs no longer need every specialist security family in every hour.

Each hour:
- run one broad breaking-security / impersonation discovery pass;
- check official source for any candidate;
- rotate specialist source families so full specialist coverage is restored within a 3-hour window; the major-CEX account-security fast lane still runs every hour.

At 08:00/09:00 daily preparation, aggregate the previous 24h receipts and fresh-verify all carried material candidates.

This is intended to improve real coverage and reduce timeout/provider-safety failures, not lower evidence standards.

## Major-CEX security fast lane and lifecycle dedupe — 2026-09-29

Read and obey the latest SECURITY_SOURCE_POLICY.md on every run.

Every ordinary hourly collector must execute one bounded major-CEX account-security discovery pass before optional enrichment. This fast lane is mandatory even when X/Reddit/specialist feeds are unavailable.

Coverage must include Binance, Coinbase, OKX, Bybit, MEXC, Bitget, Kraken, Gate, HTX and KuCoin with account-takeover / unauthorized-withdrawal / API / KYC-reset / deepfake / compensation / resolution terms. MEXC, Bitget and any exchange with an open incident receive a direct focused query until the incident is resolved.

If a material CEX security candidate appears, verify with official support/exchange statements when available plus independent English evidence. Record incident lifecycle state and material deltas.

Do not repeat unchanged security conclusions. Re-surface an incident only for a material lifecycle transition such as official acknowledgement, changed loss amount, confirmed root cause, new victims/systemic evidence, compensation/reimbursement confirmation or official resolution. Critical unresolved incidents may be carried forward as one concise ongoing/no-material-change line.

Hourly freshness target is the next successful scheduled cycle after an incident becomes searchable. External indexing/provider outages can delay discovery; the audit must record source availability rather than claim real-time completeness.


## Formal resend / correction completeness — 2026-09-29

Any user-facing resend, recovery resend, correction, or superseding Crypto Daily edition MUST contain the complete REPORT_SPEC fixed 13-section formal report. A short patch, abbreviated digest, or security-only supplement cannot replace the final formal daily report when the user asks for a resend/correction of the daily report.

For every formal resend:
1. read the latest REPORT_SPEC and the most recent complete formal report;
2. aggregate the same required 24h inputs as normal formal delivery, including security carry-forward and active private-market rights;
3. refresh material time-sensitive market/security facts;
4. render all 13 fixed sections in order;
5. Gmail send + readback;
6. archive the exact Gmail body to the canonical daily GitHub path;
7. GitHub readback and body-equality check;
8. mark earlier incomplete/superseded versions in metadata.

GitHub failure must not cause an abbreviated Gmail. A short correction notice may exist only in addition to, not in place of, a complete formal resend when the user requests the full daily report again.


## Daily input manifest + acceptance gate — 2026-09-29

This section overrides any older survival/recovery wording that could allow a structurally complete but semantically starved report to be published.

Every 08:00/09:00/10:00/11:00 daily-report path reads:
- `REPORT_SPEC.md`
- `REPORT_ACCEPTANCE.md`
- `SECURITY_SOURCE_POLICY.md`
- current TGE canonical state when relevant

### 08:00 input manifest

Create:
`crypto-daily/delivery-manifest/YYYY-MM-DD.md`

The manifest must enumerate the prior 24h coverage:
- hourly research/final artifacts present;
- missing scheduler hours;
- BTC/ETH/SOL + liquid outlier market coverage;
- derivatives/market-structure coverage;
- security source receipts and carried candidates;
- major-CEX account-security fast-lane coverage;
- TGE/claim/rights material state;
- institutional/ETF/whale/exchange-flow coverage;
- protocol/infrastructure/ecosystem coverage;
- Early/Meme/NFT discovery coverage;
- macro/cross-market coverage;
- active private-market rights coverage;
- source/provider gaps;
- trailing-5 complete report body-length median;
- trailing-5 numbered-item median;
- draft body length/item count;
- CR-01..CR-18 result;
- `qa_status: PASS|FAIL`.

A missing lane is recorded as a gap. It may not be converted into “no update/no opportunity”.

The full 13-section pending body is READY only after manifest QA PASS.

### 09:00 primary delivery

Read the QA-PASS pending body first.
Refresh only time-sensitive facts and any material event that changed after 08:00.
Rerun CR-01..CR-18 after refresh.

If a hard gate fails:
- repair the missing lane/section;
- preserve the complete-report contract;
- do not send a shortened fallback merely to hit 09:10.

### Recovery windows

09:10/10:00/10:10/11:00/11:10 recovery may send only a QA-PASS full 13-section canonical body.

A short patch/supplement can never satisfy missing formal delivery.
If Gmail already contains the complete official body and GitHub is missing, archive-only recovery is mandatory.

### Hourly collector contract

Operational survival still matters, but the hourly final must state which mandatory daily lanes were actually covered versus unavailable.
Optional enrichment failure cannot erase completed work, but it also cannot be silently treated as successful coverage for the daily manifest.

### Formal success

The formal daily is fully DELIVERED only after:
- Gmail Sent id;
- Gmail readback;
- canonical GitHub archive;
- GitHub readback;
- exact body equality after metadata stripping.

Gmail-success/GitHub-failure is archive-pending, not a reason to resend.

## Single-write collector / delivery override — 2026-09-29 16:54 Asia/Bangkok

This section supersedes earlier attempt-first and separate research-write wording when it conflicts.

Ordinary hourly collector:
- do not create an attempt file;
- do not create a separate research file before final;
- run the bounded mandatory lanes in memory;
- make one GitHub mutation only: `runs/YYYY-MM-DD/HHMMSS-final.md`;
- embed compact research payload, mandatory-lane coverage, source receipts, gaps and run_status in that final;
- if the one final write is blocked, do not retry another mutation in the same cycle; the next cycle records the prior audit gap.

08:00 prebuild:
- build manifest + complete 13-section body + CR-01..CR-18 in memory;
- after QA PASS, make at most one GitHub mutation to `delivery-pending/YYYY-MM-DD.md`;
- the manifest summary may be embedded in the pending document;
- pending-write failure does not authorize a shortened 09:00 report.

09:00 formal delivery:
- dedupe Gmail Sent and canonical GitHub report first;
- produce/read a QA-PASS complete 13-section body;
- Gmail send + readback comes before GitHub;
- after Gmail success, make one GitHub mutation for the canonical report body;
- do not write a separate run audit in the same delivery cycle;
- Gmail success + GitHub failure is archive-pending; never resend solely for archive failure;
- if Gmail send itself is blocked, stop repeated send attempts and let 10:00/11:00 recovery retry the same complete-report duty.

10:00/11:00:
- recover only the missing side;
- no digest/patch may substitute for the complete formal report.

No monitoring task may be created, deleted, disabled or rebuilt as part of this repair.



## Durable-first daily-delivery patch — 2026-09-30

Observed on 2026-09-30: durable hourly finals existed earlier in the night, but later scheduled triggers did not leave final artifacts, and the 08:00 pending file was absent. Scheduler invocation is therefore not completion proof.

Current contract for the existing hourly task:
- ordinary hours: bounded factual collection; write an attempt early and persist final immediately after core lanes, before optional enrichment;
- 08:00: PREBUILD FIRST. Build the complete 13-section pending report from durable prior finals plus a small fresh core refresh before ordinary hourly work;
- 09:00: DELIVERY FIRST. Gmail Sent dedupe, pending read, refresh only time-sensitive facts, then send/readback before archive;
- 10:00/11:00: recovery only when the same-date Gmail/canonical side is missing;
- a missing pending at 09:00 triggers bounded recovery from durable finals + fresh core, not a broad full-market scan.

Completion evidence:
- ordinary cycle: final/final-retry artifact;
- daily delivery: Gmail Sent id + readback;
- archive success is separate from email delivery and must not cause duplicate mail.

## 2026-10-09 verified actual schedule and Gmail deliverability override (latest)

The single existing Crypto 每日情报 scheduler's actual Asia/Bangkok minute is :10, with hours 00/03/06/08/09/10/11/15/19/23. This is a clarification of existing schedule, not permission to change it. The current slot mapping is 08:10 full 13-section prebuild without Gmail; 09:10 formal primary; 10:10/11:10 recovery; all other slots bounded collector with terminal final/final-retry. Older :00 or hourly-language references elsewhere in this file are historical, not governing clock times.

The 2026-10-09 primary and recovery cycles had full report material and reported QA PASS but repeated Gmail execution-layer safety blocks. Manual official delivery succeeded at the same Asia/Bangkok date; Gmail id `1a1209d4664105f9`, exact archived official report path `crypto-daily/reports/daily/2026/2026-10/2026-10-09.md`. This is authoritative delivery proof; dedupe before any retry.

Operational priority remains: read latest canonical; pre-send manifest and fresh source verification; exact Gmail Sent dedupe; complete 13-section CR-01..19 QA; send full text/plain once through approved Gmail connector; readback; identical Git archive/readback; compact truthful terminal final. No smaller email, invented Sent proof, duplicate send, extra automation, title/schedule/scope change, or unverified global security completeness claim. When Gmail's provider safety checks block a send, record the explicit external blocker; do not claim to have bypassed or resolved platform restrictions. Use the next existing delivery/recovery slot to retry only after Sent dedupe. Prompt simplification is a bounded runtime improvement, not proof that the external safety block has been permanently eliminated.

## 2026-10-09 wallet-user-draining detection and collector-persistence override

- Ordinary collection already covers wallet security under REPORT_SPEC and SECURITY_SOURCE_POLICY. Add the **wallet_user_loss_fast_lane** receipt from that latest security policy to the existing bounded security pass; do not create a new scheduler, extra monitor or user-specific notification lane. An early wallet-drain lead remains an INTERNAL CANDIDATE until evidence warrants a labeled Section 9 report.
- First persist the scheduled attempt. Finish the core bounded security and market discovery, then write one terminal `HHMMSS-final.md` or, on write failure, one `-final-retry.md`. Never leave a scheduled collection hour with only an in-memory result; if safety checks block both writes, the next successful collector explicitly records that historical gap. Do not invent files or repair past timestamps by pretending a run completed.
- The receipt for the new existing-scope security check must include whether X/Reddit original posts were ACTUALLY retrieved or fell back to English indexed web/news, the researcher/issuer handles searched, and the timestamps/source URLs found. If no wallets/social specialist sources were read, the run cannot claim FULL security coverage.
- If a significant allegation becomes public AFTER the daily email, its first due collection is the next existing scheduled collector; do not call the earlier daily report an omission caused by a story that was not yet publicly available. For the 2026-10-09 Ledger rumor, the first heavily indexed English news was at approximately 19:30 BKK after the 19:20 manual report; the 19:10 slot has no final and is a separate scheduler/persistence defect. The next existing collection slot is 23:10 BKK, not a new monitor.
- When a source later confirms an issuer investigation, reseller action, root cause, or audited loss, record lifecycle delta under the stable event key `ledger:multiuser_wallet_drain:2026-10-09`. Do not conflate a customer's reported theft with manufacturer-wide compromise. This event key is for dedupe, not a new task or permanent individual-asset watch.

## 2026-10-10 national digital-economy policy discovery correction
In the ALREADY EXISTING policy/macro/chain-infrastructure slice of each bounded ordinary collector, query newly published national economic, digital-infrastructure, data-policy and blockchain-network policy from official English government/regulator pages, then corroborate with reputable English industry/finance reporting. This is a small bounded source check within current coverage, not a new alert type or separate tracker. Persist `national_policy_receipt` with source, publication timestamp, actual checked time and whether the policy text expressly supports the proposed blockchain clause; where the English official abstract lacks that clause, say so rather than falsely claiming firsthand verbatim verification. If no accessible source, record coverage gap. Do not infer new public-chain launches, easing of crypto bans or token beneficiaries without explicit primary evidence.

Regression reference: Oct 9 CPC/State Council policy and Oct 10 English national blockchain-network reports were absent from the Oct 10 23:14 collector final-retry. The next existing Crypto Daily report must reconcile this newly verified candidate through CR-08 and CR-18/19: a single Section 4 policy item (or Section 6 if more relevant), optional single-line Top5; no duplicate across sections. Evidence note: `crypto-daily/research/2026-10-10/china-national-blockchain-network-policy-triage.md`. Do not backdate successful collectors or send a duplicate Oct 10 daily. Current task name, hours, monitor scope and App-output silence stay unchanged.
