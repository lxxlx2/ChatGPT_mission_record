# Binance Alpha + 永续 VNext 盲样本验证记录

Updated: 2026-09-30
Status: PHASE_B_FAILED

## 目标

本文件用于把 VNext early-spot-discovery 从 in-sample pattern research 推进到可审计的 holdout validation。

TRIA 继续保持完全 out-of-sample，不参与任何阈值生成或本轮验证。

本文件只属于 research 层，不修改 Monster V2.1 / Frank / Codex runtime。

## 1. Phase A 盲样本池如何固定

2026-09-30 先根据 Binance 官方英文公告固定第一批未参与原规则生成的 Alpha + Futures 标的，再检查其后续行情：

- APR
- COMMON
- RECALL
- IN
- XAN
- NAORIS

选择依据仅为 venue eligibility，不根据后续涨跌筛样本。

官方公告确认：

- APR: 2025-10-23 Binance Alpha + APRUSDT perpetual，同日开放。
- COMMON: 2025-10-27 Binance Alpha + COMMONUSDT perpetual，同日开放。
- RECALL: 2025-10-15 Binance Alpha + RECALLUSDT perpetual，同日开放。
- IN: 2025-08-07 Binance Alpha + INUSDT perpetual，同日开放。
- XAN: 2025-09-23 Binance Alpha + XANUSDT perpetual，同日开放。
- NAORIS: 2025-07-31 Binance Alpha + NAORISUSDT perpetual，同日开放。

## 2. Phase A 预注册候选规则

在查看 Phase A 行情前，上一阶段形成的主要候选为：

`seasoning >= 21d`

加：

`stress_bar = max(abs(premium_high), abs(premium_low)) >= 2%`

加：

`basis_stress_cluster = 最近 3 根 4h premium bar 中至少 2 根 stress_bar`

该规则只来源于此前 MYX / XPIN / LAB / RIVER / BTW / VELVET 与 TAG / ZORA / ZEST / KGEN / C 开发样本。

## 3. COMMON 直接构成 Phase A false positive

COMMON 于 2025-10-27 上线 Alpha + Futures。

经过 21 天 seasoning 后，2025-12-08 附近出现：

- 一根 4h premium high 约 +4.9%、low 约 -11.2%。
- 紧邻下一根 4h premium high 约 +2.3%、low 约 -2.6%。

因此 COMMON 严格满足预注册 `2-of-3` basis-stress-cluster。

同期价格从约 0.0045 区域短时冲到约 0.0112，高 turnover 明显放大；随后快速回落并继续长期衰减。

Binance 官方后续公告确认：2026-01-30 09:00 UTC 对 COMMONUSDT perpetual 自动结算并下架。

结论：

`basis_stress_cluster` 单独作为高优先级 early-spot signal 已被真实盲样本否证。

它最多证明场所 / index / perpetual 出现结构性失衡，不能证明该失衡会演化成持续 monster cycle。

## 4. RECALL 给出第二个同类 false positive

RECALL 于 2025-10-15 上线 Alpha + Futures。

经过 21 天 seasoning 后，2025-11 下旬出现明显 basis stress cluster：

- 一根 4h premium low 约 -5.7%。
- 紧邻下一根 high 约 +2.2%、low 约 -4.5%。

对应价格一度从约 0.10-0.12 区域快速 wick 到约 0.189，但随后几天迅速回到约 0.11-0.12，后续长期趋势继续衰减。

因此第二个盲样本再次证明单次 cluster 的 precision 不足。

## 5. 为什么简单 72h retention 仍不够

COMMON 在极端 spike 后的前 72h 内，4h close 大多仍处于约 0.0050-0.0054，短期依然高于 spike 前约 0.0044-0.0048 的底部区间；但一周后已经回落至更低区间。

RECALL 在 0.189 wick 后的 72h 内也仍维持约 0.11-0.13，短期看仍接近 spike 前 base；后续没有形成持续更高价格中枢。

因此仅要求 24h / 72h `price > old base` 仍可能产生明显假阳性。

## 6. Phase B 新预注册候选：SECOND-CLUSTER HIGHER-BASE

COMMON / RECALL 从盲样本转入开发集以后，只允许利用这两个失败案例提出一次结构性修正。

Phase B 在查看剩余保留样本 IN / XAN / NAORIS 之前预注册：

### First cluster

满足：

- `seasoning >= 21d`
- `stress_bar >= 2%`
- 最近 3 根 4h 中至少 2 根 stress_bar

第一 cluster 只能进入 `STRUCTURAL WATCH`，不能升级为 PRE-IGNITION。

### Independent second cluster

第二 cluster 必须：

