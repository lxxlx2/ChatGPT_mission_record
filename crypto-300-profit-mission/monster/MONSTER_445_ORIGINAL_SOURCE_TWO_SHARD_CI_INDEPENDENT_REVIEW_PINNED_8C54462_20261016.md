# 独立 Codex / Claude reviewer 说明：Monster 新增445官方原1m分片两片批处理器（非盈利模型）

目标仓库 `https://github.com/lxxlx2/ChatGPT_mission_record`，原`Draft PR #30`，源码+workflow固定 SHA **`8c544629c6432aecaf681c391d8ab517827444da`**，不要用后续Git CI归档后漂移的PR HEAD代替。原V2 D1子模块Codex独立`APPROVE@ef30be7bc67588b39efe552b39ab240843253846`只覆盖其上轮1 P1/1 P2修复，不自动批准新两个官方source shard的采集流程。底层审核精确模型无可靠身份凭据写`UNVERIFIED`。

请读仓库 Monster AGENTS、[开发节奏](MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md)、[全445来源分片模型之前冻结](MONSTER_445_SOURCE_SHARDED_REPLAY_STAGE2_FREEZE_20261016.md)、[本轮批处理冻结](MONSTER_ZEROQUOTE_V2_CODEX_APPROVE_EF30BE7_SOURCE445_BATCH_NEXT_20261016.md)以及新工作流文件 `.github/workflows/monster-v4-445-manual-two-original-source-shards.yml`，对照原`monster_v4_shared_445_official_source_shards.py`、`monster_v4_shared_445_one_db_from_shards.py`和源资格二次冻结Git file。**本轮工作流只有CI push自己的文件首次02/03，未来需要显式人工workflow_dispatch，绝无schedule**。

独立核查实际负例并提供命令、真实输出：

1. `start_shard`仅允许枚举偶数2,4,...26，本轮push默认2产生matrix`[2,3]`、max-parallel1片、每片workers<=2；不能越界选0/1、28或任意其它值；`shard27`13币末片由26/27覆盖。无计划批量触发、无选择最可能赚钱币、source名单合并不可遗漏/重复。注意`on.push.paths`只自身，不因 docs/proof push重复下载。
2. 两个真实source collector 子Job是否各从冻结字典序全445来源资格名单取16币、每币原十份发行者Binance Spot1m daily ZIP和同host CHECKSUM且原216h continuous `read_complete_216h`，所有12960 1m行真实校验、完整保存Artifact，ZIP+inner manifest+每成员rawSHA和publisher-daySHA在归档Job从同一run二次重验。对真源为出版主机checksum自洽，不是独立数据发行者签名；source都来自历史二次冻结名单不等于当时PIT列表。
3. 用真实手动或合成伪源负例验证少一币、坏ZIP、manifest被修改、重复symbol、每日publisher SHA被换、非法日期/错误source_sha、字符串数字格式异常、Git proof SHA漂移时是否确实fail closed；尤其manifest与外部小proof逐币逐日SHA能否发现两者不一致，不能把脚本标注`trusted_reader=True`当数字签名。
4. 测试artifact仓库50MB/60天保留、某一个真实分片成功而另一片下载失败时archive job是否禁止将本批2片标成功，是否能在不越过校验的情况下复采；已存在`monster_feb445_shardNN.proof.json`应fail而非覆盖；Git`rebase FETCH_HEAD`与原source/core/production/workflow的Git blob drift gate是否可靠，以及同时任务和并发下会否泄漏/覆盖旧Git proof或触发邮件交易Mac动作。
5. 真实`#38866315025` https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38866315025 的source实际结果只在CI完成后才定性；应核对真实triggerSHA是否精确`8c5446...`、Ubuntu/macOS各原7项、下载jobs02/03是否都成功、每片sources16×10天`160`个publisherSHA回执、归档job的source raw ZIP SHAs/Git证据一致。真实采集成功不代表全445历史共同D0/D1回放或获利模型验收。
6. 审核代码同时看原生产`monster_v4_shadow.py`、已批准共享核`monster_v4_shared_spot_d0_d1_original_core.py`、实验V2`monster_v4_shared_d1_zeroquote_research_v2.py`从新批次源pipeline Git SHA中是否完全没改；原V2的零quote分类不是原prod D1的批准策略。
7. 不触及真实生产SQLite、Mac、Gmail、Frank、Stage99，禁止合并/部署/交易，G4 UNKNOWN、G6 NO_GO。旧原98 WATCH注入模型91 LATE是不同源复现范围，新真实32币同刻7仍未压过limit8，不能用source batch直接宣称全445共池的运行时与收益。

最终交付：审核者身份及模型`UNVERIFIED`如不可独立核验、唯一固定代码SHA、SOURCE_ONLY回归实测与新GitHub CI JOB和source SHAs、所有P0/P1/P2及最小故障复现、明确`APPROVE / REQUEST_CHANGES / BLOCKED`，并标明全部旧业务`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`不变。
