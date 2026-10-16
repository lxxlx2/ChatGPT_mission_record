# Monster 445 全来源、同库原D0/研究D1、真实拥塞：合并独立审核包（固定 SHA）

审核对象：Mission GitHub Draft PR #30，分支 research/monster-v4-local-discovery-20261010。
**唯一审核固定代码和证据 SHA：6d7ddbf135ab9967abc1a2337d4d6ea04e4c6b93**。
与此前独立批准的 ef30be7bc67588b39efe552b39ab240843253846 比较；旧批准仅覆盖zeroquote V2的当时32币研究范围，不覆盖新445整库来源、工作流、容量或经济可用性。审核新增范围要独立完成，不准作者CI替代外部AI审查。本包创建属于仅追加文档，不能把它的新HEAD冒充审核源码SHA。

## 可直接复制至另一 AI（Claude/Codex）的完整审核提示词

你作为独立审查 AI，审核 GitHub https://github.com/lxxlx2/ChatGPT_mission_record/pull/30 的**固定 SHA 6d7ddbf135ab9967abc1a2337d4d6ea04e4c6b93**，比较基线 ef30be7bc67588b39efe552b39ab240843253846。只做只读独立审核、失败复现、源 provenance 与实测统计交叉验证。**不得替换HEAD，不得修改生产、合并PR、部署、发送Gmail、启动任何定时任务或下单。**

请先读 crypto-300-profit-mission/monster/AGENTS.md、MONSTER_MODULE_DEVELOPMENT_RULES.md、MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md、MONSTER_445_SOURCE_COMPLETE_FINAL_AND_REVIEW_PENDING_20261016.md、MONSTER_445_REAL_SHARED_D0_ZEROQUOTE_V2_FIRST_FULL_RUN_20261016.md、MONSTER_445_BURST_CAUSAL_REPRO_AUDIT_FREEZE_20261016.md 与对应全部新脚本/workflow。审查前核对固定 SHA 是 PR #30 研究分支祖先，并核对 28个Git proof与18个原来源Artifacts存在，不把313删失归零。

**独立审查/实测重点：**

