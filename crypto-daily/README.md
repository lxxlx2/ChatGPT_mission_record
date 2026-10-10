# Crypto Daily — 实际运行入口（2026-10-10）

仅现有 `Crypto 每日情报` 自动任务，不创建或启用其他定时任务。
时区 `Asia/Bangkok`；实际 schedule 原样不变：

- 00:10、03:10、06:10、15:10、19:10、23:10：普通 bounded collector
- 08:10：过去24小时资料+独立新闻发现，完整13章预构建
- 09:10：主发送；10:10、11:10：只有未交付时恢复
- 非触发时段不执行后台工作；TGE仍由自己的既有独立任务按自己的规则执行。

## 规范优先级
读取 `COLLECTOR_SPEC.md` V2、`REPORT_SPEC.md`、`REPORT_ACCEPTANCE.md`（包括CR-20）、`DELIVERY_RUNBOOK.md`、`SECURITY_SOURCE_POLICY.md` 和 `AUTOMATION_RUNTIME.md`。如历史文档出现“每小时整点”“09:00/10:00/11:00”或 `hour % 3` 字样，均按本文件上述实际 schedule 和 COLLECTOR_SPEC V2 的完成记录轮转替代。这仅澄清原 schedule，不调整任何触发时间。

## 三种不可混淆的完成状态
1. **DISCOVERY**：本轮真正查了哪些英文源？重大新候选进入哪条event_key、是否可核实、是否被合理排除？缺final或查询收据记覆盖缺口。
2. **REPORT_QA**：13章、重要事件未遗漏、CR-18去重、CR-19实质、CR-20发现完整性和最新行情均过关。Top5不满五件时不凑数量。
3. **DELIVERY**：实际Gmail Sent+readback，随后GitHub存完全相同正文+readback，缺任一不能称完整送达。单纯生成文字或写final不是发邮件。

普通collector每轮先做四类有界重大新闻发现，再做一个深度分片；通过最近两次真正完成的深度分片选择补缺，避免旧算法把4/6轮都分配给社交/NFT。高优先级未核实事件继续保存，不因未确认而当成无新闻。

已发生的XRPL、Ledger、Abstract和国家区块链网络政策漏检案例及缺失final的回归要求见 `tests/REGRESSION_CASES.md`。

**限制不变：** 英文来源、事实不编造；不新建任务、不改变现有监控范围/通知门槛；App输出静默；私人TGE已关闭和已完成权益持续去重。
