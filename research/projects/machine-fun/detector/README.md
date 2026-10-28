# Machine.fun 首发代币独立检测器

Status (2026-10-29): 独立源码已实现，17/17 离线单元测试通过；真实 WebSocket、Mac 通知投递及长期覆盖未经验证；未安装、未启用常驻任务。

本工具完全独立，不导入、不修改、不重启 Frank、Monster、Mission Control 或原有生产数据库、LaunchAgent。只处理 Machine.fun 已知的 Raydium LaunchLab PlatformConfig 下新币初始化事件，不绑定 SXTH。

## 检测范围

- Solana WebSocket logsSubscribe，单地址：3hVbfgB77tL1qDKhtMQoe4Gv7qPN2dGmKpD2KxWP2sPb。
- 对成功交易用 HTTP getTransaction(encoding=json, maxSupportedTransactionVersion=1) 解码顶层及 CPI，校验 Raydium LaunchLab 真正的 InitializeV2 或 InitializeWithToken2022，精确核对 PlatformConfig。
- 提取 Mint、Pool、Creator、Payer、Quote Mint、Slot、交易签名。忽略失败交易、普通 Swap、其他平台和重复事件。
- SQLite Journal 持久化状态，断线后按上次 checkpoint 从此地址分页回填。发生分页缺口时保留缺口证据，不声称覆盖完整。
- 输出 MACHINE_FUN_CHAIN_CANDIDATE JSON。可选 --notify-local 以 macOS 通知中心发出桌面通知；LOCAL_ACCEPTED 只是通知命令返回成功，不是用户阅读或 Gmail Sent 证明。

链上候选不等于 Machine.fun 官方认证项目、平台正式首币或可买入代币。平台以后更换 PlatformConfig 或发行程序将超出当前检测范围；原 MACHX 已关闭，不是唯一监控入口。

## 离线测试

在本目录运行：

~~~sh
python3 -m unittest -v test_machine_launch_detector
python3 -m py_compile machine_launch_detector.py
~~~

17 项测试覆盖解析、CPI、v0 Address Lookup、错误及重复过滤、首次 checkpoint、断线补漏、RPC 暂不可用、通知状态及错误分支。测试是合成数据，不能当成真实 WS 或 macOS 通知验收。

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
