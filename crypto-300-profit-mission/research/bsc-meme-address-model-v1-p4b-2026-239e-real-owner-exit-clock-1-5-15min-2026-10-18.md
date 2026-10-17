# P4-B 2026：239E 原本人真实交易时间与 1／5／15 分钟信号退出状态

日期：2026-10-18。PR #40 Draft，严格选旧 23 EOA × 19 CA 已知真实一负一正的 239E 龙虾两轮。先在 [四笔签名原交易与时间请求预冻结](./bsc-meme-address-model-v1-p4b-239e-original-4tx-real-historical-time-prefreeze-2026-10-18.json) 中确定两轮各一笔首买／最终卖的固定交易哈希和所属区块。随后 Alchemy BNB 主网四次只读 eth_getTransactionByHash，**4 次返回完整可解析 JSON（工具端响应没有截断），0 次重试**；选定的 signer/from、nonce、value、交易块和 blockTimestamp 等字段单独归档到 [四笔原交易时间证据](./bsc-meme-address-model-v1-p4b-239e-four-original-tx-real-blocktimestamp-2026-10-18.json)。仍非提供商传输层逐字节包，但比以前的 provider 截断块头强。

## 真实链上时钟对照

| 原本人钱包回合 | 买入块 | 最终卖出块 | 两块链上 timestamp 差 | 买后 +1min | 买后 +5min | 买后 +15min |
|---|---:|---:|---:|---|---|---|
| R1：本人净亏 −0.015332805033002259 BNB | 85954137 | 85957578 | **1,550 秒（25分50秒）** | 最终卖出尚未发生 | 最终卖出尚未发生 | 最终卖出尚未发生 |
| R2：本人净赚 +0.022647938898252522 BNB | 85959961 | 85961371 | **634 秒（10分34秒）** | 最终卖出尚未发生 | 最终卖出尚未发生 | **最终卖出已经发生** |

R1 首买 blockTimestamp 为 0x69b14658、卖出 0x69b14c66；R2 首买 0x69b15097、卖出 0x69b15311。这里的秒数是**确切两个区块头共识时间戳**之间的差，不是默认 BSC 每块两秒的估算，不使用 Pair.getReserves 的 blockTimestampLast 冒充区块时间。

R1 在选定本人签名历史里的两次买入与最后卖出，最终退出是在 +15 分钟以后；R2 虽然原主人自己获得净正向结算，但 +15 分钟时他的完整已选回合已经关闭。所以如果把“原钱包仍持有”作为可执行信号的一个条件，**R2 首笔买入信号在 +15 分钟已经不符合条件**，不能拿这轮后验正收益证明 15 分钟才发现机会的人还能复制。

## 两条必须分开的证据等级

[源 SHA 锁定时钟复算](./bsc_meme_address_model_v1_p4b_239e_4tx_real_clock.py) 独立加载原 239E 两轮真实买卖和净额、当次四笔可解析原始交易字段、预冻结，以及前一批 [八次真实固定 V2 数学报价](./bsc-meme-address-model-v1-p4b-239e-dragon-two-exit-v2-two-sided-math-readback-2026-10-18.json)，检查钱包／交易哈希／原交易 native value／区块时间，固定 +60/+300/+900 秒，只判定**选定本人最终已成功签名卖出是否在各截止时间之前上链**。[11 项对抗测试](./test_bsc_meme_address_model_v1_p4b_239e_4tx_real_clock.py) 反驳改原签名、改日期、改角色、改 cutoff 或把这个结果夸大成外部跟单盈利。

仍然不能推出：这三个截止时刻实际完整 ERC20 余额（本轮未各自重新调用该任意区块余额）；第三方在何时看到原钱包真实买入；真实交易者能否在 +1/+5/+15 分钟下单，是否有足够 WBNB 余额、合约允许买卖、实际收多少币／付多少 Gas／Tax、回款是多少。V2 两条数学报价的分别 N+1 和 S−1 时间也不等于以上分钟截止点，更不是假设 0.01 WBNB 的状态化买入卖出。

**下一阶段有价值的突破**不是持续叠加历史报价，而是寻找冻结原 19 exact CA 已有真实外部钱包成功签名买卖且包含真实交易时间、实际收币、Gas、退出的正负样本，并核实买家在原买信号 +1/+5/+15min 是否可观察并实际下单。同一人最终卖出后的旧 signal 必须是独立新回合才重新有效。P4-B=PARTIAL、PUBLIC_EXECUTABLE_U=UNRESOLVED、P5=BLOCKED、PRODUCTION=NO_GO、NO_MERGE／NO_DEPLOY／NO_GMAIL／NO_TRADE 保持不变。
