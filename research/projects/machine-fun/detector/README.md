# Machine.fun 首发代币独立检测器

Status (2026-10-29): 独立源码已实现，18/18 本地测试通过（含本机回环 WS）；真实 WebSocket、Mac 通知投递及长期覆盖未经验证；未安装、未启用常驻任务。

本工具完全独立，不导入、不修改、不重启 Frank、Monster、Mission Control 或原有生产数据库、LaunchAgent。只处理 Machine.fun 已知的 Raydium LaunchLab PlatformConfig 下新币初始化事件，不绑定 SXTH。**新独立运行入口 `machine_fun_runtime.py` 会只读复用 Frank 的 Alchemy RPC 与 Gmail OAuth；不读写 Frank 生产 SQLite、不重启 Frank 进程。**

## 检测范围

- Solana WebSocket logsSubscribe，单地址：3hVbfgB77tL1qDKhtMQoe4Gv7qPN2dGmKpD2KxWP2sPb。
- 对成功交易用 HTTP getTransaction(encoding=json, maxSupportedTransactionVersion=1) 解码顶层及 CPI，校验 Raydium LaunchLab 真正的 InitializeV2 或 InitializeWithToken2022，精确核对 PlatformConfig。
- 提取 Mint、Pool、Creator、Payer、Quote Mint、Slot、交易签名。忽略失败交易、普通 Swap、其他平台和重复事件。
- SQLite Journal 持久化状态，断线后按上次 checkpoint 从此地址分页回填。发生分页缺口时保留缺口证据，不声称覆盖完整。
- 输出 MACHINE_FUN_CHAIN_CANDIDATE JSON。新增的 `machine_launch_gmail.py` 只给真正的链上新发行候选发送事件邮件：用旧 OAuth 刷新短期 access token（不写回原 OAuth 文件），并复用 Frank 现有收件邮箱；发送前把可能有外部副作用的行为固化为 `SEND_UNCERTAIN`，发生超时/中断不盲目补发，后续通过 Gmail Sent 搜索和邮件完整内容读回确认。邮件的 Gmail SENT_VERIFIED 只表示 Google 已经接受到 Sent，不表示收件人读到。可选 --notify-local 同时发 macOS 桌面通知。

链上候选不等于 Machine.fun 官方认证项目、平台正式首币或可买入代币。平台以后更换 PlatformConfig 或发行程序将超出当前检测范围；原 MACHX 已关闭，不是唯一监控入口。

## 离线测试

在本目录运行：

~~~sh
python3 -m unittest -v test_machine_launch_detector test_machine_launch_ws
python3 -m py_compile machine_launch_detector.py
~~~

18 项测试覆盖解析、CPI、v0 Address Lookup、错误及重复过滤、首次 checkpoint、断线补漏、RPC 暂不可用、通知状态及错误分支。测试使用合成交易及本机回环 WebSocket。已验证协议订阅、消息接收与 JSON 输出的离线端到端路径，但不能当成真实 Solana RPC 或 macOS 通知送达验收。

## 隔离手工运行说明

Python 3.11+。以下安装仅针对本文件夹的虚拟环境：

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v test_machine_launch_detector
~~~

需要用户另外授权后才能进行 Mac 本地只读 live 实测。将自己的现有 Alchemy/Solana HTTPS 和 WebSocket RPC URL 以环境变量 MACHINE_FUN_HTTP_RPC、MACHINE_FUN_WS_RPC 放在 Mac 本地，不得提交任何 Key/URL 到公共 Git。满足条件后人工启动：

~~~sh
.venv/bin/python machine_launch_detector.py listen --notify-local
~~~

Ctrl-C 停止。首次连接之后以最新已存在签名作 checkpoint，不重放全部历史代币。不会自动创建 LaunchAgent、cron 或通知定时任务。SQLite 默认放在 ~/.local/state/machine-fun/launch-events.sqlite，不与 Frank DB 共用。

解析已保存的完整 getTransaction JSON：

~~~sh
.venv/bin/python machine_launch_detector.py replay path/to/transaction.json --signature ORIGINAL_SIGNATURE
~~~

## 发布前门禁

