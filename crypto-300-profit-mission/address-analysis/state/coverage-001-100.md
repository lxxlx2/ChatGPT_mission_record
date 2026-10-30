# 地址分析 / 原始 001–100 钱包 BSC、Ethereum、Base 历史签名筛查汇总

Observation: 2026-10-18 Asia/Bangkok
Status: `RESEARCH_ONLY / HISTORICAL_SIGNED_SCREEN_ONLY / WALLET_PNL_UNRESOLVED`

## 核对范围与可用结果

以原来源 Blob `954f3aba66be21911dd627fa40dd3dd0a9fd1d26` 固定顺序，从 Batch001–005 五份机器证据重建 **100 个不重复地址**，逐地址交叉验证与来源清单完全一致。使用固定的 2026-09-17 21:12 至 2026-10-17 21:12 UTC 窗口，只覆盖 BSC、Ethereum、Base 的钱包签名 nonce 增长。

| Batch | 原始行 | 三链任一有签名地址 | 原始签名证据 |
|---|---|---:|---|
| 001 | 001–020 | 15/20 | [nonce JSON](../evidence/batch-001-three-chain-30d-nonce-screen.json) |
| 002 | 021–040 | 13/20 | [nonce JSON](../evidence/batch-002-three-chain-30d-nonce-screen.json) |
| 003 | 041–060 | 6/20 | [nonce JSON](../evidence/batch-003-three-chain-30d-nonce-screen.json) |
| 004 | 061–080 | 18/20 | [nonce JSON](../evidence/batch-004-three-chain-30d-nonce-screen.json) |
| 005 | 081–100 | 6/20 | [nonce JSON](../evidence/batch-005-three-chain-30d-nonce-screen.json) |
| **合计** | **100/449** | **58/100** | [统一100地址状态JSON](../evidence/coverage-001-100-standardized-signed-screen.json) |

按网络独立计数：BSC **49** 个签名活跃地址 / **33,939** 笔签名交易；Ethereum **48** 个 / **6,373** 笔；Base **43** 个 / **6,094** 笔。三链签名零的 **42/100** 不等于没有买币、获空投或者在其它 EVM 链不活跃。网络间同钱包只在并集计一次。

## 盈亏证明状态

已结算正收益**单币轮次3个**，参阅 [RTX5090 #016](../evidence/batch-001-row-016-rtx5090-roundtrip.json) 和 [sauce #002/#004](../evidence/batch-001-rows-002-004-sauce-roundtrips.json)。**完整钱包30日/长期 PnL：0/100。已完成亏损单币轮次：0，不得据此把亏损认定为0。**

统一 JSON 逐钱包将两个完整钱包 PnL 字段均固定为 `UNRESOLVED`，对上述三个单币闭环仅给出指向原证据的引用，拒绝构造不完整盈利榜、胜率或跟单建议。

**具体历史证据缺口：**Batch001 的 BSC 历史窗口账户 nonce 差值可以使用，但三链合并 JSON 不含其20个账户的精确 BSC 起止 nonce 对；统一清单将此字段的可复核性明确标为 `false`。另外，Batch001–005 都没有核算全部跨链买卖、损失、期初库存、手续费和合约路由成交，不能依据签名交易数推断盈亏。

## 接下来的有界工作

历史签名普查按原始顺序继续 **Batch006（101–120）**。交易级审计并行从 Batch001 低频地址未核算币种推进至其它批次；优先补齐**负收益和历史库存成本**，有出入金/授权/铸造/空投时必须单独分类。高频钱包一轮达到分页预算后，保留确切最后页、缺口和重入条件，不能停掉其它地址处理。目标始终是完整、扣费用、可复算的近30天与长期地址盈亏，而非最大化活跃地址数量。

本文件只是覆盖快照。`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。
