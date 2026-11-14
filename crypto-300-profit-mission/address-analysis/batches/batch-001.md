# 地址分析 / Batch 001：oooooyoung 前 20 个钱包的三链筛查与单币买卖闭环

Date: 2026-10-18 Asia/Bangkok
Status: `PARTIAL`; `BSC_ACTIVITY_SCREEN_COMPLETE` = 20/20; `ETH_BASE_NONCE_SCREEN_COMPLETE` = 20/20 each; `FULL_30D_AND_LIFETIME_PNL_COMPLETE` = **0/20 wallets**; `TOKEN_ROUNDTRIP_VERIFIED` = **3 closed token roundtrips**. No claim that all EVM chains were screened.

## Frozen scope and reproducibility

- Source snapshot: [449 immutable rows](../sources/oooooyoung-evm-449-source-snapshot.json), rows **001–020** exactly as original JSON sequence, source Git blob `954f3aba66be21911dd627fa40dd3dd0a9fd1d26`.
- Chain for this stage: **BNB Chain / BSC mainnet (56)**. Primary evidence Alchemy `eth_getTransactionCount` with fixed historical and current height, plus direct RPC transaction, ERC-20 and BNB historical state.
- 30d lower snapshot block `0x74cf256` timestamp **2026-09-17 21:12:12 UTC**. Upper snapshot block `0x7a4ca36` timestamp **2026-10-17 21:12:13 UTC**. Delta `nonce(upper)-nonce(lower)` counts transactions *signed by the wallet* between the heights. The historical lower timestamp precedes upper by ~30 days 1 second. Zero count = no wallet-signed BSC transaction in this interval; it does NOT establish EVM-wide inactivity or token-only passive-transfer absence.
- `source_label` is an unverified file nickname. `eca小号` on several addresses does not prove common control.
- Fully profitable address count = **UNRESOLVED**. This stage's `13 signed wallets` cannot be equated to `13 profit-making traders`.

## 20 wallet screening results

