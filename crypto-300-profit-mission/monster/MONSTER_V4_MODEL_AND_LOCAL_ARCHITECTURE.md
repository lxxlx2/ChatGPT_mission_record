# Monster V4 — 实用型本地妖币发现与预警模型（研究合同 v0.1）

状态：**研究方案 / 未复跑 / 未经独立 review / 未上线**；目标从发现到用户通知尽可能短。已有的 V3-062 仅为 *历史参考配置*，不是生产预测模型。
依据：[历史数据复核](MONSTER_V4_DATA_BASELINE_2026-10-10.md)、[V2 D1](../local-agent/docs/MONSTER_D1_V2.md)、[V3 报告](../local-agent/PHASE_MONSTER_D1_V3_REDESIGN_REPORT.md)、[BTW 漏报](../health/2026-09-28-btw-monster-missed-alert.md) 和既有 [D2 资料源审查](../local-agent/docs/MONSTER_D2_SOURCE_AUDIT_V1.md)。

## 0. 必须先解决什么

用户目标不是“为 2021–2023 挑出 20 个未来 5x”而是**2026 年今天异常开始时尽早注意到，过时就不再推荐，真实可以下单，重要变化及时通知**。

旧模型存在三个不能通过加十条数据质量检查来修复的问题：

- V3-062 3h 触发确认 + 1h K线：MMT / AVNT / BTW 可能已涨过最佳早期观察期；把 WAIT 当成安静会漏报。
- 历史 median 89 / p95 127 entity/day：不能把所有 D1 激活直接发邮件。
- BTW 被 top3 深查限制丢在无持久队列里：发现器存在并不等于交付链路健康。

本模型的**工程目标**（不是已测 SLA）：全市场 1–3 分钟广扫、重大早期事件从可用市场数据出现至本地事件写入 <2 分钟、自然状态更新至本地通知/Gmail <5 分钟；数据源失败时展示最后成功时间，不声称实时覆盖。初始前向 shadow 会以真实延迟分布决定是否能达到这些数字。

## 1. 交易所与标的范围

首期仅 Binance USDT **Spot** + **USD-M Perpetual** 的活跃及近期退市历史标的，按官方 exchangeInfo 分类：

- `CEX_SPOT_BUYABLE`：当前开放真实 Spot 成交、交易规则与深度有效，可作为不加杠杆的 30USD 实际跟随性评估。
- `CEX_FUTURES_ONLY`：只有合约或已停止 Spot 的标的；允许妖币异动预警，**不能**写成“30USDC 现货可以买”。不能将保证金需求/资金费率忽略。
- `ENTITY_AMBIGUOUS`：Spot/Futures symbol / prefix / 合约更替有歧义时，分开显示与独立监测，不人工强合并。
- 不把 Solana 链 meme、Binance Alpha、BSC DEX 与 CEX 行情强行合并到同一个验证结果。后续可接独立 onchain source，再按链+mint/pool 做验证。

所有 WATCH / IGNITION 明确标注 Spot 或 Futures、原始 symbol、可购买/仅合约、可用首价和报价时间。

## 2. 重新定义三段模型

### D0：廉价、全市场、不丢人的实时发现

多源覆盖：官方 Spot/Futures exchangeInfo（定期）、24h ticker（全市场快照）、1h 与轻量 15m/5m closed klines；WebSocket 可用于减延迟，REST 轮询/补缺为恢复方案。**不允许只用一天 top3 涨幅币、只跟现有热门榜或赢家名单**。所有候选保存 `symbol + venue + first_seen + last_checked + deadline + reasons`；取深查有限额时必须 oldest-first 保底、剩余按优先级，无法处理的记录在 durable backlog 而非文本日志中丢失。

D0 捕获事件可以是：1h 出现 V2 A–E 任一触发、15m/5m 突然量价显著变化、全市场相对强势跃升、老币低成交恢复、上新首周、新合约异动。某一条信号源缺失只使该证据不可用，不得阻断其它独立发现路径。

**不能等候 3 个 1h bar 才生成 WATCH。** V3 第二确认可作为高置信解释，不是信息发送唯一许可。

### D1：结构性 WATCH / SETUP（及时而不虚假建议买入）

将候选所需证据分 6 组，先低成本计算（所有阈值为待回测候选，不是既定交易规则）：

1. **Momentum / breakout**：15m 或 1h 收盘超此前 24h 高位、BTC-relative 1/4h 正值与排名；观察是否“上冲回落”。
2. **Volume / trades**：15m/1h quote volume 相对之前 24h 同单位历史中位数倍数、独立 trade count、最近 taker buy share；当前段不提前当作已完成。
3. **Persistence**：5/15m 连续跟进、回踩保持、同向上涨非单根极端 high wick。
4. **Squeeze**（可选 Futures）：公开 OI、OI 变化、funding、top/global long/short 与实际 price 同向性。OI/funding 无数据可以 WATCH，但不能声称“已确认逼空”。
5. **Execution**：Spot best bid/ask spread、指定 30USD 深度估算、ticker freshness、交易状态，合约仅附风险不提供 30USD spot 执行结论。
6. **Cross-venue + lifecycle**：同一 verified entity 的 contemporaneous Spot/Futures 同向表现、上新年龄、旧币复活历史。年龄未知明确 unknown，不用“缺 30d 数据”排除新上市。

