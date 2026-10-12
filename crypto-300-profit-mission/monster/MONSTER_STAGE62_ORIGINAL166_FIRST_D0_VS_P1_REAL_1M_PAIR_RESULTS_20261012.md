# Monster Stage62：166个已经达到P1条件的候选，首次D0与P1双信号真实24h价格对照

日期：2026-10-12 Asia/Bangkok。仅Monster模块原 Draft PR #30。冻结合同 [Stage62 pre-reg](MONSTER_STAGE62_ORIGINAL166_FIRST_D0_VS_FIRST_P1_PAIRED_REAL_SHA_PREREG_20261012.md)，不得把本研究当作未使用验证集，历史P1 v0.3仍REJECTED。

## 实际执行、原始资料、完整验收

- [Stage62代码](../local-agent/scripts/monster_v4_stage62_all166_first_watch_vs_p1_paired_official_1m.py)，首次提交 6824d68af29f4ca7bdad93c39dc9183c059ab16a；严格复用锁定的[Stage60价格路径核心](../local-agent/scripts/monster_v4_stage60_exposed_all166_post_signal_futures_price_paths.py) git blob 6a638e84cf837ffc84a301649612e8f2f5dc1deb。
- 预先锁定输入：Stage61精确重建首次D0 WATCH UTC与延时Git blob 89634d4b8d049ad607be1f553515d11ff6e82573，Stage60 P1之后24h真实USD-M官方K线与发布者SHA Git blob c76b9b73c11924cb3fdc36fb852074ff9b49b3b8。
- [GitHub Actions Stage62 #38258952734](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38258952734) **SUCCESS**：166/166根本币日首次D0后续24h全真实官方一分钟SHA资料重新获取成功。针对46条第一次D0就达到P1的币，双方第一根代理close及全部四个期限结果**逐值完全一致**，独立源与模型一致性硬测试通过。所有166源时间、价格、结局均保存。
- [机器原始166逐币D0/P1配对结果、逐日官方SHA收据](evidence/monster_stage62_all166_first_D0_vs_P1_official_24h_pair_source_SHA.jsonl)，Git blob 962b1ae289aa0af3f612499e169a686fc63645a1；[统计汇总及分组](evidence/monster_stage62_all166_D0_vs_P1_paired_price_path_summary.json)，Git blob 36dd0c48e5c0c0784c7de72732e7d3475a785a77。

## 完整同方法计算的历史结果

以下均为各自真实信号之后第一根完整1m K线收盘价的USD-M **价格代理**，四期限使用同一算法。D0和P1间隔可能很长，所谓两组“24小时”属于**不同时间段**，不能推导买卖套利收益或价格改进因果。

| 对所有166条曾达到P1条件的历史候选 | 首次D0 WATCH | 首次P1达标 |
|---|---:|---:|
| 15分钟终点close中位价格收益代理 | +0.07% | 0.00% |
| 1小时终点close中位价格收益代理 | +1.28% | -1.21% |
| 6小时终点close中位价格收益代理 | +2.39% | -2.95% |
| 24小时终点close中位价格收益代理 | **+8.20%** | **-5.58%** |
| 24小时终点收盘价高于自身信号首分钟代理价 | **109/166** | **62/166** |
| 24小时最高HIGH相对于自身信号首分钟代理价曾再次≥2×（非卖出） | **9** | **5** |
| 24小时最低LOW相对于自身信号首分钟代理价跌幅中位数（非实际最大回撤） | **-7.72%** | **-13.90%** |

对120条后续才二次点火的币，首次D0之后24h终点close涨幅中位数**+12.90%**，首次P1之后24h为**-6.69%**；其首次P1完成分钟close相对首次D0完成分钟close的中位涨幅为**+20.30%**。这组的D0信号先于P1中位808.5分钟。46条两信号同时发生的对照价格与每项结果完全一致。

被原全市场日限额排除的39条候选，在首次D0之后24h终点涨幅中位数**+19.24%**，但首次P1之后24h为**-6.69%**。这些币同样早已产生原D0 WATCH，后续才达到P1条件；不可以因为P1被挤掉就认定原WATCH也没有及时发现。

## 实际业务结论与样本边界

这一对照支持将**早期D0 WATCH时效**列为研发主线，严禁通过晚期P1升级替代早期发现。观察到的“P1之后价格下跌”与等待时间有相关性，但未排除市场状态、币种差异、候选被筛选、价差和衍生品执行等混杂；绝不升级为“用户D0买入就会盈利”或“设置等待时长上限即可改善收益”的事实。

**最大样本偏差：** 这里的166个币，是后来确实达到了P1条件的完整**P1子集**，并非原V4完整D0全市场WATCH。原Stage52有效市场共有更大数量的D0 WATCH（六批日期合计519币日期）。剩余未达到P1的历史D0也可能是普通噪声或亏损。要确定原D0真正早报质量，下一阶段必须扩展至六个全市场日期的**全部519个D0 WATCH**（含353个未达P1），并用相同1m官方SHA价代理检查；既有166个D0结果应严格重叠对账。

Stage62状态：REAL_1M_SOURCE_SHA_AND_SAME_CORE_166_PASS；ALL_D0_UNIVERSE=NOT_YET_TESTED；NEW_STRATEGY/THRESHOLD=NOT_DESIGNED；OTHER_AI_REVIEW=NOT_DONE；MONSTER/TRADE/GMAIL=NO_GO。单笔交易金额未指定，绝不以固定金额推算损益。不修改其他模块。
