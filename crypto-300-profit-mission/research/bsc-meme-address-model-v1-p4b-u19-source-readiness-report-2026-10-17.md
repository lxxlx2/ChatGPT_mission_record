# BSC P4-B 19 CA：公开可执行机会 U 的统一证据准备门禁（2026-10-17）

范围：**原冻结 23 EOA × 19 exact CA = 437 单元**，不改变样本、经济口径、时间阈值，不追逐单钱包历史截断回执。沿用同一 Draft PR #40。上一版已独立审核的是 `fe08bf4ff862b6426cf8db35ef48ecb9b6464856`；本批代码、测试和报告需要新的固定 SHA 审核，不继承以前的 APPROVE。

## 完成本批后可以回答什么

`bsc_meme_address_model_v1_p4b_u19_readiness.py` 基于 **七份已存在且 Git blob 身份钉住的来源**，只读重建原来 19 CA 的跨场所 U 证据准备表；不执行 RPC、不执行交易、没有新胜率、没有后验加入钱包。所有行必须保持市场首次公开可执行 U、观察者信号时间、同一信号下的可买卖能力、税/费/Gas/资金及 1/5/15 分钟跟单收益均为 `UNRESOLVED`。这是一项 **source audit / readiness gate**，不能视为已经完成 19 CA 的可执行 U。

防止三种核心误判：

1. **后来的 V2 math quote ≠ 更早市场的实际入场报价。** 19 个 V2 `0.01 WBNB` Router 数学报价均发生在其同币研究范围内首次已证明竞争/V2 流动性活跃区块之后。Router 数学输出没有证明代币税、gas、真实可卖、同刻可跟。
2. **早期签名交易 ≠ 公开首次 U。** 既有 3 个早期原始交易证人只涉及 龙虾/DDAC （原 23 钱包内）与 牛来、MARSCOIN 的两个原 23 外买家。其余 16 CA 仍无本批精选早期签名买入核查，不能标为市场没有买卖。两个外部买家不能混入 23 钱包成功数。
3. **龙虾 N+1 eth_call ≠ 真实跟单闭环。** N+1 只读非 revert 的 buy 测试未持久化，卖出报价是未买入前同一历史状态。另一个后续区块的三笔真实独立交易者卖出是市场可售方向线索，不能回溯证明 N+1 外部跟单当时可完成同资金规模的先买后卖、税后净利或市场全球 U。

程序对固定源原文重新计算，不假称完整见证/独立链节点证据；新增 15 项反例覆盖样本删改、代币映射、外部买家归属、报价时间错配、利润和 U 擅自升级、只读买入误报真实成交、后续独立卖出误报跟单。运行：

```bash
python3 -B -m unittest discover -s crypto-300-profit-mission/research -p test_bsc_meme_address_model_v1_p4b_u19_readiness.py
python3 -B crypto-300-profit-mission/research/bsc_meme_address_model_v1_p4b_u19_readiness.py
python3 -B -m unittest discover -s crypto-300-profit-mission/research -p 'test_bsc*.py'
```

## 下一步，直接服务可用性

先用已有 19 CA 市场研究层统一确定各 token 的**首次公开可观察买入动作**及 **历史同状态买卖路径**，优先冻住跨 3–5 个 2026 重大币和多个钱包的正负控制，包括龙虾、牛来、MARSCOIN、我踏马来了，保留 16 个尚无早期精选买入证据的原币；观察者只能从事件上链可公开见之后作出决定，不能用先知买点。依同一预冻结资金量验证能否实际买卖、Gas、quote 原币、税费、深度、失败/不支持。免费源缺失则按范围记 UNRESOLVED 并换其他候选，不追单一 trace。

门禁：`P4-B=PARTIAL / PUBLIC_EXECUTABLE_U=UNRESOLVED / P4-C=PARTIAL / P5=BLOCKED / PRODUCTION=NO_GO`。不得合并、部署、Gmail、通知、交易或改变 Mac/Frank/Monster。
