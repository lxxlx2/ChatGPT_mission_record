# Monster Stage127：首次 D0 六特征时间前推模型真实519回放，REJECTED

日期：2026-10-14 Asia/Bangkok。仅原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，研发不触发新市场采集、后台任务、Frank、Gmail、实单、Mac 安装。

## A. 先方案再代码，再按原来源完整回放

- 先于任何 Stage127 新模型回放实际 Git 提交 [冻结模型方案](MONSTER_STAGE127_FROZEN_FIRST_D0_CHRONOLOGICAL_PRIORITY_MODEL_PROTOCOL_20261014.md)，commit `d62030573574b162d9bf5d1f21022a9b6647a030`。预冻结单套模型/六个首次 D0 过去61m as-of 特征、chronological anchor 日期、最少6个旧训练正例、固定 400 轮全批次 LR=.2 L2=.05 正则 logistic、只按以前训练日期负载校准阈值、不做逐日 top-N 硬截断。
- 代码 `../local-agent/scripts/monster_v4_stage127_first_d0_chronological_priority.py` 与测试 `../local-agent/scripts/test_monster_v4_stage127_first_d0_chronological_priority.py`，不使用外部统计模型依赖，禁止偷取 Stage83 未来标签进特征；所有 519 原 D0 保留，输出优先级只用于**研究**。
- 原源两份 519 完整真实 Binance 官方分钟发布者 SHA 校验历史资料。CI 再用 `git hash-object` 确认 Git blobs：
  - Stage64 `monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl` = `8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a`；
  - Stage83 `monster_stage83_all519_source_and_D1_result.jsonl` = `c76b3a137c8dbe56feed3a79a63adcc0752f5e2e`。
- 本轮只采用历史 519 条 **已经 WATCH** 的 D0，对其子群体评价「首次 D0 早于锚点后 2× HIGH≥5分钟」的 28 个历史正例，包含全部不涨的负样本及所有六个原七日锚点；**缺少没进入 D0 的全市场正例分母，因此绝不能叫全市场 G1 验证**。
- 源回放/测试 [CI #38556832716](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38556832716) 在代码 SHA `8c021fc0b8285939c6722caa0c70fe8639d5d760` 实际跑通 Ubuntu job `115827963724` 及 macOS job `115827964100`；两 OS stdout 输出解析后全部研究字段逐项对比 **数值与结构一致**。CI 把全部 519 条真实模型决定、对应锚点的纯 JSONL 与摘要作为两 OS 各一份 artifact；永久摘要已回写 [Stage127 机器结果](evidence/monster_stage127_original519_first_D0_walkforward_historical_summary.json)。CI PASS = 代码复现成功，**不代表模型过关**。

## B. 真实结果和冻结门槛

| 原七日锚点 | 原首次 D0 | 该段首次 D0 已提前≥5m的历史2× | 已有此前足量训练数据？ | Stage127 优先关注 | 其中原重要早报保留 | 优先关注当日峰值 |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| 2025-01-30 | 161 | 0 | 否 | 0 | 0（无法评分） | 0 |
| 2025-06-02 | 34 | 0 | 否 | 0 | 0（无法评分） | 0 |
| 2025-08-01 | 54 | 6 | 否 | 0 | 0（**冷启动未覆盖6例**） | 0 |
| 2025-10-02 | 75 | 13 | 是 | 69 | 12 | 18 |
| 2026-06-21 | 100 | 2 | 是 | 39 | 1 | 13 |
| 2026-07-28 | 95 | 7 | 是 | 36 | 3 | 10 |
| 合计 | 519 | 28 | 仅后3窗 | **144** | **16（可评分22中的16）** | **18** |

逐项结论：
- 首次有可评分模型的三个后续窗口中，原始早5分钟 2× **22** 例，最终入选 **16/22=72.727%**，低于预冻结最低 **80%**；其中 **6** 个重要机会被筛掉。另有早期训练不足窗口中的 **6** 个无法由模型处理的早报案例，单独报告，不能让分母消失。
- 有模型的三个七日窗口共 **21个UTC06日桶**，共升级 **144** 条，**6.857/日**，高于既定 <=5/日；实际单日峰值 **18**，高于 <=12。历史训练校准尽管保证旧训练负载不超标，在更晚日期真实负载和召回同时失败，不能据此重调阈值。
- Stage127 实际机器 verdict **`REJECTED_EXPOSED_HISTORICAL`**。无论 source/CI 是否成功，模型都不能当作 MONSTER 新策略部署、交易、实盘 WATCH 升级模型。Stage118 原失败 18/28 同样保持 `REJECTED`，不另找未来赢家优化。
- 模型属于过去曝光的 2025–2026 六个原研究日期上严格时间顺序的 *historical chronological walk-forward*；尽管训练不能读取该折未来标签，这些日期在 Monster 研究中已被多次使用，**不构成新 OOS**，更不是因果全市场实盘收益。

## C. 主线研发决策

已验证数据说明：只靠首次 D0 过去一小时的六项特征，用一个跨日期历史训练分类器，无法同时保留足够极端早报和控制新的关注数量；在无先例正样本时还会有冷启动缺口。不可继续在原 519 上微调正则、阈值、日期和赢家。**保留原始全量 D0 WATCH**，所有未过筛的币继续留观察池，不再将 Stage127 priority 当行动信号。

下一真正高价值依赖是 **全市场新独立完整时间段首次 D0 与 D1 真实召回**，以及伴随 D0 时刻真实可交易 Spot / USD-M 身份、合约单位、可验证订单簿深度/费用和后续退出证据。仅当真实新时间段自带无 WATCH 币也完整的全市场分母，才能评分 Stage77 G0-G4。Stage123/126 当前时点快照和两个手动相隔两周的市场快照不能还原首次分钟内的2×、D0时刻价、实际执行净收益。

当前源/执行权限依旧：Stage99 三个自动定时 Mac 任务已根据用户截图停止（本地时点 readback），后续 Stage124 全量新市场采集须用户聊天**明确发起**，不自动安排；真实交易与邮箱不批准，Frank 完全不变；真正独立其他 AI review、完整 OOS 和用户授权 Mac 部署均未达到。

`STAGE127_FROZEN_AND_REAL519_CODE=DONE`; `STAGE127_TWO_OS_REAL519_CI=PASS`; `STAGE127_HISTORICAL_MODEL=REJECTED`; `STAGE127_ALL_ROWS=ARCHIVED_CI_30DAY_ARTIFACT_AND_SOURCE_REPLAYABLE`; `G0=PARTIAL`; `G1_FULLMARKET=NOT_SCORABLE`; `G2=REJECTED_EXPOSED_DIAGNOSTIC`; `G3=REJECTED_EXPOSED_DIAGNOSTIC`; `G4=UNKNOWN`; `NEW_OOS=NOT_DONE`; `INDEPENDENT_OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOYMENT=NO_GO`; `GMAIL=OFF`; `FRANK=UNCHANGED`.
