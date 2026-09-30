# Binance Alpha + 永续、无主板现货的跨样本挤压结构研究

Updated: 2026-09-30
Status: ACTIVE_RESEARCH

## 研究目的

避免用目标币自身历史同时定义模式和验证模式。本文件先使用独立历史样本冻结一套可证伪的市场结构假设，再把目标币作为 out-of-sample candidate 检查。

正样本：MYX、LAB、BTW。
初始负控制：ZEST。
目标币 TRIA 不参与规则生成。

所有关于“项目方 / 做市商 / 操盘者”的身份归因均保持 UNRESOLVED，除非链上、账户级或明确披露证据能够证明。公开 Binance 聚合数据只能证明市场结构，不能证明同一实体在不同账户同时开多空仓。

## 1. 场所结构为什么值得单独研究

CONFIRMED：Binance Alpha 为链上早期代币入口；Binance Futures 可给同一标的提供 USDⓈ-M 永续；主板 spot listing 是独立审核阶段。

CONFIRMED：Binance 官方说明不收取 platform listing fee，但与项目的 structured agreements 可以包含用于 airdrop / marketing campaign 的 token budget。Alpha / Wallet 项目在双方签署正式协议后可发生约定 token transfer。因此“项目进入 Binance 生态可能伴随营销 token allocation”有官方依据；“所有 Alpha+Futures 项目都必须支付固定代币份额并因此必须拉盘”没有官方依据。

经济结构上，Alpha / 外部链上 spot 的可兑现 quote liquidity 可能远小于 futures notional。直接在浅池卖出大量库存会快速恶化平均成交价；USDⓈ-M perpetual 则允许第三方以 USDT 保证金形成远大于 spot pool 的杠杆名义头寸。这个结构为反身性 squeeze 提供条件，但场所组合本身不证明操纵。

## 2. 对“多空双开”的修正

完全等额、同价格、同期限的 long + short 本身近似 delta-neutral，扣除手续费与 funding 后期望收益更差；价格上涨后主动平 short 会确认 short loss，long gain 只负责抵消，单靠这一动作不会创造利润。

更合理、也可被公开数据部分检验的假设是动态净敞口模型：

1. 低 free-float / 浅 spot 环境中先形成库存优势；perp short 可用于库存 hedge。
2. spot / index 先出现价格抬升，外部交易者开始增加 short；若价格上涨同时 OI 上升、funding 下降、taker buy 仍接近 50%，说明新增 futures 仓位并没有简单解释涨价。
3. 若随后 short liquidation / stop-buy 出现，perp 成为上涨放大器。
4. 当大众仓位转为明显 long crowded 后，同一高杠杆结构会反向提供 long-liquidation 燃料；总体上升趋势可以包含大幅下杀。
5. 真正利润来源必须有第三方承担相反方向的 PnL / liquidation / funding，单纯自成交或完全对冲不能创造系统外利润。

该模型兼容正常做市、套利、反身性投机，也兼容协调操盘假设；仅凭聚合行情不能区分最终身份。

## 3. 独立正样本

### MYX

CONFIRMED：MYX 先进入 Binance Alpha，2025-06-18 Binance Futures 上线 MYXUSDT，最高 50x。

Binance Futures 历史：

- 2025-08-03 至 08-06，价格从约 0.1136 快速扩张，最高超过 2.17；期间单日 futures quote turnover 达数十亿 USDT。
- 2025-09-07 至 09-10，价格从约 1.31 扩张至最高约 18.58。
- 第二阶段四个交易日的 taker-buy quote share 约为 50.92%、51.13%、50.52%、51.35%。
- 第一阶段四个关键日约为 51.34%、50.91%、50.06%、49.92%。

INFERRED：多倍价格扩张没有对应持续 60%-70% 的单边 futures aggressor buy。巨大 turnover 主要表现为高度双向换手 / 杠杆循环，价格变化不能解释为同等规模的新多头现金单向流入。

