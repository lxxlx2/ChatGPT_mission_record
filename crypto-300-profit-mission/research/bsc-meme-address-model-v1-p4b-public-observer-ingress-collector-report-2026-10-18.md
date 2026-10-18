# BSC Meme V1 P4-B：真实公众可观察时刻的最小可行证据入口

日期 2026-10-18。目标：在既有 23 EOA × 19 exact CA 研究集之外**不引入新钱包、不放大研究利润**，提前准备真实“观察者何时收到原钱包相关公开事件”的可审计记录。保留此阶段所有 G4/G5 未证实条件。

## 一、已核对的 BNB 免费技术路线及限制

根据 Alchemy 官方文档（2026-10-18 阅读）：

- BNB Smart Chain `eth_subscribe` 允许 WebSocket `wss://`，官方列有 `logs`、`newHeads`、`newPendingTransactions` 等类别：<https://www.alchemy.com/docs/chains/bnb-smart-chain/bnb-smart-chain-api-endpoints/eth-subscribe>。
- **Alchemy 地址过滤的增强型 `alchemy_pendingTransactions` 各官方参考页对支持链的枚举表述并不完全一致，且未确认支持 BNB**：<https://www.alchemy.com/docs/reference/subscription-api>。故不能直接拿原 23 个 EOA 在 BNB 依赖该增强订阅，也不能把收到 BNB 成交后的日志冒充“mempool 首见”。
- 标准 `logs` 支持合约地址、topic 条件：<https://www.alchemy.com/docs/reference/logs>。本阶段选择 `eth_subscribe(["logs", {"address":[19 exact CA], "topics":[ERC20 Transfer, null, [23 EOA indexed recipient]]}])`。这是**ERC20 入币候选发现**，不是本人原始签名、买入意图、交易成功独立结算、报价币种或跟单 U 认证。BNB 上生产网络对这组组合过滤器的实际接受情况**本轮未连网实测**；不保证服务商免费配额、筛选性能或端到端时延。
- Alchemy BNB 免费 `eth_getLogs` 单次回溯最大 10 块（供以后人工核验，不代表本轮调用）：<https://www.alchemy.com/docs/chains/bnb-smart-chain/bnb-smart-chain-api-endpoints/eth-get-logs>。本轮不执行 RPC，也不新建监控任务。

## 二、本次新增的可运行、未部署代码

1. `bsc_meme_address_model_v1_p4b_bounded_postblock_log_collector.js`：Node v24 原生 WebSocket，**默认 `--dry-run` 且绝不打开网络连接**；只有用户之后显式 `--live`、`BSC_WSS_URL` 环境变量与本地输出文件才连接。最多 600 秒和 250 条原始日志，不自动重连，不发送交易，不使用私钥、不修改链上状态。单组来源固定 `23×19` blob SHA，RPC 订阅失败写实际失败，不伪造观察成功。把 WebSocket **收到时的真实本地 UTC 与 monotonic 时钟**、完整接收帧 base64+SHA256、blockHash、txHash、logs 等保存在带 `0600` 文件权限的 JSON，避免在报告和文件泄露 WebSocket URL/API key。记录 `removed` 重组日志供门禁拒绝。
2. `bsc_meme_address_model_v1_p4b_public_observer_ingress_gate.py`：只读 Python stdlib CLI，默认输出 **五份历史证据的 U 缺失**；`--input` 可离线读采集 JSON，无网络。对固定 23×19 集合、历史冻结交易不可倒填成新的 live first-seen、原数据 SHA、原始 pending 对象的 `from`/hash、ERC20 Transfer 的 token exact CA/收币人 topic/区块/数量/是否被 reorg 标记、UTC/monotonic/用户报告的时钟信息做门禁验证。程序支持两类候选：待打包 tx 全对象、已上链 post-block Transfer log。
3. `test_bsc_meme_address_model_v1_p4b_public_observer_ingress_gate.py`：只用 **SYNTHETIC_TEST** 事件覆盖伪造 hash、地址外越界、错 CA、重组日志、归零金额、原始 SHA 篡改、历史时间替代、时钟不合格、过期历史交易回填、重复 ID、无界输入、Node `--dry-run` 和 23×19 topic filter。测试通过只表示输入验证按设计处理，不是历史链上收益或真实 WebSocket 连接证明。

