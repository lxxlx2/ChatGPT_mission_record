# Monster Stage142：新上市币原始 D0/D1 冷启动模型真实工程结果与外部审核交接

日期：2026-10-15 Asia/Bangkok；原 PR #30，仍 Draft/NO_GO。本轮根据用户最新要求**先更新长期规则**再继续原信号模型。规则文件 MONSTER_MODULE_DEVELOPMENT_RULES.md 已在 commit 7fbb274cd95c65860f87e28c23c7e16ccd28a7cb 新增“进入其他 AI Review 门槛必须直接给出审核提示词，固定 SHA 和证据”的强制规则。Stage142 技术范围事先在 [冻结协议](MONSTER_STAGE142_FROZEN_LISTING_COLD_START_20261015.md) commit edc8b1d28846b5994cc7200bc5e7ba3245dd8119 固定。

## 1. 这次具体解决的模型缺陷，而非外围边界

此前 Stage137/138 对完整保留官方 1m ZIP 和 CHECKSUM 的 IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE 统一标为 NEW_LISTING_REPLAY_NOT_YET_SUPPORTED_PIT_UNVERIFIED，无论信号何时出现，都不实际运行原始 D0/D1。这造成最早期妖币上市后数分钟的信号研究关键路径被跳过，且不是缺少未来真实完整数据才能修复的代码问题。

本轮在[Stage137 原动态因果回放源码](../local-agent/scripts/monster_v4_stage137_dynamic_t0_original_core_causal_replay.py)直接加入 complete-source 新上市首次观察后的冷启动回放，实际调用冻结原 V4 D0 的 observe_snapshot/process_queue，隔离 SQLite，遵守原三分钟 UTC 绝对时钟、第一轮建立快照基线、24h quote 只能累加真实观察到的有效分钟、不能补造上市前 24h 买卖/成交额、6 根完整而且自然 UTC 边界的5分钟K线（首分钟如06:21则从06:25开始成组）、原 WATCH 资格和15分钟队列。原冻结 shadow Git blob bc958b3d90a8a52afa51515cb53f7e5fafaffaaa **保持不变**。

冻结 Stage80 D1 仍使用原模块；在首个 D0 时若不足61根真实已闭合1m，则传 features=None 令原核心保留 WATCH 状态，只用当时*已闭合*实际 D0 源价格填 WatchState.first_price（没有伪造其他60根未来K线）。待连续61根真实已观察分钟具备后，才以原 Stage80 from_archived_closed_bars 与 original gate 尝试 D1；D1 过期、first owner不变。Stage141 Unicode映射仅限原D0隔离SQLite代理，不更改原币名和官方原始来源。

新行状态为 ORIGINAL_CORE_NEW_LISTING_COLD_START_UNVERIFIED_PIT_CAUSAL_OFFLINE，始终有原首观察UTC、官方先前首次可交易未确认、asof issuer未验证、real-time delivery not observed。Stage138已在[原跨窗口统计](../local-agent/scripts/monster_v4_stage138_manual_evidence_scorecard.py)里将新币 cold_start_* 计数完全隔离于 PREEXISTING_AT_WINDOW_START 的原声称口径，CENSORED、OTHER_CORE、历史31样本冻结状态不变，不发生赢家后选和G1人数偷换。第一根上市观察分钟 OPEN 到未来 HIGH gross2×继续只能是事后上影线代理，并非交易净利润。

## 2. 实际测试和修复

目标代码与测试成功固定 SHA：**ff711ebef8367635871004f27a98838f7aa8c4f3**（review pin；其后仅新增正式报告、审查提示词及计划文件，不得把后续浮动 HEAD 当作审核过的源码）。相较修复前基线 **50de0d8316c11ac4dcf7d736f397b9fdb16e0ce2**，只有设计、原 Stage137/138 回放和测试、长期规则发生改变，原 V4 D0/Stage80 D1 都不变。

