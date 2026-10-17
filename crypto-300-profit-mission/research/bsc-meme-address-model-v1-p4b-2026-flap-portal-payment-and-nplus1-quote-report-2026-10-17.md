# P4-B 2026 Flap：真实原签名买入的 Portal 报价币支付路径，与 N+1 双向历史数学报价

**日期**：2026-10-17 Asia/Bangkok。Mission [Draft PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40)。研究范围只含**已经冻结的**牛来和 MARSCOIN 两个 2026 年 Flap 市场；引用但不修改原 23 EOA × 19 exact CA = 437 单元与五钱包／四市场 pre-freeze。龙虾另有 Four.meme N+1 原证据；我踏马来了仍为没有本批已证明早期签名买入的市场对照。两个 Flap **已选中的早期签名买入见证**的外部买家均不属于原 23 钱包，因此不能计为这 23 钱包的投资机会收益或新增候选钱包。N 是已选中并独立核对的签名见证块，**没有覆盖创建块至 N 的全部交易来证明它是全市场最早买入**。

## 1. 先预冻结、然后实际读取；区分“静态报价”和“原交易到账”

A. [N+1 双向报价预冻结](./bsc-meme-address-model-v1-p4b-flap-major2-nplus1-roundtrip-math-precommit-2026-10-17.json) Git 先于 [实际回读 JSON](./bsc-meme-address-model-v1-p4b-flap-major2-nplus1-roundtrip-math-readback-2026-10-17.json)。仅 2 市场 × 2 `eth_call`，共 4 次，零重试。用官方 Flap Portal 事先在原仓库确证的 `quoteExactInput((address,address,uint256))` / selector `0xfc847c2b`。在原已证明签名买入块 N 后一个区块的区块末，按**其真实历史 ERC20 报价币**输入 0.01 原报价币，获得数学买入输出；同一 N+1 链状态再对该精确输出数量做反向 `quoteExactInput`。两次调用**互相独立且未修改状态**，不存在“先真实买入，再卖出”的合约执行，更不等于安全的可执行卖价。**原始 RPC 回读 V1 保持不可变。** 本轮 [N+1 V2 补充](./bsc-meme-address-model-v1-p4b-flap-major2-nplus1-roundtrip-math-supplement-v2-2026-10-18.json) 中的 buy/reverse `request`、`blockTag`、`from/value=null` 是**审核阶段依据历史选定 N、原始 V1 calldata 与预冻结参数事后重建的参数字典**，而非 Alchemy 服务商在调用时记录或回传的请求原文。重建得到牛来 `0x6e45ae7`、MARSCOIN `0x6b3b833`，证据级别为 `SCRIPT_RECONSTRUCTED_NOT_PROVIDER_CAPTURED`。门禁仅保证这些字段与 V1 及预冻结的**自洽性（SELF_CONSISTENCY）**，不能证明供应商实际收到过该 blockTag。

| 币 | 来源原买入 N → 试算 N+1 | 0.01 原报价币换取数学代币数量 | 反向数学报价 | 静态往返损耗比例 |
|---|---|---:|---:|---:|
| 牛来 | 115628774 → 115628775 | 1,775,984.542161547782102975 | 0.009572139608243558 Q3B 标签原币 | ≈ 4.28% |
| MARSCOIN | 112441394 → 112441395 | 238,701.037758398982247391 | 0.009211471514791789 S5B 标签原币 | ≈ 7.89% |

这些值是源自**两条独立的视图数学查询**的价差，不是成交后亏损或预期收益。原历史买卖税配置牛来 100/100 bps、MARSCOIN 300/300 bps；数学报价是否已经包含某种费用、真实税费转账、Gas、授权、可买卖路线、失败滑点及同状态持久化购买后反向交易，均不能简单由这个百分比推导。Q3B、S5B 仅当前元数据符号，历史 18-decimal 数量不是美元或 BNB 数值。公网第三方看到 N 区块信号的准确传播时点无法从 N+1 区块头恢复。**更重要的是，历史 N+1 区块末状态已经包含该区块内全部交易，若假设观察者在 N 区块确认后立刻操作，把 N+1 区块末数学报价当作当时可执行报价会发生区块内前视偏差。** 因此这里只叫 `N+1 block-end two static mathematical quotes`，不是已复原的因果跟单机会。

