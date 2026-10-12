# Monster Stage99：一条命令真实其他AI Review → 三个固定窗口自动采集 → Git PR30 → 自动卸载

日期：2026-10-13（Asia/Bangkok）。原唯一 Monster Draft PR #30。本阶段仅为前瞻研究证据采集工具，不是 Monster 模型部署/交易/邮箱发送；Frank与已有生产进程不变。

## 冻结执行方案与实际工程结果

- 先独立设计并提交 [Stage99 技术合同](MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md)，再提交代码、测试和CI。
- GitHub Actions scheduled workflow在默认分支执行且可延迟/丢失任务；原 Monster 代码位于独立 Draft PR30 分支，因此不能为获取时点证据提前合并，也不能假设CI准点排队。采用**用户Mac本地launchd仅一次触发的三个独立研究证据采集任务**，每个完成或失败后卸载自己的plist，未启动常驻策略服务。
- [自动一次性采集+Git push+异常留存入口](../local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py)。源时刻固定`2026-10-14`、`2026-10-28`、`2026-11-11 05:48 UTC`（曼谷当日12:48）。每次仅在对应的`05:45–06:00 UTC`合法时段请求官方USD-M，用已核对的[Stage97`/time → /exchangeInfo → /time`源码](../local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py)采原始UTF8、官方时钟、SHA和市场全量符号信息。写到`monster/evidence/monster_stage97_point_in_time_usdm_YYYY-MM-DD_raw_https.json`并只推送原PR30分支。提前/已过期/网络错误/错时均不伪造，曾成功采集而Git push失败保留真实原始bytes，支持`retry-push`只把已有证据重传，绝不逾时重新抓历史数据。
- 本地隔离仓库：`~/.local/share/monster-stage99-source-capture/repo`；任务名`com.lxxlx2.monster.stage99.usdm.YYYYMMDD`，只修改这些自己的plist、隔离clone与状态日志；不修改其他工作树、不重启Frank、不给用户默认交易金额、不操作Monster正式消息/数据库/端口。运行完成时状态至少区分`GIT_PUSH_CONFIRMED`和`SOURCE_FAILED_NO_BACKFILL`、`MISSED_WINDOW_NO_BACKFILL`、`CAPTURE_VALIDATED_GIT_PUSH_PENDING`，不能把SHA核对当作Git成功。
- [真实其他AI Review+安装硬关口](../local-agent/scripts/monster_v4_stage99_external_ai_review.py)：Mac上先由用户已登录的**Claude Code CLI实际非交互只读审查**全部Stage99/97核心源码、测试、协议及仓库规则，要求输出完整结构化审查证据、reviewed_files和至少3条验证证据。审查结果即使`BLOCK`也保留在Git；只有`APPROVE`且无阻塞项、审查后源码Git blobs未变化、能成功把**真实review回执**推到原PR30分支时才调用`install()`。任何CLI无效、未登录、推送失败或审查无效均 **fail-closed，不安装**。旧review若被更新则另存有原SHA后缀的归档，防止覆盖失败记录。
- GitHub Copilot自动审查请求通过连接器提交后，GitHub未形成真实请求/审查记录。因此不能将其当作第二模型Review，更不能将自身检查/CI称为其他AI Review通过。**本对话内的真实其他AI review尚未发生**，必须用户Mac实际调用Claude后才能解除自动采集安装门槛。

## 实际自动化测试

[Stage99 macOS/Ubuntu GitHub CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38321347318) **2/2 SUCCESS**。真实GitHub runner在两个系统上完成：
- 不联网的Stage97官方时间与SHA合成数据回归。
- Stage99三窗口日期/本地时区换算及launchd plist独立一次性结构，无KeepAlive/RunAtLoad。
- 未获得第二AI APPROVE时**真实安装入口必须拒绝**。
- 模拟Mac成功安装3个单独plist、状态写入、停用后只删除自己的3个service。
- 模拟成功采集与一次Git push、重复请求幂等、假时间/源失败、逾时后禁止重新抓、Git push失败保留原始SHA、仅重试已有原始bytes、篡改原始证据后禁止上传。
- 真实Claude CLI未在CI中被调用；假的Claude模型回执**不可能被计算成review APPROVE**。

CI工程成功只是**测试**，不代表用户Mac已安装、明天真实官方名单已上传或完整Crypto-only G0符合验收。真正独立Claude审查和原Mac安装仍取决于用户首次主动运行仓库命令。用户的Mac必须保持开机、已登录、可联网；睡眠或Git凭据失效时该窗口可错过，严禁事后改时间重抓。

## 用户操作与审核状态

安装前提：macOS、Python3、Git凭据、**Claude Code CLI已安装且登录Claude帐号**。一次Git clone独立仓库并运行`.../monster_v4_stage99_external_ai_review.py review-install`；先其他AI review并push Git，**只有无阻塞审查才自动创建launchd任务**。不需要用户下载散乱脚本或上传本机文件，不要求密钥发给聊天。

全模型闸门仍保持：`STAGE99_CODE_CI=PASS_UBUNTU_MACOS`；`STAGE99_TRUE_OTHER_AI_REVIEW=NOT_DONE_UNTIL_REAL_CLAUDE_CLI_RUN`；`STAGE99_INSTALLED_ON_USER_MAC=NOT_DONE`；`STAGE97_OFFICIAL_FUTURE_CAPTURE=NOT_DONE`；`G0_INTRAWINDOW_LISTINGS=NOT_DONE`；`D1_G3=REJECTED_EXPOSED`；`OOS=NOT_DONE`；`MONSTER_MODEL_DEPLOY=NO_GO`；`GMAIL=OFF`；`AUTOTRADE=NO_GO`；`FRANK=UNCHANGED`。