- 与第一 cluster 至少间隔 24h；
- 中间存在非 stress reset；
- 再次满足 4h `2-of-3` cluster。

### Higher-base condition

每次 cluster 发生前，只使用当时已经可见的过去数据计算：

`BaseReference = trailing 7d median 4h close`

PRE-IGNITION 候选要求：

`BaseReference(second_cluster) > BaseReference(first_cluster)`

暂时不设置额外 +5% / +10% buffer，避免根据 COMMON / RECALL 事后调百分比。

### 设计含义

用户的目标是尽早发现以后持有现货。

因此：

- First cluster 提醒系统开始关注异常结构。
- Second cluster 检查结构是否可重复。
- Higher base 检查两次结构压力之间，现货 / perpetual 的价格中枢是否真正向上迁移。

一次极端 wick 后迅速恢复原 base，不应自动视为 monster pre-ignition。

## 7. Phase B 保留盲样本

以下标的在新规则写入本文件之前未用于修改规则：

- IN
- XAN
- NAORIS

三者均使用完全相同的预注册规则执行；在三只全部完成规则判定前没有修改 threshold / cooldown / BaseReference 定义。

## 8. Phase B 结果：IN

### 规则判定

第一 independent basis-stress cluster：2025-09-24 至 2025-09-25。

第二 independent cluster：2025-10-04。

两次之间存在非 stress reset，间隔超过 24h。

事前 BaseReference：

- first cluster 前 trailing 7d median 4h close: `0.068105`
- second cluster 前 trailing 7d median 4h close: `0.09282`
- base shift: 约 `+36.3%`

因此 IN 按预注册规则触发 `PRE-IGNITION candidate`。

第二 cluster 的确认 4h close 约 `0.11854`，作为本轮固定 SignalPrice。

### 冻结规则后才查看的 forward outcome

后续 90 天最高约 `0.29878`。

`90d Capture Multiple ≈ 0.29878 / 0.11854 = 2.52x`

本轮目标是发现 10x 级 extreme monster。IN 虽然信号后出现明显上涨，但 90d outcome 只有约 2.52x，不能记为 monster true positive。

同一 90d 窗口后段价格最低已下降到约 `0.05918`，相对 SignalPrice 约 -50%。

Outcome：`FALSE_POSITIVE_FOR_10X_MONSTER / MEDIUM_UPSIDE_CAPTURED`

## 9. Phase B 结果：XAN

### 规则判定

第一 independent cluster：2025-11-18。

第二 independent cluster：2026-03-15。

两次之间存在长期 reset，满足独立 cluster 要求。

事前 BaseReference：

- first cluster 前 trailing 7d median 4h close: `0.03186`
- second cluster 前 trailing 7d median 4h close: `0.0064975`
- base shift: 约 `-79.6%`

因此 XAN 被 higher-base condition 明确过滤，不触发 PRE-IGNITION。

### 冻结规则后检查 outcome

第一 cluster 后总体价格长期衰减。

第二 cluster 之后虽有反弹，后续周线高点约 `0.023079`，仍低于第一 cluster 前的 0.03186 BaseReference，也没有出现 10x 级持续重估。

Outcome：`TRUE_NEGATIVE_FOR_10X_MONSTER`

这说明“second cluster 本身”仍可发生在长期衰减标的中；BaseReference 的方向信息确实增加了过滤能力。

## 10. Phase B 结果：NAORIS

### 规则判定

第一 independent cluster：2025-09-09。

在第一 cluster 后出现 reset；随后一组更早的再次 stress 因不足 24h cooldown 不计作独立 second cluster。

满足 cooldown 的第二 independent cluster：2025-09-11。

事前 BaseReference：

- first cluster 前 trailing 7d median 4h close: `0.02459`
- second cluster 前 trailing 7d median 4h close: `0.02663`
- base shift: 约 `+8.3%`

因此 NAORIS 按预注册规则触发 `PRE-IGNITION candidate`。

第二 cluster 的确认 4h close 约 `0.07645`，作为本轮固定 SignalPrice。

### 冻结规则后才查看的 forward outcome

后续 90 天最高约 `0.15990`。

`90d Capture Multiple ≈ 0.15990 / 0.07645 = 2.09x`

90 天内后续最低约 `0.01950`，相对 SignalPrice 约 -74.5%。

NAORIS 同样捕获到真实高波动阶段，但没有发展成 10x extreme monster。

Outcome：`FALSE_POSITIVE_FOR_10X_MONSTER / MEDIUM_UPSIDE_CAPTURED`

## 11. Phase B 总结

固定 holdout 共 3 个：IN / XAN / NAORIS。

预注册规则结果：

