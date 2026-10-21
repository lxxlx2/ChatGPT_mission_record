# Crypto Daily Delivery Runbook

Updated: 2026-09-28 19:34 Asia/Bangkok
Timezone: Asia/Bangkok
> Active user-authorized schedule (2026-10-10): existing `Crypto 每日情报` at :20 Asia/Bangkok; 00:20/03:20/06:20/12:20/16:20/20:20 bounded collectors, 08:20 prebuild, 09:20 primary, 10:20/11:20 recovery. The old 09:00/10:00/11:00 and dedicated publisher text below is historical, not active. `COLLECTOR_SPEC.md` V2 + `REPORT_ACCEPTANCE.md` CR-20 govern discovery. No task or schedule change.


## Execution model

本 Runbook 由现有 `Crypto 每日情报` automation 在特定小时调用，不对应独立 scheduler。

- 09:00：主发布。
- 10:00：仅在当天日报不完整时恢复。
- 11:00：最后一次当日自动恢复。

其它小时不进入正式发布流程。

## Dedupe

每次发布/恢复前检查：
1. `crypto-daily/reports/daily/YYYY/YYYY-MM/YYYY-MM-DD.md`
2. Gmail Sent 中 subject = `Crypto Daily Brief｜YYYY-MM-DD`

若 official Gmail 已存在且 GitHub report 完整：
- 不重复发送；
- 当前小时继续按普通 collector 模式即可。

若 Gmail 已存在而 GitHub 缺失：
- 从 Gmail readback 恢复同一正文到 GitHub；
- 不重复发送 Gmail。

若 GitHub report 存在但 Gmail 不存在：
- 读取并 QA report；
- 合格后发送 Gmail；
- 回写 message_id。

## Delivery order

1. 聚合过去 24h research；若某小时 research 缺失但 final/final-retry 存在，也读取 final 中的 compact research payload / material candidates。
2. 建立 critical security carry-forward 清单，并逐项 fresh verification；任何需 revoke/patch/move/reclaim、>= $1M exposure/loss、或仍开放的钱包/approval/bridge/exchange漏洞不得静默丢失。
3. 对其余最高优先级事实做 fresh verification。
4. 生成 REPORT_SPEC 的固定 13 章。
5. QA。
6. **先发 Gmail**。
7. Gmail readback。
8. 写 GitHub official report。
9. GitHub readback。
10. finalize 当前小时 run audit，并记录 critical-security seen/included/omitted-with-reason。

GitHub archive 失败不得取消已经成功的 Gmail。

## Graceful degradation

非关键数据源失败时：
- 使用其余可靠英文/官方来源；
- 对缺失字段明确写“本轮未取得可靠数据”；
- 继续交付。

只有以下情况允许完全不发：
- 无法取得足够信息形成基本可靠报告；
- Gmail connector 不可用；
- QA 发现重大事实冲突且本轮无法消除。

## Recovery

09:00 失败后，10:00 自动检查当天是否缺报。
10:00 仍缺则重新尝试。
11:00 是最后一次当日自动恢复。

任何 recovery 都必须先 dedupe，正常情况下同一天只允许一封 official report。

## Success

- Gmail sent + Gmail readback + GitHub archive + GitHub readback = success。
- Gmail sent，但 GitHub archive 失败 = partial_success，日报视为已送达，后续只补 GitHub。
- Gmail failed = failed / partial_failure，后续 recovery 可重试。


## Dedicated fallback task — 2026-09-27

The existing `Crypto 09:00 日报发布` automation is the delivery fallback for the primary hourly task.

Schedule:
- 09:20
- 10:20
- 11:20
Asia/Bangkok.

It is delivery-only and idempotent.

Before any send:
- search Gmail Sent for exact subject `Crypto Daily Brief｜YYYY-MM-DD`;
- check the official GitHub report;
- check `crypto-daily/delivery-pending/YYYY-MM-DD.md`.

Recovery order:
- Gmail + GitHub both complete: silent exit.
- Gmail complete, GitHub missing: recover GitHub from Gmail readback.
- GitHub complete, Gmail missing: QA and send the archived body.
- both missing, pending body exists: send pending body, read back, archive official report.
- all three missing: reconstruct from the prior 24h research/final audits, create the pending body first, then send.

A prior automated claim of “already sent” is insufficient. Delivery proof requires an actual Gmail Sent message id and successful readback.


## Prebuild handoff

The 08:00 hourly collector prepares `delivery-pending/YYYY-MM-DD.md` but does not send.

The 09:00 publisher treats that pending file as the primary body:
- refresh only facts that are materially time-sensitive;
- preserve the body structure unless a correction is needed;
- Gmail delivery takes priority over broader research;
- target Gmail proof by 09:20.

If a valid pending body exists, recovery jobs must send it rather than rebuilding a new long report.


## Full-body resend rule — 2026-09-29

When the user requests a daily-report resend, correction, or reissue, recovery MUST NOT send a shortened digest as the replacement official report.

The resend must:
- contain all 13 REPORT_SPEC sections in the canonical order;
- meet the same factual and source-quality bar as the normal 09:00 report;
- include all material corrections discovered since the original report;
- use Gmail Sent + readback as delivery proof;
- write the identical body to the canonical GitHub daily-report path;
- read back GitHub and verify body equality;
- mark prior incomplete same-day editions as superseded.

An error-specific supplement may still be sent, but it never satisfies a request to resend the full formal daily report.


## Acceptance-gated delivery — 2026-09-29

Before any formal send or recovery send, read `REPORT_ACCEPTANCE.md`.

