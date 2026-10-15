# Frank Mac 本地只读预检执行合同（2026-10-15）

状态：`USER_EXPLICITLY_AUTHORIZED_PASSIVE_PREFLIGHT`，仅允许本地读元数据，不代表批准 F01/C02/F02 隔离服务启动、SQLite 实际读取、会话重放、新链上 RPC、生产写入、清理或合并。

## 预检脚本
`crypto-300-profit-mission/local-agent/scripts/frank_mac_readonly_preflight.py`。脚本只使用 macOS 系统 Python3 标准库、Git、可选的 lsof。运行时 `python3 -B -`，避免写入 Python `__pycache__`。

用户已有本地 review 仓库口径：`~/.local/share/frank-f02-r3-review`。预检不读取其他 Git 仓库，也不自动克隆、`fetch`、切分支、`reset`、`stash`、`checkout`。它只检查这一目录是否存在、是否独立 Git root、Git HEAD 是否匹配已审 PR73 或较早 PR68、五个 Git commit 对象在本地是否存在、历史证据 ref 是否为固定 SHA，并以 `GIT_OPTIONAL_LOCKS=0` 只检测源树一般未提交改动是否存在（不列出文件名）。本地仓库缺最新 Git 对象是 `NOT_LOCAL`，不能自动拉取或判断远端不存在。

已知真实既有研究根目录：`~/.local/share/frank-f02-research/manual-sessions`。只对最多200个直接子目录（`session-*`）执行文件**存在性**与符号链接检查：`positions.sqlite`、`wire/owner-*/manifest.json`。不打开 SQLite、不打开 JSON 原文、不读取 Token Account/CA/私钥、没有哈希归档，也不会修改其权限/mtime内容。报告明确 `contents_or_sha_verified=false`、`session_freshness_verified=false`。目录数超限制时报告 `session_scan_truncated=true`，不能推断全覆盖。

使用 `lsof` 被动检查本机127.0.0.1研发拟用端口 18765（F02）、18766（控制台）、18777（GET bridge）是否有 TCP LISTEN；不连接端口、不绑定端口、不创建或终止进程。若系统没安装 lsof 则返回 `CANNOT_CHECK_NO_LSOF`，不得把 `NO_LISTENER_SEEN` 当作强保证空闲。实际验收要再次核对生产进程、路径和用户明确授权。

## 用户执行命令

使用已最终成功 CI 的 **固定 Git commit SHA** 获取脚本，而不是移动分支的 latest；应在本轮完整 GitHub CI 后由开发者提供精确 URL 与完整可复制 zsh。建议通过固定 `raw.githubusercontent.com/lxxlx2/ChatGPT_mission_record/<40字SHA>/...` 下载到管道，而非下载散落补丁文件。

本命令的唯一外部网络是获取公开固定脚本的 HTTPS 内容。脚本运行时**不发网络请求**，不触发真正 Solana RPC；输出经设计没有钱包地址、Token Account、私钥、完整 Mac 路径或原始研究数据。不会把本地信息提交 GitHub 或发给第三方；用户可直接复制单行 JSON 回传到对话供分析。

## 完成标准

- PASSIVE_PREFLIGHT 本机 JSON 输出完整，包括原 git clone、固定Git证据、研究会话是否存在、三端口占用以及全部 false 的 `side_effects`。
- 仅根据 JSON 决定是否具备**进一步 Mac 隔离实测的前置条件**，不能因为 preflight 脚本完成而自动启动服务、使用现有生产端口、打开旧 Sidecar、批量读取历史原文或申请新的链上采集。
- 来源已超过 300s TTL 的旧研究归档仍应 `STALE/SOURCE_UNAVAILABLE`，不能展示历史持币数量或推断交易。
- 若不满足条件，在 Git 记入 **事实+未确认项**，并先修改单独测试方案，等待新用户授权。

绝不进行：`NO_MERGE / NO_DEPLOY / NO_NEW_REAL_RPC / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_NEW_AUTOMATION / NO_FILE_CLEANUP / NO_MAC_SERVICE_START`。