B. **真实原交易付款路由**，不使用静态数学假设冒充实际支付。先 [预冻结直接由原签名钱包转出 quote token 的单块事件查询](./bsc-meme-address-model-v1-p4b-flap-original-buyer-quote-outflow-precommit-2026-10-17.json)，每个原签名交易块 N 用对应 quote ERC20 `Transfer(from=EOA)` 筛选，两个完整 JSON 返回都是 `[]`。但这两份 `[]` 未在第二批 `to=Portal` precommit 前独立提交，Git 只能证实**先存在 from 查询 precommit，随后有 to 查询 precommit，再后来才归档回读摘要**；“from 查询已先得到空值后才决定 to 查询”是开发时序记录，未取得不可变提交证明。此时序等级为 `DEVELOPER_REPORTED_SEQUENCE_NOT_GIT_PROVEN`。这只说明这两个具体历史区块、具体报价 CA 下**没有原签名 EOA 直接转出这种 ERC20 的 Transfer**；不意味着交易免费或外层 EOA 没有其他资产成本。

根据开发时序记录，后续另有 [预冻结第二批 `Transfer(to=Flap Portal)` 单块调用](./bsc-meme-address-model-v1-p4b-flap-original-buy-quote-to-portal-precommit-2026-10-17.json)，每个币只查原报价 CA 的原买入区块 N。返回：

| 币 | 原外部签名交易 | 真实报价 ERC20 支付方 | Portal 收款数量 | 原 `TokenBought.cost` |
|---|---|---|---:|---:|
| 牛来 | `0xcb89b7ad…` | 中间合约 `0x9e698d…` | 0.205991990065603310 原 quote | **逐 wei 相等** |
| MARSCOIN | `0x6bb75edb…` | 中间合约 `0x1de460…` | 2.674483304192706318 原 quote | **逐 wei 相等** |

牛来在该块 `Transfer(to=Portal)` 精确命中 1 条；MARSCOIN 共有 2 条，其中第 2 条属于不同交易 `0x85e6a71e…`，**明确不算入原买家交易成本**。两笔被匹配的日志有原始真实交易 hash、收款 Portal 地址、报价币合约地址、完整 raw 数量和 logIndex，并与之前独立保存的原始 `TokenBought.cost` **原始整数完全相等**。

**原签名人原生币资金证据（按旧 Git 来源补全）：** 对两笔已选中的真实原签名交易，必须将 `tx.to` 和 `tx.value` 与“中间方 → Portal ERC20 收款”分开记录：

| 已选中见证 | 签名 EOA `tx.to` | 签名 EOA `tx.value` | 与本次 Portal 报价币付款方关系 |
|---|---|---|---|
| 牛来 `0xcb89b7ad…` | `0xb300000b72deaeb607a12d5f54773d1c19c7028d` 代理合约 | **0 wei（0 BNB）** | Portal 实际报价币付款方是**另一个**中间方 `0x9e698d…`；不能从 0 native 推导买家没成本，也不能确定 quote 资产原始来源 |
| MARSCOIN `0x6bb75edb…` | `0x1de460f363af910f51726def188f9004276bf4bc` | **536188664994919080 wei = 0.536188664994919080 BNB** | 与 Portal 实际报价币付款方 `0x1de460…` 是**同一地址**；说明原签名交易向它发送了这笔 native value，不能直接证明该笔 BNB 全额兑换、全额耗用或净支出 |

这些字段来源于**之前已冻结的** `bsc-meme-address-model-v1-p4b-flap-major2-original-buys-and-quotes-2026-10-14.json`，本轮不是重新补造链上交易。MARSCOIN 的 native `tx.value` 是**发送额**，合约内部换汇、余额回退、refund、实际 Gas 和完整 EOA 钱包损益依然 `UNRESOLVED`；不可擅自将 0.536188664994919080 BNB 加到 2.674483304192706318 S5B 标签原报价币上，更不可混合两种币种计盈亏。

**重要未闭合：** 原始 `TokenBought.fee` 牛来 `0.002059919900656033`、MARSCOIN `0.026744833041927063` 原 quote 单位，**不等于**这笔已核实 Portal 收款里可直接额外加上的用户实际支出。外层签名钱包 → 中间合约的资金从何处来、是何币种、内部服务费、代币税/Gas、最终用户净支出及真实卖出均没有同一完整交易闭环证据。0 条 EOA 直接报价币转出不能当作零成本证明。

## 2. 来源级别、代码回归及审查责任

