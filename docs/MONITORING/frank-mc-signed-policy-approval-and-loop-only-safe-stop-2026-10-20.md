# Frank Mission Control — 用户独立签名策略批准和仅停止 MC Loop 的发布保护

2026-10-20，状态 **DRAFT IMPLEMENTATION / PRODUCTION_NO_GO**。用户只授权新建 Draft 修复 PR、离线测试和独立复核，**未批准任何新策略字节/SHA、安装、发送通知或重启**。

本文件关联 [PR #128 集成候选](https://github.com/lxxlx2/ChatGPT_mission_record/pull/128)、[PR #126 部署准备](https://github.com/lxxlx2/ChatGPT_mission_record/pull/126) 和并行 Draft 的“跨策略遗留队列隔离”修复。两个 Draft 必须独立审核，再评估安全集成；当前 PR128 固定 SHA 继续不变。

## 目标与信任边界

之前 `APPROVED_POLICY_SHA256` 只是操作人输入的字符串，`live_delivery_policy_authorized()` 校验候选 JSON 与字符串相同，不能证明用户批准。**让 AI 把自算的 SHA 写进 GitHub 评论、JSON 或环境变量，依然不是用户授权。**

新设计采用**带外用户签名**的策略审批清单，记录以下精确字段：`schema_version=1`、`scope=FRANK_MC_DECISION_LOCAL_AND_GMAIL_ONLY`、`policy_sha256`（策略文件原始字节）、`integration_sha`（部署源码 Git commit）、`approved_by`、`approved_at`、`expires_at`、`deployment_approved=false`。对整个原始 JSON 文件使用独立私钥进行 RSA/SHA256 分离签名。只读公开验签密钥必须**预先由用户/管理员独立布置**在：

`/Library/Application Support/FrankMeme/release-approval-public-key.pem`

公钥和其直接父目录必须由 root 持有且不可被普通同组/其他用户写入；拒绝符号链接。**当前 PR 不生成签名密钥、不布置公钥、不保存私钥、不制造任何用户批准记录。** 用户签名私钥必须由用户独立保管且不得交给 AI、仓库、CI、生产服务账号。使用系统 `/usr/bin/openssl` 验签，不依赖可由代理篡改的 `PATH` 里找到的二进制。

只有全部满足，候选才能通过正常安装预检：

1. `FROZEN_APPROVED/true` 及既有完整保留期等策略硬门禁；
2. 用户签名清单验签成功、在批准期内，批准 SHA 与策略**实际文件字节**相同，批准代码 SHA 与实际 checkout HEAD 一致，并保证已追踪代码无未提交更改；
3. 签名范围只授权 **Mission Control 决策本地 + Gmail 通道**。冻结 V1 原信号通知不因此新增或取消权限；不能凭本批准做任何交易或指定默认投资金额；
4. 另有**单独部署/重启的明确用户授权**，现有安装脚本显式确认参数不能由“批准策略”自动推导。

`scripts/mission_meme_v1.py` 对请求的 `--live-delivery` 要求签名清单和签名文件，并基于实际 Git HEAD 而非用户自报 SHA 验证；安装脚本预检和安装后的 Loop 入口都验证。运行时如果审批过期，`MissionMemeService.cycle` 将 `delivery_allowed` 锁定为 False，不自行重新打开。独立直接调用类方法的测试夹具不等于生产签名授权；正式部署只能通过有签名核查的 CLI/runner。

**信任限制**：与生产服务有权修改所有源码和 launchd 的同 UID 攻击者，仍可通过替换程序逻辑绕过检查；root 锚点无法防范系统管理员本人主动篡改。此次的安全目标是阻止候选文件 SHA 自我批准、普通错误安装和过期批准继续投递，不把它宣传为对整台 Mac 已被攻陷的防护。

## 仅停 MC Loop 的安全路径

新工具 `scripts/mc_loop_only_safe_stop.py` 默认**只打印预检计划、不修改服务**。只有将来用户明确批准生产停机、Mac 上显式传入 `--apply` 并在本次操作环境设置 `CONFIRM_MC_LOOP_ONLY_STOP=1` 时，才按**唯一已核对的 loop LaunchAgent Label/Plist**执行：

- `launchctl disable gui/<uid>/com.<user>.frank-meme.loop`
- `launchctl bootout gui/<uid> <verified-loop-plist>`

两条命令只涉及 **MC Loop**，不调用原来会重启 Loop+Dashboard 的安装脚本，也不触碰 Frank V1 独立信号进程。**停止整个 MC Loop 同时会停止新增候选评估/状态刷新；Dashboard 仍可提供既有历史只读数据，但是 MC 内容将逐渐过时。** 此方案优先保留 V1 和 Dashboard 可用，绝不恢复带旧 `$30` 自动报价的策略。没有自动 restart/resume（恢复必须另外获得策略签名和部署授权）。脚本不是无副作用的“停止 Gmail 开关”，不能误用。

发布前需要单独 Mac 隔离仿真与独立人工核对 Agent plist、`launchctl disable`/bootout 的状态、Dashboard 不受影响、旧 PID 生命周期和 V1 真实健康记录；本 PR 不执行任何真实 launchctl。

## 验收及暂不批准的事项

- 在隔离 CI 或 Mac 私有文件运行 RSA 验签正反例：正确签名、错误策略 SHA、错误代码 SHA、过期/伪造签名、未批准范围、信任锚不安全；禁止直接以自算候选 SHA 代替签名；
- 使用假的 `subprocess.run` 验证 safe-stop 脚本只会对唯一 Loop label 与 plist 发出两条预期命令，遇到不匹配的路径/Agent 直接拒绝；
- 验证连续运行到批准过期后投递关闭，且不会因改动数据表而自动重新开启；
- 按最后通过的 PR128 基线运行回归，独立审核此 PR 的新增工具/签名代码/installer；**当前工作尚未批准生产操作**；
- 新签名批准记录对应的正式 LIVE 策略文件**尚不存在**；需要用户之后独立核对并签字。到时候必须区分：**策略签名批准** 与 **安装及重启批准**。

所有真实安装、停 Loop、重启、新 Gmail/本地通知、RPC/Jupiter 请求、交易或 PR 合并均继续 **NO_GO**。
