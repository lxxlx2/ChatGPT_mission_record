---
report_type: event_alert
event_date: 2026-09-14
timezone: Asia/Bangkok
project: Space
event_type: final_claim_deadline
email_subject: "[空投/TGE提醒][Space][最终Claim窗口截止]"
gmail_message_id: "1a09cc0fb4edb6f0"
gmail_sent_at: "2026-09-14T04:51:27+07:00"
automation_id: "6a85fff710e0819190ffcf8c1145a170"
status: official
qa_performed: true
qa_issues_found: 1
qa_corrections: 1
---

# 【Space 最终 Claim 窗口即将截止】

## 1. 事件
Space 官方 X 的 2026-09-04 公告已被英文搜索索引到，内容明确为重新开放 Airdrop Claim Portal，并说明这是一次性的 final claim window，要求在 2026-09-14 11:00 KST 前完成领取。换算为 Asia/Bangkok 为 2026-09-14 09:00。当前距离截止仅剩数小时。

## 2. 官方归属与操作页面
官方 Space 网站为 https://into.space/ 。Space 前身 UFO Gaming 的官方迁移页面明确写明，完成迁移的用户需要使用原先提交的同一 Solana 钱包领取，并直接指向官方 Claim 页面：https://claim.into.space/ 。因此本次建立的操作链为：Space 官方 X 截止公告 → Space 官方域名 into.space → 官方迁移页面确认的 claim.into.space Claim 页面。

## 3. 你现在需要做什么
1. 只打开 https://claim.into.space/ 。
2. 连接你此前参与 Space / UFO 迁移、sale、airdrop 或 allocation 时使用的 Solana 钱包。
3. 检查是否存在可领取额度。
4. 如有额度，在 2026-09-14 09:00 Asia/Bangkok 前完成领取，并保留少量 SOL 支付网络费用。
5. 签名前核对浏览器域名必须为 claim.into.space，并检查钱包弹出的交易内容。不要使用搜索广告、私信或第三方转发的领取链接。

## 4. QA 说明
官方 X 搜索索引的公告标题使用 “$SPACE Airdrop Claim Portal”，而 Space 既有官方迁移领取页面将领取资产标为 $SPC。由于两个官方来源的 ticker 展示存在差异，本提醒不依赖 ticker 判断资格，也不自行推断两者名称关系。项目归属、截止时间和最终操作域名均以 Space 官方来源闭环确认。

qa_performed: true

qa_issues_found: 1

qa_corrections: 1

修正内容：识别并保留官方来源中的 ticker 展示差异，最终通知中避免使用未经统一的一致 ticker 作为资格或归属判断依据。

## 5. 官方链接
1. Space 官网：https://into.space/
2. 官方 Claim：https://claim.into.space/
3. 官方迁移说明：https://migrate.ufogaming.io/

请在操作前再次核对官方域名。