重要消息分级：
- `WATCH_EARLY`：两个不同类别的当时证据指向异常，或新上市/异常成交单一路径强烈，立刻给 **观察级预警**；绝不伪称 confirmed buy。
- `SETUP_ACTIVE`：更多独立佐证（例如成交额、突破站稳和持续性），继续实时监测，发“增强/减弱”更新，而非持续沉默。
- `IGNITION_ACTIONABLE_SPOT`：实际 Spot 可交易 + 30USD 深度/价差不差 + 信号发生时效有效 + 未过度追高。标注仅是交易“候选机会”，**不是**已证明盈利或自动购买。
- `IGNITION_FUTURES_ONLY`：满足技术条件但无 Spot；提醒与现货机会明显分开。
- `EXHAUSTION` / `INVALIDATED`：量能/价位/结构转弱、交易所停牌、突发大幅价差、历史 WATCH 被追涨/超时，及时发布失效更新。

WATCH 要高召回、低发送门槛；IGNITION 要满足真实执行而非“只要历史上涨过”的回测标签。**未知项用解释 + 下调级别，不要一概沉默**；交易所是否开放下单、行情时效和异常 price/volume 是必须的基本事实。

### D2：现实追随性与优先级

研究配置打分仅用于候选排序与 A/B 验证，非涨幅概率：
- 多时框价格结构 20
- 成交额相对增长 + taker 强度 25
- 同向持续与回撤吸收 15
- BTC / peer 相对强度 15
- 有证据的衍生品/跨场景强化 10
- 已验证可交易与现价深度 15
- 合计100，空缺证据附 gaps，不杜撰 OI、orderbook、price。

观察级优先测试 score 40/55；SETUP 55/65；真实执行级另需盘口检查。**不在上线前宣称 40/55 是最佳阈值**。模型选择在 forward replay 中按机会覆盖、通知数量、可执行回报、延迟、极端回撤联合评估。强势新币独立早报路径，不要求 30d 旧币基线或 3h 守候。

明确反向条件：超时、无可用 Spot、深度突降、价差/滑点失控、跌回 breakout 前区间、OI/量能断裂、连续极端上影等均可从 WATCH 降级；即使亏损风险高也不能把非交易 WATCH 消失掉。

## 3. 数据质量的务实规则

拒绝**凭空造数**，但不要让低优先级数据缺失使整个候选消失：
- 核心：同一 venue/symbol、官方 close bar 完整、观察时间、当前交易状态、当前真实价格。缺核心 = `DELAYED/UNAVAILABLE` + 异常事件保留，不能发“立即买”。
- 增强：OI、资金费、taker long/short、跨所同步、完整 30d 历史、真实盘口深度。缺增强 = `UNKNOWN` + 缺口说明，允许 WATCH / 低可信 SETUP。
- 旧长历史可从官方 ZIP + checksum 复用；**2025+ Spot ZIP 微秒**与 Futures 毫秒分开处理。数据缺日/错序时断开样本，不前填虚构交易价格。
- 追踪 `first_observable_at`、`source_observed_at`、`ingested_at`、`decision_at`、`mail_sent_at`，实际可见的通知延迟才是工程成败，不把链下任务定时时间当作市场首次触发时间。

## 4. 实用通知策略（不多等，不滥发）

两级及时推送。**WATCH 也是必须处理的事件**；重大 WATCH 不能等到某一天日报再讲。IGNITION、EXHAUSTION 和关键级别升级发独立通知。只对同一 `venue/entity/event/transition` 做去重，例如重复 poll 不重发；若交易量/成交条件发生重大变化允许更新。**不得硬设“每日最多3个实际分析”的丢失上限**；队列过载时以合并摘要保全全部 WATCH、紧急级别单独送达，同时展示 backlog 与最长等待。

候选级 `first_seen` 一旦持久化不可事后改写。监测到已过期的数据也要记作 `LATE` 并展示，但不可当作当前机会补发；对因调度错误错过的重大早报单独报告 `MISSED_ALERT`，不可重写历史成“已通知”。

投递使用有序 outbox、持久 ID、Sent readback、错误重试、确认阈值与“只发变化”；参考已经跑通的 Mission Control Gmail 身份/哈希/人工复核模式，但**独立 Monster outbox/SQLite**，不共用 Frank 的待发信箱。凭据或网络中断恢复后过时的 IGNITION 不应当作即时价格发出，可发“迟到回顾（不可追）”的健康摘要。

## 5. 本地技术架构（先实现 → review → 试运行 → 授权部署）

