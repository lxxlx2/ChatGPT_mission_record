# Monster 445 全28官方source归档 -> 唯一SQLite共享D0/D1：执行前冻结 2026-10-16

本阶段不做新来源采集；已有全部28来源proof及18 GHA原数据artifact，详见`MONSTER_445_SOURCE_COMPLETE_FINAL_AND_REVIEW_PENDING_20261016.md`。用户说“继续干”，研究范围为使用真实445个source-complete样本做一次 **ONE SQLite 3360 global polling ticks** 的原产线D0+D1源因果回放，观察共享队列极值与D1状态；原758中的313维持CENSORED。仅GitHub Research PR #30，暂不做任何模型训练、规则更新、资金决策、生产Mac/Frank/Gmail交易或定时任务。

执行合同：
1. 原有`monster_v4_shared_445_one_db_from_shards.py`、`monster_v4_shared_spot_d0_d1_original_core.py`与`monster_v4_shadow.py`源码及永久blob严格不变。先将18个固定Artifact ID分别从 GitHub Actions API 核对自身状态、workflow_run HEAD/conclusion、大小、源请求SHA；全成功后按原始GitHub artifact名字下载，不从任意网页重建。
2. 每个Artifact只能提供固定1或2个相邻字典序原分片；从Github下载解包后proof字节必须等于对应Git-tracked原proof，28个成员不得重复或遗漏；每个ZIP经同一只读函数独立校验SHA、manifest原7658-445-313冻结、每币12960 1m条、十天publisher日SHA；任一缺文件、源过期、zip SHA不符、触发SHA不符时hard-fail、不运行partial模型。
3. 在受控临时GitHub Actions Runner中只启动**一份**共享SQLite，先导入28片后调用一次旧`run_shared`，禁止28次分片独立D1后相加。输出完整原D0/D1回放JSON和仅摘要的Git报告（完整报告保存在本次CI Artifact），明确来源同host校验≠第三方证明、预知source-complete名单非真实PIT、历史非独立OOS，未有历史盘口BBO/fees/slippage、不能当可执行收益。
4. 本次回放仅由一次性显式`crypto-300-profit-mission/monster/source-batches/monster_feb445_shared_replay_request.json`文件单独Git push触发新研究workflow，无schedule/workflow_dispatch，也不能在代码变更的push里顺带请求。严格比较唯一改动、固定schema与28完整源和委托研究-only、不影响已完成源workflow。GithubCI先单测再real replay；采用Artifacts下载和只读SQLite，没有Mac服务。
5. 永久Git只保存小型summary和可定位全量回放原始结果的GHA artifact ID/run SHA；固定核心源码、请求、workflow SHAs在push summary时检查，拒绝覆盖现存最终结果。独立另一AI审核本轮源码/来源和原回放时必须取得真实结果，当前审核=NOT_DONE；NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE；G4 UNKNOWN/G6 NO_GO。

## 真实原生产D1零quote失败后进入明确实验V2分支

第一次CI [#38897042783](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38897042783) 在445入口仍没拉源，原因严格检测到原shard00的producer run #38841076844整体`failure`，但该run内`official_shard00_16_times_10_daily` Job本身`success`，失败的是后续32币模型Job；第二次CI [#38897208225](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38897208225) 得到同一根因公开字段 `artifact_id=12021352471, producer run=38841076844, conclusion=failure, head_sha=c16c951...`，原失败不允许自改成成功。只对源0/1允许检查原source job确实success且全部原ZIP/source proof Git SHA一致，其他20片仍要求整轮run success；成功source不等于producer全部success。

修正后的CI [#38897425342](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38897425342) 固定触发SHA `317154fdc8ac5a7c6e6f34bdfa42a9e43321152c`，Ubuntu/macOS全部测试成功，18个Artifact和28个原ZIP/proof逐个验证通过（日志从单片0到pair26/27均出现真实成功消息），随后源码未改的原生产D0/D1在单SQLite处理时于约2026-10-16T12:02:25Z严格失败：`SHARED_SPOT_ORIGINAL_D1_SOURCE_INVALID_CANDLE` ← `HISTORICAL_D1_SOURCE_BAD_OHLC_OR_QUOTE`，严格禁止把这个run误称为完成445原生产D1。该来源源内合法0 quote 5m在原生产D1不可支持属于已知并测试的zero-quote研究需求。

下一步**不改原生产`monster_v4_shadow.py`或原`monster_v4_shared_spot_d0_d1_original_core.py`**。复用固定SHA`ef30be7...`已独立review的研究器`monster_v4_shared_d1_zeroquote_research_v2.py`（zero quote单独`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`而非把quote补为正、假BUY/SETUP/late；原前8 D1候选仍占用槽位；非zeroquote交原processor），向445合并器加**显式CLI研究模式**`--research-zeroquote-v2`，默认原模式仍严格fail-closed；445报告必须明确`D1_model_semantics=RESEARCH_V2_SOURCE_UNSUPPORTED_ZEROQUOTE`、`only_original_production_D0_and_D1_called=false`、`all445_original_production_D1_completed=false`，并输出真正共享D0 WATCH及V2八槽D1分布。完整445实验V2需要新的独立other-AI审核；源归档完整不代表交易盈利，G4 UNKNOWN、G6 NO_GO、NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE。

已实施的研究模式代码提交：`e1015ab619c4da7fa24fd0f795d964f2abff1b30`、`5079283be1881d38e3c1f4e91f64043ce74edf50`、`ad80e598f05d655a5cfcfafea10257be00c1091b`。**新增实验审查独立状态：NOT_DONE**。如实验仍因非零quote损坏或数据缺陷报错应继续fail-closed，不允许进一步无证据归因。
