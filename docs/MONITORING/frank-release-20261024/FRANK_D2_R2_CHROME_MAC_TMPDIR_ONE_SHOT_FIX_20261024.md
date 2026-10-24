# Frank D2 — R2 Chrome macOS 临时目录最小修正与有限补测（2026-10-24）

**状态：CODE/DOC-ONLY HANDOFF；不是新 Mac 测试结果、R2 PASS 或 Dashboard 生产上线授权。**

产品与方案绑定：
- **固定产品 SHA** `914e9e47fed2e60bc24690fcb083413a64d4e681`；原始 PR #178 HEAD `ea9a7715beb4d2a55ae956bf993828cbddcb50e5` 仍 Draft 未合并。
- 保留原 [R1 446 文件 PASS](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6383051314)，规范化 manifest `9a06f5f29fce05ccade8caa2b90d6d6c0c4248d2e6ab4e45aa26fa9d3f401062`；**不重做 R1 或重新导入**。
- 原单次 R2 retry [Mac 实测 BLOCKED](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6383466668)，失败时 Chrome `SingletonSocket` 在 `/var/folders/.../T/com.google.Chrome.*/` 下调用 AF_UNIX bind 获 EPERM。真实 browser cases **0**，此记录不得修改为 PASS。
- [独立源码与 Gate P 复核](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6383534415)：上一轮只导出了 `TMPDIR/TMP/TEMP`，遗漏 Chromium macOS 专用 `MAC_CHROMIUM_TMPDIR`；Gate P 的7个记录测试未完整覆盖 UDP、IPv6 connect 和子进程协议矩阵。

## 已核实的外部源码依据

- Chromium 固定版本 `base/files/file_util_apple.mm::GetTempDir()` 首先读取非空 `MAC_CHROMIUM_TMPDIR`；仅未设置时调用 `NSTemporaryDirectory()`。原文 https://chromium.googlesource.com/chromium/src/+/refs/tags/146.0.7680.180/base/files/file_util_apple.mm
- Chromium `chrome/browser/process_singleton_posix.cc::ProcessSingleton::Create()` 使用 `CreateUniqueTempDir()` 创建 socket 父目录，再对其 `SingletonSocket` bind。https://chromium.googlesource.com/chromium/src/+/HEAD/chrome/browser/process_singleton_posix.cc
- Chromium macOS 代码的新提交强调此环境变量**只覆盖 base::GetTempDir()**，并**不改变系统** `NSTemporaryDirectory()/confstr()` 的路径。不能据此声称 Chrome 全部子进程临时文件均已被重定向。https://chromium.googlesource.com/chromium/src/+/c2706c3317723e987f85322a25ed475bdfe3a719%5E%21/
- Playwright 的 `browserType.launch({env})` 支持明确传给所启动浏览器的环境变量。https://playwright.dev/docs/api/class-browsertype

## Mac 执行器的唯一最小代码/启动环境修正（预备，不在本 GitHub 方案编译或执行）

**目标是减少对 Seatbelt 的权限修改，不是增加系统网络能力。** 使用全新短、真实、`0700`、Git 外独立临时根，建议按已核实的真实绝对路径 `/private/tmp/fd2r2.XXXXXX` 由受控 `mktemp -d` 动态生成，禁止复用历史测试目录。避免 `/tmp` 指向 `/private/tmp` 的 symlink alias；检查完整 `.../com.google.Chrome.XXXXXX/SingletonSocket` 的实际 Darwin `sockaddr_un.sun_path` 长度限制。

在已有 `chrome-no-network.sh` 沙箱 wrapper 启动 Chrome 前，增加等价环境绑定，使用本次私有临时目录而非旧的长目录：

```sh
export MAC_CHROMIUM_TMPDIR="$R2_ROOT/ipc"
export TMPDIR="$R2_ROOT/ipc"
export TMP="$R2_ROOT/ipc"
export TEMP="$R2_ROOT/ipc"
```

上述 `$R2_ROOT/ipc` 必须先已存在、目录权限仅 owner、并完整位于生成的 Seatbelt `AF_UNIX` path allowlist 内。原 `network*` IP deny 和严格本地 AF_UNIX `network-bind/network-outbound/network-inbound` 策略不放宽，不允许 `/var/folders` 通配放行。若 Playwright/browser launch 指定 `env`，必须在最终 `browserType.launch` 的 `env` 对象显式包含上述变量，验证 `sandbox-exec` 之后、Chrome exec 之前的子进程确实能看到 `MAC_CHROMIUM_TMPDIR`（只记录布尔值与路径所在 allowlist 标志；不要在 Git 记录机器原始绝对路径）。

