# Mission BSC Meme 地址分析 V1 — 原 23 个 EOA 跨所有代币的 30 天真实活跃度筛选（2026-10-19）

## 一、业务目的与项目边界

原 19 CA × 23 EOA WebSocket 在用户 Mac 上完成 120 秒真实订阅，但 **0 条匹配转账**。因此先确认“这 23 个钱包到底是否还在 BNB Chain 活动”，不继续扩大历史样本的代码边界，也**不涉及新建的独立地址分析模块**。本轮选择固定 **30 天全链钱包主动发送交易 nonce** 作第一道低成本筛选门禁，与原 19 CA 历史收益研究严格区分：活跃 `!=` 有经济买卖 `!=` 盈利 `!=` 可跟单。没有创建自动监控、修改钱包、合并 PR、部署或发 Gmail。

- 冻结原钱包/市场母表：`bsc-meme-address-model-v1-p4b-23x19-early-opportunity-ledger-2026-10-14.json`，Git blob `f88ed9abfcb0f321ec31e98a029303aca48a8623`；23 EOA 和 19 个历史 CA 一个都没改。
- 实际 RPC：用户已连接 Alchemy `ChatGPT Crypto Monitor All Chains`，`bnb-mainnet`，`eth_chainId=0x38`；只读 `eth_getBlockByNumber`、23×两点 `eth_getTransactionCount`、少量 `alchemy_getAssetTransfers` 和 `eth_getTransactionByHash`。
- UTC 截断准确区块：起点 `#122654260`，`2026-09-18T18:34:56Z`；终点 `#128411164`，`2026-10-18T18:34:56Z`。两个原始区块哈希详见 [完整逐地址结构化来源摘要](./bsc-meme-address-model-v1-p4b-23eoa-full-market-30day-activity-screen-2026-10-19.json)。不是大致按区块速度猜 30 天，起止 timestamp 均已从真实区块请求比对。
- 每地址结果：`nonce(endBlock)-nonce(startBlock)`；它严格表示**这个时段的 EOA 主动签名发送交易笔数**。包含非交易、失败交易与可能高频自动调用；不包括只因被动转账而出现的“fromAddress tokenTransfer”日志。注意本地 API 响应没有完整存档，只记录 23 个差分值及来源 RPC 的完整重放参数，后续审查者可独立重取。

## 二、全部 23 地址排序

已取得 23/23 双区块 nonce 回执，14 有增加，9 没增加；8 个地址 30 天主动发送交易大于等于 1,000 笔。

| 排名 | EOA 缩写（全地址在 JSON） | 30天发送交易 | 研究分层 |
|---:|---|---:|---|
| 1 | `0xa83b73…548811` | 53,452 | 高频 / 交易类型待拆解 |
| 2 | `0x877af2…f1aaac` | 9,106 | 高频 / 交易类型待拆解 |
| 3 | `0x0abb84…9f1fd8` | 6,677 | 高频 / 交易类型待拆解 |
| 4 | `0x2b40f8…f70d2b` | 4,649 | 高频 / 交易类型待拆解 |
| 5 | `0xddac92…002127` | 4,415 | 高频 / 交易类型待拆解 |
| 6 | `0x498528…5bd99a` | 1,428 | 高频 / 交易类型待拆解 |
| 7 | `0x2adf96…5475ba` | 1,306 | 高频 / 交易类型待拆解 |
| 8 | `0x8e6b3c…4e9ea0` | 1,258 | 高频 / 交易类型待拆解 |
| 9 | `0x8d8c03…23ae25` | 25 | 低频 / 待观察 |
| 10 | `0xadffbe…e3946d` | 15 | 低频 / 待观察 |
| 11 | `0x5c48a7…52387c` | 9 | 低频 / 待观察 |
| 12 | `0xd70ce4…bec678` | 5 | 低频 / 待观察 |
| 13 | `0x5c0c5d…607583` | 4 | 低频 / 待观察 |
| 14 | `0xbeb713…6e2ffc` | 4 | 低频 / 待观察 |
| 15 | `0x239e74…cfb337` | 0 | 近30天未见自主发送交易 |
| 16 | `0x9d1240…eca35c` | 0 | 近30天未见自主发送交易 |
| 17 | `0xcceea3…9d8037` | 0 | 近30天未见自主发送交易 |
| 18 | `0x11a732…ab98d8` | 0 | 近30天未见自主发送交易 |
| 19 | `0x3638cd…2bc203` | 0 | 近30天未见自主发送交易 |
| 20 | `0x4789f1…5856d5` | 0 | 近30天未见自主发送交易 |
| 21 | `0x47b871…f1b429` | 0 | 近30天未见自主发送交易 |
| 22 | `0x57c98b…b0cbf4` | 0 | 近30天未见自主发送交易 |
| 23 | `0xe54bdc…2dc568` | 0 | 近30天未见自主发送交易 |