A formal send requires:
- current `delivery-manifest/YYYY-MM-DD.md`;
- `qa_status: PASS`;
- complete 13-section body;
- no unresolved CR hard-gate failure.

If manifest is missing/stale or QA is FAIL:
- do not send a digest;
- rebuild only the missing inputs/sections;
- rerun QA;
- then deliver.

The dedicated recovery automation must never invent a smaller replacement body. It may:
1. send the existing QA-PASS canonical body;
2. repair GitHub from Gmail readback;
3. rebuild missing coverage until the full body passes QA.

After send:
- read Gmail;
- archive the exact readback body;
- read GitHub;
- verify body equality;
- only then mark full delivery complete.

A short correction/supplement is supplemental only and cannot become the canonical daily body.

## 2026-10-16 delivery proof and suffix-aware deduplication

The 2026-10-16 primary 09:20 invocation persisted `runs/2026-10-16/092111-final.md` with `BLOCKED_WITH_REASON` from a Gmail safety gate, and had no 08:20 `delivery-pending/2026-10-16.md`. In an authorized same-day recovery, a complete 13-section email was actually sent and read back:
- report date: 2026-10-16
- Gmail Sent subject: `Crypto Daily Brief｜2026-10-16｜正式补发`
- Gmail Sent message ID: `1a1429397db803fe`
- canonical Git body: `crypto-daily/reports/daily/2026/2026-10/2026-10-16.md`
- Git archive SHA: `19438b9b738b211bdda7ace0d6fe674c95e4acbd`

**Recovery idempotency fix:** search Gmail Sent by the canonical date SUBJECT PREFIX `Crypto Daily Brief｜YYYY-MM-DD`, including `｜正式补发`, `｜历史漏发补送` and corrected subjects. Accept one matching authoritative, full-body, Sent-readback Gmail message plus canonical Git body equality as delivery proof. Never require the subject to equal the unsuffixed base string, and never resend because the approved recovery edition has a suffix.

At each existing 08:20 run, persist a durable QA-evidenced pending body and input manifest before optional deeper collection; if unable, persist a truthful reason in the terminal audit. At 09:20/10:20/11:20, lack of pending must trigger bounded reassembly and the unchanged full CR-01..CR-20 QA gate. Platform safety rejection remains BLOCKED_WITH_REASON and must not be bypassed; recover only via ordinary authorized calls. Gmail Sent/readback and canonical Git proof take precedence over any historical blocked attempt artifact. This fixes dedupe and records a reproducible prebuild gap; it does not assert that future platform safety blocking has been eliminated.

## 2026-10-21 publisher contract: discovery + dedupe + credible normal delivery
1. Sent-prefix check FIRST; same-day already-delivered formal/correction/resend is immutable and never silently duplicated. Reconcile only missing archive.
2. Consume current original English market/news source receipts and a bounded Arkham/Lookonchain/labelled BTC headline scan, plus seven-day real Sent/Git canonical history and existing TGE event ledger. Create an event/version decision matrix IN MEMORY; never pad 13 sections with historic safety, project-rights SOURCE_GAP, "no updates" or task-process statements. Account for each verified high materiality new item even if it has the same 500 BTC round value as old moves.
3. Construct one full final 13-section report. Before send perform semantic candidate accounting, no-delta suppression, ≤2 mentions per unique story, source/time/uncertainty checks and independent section-local 1..N numbering. When Node exists run \`node crypto-daily/scripts/daily_event_gate.mjs manifest.json\`; Node unavailable -> record gate not executed and run explicit equivalent in-memory checks (not a fake code PASS). The same report still must satisfy all preexisting CR gates.
4. Once real full QA passes, attempt Gmail normal delivery without optional repeat Git pending/attempt writes as a prerequisite. Provider Gmail safety block is real BLOCKED_WITH_REASON, never bypass; do not claim actual delivery. Successful Sent/readback followed by exact Gmail-body Git canonical archive; Git failure after Gmail is archive-only recovery, not resend. No user-visible health emails.
5. Store the compact per-event discovery/disposition in the single existing terminal final or optional pending metadata rather than creating an extra mutation per candidate. No separate new task, paid data subscription, credential or deployment.

## 2026-10-21 correction and real discovery source-receipt workflow
1. Check same-day Gmail Sent incl full corrected subject before ANY outgoing email. Oct21 corrected full Crypto email was sent as Gmail ID 1a15c6d25715d6ca and supersedes original 1a15c49e3ff24c51; do not resend either.
2. On each normal research round, gather truthful primary Arkham/Lookonchain BTC flow discovery receipts alongside original source lanes. Available on a real Node+network host: node crypto-daily/scripts/arkham_primary_discovery.mjs. Do not say code ran from a ChatGPT task unless it actually did; manual web discovery instead has its own real receipt status. Never equate reading Arkham homepage with complete blockchain coverage.
3. Use last seven successful Sent/Git daily reports plus state/daily-event-ledger.json to dedupe by exact event+material_version (txid, contract action, issuer update, market day). Existing fifth Collins transfer is already delivered in corrected edition. Old Qubic, Cysic, JPMD, HTX, Cambria, StandX, NeoSoul etc without new delta must not use numbered email space.
4. Check canonical 13 headings and each local 1..N numbering, cross-section unique-event maximum two mentions, all high-materiality candidates and source/uncertainty details. No need to pad an empty section. Keep operational metadata out of user email.
5. Send complete report only after true final QA, real Gmail Sent and full body readback, then archive actual readback body in Git. Provider safety block must be honestly marked and cannot be bypassed. A successful user-requested manual correction does not prove future autonomous delivery.
