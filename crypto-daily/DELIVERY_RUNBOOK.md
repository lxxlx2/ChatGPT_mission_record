# Crypto Daily Delivery Runbook

Updated: 2026-09-28 19:34 Asia/Bangkok
Timezone: Asia/Bangkok

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
- 09:10
- 10:10
- 11:10
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
- target Gmail proof by 09:10.

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
