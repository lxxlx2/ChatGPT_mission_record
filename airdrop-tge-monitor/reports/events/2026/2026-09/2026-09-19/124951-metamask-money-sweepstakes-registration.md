---
report_type: event_alert
event_date: 2026-09-19
timezone: Asia/Bangkok
project: MetaMask
event_type: Money Sweepstakes Registration
email_subject: "[空投/TGE提醒][MetaMask][Money Sweepstakes Registration]"
gmail_message_id: "1a0b836c33c1039f"
gmail_sent_at: "2026-09-19T12:49:51+07:00"
automation_id: "6a85fff710e0819190ffcf8c1145a170"
status: official
backfilled: true
qa_performed: true
qa_issues_found: 0
qa_corrections: 0
---

# MetaMask Money Sweepstakes Registration

MetaMask 官方 Rewards 新增 Money Sweepstakes，需要主动 Opt in 才能获得资格。

MetaMask Help Center 官方活动页面确认，活动从 2026-09-17 至 2026-10-15 运行，共四个独立周周期。参与者必须先在 MetaMask Mobile 的 Rewards 中加入 MetaMask Rewards，然后进入 Money Sweepstakes 并单独点击 Opt in。仅加入 Rewards 本身不足以获得抽奖资格。

完成 Opt in 后，需要在活动期间通过 MetaMask Money Account 新增一笔至少 100 mUSD 的合格存款。活动开始前已经存在 Money Account 的余额不计作首次参赛存款。首次合格存款完成后当天获得一个 entry；随后只要 Money Account 总余额维持至少 100 美元，每个日历日可继续获得一个 entry。每周 entries 重置，每个 weekly draw 最多 7 个 entries。

Week 1 官方时间为 2026-09-17 14:00 UTC 至 2026-09-24 13:59:59 UTC，对应 Asia/Bangkok 2026-09-17 21:00 至 2026-09-24 20:59:59。整个活动结束于 2026-10-15 13:59:59 UTC，对应曼谷时间 2026-10-15 20:59:59。

用户动作：
1. 仅打开官方 MetaMask Mobile。
2. 进入 Rewards，确认已经 Opt in MetaMask Rewards。
3. 打开 Money Sweepstakes，阅读当前应用内规则并单独点击 Opt in。
4. 在活动期内完成一笔使 Money Account 收到至少 100 mUSD 的新存款。
5. 完成后检查活动页 entry 状态；若继续参与后续每日 entry，保持 Money Account 总价值至少 100 美元。

安全要求：仅通过 MetaMask 官方应用及官方域名入口操作，不通过搜索广告、私信或第三方 claim 页面连接钱包、签名或授权。

官方来源：
https://support.metamask.io/trade/metamask-rewards/how-to-participate-in-rewards/
https://metamask.io/rewards

## Backfill audit
本文件由历史完整性检查发现 Gmail Sent 已存在正式提醒、GitHub event 尚未归档后补建。未伪造新的提醒发送或运行次数。原 Gmail message_id 与发送时间保留用于审计。