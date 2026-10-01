# Binance Alpha + 永续早期现货发现 VNext 研究设计

Updated: 2026-09-30
Status: ACTIVE_RESEARCH

## 目标

本研究只优化一个问题：在极端高波动代币进入明显主升段之前，尽量早地发现候选，供人工决定是否建立现货仓位。

明确排除：

- 不设计永续开多 / 开空执行。
- 不优化自动止盈、顶部识别或反手交易。
- 不修改当前 Monster V2.1 / Frank / Codex runtime、阈值、checkpoint 或历史回测。
- 后期 SHORT-HARVEST、LONG-CROWD、SHAKEOUT、DISTRIBUTION 数据继续保留，用于给早期特征打标签和验证完整生命周期。

本文件建立在 `binance-alpha-perpetual-squeeze-cross-sample-study.md` 和 `binance-alpha-perpetual-vnext-sample-registry.md` 上，作为 discovery-only 候选模型设计，不替代当前运行规则。

## 1. 训练 / 验证隔离

TRIA 不参与规则生成。

样本必须先登记，再参与阈值选择。不能观察 TRIA 后临时挑选历史币或调整阈值。

当前 cohort 已覆盖：MYX、LAB、RIVER、XPIN、BTW、VELVET、KGEN、ZEST、TAG、ZORA、C。

后续采用 leave-one-out / walk-forward，避免某一只极端样本主导规则。

## 2. 用户目标决定评分方式

用户只计划早期识别后持有现货，退出由用户人工分批处理。

因此模型评价重点为 discovery timing：

- Signal Price：首次升级到人工检查级别的价格。
- Base Reference：信号发生前、仅使用过去数据构造的稳定价格基准。
- Peak Price：固定 forward horizon 内的最高价。
- Pre-Signal Multiple = SignalPrice / BaseReference，越低越好。
- Capture Multiple = PeakPrice / SignalPrice，越高越好。
- 7d / 30d / 90d Forward MFE。
- 7d / 30d Forward MAE。
- Recall：历史 extreme / strong 样本在主升前被 S2/S3 捕获的比例。
- False Alert Rate：弱样本被升级到 S2/S3 的频率。

目标偏好为 Recall > Precision，但不允许把全部 Alpha+Futures 标的无差别报警。

## 3. Base Reference 禁止使用事后最低针

扩样暴露出一个重要问题：如果用事后绝对最低价作为 cycle base，KGEN、TAG 等普通高波动标的也会被人为放大倍数。

因此 live/backtest 的 Base Reference 必须只使用 signal 之前的数据，并优先测试：

- trailing 7d median close
- trailing 14d median close
- trailing 14d 20th percentile close
- trailing rolling VWAP

禁止用 signal 之后才知道的最低 wick 作为分母。

最终 Base Reference 规则要通过 walk-forward 冻结。

## 4. Venue topology 只负责 universe

### S0 VENUE CANDIDATE

候选条件：

- Binance Alpha / 可验证 on-chain spot path 已确认。
- Binance USDⓈ-M perpetual 已存在。
- Binance main-board spot 缺失，或极端行情发生时尚未上线。

S0 本身不升级成 monster signal。

C 是 venue-transition control：2025-07-15 先有 Alpha + Futures，2025-07-18 即进入 Binance Spot 生态，no-Spot 窗口仅约 3 天，后续没有形成同级极端周期。

因此 `days_without_main_spot` 应作为独立变量记录。

## 5. 新增 SEASONING / LAUNCH-NOISE 层

KGEN 暴露出一个关键混淆变量。

KGEN 2025-10-07 Alpha + Futures 同日开放，上市初期极高波动，约 10 天内曾从约 0.11 低点冲到约 0.70，但没有发展成 MYX/LAB/RIVER 式多阶段 10x+ monster cycle。

强正样本的主要行情则普遍发生在 Futures 上线一段时间之后：

