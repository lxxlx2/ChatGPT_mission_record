# Monster Stage47：真实原V4全市场重复WATCH与2×首次越线，是否有必要研究二次点火？

日期：2026-10-12（Asia/Bangkok）。唯一[Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。本阶段返回策略设计前的**事实数据补充**，不修改冻结P1v0.1/v0.2、不重调阈值、不引入BTC交易，也不触发任何Mac/Frank/Gmail/下单服务。

## 已核实来源与再算方法

- 来源：[Stage45六个新日期、全5400合约符号日期、官方9天真1m SHA与未改原V4真实WATCH时间](evidence/monster_stage45_blind_all5400_originalV4_P1v02_cases.jsonl)；[源36份原始SHA与完整指标](evidence/monster_stage45_blind_900x6_SHA_P1v02_metrics_and_gates.json)。本阶段只读这些已经验收、持久化的源文件，不为了看赢家另选日期/币，不读取未见新行情。
- [真正Stage47全样本重复WATCH时间复算脚本](../local-agent/scripts/monster_v4_stage47_fullmarket_repeat_watch_second_ignition_data_audit.py)核对全部5400币日期身份、3465个1m和1h双源有效币日期、41个有2×的真分钟越线、3424个非2×普通样本，并检查原WATCH时间升序及事件数与原Stage45完全一致。Stage47的重复WATCH仅来自**原生产V4此前就发出的信号UTC事件**，不会伪造3m/5m或引用未来HIGH改变观察时刻。
- [Stage47 GitHub CI #38215742027](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38215742027) 实际 **SUCCESS**，所有[机器审核、全41个2×事件重复WATCH事实、每日期普通币对照、原来源SHA](evidence/monster_stage47_all_market_first_and_repeated_D0_watch_vs_real2x_audit.json)已经提交到原Monster分支；这不是独立其它AI Review。

## 原V4重复预警与早期妖币事实

| 全六个真实历史七日窗口 | 实际 |
|---|---:|
| 可评分的合约symbol×日期 | **3465** |
| 未来固定窗口起点开盘价到HIGH≥2× | **41** |
| 未来未达固定日历2×的正常/普通样本 | **3424** |
| 原D0全部WATCH事件（含重复） | **936** |
| 有WATCH的不同币日期 | **437** |
| 2×事件在全部168h里至少两个WATCH | **39/41** |
| 2×事件在**首次越线2×之前**已经有第二次WATCH | **31/41** |
| 2×事件在首次越线前6小时内仍有WATCH | **26/41** |
| 未达2×的普通币日期有WATCH | **397/3424** |
| 未达2×的普通币日期有至少两次WATCH | **138/3424** |
| 所有来源有效事件中重复WATCH（除第一次） | **499** |

**最重要的口径说明：** 31/41是事后给有真2×的币日期加上「第二次原WATCH必须在真正首次2×分钟之前」的条件；正常币的138/3424则统计全7日所有重复WATCH，时间窗口不对称。两者是**因果时序事实/未来事件描述**，**不能据此计算一个已部署二次WATCH策略的准确率、净收益或可提前买入比例**。而且有2×者并非所有都有第二次早报，强制等待第二次WATCH会牺牲不少第一波行情。

**BULLAUSDT（2026-01-26窗口）** 是用户重点关注的历史10×级巨大机会，Stage46已验证其首次V4 WATCH在2026-01-28 11:33 UTC且P1v0.2由于首次60m涨幅仅2.16%、15m quote约27.25万USDT而不晋级。Stage47补充事实：
- 首次越线2×分钟：2026-01-29 07:59 UTC。
- 第一次V4 WATCH：2026-01-28 11:33 UTC，**提前1226分钟**。
- 第二次V4 WATCH：2026-01-29 05:42 UTC，**仍提前137分钟**。
- 该7天窗口共20条原WATCH，但**首次2×之前只有2条**，其余属于越线之后，禁止拿越线后报警冒充早发现。
- 若第二次WATCH有独立可信的当时量价和原始订单流证据，它可能成为再次评价的**研究对象**；本轮并没有真正计算第二次当时的P1或真实可下单性，不能擅自说BULLA已经通过新P1。

各个历史日期非2×普通币重复WATCH数为：2025-01-09 6、2025-09-02 7、2026-01-26 33、2026-02-24 32、2026-03-28 37、2026-05-10 23。重复普通币在不同市场背景仍然常见，不能用“第二次报警”直接发布BUY或紧急邮件。

## 如何据此推进主线，而非针对BULLA调单币参数

1. 保留已经通过历史早报验证的原V4 D0全部时间和持久记录。**P1v0.1、P1v0.2正式弃用，不部署。** 新策略应在同一币的第一次WATCH之后维护独立研究观察状态，后续每次真正完成的原V4观察点都可因果重新评级，允许正常回撤/不同阶段活动，不在首次WATCH未达到8%或100万U时永久失去高优先机会。
2. **先做全市场二次观察时刻量价实测数据分析：** 31个2×提前复报与138个普通重复WATCH都需同样读取官方USD-M真1m的as-of成交额/涨幅、时间间隔、成交活跃度，源SHA核验。包含额外8个2×仅在到达2×之后才有第二次WATCH及两个窗口中没有早重复的情况，不能只采赢家。不能因为这次数据已经暴露就在相同窗口调完阈值并声称OOS。
3. 策略层设计把 RAW_D0 的完整发现**持续可查**与真正每天不超过5条、单日不超过12条紧急P1分离，冻结新规则后另选日期验证：不仅高概率2×，还需确保重大5×/10×样本不被过滤，不能以事后HIGH等于卖价。未验证真实历史盘口与价差/手续费、30USDT名义成交深度、交易所历史上市可交易资格前一律WATCH_ONLY。
4. 真正其他AI Review、回归/集成测试、Frank隔离、Mac实机运行和邮件送达均是之后不可跳过的独立门槛；现在只能继续研究，不能声称模型已可用或已有盈利。

当前：**STAGE47_FULL_MARKET_REPEATED_WATCH_FACT_AUDIT=PASS；STAGE45_P1V02=REJECTED；ORIGINAL_D0_UNCHANGED；NEW_SECOND_IGNITION_HYPOTHESIS=DESIGN_REQUIRED；INDEPENDENT_OOS=NOT_DONE；EXECUTABLE_PROFIT=UNVERIFIED；OTHER_AI_REVIEW=NOT_DONE；DEPLOYMENT=NO_GO；GMAIL=OFF；FRANK=UNCHANGED；AUTO_TRADE=NO_GO**。
