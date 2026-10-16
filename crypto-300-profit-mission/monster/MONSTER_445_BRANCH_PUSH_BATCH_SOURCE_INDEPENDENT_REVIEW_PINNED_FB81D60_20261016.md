# Monster 445 源分片手动请求入口：另一 AI 独立审查固定版本（2026-10-16）

**状态：AWAITING_INDEPENDENT_OTHER_AI_REVIEW，不得自称 APPROVE。** 范围只限既有原 Monster PR #30 的来源分片手动Git push触发入口、同Run官方源二次校验及持久化，不评定D0/D1策略是否盈利。

- Git仓库：`lxxlx2/ChatGPT_mission_record`；研究PR：[Draft #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，不合并。
- **固定审核源码+请求 SHA**：`fb81d60cbb6936542629b21cbb587c116682a064`。上一成功触发SHA `ac7fa9c5ba161aae1aaba194c77e58bcdc306f05`；这两次及最新proof归档 `bd4bc7028c0c4005d96c07b1e3d376afda23cd31` 对应的workflow Git blob SHA均精确相同：`64bcb9e8387951105109666d408634c84f3d57c5`。**请按固定版本审查，不用后续HEAD替换。**
- 对比原首次通过source批处理workflow源码SHA `8c544629c6432aecaf681c391d8ab517827444da`。旧Codex `APPROVE@ef30be7bc67588b39efe552b39ab240843253846`只适用于研究V2 SQLite mask/deadline，不批准此workflow。
- 开发规范：`monster/AGENTS.md`、`MONSTER_MODULE_DEVELOPMENT_RULES.md`、`MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md`、`MISSION_SPEC.md`。代码前冻结方案记录在上述长期节奏 Stage154 中，先于workflow提交（Git `98282874e94c934e0485523a9374703234c1c780`）。

## 需要独立实测的审查重点

1. 既有workflow `.github/workflows/monster-v4-445-manual-two-original-source-shards.yml` 是否**只有**明确研究分支上 `crypto-300-profit-mission/monster/source-batches/monster_feb445_manual_request.json` 改动的 `push` 触发；没有定时器、下游workflow_run、自动继续下一对、默认分支写入、Frank/Gmail/下单/真实生产SQLite权限或生产服务副作用。旧workflow_dispatch在默认分支无文件时本来不可用于手动运行，不能以UI推测代替真实push回执。
2. `fetch-depth:2` 是否能够真的让 `git diff-tree --no-commit-id --name-only -r HEAD`检验新请求提交**仅修改请求文件**，故意多改任意文件应失败。请求JSON严格schema/start_shard/request_id/research_only/approved_scope，start_shard只能整数偶数4、6……26，必须匹配请求ID及合法公历日期；00/01及已存在proof不能覆盖、坏类型字符串/true/越界/名单重复/额外字段/目录注入要拒绝。
3. 原 `monster_v4_shared_445_official_source_shards.py`、`monster_v4_shared_445_one_db_from_shards.py`、冻结Source-complete445名单是否保持源码Git blob不变：445真源原758历史尝试、313原删失，28固定分片，每片16、最后片13；官方Spot原1m每日ZIP+同host .CHECKSUM×每币10天，12960分钟Decimal源，SHA、成员身份、时钟和行数。不能将同host checksum称为第三方数字签名或历史listing PIT。
4. 单Job源worker<=2、两分片`max-parallel:1`、所有官方数据下载真失败即fail closed；不能改为无限并行、缺源补0、排除无异动币、逐片分别跑生产D1、把研究V2替换原production。
5. 归档Job确实仅接受同一GITHUB_RUN_ID两份原始source Artifact，验证内ZIP/hash、原publisher十天SHA、manifest SHA与每币raw SHA并且两片全部成功才落Git proof；已存在proof拒绝覆写；rebase后原core/prod/workflow/request Git blob指纹漂移即拒绝；若只有单片成功不能把32币计为完成；60天Artifact过期时proof不能冒充可恢复的原始分钟价格源。
6. 固定真实CI第一次失败须保留：[#38871737877](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38871737877)（`62f0b795...`）freeze因checkout默认浅历史导致`MONSTER_FEB445_MANUAL_REQUEST_MUST_BE_ONLY_CHANGED_FILE`拒绝，后续任务skipped。要求用真实shallow负例/双深度正例复测，不能把原失败标成功。
7. 成功04/05 [#38871892429](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38871892429)（触发`ac7fa9c5...`）和06/07 [#38872802494](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38872802494)（触发`fb81d60c...`）均需独立核对**6/6 jobs completed/success**；每片16币160份官方日回执、原zip Artifact + SHA与Git proof完全一致，官方源ZIP可用且未过期。可以重验已归档原字节，不能声称新独立重下全部640份官方日ZIP，除非审查者真的做了重下。
8. 原生产 `monster_v4_shadow.py`、`monster_v4_shared_spot_d0_d1_original_core.py`、V2研究源码不因本批source请求改变；前32共享D0 WATCH29、单tick最大7低于8，不把旧Stage28 98 WATCH注入/91 LATE冒充实际445共共享D0结果。零quote V2仅研究，不批准生产切换。

## 本轮冻结可回读结果

| 分片 | Artifact ID | proof Git blob SHA | 原始内部ZIP SHA256 |
| --- | --- | --- | --- |
| 04 | `12034075028` | `0c65cb6cf9dd653bd8c2cfe08c96bb0d0ae8718e` | `362afe7cde37f571b34810b0f79e2c8c2ae08906a8a59da49dbb7167d6965a58` |
| 05 | `12033058858` | `37de4da4484f94259256427060a08495cd9024c7` | `926073e7c8a1bbeeb8621414cd9a80597990875dcb056b71ba4ebcd60d9fe4ea` |
| 06 | `12033614509` | `0d4d67e9a57c5567a468b446af43d43a664d704e` | `6040ed2c6fcf926f9dddc1f6660c82b1b44fea8bb497445e22f4517068af4e20` |
| 07 | `12034650662` | `399a009918637812b80241bd0d029e343a7cbe40` | `656e0e7e16bd6db9afbcdd1a33ca01e4e0601f585a1fd2f96bfc46ba10e5cf05` |

截至固定06/07成功，官方历史原source **8/28片、128/445币、1280份10天发行者回执**；尚未有28/28真实source，绝无全445单SQLite报告。缺源317属445完整池尚未归档，原313历史无完整source仍单列CENSORED。

审查者输出：确切AI身份/模型（无法核实写UNVERIFIED）、唯一固定代码SHA、实测命令及原始退出码/证据URL、P0/P1/P2实际缺陷/反例、明确 `APPROVE` 或 `REQUEST_CHANGES` 或 `BLOCKED`，禁止以作者自己CI冒充独立审核，保持 `NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`、`G4 UNKNOWN/G6 NO_GO`，Frank与Stage99不变。
