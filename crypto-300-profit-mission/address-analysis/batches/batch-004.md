# 地址分析 / Batch 004：oooooyoung 原始第 061 至 080 地址三链签名核查

Date: 2026-10-18 Asia/Bangkok
Status: `PARTIAL / THREE_CHAIN_NONCE_SCREEN_COMPLETE / TRADE_PNL_UNRESOLVED`

不可变来源地址 #061–#080，顺序未改变。Alchemy 历史 RPC `eth_getTransactionCount` 按前三批的固定 UTC 区块窗口逐个读取，共 20 × 3 × 2 个 nonce 响应；三条链的六个窗口边界区块哈希本轮重新比对一致。[精确地址与 120 个历史 nonce 值](../evidence/batch-004-three-chain-30d-nonce-screen.json)。

| 来源行 | BSC signed | ETH signed | Base signed | 三链任一 signed |
| ---: | ---: | ---: | ---: | :---: |
| 61 | 0 | 0 | 0 | NO* |
| 62 | 0 | 0 | 0 | NO* |
| 63 | 30 | 0 | 1 | YES |
| 64 | 1217 | 268 | 394 | YES |
| 65 | 24 | 297 | 49 | YES |
| 66 | 7 | 8 | 1 | YES |
| 67 | 18 | 2 | 1 | YES |
| 68 | 18 | 0 | 0 | YES |
| 69 | 3124 | 650 | 276 | YES |
| 70 | 7 | 4 | 6 | YES |
| 71 | 12 | 2 | 1 | YES |
| 72 | 1 | 0 | 0 | YES |
| 73 | 7 | 2 | 2 | YES |
| 74 | 5 | 2 | 0 | YES |
| 75 | 24 | 6 | 23 | YES |
| 76 | 250 | 28 | 21 | YES |
| 77 | 4 | 18 | 19 | YES |
| 78 | 9 | 2 | 0 | YES |
| 79 | 9 | 2 | 0 | YES |
| 80 | 99 | 267 | 162 | YES |

网络统计：BSC **18/20** 地址有签名，合计 **4,865** 笔；Ethereum **15/20**，合计 **1,558** 笔；Base **13/20**，合计 **956** 笔。三链并集 **18/20**，只有 **#061/#062** 三链签名皆零。三链零签名不代表所有 EVM 网络不活跃，更不代表没有被动收到代币。

## 交易分类与后续成本审计

有界抽查的 [交易哈希、方法选择器及分类](../evidence/batch-004-low-frequency-transaction-examples.json) 包括：#072 BSC 一次带 **0.25 BNB** 原生价值的 `0x4d819a2a` 合约调用，尚无 token 买入或卖出结算证明；#077/#078 的 `0x095ea7b3` 只是 ERC-20 approve；#066 一次 BNB 原生转账；#078 另有未解码合约调用。这些都未证明净盈利。

#064（BSC 1,217、Ethereum 268、Base 394）和 #069（BSC 3,124、Ethereum 650、Base 276）优先进入**有界分页/待结算队列**；#080 也有大量跨链签名（99/267/162）。同等关注低频合约交易可能亏损的情况。来源 JSON 中的「高盈利地址」只是未验证标签，不能提前形成聪明钱排行榜。

**状态边界：**Batch 004 仅三链签名活动完成 20/20；实盘成交、gas、成本、亏损、长期/30d 整钱包 PnL 全部未完成。保留 `PARTIAL`，不生成完成型 final artifact，不合并、不部署、不开启监控或交易。
