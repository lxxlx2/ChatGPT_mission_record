# BSC Meme 地址模型 V1：P3 完整 37 笔原始交易核查与 P4 23 钱包交叉资格初检（2026-10-13）

**Scope:** 23 已冻结 EOA × 19 exact CA，30 天链上窗口 `2026-09-13T08:37:36Z` 至 `2026-10-13T08:37:36Z`。**Status: P3 PARTIAL EVIDENCE COMPLETED / P4 PRELIMINARY RESEARCH_ONLY / NO_GO**。本报告只确认证据进度，不发布交易信号、盈利排名、买入意见或新的监控。

## 原始问题及高优先级边界

原始目标是在 BSC Meme 重大机会中找出**跨多个可交易大行情反复实际获利，且 2026 年仍本人主动成交，可供未来手动参考**的多个公开钱包。**实际可跟单获利**还需 P4 资格与 P5 延迟 1/5/15 分钟独立成交复盘。保留所有负回合、未完成、非本人、无原始回执、未知报价、未知交易场所等负面/不确定证据。项目内的 `bsc-meme-address-model-v1-requirements-2026-10-13.md` 及 `bsc-meme-address-model-v1-implementation-plan-2026-10-13.md` 优先于研究过程中的主观判断。

## P2 沿用证据，不得写成收益率

23 钱包、50 个历史选样已闭合库存签名回合，32 正向、18 负向，但仅 7 钱包有经济来源记录，16 钱包尚无导入回合。源 `bsc-meme-address-model-v1-p2-economic-comparison-2026-10-13.json`（Git blob `94f0de2439171d173a13b5ed82560ec4bf623c9b`）。**正向/负向是原生钱包区块余额范围或已存的混合报价参考的选样符号，不能代替因果可归属的全部实收利润。** 不能计算或推断本次样本外总胜率和钱包收益排名。

## P3 全量原始来源范围与完整核查

- 冻结 23×19 exact-CA 正值 Transfer 查询的 46 个方向全部完整分页：严格 30 天内 89 条 ERC20 Transfer，8 个钱包有 exact-CA 转账，15 个没有。没观察到这 19 CA 的 Transfer **无法确认在其他 Meme 上不活跃**。
- 75 个钱包×原交易关联，去重 71 原交易哈希，70 个原始 `from` 完整可解析、1 个截断。分类：38 本人发起关联，36 第三方发起关联，1 原始 signer 未定。先验冻结除上轮 A83B/TST 以外的全部 37 个原交易；**37/37 收集回执状态，37/37 用独立历史块 exact-CA `eth_getLogs` 核对 Transfer，37/37 检查指定直接转账对手地址的 Swap topics**。
- 37 条本批回执：4 条回执完整、33 条响应因接口截断不完整；32 条能直接读到 `status=0x1`，5 条状态头未取得。单看状态头不能证明真实 Swap。
- 37 条中，23 条存在**同笔哈希、实际 token 转给/来自池、该池 emitted Swap 事件**。对应的 11 个唯一池子均在各自最早涉及区块读取历史 `token0/token1`，且 exact CA 是该池代币之一。针对剩余 14 条又独立检查了标准 Uniswap V3 `Swap(address,address,int256,int256,uint160,uint128,int24)` topic；仍未发现直接对手池的新增 Swap。**不代表这 14 条没有经过其他跳转路由交易**。
- P3 **门禁通过 19 个新增本人真实池 Swap**，其中均有原始本人发起交易、可读成功回执状态、same-tx 指定代币真实流向、池 Swap 事件、历史池身份。另 4 条有池 Swap 但回执成功状态不可独立读取，严格保留 `POOL_SWAP_SEEN_RECEIPT_STATUS_UNRESOLVED`；其余 14 为 `NO_DIRECT_POOL_SWAP_SEEN_ROUTING_UNRESOLVED`，不得写 `NO_TRADE`。
- 加上上轮原始完整回执的 A83B/TST 1 笔，**合计 20 笔已通过严格链上门禁的近期真实本人池 Swap，分布在 7 钱包**。这 20 笔的全部 quote 到本人 EOA 最终净结算、Gas、利润、跨币结算与可复制 Alpha **尚未完成**。

代码：`bsc_meme_address_model_v1_p3.py`、`bsc_meme_address_model_v1_p3_swap.py`、`bsc_meme_address_model_v1_p3_batch.py`；新证据为 `owner37-*-part*.json`、`pool11-historical-part*.json`、`missing14-standard-v3-part*.json` 和全部前置不可变 selection manifest。最后 UTC 源：`bsc-meme-address-model-v1-p3-7wallet-latest-verified-swap-utc-2026-10-13.json`。

## 7 钱包最近本人 Swap 与 P2 历史采样横向表

时间均为 frozen 19 exact CA 范围内**最新可严格验证的真实本人 Swap UTC**，不是钱包最近的任何资产操作；P2 均为先前已选历史原生/混合报价符号，与这 20 笔 Swap 的已实现利润无直接对应关系。

