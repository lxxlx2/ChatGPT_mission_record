# Crypto Daily

Crypto 日报现在使用单一统一自动化任务。

运行方式：
- 每小时整点执行一次滚动情报采集。
- 每轮写入 `crypto-daily/research/YYYY-MM-DD/HHMMSS.md` 与对应 run audit。
- 每天 09:00 Asia/Bangkok 在完成当轮刷新后，读取过去至少 24 小时素材并生成唯一一份正式日报。
- 正式日报发送到 Gmail，并把完全相同的正文归档到 GitHub。
- 其他小时禁止发送日报邮件或 ChatGPT 状态通知。
- 月报由每月 1 日 09:00 的同一任务追加生成。

当前权威规则见 `crypto-daily/REPORT_SPEC.md`。