- IN: SIGNAL，90d Capture 约 2.52x，针对 10x monster 为 false positive。
- XAN: NO SIGNAL，后续未形成 10x monster，true negative。
- NAORIS: SIGNAL，90d Capture 约 2.09x，针对 10x monster 为 false positive。

若目标定义为 `90d >= 10x extreme monster`：

- signals: 2
- monster true positives: 0
- false positives: 2
- true negatives: 1
- observed precision on signaled Phase B holdout: `0 / 2`

因此 Phase B 明确判定 `FAIL`。

这不代表 basis stress / higher-base 完全无价值。两只 signal 都抓到了后续约 2x 级上涨，说明这些变量可能更接近“高波动 / 可交易重估”检测器；现有证据不足以证明其能区分用户真正目标的 10x monster。

## 12. 防止验证污染

Phase B 完成后：

- IN / XAN / NAORIS 全部转为 consumed validation / development evidence。
- 禁止继续修改参数后再次把三者计作 holdout。
- APR 早已在 Phase A 过程中部分查看，也不能恢复为 untouched holdout。
- COMMON / RECALL 已用于 Phase B 规则修正，同样属于 development evidence。
- TRIA 仍保持完全 untouched，不允许因为 Phase B 失败而打开 TRIA 调参。

若继续研究，必须先提出新的、可解释的结构变量，再选择全新的 Phase C holdout 并在查看 outcome 前固定规则。

## 13. 当前模型含义

当前证据支持：

`basis stress` 可以识别 perpetual / index / underlying liquidity 的异常压力。

`repeated cluster + higher base` 能过滤部分长期衰减标的，例如 XAN。

当前证据不支持：

`repeated cluster + higher base` 足以把约 2x 的高波动重估与 10x extreme monster 分开。

下一轮若继续堆 price / premium threshold，过拟合风险会进一步上升。更值得研究的是此前 S1 中尚未充分量化的结构变量：

- executable spot depth / futures turnover ratio
- free float 与可交易筹码集中度
- Binance index constituents / underlying venue fragility
- spot lead vs perp lead
- chain / CEX inventory movement

这些变量需要在新的 development set 中建立后，再进入全新的 holdout。

## 14. APR 状态

APR 已在 Phase A 过程中查看部分 post-seasoning 历史，因此不能再算 untouched holdout。

本轮已查看的早期 post-seasoning premium 窗口没有观察到类似 COMMON 的明确连续 2-of-3 extreme cluster；该结论只覆盖已检查窗口，不宣称完整生命周期无 cluster。

APR 后续可进入 development / robustness set，但不能重新包装成 untouched validation。

## 15. 当前证据等级

CONFIRMED：

- COMMON 与 RECALL 都能在 21d seasoning 后产生符合 Phase A 定义的 basis stress cluster，但没有发展成持续 extreme monster cycle。
- COMMONUSDT 后续由 Binance Futures 于 2026-01-30 自动结算并下架。
- 简单 `first cluster = PRE-IGNITION` 已被 blind data 否证。
- Phase B 的 IN / XAN / NAORIS 在查看 outcome 前使用同一套预注册 SECOND-CLUSTER HIGHER-BASE 规则。
- IN 与 NAORIS 触发信号，但 90d Capture 分别仅约 2.52x 与 2.09x。
- XAN 因第二 cluster 前 BaseReference 较第一次下降约 79.6% 被过滤，后续没有出现 10x monster。
- Phase B 针对 10x monster 的 observed signal precision 为 0/2，因此本轮验证失败。

INFERRED：

- basis stress 更像高波动 / 市场结构失衡检测器，目前还缺乏 extreme-monster-specific discrimination。
- thin spot / free float / index fragility 等 S1 结构变量可能是下一轮提高 precision 的关键。

UNRESOLVED：

- 哪一个 S1 结构变量能在不牺牲早期 recall 的前提下区分 2x repricing 与 10x monster。
- spot-depth / futures-turnover ratio 的历史数据可获得性与稳定定义。
- free-float / holder concentration 如何跨链统一量化。
- 新 Phase C holdout 上的真实 precision / recall。
- TRIA 当前是否满足任何候选规则；冻结下一阶段规则前继续禁止查看。

## Sources

- Binance APR Alpha + Futures announcement, 2025-10-23.
- Binance COMMON Alpha + Futures announcement, 2025-10-27.
- Binance RECALL Alpha + Futures announcement, 2025-10-15.
- Binance IN Alpha + Futures announcement, 2025-08-07.
- Binance XAN Alpha + Futures announcement, 2025-09-23.
- Binance NAORIS Alpha + Futures announcement, 2025-07-31.
- Binance Futures COMMONUSDT delisting announcement, 2026-01-30 settlement.
- Binance USDⓈ-M public futures kline / premium-index historical data, queried 2026-09-30.
