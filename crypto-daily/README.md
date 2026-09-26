# Crypto Daily

Crypto Daily 由**一个现有自动化**完成小时采集、09:00 正式日报和缺报恢复。

## 文件
- `REPORT_SPEC.md`：正式 13 章日报内容规范。
- `COLLECTOR_SPEC.md`：普通小时轻量采集规范。
- `DELIVERY_RUNBOOK.md`：同一任务在 09:00 / 10:00 / 11:00 的发布与恢复规则。
- `research/`：小时素材。
- `reports/daily/`：正式日报。
- `runs/`：每轮 audit。

## 自动化
现有 `Crypto 每日情报` 每小时 :00 运行：

- 普通小时：采集，不发 Gmail。
- 09:00：采集后生成/发送当天正式日报。
- 10:00 / 11:00：如果当天日报缺失则自动恢复；若已完整送达，继续普通小时采集。
- 不创建独立 publisher automation。

正式邮件成功后，即使 GitHub 临时写失败，也视为已经送达，后续只补归档，禁止重复发送。