运行仓库本身内现有代码的**无网络自检**，无须新增依赖：

```zsh
node crypto-300-profit-mission/research/bsc_meme_address_model_v1_p4b_bounded_postblock_log_collector.js --dry-run
python3 -B crypto-300-profit-mission/research/bsc_meme_address_model_v1_p4b_public_observer_ingress_gate.py
python3 -B -m unittest discover -s crypto-300-profit-mission/research -p test_bsc_meme_address_model_v1_p4b_public_observer_ingress_gate.py -v
```

只会打印或检测冻结参数，不启动监听。**未授权部署前不执行 `--live`，不建立 launchd 常驻、不接 Mac 用户本地钱包、不做任何报警/买卖。** 系统默认时钟校准证据 `UNKNOWN`：原始真实帧仍可以保存，但导入器拒绝将它升级为可用延迟起点；需要来自用户自己确有证据的时钟校准来源和实际偏移上限，不能通过随意传 `0` 假装已校准。即使用户报告已同步，导入器也只输出 `UNATTESTED` 本地时间候选。

### 链重组与重复日志的真实安全语义

Ethereum/Geth 官方原始订阅语义明确：相同区块里的日志可能在 reorg 时重新以 `removed=true` 发出，随后交易也可能出现在新区块。来源：<https://geth.ethereum.org/docs/interacting-with-geth/rpc/pubsub>。本项目**不可按 txHash+logIndex 简单去重再丢弃 removed 事件**。当前 Node 采集器对同一 `blockHash+txHash+logIndex` 分别保留 INCLUDED 与 REMOVED 两个原始订阅帧，SHA 分别保存；Python 导入阶段在一个批次发现完整来源校验的同一旧区块 `removed` 墓碑时，将旧 INCLUDED 候选转为 `REORG_REVOKED_POSTBLOCK_LOG`，且 `target_windows_utc=null`。新链不同 blockHash 的事件不应随旧块撤销。原始帧自报仍非独立外部证据，不得将这次撤销/确认凭空认证为第三方达标收益。若服务商没有发来重组撤销日志，该离线批次也不能自行宣称最终性。

## 三、首次收到事件 != 原钱包可跟单的买入

- 此项目最初要在 19 个真实 major exact CA 中发现 2026 年仍主动交易、可重复盈利且可被旁观者按公平规则跟进的地址。`Transfer(to=EOA)` 本身可以是 passive transfer、空投、内部转移、合约授权交易的结果，并不能单独证明原 EOA 是 tx signer 或钱包买入。
- 原始交易哈希和合约转账只是**候选**，后续还要独立读取 `eth_getTransactionByHash` 的原始发起人、成功 receipt、完整 Token Transfers、报价资产净出入、Gas/税费、池资金深度和入场时实际可得报价。必须先处理非 BUY/被 reorg/过期/未成交等反例。
- 实际 `first_local_observer_received_utc_claim` 和历史 `consensus block.timestamp` 各自独立存证；前者也只是**单个接收节点看到的最早已上链日志时间**，不是世界所有公网节点中最早的 mempool 首见。没有真实独立采集原始帧，历史五案例 `first_public_observer_received_utc` 仍为 null。
- 执行 `+60/+300/+900 seconds` 的时间只作为未来候选的待验证目标，而不是真实可下单或成交。未预冻结本金、费用/退出规则、未提供有状态历史报价与实际回款前，仍 `PUBLIC_EXECUTABLE_U=UNRESOLVED`、`P5=BLOCKED`。
- 由于未获得 Mac 只读运行和外部服务商实测授权，**目前业务完成度是“来源边界、采集器源码、导入门禁、离线测试”**；真正公网观察第一笔、证明可复制正负回合、运行时性能和真实盈利仍未完成。

