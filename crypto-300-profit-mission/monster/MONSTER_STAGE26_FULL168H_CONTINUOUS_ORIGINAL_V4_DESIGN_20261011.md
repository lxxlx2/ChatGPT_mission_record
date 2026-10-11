# Monster Stage26：758币×六日期，原V4连续168小时不重置状态的研发设计与源证据

研究日期：2026-10-11，归属原 Monster PR #30。状态：**原始数据全市场分片真实CI正在执行；本文件是已提交的冻结设计和执行规则，未宣称最终性能结论。**

## 一、为什么要做这一步

Stage24六个固定日期、2722个小时和分钟来源均完整的币日期里，有40个未来七日1h最高价触及2×，但原最初日历06–18 UTC固定12小时WATCH只提前发出7个。**39/40个事件首次2×在这12小时结束之后**，不能把33个直接当成全年无报警。Stage25事后按首次2×所在小时重新开一个12h原V4数据库，40个已知赢家中36个有事件附近提前WATCH；这是严重依赖后验时间的诊断，也不等于真正七天不重置监控的召回。因此Stage26不改变任何V4参数，只修复**回放时域、队列持续性和全市场分母**。

六个日期是**Stage24曾经查看过的**：2025-11-04、12-04、2026-02-04、04-04、08-04、09-04；既有40个未来2×及4个5×、1个10×结果也曾公开。本轮因此**不是新的未观察策略样本外检验**，只检验原V4是否在完整连续七天识别到这些机会。

## 二、严格预登记与数据方案

