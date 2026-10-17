# P4-B 2026：四市场／五钱包的历史观察时点资金与可售边界（2026-10-17）

这是 [Mission Draft PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40) 的**预冻结、有界 BNB 主网只读实测**，不是交易信号、PnL、P5 或生产验收。已接受的前一轮 U19 代码审核固定在 `375bd09f2bf893c18d23c03c2d158410fe6aa17d`，本轮新增证据和代码需要按**新 SHA**单独审核。

## 为什么选这批

先保存 [four-market five-wallet precommit](./bsc-meme-address-model-v1-p4b-2026-fourmarket-fivewallet-precommit-2026-10-17.json)，随后才调用 Alchemy 的 BNB 主网历史查询。沿用仓库早已研究过的五钱包／三 CA 源批次：DDAC、239E 对龙虾；2ADF、A83B 对牛来；877AF 对 MARSCOIN。增加 **我踏马来了** 作为第四个**市场层**来源对照：已归档 2026 首次所选 V2 流动性区块 73658906，但缺乏本批已证明的早期签名市场买家。该币**没有虚构一个钱包、签名买入或外部跟单入场块**。全量冻结 23 EOA × 19 exact CA = 437，5 个钱包研究案例不是 untouched holdout，已暴露先验不得进入 P5 宣传收益。

首三币的已知**原签名买入所在区块 N**依次为龙虾 83635776（DDAC 原 23 成员）、牛来 115628774（实际买家样本外）、MARSCOIN 112441394（实际买家样本外）。此批的 N+1 是**历史区块末余额查询标签**，不是第三方公网传播延迟的实测时间，也不能直接解释为当时第一个可发出的外部交易。

## 实际 EOA 只读 `eth_getBalance`，各币各自 N/N+1

| 冻结 EOA | 参照币种 | N → N+1 | 历史 N+1 BNB（展示值） |
|---|---|---|---:|
| DDAC | 龙虾 | 83635776 → 83635777 | 16.997499825194926074 |
| 239E | 龙虾 | 83635776 → 83635777 | 0.355111218425276641 |
| 2ADF | 牛来 | 115628774 → 115628775 | 1.255849416487393360 |
| A83B | 牛来 | 115628774 → 115628775 | 83.962182422190954888 |
| 877AF | MARSCOIN | 112441394 → 112441395 | 17.286540447692079170 |

五个 EOA 的这两个**区块末** BNB 余额全部相等。但不能据此断定本区块没有其他交易，更不能断言全部 BNB 可用于某条 Flap ERC20 计价曲线、价格和税、真实成交。尤其 DDAC 在第 N 块已执行原始买入，因此 N+1 是**买入之后**；绝不作先知可用资金的证据。

## 历史 quote ERC20 `balanceOf`（N+1，18 decimals 的历史来源）

| 钱包 | Token quote CA | 余额（原始整数 / 18 decimals） |
|---|---|---:|
| 2ADF | `0x205812cdbed920aff76c6580abd681a46d11efc7` | 0.018939518354366437 |
| A83B | 同上 | 0.088423634380176133 |
| 877AF | `0xbe9d156892e55e7154bcd3cb0fea677f9d3103e1` | 0.015655458327370258 |

Q3B、S5B 是**当前元数据标签**；18 decimals 已有同历史区块的源证据，但不能将本次 ERC20 的数量当作当时 BNB/USD 的换算价格、钱包完整交易成本或经 Router 中转时的真实购买能力。此处没有使用最低余额阈值进行事后优化，也没有划定合格跟单地址。

## Flap TokenSold：MARSCOIN 已知原买入 N=112441394，单块拆分

预冻结读取 `N+1、N+2、N+3` 的 Flap Portal 官方 TokenSold topic，仅限定一个区块一次调用（最多 3 次、不重试），保持完整和截断的区别：

| 原始块 | 返回状态 | 可确认的目标 CA 卖出 |
|---|---|---|
| 112441395 | 完整解析 JSON，8 条 Portal TokenSold，精确目标 CA 0 条 | **仅该块**未发现 |
| 112441396 | 8,098 字符处响应截断，非完整 JSON | UNKNOWN |
| 112441397 | 8,098 字符处响应截断，非完整 JSON | UNKNOWN |

主网事件过滤地址 `0xe2ce6ab80874fa9fa2aae65d277dd6b8e65c9de0`，topic0 `0x03a4693e592f5e75dc7c136acb39b146d2b4966c0e509c34f362dee02b3b861a`。查出的 112441395 完整块只可证明当前这一小段时间窗内未看到该 CA 的 Portal `TokenSold`；对 N+2/N+3 的部分回执**完全不能**推定无出售，先前 10 块完整无卖出尚未获得证实。此批 Git JSON 保存 395 的事件数、8 个非目标哈希的摘要和 396/397 截断标识，**未保存 395 八条日志的逐字节原始 Provider 全文**；后续独立审核应视为 `TOOL_READBACK_SUMMARY_NOT_RAW_LOG_PINNED`，不能升级为独立完整原始链证据级。

## 源复算、失败控制与后续用途

[bsc_meme_address_model_v1_p4b_2026_capital_readback.py](./bsc_meme_address_model_v1_p4b_2026_capital_readback.py) 用 Git Blob SHA 固定**预冻结 JSON、只读回读 JSON、19CA 市场来源与原 23×19 roster**；联动原先五钱包 case 选择与确切 CA、N/N+1、报价 CA，针对 MARSCOIN 两个截断结果**禁止归类为已证实无出售**。对应 [专项对抗测试](./test_bsc_meme_address_model_v1_p4b_2026_capital_readback.py) 覆盖钱包伪造、签名块改写、案例缺失、quote CA 偷换、余额修改、未见签名买入冒充 U、截断假阴性、P5 擅自升级及源字节篡改。

```bash
python3 -B -m unittest discover -s crypto-300-profit-mission/research -p test_bsc_meme_address_model_v1_p4b_2026_capital_readback.py
python3 -B crypto-300-profit-mission/research/bsc_meme_address_model_v1_p4b_2026_capital_readback.py
python3 -B -m unittest discover -s crypto-300-profit-mission/research -p 'test_bsc*.py'
```

**已满足：** 跨 3 个源已证明签名买入市场 + 1 个无本批早期签名的市场控制，5 钱包历史 native/quote 余额、MARSCOIN 1 个完整买后块和 2 个截断块的明确审计口径。

**尚缺：** 第三方收到 N 块日志的真实可观察信号时间；同一信号条件下实际可执行购买及在买入状态改变后的退出交易；真实原币/quote 资金中转、Gas/税费、池深度、原 EOA 完整经济 PnL；未暴露的独立 P5 1/5/15 分钟跟单数据。下一阶段应针对**这三种不同的市场机制**补同状态买卖路径反例证据，不再大规模重抓 23×19 历史转账或无限追一个截断回执。

**门禁继续：** `P4-B=PARTIAL / PUBLIC_EXECUTABLE_U=UNRESOLVED / P4-C=PARTIAL / P5=BLOCKED / PRODUCTION=NO_GO`，`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。
