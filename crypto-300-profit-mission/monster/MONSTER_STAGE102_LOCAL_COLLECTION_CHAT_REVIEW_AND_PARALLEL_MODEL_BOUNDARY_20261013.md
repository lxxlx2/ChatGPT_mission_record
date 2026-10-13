# Monster Stage102：按用户明确指令修复本地采集与独立Claude对话审查

记录日期：2026-10-13，Monster 原 PR #30。`MONSTER_STAGE99_USER_WORKFLOW_CORRECTION_CLAUDE_CHAT_AND_OOS_BOUNDARY_20261013.md`为前置规则。

## 不可逾越的执行权限

1. 用户截图中的全局自定义规则明确：**没有用户的明确授权，不得新增任何automation、后台监控、备用任务、删除已有任务或擅自改对话名**。此前曾擅自设定的ChatGPT定时任务已确认停用。本阶段仅**提交代码并在GitHub CI执行离线单次测试**，不能用“开发授权”代替Mac本地安装/启动授权。
2. 用户要求的采集是**本地** `launchd` **到点启动、保存官方USD-M原始时点行情/市场快照、将结果传原PR30 Git、执行后卸载**；不可擅改为ChatGPT自动化或GitHub定时云监控，更不能提前部署D0/D1/Frank生产或发真实邮件/做交易。
3. **研发主线不等待新数据**：Stage100/101等旧官方历史数据模型、收益和退出机制研究继续独立推进。新采集只辅助研究原始证据，不作为下一版本D1研发的阻塞条件。未来快照本身也不足以证明七日内上市变化/实际盘口成交或OOS通过。

## 实际完成该功能所需的闭环

- 冻结明确日程：2026-10-14、10-28、11-11 UTC05:48（曼谷12:48），只接收UTC05:45–06:00的官方响应；窗口错过不得补抓。三组任务各自无KeepAlive/RunAtLoad，完成/失败后卸载，不能无限每周运行。
- 继续复用Stage97的官方TLS `/fapi/v1/time → /fapi/v1/exchangeInfo → /fapi/v1/time`+SHA，原Git branch `research/monster-v4-local-discovery-20261010`，独立私有clone和标签，不碰Frank。成功以实际远端commit确认为准。网络或Git失败必须保留原始证据字节/sha，重试只上传旧文件，不能逾时再次采集。
- 不存在“用户Mac Claude CLI”。**禁止调用CLI Review作为安装前置**。真实独立Review在用户现有Claude聊天中完成：助手提交冻结代码与完整提示词，用户把真实审查回复发回，助手原样记录实际Claude评论、模型（若明确）、目标SHA、问题和修复后CI；未取得真实APPROVE则保持`NO_INSTALL`。在Git中加入只读 `chat_review_gate` 检查已归档真实review对应代码Git blobs的门槛；仅旧`monster_v4_stage99_external_ai_review.py`不再用于安装。
- CI必须覆盖macOS和Ubuntu：前后窗口、本地时区、真实只读Claude聊天评审文件缺失/变更、源SHA、重复运行、失败后证据/状态保留、重试不再抓、禁后台常驻、Frank无副作用、Git远端失败不报成功，整个测试不得触发真实`launchctl`或真实远端写操作。
- 与之前仓库规范相同，**代码审核通过且用户明确授权后**才提供会安装三个Mac launchd任务的命令。未审核通过时只提供Claude聊天Review提示词，禁止用“点击安装”绕开审查。

状态：`STAGE102_CODE_REVIEW_PENDING`；`CURRENT_GIT_PRODUCTION_UNCHANGED`；`MAC_INSTALL_NOT_AUTHORIZED`；`D1_HISTORY_R_AND_D_CONTINUES`；`OOS_NOT_DONE`；`D1_G3_REJECTED`。
