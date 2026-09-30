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

本文件建立在 `binance-alpha-perpetual-squeeze-cross-sample-study.md` 上，作为下一版 discovery-only 候选模型设计，不替代当前运行规则。

## 1. 训练 / 验证隔离

目标币 TRIA 不参与规则生成。

当前正样本研究池：

- MYX
- LAB
- RIVER
- BTW
- XPIN，可作为补充极端行情样本继续复核

当前负控制 / near-miss：

- ZEST
- KGEN

KGEN 是一个很有价值的控制：2025-10-07 同时开放 Binance Alpha 和 KGENUSDT 永续，最高 50x；截至 2026-09-30 Binance 主板没有 `KGENUSDT` spot symbol。Binance Futures 首日约 0.35，历史高点约 0.70，之后大部分时间远低于该高点，没有形成 LAB / MYX 那种多阶段数十倍主升周期。

因此 venue topology 只能负责候选池筛选，不能单独输出 monster conclusion。

## 2. 新发现：funding 符号不能作为统一硬门槛

历史正样本至少存在两种明显不同的衍生品燃料形态。

### Type S: SHORT-FUEL

MYX 与 RIVER 是代表。

MYX 2025-08 第一轮主升前后，价格从约 0.10 区域进入 0.20、0.30 后，funding 从小幅正值快速转负；随后在价格向 0.4、0.8、1.0、2.0 扩张时，多次出现约 -0.5% 到 -2.0% 的单次 funding，部分时段触及 -2.0% cap。

RIVER 2026-01 的主升更明显。价格从约 10-15 区域向 20、30、40、60、80 扩张期间，funding 长时间为负，并多次接近或达到 -2.0%。价格上涨与极端负 funding 同时存在，符合大量 short exposure / basis distortion 为上涨提供潜在燃料的结构。

### Type L: LONG-FLOW / POSITIVE-FUNDING EXPANSION

LAB 与 BTW 是代表。

LAB 2026-05 从约 0.7 向 2、3、4 扩张期间，funding 大部分时间为正，部分结算达到约 +0.1% 到 +0.37%，随后在价格继续上行时回落到较低正值。

BTW 2026-09 从约 0.4 向 1.4 扩张期间，funding 同样长期为正，常见约 +0.02% 到 +0.1% 量级，部分时段更高。

结论：

- `funding < 0` 不是 monster 必要条件。
- `funding > 0` 也不能自动判定顶部。
- VNext 应识别 funding regime 与价格、OI、taker flow 的组合关系，不能用统一方向阈值过滤所有候选。

## 3. 跨样本更稳定的共同结构

当前更稳定的共同点是：

1. Binance Alpha / 可验证链上现货路径存在。
2. Binance USDⓈ-M perpetual 存在。
3. Binance 主板 spot 缺失或明显晚于极端行情阶段。
4. underlying spot / free float 相对 futures notional 很薄。
5. futures quote turnover 可以远大于可执行现货深度。
6. 大幅价格扩张时，futures taker-buy quote share 往往仍接近 50%，没有持续 60%-70% 单边 aggressor buy 足以解释涨幅。
7. 主升过程中反复出现大幅上冲和大幅回撤，杠杆仓位两侧都可能在不同阶段成为清算燃料。
8. 成功样本后期往往进入严重衰减，说明完整生命周期和早期 discovery 必须分开评价。

公开数据只能证明这种 market structure，不能证明项目方、做市商或特定实体实施了协调操盘。

## 4. 用户执行约束决定模型目标函数

用户计划：早期发现以后只持有现货，分批退出由用户自行完成。

因此 VNext 主要评价 discovery timing，而不是最终顶部判断准确率。

核心指标：

### Signal Price

模型第一次把标的升级到可人工检查的价格。

### Cycle Base Price

事后定义该轮主升前的局部稳定底部，只用于回测，不允许在 live run 中偷看未来。

### Peak Price

固定 forward horizon 内的最高价格。

### Pre-Signal Multiple

`SignalPrice / CycleBasePrice`

越接近 1 越好。它衡量模型在发现时已经错过了多少早期涨幅。

### Capture Multiple

`PeakPrice / SignalPrice`

越高越好。它衡量发现以后仍然剩余多少理论价格空间。

### Forward MFE

分别记录信号后的：

- 7d MFE
- 30d MFE
- 90d MFE

### Forward MAE

分别记录信号后 7d / 30d 的最大不利波动。现货不会被强平，但过大的早期 MAE 会降低 discovery signal 的可执行价值。

### Recall

历史 monster 样本中，在大行情前成功进入 Early Candidate / Pre-Ignition 的比例。

### False Positive Rate

ZEST、KGEN 等控制样本被错误升级的比例。

目标偏好：`Recall > Precision`，但必须用控制组限制无意义的 Alpha+Futures 全量报警。

## 5. Discovery Engine 候选阶段

### S0 VENUE CANDIDATE

只负责建立 universe：

- Alpha / on-chain path 已确认
- Binance perpetual 已存在
- Binance main spot 缺失

不通知为高优先级机会。

### S1 INVENTORY / VACUUM WATCH

开始出现可被放大的底层条件：

- free float 明显低于 headline circulation
- 去除 vesting / treasury / bridge / CEX / LP 后筹码集中
- ±1% / ±2% / ±5% 可执行现货深度很薄
- futures OI / spot executable depth 比值异常
- Binance index constituents 少或 underlying 现货场所本身较薄

### S2 EARLY CANDIDATE

这是用户最关心的第一类信号。

