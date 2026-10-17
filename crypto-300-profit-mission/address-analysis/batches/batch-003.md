# 地址分析 / Batch 003：oooooyoung 原始第 041 至 060 地址三链签名活跃度筛查

Date: 2026-10-18 Asia/Bangkok
Status: `PARTIAL / THREE_CHAIN_NONCE_SCREEN_COMPLETE / PNL_NOT_STARTED`

本批使用固定来源 449 个 EVM 地址的原始第 **041–060** 行，无重排。Alchemy 只读 RPC 实查 BSC、Ethereum、Base 的历史 `eth_getTransactionCount`，三链窗口约 **2026-09-17 21:12 UTC 至 2026-10-17 21:12 UTC**。窗口区块和哈希沿用 [固定链上窗口](../sources/frozen-30d-bsc-eth-base-blocks.json)。

所有钱包的精确历史 `nonce_start`、`nonce_end`、差值及地址均保存在 [结构化证据 JSON](../evidence/batch-003-three-chain-30d-nonce-screen.json)。签名活动不能推断真实成交、盈利或钱包持仓。

| 原始行号 | 钱包 | BSC 签名 | ETH 签名 | Base 签名 | 三链任一有签名 |
| ---: | --- | ---: | ---: | ---: | :---: |
| 41 | `0x1d78fb87…04810c` | 0 | 0 | 0 | NO* |
| 42 | `0x897cff33…d2769b` | 0 | 0 | 0 | NO* |
| 43 | `0xc6792e3b…1cc7e2` | 268 | 249 | 32 | YES |
| 44 | `0xde078309…45b710` | 1 | 0 | 1 | YES |
| 45 | `0xf89f3858…bf892a` | 0 | 0 | 1 | YES |
| 46 | `0x6a30c5f1…cd9617` | 0 | 0 | 0 | NO* |
| 47 | `0xa7a9ae5b…626104` | 0 | 0 | 0 | NO* |
| 48 | `0x0d188418…5ef687` | 0 | 0 | 0 | NO* |
| 49 | `0xf68b8bb8…dd5bda` | 0 | 0 | 0 | NO* |
| 50 | `0x95ce1f0a…49355b` | 0 | 1 | 0 | YES |
| 51 | `0x624c6dbb…2b17c4` | 0 | 1 | 9 | YES |
| 52 | `0xb999055c…16a6fb` | 0 | 0 | 0 | NO* |
| 53 | `0xcbb4e8f3…d201a7` | 0 | 0 | 0 | NO* |
| 54 | `0x40cb329c…2c3986` | 0 | 0 | 0 | NO* |
| 55 | `0x6e23a5ae…9f8956` | 0 | 0 | 0 | NO* |
| 56 | `0xecc43e2c…540e10` | 0 | 0 | 0 | NO* |
| 57 | `0x98c24fae…d87afa` | 0 | 0 | 0 | NO* |
| 58 | `0x7e035fb0…87242b` | 0 | 0 | 0 | NO* |
| 59 | `0x1f605cc4…83f3bb` | 0 | 0 | 0 | NO* |
| 60 | `0xa02d5821…173dcc` | 4 | 0 | 1 | YES |

三链覆盖结果：BSC **3/20**，**273** 笔签名；Ethereum **3/20**，**251** 笔；Base **5/20**，**44** 笔。三链合并共有 **6/20** 个地址存在签名活动，原始行号：**43、44、45、50、51、60**；其余 **14/20** 个在这三条链均无钱包签名活动，不代表所有 EVM 网络无活动。

当前关注的工作量：#043 的 BSC 268、Ethereum 249、Base 32 笔签名需要分页核对真实成交；#044、#045、#050、#051、#060 签名量较少，可优先检查交易哈希类型和买卖成本。交易亏损不可遗漏；若无购买成本或卖出回款凭证，必须标 `PNL_UNRESOLVED`。

**审计范围：**仅完成 BSC/Ethereum/Base 历史 nonce 筛查。Polygon、Arbitrum 和被动 ERC20 转入/智能合约账户活动未查。没有对本批任何代币形成盈利或亏损结论，完整月度及长期钱包 PnL **0/20**。该批仍为 `PARTIAL`，不产生 final artifact，不构成实盘信号。

## 交易级有界反例核查：签名不等于成交

在三链 nonce 筛查后，通过 Alchemy 交易哈希与合约调用数据进行有限核对，参见 [交易哈希及选择器证据](../evidence/batch-003-low-frequency-transaction-classification.json)。

- **#044:** BSC ERC-20 `transfer` (`0xa9059cbb`)，Base 原生 ETH 直接转账。没有已确认的 DEX 盈利。
- **#045:** Base 唯一签名交易为成功的 ERC-20 `transfer` (`0xa9059cbb`)。
- **#050:** Ethereum 唯一签名交易为原生 ETH 直接转账，没有合约调用数据。
- **#051:** Ethereum 一笔零原生价值调用还未完整解码；Base 九笔签名中，五笔 `approve`、两笔借贷池风格调用、两笔 `0x3593564c` router `execute`，后两笔回执成功，但 **并未完成具体买卖代币、成本与卖出回款核对**。
- **#060:** BSC 四笔签名含一次授权、一次原生 BNB 转账以及两次未解码合约调用；Base 一次原生 ETH 转账。

这是签名交易与真正成交的反例核查，不代表钱包无亏损或已完整审计。两笔 router `execute` 按 `PNL_UNRESOLVED` 留在后续队列，不能推算真实利润或复制交易。

**下一步：**在维护 Batch001/002 未决交易队列的同时，对本批低签名量地址进行真实交易审计；后续签名普查推进原始第 061–080 行 Batch004。只读研究、不合并、不部署、不启用生产通知。