CoinDesk 2025-09-09 报道当时 24h liquidation 超过 $40M，超过 80% supply 仍锁定，仅约 197M circulating；报道援引分析将 $4->$8 的一段称为 targeted short squeeze，并强调薄流通使价格更易出现极端波动。该报道支持 squeeze / thin-float 机制，不证明具体操盘实体身份。

### LAB

CONFIRMED：LAB 已在 Binance Alpha，2025-10-17 Binance Futures 上线 LABUSDT，最高 50x。

Binance Futures 历史显示 2026 春季至 06 月出现极端持续重估：从约 0.2 附近逐步扩张到 2026-06-02 日内最高约 24.40，同时包含大量 30%-70% 级别的日内回撤 / 反抽。

关键上升日 taker-buy quote share 仍主要在约 49.7%-51.7%：

- 2026-05-01: ~51.03%
- 2026-05-02: ~50.66%
- 2026-05-03: ~49.66%
- 2026-05-06: ~51.19%
- 2026-05-29 to 06-02: 约 50.47%-51.69%

INFERRED：LAB 的数十倍走势同样没有出现与价格倍数相称的长期单边 futures taker-buy domination，反而呈现高 turnover、近 50/50 aggressor flow、巨大上下影和反复重定价。

### BTW

CONFIRMED：BTW 于 2026-03-02 进入 Binance Alpha；2026-06-04 Binance Futures 上线 BTWUSDT，最高 10x。

2026-09 Binance Futures 出现典型锯齿式上行：

- 09-02: ~0.42 -> high ~0.756 -> close ~0.49
- 09-13: ~0.55 -> high ~0.768 -> close ~0.734
- 09-14: high ~0.80 -> low ~0.543 -> close ~0.584
- 09-20: ~0.59 -> high ~0.915
- 09-25: ~0.95 -> high ~1.338 -> close ~1.315
- 09-26: high ~1.378 -> low ~0.753 -> close ~1.002
- 09-28: ~1.22 -> high ~1.447 -> low ~0.880 -> close ~1.118

此前 Mission 回溯还记录到：普通账户 long/short ratio ~0.61（约 62% short accounts），而 top-trader position long/short ratio ~2.02；这是一种“普通账户偏空、优势账户持仓偏多”的可观测分歧。

INFERRED：BTW 支持“总体趋势向上时仍反复制造足够大的双向清算区间”这一特征，但同样不能由此证明项目方本人控制两侧仓位。

## 4. 负控制：ZEST

CONFIRMED：Binance Alpha 2026-05-19 首发 ZEST；Binance Futures 2026-06-04 上线 ZESTUSDT；截至 2026-09-30 Binance 官方购买页仍明确写明 ZEST 不是 Binance CEX spot-listed token。

Binance Futures 从上线后约 0.235 起，早期最高约 0.35，随后大部分时间在约 0.12-0.30 区域波动；截至 2026-09-30 约 0.20，没有出现 MYX / LAB 那种多阶段数十倍重估。

因此：

- “Alpha + Futures + 无主板 spot”是结构性候选条件。
- 它不是充分条件。
- 把所有未爆发样本都解释为“项目方临时改变主意”会让假设不可证伪，不可用于模型。

后续应扩大负控制集合，统计同类 venue topology 的 base rate。

## 5. 冻结的跨样本机制假设 V0

### STRUCTURAL PREREQUISITE

- Binance Alpha / 可验证 on-chain spot path。
- Binance perpetual 已存在。
- Binance main spot 尚不存在。
- 实际 free float 明显小于 headline circulating，或 spot executable depth 相对 futures notional 很浅。

仅满足这组条件不升级。

### INVENTORY / VACUUM

关注：

- 去特殊地址后的自由流通集中度。
- ±1% / ±2% / ±5% spot executable depth，而非单看 market cap。
- 项目 / vesting / MM / treasury 到 CEX 或 LP 的 token flow。
- index constituents 是否少且流动性薄。

### LEVERAGE BUILD