实际[Stage137 GitHub Actions #38615294004](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38615294004)：Ubuntu job 116028708440 **13/13 PASS**，macOS job 116028709051 **13/13 PASS**。新测试实际将合成后观测 1m 行情送入**原**V4 D0/Stage80 D1：06:21 首观察→06:24 第一次基线 tick；合成第一次 3分钟/15分钟涨幅后的真实 D0 可以提前于 08:21 合成毛2x上影线；不允许 D1 在 61分钟历史完成前触发；同一组数据原 ASCII 新币名与 Unicode 新币名首次 WATCH/D1 时刻一致。合成K线不作为真实预测成功。

实际[Stage138 GitHub Actions #38615294086](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38615294086)：Ubuntu job 116028707966 **20/20 PASS**、macOS job 116028707565 **20/20 PASS**；完整 Stage133/134/135/137→Stage138研究记录保留原四条 synthetic venue 尝试（一个老正常ASCII、一个旧Unicode、一个源缺失、一个 source-complete新上市），加上原冻结跨独立窗口去重/重叠测试。默认无T0拒绝；没有现场 HTTP、没有自动计划、没有 Frank/Gmail/交易动作。

首轮工作流 #38614975576、#38615174262 等短暂失败源于原回归仍期待 newly listed 标为模型不支持、计数依旧 new_listing_unscored；代码新功能成功运行但原测试断言过期。根据结果修复了旧测试预期，**没有调整策略以求过线**。实际完整新测试和旧回归最终以上述两项绿色CI完成。

## 3. 外部独立其他 AI Review 按新规则已直接交付

[完整可复制其他AI独立审核提示词](MONSTER_STAGE142_INDEPENDENT_OTHER_AI_REVIEW_PROMPT_PINNED_FF711_20261015.md)，**审核指定固定代码 SHA ff711ebef8367635871004f27a98838f7aa8c4f3**，要求核对 Stage137/138 冷启动因果时序、闭合1m/5m、真实61分钟D1、源码冻结、 Unicode内域映射、Stage140 真实525合约 WWW exchangeInfo较旧的来源限制、完整人口和 G0–G6 冻结门槛，并要求 APPPROVE/REQUEST_CHANGES/BLOCKED 书面反馈和精确文件/行/复现、NO_DEPLOY保持。**其他 AI 还没有实际返回任何审核结果，所以 G5=NOT_DONE，不能声称独立审批完成。**

## 4. 下一研究主线和权限

Stage140 real user-triggered T0 原数据UTC 2026-10-14 17:52:47、初始 USD-M 525、COIN typed523/INDEX2，独立 fapi主域名HTTP451、WWW镜像exchangeInfo内嵌serverTime比实际HTTP晚/早不一致，真实G0仍PARTIAL。原始 7日后会需要 525×9=4725个真实源ZIP/CHECKSUM，当前0；窗口至UTC2026-10-21T18:00，保守最早另外请求Stage136 UTC2026-10-23T18:00后才能尝试后验官方数据获取。没有额外的7日实时上市事件流、盘口深度及真实买卖回合，不能把 Stage142 合成fixture 当真实检测模型成功。

**下一个并行可开发主线**：根据已经保存的真实 Stage140 全市场 BBO/ticker/mark 研究盘口数据新鲜度、点差和假设资金买入的可执行性，并检查原始报价和成交记录是否完全同步；针对真正首次上市的新币实时可见的证据层仍需要另行用户授权有限采集，不能擅自创建常驻任务。若外部审核给出 REQUEST_CHANGES 应按真实缺陷修复后重新 CI，并更新 reviewer pin。所有时点不修改原冻结 Stage116 失败、Stage118/127 REJECTED、Stage132 BUY proxy NEGATIVE。

G0 PARTIAL; G1 NOT_SCORABLE; G2_G3 NOT_PASSED; G4 UNKNOWN; G5 NOT_DONE; G6 NO_GO; OTHER_AI_REVIEW_REQUEST=PREPARED_AND_DELIVERED; FRANK UNCHANGED; GMAIL OFF; NO_NEW_SCHEDULE; NO_MERGE; NO_DEPLOY.
