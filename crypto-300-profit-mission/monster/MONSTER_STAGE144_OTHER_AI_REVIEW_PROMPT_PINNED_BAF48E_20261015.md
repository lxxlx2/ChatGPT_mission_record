# Monster Stage144 — 可直接复制发给另一独立AI的复审提示词（完整交付）
截至 2026-10-15 Asia/Bangkok。此文件是审核请求、不是审核批准。旧 Claude 审查旧SHA ff711... 返回 REQUEST_CHANGES；Stage143 5fd...修复和本次 Stage144 baf...新增源尚无实际独立审核回执。PR始终Draft, NO_GO。

---

你是 **独立第二 AI 审核员**，负责审查 Monster USD-M 妖币早期发现的因果时序、真实漏报与 G0–G6 门禁。**请自己拉取 GitHub 固定提交并独立执行测试/复现，不要只相信撰写者。**

仓库：https://github.com/lxxlx2/ChatGPT_mission_record
原 Draft PR #30：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
branch：research/monster-v4-local-discovery-20261010

**本轮待审源代码精确SHA：baf48e2022910ab9212f27ccb9e6a09b1f6586da**
上一轮 Stage143 已通过 CI 但仍待外审的工程提交：5fd3138702a3caef69ce2d48696059bceeefd6f9
再早前被 Claude 判 REQUEST_CHANGES 的提交：ff711ebef8367635871004f27a98838f7aa8c4f3
不得审核浮动 HEAD 后声称审核了 baf48e 固定 SHA，也不得将旧SHA的审查通过套用于新源码。除已列出的报告、规则和测试外没有批准任何交易或本机部署。

请先核对固定SHA以下文件：
1. crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md
2. crypto-300-profit-mission/monster/MONSTER_STAGE144_FROZEN_ACTUAL_ORIGINAL_CORE_DISCOVERY_DELAY_REPLAY_20261015.md
3. crypto-300-profit-mission/monster/MONSTER_STAGE143_FROZEN_CLAUDE_REQUEST_CHANGES_REMEDIATION_20261015.md
4. crypto-300-profit-mission/monster/MONSTER_STAGE143_CLAUDE_EXTERNAL_REQUEST_CHANGES_REVIEW_INTAKE_20261015.md
5. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage137_dynamic_t0_original_core_causal_replay.py
6. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage138_manual_evidence_scorecard.py
7. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage134_t0_population_readiness_bridge.py
8. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage135_full_market_publisher_minute_coverage.py
9. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage136_manual_publisher_archive_acquisition.py
10. crypto-300-profit-mission/local-agent/scripts/monster_v4_shadow.py（冻结原V4 D0，Git Blob bc958b3d90a8a52afa51515cb53f7e5fafaffaaa）
11. crypto-300-profit-mission/local-agent/scripts/monster_v4_stage80_dual_entry_core.py（冻结 Stage80 D1）
12. 对应 Stage134/135/136/137/138 test_*.py 和 GitHub Actions workflow。

**本次新增的主线审核重点**：

A. Stage143旧 `hypothetical_first_D0_after_detection_delay_NOT_LIVE_RERUN` 仅取 `max(original_first_D0, source_first_1m+delay)`，可能捏造晚发现仍能抓到暴涨。本次 Stage144 新 `counterfactual_discovery_delay_original_D0_D1_offline` 是否真的对 0/1/3/5分钟各自使用新 SQLite 并运行**相同原始 frozen V4 D0 `observe_snapshot/process_queue` + Stage80 D1**，首 poll 遵守可见时间+3min与全球UTC 3m对齐，第一笔只建基线、5m/61m必须真实闭合？未重新运行原始策略时禁止冒充实际信号结果。

B. 独立复现单元测试中的 FASTUSDT：原始首1m来源2026-10-28T06:21Z、n=8时出现8%突然涨幅、原 WATCH=06:30Z；首次发现迟1/3min可重放出原 WATCH，迟5min时06:30变成首次基线，**不能**再发出那次 WATCH（旧max方案反而假称06:30仍可发现）。首次原始 HIGH 2x统一固定07:36Z，延迟后不可重新选择分母或把晚于原2x的首次WATCH叫提前成功。需要自己独立跑重放确认 D0、D1、旧字段与新字段真实区别，审查 Unicode 元数据映射不泄露至币安交易所请求。

