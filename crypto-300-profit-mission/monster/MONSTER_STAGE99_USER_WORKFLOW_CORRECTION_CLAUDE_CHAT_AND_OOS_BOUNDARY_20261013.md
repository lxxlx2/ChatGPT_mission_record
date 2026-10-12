# Monster Stage99 用户使用方式纠正：Claude 对话审查，不依赖本地Claude CLI

时间：2026-10-13，Asia/Bangkok。原Monster PR #30。此纠正覆盖所有旧报告里“用户已登录Claude Code CLI”“直接运行 review-install”的操作建议。

## 纠正事实

- 用户明确使用 **Claude 对话界面**，从未声明在Mac安装、使用或登录`claude` CLI。不得要求用户安装CLI或凭CLI存在作为前瞻数据采集的先决条件。
- 原Stage99`monster_v4_stage99_external_ai_review.py review-install`路径 **USER_WORKFLOW_WITHDRAWN / DO_NOT_RUN**，尚未产生其他AI真实审查。代码仓库保留供审计和后续修正，但不得在用户说明或交付中把这条命令写成可用的当前安装方案。
- 正确的其他AI审查流程应为：助手先稳定Git分支代码与CI→提供同一Git SHA和文件、可复制的自包含审查提示词→用户在已经使用的Claude**对话**中提供文件/PR审查→用户把完整真实Claude审查输出发回对话→助手保存源评论和reviewer/版本/sha/问题→修复并重测→只有真实审查已经通过且与代码版本一致，才重新设计不依赖Claude本机CLI的安装命令。不能把助手自查、Mock、GitHub reviewer request或CI算作独立Claude Review。
- 研究原始快照采集是一种**证据收集**，不是Monster D0/D1策略服务部署。需要点时市场清单因为历史900币固定人口可能由事后档案构建，无法还原某个开始时点真实所有可交易Crypto；这阻断**严格完整市场G0验证**，并不阻断使用已经保存的官方历史行情继续研发D1。
- 冻结三组（2026-10-14/10-28/11-11 UTC06开始）是为了独立OOS复验，不代表模型研发只能等到11月。每个窗口七天，D1后72h回报需要再等三天及官方发布；各窗具备完整来源后可独立研究，不能拿未完成窗口冒充已验证。
- 只采集一个开窗`exchangeInfo`快照**不等于**七天完整人口：窗口内上市、退市、合约分类仍缺证据。即使三个快照齐全，也不能自动使D1平均7.26条/日、峰值52条/日这一G3不合格事实消失。
- **当前主线优先级：继续历史源研究+修复D1利润/噪声，同时并行获得真正时点市场名单与后续价格、盘口证据**。不得为了三次时点采集而停止模型设计和回测；数据采集完成不是改进D1的前置条件。
- Mac用户现在不需要运行旧命令、下载散落脚本或创建后台任务。若10月14日窗口前无法完成真实其他AI审查及正确单次采集安装，必须标`WINDOW_20261014_POINT_IN_TIME_UNIVERSE_NOT_CAPTURED`，不能补抓，也不能称全市场OOS通过；仍可正常推进历史研发和后两窗口。

状态：`STAGE99_CI_ENGINEERING=PASS`、`OTHER_AI_CHAT_REVIEW=NOT_DONE`、`STAGE99_CORRECT_NON_CLI_INSTALLER=NOT_DONE`、`USER_MAC_INSTALL=NOT_DONE`、`FUTURE_SNAPSHOT=NOT_DONE`、`D1_G3=REJECTED_EXPOSED`、`MONSTER_DEPLOYMENT=NO_GO`、`GMAIL=OFF`、`AUTOTRADE=NO_GO`、`FRANK=UNCHANGED`。


## 2026-10-13 二次更新：用户明确采集必须后台化，主线立即继续历史建模

按用户新指示，已另行创建**三次定时运行后自动结束的ChatGPT后台任务**，不再依赖Mac LaunchAgent或Claude CLI。2026-10-14、2026-10-28、2026-11-11曼谷时间12:48，尝试通过GitHub连接器向本Monster PR30分支提交一次性采集request，commit带`[MONSTER_USDM_CAPTURE]`，触发已有Stage97 GitHub Actions使用官方Binance USD-M `/fapi/v1/time→/fapi/v1/exchangeInfo→/fapi/v1/time`采真实原始数据并推送原始证据。每次必须核验真实远端Git文件、SHA和实际CI；延迟到窗口外、权限失败或官方接口失败，一律标`MISSED`，绝不补抓或伪造。`TASK_SCHEDULED` ≠ `CAPTURE_COMPLETED`。该方案不安装任何用户Mac进程、没有持久化交易/邮件权限，真实CI执行与采集结果需要届时核实。

**优先级改变：历史Monster模型是MAIN，未来市场名单采集是SIDE_TASK**。Stage100已经用先前305条官方历史D1数据建立确定性训练/按时间递进四折模型，真实CI成功且候选`REJECTED`；Stage101正使用同批官方1m因果重放检验不同退出路径。**任何一个未来窗口还未成熟都不能阻塞这些旧数据研究、策略/技术设计、开发、真实历史回测和其他AI审查。** 未部署生产Monster，Frank不变。

原Mac `review-install` 的撤回继续有效，用户不需要运行旧命令。其他AI在正式模型上线前仍必须真实通过，不允许将后台采集任务当成其他AI审查或生产模型部署。
