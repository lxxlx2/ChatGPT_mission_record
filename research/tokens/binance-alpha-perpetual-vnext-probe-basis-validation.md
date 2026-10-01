# Binance Alpha + 永续 VNext Probe / Basis Stress 验证

Updated: 2026-09-30
Status: ACTIVE_RESEARCH

## 目标

验证 early-spot-discovery VNext 当前最关键的问题：

1. `seasoning + price probe + turnover anomaly + taker-flow mismatch` 能否独立区分 extreme monster 与普通高波动标的。
2. probe 之后还需要什么额外结构，才能降低 TAG / ZORA / ZEST / KGEN 一类 false alert。
3. Binance perpetual premium/index basis 是否可以作为更早的市场结构压力信号。

本文件只属于 research 层，不修改 Monster V2.1 / Frank / Codex runtime。

TRIA 继续保持 out-of-sample，不参与本轮规则生成。

## 1. Probe + flow mismatch 单独使用会产生明显假阳性

### MYX

2025-07 下旬、第一轮正式主升前已经出现约 10%-12% 级 4h/8h probe，turnover 明显放大。

关键 4h candle 的 futures taker-buy quote share 约为 44%-47%。价格上涨并未对应明显单边主动买入。

### XPIN

2025-10 中旬从约 0.0009 区域开始出现约 20%-25% 级 probe，随后重复上冲并快速进入主升。

### TAG

TAG 在 2025-08 上旬已经经过约两周 seasoning，也出现非常相似的结构：

- 0.0007-0.0008 区域快速向 0.0010+ 扩张。
- 4h turnover 从约几十万到数百万、随后到数千万 USDT。
- 2025-08-08 左右一根主要扩张 candle 的 taker-buy quote share 约 49.1%。
- 后续继续冲到约 0.00128。

TAG 最终没有发展成 MYX / LAB / RIVER 式多阶段 extreme cycle。

### ZORA

ZORA 在 2025-08 中旬同样出现：

- 约 0.08-0.10 区域向 0.14+ 快速扩张。
- turnover 明显放大。
- 主要扩张 candle 的 taker-buy quote share 约 50.3%。

随后价格回落，并未发展成 sustained extreme cycle。

### 当前结论

以下组合仍然不足以单独输出高优先级 early-spot signal：

`seasoning + price probe + turnover expansion + taker-buy share ~50%`

TAG 与 ZORA 证明这组特征仍然存在较高 false-positive 风险。

因此 S1 的 thin-underlying / market-structure 变量不能降级为可选项。

## 2. 新候选：BASIS_STRESS_CLUSTER

Binance USDⓈ-M premium-index 历史 4h 数据给出了新的跨样本差异。

定义候选 stress bar：

`stress = max(abs(premium_high), abs(premium_low))`

第一轮只研究，不冻结阈值。

当前最值得测试的候选阈值为：

`stress >= 2%`

真正有价值的变量可能是 stress 的聚集程度，而非单根极值。

### Extreme / strong-side 样本

#### MYX

第一轮主升前，4h premium 已出现相邻极端偏离：

- 约 -2.7%
- 紧邻窗口约 -7.5%
- 后续另有约 -13.3% 的极端负 premium tail

这发生在价格正式进入 0.2、0.3、1.0+ 之前。

#### XPIN

2025-10 点火前后出现连续 basis stress：

- 约 -2.4%
- 约 -4.0%
- 约 -2.6%
- 后续扩张阶段又出现约 -8.1% 与 +5.4% 级极端 premium excursion

#### LAB

LAB 属于 positive-funding path，但仍出现明显 basis stress cluster。

2026-05 主升早期多个连续 4h 窗口出现：

- +3% 到 +5% 级 premium high
- -3% 到 -7% 级 premium low

因此 extreme basis stress 并不要求 funding 为负。

#### RIVER

RIVER 的现象最强。

2026-01 主升过程中大量连续 4h premium 处于数个百分点到十几个百分点的负偏离，局部 low 甚至超过 -20%。

#### BTW

BTW 属于 positive-funding expansion path，但 2026-09 扩张过程中同样出现相邻 4h basis stress：

- 一根约 -4.3%
- 紧邻窗口约 +9.8% / -2.7%
- 后续还有多次约 2%-5% 级偏离

这说明 `basis stress cluster` 可能跨越 SHORT_FUEL 与 POSITIVE_FUNDING 两种路径。

## 3. 控制组中的 premium stress 更常见为孤立事件

### ZORA

本轮复核窗口内，最大绝对 4h premium excursion 约 1.6%，没有形成 `>=2%` 的连续 stress cluster。

### TAG

TAG 也会出现大 premium tail，包括约 -2.8%、+2.8%，以及后续一个约 +4.0% 的孤立异常。

但这些异常相互间隔，当前窗口内没有观察到类似 XPIN / LAB / RIVER 的连续 cluster。

### ZEST

经过 launch seasoning 后仍会偶发约 2%-2.5% premium excursion，但主要为孤立 bar，中间夹着大量正常窗口。

### KGEN

剔除上市前 10 天 launch noise 后，2025-11 的 post-seasoning 窗口也存在约 -2.4% 的单次异常，但大部分 4h premium 保持在更小区间，没有形成持续 cluster。

