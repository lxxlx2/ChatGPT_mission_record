# Monster Stage77：妖币核心模型验收标准与研发边界冻结

日期：2026-10-13（Asia/Bangkok） | 状态：**STANDARD_FROZEN / MODEL_NOT_VALIDATED / DEPLOYMENT_NO_GO** | 位置：原 Monster Draft PR #30，禁止创建平行监控。

## 0. 本轮冻结的对象

这是**研发目标、评价口径、放行标准与范围冻结**，不是已验证的具体新交易策略参数，也不改变过去任何 Stage40/49/65/68 的冻结阈值、历史样本、失败结论或证据。用户要求先定标准再开始主线研发。本标准仅管理后续**一个** Monster 核心模型迭代；后续可证伪策略的特征、权重、状态转换及测试日期须**单独在首次读取新验证行情前**冻结并提交 Git。

判断顺序：可靠全市场早期发现 D0 → 用当时可见信息筛选值得关注的升级 D1 → 确认具体场所真实可交易与成本 D2 → 用下一段真正未接触数据检验 → 独立其他 AI review → 代码/回归/集成 → 经另行明确授权的 Mac 本地隔离部署。各阶段明确 DONE / PARTIAL / REJECTED / BLOCKED。严禁因为工程CI成功绕过策略失败。

严格遵守 [模块开发规则](MONSTER_MODULE_DEVELOPMENT_RULES.md)、[原 V4 范围](MONSTER_V4_MODEL_AND_LOCAL_ARCHITECTURE.md)、[Mission Spec](../MISSION_SPEC.md)。交易权限和真实通知权限始终单独授予；当前均未授予。

## 1. 不扩张的首版范围

- 目标：尽早捕获 Binance **真实加密资产** Spot 和 USD-M 的异常量价 / 老币复活 / 上新 / 快速上涨，优先研究有可实现潜在净收益的机会。BTC 仅可用于市场相对强弱，不作为 Monster 交易标的研究；不混入资产管理、Frank、NFT、日报、交易所之外的宏观价格提醒。
- 第一版只使用 Binance 官方 Spot / USD-M 已收盘 1m/3m/5m/15m/1h 价格成交量、交易状态及必要时的当时交易深度。对股票/RWA 代理、杠杆倍数前缀、无法确认标的身份、历史未上市或缺来源，分别标 **OUT_OF_SCOPE / AMBIGUOUS / UNKNOWN**，保留来源审计，不偷偷删入负例或并入现货。
- Alpha/DEX 是**独立后续交易场所适配**；现阶段已取得的四个 Alpha 公告和两个官方 CA 仅作为身份/来源边界证明，暂停“95币全量池/Swap考古”和新增稀有 Spot quote 的扩张。若代表性历史可交易性完全依赖 Alpha/DEX，单列 BLOCKED_FOR_VENUE 而不错误认定不能买。后续新增场所必须具备独立 point-in-time 数据和独立验证集，不能把 CEX 发现率偷换为全链覆盖。
- 用户**未指定**单笔金额；历史30U/300U只是固定旧实验，不能当本轮投资额度或新模型硬性筛币线。将 `notional_quote` 作为可选显式参数；未给出则任何按金额的真实冲击/实单收益都输出 UNKNOWN。
- 不启用实盘、不下单、不安装新的 LaunchAgent、不发送 Monster 真邮件、不新增自动化、绝不变更 Frank/Loop/Dashboard/生产SQLite。现有安装器保持 fail-closed。

## 2. 模型最小状态机（输出不得混淆）

