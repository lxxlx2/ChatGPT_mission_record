# Monster Stage107：用户本地 macOS 一次性来源采集任务实际安装回执

记录日期：2026-10-13（Asia/Bangkok）；原 Monster Draft PR #30；**仅依据用户在本次聊天提供的真实终端输出记录**。开发端未直接进入用户Mac执行`launchctl print`，不能将以下回执作为已采集真实 Binance 数据的证明。

## 授权／审核链

- 冻结独立受审源码：`2f25f2b921a97ab864ced7a0bc93aab1c9e85169`，真实评审主体Codex、模型具体标识UNKNOWN，结论`APPROVE`，范围仅本地一次性 Binance USD-M 市场快照采集、Git上传、自卸载。
- 固定代码 [macOS+Ubuntu专项CI #38383381420](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38383381420)：2/2 `success`。
- [真实用户转交的Codex审查全文](monster_stage106_user_forwarded_codex_stage105_independent_APPROVE_20261013.md) 与 [审查回执JSON](monster_stage102_actual_claude_chat_independent_review.json)，均在原分支归档，且核查受审八份执行/测试/CI Git blob无变化。
- 用户在2026-10-13明确回复“批准”，范围为在自己Mac安装**三项指定本地一次性研究采集任务**；[独立用户安装授权记录](monster_stage103_explicit_user_local_install_authorization.json)。不授权新增ChatGPT自动化、后台替代任务、Monster实际策略/交易或Frank/Gmail改动。
- 用户在Mac执行了 Git clone、审核/授权门禁、TTY精确确认短语及`install`，终端返回`STAGE99_INSTALLED`，随后的`status`输出为三项`SCHEDULE_INSTALLED`。确认短语已被正确输入，回执**不**存储账户密钥、系统用户名或本地绝对私有目录。

## 用户实际终端记录（归纳关键字段，未伪造第二来源）

| window UTC | 本地曼谷调度 2026 | launchd label | 实际状态 |
|---|---|---|---|
| `2026-10-14T06:00:00Z` | 10月14日12:48 | `com.lxxlx2.monster.stage99.usdm.20261014` | `SCHEDULE_INSTALLED`、`launchd_plist_exists=true` |
| `2026-10-28T06:00:00Z` | 10月28日12:48 | `com.lxxlx2.monster.stage99.usdm.20261028` | `SCHEDULE_INSTALLED`、`launchd_plist_exists=true` |
| `2026-11-11T06:00:00Z` | 11月11日12:48 | `com.lxxlx2.monster.stage99.usdm.20261111` | `SCHEDULE_INSTALLED`、`launchd_plist_exists=true` |

用户`status`实际`written_utc`时间：分别为`2026-10-13T11:16:48.179012+00:00`、`2026-10-13T11:16:48.184397+00:00`和`2026-10-13T11:16:48.189491+00:00`。

所有三个状态皆记录`actual_trades=NONE`、`frank=UNCHANGED`、`gmail=OFF`、`monster=NO_GO`、`research_only=true`。这只是采集程序的自报状态；未直接独立比对Frank进程，也不据此断言采集数据已上传。

## 验收边界与后续核对

- **安装：用户本地终端证据 PASS**；`launchctl bootstrap`在用户实际安装中返回成功，否则`install()`会抛错和尝试回滚。但**尚未独立查询用户Mac `launchctl print`**。
- **Binance时点快照：NOT_DONE**；三个未来采集窗口均未在此回执中执行。仅从`SCHEDULE_INSTALLED`不得推出来源数据真实或上传完成。
- **Git上传：NOT_DONE**；待每个窗口后独立检查原PR分支下`crypto-300-profit-mission/monster/evidence/monster_stage97_point_in_time_usdm_YYYY-MM-DD_raw_https.json`、原始SHA、来源时钟和远端提交。只有对应`GIT_PUSH_CONFIRMED`且文件确实存在才能判PASS。
- Mac需在对应时点保持开机登录、具备Binance与GitHub连通和有效Git push认证。睡眠、离线及凭据失败可能错失`05:45–06:00 UTC`窗口；**禁止事后补抓并宣称时点正确**。
- 如果采集成功而Git推送失败，原始bytes/SHA保留在隔离clone，后续只允许针对已有原始文件做`retry-push`（需要用户再次执行相应命令，**未经额外明确授权不得新建自动重试任务**）；切勿重新访问Binance假装旧日期证据。
- 三项现有任务按设计执行后自卸载，失败时必须核实launchd实际卸载成功才写清理成功；不创建任何额外长期任务。
- 此操作仅增加 Git 中一份安装验收记录，**不**修改Stage105冻结审核源码或用户Mac任何服务。历史Monster D1建模研发独立继续，不必等待三个窗口结束。

状态：`USER_INSTALL_PERMISSION=YES`、`USER_MAC_INSTALL_TERMINAL_EVIDENCE=PASS`、`LAUNCHD_PRINT_INDEPENDENTLY_VERIFIED=NO`、`FIRST_OFFICIAL_SNAPSHOT=NOT_YET_VERIFIED`、`SOURCE_GIT_UPLOAD=NOT_YET_VERIFIED`、`MONSTER_PRODUCTION=NO_GO`、`FRANK_NOT_TOUCHED_BY_THIS_WORK`、`NEW_CHATGPT_AUTOMATIONS=NONE`。