```text
Binance Spot + USD-M exchangeInfo / ticker / klines / optional WS
  -> normalized observations, completed-bar UTC clock, immutable source refs
  -> D0 full universe scanner (no missing deferred candidates)
  -> SQLite watch_queue + per-venue symbol lifecycle
  -> D1 cheap multi-path WATCH / confirmed SETUP
  -> bounded D2 deep-fetch of 5m, taker, funding, OI, book depth
  -> executable score + state transition + audit record
  -> Monster-specific local notification and Gmail outbox (after authorization)
  -> read-only localhost status: freshness/backlog/missed alerts/last receipts
```

- Python 3.11+，既有项目 `websockets==15.0.1`、标准库 sqlite3 / urllib / decimal / json，不引入不必要的大型服务。
- 任务互不依赖：`MonsterCollector` / `MonsterScanner` / `MonsterEvaluator` / `MonsterNotifier` / `MonsterDashboard`。本地独立工作树、独立数据库、独立 LaunchAgent（以后单独启用），**不修改 Frank Writer 的 sqlite 或控制服务**。
- 数据库存：`universe_snapshot`、`candles`、`candidate_queue`、`event`、`features`、`outbox`、`sent_receipt`、`runtime_health`； `event_id` = `source + venue + symbol + first_seen_window + state_transition` 的稳定哈希。
- 扫描循环与队列：统一使用数据观测时间、上次成功扫描时间；重启由 SQLite cursor 恢复；服务健康不能只看进程 PID；最老队列年龄和全市场 coverage 必须可见。原 BTW bug 用固定回归保护。
- 不需要每轮读取百万档案；历史原始资料在私有 Mac evidence 根目录，只读/复用；实时扫描进程以增量 kline、Ticker snapshot 和限流批量深查工作。
- 保存请求调度与限流、429/backoff、断线续传、抽样 retry，做看得见的数据健康，而不是无限阻断。

## 6. 验证框架及放行

**先用已有资料分析与 Mac 真档案离线回放，再新 forward shadow；无立即生产信号承诺。**

1. Baseline audit（本阶段）：原 72 组 TRAIN 汇总、2024 固定 VALIDATION、已暴露 MMT/AVNT/BTW、BTW 漏报归因，结果可重现。
2. 数据层：现存 Binance ZIP 校验和、断档、时间戳单位，取真实 2025–2026 曝露阶段做回顾研究；记录币种覆盖率而不只挑赢家。
3. 离线研究：D0 相比历史 5x/10x 的首次提前性、每日日 WATCH / IGNITION 量、谁漏了、耗时、非2x 的无效通知；全部以分钟或小时为单位，不把未来的 7d high 当成交价。
4. 交易近似：历史只有 OHLCV 时，按触发后的**下一完整5m bar**给出可观察 proxy，并单列费/冲击假设；不能称为实际可成交收益。样本有盘口时用真实 timestamp orderbook /30USDC 模拟。
5. 未来真 forward（V4 首次未暴露）：固定候选规则后连跑至少14天 shadow，覆盖低成交日/高波动；高风险改动与少数独立典型样本需独立复审；适当延长到30天观察 5x 基率，不能承诺恰有大涨币。
6. 先接 WATCH / IGNITION `DRY_RUN_LOCAL`，压测断网、429、Gmail/OAuth 恢复、重复重启、旧报延迟、安全回滚。测试全部通过、人工确认后再启用真实 Gmail。**重点是用户收得到及时且能解释的早报**，不用永无止境增加和收益无关的异常边界测试。
7. 最后才给 Mac 一段无注释的固定版本部署命令；不提前改已有 Frank/Price/NFT/Portfolio/ChatGPT 任务，不提前启用 production trading。

验收指标分两类：

| 指标 | 计划目标（待 Mac 验证，不是假定达到） |
|---|---|
| 全市场首次扫描覆盖 | 100% 官方已列可交易目标，遗漏可见并进入恢复队列 |
| D0 的遗漏/最老待查 | 持久化队列，无静默丢样；下轮覆盖 deferred |
| WATCH 通知延迟 | 日常目标 p95 <5min，重大过载有迟到标签 |
| 真实 IGNITION 通知延迟 | 事件升级后 p95 <5min，不补发过期现价 |
| 每日通知量 | 不设静默丢人的绝对 top3；按信息价值、去重与摘要控制 |
| 典型 MMT/AVNT/BTW | 重放中逐项显示“首次 WATCH 与首次可买”时间/交易条件 |
| 可执行真实收益 | 在完整报价/费与延迟证据前 **UNKNOWN** |
| Frank 副作用 | 0 改动、0 停机要求，Monster 独立部署回滚 |

本稿的 `WATCH/SETUP/IGNITION` 阈值均为研究候选，不是经过证明的可盈利买卖策略。**优先独立实现与正确通知，再用数据迭代，不能为了凑信号而伪造涨幅概率**。
