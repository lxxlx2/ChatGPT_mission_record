# Binance Alpha + 永续 VNext 样本注册表

Updated: 2026-09-30
Status: ACTIVE_RESEARCH

用途：为 early-spot-discovery VNext 固定训练样本、控制样本和 outcome 标签，避免在观察 TRIA 后临时挑样本或修改规则。

重要约束：

- TRIA 不进入规则生成。
- 本表中的 high / multiple 是历史 outcome 标签，不允许 live model 偷看未来。
- 项目方 / 做市商 / 操盘者身份归因保持 UNRESOLVED；本表只研究 Binance venue topology 与公开市场结构。
- 当前 Monster V2.1 / Frank / Codex runtime 不读取本表。

## 1. 强正样本

### MYX

- venue: Alpha -> Binance USDⓈ-M perpetual；极端周期时无 Binance main-board spot。
- 第一大周期：约 0.11 区域 -> >2.17。
- 第二大周期：约 1.31 -> 18.58。
- 主升期间 futures taker-buy quote share 仍大多接近 50%。
- funding 在 2025-08 主升中由小幅正值快速转为极端负值，多次接近或触及 -2% 单次 funding cap。
- outcome: STRONG_POSITIVE / SHORT_FUEL。

### LAB

- venue: Alpha -> Binance USDⓈ-M perpetual；极端周期时无 Binance main-board spot。
- 2026 春季约 0.2 区域扩张至约 24.40。
- 中间包含大量 30%-70% 级别回撤 / 反抽。
- 主升期 taker-buy quote share 多数约 49.7%-51.7%。
- funding 在 2026-05 早期主升阶段大部分为正，部分结算约 +0.1% 至 +0.37%。
- outcome: STRONG_POSITIVE / POSITIVE_FUNDING_PATH。

### RIVER

- venue: Alpha + Binance perpetual，主升阶段缺少 Binance main-board spot 深度。
- 用户提供完整 Binance 日线显示历史高点约 86，后续长期回落至约 1.17。
- 2026-01 主升中 funding 长时间为负；从约 10-20 向 30、40、60、80 扩张期间，多次出现约 -1% 至 -2% 的单次 funding，部分时段触及 -2% cap。
- outcome: STRONG_POSITIVE / SHORT_FUEL。

### XPIN

- venue: Binance Alpha + XPINUSDT perpetual；截至 2026-09-30 Binance spot API 不存在 `XPINUSDT` 主板 symbol。
- Futures 初期约 0.001915。
- 2025-09 后续一度下探约 0.000724；2025-10 主升最高约 0.010318。
- launch-open -> later high 约 5.4x；post-launch cycle low -> high 约 14.3x。
- 随后价格长期大幅衰减。
- outcome: STRONG_POSITIVE，funding / OI regime 仍待完整回放。

## 2. 进行中正候选

### BTW

- venue: Alpha -> Binance perpetual；当前无 main-board spot。
- 2026-09 约 0.4 区域扩张到 1.4472，约 3.5x，并包含多次 25%-45% 快速回撤。
- funding 在本轮上涨期间长期为正。
- 历史 Mission 数据记录过普通账户偏空、top-trader positions 偏多的分歧。
- 当前仍接近周期高位，完整 outcome 未结束。
- outcome: LIVE_POSITIVE_CANDIDATE / POSITIVE_FUNDING_PATH。

## 3. 中间态

### VELVET

- 2025-07-15 Binance Futures 上线 VELVETUSDT 50x，官方公告明确其当时已在 Alpha。
- 截至 2026-09-30 Binance spot API 不存在 `VELVETUSDT` 主板 symbol。
- Futures 初始周约 0.0626，早期低点约 0.0432。
- 后续最高约 0.32494。
- launch-open -> high 约 5.2x；early-low -> high 约 7.5x。
- 具备明显重估，但未达到 MYX/LAB/RIVER 的极端数量级。
- outcome: MEDIUM_POSITIVE / BORDERLINE_MONSTER。

中间态必须保留。若只训练“极端成功 vs 完全失败”，模型会过度学习极端路径，无法估计连续概率。

## 4. 弱表现 / 控制样本

### ZEST

- Alpha + Futures + no main spot。
- Futures 初始约 0.235，早期高点约 0.35，后续长期主要在约 0.12-0.30 区域。
- 没有形成多阶段极端重估。
- outcome: NEGATIVE_CONTROL。

### KGEN

- 2025-10-07 Alpha 与 KGENUSDT Futures 同日开放，最高 50x。
- 截至 2026-09-30 Binance spot API 不存在 `KGENUSDT` 主板 symbol。
- Futures 初始约 0.35，历史最高约 0.6999，约 2x。
- 后续大部分时间低于初始价，2026-09 约 0.16-0.17。
- outcome: NEGATIVE_CONTROL。

### TAG

