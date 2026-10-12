# Monster Stage56：全166条候选官方as-of主动买入/成交笔数事实

日期：2026-10-12（Asia/Bangkok）
状态：真实数据复核 DONE；新策略 NOT_DESIGNED；独立其他AI Review NOT_DONE；Monster部署 NO_GO。

本阶段遵守同目录 MONSTER_MODULE_DEVELOPMENT_RULES.md 及上级 MISSION_SPEC.md，沿用 [原Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。
没有改变原V4 D0、冻结失败的P1v0.3、Frank、Gmail、Mac、自动化、生产部署或交易。

## 一、来源、范围、方法和实际验证

- [只读诊断脚本](../local-agent/scripts/monster_v4_stage56_usdm_asof_taker_and_tradecount_source_audit.py)，源码创建提交 c1b61ee91ffe549885b3fcbe35ddb8afd1f5373d。
- [Stage56 GitHub Actions](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38251427744)，完整执行 SUCCESS，包括真实官方数据重新获取、SHA校验、61根当时已闭合分钟核查、未来分钟毒化单测、与Stage55完全数值一致性、上传artifact与Git写回。workflow创建提交 6e4c7f50dc347688dc7dec41fd2a98d04c9624fd。
- 输入为此前已固定的Stage55全部166条候选，锁定旧候选CSV Git blob dca780246adb28e045ed77f0f96eb4bd034fb2e7，以及Stage52原166候选、5400行情案例、36份原SHA收据的Git blob。
- 仅从候选合格时间以前的61根官方Binance USD-M Futures 1m K线获取 quote asset volume、number of trades、taker buy quote asset volume，Binance发布者每日ZIP及CHECKSUM逐一SHA256验证。
- 用最新最后15m/60m历史计算主动买入quote占比、成交笔数、quote60及成交分钟覆盖率；旧ret60、quote15和相对放量必须与Stage55 Decimal逐值完全相同，任何偏离停止。
- 先形成as-of特征，再关联历史后见的固定窗口2×标签，仅做诊断，禁止未来信息进入实时优先级。

[逐条166官方分钟原始source SHA收据和新指标](evidence/monster_stage56_all166_61m_asof_taker_trades_official_SHA.jsonl)：Git blob 982bddbf05f263423f9cab4f40c0992688cc3499。
[事实汇总JSON](evidence/monster_stage56_all166_taker_trades_descriptive_summary.json)：Git blob 50879caf60f7a3795519d5508594e52835be501d。
两份证据由原CI提交：5ad7cf742b4ce46aa9a66234b0a097cb102a1b87。

字段来源说明：[Binance官方历史数据仓库](https://github.com/binance/binance-public-data)。已核实交易市场是USD-M Futures。**不能将USD-M合约历史成交额当作同时刻Spot现货真实可买深度。**

## 二、实际新结果

| 首次合格前真实已闭合历史指标 | 未来2×且提前至少5分钟 | 固定七日窗口未达2×普通候选 |
|---|---:|---:|
| 已核验官方历史资料 | 27/27 | 137/137 |
| 最近15m主动买入quote占比中位数 | 54.12% | 52.85% |
| 最近60m主动买入quote占比中位数 | 52.59% | 52.26% |
| 最近60m真实成交笔数中位数 | 118,805 | 81,185 |
| 最近60m USD-M quote成交额中位数 | 1,073万USDT | 1,055万USDT |

剩余另2条事后2×但候选到达已太晚，独立保留，未并入27条。共27+2+137=166。166条的最近60m均有真实USD-M历史成交笔数。这仍不能单独证明当时接受新的订单、具有Spot交易资格或者能按30USD买入。

描述性同组配对比例：已暴露27条提前2×候选随机取一条、137条普通候选随机取一条时，前者15m taker买单占比更高的经验比例 56.61%，60m taker买单占比 52.18%，60m交易笔数 57.72%，60m绝对quote成交额 50.28%。仅为这166条样本的后见标签组间秩比较，**不等同预测准确率/未来策略胜率**，不选择新阈值。

观察判断：短周期主动买单和成交笔数有一定数值差异，但样本组大量交叠，绝不足以证明可在每天5个名额内避免原来6个容量漏报。每条交易的未来2× HIGH不是可卖出的价钱，无法计算真实净利润。

## 三、事实边界和后续开发主线

已确认：166条候选决策之前存在61根可以逐分钟还原的真实USD-M行情，已有历史成交笔数，历史发布者checksum校验通过，与原Stage55的quote/ret60/放量值一致。

UNKNOWN/UNVERIFIED：当时exchangeInfo的接受订单状态；Spot同币挂牌、精确身份和股票/RWA/乘数命名合约分类；历史同时点盘口与买卖价差；30USD真实可成交价格、滑点、手续费后净回报；单币资本流入/流出链上证据。发布者事后存档不证明当时实时可以调用该ZIP，只证明历史事件时刻的已闭合bars与旧价量闭合。

下一阶段按既定开发顺序核实**全部候选历史交易身份和Spot交易资格**，优先官方交易所当时公告、历史Spot成交源及可验证时间点，不把缺证据的UNKNOWN擅自写成不上市或可买；随后研究有真实历史盘口的30USD成交深度，无法得到就保留UNVERIFIED。只有数据够且产品目标明确，才能提出可证伪的下一版策略、技术设计、冻结尚未使用的日期并回测。完成通过后才进独立其他AI Review、修复、最终测试、本地部署；原V4 D0仍保留。

状态：Stage56数据 PASS；P1v0.1/v0.2/v0.3 REJECTED；新URGENT排序 NOT_DESIGNED；其他AI Review NOT_DONE；Monster NO_GO；Frank UNCHANGED；Gmail OFF；Auto-trade NO_GO。