1. `D0_RAW_WATCH`：全目标人口扫描；已闭合分钟时点首次异常记录，可重现 event_id、venue/symbol、first_observable_at、observed_at、source_sha / quality、当时价格和特征。即时写独立持久库，不设 top-N / 5条配额丢失。候选漏评要留下真实 backlog。
2. `D1_PRIORITY`：对 D0 后的量比、成交笔数、突破/相对强弱、**允许短期正常回撤的二次真实放量**等提出单一可证伪候选，严格只用已经闭合的历史片段；不凭未来赢家训练当日优先级；高优先级用于决定提醒，不影响 D0 留存。
3. `D2_EXECUTION_EVIDENCE`：区分 `SPOT_VERIFIED`、`FUTURES_ONLY`、`ALPHA_DEX_UNVERIFIED`、`VENUE_UNKNOWN`；必须有当时交易状态、bid/ask 或真实链上池/报价、深度、费用、退出可能性和数据新鲜度，才能使用 `ACTIONABLE_CANDIDATE`。缺少下单额或历史盘口则留 WATCH/SETUP，不得假报 BUY/利润。
4. `EXPIRED / INVALIDATED / LATE`：仅由事先冻结的时钟和当时信息触发，保留审计记录；历史后验暴涨不能逆向复活过期提示。用户通知另需授权与真实送达闭环。

## 3. 分母、事件标签与因果约束

- 同一场所/标的/冻结七日锚点的交易机会以 **coin-date** 为评价粒度；重复 WATCH 次数、不同venue的相同代码、不同名称的同一底层标的不能重复计算独立赢家。另报告一日观察窗口的总原始事件量和唯一币量。
- `CENSORED_SOURCE_MISSING`、`UNKNOWN_LISTING` 和 `UNSCORED_FUTURE_LABEL` 各自独立；现在归档里的 900 symbols **不能**等同于当时900个可交易Crypto，也不能把无未来七日资料币算作0×或负例。来源前缀上真实发生的 WATCH 即使以后缺档也不能删除（Stage73）。
- 两组完全不同的标签必须同表分列：① **发现标签**：固定锚点首根 open → 以后168小时首次1m HIGH触及2×/5×/10×的时刻；它只测 D0 提前量；② **实际策略标签**：WATCH后合理决策和系统延迟下、真实交易场所可买价 → 保守可退出价及成本的净盈亏、最大不利波动/时间。固定七日未来 HIGH **不是**用户从 WATCH 能赚2×。
- 针对发现标签，`early_strict` = 首次 WATCH 在首次跨阈值分钟**之前**；`early_5m` = **首次WATCH**至少早5分钟。另单列 `nearest_prior_watch_5m`（2×前最近一条WATCH至少早5分钟）衡量临界提醒密度，不能把两者混成同一指标。Stage34/39旧汇总中的 `early_lead_at_least_5min` / `nearest_strict_pre_cross_ge5_min` 是最近一条提前WATCH的统计，仅为历史更保守的参照，不能代替新验证集的首次WATCH时刻。若同一分钟无法证明先买后涨，按 NOT_EARLY。未知真正秒级成交不假定先后。
- 来源到达、K线闭合、事件决定、队列处理、尝试投递和实际投递时间分别保存，绝不把某历史源采样日期当实时可见性；缺日前缀保留、未来后缀扰动不影响已发生信号。相同币/时间同类重复必须去重并能恢复。
- 旧样本的已曝光日期、旧赢家、旧 P1/First5/P2 结果只能用于设计和回归，不能改名为全新 holdout。新策略确定前建立**明确的历史暴露集 inventory**，提前冻结真正未观察的验证时段和完整日期选择规则。没有未看过的独立日期或未来 forward 便 `NO_OOS`，不可声称过关。

## 4. 必须同时达到的验收闸门

