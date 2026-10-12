# Monster Stage42：483个原V4首次WATCH，冻结P1 v0.1真实USD-M分钟回放 — 降噪通过，妖币发现惨重漏失，正式FAIL

日期：2026-10-12，曼谷。仍在唯一Monster原[Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，遵循[模块开发规则](MONSTER_MODULE_DEVELOPMENT_RULES.md)严格先数据→策略指标→技术方案→实际相同代码测试。**本轮决不修改原V4 D0、Frank、Gmail、Mac/交易服务，也不改变候选参数去“优化”已曝光案例**。

## 一、真实代码、来源和提交证据

候选 v0.1 在读取新1m数据前已事先冻结：[Stage40策略与指标门槛](MONSTER_STAGE40_WATCH_PRIORITY_IGNITION_KPI_AND_STRATEGY_PROPOSAL_20261012.md)；[Stage40不可事后修改的机器阈值合同](evidence/monster_stage40_candidate_priority_v01_frozen_before_any_holdout_20261012.json)，[Stage41因果技术设计](MONSTER_STAGE41_P1_PRIORITY_CAUSAL_TECHNICAL_DESIGN_20261012.md)；[Stage42原483样本源SHA预登记](evidence/monster_stage42_all483_exposed_firstwatch_p1_pilot_prereg_20261012.json)。这些均已提交在真实行情回放之前，研究窗口固定为[Stage39官方源SHA全部900×6底册](MONSTER_STAGE39_FULL900_SIXDATE_ORIGINAL_V4_REAL1M_SHA_MARKET_DISCOVERY_FINAL_20261012.md)，不是一批新的独立样本。

实际研究代码：
- [P1 v0.1生产隔离纯因果判定](../local-agent/scripts/monster_v4_stage42_p1_priority_v01.py)：未来bar**即使恶意损坏也不可改变当前结果**，两个闭合3m确认点t+3和t+6、不回填t+0早报、不产生BUY。
- [所有483个实际Stage39原V4首WATCH source SHA取数器](../local-agent/scripts/monster_v4_stage42_p1_all483_official1m_pilot.py)：只下载watch前61min至watch后5min所需官方USD-M每日1m，严格校验发布者`.CHECKSUM`和整天1440连续源。全员483，包括433个未达窗口2×的普通WATCH，不只看已知赢家。
- [Stage42 12原Artifact ZIP SHA重新核验与完整分母聚合器](../local-agent/scripts/monster_v4_stage42_original12_sha_all483_priority_aggregate.py)：GT未来标签只在判断之后附加，并对每个日期的P1升级数与D0真正提前事件进行检查。

真实GitHub Actions：
- [Stage42纯代码因果单测 #38210967681](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38210967681) **SUCCESS**；
- [Stage42官方分钟首WATCH 12源分片 #38211198743](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38211198743) **12/12 SUCCESS**；
- [Stage42原12 ZIP/JSON SHA重新下载、全483数据聚合及Git提交 #38211358336](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38211358336) **SUCCESS**。
- 真正机器源：[Stage42 483候选完全未删负样本的逐条成交量、真实P1判断及官方SHA](evidence/monster_stage42_all483_firstWATCH_priority_source_cases.jsonl)、[Stage42实际门槛与6日期每日升级次数](evidence/monster_stage42_original12_SHA_first483_P1_metrics.json)。CI机器数据已真实Git提交 `c1251d05d5b9af49408d219d94f1941c291aa5b7`。聚合Artifact ID `11729194392`，ZIP SHA256 `4ba89a79aa31ae05d6fe4462e5cc8dfa67bc53264940853275733549f7cc7115`，另行下载独立验证原ZIP字节、CRC和483行结果一致。

## 二、冻前目标对真实结果：FAIL

| 指标 | 历史事实/结果 | 是否达到预登记 |
|---|---:|---|
| 首次WATCH币日期 | 483 | 完整研究分母 |
| P1 v0.1升级币日期 | 120 | 保留24.84%，较原首次WATCH减少75.16% |
| 历史高优先级升级均值 | **2.857条/天** | 均值≤5：PASS |
| 最高单日升级 | **10条** | 单日≤12：PASS |
| 原始V4 D0未来2×且严格提前的币日期 | 48 | 冻结历史比较基线 |
| P1对上述事件仍至少提前5分钟的保留 | **15/48 = 31.25%** | 必须≥80%：**FAIL** |
| P1升级中日历2×币日期 | 17 | 其中真正提前≥5分钟仅15；其余2个P1晚于或等于真实首次2× HIGH |
| P1升级中未来未达固定起点2× | 103/120=85.83% | 并非真实可交易失败率 |
| 原合约窗口唯一5× ALPACAUSDT | **P1不升级** | 极高价值机会漏失，策略警示 |

**不可只引用通知量PASS而宣布策略成功。** 预冻结规则要求降低用户负担和保留重要机会同时过线；其中重要发现保留仅31.25%，差距极大，因此候选`P1_V01_REJECTED`，不能进入生产部署、不能把P1替换原V4 WATCH。

相较Stage39原市场所有1,108个WATCH事件，120次P1升级数看似大幅下降，但**一个是含重发的全部WATCH事件，另一个是一币日期首次WATCH的单次升级**，口径不同；严格的可比口径为原483个有首WATCH的币日期 vs 120个P1研究升级。

## 三、为何失败：不是「资金/量不够」而是错误的持续不回调假设

仅统计**48个原V4真正提前2×案例**，独立读取每条P1量价：
- 首次WATCH时近60m涨幅低于8%：**6/48**；
- WATCH后第一个3m确认close跌破最初WATCH close：**25/48**；
- WATCH后第二个3m确认close跌破最初WATCH close：**21/48**；
- 15m官方quote成交额低于250,000 USDT：**1/48**；
- 15m相对前45m放量倍数低于1.5×（或无法计算）：**1/48**。

这些失败条件会在同一案例同时出现，**不能简单相加当成独立漏报币数**。机制上并非流动性门槛太高才过滤多数暴涨币，而是原V4优秀的早期WATCH经常发生在短时拉涨后；接下来3–6min出现正常回撤但随后仍可能暴涨。以「下一轮、下两轮都绝对不跌破首WATCH价格」作为高优先升级条件，会系统性漏掉这种行情。

具体例子：2025-04-19 **ALPACAUSDT**是这六周唯一经完整1m/1h官方SHA确认的5×高价事件。原WATCH价约0.04211 USDT，P1的WATCH时60m涨幅约+7.014%（没有达到冻结8%），两轮确认收盘分别0.04170、0.04121低于初始价；当时15m真实quote成交额约327.68万USDT、归一化放量5.008×，故**并非缺乏真实量能，而是动量和回撤持续性条件否决**。上述价格及时间来自原始固定记录，不是未来实际可成交退出价。

**研究判断（不是已验证新策略）：** D0应维持最早发现。若以后需要升级排序，必须能识别「早期WATCH后允许正常回撤、但仍有持续交易与再次放量」以及「短时资金爆发但质量不佳」的差异；不能不经新独立日期就反复改变P1阈值直到拟合旧赢家。

## 四、研发Gate与下一步

- `STAGE39_FACTUAL_FULL_USDM_CENSUS=PASS`
- `STAGE40_CANDIDATE_P1_V01_NOISE_BUDGET=PASS`
- **`STAGE40_CANDIDATE_P1_V01_MATERIAL_EARLY_RECALL=FAIL`**
- **`STAGE40_CANDIDATE_P1_V01=REJECTED_NOT_FOR_DEPLOYMENT`**
- `STAGE42_REAL_1M_PUBLISHER_SHA_SOURCE=PASS`、`STAGE42_ORIGINAL12_SHA_FULL483=PASS`
- `OOS_PREDICTIVE_VALIDITY=NOT_DONE`、`REAL_EXECUTABLE_NET_PROFIT=UNVERIFIED`、`OTHER_AI_REVIEW=NOT_DONE`
- `MONSTER_DEPLOYMENT=NO_GO`、`FRANK=UNCHANGED`、`GMAIL=OFF`、`AUTO_TRADE=NO_GO`

下一步不是重调已研究日期的几个百分点，而是：先对截至Stage42的所有历史日期完成真实已曝光样本审计，再在**独立未使用日期**上锁定另一套策略候选及完整不涨普通币分母，另行测试「早期D0原始提醒不能丢失」和「处理负担是否可容忍」。没有充足可信的OOS样本就明确 `INCONCLUSIVE`。原V4产生的D0事件必须保留，不允许因为本P1失败直接停掉妖币发现模块。