| 钱包 | P3 本人池 Swap 已核实笔数 | P3 最新已核实 UTC | P2 已选完整库存回合（正向/负向） | P2 不同重大 CA 正向数 | P4 分层 |
| --- | ---: | --- | --- | ---: | --- |
| A83B (`0xa83b73f5…548811`) | 10 | 2026-10-12 07:57:23 | 4（0/4） | 0 | 近期真实交易，经济证据不足 |
| DDAC (`0xddac928a…002127`) | 1 | 2026-10-06 11:16:54 | 6（5/1） | 2 | 研究优先候选 |
| 0ABB (`0x0abb84c9…9f1fd8`) | 1 | 2026-09-22 15:37:36 | 0（0/0） | 0 | 近期真实交易，经济证据不足 |
| 2ADF (`0x2adf961b…5475ba`) | 4 | 2026-09-20 13:18:20 | 5（4/1） | 2 | 研究优先候选 |
| 4985 (`0x498528e3…bd99a`) | 2 | 2026-09-19 05:36:37 | 0（0/0） | 0 | 近期真实交易，经济证据不足 |
| 8E6B (`0x8e6b3c9c…4e9ea0`) | 1 | 2026-09-15 04:34:39 | 17（10/7） | 5 | 研究优先候选 |
| ADFF (`0xadffbebbd…9e3946d`) | 1 | 2026-09-14 06:02:53 | 7（6/1） | 2 | 研究优先候选 |

其余 **16/23 钱包近期真实本人 Swap 仍 `UNRESOLVED`**，不能判定全部停止交易。且此表不是 2026 年 / 全 BSC 的交易活跃榜。

P4 统一机读横向矩阵：`bsc-meme-address-model-v1-p4-p2p3-readiness-matrix-2026-10-13.json`。全部 23 钱包留行、P2 50 已选原样保存；仅 4 个有“最近已核实真实 Swap + ≥2 个重大 exact CA 历史样本正向”的**研究优先**：2ADF、8E6B、ADFF、DDAC。它们不满足最终真实归因已实现盈利、合格重大机会、复制策略或盈利排行门禁。

## P4 报价资产身份直接链上核实（历史区块）

在 11 个原始池子中，部分并非 WBNB 直接报价。复核最早相关块的两个池组成代币地址，再对实际 quote CA 在同一历史区块查询 `symbol()` 和 `decimals()`：

| 原目标代币 | 交易池 | 已读取 quote CA / symbol | decimals |
| --- | --- | --- | ---: |
| 牛来 | `0x595d7097…9423` | `0x205812cdbed920aff76c6580abd681a46d11efc7`，QQQB | 18 |
| MARSCOIN | `0x94f3ed36…d8f1` | `0xbe9d156892e55e7154bcd3cb0fea677f9d3103e1`，SPCXB | 18 |
| 牛来 | `0xe5ae3183…126` | `0x55d398326f99059ff775485246999027b3197955`，USDT | 18 |

机读 `bsc-meme-address-model-v1-p4-nonnative-quote-token-identities-2026-10-13.json` 同时归档原始 ABI 返回值和链上区块。**QQQB/SPCXB 的名称和 symbol 不能换算成美元，更不能把原钱包的 BNB 区块变化等价于这个非原生报价交易的实现利润**。需要真正的历史报价和成交结算路径后才能做 P4/P5 资金经济比较。

## 已验收内容、尚欠门禁

- 原研究 Draft PR #40、P0/P1、P2 历史来源仍保留。**独立其他 AI Review 尚未完成**。
- 固定代码及 P2、P3、P4 横向矩阵测试：GitHub Actions `https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38392188833`：**93 + 9 = 102 项离线 unit regressions PASS**，P3 37 笔回放以及 P4 23 行 Git JSON 精确对照同时 PASS。未测试真实 Mac 上的只读部署，也未接入任何正式运行时。
- P4 下一主线：对 4 候选先核查真实资金来源、关联/同控证据的等级、首次可交易时刻和历史池深度；必须先冻结重大市场机会 U 的可执行起点，才允许按资格计分参与/漏买。保留对应负面与不活跃样本，16 个 UNKNOWN 不得从统计分母中静默消失。
- 对 4 个 receipt 状态不可读、14 个复杂路径可另列审计队列并按研究优先级处理。避免被少量边界限制卡住整个 P4。
- P5 使用第三方首次可观测信号起点及严格历史 1/5/15 分钟下单和卖出路径，必须包含流动性、gas、手续费、税费、不能成交、错过起点、账户余额与多钱包关系。不使用未来价格和结果调参数。
- G6 独立其他 AI Review、完整测试/只读本地实测需按开发流程继续；未经单独用户授权不安装生产，不开启真实交易、Gmail、alert、automation，Frank/Monster 完全不改。**PRODUCTION_TRADING=NO_GO**。