- 2025-07-25 Futures 上线 TAGUSDT，官方公告明确当时已在 Alpha。
- 截至 2026-09-30 Binance spot API 不存在 `TAGUSDT` 主板 symbol。
- 初始周约 0.000663，后续最高约 0.001283，约 1.9x。
- 随后整体衰减，未形成 monster cycle。
- outcome: NEGATIVE_CONTROL。

### ZORA

- 2025-07-25 Futures 上线 ZORAUSDT，官方公告明确当时已在 Alpha。
- 截至 2026-09-30 Binance spot API 不存在 `ZORAUSDT` 主板 symbol。
- Futures 初始周约 0.0853，历史阶段高点约 0.1486，launch-open -> high 约 1.7x。
- 后续从约 0.0504 反弹到约 0.1238，也只有约 2.5x。
- 未形成持续多阶段 monster cycle。
- outcome: NEGATIVE_CONTROL。

## 5. Venue-transition 控制

### Chainbase C

- 2025-07-15 Binance Futures 上线 CUSDT 50x，官方公告明确当时 C 已在 Alpha。
- Binance 2025-07-18 又把 C 加入主板 Spot 生态，只有约 3 天 Alpha+Futures+no-Spot 窗口。
- Futures 初始约 0.294，早期最高约 0.475，约 1.6x；之后整体衰减。
- 截至 2026-09-30 Binance spot API 存在 `CUSDT`。
- outcome: VENUE_TRANSITION_CONTROL。

C 很重要，因为它说明“no Spot 的持续时间”可能是一个独立变量。若主板 Spot 很快上线，现货价格发现和可执行深度结构会改变。

## 6. 当前 cohort

已注册：

- Strong positive: MYX, LAB, RIVER, XPIN
- Live positive candidate: BTW
- Medium / borderline: VELVET
- Negative controls: ZEST, KGEN, TAG, ZORA
- Venue-transition control: C

总计 11 个样本，其中 TRIA 保持完全 out-of-sample。

这个规模已经比只看 LAB/MYX/BTW 更能抵抗幸存者偏差，但仍不足以冻结最终机械阈值。

## 7. 从扩样得到的当前结论

### Venue topology 是高价值 prior，不是结论

Alpha + perpetual + no main Spot 在强正样本中频繁出现，但 KGEN / TAG / ZORA / ZEST 证明该结构可以长期存在而没有 monster cycle。

### funding 方向不是统一条件

- MYX / RIVER: extreme negative funding path。
- LAB / BTW: positive funding expansion path。

因此 live discovery 应检测 funding 相对自身历史基线的 regime shift 及其与 price / OI / taker 的关系。

### 更稳定的候选信号是 flow mismatch

当前跨样本最值得继续机械化的是：

`价格显著变化` + `futures turnover/OI 放大` + `taker-buy share 仍接近双向平衡` + `underlying spot/free-float 相对薄`

它说明巨大 futures turnover 并不能简单解释成同规模单向真实买盘。后续再根据 funding / positioning 将路径分成 SHORT_FUEL 与 POSITIVE_FUNDING 两类。

### PROBE 可能是最适合用户目标的早期标签

对 spot-only 用户，最有价值的信号不是已经确认的 S4 breakout，而是第一次或第二次：

- 异常上冲
- 大幅回撤
- OI / turnover 没有完全回到原状态
- 后续 floor 抬高

VNext 回测需要优先测这种 probe 出现在最终大周期前多久，以及它在负控制中的出现频率。

## 8. 下一批工作

1. 给 11 个样本统一构造 minute/hour-level `probe event`。
2. 对每个 probe 记录 price jump、retrace、OI delta、funding percentile、taker-buy share、turnover、后续 floor shift。
3. 从控制组统计同样 probe 的假阳性率。
4. 用 leave-one-out / walk-forward 方式选机械阈值。
5. 固定阈值后再评估 TRIA。

## Sources

- Binance C / VELVET Futures 2025-07-15: https://www.binance.com/en/support/announcement/detail/4f59bfc195ed4484ac810a9b8869fa86
- Binance C Spot ecosystem 2025-07-18: https://www.binance.com/en/support/announcement/detail/8b78eb7a4119436c9a8272d9a299fc32
- Binance ZORA / TAG Futures 2025-07-25: https://www.binance.com/en/support/announcement/detail/b8d4d5be7c894e1f9bf2c5e091da85e9
- Binance KGEN Alpha + Futures 2025-10-07: https://www.binance.com/en/support/announcement/detail/70ff0dd3181940e39bf7601f94fc1935
- Binance ZEST / BTW Futures 2026-06-04: https://www.binance.com/en/support/announcement/detail/61e41ce0e4b74dc7a794cc6bf9c57d38
- Historical market observations: Binance USDⓈ-M public futures market data, queried 2026-09-30.
