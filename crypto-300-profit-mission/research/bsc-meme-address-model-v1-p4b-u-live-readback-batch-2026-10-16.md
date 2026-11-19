# BSC P4-B / U：2026 三个早期真实买入样本，Alchemy BNB Mainnet 只读复核

日期：2026-10-16 Asia/Bangkok。研究 Draft PR #40；**本报告和附带三个新 JSON 是批准后新增的研究材料，不在已批准的 SHA 内，且不能继承该 SHA 的审查结论。**

## 已关闭的代码审核门禁

收到用户转达的独立审查结论：固定 `47945ca77806d23d942fa2abb681c70244e273a7` **APPROVE**，仅覆盖 P2 近期 Swap 三态修复和该 SHA 的固定来源与回归执行范围；旧 `9b82f932d60ef8945375091ec5b0dd0bf2753b53` 继续 `REQUEST_CHANGES`。独立审查在目标 detached checkout 通过 P4-B 专项 13/13、广义 BSC 回归 382/382；PR merge-context 关联四套 CI 成功。**本开发会话没有重做该审查或在 CI 中执行实时 RPC**。已单独写入 [PR #40 审核结论记录](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40#issuecomment-6199564733)，没有提交与 GitHub 身份不对应的假冒人工 APPROVE。

## 本轮实际只读链上查询

范围严格限制在冻结的五钱包/三 CA 研究批次中的**三个 2026 市场早期买入证人交易**，原始市场矩阵 Git blob `c42ad01e896f30262f89f7852f927fc84fb3ea18`。Alchemy app 为只读多链监控应用；网络 `bnb-mainnet`。实际逐例执行 `eth_getTransactionByHash`、ERC-20 `Transfer` topic 的 `eth_getLogs`（从冻结首个已观测 ERC-20 Transfer 区块到固定早期买入区块）、`eth_getBalance` at `N-1` and `N`、原区块头、交易回执。FLAP 两例额外执行历史 `balanceOf`、`decimals` 和精确区块、按买家 topic 过滤的报价代币转入及转出 `eth_getLogs`。

| 预冻结机会 | 实际样本买家签名人 | 买入区块 | 已读取原代币 Transfer 数 | 样本前 BNB | 样本所在区块 BNB 差额 |
|---|---|---:|---:|---:|---:|
| 龙虾 | `DDAC (0xddac928a…002127)`（冻结 23 钱包内） | 83635776 | 4 | 17.806507402194926070 | −0.809007576999999996 |
| 牛来 | `0xb0d0c4c1…9484d9`（冻结 23 钱包外） | 115628774 | 4 | 0.055527722292177968 | −0.000068119205380800 |
| MARSCOIN | `0x504ba7b1…2dde3ea`（冻结 23 钱包外） | 112441394 | 5 | 4.225374413948780923 | −0.536281148634919080 |

逐例 Tx 的 `from` 与上述签名人一致，且目标 CA 的 `Transfer` 事件确实将代币转入原买家；截取到的原回执 `status=0x1`。只读接口对三个交易回执均返回**截断 JSON**，所以本轮**没有**把回执标为可完整解析，也没有再次声称全部 receipt/logs/Gas/内部 trace 闭合。

更具体地：
- 龙虾原交易 `0x35793699fbf006cfb07d5775991f50c106af64ea840db10a2f580b4661a0df12`，交易本身 `value=0.8 BNB`；原钱包所在区块本币余额下降约 `0.809007576999999996 BNB`，**区块余额差不是自动等于该交易总成本**。
- 牛来原交易 `0xcb89b7adafacdfb5f844102c4e27ed474abec8947c74476d461be70a9b0e8fa5`，`value=0 BNB`，不能从很小的原生 Gas 余额变化推出“零投入交易”。
- MARSCOIN 原交易 `0x6bb75edb235d86747fcaa1b6f13c820601973fe840ef22eb54aa22e54d36d028`，`value=0.536188664994919080 BNB`；不能把它与当前 metadata 标注为 S5B 的内部事件报价直接混为一谈。

### 关键新限制：原钱包报价币真实支付仍未闭合

| 早期交易 | 来源报价 CA | 原事件归档 cost 原始整数 | 买家 N−1 的报价币余额原始整数 | N 区块买家该报价币 Transfer |
|---|---|---:|---:|---|
| 牛来 | `0x205812cdbed920aff76c6580abd681a46d11efc7`（来源当前 metadata Q3B） | 205991990065603310 | 11376929809701619 | 入 0，出 0 |
| MARSCOIN | `0xbe9d156892e55e7154bcd3cb0fea677f9d3103e1`（来源当前 metadata S5B） | 2674483304192706318 | 0 | 入 0，出 0 |

该报价 CA 两例在对应历史区块的 `decimals()` 都返回 18，`balanceOf` 前后相同；两笔样本所在区块没有检索到目标买家**直接**该报价代币的 indexed ERC-20 Transfer。这个结果与事件报价中的 raw cost 不可直接对成钱包余额支付；潜在原因包括项目合约内部报价/中间路由/原生支付换算等，**任何一种都尚未确认**。不能据此宣称早期交易失败、项目诈骗、钱包花费为零，亦不能把来源报价币按名字当作 WBNB/USD；后续若要闭合需逐步核对 launchpad 实际成交函数与完整资金回执，而不是改写成本或隐藏负样本。

### 可审计链上原始读取档案

三个 append-only JSON 保留实际 `eth_getTransactionByHash` 原 JSON、指定 CA 和区块窗口的完整 `eth_getLogs` 返回数组、`N-1/N` 原生 wei、区块头可读取字段、receipt 截断标记以及 FLAP 历史报价 ERC-20 `balanceOf/decimals/Transfer` 查询条件与结果：

- [龙虾 DDAC 早期买入](./bsc-meme-address-model-v1-p4b-u-live-early-buy-lonxia-2026-10-16.json)
- [牛来 FLAP 外部买家](./bsc-meme-address-model-v1-p4b-u-live-early-buy-niulai-2026-10-16.json)
- [MARSCOIN FLAP 外部买家](./bsc-meme-address-model-v1-p4b-u-live-early-buy-marscoin-2026-10-16.json)

**等级与局限：** 这里只证明三笔**有选定市场证人/买家实际签名**及有界观察的 token logs/历史余额。不是全网最早买入的穷尽证明，不是区块时刻对公开第三方可观察的 earliest U，不是同刻确有**买与卖都可以成交**的历史流动性/费用/税后容量，不是五钱包的完整交易史或 1/5/15 分钟实际跟单收益。三个样本此前已被研究者看到，不是 untouched holdout。冻结 23×19=437 的分母与五钱包三 CA 容器不变；不得把两个外部买家收入 23 EOA 成功次数。

## 紧接下一阶段的有界开发目标

1. 先以 **DDAC／龙虾** 的真实早期 Four.meme 交易为最小完整案例，重新锁定第三方只读观察者最早何时能从可公开链上事件/确认区块看到可信买入信号（必须明确是本交易前还是本交易后），不能把签名人交易所在区块当作外部跟单入场。
2. 在同一历史可见时点检验 launchpad 真实 **买入和退出路径**，起码一笔可售的投资者规模测试，税费/Gas/实际路由、资金约束。**V2 历史公式报价不能替代当时 Flap/Four.meme 实盘执行。**
3. 批量处理牛来、MARSCOIN 的真实早期交易，但二者市场证人为**非冻结候选买家**，当前优先作为跨钱包归属、报价语义与失败控制，不能变成 2ADF/A83B/877AF 的早期交易。遇到完整回执截断或免费接口不可证实的路径，用 `UNRESOLVED` 停止，而非无期限抓取。
4. 只有确认公开 U、真实可买和可卖、资金容量与源钱包经济闭合，才在**不暴露的独立 2026 留出集**上启动 P5 1/5/15 分钟回放。禁止事后为回放结果调整阈值。

**本批结果：`P2_CODE_REVIEW=APPROVE@47945`; `P4-B FIRST PUBLIC EXECUTABLE U=0/5 PROVEN`，即 `UNRESOLVED`；`P4-C=PARTIAL`; `P5=BLOCKED`; `PRODUCTION=NO_GO`; `NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。**
