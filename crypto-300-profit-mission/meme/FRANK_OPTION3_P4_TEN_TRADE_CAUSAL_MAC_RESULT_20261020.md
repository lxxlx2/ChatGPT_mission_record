# Frank 方案 3 · P4 10 笔真实本地交易与 V1 模型因果关联（Mac 实测，2026-10-20）

## 执行和来源

本页整理用户于 2026-10-20 提供的 **实际 Mac stdout**，并非 GitHub 单测或新 RPC 查询。命令从本机旧 Frank `127.0.0.1:8766/api/trades` 一次性获取最新 100 行中的最多 5 买类 + 5 卖类交易，并使用已存在的 `forward.sqlite`、`mission-control.sqlite` 的 SQLite URI `mode=ro` 与 `PRAGMA query_only=ON` 复查；程序只输出匿名分类与计数，不包含 CA、地址、签名、金额或生产路径。

- 固定已审核产品 SHA (PR #146)：`72cf75c61fdb220a01b98df0abe81ebc5d248fd4`，未合并/部署。
- 实际本次 Mac 执行 QA SHA：`e8b66ee3a1729bcac34891ccfa242c015ed12216`。后续 QA HEAD 可能变化，不可把此结果自动算作后来版本的执行通过。
- 采样：`2026-10-20T10:22:40.750794+00:00`；只对应当时本地索引，**非全链完整性证明**。
- 用户 Mac stdout 中 `PYTEST_NOT_AVAILABLE`：本机本轮**未执行新增 synthetic pytest**；独立 CI 不能替代这一事实。

## 真正得到的交易来源事实

| 检查项 | Mac 实际结果 |
| --- | --- |
| 选取交易签名 | 10 个互异签名 |
| 与原库签名 + mint + side + block time 精确匹配 | **10/10** (`TEN_LOCAL_SOURCE_ROWS_RECONCILED`) |
| 买类交易 | 5（3 BUY + 2 REENTRY） |
| 买类确切 V1 评估存在 | **5/5** |
| 买类确切签名触发的 V1 新信号 | **0/5** |
| 买类状态 | `EXACT_TRANSACTION_EVALUATED_NO_NEW_SIGNAL` ×5 |
| 卖类交易 | 5（3 EXIT + 2 SELL_POSITION_UNRESOLVED） |
| 卖类确切 V1 评估存在 | 3/5（3 EXIT 各一次） |
| 卖类无确切 V1 评估 | 2/5（均 SELL_POSITION_UNRESOLVED） |
| 10 事件本身触发 ACCUMULATION/MULTIPLE 源信号 | 0/10 |
| 精确新信号 → 控制库关联 | 0/10 (`NO_EXACT_TRIGGERED_V1_SIGNAL_TO_JOIN`) |
| 控制库是否可读 | YES，`EXISTING_CONTROL_SQLITE_MODE_RO_QUERY_ONLY` |
| 交易 / RPC / Gmail / DB 写入 | 不在程序许可范围；CLI 报告相应字段为 false |

5 个买事件各自的 `exact_source_evaluations` 个数分别为 **4、4、4、2、4**。它们被 V1 模型评估、未产生新的本次 ACC/MULT 信号，与既有 PR #109 两笔 BUY `TRADE_EVALUATED_NO_TRIGGERED_SIGNAL` 发现方向一致；但这些事件与 PR #109 的两笔并非证明是完全相同抽样，也**不得**据此推断具体冻结谓词失败原因（未检查 `v1_evaluations.body.predicates`）。

本次不存在源签名丢失的证据；**“模型没有产生新信号”不能写成“链上漏交易”**。来源只覆盖本地索引 `LOCAL_INDEX_ONLY_NOT_CHAIN_VERIFIED`，不能推断完整链历史或者系统真实新通知送达状态。

## 重要缺口：新风险提醒如何捕获后续卖出

当前 PR #146 `DashboardState.frank_intelligence()` **只调用** `self.frank.candidates()`；该适配器对 `v1_states` 每个 mint/current episode 只保留同轮已确认 ACCUMULATION/MULTIPLE 或当前 OPEN REENTRY_WATCH。故这 10 笔交易虽然能出现在交易列表与历史回放，却不能直接得出“每次相关卖出都能进入新版智能卡片”。五个 SELL 记录的**本次签名**没有新的 V1 买入源信号是正常现象：要判断是否触发“此前关注代币的卖出风险变化”，需要检查**卖出之前的源信号及相同交易轮次/时间先后**，而不是要求卖出本身产生一个新买入信号。

下一步优先研究并设计 **prior-signal → later-SELL** 有证据关联的独立只读风险输入：必须有可信来源、准确签名/时间和状态；`SELL_POSITION_UNRESOLVED` 的余额继续未知；未满足原 V1 条件的无关交易不能自动触发此前未获授权的实时提醒。历史假卖出提醒不代表现实可发通知。不得为了让提醒数量变大而放宽原冻结 V1 策略或给买入额设默认值。

## 当前结论与停止条件

- `P4_TEN_LOCAL_SOURCE_RECONCILIATION_PASS`（用户真实 Mac 输出证明）。
- `P4_BUY_MODEL_EVALUATED_NO_NEW_SIGNAL_5_CONFIRMED`（不继续重复无新事实的两笔旧例核查）。
- `P4_ORIGINAL_V1_SIGNAL_TO_INTELLIGENCE_SELL_RISK_PARTIAL`（下一块主线功能，不是 P4 全面完成）。
- `MAC_PYTEST_NOT_EXECUTED`（缺 pytest；不要伪装测试已通过）。
- `OPTION3_LIVE_ALERTS_NOT_AUTHORIZED / PRODUCTION_NO_GO / FOLLOW_PROFIT_UNPROVEN`。

严格禁止生产安装、合并、策略签署、服务重启、钱包交易、Gmail/本地实际通知，继续独立 QA/静态审查。
