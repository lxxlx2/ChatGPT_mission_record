# Monster Stage102 — 给 Claude **普通对话**的独立代码 Review 请求

**本文件是审查材料，不是已通过审查的声明，也不安装Mac定时任务。** 审查目标版本：`fab11d34451388808c5045118f933d542c77ecbe`，原 GitHub PR [#30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，仓库 `lxxlx2/ChatGPT_mission_record`，分支 `research/monster-v4-local-discovery-20261010`。此版本已在 [Stage99双系统专项CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38325534940) 中通过离线测试，CI不等于独立审查。

## 给Claude的完整提示词（可直接复制进Claude聊天）

你是**另一个独立AI代码审查者**，不是作者。请审查GitHub仓库 `lxxlx2/ChatGPT_mission_record` 的 Monster **本地研究原始行情采集器**，锁定 commit `fab11d34451388808c5045118f933d542c77ecbe`。它不是Monster策略交易/预测的生产部署，禁止触碰Frank、邮箱和交易。用户不使用Claude Code CLI，**只使用当前Claude对话**；不得要求用户下载或执行其他CLI。要求完整读取下列GitHub代码及开发规范（若无法访问文件，请明确报告无法审查、不要假装通过）：

1. [Stage99本地 launchd 采集/上传/自动退出核心](https://github.com/lxxlx2/ChatGPT_mission_record/blob/fab11d34451388808c5045118f933d542c77ecbe/crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py)
2. [Stage97 Binance官方HTTPS时点来源采集器](https://github.com/lxxlx2/ChatGPT_mission_record/blob/fab11d34451388808c5045118f933d542c77ecbe/crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py)
3. [Stage102 Claude聊天版独立审查记录安装关口](https://github.com/lxxlx2/ChatGPT_mission_record/blob/fab11d34451388808c5045118f933d542c77ecbe/crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py)
4. [Stage99所有隔离单测](https://github.com/lxxlx2/ChatGPT_mission_record/blob/fab11d34451388808c5045118f933d542c77ecbe/crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py)
5. [Stage99 macOS/Ubuntu GitHub CI](https://github.com/lxxlx2/ChatGPT_mission_record/blob/fab11d34451388808c5045118f933d542c77ecbe/.github/workflows/monster-stage99-mac-one-shot-capture-safety.yml)
6. [Stage91冻结日期与Crypto身份限制](https://github.com/lxxlx2/ChatGPT_mission_record/blob/fab11d34451388808c5045118f933d542c77ecbe/crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py)
7. [Stage99设计](https://github.com/lxxlx2/ChatGPT_mission_record/blob/fab11d34451388808c5045118f933d542c77ecbe/crypto-300-profit-mission/monster/MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md)
8. [Stage102纠正与权限规则](https://github.com/lxxlx2/ChatGPT_mission_record/blob/fab11d34451388808c5045118f933d542c77ecbe/crypto-300-profit-mission/monster/MONSTER_STAGE102_LOCAL_COLLECTION_CHAT_REVIEW_AND_PARALLEL_MODEL_BOUNDARY_20261013.md)
9. [Monster模块长期规范](https://github.com/lxxlx2/ChatGPT_mission_record/blob/fab11d34451388808c5045118f933d542c77ecbe/crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md)
10. [遗留错误的Claude CLI入口，确认安装路径已切断](https://github.com/lxxlx2/ChatGPT_mission_record/blob/fab11d34451388808c5045118f933d542c77ecbe/crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_external_ai_review.py)

必须实际审查以下要点：

- **时间**：三组固定UTC 2026-10-14/10-28/11-11 05:48 单次Mac启动，本地时区转换正确；启动/HTTP结束若超过05:45–06:00严格失败；睡眠、错过时间不能伪造、不能补抓；launchd执行后卸载/不残留每年重复工作。
- **原始官方证据**：使用真实Binance USD-M `/fapi/v1/time → /fapi/v1/exchangeInfo → /fapi/v1/time` 和原始JSON SHA；`exchangeInfo.serverTime`不能作为校准时间。缺包、重复symbol、时钟漂移、假来源和数据不完整如何拒绝。
- **Git正确性**：只提交原 `research/monster-v4-local-discovery-20261010` 分支，独立 Mac clone，凭证不出日志，不得强推/main/覆盖其他内容，成功状态必须以真实远端push为依据。尤其检查**push失败但原始数据已采集**时本地SHA保留、第二次不再采官方旧时点，只允许按SHA推送原始文件。
- **独立 Review**：Mac安装必须依赖用户在Claude对话的**真实完整审查内容**、记录到Git后的代码SHA匹配；本地不依赖Claude CLI；用户未明确授权之前不得安装/创建任何定时任务。能否通过伪造测试或旧review绕过？
- **项目主线**：证据采集是非交易研发旁支，不能阻断现有旧数据D1回测，不能修改Frank、生产邮件/交易、Monster模型阈值或宣称OOS通过。
- **测试可信度**：区分合成测试、真正Mac隔离测试与真正交易所网络请求；不因CI绿灯就判断真实时点采集已成功。

严格按以下格式返回（中文），不要只写“LGTM”：

**Review结果**：`APPROVE` 或 `BLOCK`。
**审查主体/模型**：准确写你实际使用的Claude模型；无法确认写`UNKNOWN`。
**目标commit**：完整 SHA。
**实际读取文件**：列出完整Git路径；没读到要注明。
**阻塞问题**：逐项包含文件、函数/行号、触发条件、后果和可复现思路；没有则写“无”。
**非阻塞问题**：含原因和优先级。
**回归检查要求**：指出最重要的真实Mac和无网络场景。
**结论与允许行为**：审查是否足以进入“**经用户再次明确批准后在Mac安装仅研究数据采集器**”阶段，明确不是Monster策略部署批准。

禁止修改 Git，禁止装任务，禁止声称已经执行Mac定时或获取未来数据。若有阻塞问题请判 BLOCK，不得以未来再修代替拒绝。

## 我收到Claude真实报告后怎么做

将Claude在**对话中实际生成的完整回复**送回当前ChatGPT聊天；由当前研发负责人做纠错/修复/源blob锁定、再次跑双系统CI，并把真实审查逐字留存原PR#30，构造Stage102结构化审查回执。只有`APPROVE`且源码SHA一致，才由用户另外明确批准在本机安装本地定时采集；**本文件不能自行批准或安装**。

**审核前状态：**`OTHER_AI_REVIEW=NOT_DONE`、`MAC_INSTALL=NOT_DONE`、`SCHEDULE=NOT_INSTALLED`、`AUTOMATIONS=OFF`、`MONSTER_MODEL_DEPLOYMENT=NO_GO`。
