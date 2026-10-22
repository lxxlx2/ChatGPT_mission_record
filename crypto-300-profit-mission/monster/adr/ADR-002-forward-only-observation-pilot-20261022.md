# ADR-002 — Monster BSC 新池前向只读证据试验（2026-10-22）

状态：`OFFLINE_PROTOTYPE_APPROVED_TO_PREPARE / LIVE_MANUAL_RUN_NOT_YET_APPROVED / NO_DEPLOY`。本 ADR **不取代** ADR-001 免费来源、功效停止和统一治理；2025-07-01 冻结母体、P0/P1 门槛以及 2026-11-02 历史来源截止均不变。用户同意继续规划前向验证，但没有授权定时采样、实际购买或生产切换。

## 为什么要开这条独立验证路径

2025 年 BSC V2 已有 30 个按 Factory 时序选出的历史样本，Four.meme 日内有 538 个 launchpad 索引，部分交易和卖出为真实历史链上事实。但现在读取旧区块只能证明历史事件存在，不能凭 `block.timestamp`、`milliTimestamp` 或 2026 年 `ingested_at` 推断 2025 年当时普通用户实际收到事件的 `available_at`。这不是再扩大事后迁池样本能解决的问题。

新方案只对 **2026-10-22 以后真实发生且当场收到响应**的事件留下机器记录；不修改 2025 研究标签，也不宣称观察样本为真正的 2025 OOS。阶段状态仍 `P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`。

## 一次性前向观察最小合同

1. **发现源**：BNB Smart Chain 主网 Chain ID 56；PancakeSwap V2 Factory `0xca143ce32fe78f1f7019d7d551a6402fc5350c73`。先复用仓库已有的 Factory `allPairsLength()` 和按索引 `allPairs(index)` 只读调用，不依赖禁用的免费公共长窗 `eth_getLogs`。没有证明 V3、Four.meme 或整条 BSC 同样可覆盖。
2. **一次性样本**：仅一次前台调用，两个有明确时间的链头快照；两次间隔上限 3 秒；最多20次只读RPC；相邻块校验 parentHash、同一块在查询前后的 blockHash，看到链重组或 RPC 状态不一致就 fail-closed。新增索引超过3个仅完整记录总差额并明确 `PARTIAL`，不能吞缺失。
3. **证据**：对每次 RPC 留本地原始 HTTP **响应体字节**、SHA256、调用开始 UTC、完整响应处理完成 UTC、单调时钟耗时、请求方法及经过处理的参数、固定区块高度和hash。manifest 仅做有限摘要；**不得把用户私有 RPC URL/API key、原始大文件上传 Git**。当前不是第三方可信时间戳服务，时钟安全/本机时间校准需要独立审核。
4. **PIT语义**：`local_response_completed_at_utc` 是“此观察者最迟此刻已获取该响应”的**本地记录**，不是网络首次公开时刻、服务器生成时刻、可供所有普通用户执行的 `T_entry`；链上`timestamp`与本机完成时间永远不同列。既有历史`available_at`仍`UNKNOWN`。哪怕首次计数增长也不能据此证明交易可买、可卖、税率或资金利润。
5. **安全边界**：只允许 `eth_chainId`、`eth_blockNumber`、`eth_getBlockByNumber`、`eth_call`；无send/sign/approve、无私钥、无默认购买金额、无付费RPC，严禁后台cron/launchd和自动复跑。新样本计数为0时只能写“两个观察快照之间未见Factory计数增长”，不能写“全市场无新币”。
6. **验收**：交付可复现的离线负例与原始响应/manifest回放、SHA校验、只读限额和错链/重组/缺页 fail-closed；真实前台运行必须有用户单独明确批准。独立代码/来源审核前，不把捕获到的 `observed_at` 直接升级成正式 `PIT_VERIFIED`，也不允许进入P1建模。
7. **止损/后续**：若接口无可用响应、样本计数长期不足或发生本机时钟和RPC异常，保留失败事实，**不要**为凑正例改母体或增加默认交易金额。只有获得前向真实收包证据、完整源覆盖及经审查的买卖执行成本后，才另行讨论 P1。

## 当前真实性核对

2026-10-22 在已连接的、先前已使用过的 Alchemy 免费 BSC 只读应用中，`eth_chainId`实际返回`0x38`；`eth_blockNumber`返回`0x7b2afc1`；在**同一固定高度**调用 Pancake V2 Factory `allPairsLength()` 返回`0x35e3aa`（3,531,690）。这是“可读取状态”的单点验证，**不是**已在用户 Mac 原字节归档、持续观察或跑通双快照。无法把这次连接器调用的时间戳当成用户 Mac 网络可见性/成交时延。此证据只授予离线原型方向，不变更历史P0结论。

研发版本审查、任何运行本地命令以及是否建立独立长期前向试验，需要后续固定Git SHA与单独决策。