## 4. 边界样本：VELVET 与 C

### VELVET

VELVET 是 medium / near-monster 边界样本。

2025-08 初，价格从约 0.044-0.05 区域快速重估到 0.118 高点时，4h premium 出现连续 stress：

- 一根 premium high 约 +3.7%
- 后续相邻窗口 premium low 约 -2.2%
- 随后又出现约 +2.1% / -1.4%、约 -3.6%、约 -2.3% 的连续偏离

VELVET 因此满足 basis-stress-cluster 的方向性特征，与其 MEDIUM_POSITIVE / BORDERLINE_MONSTER 标签一致。

### Chainbase C

C 在 2025-07-18 已很快进入 Binance Spot 生态。

复核 2025-08 与 VELVET 相近时间窗口，C 的 4h premium 主要只有零点几百分比，局部极端仍远低于 2%，没有观察到 stress cluster。

这支持两个当前假设：

1. `basis stress cluster` 与更强的高波动重估存在关联。
2. `days_without_main_spot` / venue transition 可能显著改变 basis 压力结构。

该结论仍属于小样本 INFERRED，需要盲样本继续验证。

## 5. 当前最值得回测的机械定义

候选定义 A：

`stress_bar = max(abs(premium_high), abs(premium_low)) >= 2%`

候选定义 B：

`basis_stress_cluster = 最近 3 根 4h bar 中至少 2 根为 stress_bar`

也就是在约 12 小时窗口内至少两次明显 premium/index dislocation。

候选定义 C：

更宽松版本可测试：24 小时内至少 3 根 stress_bar。

这些阈值仍处于 CANDIDATE 状态，不能直接写入 runtime。

下一步必须逐个样本计算：

- first cluster timestamp
- signal price
- Base Reference
- Pre-Signal Multiple
- 7d / 30d / 90d MFE
- 7d / 30d MAE
- Capture Multiple
- false cluster count

然后做 leave-one-out / walk-forward。

## 6. 为什么 cluster 比单根 premium tail 更合理

Premium-index high/low 可能包含极短时 index / perp 失衡，单根极端值容易受瞬时流动性影响。

要求相邻窗口重复出现，可以降低单 tick / 单次清算 / 短暂数据失真的影响。

当前研究假设为：

`price/turnover probe + repeated basis stress + thin underlying`

可能比单纯价格涨幅或 funding 方向更接近真正的 pre-ignition state。

该假设尚未冻结。

## 7. Historical OI 数据边界

2026-09-30 使用 Binance public `openInterestHist` 类接口回拉 MYX 2025-07 历史 4h OI 时，接口对旧 `startTime` 返回 invalid parameter / HTTP 400。

当前 Binance 公共 live history 接口无法直接补齐这些 2025 老窗口的完整 OI 序列。

仓库代码搜索本轮也没有发现可直接复用的 `openInterest` 历史快照。

因此：

- 旧样本 OI 暂标 `DATA_UNAVAILABLE_FROM_CURRENT_PUBLIC_ENDPOINT`。
- 不允许为了回测完整而估算或伪造 OI。
- 如果后续找到已归档的一手历史快照，可再补入。
- 第一版 VNext 必须能够在 OI 缺失时退化到 price / turnover / taker / funding / premium / venue / on-chain liquidity 特征。

## 8. 对当前 VNext 的修改方向

当前 S2/S3 应继续保留 price probe，但不再把它视作主要区分器。

更合理的研究顺序变为：

`S0 venue topology`

`-> seasoning`

`-> S1 thin underlying / free-float / spot-depth / index fragility`

`-> S2 price-turnover probe`

`-> basis stress cluster`

`-> S3 repeat / retention / higher-base rebuild`

funding 用于识别 fuel regime，不作为统一正负过滤器。

## 9. 当前证据等级

CONFIRMED：

- MYX / XPIN / LAB / RIVER / BTW 的历史 Binance 4h premium 数据中均存在明显成簇 basis dislocation。
- VELVET 的 medium-positive 重估窗口也出现 basis stress cluster。
- TAG / ZEST / KGEN 会出现孤立 premium extreme，因此单根 premium tail 不能作为 signal。
- ZORA 本轮对照窗口的 premium stress 明显弱于 extreme cohort。
- C 在进入 Binance Spot 生态后的对照窗口没有出现 2% 级 basis stress cluster。
- Binance 当前 public OI history 无法直接补拉 MYX 2025-07 老窗口。

INFERRED：

- basis stress cluster 可能是比 funding sign / taker share / 单次 price probe 更稳定的 early-discovery feature。
- 该特征可能反映 underlying spot/index 深度不足以顺畅吸收 perpetual notional 的状态。
- venue transition / main-spot availability 可能削弱这种 basis stress。

UNRESOLVED：

- 2% 是否为最优 stress threshold。
- 12h `2-of-3` 是否优于 24h `3-of-6`。
- basis stress cluster 与 on-chain free float / executable spot depth 的因果关系。
- 更大盲样本上的 precision / recall。
- TRIA 是否满足该规则，冻结规则前禁止查看并调参。

## Sources

- Binance USDⓈ-M public futures Kline / premium-index historical data, queried 2026-09-30.
- Existing sample/venue announcements are indexed in `binance-alpha-perpetual-vnext-sample-registry.md`.
