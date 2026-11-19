# BSC P4-B 19 CA：公开可执行机会 U 的统一证据准备门禁（2026-10-17）

范围：**原冻结 23 EOA × 19 exact CA = 437 单元**，不改变样本、经济口径、时间阈值，不追逐单钱包历史截断回执。沿用同一 Draft PR #40。上一版已独立审核的是 `fe08bf4ff862b6426cf8db35ef48ecb9b6464856`；本批代码、测试和报告需要新的固定 SHA 审核，不继承以前的 APPROVE。

## 完成本批后可以回答什么

`bsc_meme_address_model_v1_p4b_u19_readiness.py` 基于 **七份已存在且 Git blob 身份钉住的来源**，只读重建原来 19 CA 的跨场所 U 证据准备表；不执行 RPC、不执行交易、没有新胜率、没有后验加入钱包。所有行必须保持市场首次公开可执行 U、观察者信号时间、同一信号下的可买卖能力、税/费/Gas/资金及 1/5/15 分钟跟单收益均为 `UNRESOLVED`。这是一项 **source audit / readiness gate**，不能视为已经完成 19 CA 的可执行 U。

防止三种核心误判：

1. **后来的 V2 math quote ≠ 更早市场的实际入场报价。** 19 个 V2 `0.01 WBNB` Router 数学报价均发生在对应 CA 的已知 **研究范围内最早活跃池** 出现之后。仅 7 个 CA 的最早范围内活跃池与 V2 报价池为同一 V2/WBNB 池；另 12 个属于**跨场所时间比较**，其中 10 个最早池为 V3/WBNB，2 个最早池为 V3/USDT，而历史数学报价一律来自较晚的 V2/WBNB 池。代码分别校验两个池地址、协议、报价资产、对应活跃区块与 CA，并显式输出同池/跨池类别。Router 数学输出不能代表更早 V3 或 Launchpad 成交价格，也没有证明代币税、Gas、真实可卖或同刻可跟。
2. **早期签名交易 ≠ 公开首次 U。** 既有 3 个早期原始交易证人只涉及 龙虾/DDAC （原 23 钱包内）与 牛来、MARSCOIN 的两个原 23 外买家。其余 16 CA 仍无本批精选早期签名买入核查，不能标为市场没有买卖。两个外部买家不能混入 23 钱包成功数。
3. **龙虾 N+1 eth_call ≠ 真实跟单闭环。** N+1 只读非 revert 的 buy 测试未持久化，卖出报价是未买入前同一历史状态。另一个后续区块有三笔不同 EOA 签名的实际卖出，其中 **2 个签名人属于原 23 钱包，1 个签名人为样本外地址**。这些卖出仅提供该区块的交易方向证据，地址控制人是否相互独立仍未验证，更不能回溯证明 N+1 的假设外部买家当时可以完成同规模先买后卖、税后净利或市场全球 U。

程序对固定源原文重新计算，不假称完整见证/独立链节点证据；本轮共 22 项专项测试覆盖样本删改、跨场所池与报价币身份、早期买家和后续卖家 cohort 归属、Git 原文件字节篡改、时间错配、利润和 U 擅自升级、只读买入误报真实成交、后续卖出误报真实跟单。运行：

```bash
python3 -B -m unittest discover -s crypto-300-profit-mission/research -p test_bsc_meme_address_model_v1_p4b_u19_readiness.py
python3 -B crypto-300-profit-mission/research/bsc_meme_address_model_v1_p4b_u19_readiness.py
python3 -B -m unittest discover -s crypto-300-profit-mission/research -p 'test_bsc*.py'
```

## 2026-10-17 独立审核 REQUEST_CHANGES 修复边界

独立审核针对固定 `19222389e07c988f2524be32cd48243083db606f` 报告两项 MEDIUM，均只影响来源级语义与门禁反例覆盖，**未发现真实 U、钱包 PnL 或 P5 被误升级**。本轮更正：

- **M-1 场所身份与时间：** 最早范围内活跃与后来的 V2/WBNB 数学报价同池的 7 个 CA 为 BOB、4、GIGGLE、币安人生、我踏马来了、龙虾、HAJIMI。较早 **V3/WBNB** 而后取得 V2/WBNB 数学报价的 10 个 CA 为 TST、CHEEMS、MUBARAK、TUT、BROCCOLI714、BROCCOLIF3B、SIREN、BANANAS31、BULLA、BUBB。较早 **V3/USDT** 而后取得 V2/WBNB 数学报价的 2 个 CA 为牛来、MARSCOIN。每个数学报价必须与该 CA 的真实 V2 reference 池地址、V2 协议、WBNB 资产、首次正流动性区块绑定；最早 scoped 池必须与该 CA 的首次活跃池地址、协议和资产一致。跨场所的时间先后只说明先后，不能做同一交易场所的价差或收益计算。
- **M-2 后续真实卖出所属钱包：** 龙虾 `0x21870257…` 原签名人 `0x5c48a7…` 属于 23 钱包，`0x6e539947…` 原签名人 `0x9d1240…` 也属于 23 钱包，`0x656ed12c…` 原签名人 `0xbb99a9…` 在该冻结样本外。三笔的原交易 hash、sale event owner/CA 和 ERC20 日志交易身份一同验证；**不声称地址控制权独立**。所有 N+1 跟单收益保持未知。
- **LOW 元数据警示：** 牛来的 `Q3B (current metadata only)` 和 MARSCOIN 的 `S5B (current metadata only)` 仅为后续查询时的元数据标签；没有完成历史报价币价值或购买者实际现金流确认。
- **LOW 测试与 CI 文字：** 新增了真正复制七个来源到临时目录、修改原报价文件一个字节并要求 `load()` 拒绝的测试。现有 CI 工作流未修改，新增测试由已有单测 glob 发现；历史 commit message 不追溯修改。

原来源仍维持七个旧 Git blob，原 23×19 分母、既有失败/未知证据、观察者 U、P5 和 `NO_GO` 不变。此次修复须在新的最终固定 SHA 上单独得到其他 AI 审核批准。

## 下一步，直接服务可用性

先用已有 19 CA 市场研究层统一确定各 token 的**首次公开可观察买入动作**及 **历史同状态买卖路径**，优先冻住跨 3–5 个 2026 重大币和多个钱包的正负控制，包括龙虾、牛来、MARSCOIN、我踏马来了，保留 16 个尚无早期精选买入证据的原币；观察者只能从事件上链可公开见之后作出决定，不能用先知买点。依同一预冻结资金量验证能否实际买卖、Gas、quote 原币、税费、深度、失败/不支持。免费源缺失则按范围记 UNRESOLVED 并换其他候选，不追单一 trace。

门禁：`P4-B=PARTIAL / PUBLIC_EXECUTABLE_U=UNRESOLVED / P4-C=PARTIAL / P5=BLOCKED / PRODUCTION=NO_GO`。不得合并、部署、Gmail、通知、交易或改变 Mac/Frank/Monster。
