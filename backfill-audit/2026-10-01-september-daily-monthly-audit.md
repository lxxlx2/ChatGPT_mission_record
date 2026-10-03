# 2026-10-01 September Daily / Monthly Audit

Timezone: Asia/Bangkok
Audit scope: September 2026 Crypto Daily + US Stock Daily canonical archives, Gmail authoritative delivery records, monthly-report capability, and September monthly-report recovery.

## 1. September daily archive completeness

### Crypto Daily

- Expected dates: 2026-09-01 through 2026-09-30 inclusive.
- Current Git canonical coverage: **30 / 30**.
- No missing September daily date was found in the canonical directory during this audit.

### US Stock Daily

- Expected dates: 2026-09-01 through 2026-09-30 inclusive.
- Initial Git canonical coverage found by this audit: **29 / 30**.
- Missing date: `2026-09-15`.
- Gmail authoritative source found:
  - subject: `美股每日晨报｜2026-09-15｜10年美债突破5%，AI硬件急跌，软件反向轮动与能源供给风险并行`
  - Gmail message id: `1a0a2935489872db`
- The exact Gmail readback body was backfilled to:
  - `us-stock-daily/reports/daily/2026/2026-09/2026-09-15.md`
  - repair commit: `afbb11ba36d4314fd92552d29bfc47c5a4fba7ad`
- Current Git canonical coverage after repair: **30 / 30**.

## 2. Authoritative revision-chain spot checks

The audit also checked representative dates with corrections / formal resends to ensure the Git canonical pointed at the intended authoritative version rather than blindly counting every sent email as a separate day.

Examples checked:

### Crypto
- 2026-09-04: corrected/final version retained as canonical.
- 2026-09-21: correction version retained as canonical.
- 2026-09-29: formal resend retained as canonical and prior versions treated as superseded history.

### US Stock
- 2026-09-04: final corrected V2 retained as canonical.
- 2026-09-21: corrected version retained as canonical.
- 2026-09-26: later authoritative version retained with superseded metadata.
- 2026-09-29: formal resend retained as canonical.

This is a targeted revision-chain audit, not a claim that every sentence in every historical email was independently re-fact-checked on 2026-10-01.

## 3. Historical content-quality debt

Archive completeness and content quality are separate.

Some September authoritative emails were correctly archived from Gmail but contain user-visible operational/meta prose that would fail the current report-quality rules. A clear example is the 2026-09-29 US Stock report, whose visible section 11 discussed automatic-delivery failure, Gmail/readback/GitHub recovery, and resend mechanics.

Policy after this audit:

- Historical Gmail-derived canonical bodies remain immutable audit records; do not silently rewrite what was actually sent.
- Monthly synthesis must ignore scheduler/Gmail/GitHub/recovery/prebuild/pending/canonical/QA prose, empty-section explanations, and other monitoring/editorial plumbing.
- New daily reports are subject to the current hard pre-send lint and must not include this operational prose.

## 4. Monthly-report capability regression

Monthly reporting was an existing capability, not a new monitoring task.

Evidence before repair:

- Crypto canonical spec already defined a formal monthly archive and required the first-day daily publisher run to prepare the previous calendar month's long-term investment report.
- `crypto-daily/reports/monthly/2026/2026-08.md` exists and records Gmail delivery on 2026-09-01.
- `us-stock-daily/reports/monthly/2026/2026-08.md` also exists and records Gmail delivery on 2026-09-01.

Regression found:

- Later automation-prompt revisions no longer contained the monthly-report execution logic.
- The current US Stock `REPORT_SPEC.md` also lacked an explicit monthly contract even though an August monthly report existed.

Repairs made on 2026-10-01:

- Restored monthly-report logic inside the existing `Crypto 每日情报` automation; no new automation created.
- Restored monthly-report logic inside the existing `美股每日晨报` automation; no new automation created.
- Added a monthly source-completeness gate: every prior-month date must resolve to one authoritative final/corrected/formal-resend body before the monthly email may send.
- Added same-day supersession handling so corrected/resend emails are not double-counted.
- Added a monthly synthesis rule excluding monitoring plumbing from market evidence.
- Added explicit investment recommendation fields: tier, price/valuation context, 1–5 year thesis, 6–12 month catalysts, risks, invalidation, preferred entry, and portfolio role.
- US Stock canonical monthly-contract repair commit: `619506c0294771dd8d7d500d1ddbde57b5bbffa8`.

## 5. September monthly reports recovered

### Crypto September monthly report

Authoritative final correction:

- subject: `Crypto Monthly Investment Report｜2026-09｜长期机会与投递清单｜最终修正版`
- Gmail message id: `1a0f8388da681a81`
- Git path: `crypto-daily/reports/monthly/2026/2026-09.md`
- Git final-correction commit: `e2a572049d5576338b3066af4cf91851fa9df517`
- source manifest: 30/30 September daily canonical dates.

The earlier recovery email `1a0f8352080d83f5` is superseded because its user-visible introduction still exposed internal canonical/source-process wording.

### US Stock September monthly report

Authoritative final correction:

- subject: `月度长期投资报告｜2026-09｜长期股票、IPO与项目机会｜最终修正版`
- Gmail message id: `1a0f8390e3fa9b0d`
- Git path: `us-stock-daily/reports/monthly/2026/2026-09.md`
- Git final-correction commit: `4574d6c9538b9ba5a873d4af8f5dae4402d76c92`
- source manifest: 30/30 September daily canonical dates after the 2026-09-15 Gmail backfill.

The earlier recovery email `1a0f835ff6832cc3` is superseded because its user-visible introduction still exposed internal canonical/Git-backfill wording.

## 6. Current monthly execution contract

On the first Asia/Bangkok calendar day of a month:

1. The normal daily report remains first priority.
2. The same existing daily automation builds a previous-month source manifest.
3. Git missing dates must be reconciled against Gmail Sent authoritative versions before synthesis.
4. Any unresolved date produces `MONTHLY_SOURCE_GAP` and blocks the monthly send.
5. If complete, the previous natural month's daily evidence is aggregated into a direction / regime / investment report rather than concatenated.
6. Monthly recommendations must include explicit entry/invalidation/risk/portfolio-role fields.
7. Before sending, search Gmail Sent for the exact monthly subject and deduplicate.
8. Gmail Sent + readback is delivery authority.
9. The exact final Gmail body is archived to the corresponding monthly Git path and read back.

No separate monthly automation was created.

## 7. Verification status

- September daily source completeness: repaired and currently **30/30 Crypto + 30/30 US Stock**.
- September monthly reports: manually recovered, Gmail readback verified, Git monthly canonical written.
- Automation prompt contract: monthly logic restored in both existing daily tasks.
- Future automatic first-day monthly execution: contract repaired but the next fully automatic month-boundary run has not yet occurred; it must be judged by actual Gmail Sent/readback + Git monthly archive evidence, not by prompt text alone.