更强的早期信号：

- price trend upward while OI rises materially；
- futures taker-buy share 仍在约 48%-52% 附近，而价格出现远超正常 beta 的扩张；
- funding neutral / negative 或在上涨中下降；
- futures turnover / spot executable liquidity 比例极高。

解释：futures 并没有以单边主动买盘解释涨幅，反向仓位可能在累积。

### SHORT-HARVEST / REFLEXIVE EXPANSION

确认项：

- price breakout + OI / liquidation expansion；
- short-account crowding 或 funding negative；
- top-trader / retail positioning divergence；
- spot / index lead 后 perp 跟随；
- OI 在上冲或强平阶段出现可解释的变化。

### LONG-CROWD / SHAKEOUT

当 retail long ratio、positive funding、OI 同时过热时，不继续把高 OI 当作 bullish。历史正样本显示总体上升趋势中可以出现 30%-70% 的快速回撤；这类回撤可清理 long leverage 后再进入下一轮，但是否由同一实体主动制造必须保持 UNRESOLVED。

## 6. 如何证明“多空双吃”比普通投机更可信

公开聚合数据能够验证的是模式，不能直接验证操盘身份。要提高归因置信度，需要额外证据：

1. 已标记 project / MM / treasury 链上钱包在拐点前后的 CEX deposit / withdrawal。
2. spot/index venue 先动，Binance perp 随后被动跟随，且该 lead-lag 重复出现。
3. 拉升时真实 spot quote inflow 很小，却触发远大于它的 futures turnover / liquidation。
4. top-trader 与普通账户方向长期反向，并在关键 turning point 切换。
5. funding、OI、liquidation 的变化顺序与“先吸引一侧杠杆，再反向清算”一致。
6. 多轮周期重复，而非单次新闻冲击。

若缺少这些证据，只能写为 MARKET-STRUCTURE-CONSISTENT，不写“项目方操盘已确认”。

## 7. 对 TRIA 的 out-of-sample 使用规则

TRIA 不参与上述阈值和阶段定义。后续只检查：

- 是否满足 STRUCTURAL PREREQUISITE；
- free-float / spot executable depth 与 futures OI 的比值；
- Binance index constituents 与 spot lead-lag；
- funding / OI / taker / retail-vs-top-trader positioning 是否按冻结顺序演化；
- community unlock / project-linked wallets 是否向交易场所形成供应；
- 是否出现与 MYX / LAB / BTW 一致、但在 ZEST 控制中缺失的阶段序列。

只有出现阶段序列才升级概率，不因“Alpha + Futures”标签本身升级。

## Primary / high-quality sources

- Binance listing requirements and Alpha/Futures/Spot relationship: https://www.binance.com/en/support/announcement/detail/d378c2176ac841bb8eae68f63d4c4845
- Binance listing fee / token budget clarification: https://www.binance.com/en/support/announcement/detail/b600c21f364a43fb9647f64797e8cb0f
- Binance MYXUSDT futures launch: https://www.binance.com/en-IN/support/announcement/detail/9801625522154e098d73b8245ad70646
- Binance LABUSDT futures launch: https://www.binance.com/en/support/announcement/detail/b7c479f8dfa64156a34e8bcefc241732
- Binance BTWUSDT futures launch: https://www.binance.com/en/support/announcement/detail/61e41ce0e4b74dc7a794cc6bf9c57d38
- Binance ZEST Alpha background: https://www.binance.com/en/academy/articles/what-is-zest-protocol-zest
- Binance ZEST Alpha trading campaign: https://www.binance.com/en/support/announcement/detail/e719094bd91844a39a5ea5866a1bd19d
- Binance ZEST current purchase page / no CEX spot statement: https://www.binance.com/en/how-to-buy/zest-protocol
- CoinDesk MYX short-squeeze report, 2025-09-09: https://www.coindesk.com/business/2025/09/09/more-than-usd40m-liquidated-as-market-makers-suffer-shattering-myx-short-squeeze