下一里程碑：其他 AI 对本次独立 U 入口核心算法进行一次**固定 SHA 代码安全/证据等级定向审核**；通过后另获许可，在用户 Mac 使用 free RPC 作有时长、有条数上限的 **2 分钟 read-only dry actual WSS** 验收，确认 BNB provider 真实接受过滤器与日志质量，观察实际捕获率与时钟证据。拿到独立验收前绝不把原五个历史回合产生的模型收益当成回测结论。

## 四、2026-10-18 外部审核 REQUEST_CHANGES 后的定向修复（未经新外部 APPROVE）

外部 Codex 对原固定 SHA `c8482d1e2d5c44fb7e712538def09abd33a5739d`（比较基线 `4158e7bd...`）出具 `REQUEST_CHANGES`：P2 撤销帧绕过完整校验，P3 在 UTC 接近 9999 年底时导致整批 OverflowError；另一名审核者的本地回环模拟另指出 SIGTERM 未落盘、没有核查 WebSocket 来源 `eth_chainId`，以及同一个 log 修改 `event_id`、来自旧区块的转账换新自报时间亦能被当成未证明时效的候选。这些是真实提出的风险，不等同于财务盈利证据。

**定向修复结果：**

- Python 原共享 `validate_event()` 会先验证 `network=bnb-mainnet`、23/19 集合、事件 ID 唯一性、原始帧 SHA、所报告的时钟质量、固定历史交易黑名单。已上链 log 的 `removed=true` 现须再次满足与包含事件**同级别的 token CA、钱包收款 topic、tx、blockHash、logIndex、数量及发送方 topic** 完整验证，才可成为结构化撤销证据；普通 `REJECTED_EVIDENCE` 不会产生任何撤销副作用。重复 ID、错误网络、同 tx 的其他钱包/CA、数量/发送方冲突不得撤销第一条；原本同批次真正 `removed` 仍撤销且 `target_windows_utc` 清空。
- 同一链上位置 `bnb-mainnet + blockHash + txHash + logIndex` 只能对应一条规范化内容；同位置同内容换 `event_id` 或 JSON 序列化只计一次；同位置金额、sender、区块号、CA 或 wallet 有冲突时，两份 INCLUDED 均标 `LOG_IDENTITY_CONFLICT` 并清空延迟目标，不作为有效候选。`REMOVED` 仍需与原 INCLUDED 的 CA、wallet、blockNumber、sender topic、金额等内容严格一致才能撤销，**不同内容的 tombstone 无权更改原候选**。证据作用仅限同一输入批次，不保证跨批去重和跨批重组。
- `+60/+300/+900 秒` 的 UTC 算术集中校验。极端 `9999-12-31T23:59:59Z` 在 pending 与 mined-log 均返回明确 `UTC_DELAY_WINDOW_OUT_OF_RANGE`，合法的同批其他记录继续处理，而不是中断整个导入。
- Node.js 限时只读采集器在订阅之前必须先通过 `eth_chainId` 验证 `0x38`，不匹配即拒绝订阅和归档失败状态；收到 SIGTERM 后走同一 `finish()` 写盘并以 143 退出。分别追加完全在 Node 进程内覆盖 `WebSocket` 的离线模拟测试，证明 BNB 正确路径有真实接收帧与终止证据，错误 chain ID 不开启订阅、不产生事件文件中的假数据（仅写失败状态）。**没有接入任何真实公共 RPC/WSS、未启动后台监听。**
- **仍未解决的信任边界：** `raw_sha256` 只锁定消息帧原始字节，`observer_received_utc`、`observer_monotonic_ns` 及 provider/capture 端字段本身仍是自报，不存在可被本次离线复算独立验证的防倒签、第三方时间公证。已发生的历史新区块事件换上新的自报 UTC 可能得到 `UNATTESTED` 候选，但始终不能生成 `first_public_observer_received_utc`、经过鉴证的公网 U、经审计可执行跟单报价或盈利。该问题必须在**未来真实受控实测的来源与时钟证明**中解决，不能继续对老历史区块逐条添加黑名单。真正公平样本外跟单回测仍未开始。

