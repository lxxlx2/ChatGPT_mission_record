# Monster主线：原120个真正D1 SETUP之后的实际历史分钟收益与删失（2026-10-19）

## 一、结果先行——SETUP不是可买正收益信号

这次不是再修公平性或来源准入，而是直接从Stage162原共享SQLite研究输出中**原始120条SETUP_ACTIVE**、56个不同币种的真实信号时钟入手，重新读取被独立Codex审核过的 **28个原February 2026 publisher/source ZIP**、完整 `2026-02-04` 开始9天分钟价量数据，把已发生的SETUP逐条按**预冻结的进/退时钟**计算，不看未来赢家决定入场。

主要口径：SETUP后+3分钟下一根1m `OPEN`价格代理入场、24h固定`OPEN`代理退出；每边假定手续费**10bps**、每边假定滑点**20bps**，100bps滑点是压力情景；入场和退出真实盘口从未归档，**不是历史实际成交或账户净利润**。在同币24h研究资金占用约束下：

| 原始120条真实SETUP | 数量 |
|---|---:|
| 原D1 SETUP事件 | **120** |
| 事件中不同币种 | 56 |
| 同币24h研究资金占用重叠，跳过 | 33 |
| 退出/入场源条件无法充分定价，保留删失 | 30 |
| 最终有合法历史分钟价代理的事件 | **57** |
| 合法代理里的盈利 / 亏损 | **18 / 39** |
| **合法代理样本胜率** | **31.58%** |
| **24h净价代理中位收益率** | **−8.490361%** |
| 24h简单均值 | −2.695088% |
| 每边100bps压力滑点中位 | −9.942924% |
| 每笔互不约束、假设独立历史30 USDT投入累计 | **−46.085998 USDT** |

**这组中位数为负且39/57亏损**，表明现有原D1升级本身没有证明“值得真实买入”，与Stage30 WATCH价代理和Stage152不同D1研究的负面方向一致；三个不同日期/样本/价代理口径不能合并推一份市场胜率、也不得把上表18笔历史价格赢单当可成交实际盈利。

30条Source删失具体拆分并保持原源状态：**15**条退出及前5分钟零成交，**6**条退出分钟无成交，**8**条入场或退出分钟成交额不足30 USDT，**1**条入场无成交；33条有原同币研究24h资金占用，不假设同时能重复买入。**未来退出量能在初次SETUP时不可见**，上述删失是事后评价完整度，不能反过来当成当时就能筛币的条件。

## 二、三个额外固定期限的经济代理（不是挑最优的未来退出时间）

| SETUP后+3m统一入场，随后固定持有 | 本期限可评价 | 赢/亏 | 20bps每边净中位 | 100bps每边净中位 | 每笔独立历史30U累计价代理 |
|---|---:|---:|---:|---:|---:|
| 15分钟 | 83 | 26 / 57 | −1.808674% | −3.367298% | −36.873746U |
| 60分钟 | 80 | 23 / 57 | −3.506801% | −5.038469% | −56.962290U |
| 360分钟 | 59 | 17 / 42 | −5.227021% | −6.731383% | −54.229197U |
| **1440分钟（主24h）** | **57** | **18 / 39** | **−8.490361%** | **−9.942924%** | **−46.085998U** |

各行有不同的合法源分母，**不能仅看这些不同分母中位数字便断言每个币必然越拿越亏**。为排除这类错觉，进一步纯描述性核查：同时在15/60/360/1440分钟四期限均合法评价的**46条完全相同的事件**，其四时点各自净收益率的中位数约为 **−0.913298% / −2.544112% / −4.864695% / −8.111379%**。这只是这46条已经曝光价格路径的结果，不是未来收益趋势预测或选持仓窗口的许可。

## 三、为什么偶有暴涨币也不能解决策略盈利

57个24h合法代理中有40个不同币种。最大历史赢家集中于少数已经曝光的个别SETUP：NKNUSDT约+177.18%、GHSTUSDT约+87.25%、DFUSDT约+37.33%、ZKPUSDT约+28.59%、DATAUSDT其中一次约+26.02%。事后前5笔合计**+356.36个百分点**，但全部57笔的收益率直接总和为**−153.62个百分点**，其余52笔总和约**−509.98个百分点**。这里所有排名只能解释为什么简单均值不如中位数悲观；这些赢家是看了未来收益后才排出的，**不能充当实时选币规则**。

逐UTC日原SETUP及24h有效/赢数分别为：

| 真实历史UTC日 | SETUP | 合法24h价代理 | 历史盈利 |
|---|---:|---:|---:|
| 2026-02-04 | 7 | 6 | 0 |
| 2026-02-05 | 8 | 5 | 3 |
| 2026-02-06 | 18 | 8 | 3 |
| 2026-02-07 | 30 | 9 | 3 |
| 2026-02-08 | 15 | 9 | 0 |
| 2026-02-09 | 11 | 7 | 4 |
| 2026-02-10 | 26 | 11 | 5 |
| 2026-02-11 | 5 | 2 | 0 |

这些日历不是8个独立前瞻实验，且为已暴露历史样本。

## 四、直接可复现的机器来源、源码、CI

