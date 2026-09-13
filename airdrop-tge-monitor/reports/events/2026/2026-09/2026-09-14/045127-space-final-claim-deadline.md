---
report_type: event_alert
event_date: 2026-09-14
timezone: Asia/Bangkok
project: Space (@intodotspace)
event_type: final_claim_deadline
email_subject: "[空投/TGE提醒][Space][最终Claim窗口截止]"
gmail_message_id: "1a09cc0fb4edb6f0"
gmail_sent_at: "2026-09-14T04:51:27+07:00"
automation_id: "6a85fff710e0819190ffcf8c1145a170"
status: retracted
retracted_at: "2026-09-14T04:57:00+07:00"
error_type: cross_project_misattribution
qa_performed: true
qa_issues_found: 2
qa_corrections: 2
---

# RETRACTED：Space 最终 Claim 窗口提醒

本事件已撤销，不得作为后续提醒、去重基线或历史事实使用。

## 1. 错误说明
白名单监控对象是 `Space (@intodotspace)`。本次候选事件实际来自另一个同名/近名项目 Spacecoin `@spacecoin` 的 `$SPACE` airdrop 信息，却被错误合并到 `into.space` / `@intodotspace` 的项目身份下。

随后又把 `migrate.ufogaming.io` 与 `claim.into.space` 作为操作页面接入同一证据链，形成了错误的跨项目拼接。

## 2. 原提醒中需要撤销的结论
以下结论全部撤销：

1）`@intodotspace` 在 2026-09-04 宣布 final airdrop claim window。
2）该窗口在 2026-09-14 11:00 KST / 09:00 Asia/Bangkok 截止。
3）`claim.into.space` 是该所谓 `$SPACE` final claim 的操作入口。
4）该事件满足正式提醒条件。

## 3. 正确身份基线
监控对象：Space

官方 X：`@intodotspace`

官方域名：`into.space`

同名冲突项目：Spacecoin `@spacecoin`

今后任何候选事件只有在原始官方发布账号、官方根域名、项目自述身份至少两项与白名单身份直接一致时，才允许进入动作页面核验。搜索摘要、ticker 相似、同名、生态关系、迁移历史均不得替代身份锚点。

## 4. QA 失败原因
原 QA 已发现 `$SPACE` 与 `$SPC` ticker 冲突，却采用“通知中不依赖 ticker”继续放行。正确处理应为 hard fail：出现 ticker、官方账号、根域名、项目名称体系任一身份冲突时，必须停止正式提醒并重新做项目身份核验。

本事件因此由 `status: official` 更正为 `status: retracted`。

## 5. 后续防复发
已新增项目身份锁定规则、同名项目冲突检查、跨项目 hard fail、candidate source account 记录和 identity_match 审计字段。对应事故记录见：

`airdrop-tge-monitor/incidents/2026-09-14-space-cross-project-misattribution.md`
