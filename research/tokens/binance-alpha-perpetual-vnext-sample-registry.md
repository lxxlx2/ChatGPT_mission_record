# Binance Alpha + 永续 VNext 样本注册表

Updated: 2026-09-30
Status: ACTIVE_RESEARCH

用途：为 early-spot-discovery VNext 固定训练样本、控制样本和 outcome 标签，避免在观察 TRIA 后临时挑样本或修改规则。

重要约束：

- TRIA 不进入规则生成。
- historical high / forward multiple 只作为 outcome label，不允许 live model 偷看未来。
- 项目方 / 做市商 / 操盘者身份归因保持 UNRESOLVED；本表只研究 Binance venue topology 与公开市场结构。
- 当前 Monster V2.1 / Frank / Codex runtime 不读取本表。
- 单根极端 wick low 不能直接作为 cycle base；后续统一使用只依赖过去数据的稳定 Base Reference。

## 1. Extreme positive

### MYX

- Binance Alpha 已存在；2025-06-18 Binance Futures 上线 MYXUSDT 50x。
- 第一大周期约 0.11 区域扩张到 >2.17。
- 第二大周期约 1.31 扩张到 18.58。
- 主升期间 futures taker-buy quote share 多数仍接近 50%。
- 2025-08 主升中 funding 从小幅正快速转负，多次接近 / 触及 -2% cap。
- 第一轮 monster expansion 距 Futures 上线约 6 周，有明显 seasoning period。
- outcome: EXTREME / SHORT_FUEL。

### LAB

- Binance Alpha 已存在；2025-10-17 Binance Futures 上线 LABUSDT 50x。
- 2026 春季约 0.2 区域扩张至约 24.40。
- 中间包含大量 30%-70% 级别回撤 / 反抽。
- 主升期 taker-buy quote share 多数约 49.7%-51.7%。
- 2026-05 funding 大部分为正，部分结算约 +0.1% 至 +0.37%。
- 极端主升距 Futures 上线数月。
- outcome: EXTREME / POSITIVE_FUNDING_PATH。

### RIVER

- Binance Alpha 已存在；2025-10-17 Binance Futures 上线 RIVERUSDT 50x。
- 2026-01 极端主升，历史高点约 86，后续长期回落至约 1.17。
- 主升期间 funding 长时间极负，多次接近 / 触及 -2% cap。
- 极端主升距 Futures 上线约 2-3 个月。
- outcome: EXTREME / SHORT_FUEL。

### XPIN

- Binance Alpha 已存在；2025-09-12 Binance Futures 上线 XPINUSDT 50x。
- 截至 2026-09-30 Binance spot API 不存在 `XPINUSDT` 主板 symbol。
- Futures 初期约 0.001915；随后经过较长回落 / 横盘。
- 2025-10 主升最高约 0.010318。
- 2025-10-13 左右从约 0.00091 向 0.00114 出现第一组明显 4h probe；2025-10-16 左右再次 probe，随后快速进入 0.002+ 主升段。
- 第一组有效 probe 距 Futures 上线约 1 个月。
- 若使用稳定 base 区域约 0.00085-0.0011，后续 peak 大约仍为 9x-12x 量级；精确倍数待 Base Reference 规则冻结后重算。
- outcome: EXTREME_CANDIDATE，funding / OI regime 仍待完整回放。

## 2. Live positive candidate

### BTW

- 2026-03-02 进入 Alpha；2026-06-04 Binance Futures 上线 BTWUSDT。
- 2026-09 约 0.4 区域扩张到 1.4472，约 3.5x，并包含多次 25%-45% 快速回撤。
- funding 在本轮上涨期间长期为正。
- 历史 Mission 数据记录过普通账户偏空、top-trader positions 偏多的分歧。
- 明显 mark-up 距 Futures 上线约 3 个月。
- 当前周期尚未结束。
- outcome: LIVE / POSITIVE_FUNDING_PATH。

## 3. Medium / near-miss

### VELVET

