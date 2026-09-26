# Crypto Daily Delivery Runbook

Updated: 2026-09-26
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

1. 聚合过去 24h research。
2. 对最高优先级事实做 fresh verification。
3. 生成 REPORT_SPEC 的固定 13 章。
4. QA。
5. **先发 Gmail**。
6. Gmail readback。
7. 写 GitHub official report。
8. GitHub readback。
9. finalize 当前小时 run audit。

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