**不能把 9 个零增量地址写成“钱包空了/项目跑路/链上没有任何代币活动”**；它们只是在这两个固定区块间没有自主签名发送的交易。Alchemy `getAssetTransfers` 的 token `from` 可能在另一个交易签名人调用的 ERC20 合约中出现，例如原 `239E` nonce 不变但 still 有发出方向 Token Transfer event，足见必须分开判断“token 所属人”和“交易发起人”。

## 三、跨越旧 19 CA 的实质新发现

对 23 EOA 均执行小额、有界最新 `fromAddress` 转账查询（最多各 4～6 行，**绝不是完整 30 天所有转账**）。其中高活跃钱包的最新 token CA 普遍不在原先冻结 19 CA 中。

从中挑选**六笔独立按原始交易哈希读取 `eth_getTransactionByHash`、证实 `transaction.from` 即钱包本人的样本**。六笔 `transaction.to` 都为 `0x1de460f363af910f51726def188f9004276bf4bc`、输入方法前四字节均为 `0x4d819a2a`，是同一个 swap 风格的路由接口；不能因此把完整 quote token 成本、买入/卖出方向或成功退出当成已证实。

| 主动钱包 | 关联代币显示名（未经价格或防伪认证） | 精确 CA | 已核实的本人签名 TX | 证据等级 |
|---|---|---|---|---|
| `0xa83b73…548811` | `한화` | [`0x59d87d…127777`](https://bscscan.com/token/0x59d87d46f53b1bdefcd406e8a20f059a92127777) | [`0xb4e4a141…`](https://bscscan.com/tx/0xb4e4a141ae885d1166a1363f79f5befb593d6f2308c036c009a2dd9f0ceb7b12) | 原 signer 符合；未确认整个买卖回合 |
| `0x877af2…f1aaac` | `尤栗` | [`0x1bd0d6…c07777`](https://bscscan.com/token/0x1bd0d654e44a78d9b20dcf09fa61100013c07777) | [`0x34d72b0f…`](https://bscscan.com/tx/0x34d72b0fd8c840a5d47baf1ec455c4988154e22ff2d203e054ae393b1e5bdec9) | 原 signer 符合；未确认整个买卖回合 |
| `0x0abb84…9f1fd8` | `币安手机` | [`0x61c5a2…3f7777`](https://bscscan.com/token/0x61c5a28fe580d7cc79bdcc67f0023e3f503f7777) | [`0xd2ae8b6e…`](https://bscscan.com/tx/0xd2ae8b6edef3ee9e773c63f76466af1758668cdecfb2867ba9d81e1530a3a1e3) | 原 signer 符合；未确认整个买卖回合 |
| `0x8e6b3c…4e9ea0` | `FLAP` | [`0x3b7a5c…5c7777`](https://bscscan.com/token/0x3b7a5c1519731e555782bb623adfb9cfca5c7777) | [`0x9d6c8d64…`](https://bscscan.com/tx/0x9d6c8d64d24367f2f52cdcdb9cebe84c7462209b71ba291377a9056000ac6559) | 原 signer 符合；未确认整个买卖回合 |
| `0xddac92…002127` | `Fâché` | [`0x9ec1c7…8c7777`](https://bscscan.com/token/0x9ec1c7fc2cbd74ad0f9badd0c6b7e7260e8c7777) | [`0xcee9ee07…`](https://bscscan.com/tx/0xcee9ee0722a29699906a8acaefbfa568b924ae805392ad385e0deec3a674a22e) | 原 signer 符合；未确认整个买卖回合 |
| `0x2adf96…5475ba` | `yoki酱` | [`0xa96402…5c7777`](https://bscscan.com/token/0xa96402db0112ed21a6613b43cdfb766d9e5c7777) | [`0x092edd1d…`](https://bscscan.com/tx/0x092edd1dc44a7b1671d0e6de1e7594bca1b9129a6c12a7ea9967c0326e235c6a) | 原 signer 符合；未确认整个买卖回合 |

上面六个显示名仅为索引 API 返回的合约自报 token symbol，可能伪造、乱码、仿冒 BNB；**所有计算一律依精确 CA，不按名字**。这六个新 CA 都不属于原来冻结的 19 个历史 CA。所见单次代币向外转账不等于签名卖出，更不等于卖出收到稳定币或 BNB。本轮没有取得完整双向 receipt 的净资产流、真实 Gas、真实 quote 回款、开始持仓来源和 60/300/900 秒公平执行价格，因此 23/23 的**可靠已实现净收益都标 UNRESOLVED**。

## 四、可用性优先的下一批，不反复追历史一笔

不按“交易笔数越多越赚钱”推荐交易。结合当前原始链上主动交易次数与当前代币 CA 的发现，建议下一批先选：

1. **877AF**（9,106）：旧 19 CA 范围下可误判为不活跃，新样本有本人签名、完整 token CA 可跟进；优先查最近一个已买已卖回合及其真实收款。
2. **DDAC**（4,415）：有之前冻结的历史正负案例，可做近期非旧 19 CA 的样本外对照，不能沿用旧正收益。
3. **8E6B**（1,258）：活跃度中等，相对高频钱包更有必要先核查买卖间隔是否可跟单。
4. **2ADF**（1,306）：近期另一个原钱包 signer 的路由样本，可独立观察同类新代币表现。

**A83B**（53,452）与 **0ABB**（6,677）等列入高频观察对照：不排除高频/自动化造成普通跟单延迟期间价格条件完全不同，若无法找到可重复真实资金正负完整回合即降级。**4985**（1,428）及 **2B40**（4,649）目前暂不盲目归为 Meme 盈利钱包。

后续业务查询以真实交易哈希为单位：先问它是否 owner-signed 及 receipt 成功、到底买入还是卖出、实际投入何种资产、真实可出售 token 库存与回款、失败与 no-fill，再问 30 天已实现净回报；保留亏损和不能归因的案例。禁止只按代币转账总和算利润。

## 五、状态与停止点

**已解决：** 23/23 完整 30 天 EOA 主动交易活跃度初筛，排除原 19 CA 过滤误差；6 笔新 CA 原钱包签名交易已经实例抽查；真正高频/低频名单已有可复现链上基准。

**尚未解决：** 完整 30 天 token 交易分页、每钱包成本基础、买卖全链上资产流、诈骗同名代币核验、真实已实现盈亏、可信公网上首次发现 U、60/300/900 秒本金/成交/退出、生产。

代码独立 `APPROVE@f8e7ba21f466774b16ed1eef45f8ff31ff7f6243` 仍仅限其固定**旧代码 SHA**，本轮只新添研究数据/报告，不回溯更改已审核代码结论。下一步只读、分批审计上述四钱包各 1～2 个真实完整成交回合，不在没有新证据时扩大代码负向测试或自动启动新监控。始终 `P4-B/P4-C=PARTIAL / PUBLIC_EXECUTABLE_U=UNRESOLVED / P5=BLOCKED / PRODUCTION=NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。

## 六、进一步独立筛到两组新 CA 的本人签名入场与完整出账 Token 流

本轮未停留在 nonce 活跃排行榜。对 **8E6B 的 FLAP**（CA `0x3b7a5c1519731e555782bb623adfb9cfca5c7777`）及 **2ADF 的 yoki酱**（CA `0xa96402db0112ed21a6613b43cdfb766d9e5c7777`），使用 Alchemy BNB Mainnet 只读 `getAssetTransfers` 按 **钱包地址 + exact CA + 起止固定区块** 查询完整 Token IN/OUT；两者的 IN/OUT 查询均返回 `pagination=false`（该 30 天窗口内索引数据可以枚举到这一具体 CA 的全部回执）。随后按原始 TX hash 独立读取原 signer `from`、目标路由 `to`、原生 `value` 和调用 method；所有主进出交易都由对应原 EOA 本人签名。

| 地址 | 精确 token CA | 窗口内转入 Raw | 窗口内转出 Raw | 本人签名入场原生 value | 实际卖出 BNB 净回款 |
|---|---|---:|---:|---:|---|
| 8E6B FLAP | `0x3b7a5c1519731e555782bb623adfb9cfca5c7777` | `1293859551216114584142304` | `1293859551216114584142304` | **0.15 BNB** | **UNRESOLVED** |
| 2ADF yoki酱 | `0xa96402db0112ed21a6613b43cdfb766d9e5c7777` | `247790844884194236639000` | `247790844884194236639000` | **0.08 BNB** | **UNRESOLVED** |

证明的是上述**两个固定钱包对两个精确 token CA 的 30 天入出 Token 账面流水精确守恒（Raw 整数差为 0）**，分别有一个本人签名收到 Token 的入场调用，随后 8E6B 有 2 笔、2ADF 有 1 笔本人签名出币交换调用；将手续费拆成两条 Token Transfer 归集，不能只看给池子的部分就误算剩余库存。**不能借此证明窗口期初或期末没有历史遗留库存，也不能得出已实现净盈利。** 原始交易及每段原始 Token Raw 记录见 [两组新 CA 全量 IN/OUT 只读证据 JSON](./bsc-meme-address-model-v1-p4b-8e6b-2adf-two-new-ca-complete-token-flow-2026-10-19.json)。

真正的盈利结算仍卡在**真实卖出 BNB/quote 资金回到原钱包多少**、receipt 实际 Gas 和其他资金流：当前 Alchemy BNB 免费接入 `getAssetTransfers(category=internal)` 报 `-32602 unsupported`，`trace_transaction` 报 `-32600 requires Pay As You Go/Enterprise`，用户使用免费方案，**不得自动升级或自费试用付费接口**。本阶段及时停止，不靠推测、代币数量或单一 WBNB 流动性报价填写盈利。下一步若要核算，可用官方允许的其他免费来源取得逐 TX native internal trace/receipt，且必须能交叉验证 exact TX hash、start/end balance、Gas 与真实最终币种回款；无法拿到即保持 `ACTUAL_OWNER_REALIZED_NET_PNL=UNRESOLVED`。对 877AF 仍需继续分页完整 Token 流后才能做同等级结论；其他高频钱包不可自动类推。

## 七、免费原生余额双区块实测：增加真实金额但不能伪造逐交易盈利

继续实际读取两组本人交易的前一块和目标块 `eth_getBalance`、`eth_getTransactionCount`（总共 5 个目标区块，每个都有真实前后 BNB 余额及 EOA nonce），证据保存在 [8E6B/2ADF 原生 BNB 区块变化与不可单 TX 归因](./bsc-meme-address-model-v1-p4b-8e6b-2adf-signed-round-bnb-block-delta-unattributed-2026-10-19.json)。

| 钱包 | 目标交易区块 | 整区块钱包 BNB 净变化 | 同区块本人发送交易数 |
|---|---|---:|---:|
| 8E6B FLAP 入场 | `0x79d7283` | −0.150045929 BNB | 1 |
| 8E6B FLAP 出账 1 | `0x79d77c1` | +0.140223744 BNB | **2** |
| 8E6B FLAP 出账 2 | `0x79f7fc0` | +0.010165345 BNB | **2** |
| 2ADF yoki酱 入场 | `0x7a4257c` | −0.080045234 BNB | 1 |
| 2ADF yoki酱 出账 | `0x7a6133d` | +0.071015473 BNB | **2** |

**不能把上述出账区块余额增量直接记作被选 token 的卖出收入**。每个出账区块的本人 nonce 都增长 2，说明还包含另一笔本人签名交易；不能把一整个区块的 native 变化强行归因到唯一一笔 Meme token trade（还可能有同块被动入账）。准确实际 Gas 与原生币内部 trace 尚未取得，受免费 API 限制。用户追求的是真实可复现赢/亏，故本批明确输出 `NATIVE_BLOCK_DELTA_OBSERVED / PER_TX_NATIVE_PROCEEDS_UNRESOLVED / REALIZED_NET_PNL_UNRESOLVED`，不报看似精确的收益率。下一步必须获取交易级别的真实 internal value 以及其他同块交易归因才可升级。

## 八、两组新 CA 的完整归零＋同区块 approve/swap Gas 归因：可以给出有条件的盈亏候选

此前三个“退出区块 nonce+2”未能确认是否混有另一笔交换。本轮进一步实际使用 `eth_getTransactionByBlockNumberAndIndex` 在**每个退出区块按交易索引定位**第二笔本人交易，三组均证明正好是**先 `approve(0x095ea7b3)` 后 `swap(0x4d819a2a)`，且相邻交易索引**：

- 8E6B FLAP 第一次卖出：`#127760321`，approve index `13`，swap index `14`。
- 8E6B FLAP 第二次卖出：`#127893440`，approve index `107`，swap index `108`。
- 2ADF yoki酱 卖出：`#128324413`，approve index `13`，swap index `14`。

这些 approve 不是另一笔本金买入。五笔选择交易（两个入场，三个出场）及上述三个授权回执均返回 `status=0x1`。Alchemy 连接器在复杂 swap receipt 超 8KB 时会截断尾部 `gasUsed`，但保留了**每笔 receipt 开头的 `cumulativeGasUsed`**。严格依据同块相邻交易前后累计 Gas 差，能恢复真实 swap `gasUsed`；三个 approve 的完整 receipt 直接读取 `gasUsed=48984`。原交易均为 legacy `type=0x0`，`gasPrice=0x7270e00=120000000 wei`，与 approve receipt 的 `effectiveGasPrice` 相符。两笔买入也用前一序号 receipt 的累计 Gas 复算，与钱包块级实际 BNB 减少量**逐 wei 一致**，因此这次 Gas 不是估值或配额。

独立链上 ERC20 `balanceOf` 经 `eth_call` 证明：两位钱包在**入场前一块持有目标 token Raw=0**，入场后分别持有 `1293859551216114584142304` FLAP 和 `247790844884194236639000` yoki酱，最后出场区块末、30 天终点持仓均 **0**。两个 token 合约在历史 30 天起始块 `eth_getCode=0x`，不能将当时无合约的 `balanceOf` 返回 `0x` 错当有效余额；这里使用的是**真实开仓前一块返回完整 32 字节 `0`**。因此这两个**选定钱包与精确 CA 的样本已确认代币仓位完整归零**，不是仅推算 Token 流量。

现将区块级 BNB 余额变化与对应区块两个本人签名交易的 Gas 汇总，并以 `BNB EXIT GROSS (推导) = BNB BLOCK Δ + approve gas + swap gas` 得到**有条件的 BNB 退出回款**：

| EOA / 交易回合 | 真正投入 BNB | 出场 BNB 总回款（区块与 Gas 重建，待交易内部流最终鉴证） | 选定区块合计钱包净变化 | 占入场 BNB 的候选回报 | 持仓及时间 |
|---|---:|---:|---:|---:|---|
| 8E6B FLAP | 0.15 | **0.150497844237345206 BNB** | **+0.000343160277345206 BNB** | **+0.228774%** | 最后持仓 0；10m04s 开始卖，16h49m14s 全部卖出 |
| 2ADF yoki酱 | 0.08 | **0.071067120899666730 BNB** | **−0.009029761100333270 BNB** | **−11.287201%** | 最后持仓 0；15h48m13s 全部卖出 |

**特别重要的证据等级：上述百分比不是“已独立认证的实际已实现利润”，而是 `BLOCK_BALANCE_GAS_RECONCILED_CANDIDATE_UNATTESTED`。** 三个卖出块都用索引证实钱包发出的两笔交易仅为 approve + swap，且查询到钱包同区块的普通 `external` 原生 BNB 入账为 0；上述真实区块和 Gas 的 BNB 重建还与这些 swap 的 `minReturn` calldata 下限兼容。**但 BNB 仍可能由同区块的第三方合约内部转入，或出现未被跟踪的内部调用**。既然免费 Alchemy `trace_transaction` 与 `debug_traceTransaction` 明确不开放，尚不能单独隔离这些可能性，故资金归因必须停在候选等级。它比之前“整块 BNB 涨跌、完全不知道第二笔交易是什么”推进了实质一步，但仍不等于经过外部独立 trace 的真实结算。

[完整相邻交易索引、各笔原 Gas、入场区块逐 wei 对账、两笔出场净候选及可信边界 JSON](./bsc-meme-address-model-v1-p4b-8e6b-2adf-adjacent-approve-swap-gas-attributed-native-balance-2026-10-19.json) 可以独立复算。**资金收益非常微薄的 8E6B 正例并不足以证明“普通跟单者 1/5/15 分钟后还能盈利”；2ADF 大幅负例必须一并保留。** 不得据此给钱包打长期盈利标签，不得把高频 A83B 交易量当成收益率。

下一次真正提升经济证据等级的路径：使用免费可信公共 BNB 交易内链上 value trace，或者其他可认证的单笔原生到账信息，并确保同块外部/内部事件不会将与目标 swap 无关的 BNB 变化混入；没有该证据则将这两个结果保留为有条件的资金候选。**绝不升级付费 Alchemy 或凭报价反推出回款**。

