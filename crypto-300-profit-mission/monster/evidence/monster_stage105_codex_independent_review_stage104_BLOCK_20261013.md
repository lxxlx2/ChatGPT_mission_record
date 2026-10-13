Claude没额度了，6.1sol接手的

**审查结论：`BLOCK`。**

固定受审 commit：`8c318b601ebe1ab09d71d8bbafd6c1299fec8d4e`
仓库：`lxxlx2/ChatGPT_mission_record`，Monster PR #30 研究采集器范围。
审查主体：本次为 **Codex 独立审查**；实际 Claude 模型：`UNKNOWN`，本次没有调用 Claude。**这份报告不能被归档成“真实 Claude 聊天 APPROVE 回执”。**

本轮确实修复了原来的卸载失败误报，并加入了有效的八文件 Git 完整性检查和真实本地 Git 竞争测试。但完整性检查仍遗漏实际导入执行的依赖；另有一条安装失败路径会让回滚中途终止、留下此前成功加载的任务。两项都有固定源码证据和离线复现，因此目前不足以进入“再取得用户独立授权后考虑安装”的阶段。

**固定版本、读取范围与测试证据**

我在独立临时副本中检出指定 SHA，最终 HEAD 仍为上述完整 commit，受审副本 `git status --short` 为空。已逐项核对：
- 固定 commit 中的文件 blob；
- 本地原始文件计算出的 Git blob SHA；
- 全文审查包所列的 blob 与文件内容。

