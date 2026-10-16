# 独立Codex/Claude固定SHA复审：Monster 445 source-complete前8字典序真实共享Spot D0→D1

审查唯一源码/测试/CI固定SHA：**`84a8d35e8f52c5c554886eeb926b2e66ec7a442d`**。请 detached checkout此SHA审，不把后来归档机器文件和文档PR HEAD视为代码审核版本。仓库 https://github.com/lxxlx2/ChatGPT_mission_record ，原PR Draft https://github.com/lxxlx2/ChatGPT_mission_record/pull/30。

上一固定原共享核心`1154e97a25648dbf58c181be62076e4c1d406dde`已经由用户提供**独立Codex APPROVE**：HIGH=`"0"`时间正常的坏5m源不再让原D1重试错误制造虚假的LATE。这个先前审核只批准原核心P2，不自动批准本次真实pilot源选择/官方数据。

先读取Monster AGENTS、开发规范、长期节奏、[本阶段在代码提交前先冻结的审查记录和445资格合同](MONSTER_SHARED_SPOT_CODEX_APPROVE_1154E97_AND_445_HIGHPRESSURE_EXECUTION_FREEZE_20261016.md)，还有真实[业务发现报告](MONSTER_SHARED_SPOT_445_SOURCE_COMPLETE_FIRST8_REAL_80_OFFICIAL_DAILY_20261016.md)。

请独立核查：
- **真实原758历史分母**：固定Stage26原36 Artifact双SHA派生`758`名单，2026-02-04源码完整`445`、原缺源`313`，本次只是445个完整币字典序头部8个，不按旧Stage26 98 WATCH、历史盈利或未来成交筛选，未声称445或758全量成功。实际名单`0GUSDT,1000CATUSDT,1000CHEEMSUSDT,1000SATSUSDT,1INCHUSDT,1MBABYDOGEUSDT,2ZUSDT,A2ZUSDT`。
- **新可执行源码**`crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_spot_445_source_pilot.py`；新tests`test_monster_v4_shared_spot_445_source_pilot.py`，对应.github工作流`.github/workflows/monster-v4-445-source-complete-real-shared-pilot.yml`。源码必须依旧调用SHA固定之前已获批准的`monster_v4_shared_spot_d0_d1_original_core.py`，原`monster_v4_shadow.py`不变；每个币`old.read_complete_216h`真实同host官方Spot1m ZIP/CHECKSUM 10天12960分钟、同源旧Stage26每币单库`scan_continuous` 168h+全8共同一个SQLite的3360 tick`run_shared`，每币所有WATCH UTC必须完全一致否则fail-closed。人工依赖注入不能伪装`source_origin_verified=true`，输出命名明确8/445历史已曝光。
- **真实 [GitHub CI #38837915650](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38837915650)**：触发唯一SHA精确，4/4 jobs success；Ubuntu/macOS各新增4项单测OK和py_compile；官方真实8×10=80日历史Binance Spot1m ZIP+CHECKSUM，80个逐日SHA与完整源身份在[Git机器结果](evidence/monster_shared_spot_445_feb2026_first8_real_pilot.json) 固定Git blob`f8ce449eff6212978adb66cfc7d9e53d9bf9af0d`；CI final Job在提交后校验核心、新pilot、test、workflow等共5个Git blob与触发SHA相同。**如果本会话没自行重新下载官方ZIP，请仅写读到了真实CI证据，不要冒称本人独立下载了80个**。
- **最关键真实正例事件**：2026-02-06 00:36 UTC，1000SATSUSDT、1INCHUSDT、2ZUSDT在旧98同一时点由**真实共享D0自己发出的三条WATCH**；2026-02-07 02:27 UTC有0GUSDT WATCH，02:30有一条SETUP；总WATCH=4，INVALIDATED=1（2ZUSDT后续），D1 selected=20**重复累计选取**、deferred=16**重复累计延期**、completed=4、late=0，所有新WATCH UTC与同一官方source旧Stage26逐币D0完全一样。请检查有无同一时刻3个币其实未共SQLite或来自注入历史WATCH，以及为什么**这个3/8结果不能证明98同刻真实共同D0全扫下的队列结果**：旧98里91 LATE是Stage28历史WATCH注入队列；目前实际3个同刻低于原D1 limit8，不可认为旧Stage28的91过期被推翻。
- 找有无P0/P1/P2：同source重复下载被二次污染、旧Stage26 per-symbol在相同tick使用未来minute、本次冒充完整历史上市PIT、旧源名单/后验winner泄漏、人工注入假来源升级官方、错误WATCH UTC匹配、缓存损坏被生产ValueError捕获、退出代码0但缺真实源、sqlite输入输出覆盖/残留、CI Job路径或schedule/邮件/交易/Frank越权。细分源码真实缺陷与事实源限制。
- 已知限制：本次真实币数仅8/445、其余437未跑、313原缺源。旧Stage26事前没有完整758逐名Hash且另2 unsupported Unicode未补映射。原D0过去1m聚合quote24只是历史代理，不是当年真实ticker HTTP响应；PIT listing、真实盘口深度、OOS、实际资金净回报、完整Spot+Futures、Mac、Gmail都是UNKNOWN/NO_GO；本次4个WATCH只可称成功产生历史研究信号，不能变BUY。

请产出独立审核身份、底层精确型号（不能核验写`UNVERIFIED`）、**唯一固定SHA**、实际执行的本地单测/来自官方源独立下载或仅看CI的证据等级、全部新增P0/P1/P2最小复现、最终`APPROVE|REQUEST_CHANGES|BLOCKED`。独立APPROVE最多证明8币历史source和新pilot包装器，不批准已完整445/758模型或盈利。保持`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`、`G4 UNKNOWN/G6 NO_GO`。