- 2025-07-15 Binance Futures 上线 VELVETUSDT 50x，官方公告明确当时已在 Alpha。
- 截至 2026-09-30 Binance spot API 不存在 `VELVETUSDT` 主板 symbol。
- Futures 初始周约 0.0626，后续最高约 0.32494。
- launch-open -> high 约 5.2x；若使用早期稳定低价区，约为 5x-7x 级别，精确值待 Base Reference 冻结。
- 最大重估发生在 Futures 上线数周后，并非首日 launch spike。
- outcome: MEDIUM_POSITIVE / BORDERLINE_MONSTER。

### KGEN

- 2025-10-07 Alpha 与 KGENUSDT Futures 同日开放，最高 50x。
- 截至 2026-09-30 Binance spot API 不存在 `KGENUSDT` 主板 symbol。
- Futures 首日约 0.35，上市后快速跌入约 0.15-0.25 区域。
- 上线后约 10 天内出现极高波动，单次最高到约 0.6999。
- 相对 launch open 只有约 2x；若错误地用 0.11 单根 wick low 作 base，会得到约 6.4x，这正说明 Base Reference 不能使用事后最低针。
- 4h 数据中上市前 10 天已经出现多组 20%-50% probe / crash，属于典型 launch-noise 混淆样本。
- 没有发展成 MYX/LAB/RIVER 式 10x+ 多阶段 monster cycle。
- outcome: NEAR_MISS / LAUNCH_NOISE_CONTROL，不再作为纯 NEGATIVE_CONTROL。

## 4. Weak / negative controls

### ZEST

- Alpha + Futures + no main spot。
- Futures 初始约 0.235，早期高点约 0.35，后续长期主要在约 0.12-0.30 区域。
- 没有形成多阶段极端重估。
- outcome: NEGATIVE_CONTROL。

### TAG

- 2025-07-25 Futures 上线 TAGUSDT，官方公告明确当时已在 Alpha。
- 截至 2026-09-30 Binance spot API 不存在 `TAGUSDT` 主板 symbol。
- 初始周约 0.000663，早期高点约 0.001283。
- 后期存在深跌后反抽，因此单纯 low-to-high multiple 会被低 wick 人为放大。
- 没有形成持续多阶段 monster cycle。
- outcome: WEAK / NEGATIVE_CONTROL。

### ZORA

- 2025-07-25 Futures 上线 ZORAUSDT，官方公告明确当时已在 Alpha。
- 截至 2026-09-30 Binance spot API 不存在 `ZORAUSDT` 主板 symbol。
- Futures 初始周约 0.0853，阶段高点约 0.1486。
- 后续从约 0.05 区域反弹到约 0.124，但没有形成持续多阶段 extreme cycle。
- outcome: WEAK / NEGATIVE_CONTROL。

## 5. Venue-transition control

### Chainbase C

- 2025-07-15 Binance Futures 上线 CUSDT 50x，官方公告明确当时 C 已在 Alpha。
- Binance 2025-07-18 已把 C 接入 Spot / Convert / Margin 生态，Alpha+Futures+no-Spot 窗口仅约 3 天。
- Futures 初始约 0.294，早期最高约 0.475，之后整体衰减。
- 截至 2026-09-30 Binance spot API 存在 `CUSDT`。
- outcome: VENUE_TRANSITION_CONTROL。

C 说明 `days_without_main_spot` 可能是独立预测变量。主板 Spot 很快上线以后，underlying price discovery / executable depth 结构已经改变。

## 6. 连续 outcome tier

后续不再用简单成功 / 失败二分类。

候选 tier：

- EXTREME: stable Base Reference -> forward peak >= 10x
- STRONG: 5x-10x
- WEAK: 2x-5x
- NULL: <2x
- LIVE: 周期尚未结束

具体边界属于研究候选。所有 multiple 必须基于 signal 前可计算的 stable Base Reference，不能用未来最低价。

## 7. 当前 cohort

- Extreme: MYX, LAB, RIVER, XPIN candidate
- Live: BTW
- Medium / near-miss: VELVET, KGEN
- Weak / negative: ZEST, TAG, ZORA
- Venue transition: C

