# Monster Stage104：Claude 聊天第三次独立代码审查请求

**本文件只是独立代码审查输入，不是用户安装许可、也不是已通过结论。** 第二次Claude Haiku 5.5判`BLOCK`，目标旧代码`27c2c839d83dac11d1664d0fb6c9691844d0ca9a`。本轮修复锁定代码 `8c318b601ebe1ab09d71d8bbafd6c1299fec8d4e`；仅在修复后另提交审查文件。**实际 macOS+Ubuntu 专项CI对该代码SHA的运行**： [#38375453893](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38375453893)，两个Job都成功。不要引用旧CI #38372685819 证明本版。

上次审查因为 GitHub blob 页面503导致Stage102/38/80、测试等没有读取。本轮附[**13个文件全文+Git blob SHA单一完整审查包**](MONSTER_STAGE104_FULL_SOURCE_CLAUDE_REVIEW_BUNDLE_20261013.md)，是基于固定受审源码pin由GitHub connector逐个读取后原样串接，可在Claude聊天中一次提供全文，不依赖逐页浏览成功。也可以访问 [原Git SHA的审查包](https://github.com/lxxlx2/ChatGPT_mission_record/blob/da7f403b101d567a811cd6eb364a1055f323b22a/crypto-300-profit-mission/monster/MONSTER_STAGE104_FULL_SOURCE_CLAUDE_REVIEW_BUNDLE_20261013.md)。如任何文件仍未能全文查看，请明确写`UNVERIFIABLE`，不要推断。

## 给Claude普通对话的自包含提示词

请审查`lxxlx2/ChatGPT_mission_record`，严格锁定代码commit `8c318b601ebe1ab09d71d8bbafd6c1299fec8d4e`、原 Monster Draft PR #30。目标是用户明确要求的**本地macOS launchd一次性只读Binance USD-M开窗市场名单采集→原PR分支上传Git→自动退出**，**不是**策略交易、Frank生产服务、ChatGPT自动化或其他后台长期监控。用户不使用Claude CLI，未经用户之后逐项明确授权绝不能安装任何Mac定时任务。

请先阅读：

1. [第二轮实际Claude Haiku 5.5 `BLOCK`审查**全文**](https://github.com/lxxlx2/ChatGPT_mission_record/blob/8c318b601ebe1ab09d71d8bbafd6c1299fec8d4e/crypto-300-profit-mission/monster/evidence/monster_stage104_external_claude_haiku55_stage103_review_BLOCK_20261013.md)；
2. [所有13份必读执行源码、测试、工作流及开发规则的**完整原文**](https://github.com/lxxlx2/ChatGPT_mission_record/blob/da7f403b101d567a811cd6eb364a1055f323b22a/crypto-300-profit-mission/monster/MONSTER_STAGE104_FULL_SOURCE_CLAUDE_REVIEW_BUNDLE_20261013.md)；
3. [Stage103前一次整改报告](https://github.com/lxxlx2/ChatGPT_mission_record/blob/8c318b601ebe1ab09d71d8bbafd6c1299fec8d4e/crypto-300-profit-mission/monster/MONSTER_STAGE103_CLAUDE_BLOCK_REMEDIATION_REAL_CI_AND_REVIEW_GATE_20261013.md)；
4. [本次准确代码SHA的macOS/Ubuntu CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38375453893)。

本轮必须优先核对上次两项`BLOCK`：

**N-B1，安装rollback安全**：Stage99 `bootout()`现在调用launchctl bootout（非零/超时必须报错）、`assert_unloaded()`通过 `launchctl list` 全量标签和 `launchctl print gui/<uid>/<label>`二次核对后才删plist；`install()`安装任何一步失败，逐个回滚。若不能证明服务确已卸载，应保留其plist、标`ROLLBACK_FAILED_SERVICE_STILL_LOADED`并抛出非零错误。请检查既定输出是否会对失败状态冒充安全；`execute()`自身卸载失败应报告`AUTO_UNLOAD_FAILED_SERVICE_MAY_REMAIN`并强制非零退出。需要指出有无法证明完全清理的真实Mac异常路径。

**N-B2，审核后源码执行完整性**：Stage99`assert_reviewed_runtime_source()`新增交叉核对**真实回执+用户独立授权**、`reviewed_commit`祖先链、当前工作区8个REQUIRED_SOURCES文件是否dirty、每个文件`HEAD:path`blob与`reviewed_commit:path`blob及工作区`hash-object`是否都相同。任何修改拒绝执行；但**不能要求HEAD严格等于reviewed_commit**，因为正式review记录和用户单独授权文件是要在审过代码之后提交进Git的，若直接要求相等，系统合法路径将永远无法安装。正确条件是review commit在当前HEAD祖先链上+八个冻结源码blob完全相同。请检查实际代码是否遵守，是否有通过git status或未跟踪文件绕过路径。

其次关注回归：
- 从原本就已经`BLOCK`的Claude回复**不能**自动转成APPROVE；Stage102/103门禁的`validate_authorization`严格依赖下一轮真实Claude聊天`APPROVE`、全部受审执行依赖Git blob、独立用户授权manifest，以及现场TTY输入审查指纹绑定的确认短语。不要把SHA自证当作实际Claude模型身份的密码学证据。
- Stage91处理交割合约`BTCUSDT_261225`、不完整记录与时间窗；Stage97三段官方HTTPS原始SHA与官方单独时间接口，而不是exchangeInfo.serverTime校时。
- Git上传是临时worktree、不做主执行目录rebase、保存旧证据，不允许强推main或覆盖同名不同源的历史证据；新真实本地Git集成覆盖远端就在fetch/push之间前进的竞态。
- 安装前检查所有plist，不可部分安装；Frank只读标签对比，不得控制Frank；CI只模拟launchctl不是用户真实Mac。macOS/Ubuntu全部测试在固定SHA成功，不代表真Binance采集已经完成。
- 本地Claude CLI遗留代码已替换为不可运行的tombstone。研究采集辅助任务不能阻断妖币D1历史数据建模。
- 对任何新的安全/可用性阻塞问题如实判`BLOCK`，提供源码位置、触发场景和可复现方式；不要用不必要的边界优化无限延期，但已明确授权/卸载/真实数据完整性必须有充分证据。

**请完整输出**：`APPROVE`或`BLOCK`；实际Claude模型（不能确定填UNKNOWN）；目标完整40位commit；实际阅读的13个文件及未读文件，不能简单声明“已阅”；N-B1/N-B2逐项PASS/FAIL；其他缺陷含文件函数/触发条件/影响/最小修复；项目规则的权限边界；实际CI与真实Mac运行区分；结论仅说明是否可进入“再取得用户独立授权后考虑仅研究采集器安装”的阶段。**不要修改仓库、不要安装任何定时任务、不要运行公网请求或本地交易。**

审查后请向用户提供完整原始最终报告，由本ChatGPT研发负责人归档并修改，**用户粘贴Claude审查不是本机安装许可**。

截至该材料：`CURRENT_OTHER_AI=BLOCK_FROM_SECOND_REVIEW`、`THIRD_INDEPENDENT_REVIEW=NOT_DONE`、`USER_LOCAL_INSTALL_PERMISSION=NOT_GIVEN`、`NO_NEW_AUTOMATION`、`MAC_NOT_INSTALLED`、`MONSTER_MODEL_NO_GO`。