[Stage26永久冻结合同](evidence/monster_stage26_full168h_original_v4_continuous_758x6_prereg_20261011.json)，主提交 \`74a05bb2d58bfd52963bb3a91fa8e03b5c282b2f\`。原始Binance归档版、本机原V4功能、Stage24真正历史价格标签和代码的Git blob SHA都在运行前冻结。首次CI的预检发现**仅SHA身份名称**混淆，底层官方日度解析器正确 Git SHA为\`119d17f46b13f7ee70a1309f0689216e2388fd78\`，封装脚本Git SHA为\`1c5a6b7ee3132ac498d885c329f0422d63d01008\`，重新锁定，不改变任何源文件、价格、参数、日期或条件。随后首次轮询声明原文件写\`Stage24\`而测试预期写\`Stage24 baseline\`，改为原合同精确文本。前两次CI都在**读取新的10天分钟价格前的预检阶段**失败，失败证据保留，没有拿结果回填参数。

原始Stage24六个758币完整JSON通过原始ZIP和解压JSON SHA256验证。每币先判定其既有未来168h官方小时数据是否完整（未来价格**仅用于核对回放可评估性和之后标记**，不喂进V4），若月度1h来源缺失，则保留\`CENSORED_GT_NOT_COMPLETE_168H\`，不视作无WATCH或不会翻倍。对小时数据完整的币日期，主动独立下载从起始UTC 06:00前24小时到第168小时后24小时，共**216h连续分钟源**，实际涉及10个官方Spot日度1m ZIP及它们分别的发行方SHA256 CHECKSUM。下载、SHA、日期、分钟连续性有一项不合格，这个币整期判定\`CENSORED\`/SOURCE_FAILURE，不把多天未联网复盘编成成功历史扫描。

真实源码：[Stage26 168h完整扫描器](../local-agent/scripts/monster_v4_stage26_continuous168h.py)；[8项分钟源及无状态重置回归测试](../local-agent/tests/test_monster_v4_stage26_continuous168h.py)。

## 三、原始生产代码相同、研究模型不同于实盘的限制

每个有完整来源的币、每个固定日期单独创建**一份真实SQLite数据库**，过去24小时只有分钟预热，活动期从次日06:03 UTC开始以3分钟轮询，连续整168h保留snapshot、snapshot_history、watch_state、candidate_queue、events及outbox DRY_RUN 状态，调用**原生产**\`monster_v4_shadow.observe_snapshot\`与\`process_queue\`、官方minute rolling24h真实quote金额和已结束的5m Candle，没有提供后验标签。每币活动期**3360次**轮询（原Stage24的12h不足240次），所有原WATCH/SETUP/INVALIDATED事件UTC时间和原SQL队列状态都写入逐币研究证据。

这不是完全等同真实全市场单一数据库的回放：跨币共享的D1处理能力上限、交易所每分钟实时延迟、真实此时\`exchangeInfo\`上市权限、历史OrderBook L2档位和真实Gmail投递均无法被独立逐币的SQLite重演模拟。必须报告这些限制；若跨币真实排队积压，会影响真正WATCH和D1时效，故本实验的按币召回可能仍偏乐观。原本在零成交分钟使用该分钟收盘价作为模拟ticker的做法与Stage24保持一致，但它不证明当时有一笔可以买到的真实价格。

## 四、明确同时计算全部正常币和未来赢家

全部758币每日期都必须按确定排序分为6个shard，各126或127个；即使不具备60h/216h档案也保留可验证的负面状态。共六日期×6 shards=36个结果Artifact，**没有只按40个已知未来赢家运行**。

- 后验粗标签：固定日期06:00第一根1h open为基准，未来168h原始1h high最高价≥2×/5×/10×。
- 真正分钟越线：只用该币真实官方1m high查找首次≥固定基准×阈值的**第一个分钟**，核对与Stage24的1h标签必须一致，不一致则source integrity拒绝。
- 连续原V4时效：WATCH时间严格不晚于第一个真实1m越线时间才算\`EARLY_OR_SAME\`，否则标记\`LATE\`或\`NO_WATCH\`。除了原本首条WATCH，也记录**越线前最近一条WATCH距离越线6h/24h以内**的独立计数，避免把提前六天的警报误认为入场机会。
- 通知负担：总WATCH事件、涉及多少币日期、每小时预警高峰、SETUP/invalidated/队列事件，不把“七日没有2×”自动定义为没有可观利润/错误报警。
- 盈亏假设：沿用原V4每条WATCH延后3min以1m开盘价代理进入、24小时价格代理退出、每边10bps手续费、20bps与100bps滑点的对照；所有无成交、零流量、资金占用冲突和未能退出的情况单独删失。
- 资金限制：对时间先后发出的所有合格WATCH，以单个30USDT仓位及至多十个30USDT仓位（名义300USDT）分别模拟24小时持仓占用；无法证明历史L2成交或有足够资金连续复投，这仍是**固定30U头寸占用模型，不是账户真实流水或动态余额证明**。若总模拟负收益超过预算，则需另报告资金不足和不得视为真实续单的界限。

[36个原始ZIP/JSON SHA验证及全市场盈亏聚合程序](../local-agent/scripts/monster_v4_stage26_aggregate.py)与[独立资金排序等测试](../local-agent/tests/test_monster_v4_stage26_aggregate.py)已提交。真正36份原始产物需先获得GitHub CI success才可登记各自ID+SHA并再跑[二次验收CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/workflows/monster-v4-stage26-verify-36-original-zip-sha.yml)。

## 五、实际执行进度与下一放行边界

真实持续扫描CI：[Stage26全六日×758币原V4 168h GitHub Actions](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38136620497)。本轮只有**真实完成并验过输入及输出来能写DONE的节点才算完成**；GitHub任务\`queued\`、\`in_progress\`绝不算模型已验证、策略过线、外部独立Review或部署成功。

策略仍必须未来未用的完整全市场日期、买入成本、资金占用和稳定净收益均可验证后，才可以进入**真正另一AI独立Review→修复回归→Mac与Frank安全并行安装**。这次不修改原V4、Frank/邮件发送/自动交易/对话标题。当前\`MAC_MONSTER_DEPLOYMENT=NO_GO\`，\`OTHER_AI_REVIEW=NOT_DONE\`，\`REAL_GMAIL=OFF\`，\`AUTO_TRADING=NO_GO\`，\`FRANK=UNTOUCHED\`。
