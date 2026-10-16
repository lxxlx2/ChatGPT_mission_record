# Monster共有Spot高压日期445可用源子集：字典序前8币官方源真实首测

当前日期2026-10-16。研究仅在原PR #30 Draft分支，历史2026-02-04 06:00UTC起168h，非样本外、非PIT上市、非全445/758模型验收。上一步**独立Codex APPROVE@1154e97a25648dbf58c181be62076e4c1d406dde**已将原坏HIGH=0 K线误作D1 LATE的P2关闭；源修复审批不扩至新的研究包装器。

## 本轮事前约束与代码/CI固定性

在本轮写任何pilot源码之前，已Git提交[独立审查结果+445高压回放源与程序事前冻结合同](MONSTER_SHARED_SPOT_CODEX_APPROVE_1154E97_AND_445_HIGHPRESSURE_EXECUTION_FREEZE_20261016.md)。原36份双SHA历史Stage26抽出的758枚实名2026-10-16二次冻住，六日期来源complete`433/440/445/438/478/485`，2026-02共有`445` SOURCE_COMPLETE 和`313` SOURCE_MISSING/INCOMPLETE，完整758是分母而不是已扫描币数。

本轮**唯一源码+test+workflow固定SHA** `84a8d35e8f52c5c554886eeb926b2e66ec7a442d`。新程序[monster_v4_shared_spot_445_source_pilot.py](../local-agent/scripts/monster_v4_shared_spot_445_source_pilot.py)每次按`original_source_freeze()`核对758完整实名与2026-02完整来源445，选择**字典序前8**完整源成员，绝不从已知2026-02-06爆发98个WATCH筛币、按未来涨幅或Stage28真赢家排序。允许pilot`size<=16`但本次固定size=8，不可将demo标为SOURCE_COMPLETE_445_FULL。对每币经原Stage26`read_complete_216h()`实际下载 **10天官方Spot1m ZIP+同host CHECKSUM**、取得12960根闭合分钟、保存十个逐日期发行者SHA，立即用同份分钟行情跑原 Stage26 `scan_continuous`独立 per-symbol D0，再把同份source prep入SQLite，调用已CodeReview通过的共享`run_shared()`3360个3分钟Tick。**必须逐币比较所有WATCH UTC准确相等，否则整个本次研究RuntimeError**。只有受控官方下载入口显示source_origin_verified=true；人工注入假的source不升格官方。新4个测试在Ubuntu+macOS使用合成行情确认old-vs-new相同D0 WATCH时钟、选择不可变、无后验赢家名单和假的来源不能认证。

真实[GitHub Actions #38837915650](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38837915650)：**4/4 Jobs completed SUCCESS**，trigger SHA精确`84a8d35e8f52c5c554886eeb926b2e66ec7a442d`，Ubuntu/macOS各4/4新回归测试通过+py_compile，官方来源真实下载8×10=**80个日ZIP及CHECKSUM**；实际80份日SHA已写入机器证据。归档Job使用当次CI artifact并校验5个源码/测试/workflow Git blobs与原trigger SHA一致才归档，Git写后只机器数据追加无可执行改动。

原 [Git机器研究结果](evidence/monster_shared_spot_445_feb2026_first8_real_pilot.json)，Git blob `f8ce449eff6212978adb66cfc7d9e53d9bf9af0d`。

## 新事实：出现真实三币同时WATCH，高压场景开始从源码级转为事件级

`2026-02-06T00:36:00Z`，恰是原 Stage28 报告的**原98币WATCH同刻**，这8个字典序头部币中有 **3个在这同一刻由新真正共享D0自行生成WATCH**：

| 真实币种 | 本共享D0真实WATCH UTC | 同源原Stage26逐币D0 | 共享D1 |
|---|---|---|---|
| 1000SATSUSDT | 2026-02-06 00:36:00 | WATCH时钟一致 | EVALUATED |
| 1INCHUSDT | 2026-02-06 00:36:00 | WATCH时钟一致 | EVALUATED |
| 2ZUSDT | 2026-02-06 00:36:00 | WATCH时钟一致 | EVALUATED |
| 0GUSDT | 2026-02-07 02:27:00 | WATCH时钟一致 | EVALUATED；SETUP_ACTIVE随后于02:30 |

剩余4个原pilot成员`1000CATUSDT, 1000CHEEMSUSDT, 1MBABYDOGEUSDT, A2ZUSDT`在这一168h窗口没有WATCH。另`2ZUSDT`在2026-02-10 18:03UTC发生INVALIDATED（见机器events；不影响其之前已完成D1）。

机器归档汇总：`polls=3360`,`D0_watch_new=4`,`D1_selected=20`(累计每轮处理尝试，非20不同候选),`D1_completed=4`,`D1_deferred=16`(累计延期，不是16不同token),`D1_late=0`; `queue_final=EVALUATED 4`; `WATCH_EARLY=4,SETUP_ACTIVE=1,INVALIDATED=1`。两个引擎WATCH事件的每币UTC精确吻合；源没有使用已知WATCH时间“注入”。

**严格不得混淆**：此3币正好重现原98同刻信号，不代表原98在同一SQLite一次全扫已执行；当前仅有3个同时排队，原每3min`limit=8`尚未承受98同时候选，因此`0 LATE`不能推翻旧Stage28基于注入98 WATCH得到`91 LATE,7 EVALUATED`，更不代表445完整源队列拥塞已经验收。相反，此结果证明在一份共同SQLite真实D0生成信号后再由真实原D1评价这个边界的接线是有效的。

## 进度与下一提交

- **DONE**：历史2026-02-04原445资格445/758+313来源分母不变；字典序不按收益筛选前8；官方80日Spot1m ZIP+CHECKSUM同host核实和每日SHA留存；真实原D0 4个信号、原生产共享D1全部评价、3币确实在2026-02-06 00:36同刻；与同minute source旧Stage26 D0全部4个UTC吻合；4/4真实CI、跨平台4项pilot新测试 + 原SHA审过的22项共享核心在其原审核版本独立通过。
- **NOT_DONE**：其余437个`SOURCE_COMPLETE`原币未在本次共享跑；313缺源没有被虚构替代；旧Stage28真正同样445成员D1比较、高压98同时共用队列、大规模API/下载并发和缓存合并同源校验还没完成；无订单簿/PIT/OOS/净利润/真实通知/用户Mac验收。仍`G4 UNKNOWN, G6 NO_GO`。
- 下一高价值任务是将已有真实可运行先验`8`扩展成**严格原445 SOURCE_COMPLETE 子集完整同一SQLite共用时钟**，按冻结来源名单8份内并行下载并分批存只读缓存，一次全445同池验证00:36真实98币是否发生及D1实际LATE，并报告每币所有历史SHA和失败状态。采用触发SHA精确、GitHub一次性research workflow无schedule，严禁以模型收益优化选币。新pilot包装脚本+CI尚需另外AI review，不得自评APPROVE；本次Codex批准只属于之前已审共享core SHA。

NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE，Frank/Stage99不变，不自动交易/启用邮件/定时运行。
