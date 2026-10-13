# Monster Stage105：供Codex或其他独立AI的固定SHA复审

原PR [#30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，锁定修复代码commit `2f25f2b921a97ab864ced7a0bc93aab1c9e85169`，不得用最新分支文档commit冒充受审代码。旧Codex独审结果[BLOCK](evidence/monster_stage105_codex_independent_review_stage104_BLOCK_20261013.md)，新版本未独立批准。用户无Claude CLI，也不需要Claude额度。本文件可直接在Codex/其他AI对话中引用。

[完整12份固定源码及测试、Git blob SHA和开发规则（单文件，避免GitHub 503）](MONSTER_STAGE105_FROZEN_REVIEW_FULL_SOURCE_20261013.md)；[Stage105两项BLOCK修复与实测CI](MONSTER_STAGE105_CODEX_BLOCK_IMPORT_ROLLBACK_REMEDIATION_20261013.md)；[macOS+Ubuntu完全对齐此源码commit的CI #38383381420](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38383381420)。

## 可直接复制给独立Codex/AI的任务

请独立审查`lxxlx2/ChatGPT_mission_record`原Monster PR #30，**准确固定代码commit `2f25f2b921a97ab864ced7a0bc93aab1c9e85169`**。只审本地macOS一次性官方Binance USD-M市场快照采集器→Git隔离上传→执行后卸载，不涉及真实交易、Frank生产、邮箱、模型阈值、任何ChatGPT automation或用户Mac任务安装。绝对禁止执行`install`、`launchctl bootstrap`或`run`真实市场采集。

你上次在旧SHA`8c318b…`对采集器判`BLOCK`，给出两项实证阻塞：

**N-B2，启动导入未审依赖**：先读旧BLOCK报告，再看新源码`monster_v4_stage105_capture_universe_core.py`、Stage97、Stage99、Stage102审查门禁、Stage91研究回放。核实Stage99/97实际顶层导入仅到Stage105+标准库；不会加载Stage91→Stage38→Shadow/历史回放。验证Stage91研究仍能使用统一Stage105`freeze_universe()`且不反向导入到采集进程；Gate`REQUIRED_SOURCES`应包含所有**实际被采集器执行的**Python文件和CI/测试，Codex/Claude真实用户提交的BLOCK不能伪造为APPROVE。核实新`test_monster_v4_stage105_capture_import_isolation.py`确实启动全新Python进程，植入导入立即写磁盘的危险历史模块，确认未触发；真实本地Git测试对Stage105进行dirty和未经批准commit检测。检查是否仍有其他**实际启动导入期副作用**遗漏，不要只数文件名。

**N-B3，回滚状态文件磁盘满**：重点读Stage99`install()` `except BaseException as install_error`分支。用户真实`launchctl`可能已有1、2个服务加载成功，接着`store_status`出现`ENOSPC`且回滚记录继续失败；必须仍尝试所有已创建服务的`bootout`并检查`launchctl list+print`、不能写状态则输出stderr、内存汇总失败、最后非零抛错。检查`test_stage105_enospc_status_write_does_not_interrupt_other_bootouts`和`test_stage105_disk_full_and_one_failed_unload_still_attempts_every_service`触发场景是否真实，明确上次离线复现的问题是否闭合。不得把模拟launchctl说成用户真实Mac已验收。

附带复核：原B1独立用户逐项明确安装授权、真实Codex/Claude外部聊天APPROVE才可能进入用户另行授权、指纹与TTY交互、运行期源码blob验证；B4交割合约含下划线人口过滤与官方`/time`记录；Git远端竞争临时worktree、无rebase/force、同名不同内容拒绝覆盖；`uninstall()`幂等性等可列为非阻塞，**但不准以边界优化无限阻止Monster历史模型主线**。

审查证据：12份完整原文（应逐个列出实际读到的文件，若有受阻明确写`UNVERIFIABLE`）；GitHub Action [#38383381420](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38383381420)，两平台日志是24项隔离测试＋4项真实本地Git测试＋1项新进程导入攻击测试，CI仅离线，不等于实盘/真Mac。

**输出必须包含**：`APPROVE`或`BLOCK`；审查的实际AI产品/模型（无法核实写UNKNOWN，**不得冒称Claude**）；完整40位审查SHA；已读及未读源码；N-B2与N-B3分别PASS/FAIL及源码证据；其他真正安全阻塞问题的函数/触发条件/后果/最小修复；非阻塞建议；测试真实性区别；是否足以进入**“由用户之后另行明确批准，才在Mac安装仅研究采集器”**的阶段。独立审查结论**永远不是安装授权**。本轮只做审查，不修改仓库、不安装任何定时任务、不发交易或邮件。

## 当前门禁（审查前）

`PR_DRAFT=YES`；`STAGE105_CI=PASS`；`CODEX_LAST_REVIEW=BLOCK_OLD_SHA`；`STAGE105_EXTERNAL_REVIEW=NOT_DONE`；`USER_INSTALL_AUTHORIZATION=NOT_GIVEN`；`MAC_SOURCE_COLLECTOR_INSTALLED=NO`；`MONSTER_PRODUCTION=NO_GO`；`FRANK_UNCHANGED`；`HISTORICAL_D1_RESEARCH_CONTINUES_INDEPENDENTLY`。
