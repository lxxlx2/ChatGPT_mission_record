# BSC F0 — 冻结主钱包技术资格与官方 Router 来源离线预检

**状态:** `OFFLINE_ONLY / NO_NEW_NETWORK_AUTHORITY / NO_LIVE_WATCHLIST / NO_LIVE_CONTROLS / INDEPENDENT_REVIEW_PENDING`。基线为已批准离线代码 PR #130 固定 SHA `82705502079c85685fc6a3ccb3cefa9fa027dc33`。此模块是 L1 真实捕获前的技术资格资料与审计记录，**不是**实盘 EOA 资格批准器、监控器或交易系统。

## 实际完成什么

- 读取已经冻结的 PR #116 `F0_COHORT_PRESELECTION.json` **原始字节**；调用既有 `load_frozen_cohort()` 验证固定 Git blob SHA1 `fcd0029314353313867e565190cd4f2882089f11`，选取 20 个 PRIMARY；10 个 BACKUP 不自动放入实时名单，也不会根据收益/结果替换。
- 对 `eth_getCode(wallet, hex(block))` **已保存的响应**做方法、链 ID 56、钱包、固定区块高度、JSON-RPC ID、返回代码形状校验，保持 20 个钱包（包括没有采集到响应的）的分母。输出 `NOT_CHECKED`、`NO_CODE_AT_SAMPLED_BLOCK` 或 `HAS_RUNTIME_CODE_AT_SAMPLED_BLOCK`。没有代码仅证明在那个高度查询返回空代码，不证明签名私钥控制、永久 EOA 或真实 BUY/SELL。
- 冻结 PancakeSwap **官方开发文档**当前披露的 BSC v3 Universal Router 和 Infinity Universal Router **地址候选**：`0x1A0A18AC4BECDDbd6389559687d1A73d8927E416`、`0xd9C500DfF816a1Da21A48A732d3498Bf09dc9AEB`。来源 [官方 Universal Router Addresses](https://developer.pancakeswap.finance/contracts/universal-router/addresses)。**仅是来源核对**，未调用 `eth_getCode`、未验证运行时代码、部署高度、method selector、真实 swap 因果，不能启用 Router 对照采样。此列表**不包含**所有 V2 Router、聚合路由器或用户经合约代发的交易，潜在覆盖不足必须报告。
- 当前 snapshot 和报告是 100% 人工合成的演示数据，钱包不代表真实 PR #116 地址。实际运行的第一次 4-call smoke 不包含任何 `eth_getCode` 观察，不能据此推断这 20 个钱包的资格。

## 代码和可复现命令（全程离线）

在完整仓库根目录运行：

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_*.py'
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_l1_preflight.py --manifest crypto-300-profit-mission/bsc-forward-follow-model/f0/F0_COHORT_PRESELECTION.json --snapshot crypto-300-profit-mission/bsc-forward-follow-model/f0/fixtures/l1_code_fake_snapshot.json --router-registry crypto-300-profit-mission/bsc-forward-follow-model/f0/F0_ROUTER_SOURCE_CANDIDATES.json
```

**注意：** 第二条命令使用的是真实冻结钱包清单，但 snapshot 是**零个观察的合成夹具**，报告应显示 **20 个 NOT_CHECKED、0 个实际 RPC**。这有意拒绝借用合成 `0x` 来“证明”真实钱包是 EOA。

本地隔离目录运行原有 163 项与新增 15 项，结果 `Ran 178 tests / OK (skipped=2)`；**两项 skip 都依赖当前隔离目录不存在的真实 manifest**。本模块在完整 Git checkout 的复审要求是 `Ran 178 tests / OK`，**零 skipped**。不能将本地 skipped 的 positive test 记为 PASS。

## 下一步到真实 F0 的业务门禁

1. **仅在本模块独立审核通过后**，才准备一个具体的小型、只读、本地一次性资格检查许可。建议的预算设计为 **20 PRIMARY `eth_getCode` + 两个 Router `eth_getCode` + 一次 `eth_chainId` 和一次 `eth_blockNumber` = 24 次尝试上限**，明确端点、同一固定高度、UTC 时间窗、每次错误及分母、速率与响应大小；这些是**提议值，尚未获得用户批准**，不是可执行许可。
2. 真实 RPC 请求及原始证据先经独立批准的 bounded runner 捕获，记录原始响应和请求/响应时刻与字节哈希，具体 permit 需独立审核。**本 PR 没有 HTTP、WS 或循环网络采集路径。**
3. 真实 EOA 资格只允许从经检查的区块高度得到技术性候选；需要固定 Router allowlist、合约代码证据与协议方法范围、明确控制采样覆盖分母，才能进入下一阶段连续 L1 实时捕获。Transfer hint 不是 E2，空代码也不是 E1/E3；任何未知情况必须保留为 `UNRESOLVED`。

`NO_RUN / NO_WS / NO_TRADE / NO_SIGN / NO_NOTIFICATIONS / NO_BACKGROUND / NO_DEPLOY / NO_MERGE`。