| Row | Imported alias (unverified) | EVM address / BscScan | BSC 30d signed tx | Per-token realized / completion |
| ---: | --- | --- | ---: | --- |
| 01 | eca小号 | [`0x0006d0…c29111`](https://bscscan.com/address/0x0006d09df7b0e8dce98463b95439475fcec29111) | 3 | PNL_UNRESOLVED |
| 02 | eca小号 | [`0x0d8d6c…95b5e0`](https://bscscan.com/address/0x0d8d6c105629e472691f9a970a6f70899195b5e0) | 11 | PNL_UNRESOLVED |
| 03 | eca小号 | [`0x45004a…d58dad`](https://bscscan.com/address/0x45004af18692aac16840c807d8980ad215d58dad) | 3 | PNL_UNRESOLVED |
| 04 | eca小号 | [`0x000777…331111`](https://bscscan.com/address/0x00077705952c90b728c6d7dc450beb4429331111) | 17 | PNL_UNRESOLVED |
| 05 | eca小号 | [`0x4d75b1…13299a`](https://bscscan.com/address/0x4d75b19b27db424effc711d046e62bb3a713299a) | 0 | BSC_SIGNED_ZERO；其他链未查 |
| 06 | eca小号 | [`0x000ae1…3c6111`](https://bscscan.com/address/0x000ae1e2ba3624208300605d7919d6c4803c6111) | 3 | PNL_UNRESOLVED |
| 07 | 早期 | [`0x3f63c1…d92fa5`](https://bscscan.com/address/0x3f63c175ff9746cf0e0e6095d0568180f9d92fa5) | 3 | PNL_UNRESOLVED |
| 08 | 早期derwold | [`0x13a405…b74287`](https://bscscan.com/address/0x13a4059646875645b2db4592aa224ea79fb74287) | 0 | BSC_SIGNED_ZERO；其他链未查 |
| 09 | 早期derwold | [`0x049823…74e4f8`](https://bscscan.com/address/0x049823701eef27e235d4c1271bc4410c7974e4f8) | 0 | BSC_SIGNED_ZERO；其他链未查 |
| 10 | 早期derwold | [`0x716ed4…6a2f02`](https://bscscan.com/address/0x716ed41f601012139490802f9aec155e736a2f02) | 0 | BSC_SIGNED_ZERO；其他链未查 |
| 11 | 早期derwold | [`0x9fb841…78ff9d`](https://bscscan.com/address/0x9fb8412d79ea66b8f2c747b9457b2b1d5d78ff9d) | 0 | BSC_SIGNED_ZERO；其他链未查 |
| 12 | 早期 | [`0x2fc947…71a300`](https://bscscan.com/address/0x2fc9478c3858733b6e9b87458d71044a2071a300) | 0 | BSC_SIGNED_ZERO；其他链未查 |
| 13 | 早期高手 | [`0x9bd3a9…dc86b5`](https://bscscan.com/address/0x9bd3a92c231893278c2fa654fc8d152ae6dc86b5) | 0 | BSC_SIGNED_ZERO；其他链未查 |
| 14 | 早期高手 | [`0x40e56f…486c08`](https://bscscan.com/address/0x40e56fa7759c1bdc67764fcd76c8ee7bc9486c08) | 2307 | PNL_UNRESOLVED |
| 15 | 早期alpha高手 | [`0xd68def…f3fe1a`](https://bscscan.com/address/0xd68def46b1114f51b7e676e6dde89069a2f3fe1a) | 5 | PNL_UNRESOLVED |
| 16 | (无标签) | [`0x29935e…31d4ed`](https://bscscan.com/address/0x29935ef1417e1c3b1fec68dd666ea9baac31d4ed) | 1982 | RTX5090 **+0.226099 BNB**；其他未审 |
| 17 | (无标签) | [`0x89c030…7dae08`](https://bscscan.com/address/0x89c030914b562628618e68bcda49f8ed617dae08) | 207 | PNL_UNRESOLVED |
| 18 | (无标签) | [`0x4d9644…0726f3`](https://bscscan.com/address/0x4d9644d05fe2123b4eafa8d7fd31b0ea430726f3) | 4183 | PNL_UNRESOLVED |
| 19 | 敏锐 | [`0xe70866…57e7e6`](https://bscscan.com/address/0xe7086669436e90d6a2a0a6aeb23c71188057e7e6) | 38 | PNL_UNRESOLVED |
| 20 | (无标签) | [`0x0209aa…44eb94`](https://bscscan.com/address/0x0209aa08dd3f5a1057cd66771a6009854144eb94) | 520 | PNL_UNRESOLVED |

Summary: **13/20** with signed BSC transaction(s); **7/20** signed BSC zero; total **9282** signed BSC tx in this fixed BSC window. This census includes transfer, approval, router and other types. **此处为最初 BSC-only 阶段的数据；Ethereum/Base 随后按下面的续查章节完成，其他 EVM 网络尚未检查。** No return or win rate inferred from counts.

## 2026-10-18 continuation: Ethereum + Base signed activity

Alchemy historical Ethereum and Base nonce pairs were collected for the same 20 fixed source rows. Evidence: [machine-readable three-chain screen](../evidence/batch-001-three-chain-30d-nonce-screen.json). Historical boundaries are aligned within two seconds across chains.

- Ethereum: blocks 25,999,816 (2026-09-17T21:12:11Z) to 26,214,883 (2026-10-17T21:12:11Z), **13/20** wallets signed, **1,331** signed transactions.
- Base: blocks 51,445,092 (2026-09-17T21:12:11Z) to 52,741,093 (2026-10-17T21:12:13Z), **10/20** wallets signed, **1,515** signed transactions.
- BSC remains **13/20** wallets signed, **9,282** transactions in the previous fixed-height screen.
- Across BSC + Ethereum + Base: **15/20** signed at least once. Rows **008/009/010/011/013** were signed-zero on these three networks only. Rows **005** and **012** had zero BSC signed transactions but nonzero Ethereum activity.

| Source row | BSC signed | Ethereum signed | Base signed | Signed on any of three |
| ---: | ---: | ---: | ---: | :---: |
| 01 | 3 | 114 | 91 | YES |
| 02 | 11 | 58 | 108 | YES |
| 03 | 3 | 94 | 0 | YES |
| 04 | 17 | 124 | 90 | YES |
| 05 | 0 | 89 | 76 | YES |
| 06 | 3 | 107 | 87 | YES |
| 07 | 3 | 0 | 0 | YES |
| 08 | 0 | 0 | 0 | NO* |
| 09 | 0 | 0 | 0 | NO* |
| 10 | 0 | 0 | 0 | NO* |
| 11 | 0 | 0 | 0 | NO* |
| 12 | 0 | 3 | 0 | YES |
| 13 | 0 | 0 | 0 | NO* |
| 14 | 2307 | 465 | 965 | YES |
| 15 | 5 | 4 | 0 | YES |
| 16 | 1982 | 157 | 0 | YES |
| 17 | 207 | 13 | 7 | YES |
| 18 | 4183 | 92 | 82 | YES |
| 19 | 38 | 0 | 1 | YES |
| 20 | 520 | 11 | 8 | YES |

**NO*** means zero wallet-signed transactions on the three checked networks during the frozen window, not total EVM inactivity. Smart accounts, passive ERC20 receipts, Polygon/Arbitrum and other chains remain unexamined. Signed nonces do not establish trade execution or profitability. No additional token gain/loss positions or whole-wallet PnL were confirmed in this continuation.

## Verified completed token roundtrip: row 016 RTX5090

- Wallet: `0x29935ef1417e1c3b1fec68dd666ea9baac31d4ed`, source label empty, not an identified trader.
- BSC token name/symbol: **RTX 5090 / RTX5090**, canonical audited-in-this-transaction contract [`0x5601a422986034521330bb4c799a8a3f29137777`](https://bscscan.com/token/0x5601a422986034521330bb4c799a8a3f29137777), **18 decimals** from chain metadata.
- One successful buy at 2026-10-17 **13:50:19Z**, **6,541,299.252621676 RTX5090** acquired. Read-only `balanceOf` before initial purchase: **0**.
- Five successful sales at 13:51:47, 13:52:41, 13:52:48, 13:54:52, 13:55:00 UTC. ERC-20 outflows **including separately charged token transfer-tax/fees** total **6,541,299.252621676**; ending `balanceOf`: **0**. No remaining unpriced inventory for this specific roundtrip.
- Full wallet BNB block `height-1 → height` differences, with direct successful receipts and per-block native signed transaction enumeration: **buy −0.106481164474 BNB**; five net sale receipts **+0.332580497590 BNB** (includes approval and gas costs within those blocks). Net **+0.226099333116 BNB**, roundtrip **+212.34% on BNB spent**.
- Valuation using **Binance BNBUSDT official 1-minute close at each chain timestamp**: **about +$162.86 USD-equivalent**, indicative rather than exact settled USD gain. The six blocks contain only one buy or one sale and at most a related ERC20 approval as wallet-signed actions. This is **CONFIRMED single trade-set** supported by [machine-readable detailed audit](../evidence/batch-001-row-016-rtx5090-roundtrip.json).
- Chain tx links: [buy](https://bscscan.com/tx/0x38be951419849aaaaf6c6f15cf6cf6614d069095f548bcfbd1af36ebcf5d816a), [sell 1](https://bscscan.com/tx/0x0ed58497cf8a7b3b9a2bf3b34eca387fa506ca98a9c188092fa6893d614fcb92), [sell 2](https://bscscan.com/tx/0xa6397e9648e9b1ee602bcf51444f15a732cfd0d14d7cf8631527d93d26ea92cb), [sell 3](https://bscscan.com/tx/0xc8f8649a3cc02f1e5cf940f594f548083f1216c615b5c43ad4915cb8ec3d29b4), [sell 4](https://bscscan.com/tx/0xca66407e72e2983babf5ac8ace5f00d90dc26cb369dc5955dafa6e81a26d9e5a), [sell 5](https://bscscan.com/tx/0xb4b279e0cb7b8270ee5993ac2502a87ae69ac34e0795d6f2c1ba5825ee14c223).
- **Critical scope:** the row 016 wallet's other **1,982 signed BSC transactions in the 30-day census** are not all reconciled by this one profitable roundtrip. Do **not** treat +$162.86 as row 016's total 30d, lifetime gain, or competition PnL. Other losses may outweigh it.

## 新确认：#002 和 #004 sauce 完整单币交易盈利

2026-08-20 两个钱包各通过 [路由合约](https://bscscan.com/address/0x1de460f363af910f51726def188f9004276bf4bc) 使用 BNB 分两笔买入 saucecoin / sauce (`0xd7ccd29b6fd1464edb425f24b01115556e737777`)，并在 2026-10-16 全部卖出。买入早于近30天窗口，卖出发生在窗口内。Alchemy 历史 `balanceOf` 在买前和卖后都为0，卖出区块有 ERC20 授权和交易各一笔，钱包 BNB 区块净变化已扣除同区块相关 Gas。

| 钱包原始行 | 买入总成本（BNB） | 卖出净回款（BNB） | 单币净收益（BNB） | BNB 本位 ROI | 指示性 USD 净收益 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 002 | 0.054313975 | 0.211142080278687674 | **+0.156828105278687674** | +288.74% | **+$118.86** |
| 004 | 0.054313975 | 0.208529773043203099 | **+0.154215798043203099** | +283.93% | **+$116.96** |

美元参照为 Binance 官方 BNBUSDT 1m 历史收盘价：2026-08-20 12:29 UTC **642.07**，2026-10-16 12:58 UTC **728.09**。这是按历史时间估计的美元等价收益，不代表链上结算 USDT。详细交易哈希、审批哈希、token raw balance 和 Wei 净额详见 [结构化可复算证据](../evidence/batch-001-rows-002-004-sauce-roundtrips.json)。两个钱包在相近区块买入、同一区块退出，仅证明时间相似，无法证明同人控制。BNB 区块余额差可能包含非钱包签名的同区块意外入账；目前尚无完全独立的 BSC 内部转账追踪，单币结果仍需要独立审核。

这两个结果与 #016 RTX5090 共 **3 个已核实正收益单币闭环**。没有完整确认的负收益交易，**不代表没有亏损**。#002 的 FTR 和其他代币、#004 的其他交易、以及所有钱包整体 30d 和长期收益继续保持 `PNL_UNRESOLVED`。

## Additional observed specific tokens, PnL unresolved

| Row | Token (on BSC) | Why still unresolved |
| ---: | --- | --- |
| 001 / 003 / 006 | FTR `0xa6546faf3ea3e7f10dcb7dab6b30b9005248265e`, S3B `0x7138b48df7d98d7e3cc221bfe7192d0a178182d8` | Shared passive FTR incoming transaction hashes, tiny S3B transfers; wallet-signed transaction count low. No independently matched paid buy and realized exit for FTR. **Do not infer airdrop value or multi-wallet control** |
| 002 | FTR `0xe895398d9814354ca30ef5b35b9b8e13e8416666` | sauce 已在本次闭环核算；FTR 的具体买卖与其他资产成本仍未审完 |
| 004 | sauce `0xd7ccd29b6fd1464edb425f24b01115556e737777` | sauce 单币已闭环；其他资产和全钱包长期收益未审 |
| 007 | ETH `0x2170ed0880ac9a755fd29b2688956bd959f933f8` | Token outbound, unverified contract identity/quote receipts, unknown basis |
| 015 | HODL `0xc242c264efe56109c495b308985f2694593477f8` | Two transfers out, no verified starting inventory cost |
| 017 | RM `0x33fe24f4298a8659668e8d1f2044fd01e8a57777`, Mongo `0x88adc3093a2e7bce52e9ec53f3eaf1f72a727777` | Sampled ERC20 token outflows only, buy-side/inventory/other exchanges not audited |
| 018 | CZ `0x49b7ebe0af6a94998babe0255cf06593f5b07777`, CZ LIFE `0x5aefc3e2a9e06c5b7b3c9a44a895f2311a0a7777`, BYTE `0xbb7d00c683bcf5807c31573632245e1df37a7777` | Heavy activity, incomplete pagination; no PnL ranking until full historical receipts |
| 019 | GOOGLon `0x091fc7778e6932d4009b087b191d1ee3bac5729a`, AAPLon `0x390a684ef9cade28a7ad0dfa61ab1eb3842618c4` | Contract identity/prices and trade history not established; numerous likely tiny transfers |
| 020 | 屌丝生活 `0x11e80d2b5f182149c9168ec62d93eaf51d0177777` | Multi-sale outflows observed, acquisition cash flows and precise exits not fully reconciled |


## 2026-10-18 独立 RPC 校验升级：#002/#004 sauce

[最新窄过滤 ERC-20 Transfer / 历史代币余额 / BNB 区块余额 / nonce 证据](../evidence/batch001-sauce-rows002-004-narrow-transfer-native-block-20261018.json) 已重新读取 **两钱包各2买1卖** 的链上数据。每钱包买入区块两条实际收币日志、卖出交易两条转出日志（必须合并计算）与历史 `balanceOf` 的 0 → 两次买入合计 → 0 完全一致。6组反向日志查询均为空；各钱包买入高度签名 nonce +1/+1，卖出高度 +2（含授权）。

另外历史 BNB 地址余额在交易所处**区块**的差分总和，#002 为 **+156828105278687674 wei BNB**，#004 为 **+154215798043203099 wei BNB**；这是重新取得的区块级现金流，数值与先前保存的 sauce 单币轮次一致，并不是新增收益案例。

**重要证据等级限制：**当前 Alchemy 的完整路由收据仍截断、免费档无法提供 BSC internal trace，尚不能排除同一出售区块中的其他被动 BNB 收款，更不能把全部余额差分百分之百归因于该笔 router sell。记录为 `NATIVE_TX_ATTRIBUTION_UNRESOLVED`，不得宣称已获得完整独立买卖利润审计通过。其它交易及整钱包月度/长期 PnL 继续 `UNRESOLVED`。

[可复核的保存数据一致性程序](../tools/verify_block_roundtrip.py)、[12个通过的合成反例测试](../tests/test_verify_block_roundtrip.py) 与 [完整 QA](../state/sauce-rows-002-004-independent-log-block-recheck-20261018.md)。模块重点仍是逐交易来源与成本归因，不是继续单纯提高活跃地址筛查数。


## 2026-10-18：其它代币的真实转入/转出与未决成本（#002/#007/#015）

新核查 [三钱包 ERC20 完整方向分页、历史余额、native BNB 区块变化及钱包关联证据](../evidence/batch001-rows002-007-015-erc20-cost-origin-20261018.json)：**#015 HODL** 一笔第三方交易转入、两笔路由转出，代币入出一致、卖出两区块 BNB 余额合计增加 161287873766664482 wei，但资金取得成本/交易内部回款归因仍无证据，不能认盈利；**#007 BSC-ETH** 两笔外部转入、一次转出，代币全部移走，后者区块级 BNB 余额增加 40938120000000 wei，不能当净利润；**#002 FTR** 5笔转入、同一交易内6条转出、期末仍有 4143143596856588493468792 raw 持仓。FTR 转出流向来源清单 #001/#006 是明确的链上关系，**不是同人控制证明**。

[分析、未决成本和下一核验条件](../state/batch001-erc20-cost-origin-20261018.md)。[机器可重复核查工具](../tools/verify_transfer_provenance.py) 与 [10项离线测试](../tests/test_verify_transfer_provenance.py) 已通过，门禁明确拒绝把被动转入记为零成本、把多个转出日志记为多个盈利卖单。所有三个钱包及其完整盈亏依然未决。该轮没有新的已证明盈利或亏损闭环。


## 2026-10-18：HODL 上游经济成本与跨钱包分发关系（#015/#016）

[新链上资金上游证据](../evidence/batch001-hodl-funded-distributor-lineage-20261018.json)：`0x1c2b…6e3f` 两次直接向 BSC 路由支付合计 **0.425046148539676102 BNB**，相应区块钱包 BNB 余额减少 **0.426177349239676102 BNB**，收到约2,435万 HODL，随后一次分发给6个钱包；其中原始名单 **#015/#016** 均在收款后两次转出全部 HODL。六人分发合计 `20582363267535883637548391` raw，上游仍留 `3770187907347020068657211` raw，整数守恒。

**不能自动推断：**不证明这6个地址属于一人、没有收款地址各自的经济取得成本、上游源支付不能比例摊派为下游成本、#016 首次退出高度钱包**另外有签名交易（nonce +4）**；该块的 BNB 余额增量不能直接作为单笔退出回款。#015/#016 以及所有钱包整体盈亏仍 `UNRESOLVED`。

[独立上游/收款守恒报告](../state/batch001-hodl-funded-distribution-20261018.md)、[通用成本归属拒绝门禁](../tools/lineage_gate.py)、[10项通过的合成测试](../tests/test_lineage_gate.py)。下一阶段转到其它低频候选的**真实成交和亏损**，而非无期限重复HODL归因。

## What is complete, what remains

- **Completed & durable:** BSC first-20 signed nonce census with immutable block bounds, fully closed row016 RTX5090 and rows002/004 sauce single-token profit and loss-aware evidence records, issuer labels preserved untrusted.
- **Incomplete:** all 20 wallets' complete 30-day and lifetime aggregate realized PnL; row016 other trades and rows002/004 non-sauce trades; other EVM networks beyond BSC/Ethereum/Base; unexpected token/stablecoin sales, passive token spam, cross-wallet movements and USD time matching. **No verified loss roundtrip within this specific first-batch audit yet; do not assert zero losses.**
- **Next action:** loss-aware per-token audit for rows001/003/006/007/015 and other assets in 002/004; HODL row015 has unresolved historical token inventory movements, must retain as PNL_UNRESOLVED. High-frequency 014/016–020 receive bounded pagination/deferred status, and other EVM chain coverage must be assessed; Ethereum/Base nonce scans for the batch are already complete. Keep `batch-001=PARTIAL` until gate closure. Then move batch 002 rows 021–040 while preserving deferred issues explicitly.
- **No production authority:** No trades, alerts, live scanning, deployment, Gmail or automations. Existing Frank, Monster, Mission portfolio and price-monitor states untouched.
