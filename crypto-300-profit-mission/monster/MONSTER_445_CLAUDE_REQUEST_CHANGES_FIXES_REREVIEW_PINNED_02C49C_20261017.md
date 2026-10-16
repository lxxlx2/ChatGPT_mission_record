# Monster 445 — Claude REQUEST_CHANGES 问题修复与一次性复审（2026-10-17）

## 事实、状态与固定版本

- PR：[Mission Draft #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，分支 `research/monster-v4-local-discovery-20261010`，`Open/Draft/unmerged`。
- 上一**实际独立审核**：用户提供的 Claude 对固定 SHA `6d7ddbf135ab9967abc1a2337d4d6ea04e4c6b93` 的报告，底层模型版本 `UNVERIFIED`，结论 **REQUEST_CHANGES**。独立审核者由于环境限制无法下载原445回放Artifact，来源JSON独立复算为 UNVERIFIED；不把此访问障碍冒称代码缺陷，也不宣称用户已批准生产。
- **本次交付复审唯一固定SHA：`02c49c2533776a564c94bcc8d9b6d8faf1605171`**；对比上一审核SHA `6d7ddbf135ab9967abc1a2337d4d6ea04e4c6b93`。新审计及28份来源证据已经归档、可用，后续该文件的新增文档commit**不修改复审代码身份**。原生产 `monster_v4_shadow.py`、`monster_v4_shared_spot_d0_d1_original_core.py`、研究 `monster_v4_shared_d1_zeroquote_research_v2.py` Git blob 分别为 `bc958b3d90a8a52afa51515cb53f7e5fafaffaaa` / `3a9e4bbd75ff4f5ef6cd0bfe87895d932c95892c` / `b16e89f2a20c1dfaaebce1497da8d991d3907ed7`，未被本轮修改。
- 来源完全覆盖仅为历史2026-02-04同日source-complete445币的**事后样本**，原758中的313删失，无真实历史PIT上市池/独立OOS/盘口深度、费用、滑点、可执行净利润。
- 研究模型仍为原生产D0加零quote实验性V2 D1，历史完整实验结果不可直接升级生产；原产线D1对合法市场0 quote fail-closed仍属真实事实。历史旧统计269 WATCH、98同刻、93 LATE、120 SETUP，G4 UNKNOWN/G6 NO_GO，NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE。

## 对 Claude 问题逐项处理（本次作者修复，等待另一AI重新确认）

1. **P1-1（市场零成交额语义）**：保留历史固定V2的原始状态字面值 `SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`，不伪造已发生的历史队列终态，不重写历史JSON或擅改冻结V2。新的 `monster_v4_shared_445_burst_audit.py` 报告明确 `D1_market_zero_quote_is_real_no_trade_not_missing_data=true`、`D1_research_D1_rates_conditional_on_market_quote_presence=true`；相关 `archive_replay_runner.py` 对未来摘要也做显式市场无成交说明。**新增实测反例确认审核者“仅用最后6根且老前2根零quote也可正常评估”的假设不成立**：原 `monster_v4_shadow.evaluate_closed_5m` 在截取 `usable[-6:]` 前会对传入8根逐根调用 `positive(c[7])`。在第一根合法5m零成交额、后六根为正的真实生产函数模拟中抛 `ValueError`，不可能在既有生产算法下当成支持成功。此次是**统计语义及前8根生产等价性纠偏**，不是新策略上线批准；请复审者明确是否接受此语义修复，若要求改历史状态请给出迁移/旧证据隔离方案。
2. **P1-2（其他AI匿名环境无法下载）**：原GitHub Actions `#38898752712` 的结果Artifact `12044872933` 已被本会话下载并校验ZIP内 `monster_feb445_all445_one_sqlite_full_result.json` 的精确SHA256 `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`。包含 `monster_feb445_all28_source_audit.json`、原full JSON和原summary的完整ZIP可由用户在本对话下载后上传Claude审查（**不请求GitHub token或用户秘密**）。新复算在固定原文件字节上`120/120 SETUP`、`93/93 LATE`按真实生产 `event_key(venue,symbol,kind,queue.id)` 精确匹配。
3. **P2-1（生产未改的自证字段）**：新审计 `monster_v4_shared_445_burst_audit.py` 从工作树中独立计算3个Python生产/研究源码的实际Git blob SHA1，并与冻结常量逐个比对，否则fail closed。 `monster_v4_shared_445_archive_replay_runner.py` 的后续 `summarize()` 同样引入实际源码Git blob读回校验，不能仅根据自写JSON中True确认真实程序身份。
4. **P2-2（proof与ZIP manifest收据不交叉）**：`monster_v4_shared_445_official_source_shards.py` 的 `read_archive` 对每个币 `source_sha256_by_symbol[*].raw_sha256` 和 `publisher_days` 同ZIP内manifest逐项强制一致，任何篡改都reject；源单测新增同时篡改日SHA与币原行SHA的2个反例。真正读取原18来源Artifact的工作流 [#38947715265](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38947715265) `completed/success`，全28片、445币、4450日收据与inner manifest严格相等，未重新下载全部Binance官方外网数据，仅校验已归档原字节。不可将同host .CHECKSUM称为第三方签名。最终可解析JSON：`evidence/monster_feb445_original28_publisher_sha_proof_manifest_verified_actual.json`（Git blob `24603b09ec66a2ba84b25491c6806d4b8897c5c0`）。
5. **P2-3（源码窄例外与覆写守卫单测）**：只读源run整体失败而源Job成功的0/1例外抽为 `attest_source_job_on_failed_early_run`，单测真实型对象涵盖 `(0,)` 允许、非法pair和失败/未完成源job fail closed。静态workflow单测扫描原shard01及另外4条遗留工作流的覆盖守卫、不得再含 push/schedule。此轮真实 [#38947037957](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38947037957) 和 [#38947715265](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38947715265) Ubuntu研究验收均 `success`，一次执行 **14项**源/来源runner单测和真实第一根0quote生产负例。
6. **P2-4（旧push工作流重复写证据）**：对 `.github/workflows/monster-v4-445-first32-zeroquote-research-v2.yml`、`monster-v4-445-real-first32-shared-D0-D1.yml`、`monster-v4-445-source-complete-real-shared-pilot.yml`、`monster-v4-shared-spot-d0-global-d1-official.yml` 移除普通代码push监听，保留仅显式`workflow_dispatch`，并为原目标证据加拒绝覆盖守卫；历史shard01工作流之前已停用push并防覆盖。本轮未新建任何 ChatGPT Automations/GitHub schedule/launchd。
7. **P2-5（SETUP与队列匹配启发式）**：新 `monster_v4_shared_445_burst_audit.py` 用冻结生产 `event_key`（原 `record_event` 固定SHA256格式）把每个SETUP/LATE event精确解码并与candidate ID唯一关联、校验同币身份、有效期、LATE最终态及截止时间，而非以前同币15分钟简单存在性判断；真实原full JSON 120个SETUP及93个LATE全数一对一匹配，并保留269 WATCH、98同刻、峰值91 LATE、另外GPS/LUNA两条LATE。原8槽每3m、15m最乐观6×8=48、98-48=50是**结构性容量下界**，不是盈利或真实漏赚笔数。新审计证据：`evidence/monster_feb445_true_burst_causal_audit_review_verified_actual.json`（Git blob `22fce695786c49b6b0fdfb9a6f4c1cf0d9a26d6c`）。
8. **P2-6（命名/范围）**：原 `SECONDARY_ROSTER_SHA256`确实固定原758名册，不是445成员hash；为了保护旧已固定原shared-core Git blob，不回写生产函数给冻结常量重命名。报表及交接均明确“原758冻结原始roster”“事后来源完整445”“原313删失”“历史PIT UNVERIFIED”而非隐含445有PIT资格。
9. **可审计失败历史**：中间审计run #38947438938 虽source核验Job成功，但写出的 `evidence/monster_feb445_original28_publisher_sha_proof_manifest_review_actual.json` 末尾带字面量\\n，不可JSON解析。**故意保留原Git证据不覆写/冒充合格**。修正为 `chr(10)`、文件内 `json.loads` roundtrip 后在新的固定run #38947715265 成功输出`*_verified_actual.json`，新增Artifact ID `12067007305`、当前未过期、预计到期2026-12-15T18:30:32Z。这个失败是输出序列化问题，不是Binance行情或28个原始ZIP不一致。

## 最新复审命令（请实际执行并提供真实退出码）

在独立环境：
- `git checkout 02c49c2533776a564c94bcc8d9b6d8faf1605171`，`git diff --name-status 6d7ddbf135ab9967abc1a2337d4d6ea04e4c6b93 HEAD`。
- 在 `crypto-300-profit-mission/local-agent/scripts` 下 `python3 -m unittest -v test_monster_v4_shared_445_archive_replay_runner test_monster_v4_shared_445_source_shards test_monster_v4_shared_d1_zeroquote_research_v2`。特别核查 production `evaluate_closed_5m` 的8根零quote prevalidation（最后6根用于指标，不代表仅最后6根需要有成交额）。
- 获取原445 JSON：可从用户上传的原Artifact ZIP中抽取3个文件，无须Token；核实SHA并跑 `monster_v4_shared_445_burst_audit.py --full <解压后原full文件> --summary <原summary文件> --out <全新路径>`。对比Git新精确锚点结果。
- 核查新source原版18Artifact读取的Git JSON已经可以`json.loads`且来源28/28每分片的十天SHA计数=4450；对照CI #38947715265原日志和所有固定proof Git SHA；勿把作者CI充当独立证明。
- 针对原raw JSON故意篡改一个SETUP `event_id`（在隔离复制中）并同时修正本地输入SHA用于反例，核查精确锚点校验确实拒绝；其他真实时窗和候选ID不改变。必要时复现旧工作流覆写被防止的独立负例。

**独立复审反馈格式**：审核者真实AI身份/准确版本（无法核实写UNVERIFIED）；固定SHA/原基线；实际运行的命令与退出码、源和代码SHA核验；每一条P1/P2`CLOSED/OPEN/PARTIAL/BLOCKED`与复现证据；结论`APPROVE/REQUEST_CHANGES/BLOCKED`仅针对本次source/audit/CI研发代码，**不包含**历史来源样本外、实盘信号盈利/自动下单/邮件或Mac部署放行。正式另一AI复审 **NOT_DONE**，之前Claude审核结论仍为 REQUEST_CHANGES，G4 UNKNOWN/G6 NO_GO与所有生产禁令不变。