**重要：此变量是推定修复路径而非已复现成功。** 必须先在同一策略下用无浏览器子进程确认变量确实透传，并证明本次临时根内 Unix bind 与出根拒绝；不能把 `getenv` 成功错写为 Chrome 已使用此目录。

## 如果获得新的单次离线 R2 授权，唯一补测门禁

1. **先验静态条件**：已固定源 SHA、manifest 和原 runner/priv-source hash；`MAC_CHROMIUM_TMPDIR` 非空且指向 owner-only 短真路径；profile 与管道也位于新根；严格无新 TCP/UDP socket 监听、无生产 I/O。原用户上次给出的“只执行一次”授权已经执行完毕；本方案不等于自动追加权限。
2. **加强 Gate P 防护证明**：继续必须实测根内 AF_UNIX echo、根外 bind/connect EPERM；补齐 AF_INET/AF_INET6 的 `SOCK_STREAM` **及** `SOCK_DGRAM` bind/connect，且任一不属 EPERM/内核策略拒绝均视为 `BLOCKED_NETWORK_POLICY_NOT_PROVEN`。子进程重复至少一个 UDP、IPv6、越界 AF_UNIX 负例。**禁止再用生产 `127.0.0.1:8766` 作安全连接测试目标**；只用无生产服务的合成/保留测试地址，所有调用必须被拒绝，不能实际发送 IP 报文。
3. **Gate B：仅一次真正的 Chrome 启动**，必须先验证 wrapper→Chrome 启动环境包含 `MAC_CHROMIUM_TMPDIR`，以 `--remote-debugging-pipe` 启动，不使用 TCP DevTools/WebSocket 监听，不另开 HTTP 测试端口。Chrome ProcessSingleton 的目标 socket 路径若仍在 `/var/folders`，立即 `BLOCKED_CHROME_TMP_OVERRIDE_NOT_EFFECTIVE`；若在受控根却仍 EPERM，则 `BLOCKED_CHROME_IPC_WITHIN_ALLOWLIST`；如果出现 Mach/其他 IPC 权限要求，保留错误、停止，不放宽策略或第二次启动。
4. **R2 真实浏览器用例**：浏览器成功建页后才运行，静态页面/JS/CSS 原样来自产品 candidate；所有资源以拦截/pipe 合成供应、不使用正式 `8766` 或生产余额文件；检查 D2 初始无自动 GET、手动点击、100/48 分页、Mint 非零/零/缺失、双 slot/曼谷时间/非实时、失效/错误、竞态、原 CA 与 Frank 控件未退化；区别浏览器渲染结果和模拟 Handler 的范围。
5. **首个失败即停止，完整清理**：不得二次 Chrome 启动、换 Firefox 混充 Chrome、放宽通用 Unix socket、建立额外 TCP listener、接入真实 API；保留此前真实 R2 BLOCKED，单独发布 `R2_BROWSER_SYNTHETIC_PASS` 或新的首个 `BLOCKED` 和实际未测项目，GitHub 只上传脱敏证据，Mac 上检查已有正式 `8766` / Loop / V1 及已导入私有 JSON 不变。

## 产品优先级与停止条件

这只是针对 **一次已经确认的环境阻断** 的候选修正，不能开展多轮无尽 Chrome/Seatbelt 细节研究。如果经过这一个有界且单独获批的 R2 依然不能正常启动真实浏览器，应转为**发布决策风险评估**，坦诚区分已通过的 Python/JS/Handler 合成测试与未通过的真 Chrome，而不是无穷补测。绝不据此默认取得生产切换许可。

`NO_NEW_PORT / NO_IP_NETWORK / NO_PROD_HTTP / NO_RPC / NO_IMPORT_AGAIN / NO_DEPLOY / NO_RESTART / NO_MERGE / NO_TRADES / NO_NOTIFICATIONS / KEEP_8766`。

**当前状态**：`R1_PASS / R2_BROWSER_BLOCKED / SPECIFIC_ENV_FIX_PREPARED_NOT_TESTED / PRODUCT_SHA_UNCHANGED / MAC_RETRY_NOT_EXECUTED / FUTURE_CUTOVER_NOT_AUTHORIZED`。
