# 地址分析 / Batch 005：固定来源第 081 至 100 行钱包的三链历史签名活动

Updated: 2026-10-18 Asia/Bangkok
Status: `PARTIAL / THREE_CHAIN_NONCE_SCREEN_COMPLETE / TOKEN_AND_WALLET_PNL_UNRESOLVED`

使用 [固定449地址来源](../sources/oooooyoung-evm-449-source-snapshot.json) 的原顺序第 081–100 行，按 [冻结窗口](../sources/frozen-30d-bsc-eth-base-blocks.json) 在 BSC、Ethereum、Base 执行共 120 次历史 nonce 查询，并在本轮重新查询 6 个边界区块、逐一验证哈希。该窗口截至 2026-10-17 21:12 UTC，**此结果是冻结历史样本，不是当前活跃提醒**。

[Batch005 原始地址及 nonce 快照](../evidence/batch-005-three-chain-30d-nonce-screen.json)

| 来源行 | BSC 签名 | ETH 签名 | Base 签名 | 已检查三链活跃 |
|---:|---:|---:|---:|:---:|
| 81 | 0 | 14 | 142 | YES |
| 82 | 21 | 0 | 1 | YES |
| 83 | 0 | 5 | 0 | YES |
| 84 | 0 | 0 | 0 | NO* |
| 85 | 0 | 0 | 0 | NO* |
| 86 | 271 | 1 | 0 | YES |
| 87 | 0 | 0 | 0 | NO* |
| 88 | 0 | 0 | 0 | NO* |
| 89 | 0 | 0 | 0 | NO* |
| 90 | 0 | 0 | 0 | NO* |
| 91 | 461 | 316 | 25 | YES |
| 92 | 0 | 0 | 0 | NO* |
| 93 | 0 | 0 | 0 | NO* |
| 94 | 0 | 13 | 0 | YES |
| 95 | 0 | 0 | 0 | NO* |
| 96 | 0 | 0 | 0 | NO* |
| 97 | 0 | 0 | 0 | NO* |
| 98 | 0 | 0 | 0 | NO* |
| 99 | 0 | 0 | 0 | NO* |
| 100 | 0 | 0 | 0 | NO* |

统计：BSC **3/20** 活跃，共 **753** 次签名；Ethereum **5/20**，共 **349** 次；Base **3/20**，共 **168** 次。三链并集 **6/20**，原行号 **#081、#082、#083、#086、#091、#094**。其余 14 个钱包仅能确认为三链 nonce 差值零，**不能认定 EVM 全链不活跃**。

## 真实交易抽查与下一步

- #083 Ethereum 五次签名交易的 external 流在冻结窗口内分页至结束，其中确认两笔向 USDC 合约的 `approve(0x095ea7b3)`，以及其他尚未完成日志级现金流解码的操作。授权不得计为 DEX 成交；完整 PnL `UNRESOLVED`。
- #082 BSC 首批交易包含原生 BNB 支付的 `0x39ecce49` 合约调用与 `0x095ea7b3` 授权，相关合约用途、最终代币取得成本和退出回款均未完整复算。
- #094 Ethereum 样本内存在 1 ETH 的合约调用（`0xa9b2c6eb`），无法据此认定买币盈利。源文件其他钱包的「创始人」「名人」等身份标签全部保留为未核实来源声明。
- #086、#091 是签名较多的钱包，需要有界分页并保持先亏损后盈利同一核算口径，不能按交易次数做盈利排行榜。

本批没有新增可审计闭环的收益或亏损，亦没有任何钱包完整 30 天、长期 PnL。剩余的 Ethereum/Base/BSC 交易类型、其他 EVM 链、被动转入和期初库存需继续研究。下一批活跃筛查为 Batch 006（#101–120）；Batch001–005 均保留交易级别的 `PARTIAL`/`UNRESOLVED`，不构成已完成交易价值验证。

`RESEARCH_ONLY / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。
