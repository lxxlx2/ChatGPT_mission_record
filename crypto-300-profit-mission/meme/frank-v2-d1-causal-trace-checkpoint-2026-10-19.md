# Frank V2 D1：最近 24h 两笔 BUY 的评估链归因

Date: 2026-10-19 Asia/Bangkok
Branch: `research/frank-v2-d1-mainline-20261019`
Status: **D1_LOCAL_CAUSAL_JOIN_CODE_ADDED / SYNTHETIC_SQLITE_REGRESSION_PENDING / REAL_MAC_TWO_BUY_TRACE_PENDING / NOT_DEPLOYED**

## 为什么先做这一项

V2 原定 D0→D1→D2→D3→D4，当前真实 Mac 的最新只读事实为：24h **273 个已索引签名、2 笔识别为 BUY、0 SELL、4 待复核**；Mission Control 仅 4 个历史候选，3 NO_BUY、1 WAIT，最后候选动作约 79.3 小时前；F01 GET 404（运行版未安装接口）。这些观测没有单笔因果映射，**无法证明这两笔 BUY 应形成新的累积/多次买入信号，也无法排除事件未送达模型的缺口**。

参考：Draft PR #108 真实 Mac 报告 https://github.com/lxxlx2/ChatGPT_mission_record/pull/108#issuecomment-6263529523 。

## 本轮业务成果

在本分支直接使用**现有** `forward.sqlite` 和 `mission-control.sqlite` 的只读查询，按真实 Mac 采样时间 `2026-10-19T08:56:26+00:00` 锚定 24 小时窗口，对每条 BUY/ADD/REENTRY 做：

1. 按 `wallet+signature` 联到已索引交易，并查来源 `signatures.classification`；不把被动转账计为主动 BUY。
2. 以 **exact signature** 查 `v1_evaluations` 是否实际评估过；以 `signals.body.triggering_signature` 精确确认本笔交易是否触发 ACCUMULATION/MULTIPLE。**同 mint 的旧 signal 不算本次触发。**
3. 查 `v1_states.events` 是否仍出现该笔签名，明确当前 episode 状态不会代表所有历史事件。
4. 仅当本次 signal id 与 `candidate_latest.body.source_signal_id` 及相同 episode 确切相同，才报告该信号的实际 Mission Control 决策；否则标记为同 episode 的非精确关联、缺少匹配，或控制库不可用。
5. 所有结果输出 event_ordinal、same_mint_group、受限原因枚举、评估/信号/判断是否关联和局部计数；不输出 CA、地址、签名、资金金额、原始模型正文及生产路径。不访问链上 RPC、无服务动作。

重点分辨 `TRADE_EVALUATED_NO_TRIGGERED_SIGNAL`（确有评价但未形成新阶段）、`TRADE_TRIGGERED_SIGNAL_FOUND`（信号已触发、核对判断）和 `TRADE_NOT_JOINED_TO_MODEL_EVALUATION`（事件与模型来源缺少关联，需进一步核实）。没有独立源证据之前，后一种**不是链上漏单的定论**。

## 出口与硬停止条件

- 固定分支代码通过真实 SQLite schema 反例、旧信号误关联反例、完全脱敏 ZIP、自身只读、完整 Python 回归和单次独立审核。
- 实机只做**一次有界、本地已有数据**读取，核实预期 2 笔 / 273 个索引记录是否匹配。若窗口/版本差异，保持 `SOURCE_WINDOW_DIFF`，不得编造筛选结果。
- 取得两笔的归因后，判断是**正常不满足冻结阈值、缺少模型评估/来源、还是产生信号但未进入 Mission Control**；下一项仅修真实证明的核心业务缺口。
- 不为已完成的 C02、503 或外层截图验收开启新审查；非阻断 P3 延后，D1 归因完成即转 D2 持仓/观察池数据准确性。
- **NO_MERGE / NO_DEPLOY / NO_NEW_RPC / NO_GMAIL / NO_TRADES / NO_PRODUCTION_SQLITE_WRITE**；没有买卖授权和完整链上覆盖证明。

核心规则：[Mission 开发主线与停止规则](../../docs/DEVELOPMENT_MAINLINE_RULES.md)。