当前代码不得因为单元测试通过而被自我标为独立 `APPROVE`。保留 `PENDING_OTHER_AI_REVIEW`、`P4-B/P4-C=PARTIAL`、`PUBLIC_EXECUTABLE_U=UNRESOLVED`、`P5=BLOCKED`、`PRODUCTION=NO_GO`。最后一次完整 CI、审核比较 SHA 与来源由 PR #40 的新固定版本评论补充。

## 五、2026-10-19 第二次独立 `REQUEST_CHANGES`：相同链上日志位置的冲突版本隔离

独立审查结果 `REQUEST_CHANGES@e7caa4caee517ef39ea436dfe34aa34fab6c22db`，比较基线 `c8482d1e2d5c44fb7e712538def09abd33a5739d`。旧 P2 四类撤销注入、旧 P3 两种 UTC 溢出、Node 链 ID/SIGTERM 离线测试均通过，但新 P2 是：已有 `_validated_log_key` 把金额、sender topic、blockNumber 等**内容**混进**位置身份**，导致同 `blockHash/txHash/logIndex` 但内容不同的两个 INCLUDED 被计为两个候选；如再追加与原 A 完全匹配的 REMOVED，旧代码只撤销 A，伪造 B 继续保留 60/300/900 秒窗口。原报告称“同一原始日志不能重复计入”过宽，已在上文收紧到有界单批**位置去重 + 内容一致性隔离**。

本轮新实现分别采用：
- 稳定位置：`("bnb-mainnet", blockHash, txHash, logIndex)`，不包含 CA、wallet、sender topic、blockNumber、amount。
- 规范化内容：位置 + exact CA + original receiver EOA + blockNumber + sender topic + ERC20 raw amount。上述字段均先通过原 `validate_event`、真实消息帧 SHA 与 23 EOA/19 CA 范围校验。大小写或 JSON 字节序列化变化不会创建新位置。
- 相同位置、内容一致：第二份 `DUPLICATE_ORIGINAL_LOG_IDENTITY`，只算一条；相同位置、任一内容冲突：所有同位置已接受的 INCLUDED 均 `LOG_IDENTITY_CONFLICT`，`target_windows_utc=null`；后续同位置重复也不解封。严格的 `REMOVED` 仍必须完整匹配原内容才能撤销，错误网络或另一个 CA/EOA/金额的 tombstone 不触发撤销副作用。真实同块、同内容 REMOVED 对没有冲突的候选继续产生 `REORG_REVOKED_POSTBLOCK_LOG`。
- 冲突数单列 `counts.log_identity_conflicts`，不冒充历史发生的交易亏损，也不冒充来自独立公网的时钟/地址审核成功。记录保留原始数据供离线核验。

测试单独加入四组方法、覆盖多种子例：金额、sender、blockNumber、CA、wallet 冲突的 `[A,B]`；匹配 A 的真实 REMOVED 与 `[A,B,R]` / `[R,B,A]`；同内容不同格式但不同 event ID；同交易不同 logIndex 本来就属于另一个位置。旧 P2/P3/链身份/中断落盘测试均保留。任何正式批准仍需独立 other-AI 在**新固定 SHA**定向复审，之前被拒绝的 SHA 仍为 `REQUEST_CHANGES`。所有结果仍为**只读离线证据门禁**，没有真实 BNB 节点连接、没有可交易 U/P5 成果。