1. 官方真实平台归属及新配置更替的独立核验。已知 PlatformConfig 存在链上，但仅凭自填 Machine.fun 名称并不足以完成企业归属证明。
2. 用户单独授权的 Mac 上真实 WebSocket 长连接和断线重连验收，测量从上链到候选输出的真实延迟，记录资源/RPC 限流。
3. macOS 通知到达验收；如要远程 Gmail 推送，必须另建独立、经授权且有实际 Sent 读回的送达路径。当前只支持 stdout 和可选 macOS 本地通知。
4. 独立固定 SHA 代码审查通过后，另行评估常驻运行；本 PR 保持 Draft，既不部署，也不交易，不接触 Frank。

官方来源：
- https://github.com/raydium-io/raydium-sdk-V2/blob/master/src/raydium/launchpad/instrument.ts
- https://github.com/raydium-io/raydium-sdk-V2/blob/master/src/raydium/launchpad/layout.ts
- https://github.com/raydium-io/raydium-docs-v1/blob/main/products/launchlab/instructions.mdx
- ../machine-fun-first-launch-detection.md

## 2026-10-29 新增：复用 Frank 的 Alchemy 和 Gmail，独立人工启动

不用申请新的 Alchemy Key，不需要重新授权 Google（前提是 Frank 现有 OAuth 仍有效）。代码在 Mac 本地只读使用：

- `~/Library/Application Support/FrankMeme/solana_rpc_urls` 的首个有效 Alchemy Solana Mainnet HTTPS 地址，自动转换为 Alchemy 官方的 `wss://solana-mainnet.streaming.alchemy.com/v2/<existing-key>`。只在进程内转换，不在 Git 或终端输出真实 Key。
- `~/.frank_meme_control_root` 指向的 `gmail-existing-source.json`；找不到时从 `~/Library/Application Support/FrankMeme/mission-loop.sh` 读取固定 PROD 配置，再只读取得 `existing_oauth_file` 和 `recipient`。不会重置 OAuth，不修改旧文件或写入 Frank 的邮件/监控数据库。
- 新模块自己使用 `~/.local/state/machine-fun/launch-events.sqlite` 和 `gmail-alerts.sqlite`，权限 0600，独立单实例锁，控制台输出不包含密钥。

在一个**新的独立目录** clone PR #243 分支后，进入 `research/projects/machine-fun/detector`：

~~~sh
bash run_machine_fun.sh check
bash run_machine_fun.sh probe
bash run_machine_fun.sh run --notify-local
~~~

`check` 只读本地两个现有凭据并检查权限，不联网、不发邮件、不启用监听；`probe` 通过现有 RPC 实际执行一次 getHealth，并用现有 Gmail OAuth 刷新短期 token，核对 Google 账户身份与 Sent 读取权限，**不发邮件**；`run` 首先自动执行本模块全部 28 项离线/本机回环测试；任意失败则不启动真实监听和 Gmail 发送。测试成功后，`run` 在前台监听已知 Machine.fun PlatformConfig，对**新检测到的真实候选**发送 Gmail 通知，另可选本地桌面通知。首次启动只设置现有链上状态为 checkpoint，不会给历史代币补发邮件。终端保持运行才能持续监控，Ctrl-C 停止；无 LaunchAgent、cron、定时任务。

完整独立测试命令：

~~~sh
.venv/bin/python -m unittest -v test_machine_launch_detector test_machine_launch_ws test_machine_launch_gmail
.venv/bin/python -m py_compile machine_launch_detector.py machine_launch_gmail.py machine_fun_runtime.py
~~~

**重要门禁：** 新增 10 个 Gmail/配置测试已提交到 Git，但本次交付不把未在目标 Mac 实际运行的测试写成 PASS。完整 28 项测试、真实 Gmail OAuth `probe`、Solana WS 订阅确认、单独的真正链上新发行邮件 Sent readback，均需要 Mac 的执行回执。没有创建后台进程或不经授权的定时通知。

官方 API 来源：
- https://www.alchemy.com/docs/reference/solana-subscription-api-endpoints
- https://www.alchemy.com/docs/reference/logs-subscribe
- https://developers.google.com/workspace/gmail/api/guides/sending