1. **原事件**：Stage162原A/B完整JSON GitHub [Actions #39068290868](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39068290868) Artifact `12113719899`，内部SHA256 **`c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2`**，原269 WATCH与120 SETUP事件ID全部从`raw_alternative_events`读取，精确56个symbol，源前后120 SETUP不变。
2. **原历史行情**：原2026年2月445已归档、28份原始分钟ZIP+28个publisher source-proof，源代码复用`monster_v4_shared_445_archive_replay_runner.collect`与`verified_shard_paths/read_archive`，核对28 ZIP SHA、manifest、原445人口、56币原真实逐分钟12960条时钟与来源；不取现在市价、不调指标阈值、不预先查看获利币。完整原758缺313币在本轮无法代表真实市场完整回测，亦不能从10月现时交易状态推断旧时PIT上市。
3. **先于具体经济结果冻结**：[原120 SETUP经济研究入退场与删失合同](MONSTER_ORIGINAL120_SETUP_POST_SIGNAL_ECONOMICS_FROZEN_20261019.md)，预冻结commit `344adebe0c25cb5ccc55f54bc4800753fbbd4148`；源码`local-agent/scripts/monster_v4_original120_setup_price_economics.py`与离线11项测试、GitHub单次push-only workflow`.github/workflows/monster-v4-original120-setup-real-price-economics-once.yml`，**实际有执行代码固定版本SHA `a91be24924821b3f6afa5200a3c9688d63a28896`**。
4. **真正CI与原结果**：[Actions #39154148283](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39154148283) **SUCCESS，11/11步骤完成，11/11单测通过**，原28历史ZIP读取校验、原SHA绑定、原120确切SETUP重算；当次衍生 Artifact `12146216682`。Git已归档[真实全120个逐事件四期限结果与原ZIP各自SHA](evidence/monster_original120_setup_exposed_minute_price_economics_v1.json)，Git Blob **`3ea9391ef34b474db1df9a0e5a8ad810fc3a0cb9`**。输出含所有本源实际source censored原因及初始时间，结果没有假装已拿到历史L2或验证获利。
5. 初次[CI #39154109140](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39154109140) FAIL：`result_for_events`和`summarize`把内部test小样本强制写死为120，导致4个测试在非真实120的人造场景抛源数异常。实际修复`len(rows)==len(events)`后保持`load_immutable_setups`真实源120及严格SHA守卫不变；真实第二轮全11测试通过，失败历史不抹去。没有为追数据正回报改变进场、退出、费用或D1规则。

## 五、决策：不能把这些SETUP叫买点，更不能卡在更多数据源边界循环

本轮回答了核心经济主线：**SETUP之后合法历史价格代理仍亏损居多，延迟3m追涨+固定退出不具备已验证盈利性**。公平8调度已确认新增27有效首评也没新SETUP，现有D1本身主要仍是观察过滤而非正收益交易门槛；“多做审核或多显示指标”不会自动改善这个结果。

应继续的高价值工作是：
- 首先检查有无**前瞻、全市场PIT真实数据**能证明新的SETUP与实际可执行净利润；已冻结的511 Spot七日窗口`[2026-10-17T22:06Z,2026-10-24T22:06Z)`仍未满，并且2026-10-16—24日4599个Publisher ZIP不能现在假装已出版齐全。
- 真正未来市场里验证早报召回与可实现收益前，不重新挑历史赢家、乱调D1成交额门槛、不把过去90%涨幅触达冒充真实买单收益；下单金额与fee tier未由用户指定，保持`UNKNOWN`。
- 价值观测上应该清晰报告`SETUP→价代理合法性→净负中位→实盘盘口未知`，而不是只展示120个SETUP或Code Review APPROVE当进度。

**本轮新代码其它AI独立review仍`NOT_DONE`**，源与CI是作者自验，并不代替固定代码审查；以前Stage165/166的APPROVE不跨版本适用。但利润方向并非从现有Stage30反推，此次确实直接得到原120 SETUP的独立样本数据。部署/真实监控/自动通知/交易仍`G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。

## 六、独立外部定向审核任务（固定新经济代码，不重审已有边界）

> 请独立审核 Mission Monster Draft PR #30 分支 `research/monster-v4-local-discovery-20261010` 新增的**实际原120 SETUP后收益统计代码和source结果**。唯一固定审核源码SHA `a91be24924821b3f6afa5200a3c9688d63a28896`，对比研究冻结 SHA `344adebe0c25cb5ccc55f54bc4800753fbbd4148`；使用固定SHA detached checkout，不以PR HEAD替代。新增`crypto-300-profit-mission/local-agent/scripts/monster_v4_original120_setup_price_economics.py`、`tests/test_monster_v4_original120_setup_price_economics.py`、`.github/workflows/monster-v4-original120-setup-real-price-economics-once.yml`。原Stage162 full JSON SHA256 `c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2`、原28 source ZIP及proof SHA，独立取真实源，验证原始120 SETUP unique事件IDs、56 symbols、原269 WATCH、来源全部仅445/758与313删失。独立重放每个SETUP `observed_ms + 3m`下一1m OPEN为入场，预先固定15m、60m、360m、1440m退出对应1m OPEN、每边10bps手续费和20/100bps滑点、同币24h占用、入退出分钟30USDT最小quote和零交易邻近退出删失。不要把原一分钟OPEN当历史可执行bid/ask，不能拿退出时量能当事前筛币条件。核验全120每一行、24h**57合法价格代理、18胜39负、中位净收益约−8.49036%、重叠33、来源删失30、独立每笔历史30U代理合计−46.085998U**，其它三个持仓期数据及源原因；逐币反例测试零成交、退出缺失、资金占用、未闭合时间，不得依赖作者已写摘要直接APPROVE。检查真实[成功CI #39154148283](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39154148283)触发SHA、11/11测试及原28 ZIP真实取回与Artifact，旧[失败CI #39154109140](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39154109140)仅小合成测试按120硬编码导致fail的真实原因。输出`APPROVE/REQUEST_CHANGES/BLOCKED`、审查者/底层精确版本或UNVERIFIED、固定SHA、P0/P1/P2与源码行号、未证实之处，特别评估统计“逐币相关性、净资金回撤、均值尾部极端占比、价格代理不能交易”是否充分。Stage165/166既有固定代码已批准不重审。原门禁`G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`继续，非盈利策略推荐。
