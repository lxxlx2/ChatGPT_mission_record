# Frank 方案 3 — P4 Mac 隔离历史回放实测记录（2026-10-20）

**来源：用户 Mac 实际终端日志与 Safari 截图，非 GitHub CI 或脚本开发者的自测宣称。**

## 1. 固定范围

- 产品代码（PR #146）：`72cf75c61fdb220a01b98df0abe81ebc5d248fd4`；Claude 已审核该 SHA 的产品代码，OPEN/Draft，未合并、未部署。
- 实际 Mac 运行的 P4 QA 代码：`eb91bd7b245bdd9e507dc4dbae6964dead9d03eb`；`qa/frank-option3-mac-isolated-20261020`。
- QA 相对已审核产品 SHA 只新增 `scripts/frank_option3_mac_staging.py` 与 `scripts/frank_option3_p4_history.py`，未修改任何原产品文件。
- 旧 Frank 源：`127.0.0.1:8766`，一次性本地 GET 快照，来源 `OLDER_FRANK_8766_SNAPSHOT_NOT_LIVE`。
- 隔离页面：`127.0.0.1:18766/` 和 `/qa/p4-replay`，只读、无 RPC/报价/发信/下单能力。
- 当前记录仅保存用户分享的结果摘要；截图保存在此次 ChatGPT 对话里，并未擅自复制用户本地截图到仓库。

## 2. Mac 实际验收证据

实际输出：

```text
FIXED_REVIEWED_SOURCE_SHA: 72cf75c61fdb220a01b98df0abe81ebc5d248fd4
CAPTURED_AT_UNIX: 1792490229.757
INTELLIGENCE_ROWS: 5
FAKE_UNSENT_SELL_NOTICES: 0
P4_REPLAY_STATUS: PASS_LOCAL_INDEX_RETROSPECTIVE_REPLAY
P4_REPLAY_CASE_COUNTS: {"distinct_signatures": 10, "distinct_mints": 7, "indexed_sides": {"REENTRY": 2, "BUY": 3, "EXIT": 3, "SELL_POSITION_UNRESOLVED": 2}, "historical_fake_sell_notices": 5}
P4_REPLAY_CHECK_ERRORS: []
REAL_NOTICES_SENT: 0
PRODUCTION_FILES_WRITTEN: 0
LOCAL_HTTP_SMOKE: PASS
STAGING_STOP_REQUESTED
```

源快照观察：`runtime_at_capture=LIVE`、`production_db_readable_at_capture=true`、`source_scope=LOCAL_INDEX_ONLY`、`source_chain_complete=false`；最近页 100 个互异已索引签名、46 个不同 mint，本次用于新版候选分析的当前候选条目 5 个。100 条交易页的分布为 `REENTRY=3, EXIT=27, BUY=23, SELL_POSITION_UNRESOLVED=25, SELL=7, ADD=15`。

用户实际 Safari 截图可观察到：主页面显示原 Frank 旧候选、历史信息和新的只读分析卡片；隔离历史页显示 10 张来源交易卡片与 5 条标明 `FAKE ONLY, UNSENT` 的模拟历史 SELL 风险记录。卡片时间按 UTC 展示；原始样本记录在前一次验收中按 Bangkok +07 展示，换算不能混用。历史页面未冒充实时行情或真实仓位。

页面真实点击了哪些 CA 复制、交易签名跳转、搜索过滤，截图**无法证实**；不得标记这些人工交互已通过。

## 3. 已通过的**有限** P4 子项目

