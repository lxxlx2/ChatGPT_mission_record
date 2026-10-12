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
