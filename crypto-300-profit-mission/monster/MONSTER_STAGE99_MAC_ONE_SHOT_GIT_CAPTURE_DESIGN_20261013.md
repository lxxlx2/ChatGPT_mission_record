# Monster Stage99：Mac launchd 三个冻结窗口的单次采集→Git PR#30→自动退出

状态：TECHNICAL_DESIGN_FROZEN_2026_10_13；Stage103 修订纠错补充。此为**研究原始证据采集工具**，不是 Monster D0/D1/D2 策略部署、Shadow、Mac常驻Daemon、Frank修改或交易/邮件。用户明确要求定时执行、自动传Git、完成后退出，代码由仓库统一交付并须其他AI独立Review。

## 约束与取舍

- 官方GitHub `schedule` 只读取仓库**默认分支**且可能延迟或丢弃任务；Monster原研究分支 PR #30 为 Draft，不能为采集把代码提前合并到main，也不能凭GitHub Actions排队及时性保证时点。因此选用用户Mac现有launchd **三个独立一次性 LaunchAgent**，不借用/重启Frank任何label。可选研究证据采集不视为已放行的Monster策略服务。
- 三个冻结窗口 `2026-10-14, 2026-10-28, 2026-11-11 06:00 UTC`。Mac各自按用户机器**本地时区**换算 `05:48 UTC` 调度（曼谷`12:48`）；真实HTTPS完成必须在对应 `05:45:00 <= t <= 06:00:00 UTC`；不满足时间/网络不伪造，不事后补抓。
- 使用独立目录 `~/.local/share/monster-stage99-source-capture/repo` 克隆**同一个** `lxxlx2/ChatGPT_mission_record` 及PR30分支；禁止操作用户常用本地repo/Frank/MonsterSQLite/邮箱。入口代码只能 `git` 提交采集结果到原`research/monster-v4-local-discovery-20261010`，不得push main、新建PR或覆盖已有raw历史证据。
- 定时器仅在指定日期启动一次`python3 ... runner run --window ...`，launchd plist `KeepAlive=false`、`RunAtLoad=false`、无WatchPaths/StartInterval；每个任务完成后清除自己的plist并卸载，不继续运行。三个窗口都用同一安装命令完成；不是独立交易/价格通知监控。Mac需保持开机、联网、唤醒；OS休眠或网络中断会使该次窗口`MISSED`，不能声称已采集。
- 每次在窗口内复用**Stage97原`capture_one`**：`/fapi/v1/time`→`/fapi/v1/exchangeInfo`→`/fapi/v1/time`，原始UTF8、SHA256、客户端时间、原始时点完整名单验证。成功后自动写 `crypto-300-profit-mission/monster/evidence/monster_stage97_point_in_time_usdm_YYYY-MM-DD_raw_https.json`，`git add/commit/push`至原PR30分支。远端已有同名不同内容必须拒绝覆盖。失败保存本机日志和状态供用户复核，不向Git写伪造成功或缺失填零。
- 唯一需要用户的操作是**review通过后执行一条zsh命令安装一次性调度**，GitHub远端push使用用户本机现有GitHub Git凭证；绝不要求用户贴token，也不在日志泄漏账号凭据。安装时检查macOS、git/Python3/launchctl、三次日期未来/权限、origin分支存在、独立目录安全，Mac本机时钟有合理UTC窗口约束；已过期的日期直接拒装并可明确改为只装未来日期，但不能将其标成成功。
- **纠正原错误方案（Stage103）**：用户一直只在Claude**普通对话**中进行独立AI Review，不使用任何本地Claude Code CLI。原`monster_v4_stage99_external_ai_review.py`中的可调用CLI/安装功能已经用无可用安装路径的tombstone替换，任何`review-install`均拒绝。用户把实际Claude审查全文发回，研发负责人如实留档并根据`BLOCK`修复，再运行macOS/Ubuntu真实CI；未经第二轮真实`APPROVE`且用户再单独明确授权，**禁止任何本地调度任务安装**。
- Stage102/103双重安装闸门：Claude审查回执绑定完整审查原文哈希、`reviewer_model`、`reviewed_commit`及全部8个执行/测试/工作流文件的Git blob（Stage38/80/91/97/99/102、集成单测、CI）；代码有变更旧审查自动失效。独立的`monster_stage103_explicit_user_local_install_authorization.json`必须在获得用户**明确独立授权**后才建立，记录精确原话、时间、窗口和对应review指纹；安装进程另外必须连接真实交互终端，并由用户现场完整输入绑定上述review/源码的确认短语。**Claude review本身不是授权，用户提交审查报告也不是授权；SHA和回执仅为完整性检查，无法密码学证明文字真正来自人或Claude**。
- 独立用户明确批准后才考虑执行Git内的本地安装入口；Mac必须有现有Git权限、Python3与launchctl、采集时开机并联网，**不需要**Claude CLI或向聊天泄漏任何token。安装先验证所有目标plist不存在，再按窗口独立bootstrap；若任一步失败，逆序只回滚自己本轮创建的服务；安装前后只读对照Frank已有launchd标签，不控制或重启Frank。
- 研究原始数据先通过本地独立目录保存，经独立的`/time`两次校时和`exchangeInfo`原始SHA核验，再上传至原PR30分支。**数据采集之前不访问GitHub远端网络**；Git暂时不可用也保留准确原始字节，稍后只重传原字节。Git上传在临时worktree中以远端最新HEAD新建证据commit，遇到远端新提交有限重试，不对采集程序的已审本地仓库执行`rebase`、`reset`或`force push`。
- `StartCalendarInterval`没有年份：这三个自卸载任务如果因Mac整日关机而错过，理论上可能在以后相同月日被launchd再次启动；运行时必须按精确冻结UTC窗口fail-close且禁止补抓，执行后删除自身plist。这个缺口不能声称三次准时成功。
- 异常优先级：真实性>采集成功率。记录`SCHEDULE_INSTALLED / CAPTURE_VALIDATED / GIT_PUSH_CONFIRMED / MISSED_WINDOW / AUTH_FAILED / SOURCE_FAILED / REVIEW_PENDING`，且`CAPTURE_VALIDATED`不得当成Git成功。GitHub原分支变化安全重试，不以reset覆盖他人提交。若窗口内已抓取有效原始证据但Git push失败，保留本机完整sha证据，允许事后**仅重试上传当时已保存的字节**，不得事后重新抓取。
- `launchd`定时仅保存起始快照，不证明窗口内新上架或停牌覆盖。Crypto身份、D0/D1效果、真实盘口与回报仍未验证。采集完整不等于`G0/G1/G4 PASS`。

### 研发阶段验收

`OTHER_AI_REVIEW=NOT_DONE`直至其他模型真实审查；`STAGE99_INSTALL=BLOCKED_UNTIL_REVIEW_AND_TESTS`；`D1_G3=REJECTED`；`MONSTER_DEPLOY=NO_GO`；`GMAIL=OFF`；`AUTOTRADE=NO_GO`；`FRANK_UNCHANGED`。
