# Monster ADR-005：Codex P2 BTC基准来源依赖缺失 — 固定SHA修复与独立复审

**状态：P2_CODE_FIXED_INTERNAL_CI_SUCCESS / INDEPENDENT_CODE_RE_REVIEW_PENDING / G6_NO_GO**。本记录仅涉及已曝光工程代码审查，**没有读取尚未开始的11月行情、没有执行真实 D0/D1、没有获取行情/交易/账户数据**。

## 1. 独立审核反例

用户提供的Codex主代理（底层具体模型 **UNVERIFIED**）在用户Mac、Python **3.14.7**，针对固定 SHA `3cab91ba45e68ce2e05e963b9d75da7e2afb4ff3` 的detached只读审查，结果 **`REQUEST_CHANGES`**。其独立运行来源T0 14项、daily 10项、score 14项，共38 PASS，另下载Artifact `12614699385` 并复算真实三窗`NO_SOURCE` JSON：旧T0/issuer完整性、无来源不可评分及无交易的边界成立。

**唯一P2**：原`join_census()`对AAAUSDT只检查自身完整15日，而预注册`D1_RBTC15_LAST5_V1`需要**BTCUSDT与候选币同期六根已闭合5m**。一个真实自洽合成来源场景：`AAAUSDT`完整15天、`BTCUSDT` 2026-11-04观察日缺失；原代码误将AAA标 `SOURCE_COMPLETE_OFFLINE_REPLAY_ONLY` 且`technically_eligible_for_offline_d0_d1_source_replay=True`，误宣称研究D1输入完整。实际应保留AAA本币原D0来源就绪，同时阻断RBTC D1，记录BTC缺日而不是伪造负例或删减原市场人口。独立审核未发现该增量其它P0/P1。

## 2. 代码增量与当前来源就绪定义

**本次固定新代码/测试SHA `08340771a46e37856bad0b2b58cc4bdc97f37813`**（这是运行正式一次性CI的代码提交；下述文档提交绝不代替其固定SHA）。

修改`local-agent/scripts/monster_v4_adr005_forward_spot_score_admission.py`：Git Blob **`1686bfbe0684d0ba47ea527715850977fcad12d7`**，Schema `MONSTER_ADR005_SPOT_NOV_FORWARD_D0_D1_G1_G2_G3_SCORE_ADMISSION_V2`。旧`_valid_census`原人群/15天×每币完整性、冻结日期/分段及源计数门禁保留：

1. 明示每币本身基线`candidate_own_observation_7d_source_verified`、未来标签；`technically_eligible_for_offline_original_d0_source_replay`**只**要求该候选币本身1+7日完整，排除BTC基准本身作为D1候选。保留独立`technically_eligible_for_original_d0_gt2x_label_sources`只需本币1+7+7；未来高点标签仍尚未真实计算。
2. **BTC固定源依赖单独核对**：`BTCUSDT`必须实际存在于**同一个已准入T0的原始来源人口**中，并具备`BASELINE_24H` 1日与`D0_D1_OBSERVATION_7D` 7日全套Publisher ZIP/CHECKSUM均已通过原Stage166验证。BTC作为相对强弱基准不需要自己的未来七日GT2×高点标签（缺BTC未来标签不得阻断候选币D1）。
3. 对非BTC候选币，`technically_eligible_for_offline_rbtc_d1_source_replay`=`candidate_D0_source_ready AND btc_source_ready`。旧有易误判的组合字段`technically_eligible_for_offline_d0_d1_source_replay`**现严格同步RBTC D1完整来源门禁**；对应原汇总`technical_offline_replay_source_complete_symbols`不再高估D1就绪。额外汇总`technical_original_d0_source_complete_symbols`、`technical_rbtc_d1_source_complete_symbols`及各自未来标签技术可用数。
4. 候选币本身完整但BTC缺失：`D0_SOURCE_READY_RBTC_D1_BLOCKED`；`source_blockers`写`BTC_BENCHMARK_NOT_IN_T0_SOURCE_CENSUS`、`BTC_BASELINE_24H_MISSING_OR_INVALID`、`BTC_OBSERVATION_7D_MISSING_OR_INVALID`中真实成立的项。BTC参考币永远留在原T0源分母与逐日attempt中，用`BTC_BENCHMARK_SOURCE_COMPLETE`或`BTC_BENCHMARK_SOURCE_INCOMPLETE`明确只作基准、不当作Monster候选触发目标。
5. `all_source_15days_complete`严格沿用原publisher census的原分母完整标记，和「可评的非BTC研究目标数量」分离。V2除明示BTC新字段及BTC本身的来源状态外，所有`replay_engine_executed=False`、`metrics_from_future_labels_computed=False`、所有事件ID为null、G1 NOT_SCORABLE、G2 UNKNOWN、G3 NOT_SCORABLE、G4 UNKNOWN、G6 NO_GO 不变。没有生成SETUP、GT、高点、交易或通知。

