# Binance Alpha + 永续 VNext 盲样本验证记录

Updated: 2026-09-30
Status: ACTIVE_RESEARCH

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

接下来对三者只能执行预注册规则并记录结果，禁止在看完单个样本后再次修改阈值。

如果 Phase B 失败，必须把失败记录为模型证据，再建立下一阶段新 holdout；不能回头把同一批样本继续包装成盲测。

## 8. APR 状态

APR 已在 Phase A 过程中查看部分 post-seasoning 历史，因此不能再算 Phase B untouched holdout。

本轮已查看的早期 post-seasoning premium 窗口没有观察到类似 COMMON 的明确连续 2-of-3 extreme cluster；该结论只覆盖已检查窗口，不宣称完整生命周期无 cluster。

APR 后续可进入 development / robustness set，但不能重新包装成 untouched validation。

## 9. 当前证据等级

CONFIRMED：

- COMMON 与 RECALL 都能在 21d seasoning 后产生符合旧候选定义的 basis stress cluster。
- 两者均未因此发展成持续 extreme monster cycle。
- COMMONUSDT 后续由 Binance Futures 于 2026-01-30 自动结算并下架。
- 简单 `first cluster = PRE-IGNITION` 已被 blind data 否证。

INFERRED：

- repeated independent cluster + higher pre-existing base 可能比单次 cluster 更有区分度。
- 结构压力需要配合价格中枢迁移才能更接近用户需要的 early-spot discovery。

UNRESOLVED：

- SECOND-CLUSTER HIGHER-BASE 在 IN / XAN / NAORIS 上的盲测结果。
- 24h cooldown 是否长期合理。
- trailing 7d median 4h close 是否优于 14d median / VWAP。
- 该结构在更多年份、更多 Alpha + Futures cohort 上的 precision / recall。

## Sources

- Binance APR Alpha + Futures announcement, 2025-10-23.
- Binance COMMON Alpha + Futures announcement, 2025-10-27.
- Binance RECALL Alpha + Futures announcement, 2025-10-15.
- Binance IN Alpha + Futures announcement, 2025-08-07.
- Binance XAN Alpha + Futures announcement, 2025-09-23.
- Binance NAORIS Alpha + Futures announcement, 2025-07-31.
- Binance Futures COMMONUSDT delisting announcement, 2026-01-30 settlement.
- Binance USDⓈ-M public futures kline / premium-index historical data, queried 2026-09-30.
