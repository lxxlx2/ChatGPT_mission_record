# Crypto Daily Delivery Runbook

Updated: 2026-09-26
Timezone: Asia/Bangkok

## Schedule

运行于每天 09:10、10:10、11:10。

09:10 是主发布。
10:10 与 11:10 仅负责 missing-delivery recovery。

## Dedupe

每次开始先检查：
1. `crypto-daily/reports/daily/YYYY/YYYY-MM/YYYY-MM-DD.md`
2. Gmail Sent 中 subject = `Crypto Daily Brief｜YYYY-MM-DD`

若 official Gmail 已存在且 GitHub report 完整：
- 立即静默退出；
- 只写一个很小的 recovery-check audit，或在无必要时不重复写正文。

若 Gmail 已存在而 GitHub 缺失：
- 从 Gmail readback 恢复同一正文到 GitHub；
- 不重复发送 Gmail。

若 GitHub report 存在但 Gmail 不存在：
- 读取并 QA report；
- 合格后发送 Gmail；
- 回写 message_id。

## Delivery order

1. 聚合过去 24h research。
2. 对最高优先级事实做 fresh verification。
3. 生成 REPORT_SPEC 的固定 13 章。
4. QA。
5. **先发 Gmail**。
6. Gmail readback。
7. 写 GitHub official report。
8. GitHub readback。
9. 写 publisher run audit。

GitHub archive 失败不得取消已成功的 Gmail。

## Graceful degradation

非关键数据源失败时：
- 使用其余可靠英文/官方来源；
- 对缺失字段明确写“本轮未取得可靠数据”；
- 继续交付。

只有以下情况允许完全不发：
- 无法获得足够信息形成基本可靠报告；
- Gmail connector 不可用；
- QA 发现重大事实冲突无法在本轮消除。

## Recovery

09:10 失败后，10:10 自动检查当天是否缺报。
10:10 仍缺则重新尝试。
11:10 是最后一次当日自动恢复。

任何 recovery 都必须先 dedupe，禁止同一天正常情况下重复发两封 official report。

## Success

- Gmail sent + Gmail readback + GitHub archive + GitHub readback = success。
- Gmail sent，但 GitHub archive 失败 = partial_success，日报视为已送达，后续只补 GitHub。
- Gmail failed = failed / partial_failure，后续 recovery 可重试。