| Gate | 原先约定且本轮继续采用的目标 / 新的实证要求 | 失败或证据不足 |
|---|---|---|
| G0 来源和范围 | 冻结时间点交易资格/类别，覆盖所有按规则符合范围的标的，原始 attempts/valid/censored/unknown 对账，官方原始字节和发布方SHA记录；有完整普通负样本分母 | 缺上市资格或数据时 `PARTIAL_SOURCE`；不能声称全市场 |
| G1 D0发现 | 源有效的**独立验证**2×事件至少20个、至少3个分离窗口；严格提前比例≥90%、提前≥5分钟比例≥85%；同时逐一报告5×/10×，无正例明确N=0 | 未达则 `REJECTED`，事件不足 `UNDERPOWERED`；不可沿用旧结果宣称PASS |
| G2 D1升级 | 对D0已提前≥5分钟的2×事件，升级也要在真实首次跨2×前≥5分钟，**保留≥80%**；历史5×/10×任何遗漏逐案检验和报告，并遵守历史已冻结的强门槛 | 低于80%或违反强门槛即 `REJECTED`，不能改阈值重跑原holdout |
| G3 关注负载 | 保留全部 D0 到独立观察池；升级事件历史/前向完整天**平均≤5/日、单日≤12**（承接Stage40），监测去重、分布、最老 backlog；这只是注意力目标，**不是每天硬5条无声丢弃的策略** | 负载高或因降噪漏掉G2均不通过；观察池也不能冒充已发邮件 |
| G4 执行与净收益 | 新验证样本完整呈现信号后可买资格、下一可成交报价、假设系统延迟、费用、实际或有严格证据的价差/冲击及退出、失败/删失、净收益分布和最大回撤；以**费后净盈利**与清楚的负例基线作为策略目标，至少30个来源有效且买卖价证据充分的独立交易观察方能作初步统计 | 盘口或单笔金额未知则 `EXECUTION_UNKNOWN`；样本少则 `UNDERPOWERED`；仅OHLC代理不能视为“真实可实现净利润” |
| G5 稳健性与审查 | 新样本日期分布、普通/赢家、现货/合约、首次/再次点火、上市年龄、流动性与来源失效分层；同一份核心规则用于历史与后续 shadow；经过**真正另一AI review**、修复重测 | 代码CI PASS不等于G1–G4通过；没有review输出为NOT_DONE |
| G6 本机交付 | G0–G5及规则规定的真实回归通过，才允许请求本机与Frank独立 shadow 部署授权；随后检验时效、恢复、幂等和投递回执，真Gmail再次单独授权 | 任何前置失败则 `DEPLOYMENT=NO_GO` |

注意：20个2×及≥80%、平均5/日/单日12，沿用原 Stage40/49 标准；`至少30个完整买卖观察`是**本轮新增的最低统计样本要求**，仍不足以证明普遍盈利，必须报告置信区间、日期集中度和选择偏差。不能为了凑30而把 FUTURES HIGH 伪装现货卖价。D0的90%/85%来自原Stage40。任何验证样本条件不足记证据不足，不用“PASS”。

## 5. 唯一主线任务与止损点

A. **先核对事实底座**：逐源重算 Stage39、Stage52、Stage66、Stage70、Stage74/75 已有汇总的一致性；明确失败归因。仅做必要的源/身份核验，不再扩95币DEX考古。

B. **再冻结一个D1新候选**：利用已曝光样本做描述性归因，选择少量当时可观察、明显相关的特征及一个状态机；同时制作全日期暴露台账。策略阈值在选定新的未知日期/真正forward之前独立预注册提交，不能把本阶段诊断当作样本外。

C. **同代码真实验证**：新策略 vs 不变原D0 + 拒绝的P1/P2对照，按G0–G5给出真实结论；失败保留原样并回到模型策略层，不因为Stage数字增加而继续扩研究枝节。

D. **模型通过之后再工程交付**：独立 review、代码测试、Mac 独立部署授权、实际修复，仍严格遵守 [AGENTS.md](AGENTS.md)。

已冻结失败对照：P1v0.1、P1v0.3、D0_FIRST5、P2_HALF_DAY 均 `REJECTED`；历史固定30U/300U资金实验结果不修改。Stage70 SQLite只是离线观察池原型；Stage71有真实独立review但Stage72–76新增代码尚未获得覆盖式新review。

**本次标准与事实清单不自动批准任何新参数、新日期的事后调优、实盘交易或真实邮件；研究新模型须先独立策略/技术合同，再修改核心规则。**

## 6. 当前执行状态

`STANDARD=FROZEN`; `SOURCE_BASELINE=AUDIT_IN_PROGRESS`; `D0_DISCOVERY=HISTORICAL_PROMISING_NOT_FORWARD_VALIDATED`; `D1_PRIORITY=REJECTED_NEEDS_NEW_PROPOSAL`; `EXECUTABLE_NET_PROFIT=UNKNOWN`; `OTHER_AI_REVIEW_OF_NEW_WORK=NOT_DONE`; `MAC=NO_GO`; `GMAIL=OFF`; `AUTOTRADE=NO_GO`; `FRANK=UNCHANGED`; `NOTIONAL_QUOTE=UNSPECIFIED`.