满足 S1 后，出现至少一组可重复的行为异常：

- 价格开始抬升，同时 futures taker-buy share 仍约 48%-52%
- price ↑ + OI ↑，但 futures aggressor flow 无法解释价格幅度
- funding regime 快速偏离自身基线，方向可正可负
- futures turnover 相对 spot executable liquidity 异常放大
- 出现 PROBE / TEST-PUMP：短时 15%-30% 以上上冲后大幅回落，但 OI / turnover / subsequent floor 没有完全回到原状态
- 同类 probe 在数日到数周内重复

S2 的目标是早，不要求 breakout 已经确认。

### S3 PRE-IGNITION

S2 后出现第二确认：

- 回撤未破坏 cycle base
- OI / funding 经 reset 后再次构建
- retail 与 top-trader positioning 出现稳定分歧，或某一侧 crowding 持续加深
- spot / index 先动、perp 跟随的 lead-lag 重复出现
- 第二次 probe / breakout 的价格中枢高于第一次

S3 是 discovery engine 的最高优先级输出。

### S4 IGNITION

正式 breakout、volume / liquidation expansion、价格进入明显主升。

S4 主要用于验证早期模型是否正确。若模型长期到 S4 才首次发现，虽然方向判断正确，也应在 discovery score 中扣分。

## 6. 两种 fuel regime 都必须支持

### SHORT-FUEL PATH

典型：MYX、RIVER。

可观察序列：

`price ↑ -> funding 下降/极负 -> OI / turnover 放大 -> short exposure 成为潜在买回燃料 -> squeeze / reset`

### POSITIVE-FUNDING PATH

典型：LAB、BTW。

可观察序列：

`price ↑ -> funding 保持正值 -> futures turnover 巨大且 taker flow 仍接近双向 -> 大幅 shakeout -> 价格中枢继续提高`

VNext 不要求先判断幕后实体身份，只判断当前市场状态是否与历史 monster lifecycle 一致。

## 7. 控制组为什么重要

### ZEST

同样具备 Alpha + Futures + no Binance main spot，但截至当前没有形成 MYX / LAB 级多阶段重估。

### KGEN

2025-10-07 Alpha 与 Futures 几乎同时开放，首日 0.35 附近，随后历史高点约 0.70，之后大部分时间没有走出持续 monster cycle。

这两个控制说明：

- venue topology 提高先验概率，但不能替代行为确认。
- 如果 S1/S2 条件无法区分成功样本与 ZEST/KGEN，模型没有实际预测价值。
- 任何“没涨只是项目方后来改主意”的解释不能用于回测，因为它无法被证伪。

## 8. 后期生命周期数据的用途

用户不要求模型自动卖出，但后期数据继续保留为标签：

- SHORT-HARVEST
- LONG-CROWD
- SHAKEOUT
- SECOND-CYCLE
- DISTRIBUTION
- COLLAPSE

用途：

1. 判断某个早期 signal 最终是否真的演化成完整 monster cycle。
2. 区分一次性新闻冲击与可重复的反身性结构。
3. 衡量不同 S2/S3 早期模式的最终 Capture Multiple。
4. 给未来模型训练提供 outcome labels。

这些后期状态不自动触发用户退出。

## 9. TRIA 的 out-of-sample 约束

TRIA 不参与阈值生成。

只有在上述规则冻结以后，才检查 TRIA：

- 当前处于 S0/S1/S2/S3 哪一层
- 是否更接近 SHORT-FUEL 或 POSITIVE-FUNDING path
- 当前 long crowd 是否需要先 reset
- 今日 / 近期 unlock 对 free float 与场所供应的影响
- 后续第一次和第二次 probe 是否满足冻结规则

不能因为 TRIA 的走势不符合规则就回头即时修改阈值；任何修改必须先回到训练样本和控制组重新验证。

## 10. 与 Codex / Monster 当前工作的隔离

本文件只属于 `research/tokens/`。

当前 Monster V2.1、Frank、Codex 正在进行的历史验证继续使用原规则，保证前后样本可比。

VNext 只有在研究规则冻结、训练/控制组扩充、回测指标确定以后，才单独交给 Codex 实现新版本并与 V2.1 做 A/B 回测。

禁止在当前 V2.1 中途修改 runtime 阈值来适配本研究。

## 当前下一步

1. 扩大正样本与负控制到足够规模，至少覆盖 10+ Alpha+Futures+no-Spot 标的。
2. 为每个样本回放 futures launch 后的 price / funding / OI / taker / turnover 序列。
3. 建立不使用未来数据的 cycle-base 定义。
4. 固定 S1/S2/S3 机械规则。
5. 对训练集做 walk-forward / leave-one-out，防止单币过拟合。
6. 最后只把冻结规则应用于 TRIA。

## Sources

- Binance KGEN Alpha + Futures announcement: https://www.binance.com/en/support/announcement/detail/70ff0dd3181940e39bf7601f94fc1935
- Binance ZEST + BTW Futures announcement: https://www.binance.com/en/support/announcement/detail/61e41ce0e4b74dc7a794cc6bf9c57d38
- Binance C + VELVET Futures announcement: https://www.binance.com/en/support/announcement/detail/4f59bfc195ed4484ac810a9b8869fa86
- Binance ZORA + TAG Futures announcement: https://www.binance.com/en/support/announcement/detail/b8d4d5be7c894e1f9bf2c5e091da85e9
- Binance XPIN Futures announcement evidence indexed from official Binance pages
- Raw historical price / taker / funding observations in this study use Binance USDⓈ-M public market data.