## 3. 真实增量测试和来源对账

新增/更新`local-agent/tests/test_monster_v4_adr005_forward_spot_score_admission.py`：Git Blob **`e0508b4b86299edb942807404f4d6cfc0250fac9`**。在原14项基础上新增6项并修订原完全源的测试fixture，以包含**两个研究目标+BTC基准**，回归总数20项。独立测试覆盖：

- 同一来源档案AAA所有15日完整、BTC 11月4日缺失 => `AAA.D0_ready=True`、`AAA.D1_RBTC_ready=False`、`AAA.D1_blocker=BTC_OBSERVATION_7D_MISSING_OR_INVALID`，两者分层不丢；
- BTC不在原T0源集合 => 保留AAA/BBB原市场人数、两个D0技术就绪、`D1 ready=0`、所有候选报告明确BTC缺来源，**禁止静默凭空加入BTC**；
- BTC恢复1+7日完整 => 非BTC目标独立D1技术就绪回归；还没运行真实模型／算GT；
- BTC基线缺失 => D0不受影响、D1明确阻断；
- BTC自己的未来7日GT标签缺一天，但1+7观察均完整 => 候选D1仍就绪（BTC未来2×不是其D1输入），整体15日官方源未全；
- 一个BTC观察日缺失时所有AAA/BBB目标均正确阻断D1；BTC本身不当目标。

**真实运行**：[GitHub Actions #40238490187](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40238490187) **SUCCESS**，T0 14/14 + Publisher 10/10 + 新score 20/20=**44/44 PASS**，Python3.11。仅推送了无`schedule`的一次性workflow、没请求任何新真实市场源。GitHub真实Artifact **`12615773413`**，包含 `2026-11-02/11-16/12-01.json` 三个`asof=2026-10-26T00:00Z`离线报表。本会话实际下载zip并使用容器`zipfile.testzip()`、JSON解码验证：三份都新V2 schema，T0人口null、BTC基准就绪null，G1 NOT_SCORABLE/G6 NO_GO；外包zip SHA256 `7bb131f94639446253afb297084c1f58624efbac2cbd831c654b802e445cf8cf`。**这3份实际Artifact是“不存在真实新T0”的证据，不是已经取得未来BTC 1m历史。**

**原先外部已批准代码Git Blob实际重新核对未变**：
- T0 `b2512a393594254633c371a6e576dcec001aa009`
- 15日Publisher `9250a815ab80bc3335800b8cc90d2f5097bae1fd`
- 原D1 episode V2 `d7afa1053f82fb5c6b13b91ef41d0836e4ca8094`
- D2 HTTP微秒桥 `c80dc799074e63230d88ebaf81bf573a870b91e1`。

## 4. 独立Codex固定增量再审要求

从隔离detached worktree固定 `08340771a46e37856bad0b2b58cc4bdc97f37813` 对比被拒版`3cab91ba45e68ce2e05e963b9d75da7e2afb4ff3`，不要用后续PR文档HEAD替代。执行三个测试：
```sh
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_adr005_forward_spot_t0_gate.py -v
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_adr005_forward_spot_daily_gate.py -v
PYTHONPATH=crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_adr005_forward_spot_score_admission.py -v
```

关键重放上轮真实固定合成P2：AAA+BTC人口两币15日，仅BTC中间观察日损坏/缺失，候选D0仍ready、研究D1明确false、blocker明确存在、重算分母/汇总无漂移；BTC源不在T0、BTC源恢复、BTC基线缺失、BTC缺未来GT标签但不阻D1、目标本币缺档六种独立负面与恢复场景。读取实际Artifact12615773413、原旧10月T0来源拒绝。复审检查是否还有可用其它符号代替`BTCUSDT`的隐式路径、G0动态新上币及发行方minute`available_at`不可追溯、未来3个窗还不能评分；不得把完备来源当成模型执行结果。输出**APPROVE | REQUEST_CHANGES | BLOCKED**、固定SHA/模型实际型号或UNVERIFIED、环境/实际测试数量/发现项/G0-G6/发布评论前PR HEAD核验。此增量的独立G5目前为 **RE_REVIEW_PENDING**，**尚未收到Codex新版本审核通过**。

## 5. 边界

**`G0 PARTIAL; G1 NOT_SCORABLE; G2 UNKNOWN; G3 2026-10 EXPOSED_NOT_PASSED, NOV NOT_SCORABLE; G4 UNKNOWN; G5 PREVIOUS_PATCH_APPROVED_NEW_BTC_SCORE_ADMISSION_RE_REVIEW_PENDING; G6 NO_GO`**。依旧 **NO_MERGE / NO_DEPLOY / NO_MAC / NO_AUTOMATIONS / NO_GMAIL / NO_TRADES / NO_NEW_RPC**。