1. 原始758历史候选中445在2026-02-04历史source-complete，313 CENSORED；445是事后source-complete cohort非真实当时PIT上市池，也非新的独立OOS。核查冻结名单、28分片、4450个Binance同host日ZIP/.CHECKSUM身份、每币12960分钟、SHA/manifest/原blob；同host SHA一致不可上升为发行方独立数字签名或当时listing资格。
2. 来源CI实际成功 #38874454025（08–27来源十对13/13），固定触发 df83c4367e8da9bce593dd123e18cd8f25b01917；早期shard00来源Artifact 12021352471所属整体run #38841076844为 failure，但其源下载job success，后续原32币模型job failure：代码是否**严格仅对0/1源Job成功**作窄例外，其他后续来源依旧要求run全部success。shard01旧GitHub工作流曾在新增合并器源码push时重采且**覆写旧proof**（d16a2c），改动manifest/ZIP/触发SHA但逐币原市场SHA不变；验证旧workflow push触发确已关闭且拒绝覆写、旧冻结proof与原Artifact严格相等。
3. 真实445共SQLite全量CI #38898752712，固定执行 9b32f8debe6a4246f91f56a84aa7539884f5f857：3/3 Jobs completed/success，18来源Artifact二次回读、28 ZIP+proof SHA、1份SQLite/3360次全445共同轮询（不是28分片独立D1相加）。完整模型文件Artifact ID 12044872933，名 monster-feb445-all445-real-original-shared-D0D1-once，内 monster_feb445_all445_one_sqlite_full_result.json SHA256 **370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf**；摘要证据 crypto-300-profit-mission/monster/evidence/monster_feb445_all445_one_sqlite_replay_actual.json（Git blob 532d887a78f0d225132959731ea166d13767bf9c）。
4. **绝不能混淆模型语义**：原产线monster_v4_shadow.py及monster_v4_shared_spot_d0_d1_original_core.py代码blob保持冻结，原生产D1共池回放 #38897425342 在真实0报价5m源上 fail-closed（SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE）；成功的445结果是同一源码的原D0加zeroquote V2实验D1，只允许保留原前8 FIFO槽位并对0 quote独立分类 SOURCE_UNSUPPORTED_D1_ZERO_QUOTE，不得伪造正报价、SETUP、LATE或提前套用生产。核查mask持久化、截止时刻、超额9个候选不得挤入、旧通过版本与本次是否相同，确认研究V2不能自称生产通过。
5. 从**完整事件与queue原字节**独立重做269 WATCH、269唯一候选、最大单tick98（2026-02-06T00:36:00Z）、其峰值原源D0触发96个15m与2个3m、对应98队列的91 LATE+7 EVALUATED，额外GPSUSDT和LUNAUSDT在00:39Z产生2个LATE，从而总93 LATE，120 SETUP_ACTIVE均须按各自15分钟同符号候选窗口核对。D1 169 EVALUATED、93 LATE、4 INVALIDATED、3源zeroquote不支持，3位为ACAUSDT×2和GUSDT×1。每轮原8槽上限、V2最大选中8和selected753总尝试不能说成753独立候选。旧Stage28的98 WATCH/91 LATE来自注入式旧结果，不得替代本次真实共源。
6. 只读统计审计 #38904182068（1/1 success，触发 c32a532cef545a963fe6db9dd86561a56473edd1）：重取 **同一**原回放Artifact/原SHA，跑 local-agent/scripts/monster_v4_shared_445_burst_audit.py 与固定summary，成果 evidence/monster_feb445_true_burst_causal_audit_actual.json（Git blob 0f935730e9fcdbbb0d75d12e801d2237559e0c93）。核对91/93迟到集中率97.8495%、候选15m期限、3m轮询、原8槽，最乐观理论6轮×8=48个**不同候选一次处理**、98同刻至少50个即使无重试也无法全部在时限内处理。这个50是容量数学下界不是会赔钱的币数；全部93 LATE不能叫93笔盈利交易。
7. 漏报/提前量/真实买卖时点尚无独立OOS、历史PIT listing和可成交深度BBO；24h成交额是从分钟数据回推的历史proxy而非真实当时ticker；手续费、滑点、流动性、真实通知延迟与真实净PnL缺失。不能将120个SETUP_ACTIVE事件当作120个真实盈利买入，或对98币事后挑赢家优化并在同一日期宣称模型赚钱。须同时给出未来正常币/大行情拥堵对照、短/长期漏报、候选排序与信息量、风险、成本和是否值得上线的实际门禁建议。
8. 必须审核所有涉及的 CI workflow 是否无 schedule/cron/launchd/ChatGPT Automation、无 Frank/Gmail/交易副作用；来源归档严格防覆盖、Git重放指纹、避免跑旧trigger重复覆写新proof；研究 PR仍应 Draft/未合并。按Monster现有G0–G6要求逐项给出是否能过线，不降低准则，不发真实提醒。

可复现只读命令示例，在独立环境执行：先 git checkout 6d7ddbf135ab9967abc1a2337d4d6ea04e4c6b93，再 gh run download 38898752712 -R lxxlx2/ChatGPT_mission_record --name monster-feb445-all445-real-original-shared-D0D1-once --dir /tmp/monster-review-445；验证full_result SHA256，然后以 Python 3.12 执行
python crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_445_burst_audit.py --full /tmp/monster-review-445/monster_feb445_all445_one_sqlite_full_result.json --summary /tmp/monster-review-445/monster_feb445_all445_one_sqlite_summary.json --out /tmp/monster-review-445/independent-burst.json
还请独立查看 #38904182068、#38897425342 和前述来源CI原日志，并视能力复现至少一个真实反例或故障注入，不要只总结作者的说明。

**固定格式反馈**：审查者真实身份及可核验模型版本（无法核验写UNVERIFIED）、唯一审核SHA和对比基线、检查过的文件/Artifact/CI、自己运行的命令与原始退出码、能复现的P0/P1/P2/P3问题（文件行号、触发输入、业务后果）、各项证据是否可靠、是否可安全开展下一阶段*研究*，以及最终明确 **APPROVE / REQUEST_CHANGES / BLOCKED**（只能针对明示的本次固定研究代码及来源证据，不能扩展为盈利模型/生产批准）。无论结果如何，保持 **NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE，G4 UNKNOWN、G6 NO_GO**。

## 作者内审与实际独立审查状态

作者源码和成功CI都是内证，**OTHER_AI_REVIEW=NOT_DONE**。未经真实另外AI回复，不能把审核提示词或脚本结果当作外部APPROVE。下一高价值工作是评估98同刻市场级事件的分组展示、预先约束的D1分配方案、真实可执行净收益与未来样本外召回，先冻结指标，不能回头修改过去信号的评价标准。