C. Source timing / selection：所谓首次观察只是后验 publisher Kline 的 first open，不是真正本机收到 Binance `!contractInfo` 的时间。模型假设首次发现延迟后历史闭合1m数据仍可回读，**只模拟 symbol discovery delay、不模拟传输、下单、source receipt 延迟**。本假设是否清楚，是否存在未来OHLC泄露、无法取得 source 时被错计 no-WATCH、真实消息到达后才能知道有多少ticker、原 D0 quote24滚动累加等研究性偏差？真实0/1/3/5m应标研究性而不是正式G1 recall。

D. Stage138 是否实际核对4个版本、0m和原始D0/D1一致、模型事件时钟和固定2x的5分钟提前标签，并把0/1/3/5m漏报、source-censored与已有币/窗口内上市分组隔离？跨窗口三组 synthetic 样本是否被误当3个真实独立前瞻数据？D1总通知次数是否仍覆盖所有既有、新上市和preT0最近上市群体？

E. 重查上次 Claude **P0 T0前24小时内上市币缺24h前史而被整体CENSORED** 的Stage143修复：原 onboardDate 00:20Z vs T0 06:20Z，首源 minute与onboard对齐才做严格来源限定的冷启动；若首根00:25Z，必须仍为 source censored。重新核对是否可能把迟报或来源错误错误声称为首可交易。**现有Stage140实际525个合约T0记录中该preT0近24h群体为0，只有 synthetic unit cases；不可自称已在真实赢家集上验证。**

F. Frozen收益、时效和原完整市场population门禁：真实Stage140只有一次2026-10-14 17:52Z WWW-FAPI备选源采样，标准FAPI自GitHub美国出口HTTP451，镜像exchangeInfo内嵌serverTime约旧8h44m，523 COIN-typed / 2 INDEX混合，issuer未知；未来7日完整publisher 1m + live listing event census 尚未成熟/获取。此前Stage116 2026-10-14 06:00 首源失败不可倒补，Stage118/127拒绝，Stage132立即追动量净经济代理负。G0 PARTIAL，G1 NOT_SCORABLE（原需3独立7日前瞻窗口、至少20真正crypto 2x、D0 strict提前>=90%和>=5min>=85%），G2/G3 NOT_PASSED，G4 UNKNOWN（至少30笔实际含盘口/手续费/滑点/退出），G5 外审尚未APPROVE，G6部署NO_GO。任何存档收益不能写成已成交净盈利。

**原始机器测试**（请独立验证固定head_sha等于baf48e...并取日志，不要用汇报代替）：
- https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38692218885 — macOS / Ubuntu 各 74/74 PASS，全部Stage134–138整合，含无默认HTTP/Gmail/任务/Frank修改。
- https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38692218936 — macOS / Ubuntu 各29/29 PASS，Stage138源/整合/统计/三 synthetic 非重叠窗口。
自行在克隆固定SHA的 crypto-300-profit-mission/local-agent/scripts 目录执行：
python3 -m unittest -v test_monster_v4_stage134_t0_population_readiness_bridge.py test_monster_v4_stage135_full_market_publisher_minute_coverage.py test_monster_v4_stage136_manual_publisher_archive_acquisition.py test_monster_v4_stage137_dynamic_t0_original_core_causal_replay.py test_monster_v4_stage138_manual_evidence_scorecard.py

请返回固定结构：
- 审核方模型身份；审核的固定 SHA 是否确认为 baf48e...；实际复测了什么；
- **代码审查总意见** `APPROVE / REQUEST_CHANGES / BLOCKED`；
- 上次Claude P0/P1各问题修复状态，新Stage144延迟真实重放是否可信；
- 所有实质 P0/P1/P2 问题，精确文件/行号、可复现输入和实际/预期、对真正提前发现/漏报/可交易性的影响、最小修复方案；不为凑边界错误数量制造无意义问题；
- 代码若 APPROVE，也**绝不**意味着 G0–G4模型业务验证成功，更不解除 `NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`、Frank隔离、手动采集节奏；未核实一律 UNVERIFIED，不得自称真实市场 Alpha。

---