总计 11 个注册样本，TRIA 保持完全 out-of-sample。

## 8. 新增关键维度：SEASONING

当前极端 / 活跃正样本的有效主升普遍晚于 Futures 首日：

- MYX: 约 6 周
- XPIN: 约 1 个月
- RIVER: 约 2-3 个月
- LAB: 数月
- BTW: 约 3 个月

KGEN 的大幅 probe 集中在上市后约 10 天内。

因此需要测试 minimum seasoning days：14 / 21 / 28 / 35d。

seasoning 不能单独证明后续会爆拉，但可能有效过滤 launch-day / launch-week volatility。

## 9. 第一组 early-probe 对照

### MYX

2025-07-26 左右，距离正式第一轮大扩张约一周：

- 约 0.115 附近出现 4h/8h 上冲到约 0.128。
- turnover 相比此前数日基线显著放大。
- 对应关键 4h taker-buy quote share 约 44%-47%，主动 futures 买盘并没有呈现单边占优。
- 随后快速回撤，但几天后重新回到相同价格区并进入主升。

说明固定 `15%-30% probe` 门槛可能太高。MYX 更早的有效异常只有约 10%-12% 级别。

### XPIN

2025-10-13 左右：

- 从约 0.00091 向 0.00114 上冲约 25%。
- turnover 明显放大。
- 后续大部分交易中枢仍高于此前约 0.0008-0.0009 base。

2025-10-16 左右再次从约 0.00114 向 0.00140 probe，随后迅速进入 0.002+ 主升。

### KGEN

上市后几天就出现多组 20%-50% 上冲 / 回撤，甚至随后冲到 0.6999，但整个结构仍停留在 launch-noise / near-miss，没有发展成 10x+ seasoned monster cycle。

因此 S2 probe 必须与 seasoning、retention、repeat、Base Reference 一起使用。

## 10. 当前模型方向

更稳定的候选结构为：

`seasoned venue topology` + `thin underlying / free float` + `price/turnover anomaly` + `futures taker-flow mismatch` + `post-probe retention` + `repeat at higher base`

然后根据 funding / positioning 分成 SHORT_FUEL 或 POSITIVE_FUNDING 两条路径。

## 11. 下一批工作

1. 对全部 11 个样本统一构造 4h / 8h probe event。
2. 测试 seasoning 14/21/28/35d。
3. 测试 probe amplitude 8%-30%。
4. 记录 turnover multiple、taker-buy share、funding percentile、OI delta（可得时）。
5. 测试 24h / 72h retention 与 second-probe higher-base。
6. 使用 continuous outcome + Capture Multiple 做 leave-one-out / walk-forward。
7. 规则冻结后才评估 TRIA。

## Sources

- Binance MYX Futures 2025-06-18: https://www.binance.com/en/support/announcement/detail/9801625522154e098d73b8245ad70646
- Binance XPIN Futures 2025-09-12: https://www.binance.com/en/support/announcement/detail/4426d75b5b7f47f89a11f622739d6186
- Binance LAB / RIVER Futures 2025-10-17: https://www.binance.com/en/support/announcement/detail/b7c479f8dfa64156a34e8bcefc241732
- Binance C / VELVET Futures 2025-07-15: https://www.binance.com/en/support/announcement/detail/4f59bfc195ed4484ac810a9b8869fa86
- Binance C Spot ecosystem 2025-07-18: https://www.binance.com/en/support/announcement/detail/8b78eb7a4119436c9a8272d9a299fc32
- Binance ZORA / TAG Futures 2025-07-25: https://www.binance.com/en/support/announcement/detail/b8d4d5be7c894e1f9bf2c5e091da85e9
- Binance KGEN Alpha + Futures 2025-10-07: https://www.binance.com/en/support/announcement/detail/70ff0dd3181940e39bf7601f94fc1935
- Binance ZEST / BTW Futures 2026-06-04: https://www.binance.com/en/support/announcement/detail/61e41ce0e4b74dc7a794cc6bf9c57d38
- Historical market observations: Binance USDⓈ-M public futures data queried 2026-09-30.