- MYX: 2025-06-18 Futures 上线，第一轮主要扩张在 2025-08 初，约 6 周后。
- XPIN: 2025-09-12 Futures 上线，第一组有效早期 probe 出现在 2025-10 中旬，约 1 个月后。
- LAB: 2025-10-17 Futures 上线，极端主升发生在 2026 春季，经历数月沉淀。
- RIVER: 2025-10-17 Futures 上线，极端主升集中在 2026-01，约 2-3 个月后。
- BTW: 2026-06-04 Futures 上线，明显 mark-up 集中在 2026-09，约 3 个月后。

因此必须区分 launch volatility 与 seasoned setup。

当前只建立候选阈值，不冻结：

- 14d
- 21d
- 28d
- 35d

回测比较这些 minimum seasoning days 对 extreme recall 与 false alert 的影响。

第一版研究优先测试 21d 作为候选，不写进当前 runtime。

## 6. funding 符号不能作为统一硬门槛

历史正样本至少有两条路径。

### SHORT-FUEL

典型：MYX、RIVER。

- price 上升
- funding 从自身基线快速下降，甚至长期极负
- OI / turnover 放大
- short exposure / basis distortion 提供潜在买回燃料

MYX 与 RIVER 主升期间都曾多次出现接近 -2% 的单次 funding。

### POSITIVE-FUNDING EXPANSION

典型：LAB、BTW。

- price 上升
- funding 长期为正
- futures turnover 巨大
- taker flow 仍接近双向平衡
- 中间出现大幅 shakeout，但价格中枢继续提高

因此 VNext 记录 funding percentile / regime shift，并结合 price、OI、taker、turnover 解释，禁止统一要求 funding < 0。

## 7. S1 INVENTORY / VACUUM WATCH

通过 S0，并经过 launch-noise 标记后，关注底层条件：

- free float 明显低于 headline circulation
- 去除 vesting / treasury / bridge / CEX / LP 后筹码集中
- ±1% / ±2% / ±5% executable spot depth 很薄
- futures OI / spot executable depth 比值异常
- Binance price-index constituents 少或 underlying 现货场所本身较薄
- project / treasury / vesting / MM token flow 没有形成显著持续卖压

## 8. S2 EARLY CANDIDATE: PROBE

这是用户最需要的第一类实时信号。

初始研究发现 15%-30% 的固定短时涨幅门槛过高，可能漏掉 MYX 第一轮更早的异常。

MYX 在 2025-07-26 附近，距离正式大幅扩张约一周，已经出现：

- 约 0.115 附近的 4h/8h 异常上冲，局部高点约 0.128
- turnover 相比此前基线明显放大
- 一组关键 4h candle 的 taker-buy quote share 仅约 44%-47%
- 随后快速回撤，但数日后重新回到相同价格区并进入主升

XPIN 在 2025-10-13 左右、距离大爆发约 3 天，也出现：

- 从约 0.00091 向 0.00114 的 4h 上冲，约 25%
- turnover 明显放大
- 后续价格大部分保持在之前 base 之上
- 2025-10-16 再次 probe 后迅速进入 0.002+ 主升段

所以 probe 振幅候选区间应从约 8%-30% 开始回测，不能预先固定 15%。

每个 probe 记录：

- 4h high/open
- 8h high / pre-window close
- close/open
- retrace from high
- turnover / trailing median turnover
- taker-buy quote share
- funding percentile vs trailing history
- OI delta，若历史 OI 可获得
- 24h / 72h retention
- days since futures launch
- days since Alpha listing
- days without main Spot

S2 的目标是早，不要求 breakout 已确认。

## 9. S3 PRE-IGNITION: RETENTION + REPEAT

单次 probe 很容易被 KGEN / TAG / ZORA 一类普通高波动标的触发，所以第二层必须检查 probe 之后是否留下结构性痕迹。

重点候选：

- 24h / 72h median close 是否高于 pre-probe Base Reference
- probe 后最低 close 是否守住 Base Reference 附近
- turnover 是否完全回落到旧基线
- OI / funding reset 后是否再次构建
- 第二个 probe 是否出现在更高价格中枢
- retail / top-trader positioning 是否出现持续分歧
- spot / index lead -> perp follow 是否重复发生

S3 是 discovery engine 的最高优先级输出。