- [N+1 双向数学报价 replay](./bsc_meme_address_model_v1_p4b_flap_nplus1_two_sided_quotes.py) 同时检查原始 [V1](./bsc-meme-address-model-v1-p4b-flap-major2-nplus1-roundtrip-math-readback-2026-10-17.json) 与追加 [V2](./bsc-meme-address-model-v1-p4b-flap-major2-nplus1-roundtrip-math-supplement-v2-2026-10-18.json) 的来源 Git blob 和原始叶子字段完全不漂移；同时校验签名原币 CA、quote CA、N/N+1、原买入签名与 2026 原始事件、函数 selector、exact ABI calldata、原始 uint256 buy/reverse 返回及复算差额；[24 项对抗性测试](./test_bsc_meme_address_model_v1_p4b_flap_nplus1_two_sided_quotes.py) 防止来源错配、把静态结果当真实成交及擅自放开 U/P5。
- [原签名买入 Portal quote receipt replay](./bsc_meme_address_model_v1_p4b_flap_original_quote_portal.py) 将两个 precommit、原始 [Portal quote V1 回读](./bsc-meme-address-model-v1-p4b-flap-major2-actual-portal-quote-transfers-2026-10-17.json)、追加 [Portal 付款 V2](./bsc-meme-address-model-v1-p4b-flap-major2-original-buy-payment-supplement-v2-2026-10-18.json) 和旧原真实买入来源全部按 Git blob 锁定，并检查 V2 没有修改 V1 任一原有的事件叶子字段，按**完全相同原交易 hash**选出单独的中间方→Portal 真实转账，逐原始整数比较 `TokenBought.cost`，不将非对应交易或独立 fee 算进原 EOA 成本。对应 [18 项负向测试](./test_bsc_meme_address_model_v1_p4b_flap_original_quote_portal.py)。
- **原地改写纠正记录（旧 blob → 恢复及追加）：** 历史数学报价 V1 原始 blob 为 `b7c618582b969c61772deb8a07dbd0e706a187e4`，此前曾原地 relabel 到 `57fd53d2e6e00adbb1576b2436a975887ee87a8d`。本次按 Git 旧 SHA 逐字恢复 V1，后者并非新的 RPC 获取；新增 V2 blob `cc96297ace51a74efb8b800f0fd0bed385fcbce4`。Portal 原始 V1 blob `db2e47010025fde7adf150c408748806e594a4c2`，此前曾原地追加 native/grade 信息成为 `25123c96619dc6b61b4a96a6f6dbd8372128c1a9`；本次逐字恢复 V1，追加 V2 blob `c2085b4f35187d7ca90123aaea93e15ee068044b`。所有原先记录的真实 RPC 选定字段（报价 `raw_return`、calldata，Portal ERC20 txHash、地址、amount、logIndex）保持原样。V2 新增 original signed EOA native 值来自更旧原始签名交易 JSON，**没有重新发起 RPC**。
- **来源级别：** 原始历史报价与日志保留选定 RPC 返回字段和对应 Git 原始 blob，不包含 Alchemy 服务商完整带区块哈希的逐字节原文；Portal 字段等级仍为 `TOOL_PARSED_FILTERED_FIELDS_NOT_FULL_RPC_RAW_LOG_PINNED`。V2 `request` 字典单独属于 `SCRIPT_RECONSTRUCTED_NOT_PROVIDER_CAPTURED`，仅做自洽校验；不能把数学反向报价提升为真实卖出，也不能把 source-grade 提升为 provider-grade。
- 本阶段没有经由私钥或钱包发起任何交易，没有下载付费 GMGN，未清理用户 Mac 服务，未通知或部署。当前代码和来源虽可通过 CI，仍需**其他 AI 对实际最新 SHA 独立审核**，不能继承上一轮 `APPROVE@dd3d529` 的批准。

## 3. 后续真正解锁 P4-B 所需证据

牛来、MARSCOIN 历史真实原始买入经 Portal 的接收端 quote 成本已得到较直接核验；龙虾有另一条独立 Four.meme 实际第二买家 D503 两次真实签名买卖闭环的源研究，但尚无统一的观察者信号收到时间证明。实际外部可跟单 U 仍需：公开节点 N 区块消息何时到达观察者；到达之后的**同资金量买入→状态变化后可卖出**，各资产的完整来源成本/授权/路由、历史税费 Gas、滑点与可支付资本；原 23 钱包逐案正负及未成交对照；直到这些成立才能开始 P5 untouched 2026 的 1/5/15 分钟回测。

状态严格保持：`P4-B=PARTIAL / PUBLIC_EXECUTABLE_U=UNRESOLVED / P4-C=PARTIAL / P5=BLOCKED / PRODUCTION=NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。
