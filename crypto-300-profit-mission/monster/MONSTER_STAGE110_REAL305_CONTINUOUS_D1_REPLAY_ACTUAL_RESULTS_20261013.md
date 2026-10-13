# Monster Stage110：原519 D0 / 305 D1 官方1m连续确认模型——完整历史实验与正式拒绝

日期：2026-10-13 Asia/Bangkok，原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。本轮回到用户要求的**旧历史数据建模—回测—按结果修正策略**主线，既有 Stage99 Mac来源快照保持隔离，不干扰此实验。

## 执行证据 / 不可掩盖的原始失败

1. 事先冻结[唯一 Stage110 持续确认/失效策略](MONSTER_STAGE110_D1_CONTINUOUS_CONFIRM_INVALIDATE_HISTORIC_PROTOCOL_20261013.md)，然后开发[同一因果确认主程序](../local-agent/scripts/monster_v4_stage110_d1_continuous_confirm.py)、[全519/305聚合与G2/G3/毛价闸门](../local-agent/scripts/monster_v4_stage110_aggregate_confirmed_priority.py)、[GitHub两系统测试＋官方24分片](../../.github/workflows/monster-stage110-d1-post-setup-continuous-1m.yml)。
2. 最初 [CI #38415636244](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38415636244) **FAIL（保留）**：Stage85 原来源的 D1 在 t 评估时只可见 t-1m 最后已闭合1m，首版错误地用 t 当分钟收盘价做SHA重读对账；第一批全部严格拒绝。查原 Stage85 的 at(data,t) 使用 bars[i-61:i] 后，修复为按 t-1m 官方K线校验，UTC零点特例按旧Stage85 SHA核对前一日；**没有修改策略阈值或历史赢家标签**。
3. 修复后的最终[Stage110官方历史1m CI #38416113241](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38416113241) **27/27 jobs SUCCESS**：macOS/Ubuntu因果自测两项＋六日期×四shard实读Binance官方日1m发布者SHA全部24项＋全519/305聚合并成功Git提交一项；CI head为 `257c2033d750bd0f03e79febc42f4749a82d7df4`。原 Stage101 全305发布者日ZIP SHA逐币复核无删失，原 Stage83/85/88 Git blob 时间及价格对账完成。
4. 所有可复算逐币、每日及重大遗漏证据保存在[官方完整机器JSON](evidence/monster_stage110_real519D0_305D1_causal_confirm_states.json)，Git blob `314c0ee532b93dd24dbda4ec6a146e03ee2c5c1b`。不是合成收益，也未使用任何交易账户实盘执行。

## 预注册策略与真实状态

D0始终519、原Stage79 D1始终305（DIRECT164/REIGNITION141），其余214个D0仍在可检索WATCH；新策略只在原D1后观察**真实30个已收盘1m**，分别以首次直接连续两组3m价格/quote或重新点火一组3m价格/quote做确认、跌8%否定；新确认后下一分钟真实1m open才作为价格代理入场，不用旧D1的假入场价计算收益。

| 新状态 | 数量 | 含义 |
|---|---:|---|
| `PRIORITY_CONFIRMED` | **106** | 连续确认后的高关注研究候选 |
| `EXPIRED_NO_CONTINUOUS_CONFIRM` | **172** | 30m未出现预注册持续确认；仍保留D1_SETUP |
| `INVALIDATED_EARLY_8PCT` | **27** | 已完成分钟收盘价触发原D1下跌8%失效 |
| 原D0没有任何D1升级 | **214** | 不删除、不冒充本策略没见到 |

原164条DIRECT中51条确认；原141条REIGNITION中55条确认，延迟完成的确认时点严格计入早报评价，而不是拿旧D1原时间替代。

## 已冻结历史G2/G3及价格结果，三项全部未过

| 同一历史GATE | 原D1 Stage79 | Stage110真实连续确认 | 原冻结要求 / 本版判定 |
|---|---:|---:|---|
| 对原D0提前5m的28次历史2×，D1或PRIORITY在2×前至少5m | 原 **27/28** | **16/28 =57.14%** | ≥80%；**FAIL** |
| 42个完整UTC06日平均关注候选 | 原 **7.26/day** | **2.52/day** | ≤5/day；通过单项 |
| 单日峰值 | 原 **52/day** | **16/day** | ≤12/day；**FAIL** |
| 确认后下一分钟open→满24h末close价代理毛中位 | 原D1后24h **-2.80%** | **-3.65%** | >0；**FAIL** |
| 真实双向成交价格／盘口／名义金额净收益 | UNKNOWN | **UNKNOWN** | 不得叫可交易策略 |

新106个经真正延迟入场的历史价格代理 **46盈利、60非正收益**，≥+100%有3条、≤-20%有11条。人工统一每边20bps及100bps费用敏感性中位分别约 **-4.03%**、**-5.56%**；不是交易所真费率、盘口真实成交或组合收益。DIRECT确认51个毛中位 **-4.73%**；REIGNITION确认55个毛中位 **-2.99%**。与此前被拒绝的Stage100、108、109相比，新方案尽管关注日均明显下降，仍**没有提高入场收益，且牺牲大量重要右尾**。

## 真正的失败归因（优先指导下一研究，而非再调阈值）

1. 27个原D1已提前5m的2×历史机会里，**11个被30分钟确认模型排除**（可在机器JSON逐币重算），包括 MYXUSDT、AIAUSDT、A2ZUSDT、BROCCOLIF3BUSDT、DOODUSDT、GIGGLE以外的其它重要个案。特别是 **MYX** 的旧5×与10×、**AIA** 的旧5×在本方案都因30m未确认而消失；COAI 5×/10×仍能提前确认。因此“未在首次30分钟内连续确认”不能简单等价于未来毫无机会。
2. 最拥挤的2025-01-30七日窗旧52 D1同桶，Stage110降至**单日16个**，且那一天没有原冻结7日2×事件，说明还存在广泛的行情共振噪声；不能因为事后该天无2×就对该日期专门新增一个过滤阈值。
3. 新确认信号中24h获利仍不到半数、毛中位反而比旧版更负，说明**把量价延续当作“合适买入价”并不成立**：确认可能只是买在涨势短期局部高位。仅针对旧历史0.92、1.01、1.02、1.20等数值循环调参，属于事后过拟合。
4. 事实上仍只有官方USD-M合约混合历史人群，无法将混合交易所身份当成 Crypto-only 全市场事实；没有盘口深度、滑点、成交金额时 `REAL_NET_PNL=UNKNOWN`，不能把3条价格右尾当真利润。

## 正式结论和下一主线（不延误）

本版 `STAGE110_STRATEGY=REJECTED_STAGE110_PRE_REGISTERED_HISTORICAL_GATES`，不部署、不改原D0/D1、不发真实Gmail、不下单，已安装Stage99三次快照采集器和Frank完全不动。无需等2026-10/11月未来采集完成才做旧历史研究。

**下一主线转向重大机会的“较长、可恢复WATCH观察周期”和“不同时间尺度的第二次入场时机”经济逻辑**，而不是复跑另一套同30m确认阈值：
- 用同一原519 D0和305 D1全量案例，按时间和路径标记从首次D0到原D1/首次2×之间的实际可观察分钟价格状态，明确重大2×为何常在连续30m确认后仍数小时/数天才触发；
- 原D0观察池及全部历史D1 SETUP长期可检索，候选无需在30分钟后“永久失联”，但不能直接延长到无限生命周期而产生海量旧提醒；需要有真实再触发、失效和提醒冷却/合并规则；
- 下一个独立候选必须**先冻结唯一时序策略和新的延迟入场/风险评价合同，使用原发布者SHA全量回放**；不直接参考旧赢家参数挑阈值。旧日回测只做研究，后续新时段独立确认才能通过OOS；
- D2真实可成交研究仍受限于历史盘口及用户未指定名义金额，只能单列`EXECUTION_UNKNOWN`。历史方案失败时不去忙新监控工具，也不借Stage99采集审查APPROVE审批Monster交易模型。

正式状态：`STAGE110_CI=PASS_FULL_OFFICIAL_27_JOBS`；`STAGE110_CORE_STRATEGY=REJECTED`；`G2=16/28_FAIL`；`G3_AVG=2.52_PASS_PEAK=16_FAIL`；`G4_PRICE_ONLY_MEDIAN=-3.65_FAIL`；`G4_NET=UNKNOWN`；`OOS=NOT_DONE`；`NEW_MODEL_OTHER_AI_REVIEW=NOT_DONE`；`MONSTER_DEPLOYMENT=NO_GO`；`FRANK=UNCHANGED`；`STAGE99_LOCAL_SNAPSHOT=UNCHANGED`。