## 10. S4 IGNITION

正式 breakout、volume / liquidation expansion、价格进入明显主升。

S4 主要用于给 S2/S3 做 outcome 验证。如果模型长期到 S4 才首次发现，即使方向正确，也应降低 discovery score。

## 11. Outcome 使用连续分层

禁止简单二分类 monster / non-monster。

建议先按不偷看未来的 Base Reference 计算 forward multiple，再划分：

- EXTREME: >=10x
- STRONG: 5x-10x
- WEAK: 2x-5x
- NULL: <2x
- LIVE: 当前周期尚未结束

具体边界仍属于研究候选，需要结合用户 10x 目标和样本数量验证。

KGEN 应从纯 negative control 降级为 near-miss / medium-volatility control，因为其上市初期存在约 6x 的 wick-low-to-high 路径；但该倍数高度依赖瞬时最低针，使用稳定 Base Reference 后会明显降低。

## 12. 后期生命周期只作为 outcome 标签

继续记录：

- SHORT-HARVEST
- LONG-CROWD
- SHAKEOUT
- SECOND-CYCLE
- DISTRIBUTION
- COLLAPSE

这些状态用于判断早期 signal 最终是否演化成完整 monster lifecycle，不自动触发用户卖出。

## 13. TRIA 的 out-of-sample 约束

只有在 seasoning、Base Reference、probe、retention、repeat 规则冻结后才评估 TRIA。

检查：

- 当前 S0/S1/S2/S3 层级
- SHORT-FUEL 或 POSITIVE-FUNDING path
- current long crowd 是否先需要 reset
- unlock 对 free float / venue supply 的影响
- 下一次 probe 是否满足冻结规则
- probe 后是否产生 retention + repeat

如果 TRIA 不符合规则，不允许立即回头改阈值。任何规则修改必须先回到训练 cohort 和控制 cohort 重新验证。

## 14. 与 Codex / Monster 当前工作的隔离

本文件只属于 `research/tokens/`。

当前 Monster V2.1、Frank、Codex 历史验证继续使用原规则。

VNext 只有在研究规则冻结、训练 / 控制 cohort 扩充、机械回测指标确定后，才单独交给 Codex 实现并与 V2.1 做 A/B backtest。

禁止在当前 V2.1 中途修改 runtime 阈值适配本研究。

## 当前下一步

1. 对样本注册表逐个构造 4h / 8h probe event。
2. 测试 seasoning 14/21/28/35d。
3. 测试 probe price threshold 8%-30%，配合 turnover multiplier 和 taker-flow mismatch。
4. 测试 24h / 72h retention 与 second-probe higher-base 条件。
5. 使用 continuous outcome tier 和 Capture Multiple 评分。
6. 做 leave-one-out / walk-forward。
7. 最后冻结规则并只对 TRIA 做 out-of-sample evaluation。

## Sources

- Binance MYX Futures 2025-06-18: https://www.binance.com/en/support/announcement/detail/9801625522154e098d73b8245ad70646
- Binance XPIN Futures 2025-09-12: https://www.binance.com/en/support/announcement/detail/4426d75b5b7f47f89a11f622739d6186
- Binance LAB / RIVER Futures 2025-10-17: https://www.binance.com/en/support/announcement/detail/b7c479f8dfa64156a34e8bcefc241732
- Binance KGEN Alpha + Futures 2025-10-07: https://www.binance.com/en/support/announcement/detail/70ff0dd3181940e39bf7601f94fc1935
- Binance C / VELVET Futures 2025-07-15: https://www.binance.com/en/support/announcement/detail/4f59bfc195ed4484ac810a9b8869fa86
- Binance ZORA / TAG Futures 2025-07-25: https://www.binance.com/en/support/announcement/detail/b8d4d5be7c894e1f9bf2c5e091da85e9
- Binance ZEST / BTW Futures 2026-06-04: https://www.binance.com/en/support/announcement/detail/61e41ce0e4b74dc7a794cc6bf9c57d38
- Historical price / turnover / taker / funding observations: Binance USDⓈ-M public market data queried 2026-09-30.
