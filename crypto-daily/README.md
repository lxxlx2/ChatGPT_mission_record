# Crypto Daily

Crypto 日报采用“采集”和“发布”拆分架构。

## 文件
- `REPORT_SPEC.md`：正式 13 章日报内容规范。
- `COLLECTOR_SPEC.md`：每小时轻量采集规范。
- `DELIVERY_RUNBOOK.md`：09:10/10:10/11:10 发布与自动恢复。
- `research/`：小时素材。
- `reports/daily/`：正式日报。
- `runs/`：采集与发布 audit。

## 自动化
- 每小时 :00：只采集，不发 Gmail。
- 09:10：日报首次发布。
- 10:10 / 11:10：如果当天没有 official delivery 才恢复。

正式邮件成功后，即使 GitHub 临时写失败，也视为已经送达，后续只补归档。
