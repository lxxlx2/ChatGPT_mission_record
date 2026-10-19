# BSC F0 — 2026-10-20 用户首次真实公共 HTTP RPC Smoke 结果与下一阶段验收

**状态:** `FIRST_REAL_TRANSPORT_SMOKE_REPORTED_COMPLETE / F0_NOT_PASSED / NO_ADDITIONAL_NETWORK_AUTHORITY`. **证据：** [F0_FIRST_REAL_HTTP_SMOKE_20261020_EVIDENCE.json](F0_FIRST_REAL_HTTP_SMOKE_20261020_EVIDENCE.json)。本文件为用户上传的 Mac 本地运行报告的事后记录，**不是**我们在本会话对 HTTP 原始响应的独立重放。

## 已得到的真实、有限的结果（L0 → L1 传输前提）

2026-10-20 用户在自己的 Mac 上运行 PR #125 通过离线审核的脚本（固定 `fa3dae9b0f221747cb64bb1be21497979985e596`，脚本 SHA256 `2322e024e9beb0e92e653e564be4831b09367b49eb1e868f3affe44636002115`），使用本地生成且自检通过的一次性许可，粘贴最终 JSON 和进程退出码。

| 观察值 | 本次用户报告 | 严格含义 |
|---|---|---|
| 端点 | `https://bsc-dataseed.bnbchain.org`（由已审核固定代码确定） | 此次允许的唯一公共端点，非其他商业提供商 |
| `eth_chainId` | 56 | BSC 主网身份匹配 |
| `eth_blockNumber` | 128614660 | 读取到的区块高度；不证明传播时延 |
| `eth_getBlockByNumber(full=true)` | 1 次、返回 49 笔完整交易对象 | **单个区块**能返回可遍历发起者的完整交易格式，不能外推平均吞吐/交易结构 |
| `eth_getTransactionReceipt` | `IDENTITY_VALIDATED_NOT_FINALITY` | 从区块的第一笔交易取得 receipt，身份与区块相符；不能证明状态成功、finality 或 swap 因果 |
| 调用统计 | `attempted_rpc_calls=4`、`attempted_control_discovery_calls=1`、`actual_rpc_calls=4` | 全部许可额度已消耗，**不得**作为继续调用的授权 |
| 退出状态 | `Exit code=0`，`SMOKE_COMPLETE_NOT_F0_PASS` | 基础传输 smoke 成功，F0 技术验收并未成功 |

原报告提供四份 JSON-RPC 响应 envelope SHA256，可供将来同一原始响应重新校验；**原始 HTTP payload 未在本对话提供，也没有独立复现这些摘要**。许可的 SHA256 与 nonce 的 SHA256 可作为对应本地记录的关联信息，但原始 nonce、permit JSON 或私人路径不需要进入 Git。报告没有 UTC 首次观察或 monotonic request/response 时戳，因此**不能**测量最初可交易信号的延迟。

**透明的流程偏差：** 代码 PR #125 已通过独立审核，用户明确同意一次最多四次的只读 smoke。但本轮实际使用的是脚本动态生成、仅经过本地程序校验的具体 permit，**没有**在使用之前另外交给独立审核者审核。这不否定本次真实返回的用户报告，但不能把这份 permit 追认为“独立已审核的许可”；之后的更大试验必须恢复这一门禁。

## 仍为未验证的指标

- 观察窗口只有一次读取：**连续块覆盖率、漏块、请求排队、断网恢复与重组处理均未实测**。
- 49 笔交易中是否包含固定 20 名关注钱包、allowlist Router 的非关注钱包、BUY/SELL 或可随机抽样的普通对照，**没有逐交易数据证据**。`control_random_coverage=NOT_MEASURED`。
- E1 finality `UNRESOLVED_F1_POLICY`；Transfer 不证明 E2；实际 E3、真实 Router QUOTED 与 Paper PnL 为 0 / 未建立。
- 公共端点 `eth_getLogs` 对列出的主网节点禁用；不可当作事件发现渠道。官方文档写该端点名义请求限制 10K/5min，**不等于个人额度或持续可用性证明**。出处：https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/
- BSC 官方现行介绍约 0.45s/块。严格按“一块一完整区块读取”推算 24h **192,000 次**，48h **384,000 次**，还没算 HTTP 头查询、receipt、quote、独立审计或重试。出处：https://docs.bnbchain.org/bnb-smart-chain/overview/ 。单块 49 TX **禁止**当作平均区块 TX 数去推 24h 交易量。

## 从成功 smoke 推导的下一项实际开发任务

**L1 连续完整区块候选发现 + 随机 Router 控制的真实数据预检**，而不是再开发一个只能显示 PASS 的单块 RPC 试验。

开发（**先纯离线 + PR review**，不触发网络）必须完成：
1. 利用已经批准的 `f0_rpc_adapter.block_candidates()` 和 `f0_rpc_bridge` 接口，以按高度连续的完整区块输入驱动 `WATCHLIST` 钱包 `from` 检测与 `CONTROL_CANDIDATE` Router `to` 检测，禁止读取事后盈利字段；群体来源仅来自 PR #116 冻结的 F0 cohort，**先完成 EOA 技术资格检查，不准任意更换地址**。
2. 使用已冻结 `seed|wallet|tx_hash` 的随机抽样规则；没有预先确认 Router allowlist、随机参数、候选分母时，输出 `CONTROL_COHORT_UNRESOLVED`，而不创建伪对照。
3. 记录每个高度的 `received_utc` + `received_monotonic`、请求/响应时间、`block_hash`、成功/失败/重复、持续丢块区间、`BACKFILL` 与真实 `FIRST_OBSERVED` 不得混用。
4. 按 **WATCHLIST / CONTROL_RANDOM / RECEIPT / QUOTE / INDEPENDENT_AUDIT / GAP_RECOVERY** 分类记账；严格预算约束、超限停止，不启用无限重试或付费。**用户未批准任何更多网络请求**。
5. 同一钱包/tx ID、Unknown→BUY/SELL 的第一个可行动时刻与失败保留；卖出单列 EXIT。未经 F1 finality 和 E2 Router 因果判定的仅为提示，**不能**进入真实 E3/PnL。
6. 保留分母：`blocks_expected`, `blocks_received`, `missing_heights`, `watch_signer_transactions`, `router_control_candidates`, `precommitted_control_selected`, `direction_hints`, `e1_rejected`, `first_actionable_latency_distribution`, `billable_attempts`, `quote_failures`。只有真实获得且被可靠记录的观测才能进入实测指标，否则标 `NOT_MEASURED`。

**下一次现实性测试建议，待用户单独批准，不是预定任务：** 先做一个短窗口（例如 2 分钟）的有界、只读、只观察 L1/控制发现的 HTTP 验证。0.45s/块意味着约 267 个新增区块；设计上需独立冻结 **最大 RPC 总数、最大完整块/控制发现次数、并发与速率、每响应字节数、真实时间窗口、提供商、储存和停止条件**，并由另一审核者检查该具体许可。只有见到真实完整连续块和有用对照候选，再讨论扩大到 24–48 小时 F0 及真正的实时 +60/300/900 报价，不用一次扩大请求数量。

**明确定义当前权限：** 此次 4 次请求的许可已经耗尽。全部 Git 修改属于**结果归档与下一阶段设计**；没有进一步真实 RPC、WS、后台、交易、签名、提醒、部署、PR 合并或付费的授权。