结果为 **13/13 一致**。审查包来自后续文档 commit `da7f403b101d567a811cd6eb364a1055f323b22a`，但下面的源码审查全部绑定到 `8c318b…`，没有用当前分支最新源码替代。[全文审查包](https://github.com/lxxlx2/ChatGPT_mission_record/blob/da7f403b101d567a811cd6eb364a1055f323b22a/crypto-300-profit-mission/monster/MONSTER_STAGE104_FULL_SOURCE_CLAUDE_REVIEW_BUNDLE_20261013.md)

以下为实际全文读取清单。表中脚本均位于 `crypto-300-profit-mission/local-agent/scripts/`；三份规则与设计文档均位于 `crypto-300-profit-mission/monster/`。

| # | 实际全文读取文件 | 行数 | Git blob 前缀 |
|---|---|---:|---|
| 1 | monster_v4_stage38_usdm_original_v4_1m_pilot.py | 299 | a26445dbb72a |
| 2 | monster_v4_stage80_dual_entry_core.py | 208 | 6ad6ef2a78d2 |
| 3 | monster_v4_stage91_forward_oos_replay_gate.py | 401 | 5ba64098cbc2 |
| 4 | monster_v4_stage97_one_shot_usdm_capture.py | 240 | 8839472ccd90 |
| 5 | monster_v4_stage99_mac_launchd_one_shot.py | 593 | 2e7b21ada4cc |
| 6 | monster_v4_stage102_claude_chat_review_gate.py | 223 | b76f08e4390d |
| 7 | test_monster_v4_stage99_mac_one_shot.py | 390 | 2008879343de |
| 8 | test_monster_v4_stage103_git_worktree.py | 159 | e04d6fe55e69 |
| 9 | monster_v4_stage99_external_ai_review.py | 22 | 429dac1b52de |
| 10 | .github/workflows/monster-stage99-mac-one-shot-capture-safety.yml | 58 | 99efdff70d35 |
| 11 | MONSTER_MODULE_DEVELOPMENT_RULES.md | 77 | 55668e29cac3 |
| 12 | MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md | 23 | 47d322c26425 |
| 13 | MONSTER_STAGE102_LOCAL_COLLECTION_CHAT_REVIEW_AND_PARALLEL_MODEL_BOUNDARY_20261013.md | 19 | 2e127cf4b0f7 |

**指定的13份文件未读项：无。** 另已全文读取第二次BLOCK归档、Stage103整改报告和Monster`AGENTS.md`。为检查导入链，额外读取了 `monster_v4_shadow.py` 与 `monster_v4_historical_replay.py` 的导入及初始化部分；没有将这两个额外文件声明为完整功能审查。

CI已通过GitHub API、两个job的步骤状态和日志核实：
- Run：`38375453893`
- `head_sha`：准确等于 `8c318b601ebe1ab09d71d8bbafd6c1299fec8d4e`
- macOS job `115222568008`：`success`
- Ubuntu job `115222568321`：`success`
- 两个平台日志均显示**22项安全测试和4项真实本地Git测试通过**，新增源码修改与fetch/push竞争测试均为`ok`。[准确SHA的CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38375453893)

我也在本地临时副本重跑了这 **26项测试和工作流中的5个离线自测，全部通过**。本地Python为`3.14.7`；CI配置为Python`3.12`。

**N-B1 / N-B2逐项判断**

| 原问题 | 本轮判断 | 证据与限制 |
|---|---|---|
| N-B1 launchd卸载失败后误报成功 | PASS，针对原误报问题 | `bootout()`检查非零返回码，随后检查`list`与`print`，只有核对通过才删除plist；回滚卸载失败会标记危险状态并抛错；`execute()`卸载失败会以`SystemExit(4)`强制失败。原来的无条件成功报告已修复。不过完整回滚仍有下面的N-B3阻塞。 |
| N-B2 运行时代码完整性不足 | FAIL，部分修复有效但未闭合执行依赖 | 八个列名文件的dirty检查、HEAD/review/worktree blob一致性及祖先关系确实存在；允许后续提交审查记录与授权文件的设计合理。问题是实际导入执行的两个依赖不在冻结清单中，且导入发生在门禁之前。 |

N-B1的通过属于源码与模拟测试结论。**没有执行用户真实Mac的launchctl卸载或回滚验收，不能据此声称真实服务已经被卸载。**

**阻塞项一：N-B2仍存在——未冻结的依赖在完整性门禁之前执行**

位置：
- Stage99第21–26行：顶层导入Stage97、Stage91。
- Stage91第18–23行：顶层导入Stage38、Stage80。
- Stage38第15–20行：顶层导入`monster_v4_shadow`、`monster_v4_historical_replay`。
- Stage102第25–34行：`REQUIRED_SOURCES`不包含上述两个依赖。
- Stage99第130–155行：完整性检查只覆盖回执列出的八文件。

触发条件：八个冻结文件保持原样，仅修改私有clone中的`monster_v4_historical_replay.py`，然后启动Stage99。Python会先执行该模块的顶层代码，之后才进入安装或运行门禁。

离线复现：在独立临时Git夹具中复制固定版本文件，建立明确标记为合成的review/authorization记录；只给遗漏依赖增加一个无副作用的顶层布尔标记。使用真实`validate_review()`、`validate_authorization()`和`assert_reviewed_runtime_source()`，没有mock这三个门禁。结果：
```
omitted_dependency_dirty: True
tampered_dependency_imported: True
complete_execution_path_verified: 8
```
这证明：**被修改的依赖已执行，门禁仍返回完整性通过。**夹具使用自己的测试commit；它不是目标commit的真实批准记录，也没有安装任务、访问Binance或推送公网Git。

最小修复方向：
- 让研究采集器依赖不再通过Stage38导入Shadow/历史回放模块；将所需窗口、时间或人口验证工具放入明确冻结的最小依赖中。
- 若保留这些导入，必须纳入完整执行依赖清单，并把验证放到这些依赖执行之前。仅增加两个路径、继续先导入后检查，仍不能阻止导入阶段副作用。
- 增加从新Python进程启动的离线测试：遗漏依赖发生变更时，必须在其顶层代码执行前拒绝。

**阻塞项二：N-B3——状态写入失败会中断剩余安装回滚**

位置：Stage99`install()`第284–299行，特别是回滚分支内第291、295行的`store_status()`。

触发条件：
1. 第一个窗口bootstrap成功，状态写入成功。
2. 第二个窗口bootstrap成功。
3. 第二个窗口写`SCHEDULE_INSTALLED`时发生磁盘满、I/O或权限错误，进入回滚。
4. 第二个窗口卸载后，再写回滚状态仍发生同一文件系统错误。
5. 这个`store_status()`异常没有被隔离，直接跳出回滚循环，**第一个已加载窗口没有得到卸载尝试**。

失败卸载分支也有同样问题：写`ROLLBACK_FAILED_SERVICE_STILL_LOADED`失败，会在继续处理其他窗口之前退出。

离线复现：对原始`install()`注入第二个窗口状态写入的`OSError(ENOSPC)`；launchctl和卸载动作仅用模拟调用记录，没有操作真实服务。结果：
```
raised: OSError 28
bootstrap_calls: 2
rollback_attempts: ['2026-10-28T06:00:00Z']
first_successfully_bootstrapped_job_never_rolled_back: True
```

影响：安装命令已经失败，但此前成功加载的任务可能继续保留并按时运行。这个错误不会再误报安装成功，却仍违反安装失败后逐个回滚本轮已创建服务的要求。

最小修复方向：让状态记录失败不能阻止其他服务的卸载。逐个完成卸载与核对，在内存中汇总卸载失败和记录失败，最后统一非零退出；无法写状态文件时至少向stderr输出具体窗口与错误。需要增加持续状态写入失败时仍尝试全部回滚的测试。

**其他检查结果与非阻塞问题**

- Git上传：PASS。临时worktree基于远端最新提交，只增加目标证据文件；同名不同字节拒绝覆盖；fetch/push之间远端前进时有限重试。真实本地Git测试验证原执行目录HEAD不变、远端新提交保留，没有主目录rebase或强推。
- Stage91/97：范围内PASS。交割合约带`_`可保留在人口中而不计入永续候选；必需字段缺失拒绝。Stage97使用独立`/time`前后校时、三段原始SHA、因果时间顺序和冻结窗口，不以`exchangeInfo.serverTime`校时。
- 授权门禁：结构检查PASS，来源真实性仍依赖人工流程。结构化`BLOCK`回执被拒绝；需要独立授权manifest和安装TTY指纹短语。哈希不证明Claude或用户身份，也不判断全文与人工填写verdict的语义一致性，不能代替真实归档核对。
- 旧Claude CLI：PASS。已替换为tombstone，没有可运行安装路径。
- 非阻塞P2：`uninstall()`缺少“已不存在”处理。它按三个窗口顺序调用严格`bootout()`，若前一个任务已自动卸载，非零返回会使整个卸载入口提前结束，后续仍存在的任务没有被处理。建议在确认目标已不存在后视为幂等完成，并继续处理其余目标；不能把任意bootout错误当作不存在。
- Frank检查只比较标签中含`frank`的只读集合，不能证明全部实际Frank标签或资源隔离。当前源码没有主动控制Frank的调用；真实共存仍未验收。

**最终：`BLOCK`。需要先闭合N-B2的导入执行依赖，并修复N-B3的回滚中断路径，再审查新的固定commit。用户独立安装授权仍为`NOT_GIVEN`；研究采集器不得安装，Monster模型部署及自动交易继续保持`NO_GO`。