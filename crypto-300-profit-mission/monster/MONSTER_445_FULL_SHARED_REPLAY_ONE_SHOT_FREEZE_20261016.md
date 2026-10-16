# Monster 445 全28官方source归档 -> 唯一SQLite共享D0/D1：执行前冻结 2026-10-16

本阶段不做新来源采集；已有全部28来源proof及18 GHA原数据artifact，详见`MONSTER_445_SOURCE_COMPLETE_FINAL_AND_REVIEW_PENDING_20261016.md`。用户说“继续干”，研究范围为使用真实445个source-complete样本做一次 **ONE SQLite 3360 global polling ticks** 的原产线D0+D1源因果回放，观察共享队列极值与D1状态；原758中的313维持CENSORED。仅GitHub Research PR #30，暂不做任何模型训练、规则更新、资金决策、生产Mac/Frank/Gmail交易或定时任务。

执行合同：
1. 原有`monster_v4_shared_445_one_db_from_shards.py`、`monster_v4_shared_spot_d0_d1_original_core.py`与`monster_v4_shadow.py`源码及永久blob严格不变。先将18个固定Artifact ID分别从 GitHub Actions API 核对自身状态、workflow_run HEAD/conclusion、大小、源请求SHA；全成功后按原始GitHub artifact名字下载，不从任意网页重建。
2. 每个Artifact只能提供固定1或2个相邻字典序原分片；从Github下载解包后proof字节必须等于对应Git-tracked原proof，28个成员不得重复或遗漏；每个ZIP经同一只读函数独立校验SHA、manifest原7658-445-313冻结、每币12960 1m条、十天publisher日SHA；任一缺文件、源过期、zip SHA不符、触发SHA不符时hard-fail、不运行partial模型。
3. 在受控临时GitHub Actions Runner中只启动**一份**共享SQLite，先导入28片后调用一次旧`run_shared`，禁止28次分片独立D1后相加。输出完整原D0/D1回放JSON和仅摘要的Git报告（完整报告保存在本次CI Artifact），明确来源同host校验≠第三方证明、预知source-complete名单非真实PIT、历史非独立OOS，未有历史盘口BBO/fees/slippage、不能当可执行收益。
4. 本次回放仅由一次性显式`crypto-300-profit-mission/monster/source-batches/monster_feb445_shared_replay_request.json`文件单独Git push触发新研究workflow，无schedule/workflow_dispatch，也不能在代码变更的push里顺带请求。严格比较唯一改动、固定schema与28完整源和委托研究-only、不影响已完成源workflow。GithubCI先单测再real replay；采用Artifacts下载和只读SQLite，没有Mac服务。
5. 永久Git只保存小型summary和可定位全量回放原始结果的GHA artifact ID/run SHA；固定核心源码、请求、workflow SHAs在push summary时检查，拒绝覆盖现存最终结果。独立另一AI审核本轮源码/来源和原回放时必须取得真实结果，当前审核=NOT_DONE；NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE；G4 UNKNOWN/G6 NO_GO。