- 10 个独立签名、7 个币种、5 次买入类别（3 BUY、2 REENTRY）及 5 次卖出类别（3 EXIT、2 SELL_POSITION_UNRESOLVED）被旧本地索引返回并成功转换为 10 张日期化离线分析卡片。
- 离线程序对每张卡执行显式历史截点和 `T−1` 未来事件排除、无原 V1 源信号不编造、无真实市场参考不计算回报、仓位不确定不可伪作已确定、无预设购买金额等检查。程序结果 `P4_REPLAY_CHECK_ERRORS=[]`。
- 5 个 SELL 类样本在**人为指定为历史交易时间**的离线上下文中生成 5 个模拟风险对象；同批重复和 601 秒后的过期模拟抑制经程序自检，人工未逐条核对内部 JSON。
- 用户提供的真实隔离 HTTP smoke 输出是 PASS；真实通知 0、生产文件修改 0。用户 Control+C 后隔离进程正常停止。

**子结论：`P4_LOCAL_INDEX_RETROSPECTIVE_REPLAY_PASS`。**

## 4. 没通过或尚未核实的范围

这些事项不能由历史回放 PASS 推导为已通过：

1. 10 笔真实链上签名**未逐笔独立重新查询**；只验证已有本地索引与其方向字段的约束。历史交易在当时是否已经被采集到系统：`UNVERIFIED`。
2. 10 条是不同的**历史交易签名**，不是 10 个独立、可在当时追踪的 V1 信号或可成交买入机会。不存在已证实的 10 条“真实源信号→当时提醒→行情→买卖结果”全链路证据。
3. 当前 `/api/frank-intelligence` 实际旧生产版仍是 404；隔离版不会部署到现有 8766。新的实时 SELL 风险提醒尚未授权，历史 5 条提示不代表今天应发送。
4. 风险追高判断需要同链/同 mint、可溯源且新鲜的参考行情，这次明确没有行情，因此**不能标记涨幅追高验证通过**。
5. D1 钱包签名活动接口在旧 8766 是 404；不能以此证明真实钱包当前余额或完整链上覆盖。
6. 已完成 QA 的 10 张历史页面为英文研究/调试展示，和生产中文新风险消息的可读性仍需区分；CA 复制、筛选、签名跳转的人工逐次点击尚未证实。
7. 新版本地/Gmail 通知策略、可靠发送、用户签名、P5 生产切换及跟单盈利均未获批准或证明。

## 5. 实际业务改进点与优先级

- **P2（正式风险提醒之前必须确认语义）**：5 条历史模拟 SELL 中，2 条索引分类是 `SELL_POSITION_UNRESOLVED`，模拟通知目前统一文案为 `FRANK_VERIFIED_SELL`。这能表示本地索引认定的卖出动作，却**不能**被描述为“彻底清仓、仓位归零或盈利退出”。正式面向用户的风险提醒至少要表达“观察到卖出，剩余仓位未核实”与“EXIT 分类”之区别，且不把 EXIT 分类本身充当独立链上当前余额证明。只修改确实会误导用户的核心文案/状态映射，不扩大无关边界修改。
- **产品缺口（本阶段限制，不是提交新假数据来掩盖）**：没有可比的新鲜行情时，智能分析只能展示链上交易证据和数据缺口；价格追高、真实可执行性及收益判断继续 `UNVERIFIED`，不可用任意假价格填补。
- **历史抽样代表性**：选择规则是最多五笔买入类别和五笔卖出类别，具有确定性，不代表随机样本，也不能作为策略收益评估。

## 6. 下一步主线

1. 固定并记录这一轮 Mac 验收证据；不再重复安装或跑相同版本。
2. 只针对生产用户会看到的“卖出后仓位未核实”风险文案、事实来源、去重与禁发策略建立最小更改方案。
3. 补实际 V1 source signal → 当前候选分析的证据关联，与 10 条交易的历史可观察性明确分开；找不到来源即保留 `UNVERIFIED`，不伪造。
4. 将原 V1 原样保留，新的任何实时风险提醒、邮件、新发布包与切换仍需新的用户策略审批、准确 SHA 和生产授权。

**最终状态：`PR146_CODE_APPROVED / P3_MAC_ISOLATED_PASS_FOR_CARDS / P4_RETROSPECTIVE_10_CASES_PASS / P4_FULL_CAUSAL_REALTIME_INCOMPLETE / P5_NO_GO`。**
