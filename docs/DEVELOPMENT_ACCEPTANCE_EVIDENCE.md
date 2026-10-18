# Mission / 开发、审核与实机验收证据规则

Updated: 2026-10-18
Status: canonical development acceptance workflow supplement
Applies to: Frank, C02 and subsequent Mission browser UI modules (and other UI changes as applicable).

## 开发流程（缺一不可）

1. 从 canonical 仓库规则与该模块开发计划确认目标、现状、来源、风险和固定比较基线。明确是哪一个模块，不因局部边界问题偏离主要业务功能。
2. 独立分支提交实际变更、定向反例测试和相关回归；不得修改已获批准的固定 SHA。遵守现有文件命名、路径、no new RPC/trade/email gates。
3. 让**外部独立 AI**审核固定提交 SHA，提交时主动附上可直接复制的审核提示词（repo、PR、HEAD、base、差异范围、完整测试命令、阻断标准、报告格式）。自测绿色不等于外部批准；重审旧 SHA 不追溯批准新 SHA。
4. GitHub CI 固定 SHA 执行。记录实际 Actions run URL、完整日志结论、测试数与未验证项；P0/P1/P2 阻断修复后必须重新审核新固定 SHA，P3 不得无故使项目陷入无限修复循环。
5. **Mac 实机/浏览器验收**：明确区分 GitHub 离线测试、隔离页面 + 现有 GET 数据、真实 Mac/Safari、真实链上证据和生产部署。不能凭截图假定交易、钱包余额或来源真实性。
6. **截图与压缩证据是每次要求用户实机验收时的命令组成部分，不得只让用户逐张手工上传截图。** 标准命令/仓库脚本必须（a）使用固定审核 SHA；（b）提示并捕获实际需要的页面区域；（c）记录可核验的时间、SHA、页面来源与结果范围；（d）将截图和 manifest 打包 ZIP 至用户本地 Downloads（不是 Git 仓库）；（e）自动在 Finder 中选中 ZIP 方便用户直接上传；（f）退出时安全清理隔离临时目录/服务，不能删除现有监控。
7. **截图取证的源码完整性：** 任何允许人工停留的验收预览，必须从固定 Git commit 的 blob 导出至本次私有临时快照，只提供该快照，不可直接提供可变工作区；在导出后与 ZIP 成功交付前重新核验原 checkout 的 HEAD、dirty 状态及快照逐文件 SHA256。检测到任何漂移必须以非零状态拒绝可信验收 ZIP，保留已拍截图并明确标记 REJECTED，不得将其归属于启动时 SHA；不得覆盖或删除用户已有同名压缩包。
8. 用户上传 ZIP 后再根据截图和来源记录标注 `PASS / PARTIAL / BLOCKED / NOT_VERIFIED`，附 PR comment 证据，明确仍缺什么。不能把仅静态展示说成生产部署验收。
9. 仅在独立审核、相关验收和**用户另行明确授权**后，才能进入 merge/deploy。默认保留 `NO_MERGE / NO_DEPLOY / NO_NEW_RPC / NO_GMAIL / NO_TRADES / NO_PRODUCTION_SQLITE_WRITE`。

## 进一步要求：全自动实机截图（2026-10-18）

- **用户不应再负责找截图位置、选择 CA、展开面板、手动框选或反复按 Enter。** 用户只运行一条固定 SHA 的 zsh 命令，结束后 Finder 自动选中 ZIP；除 macOS 首次要求的 Safari 自动化/屏幕录制系统权限外不得依赖人工操作。仅当自动化明确失败时给出对应阻断状态，不得要求用户猜要截哪里。
- 对新增的 C02 归档页面，使用 `crypto-300-profit-mission/local-agent/scripts/frank_c02_auto_safari_capture.py --candidate-sha <固定审核SHA>`。脚本先从 Mac 的 `~/.frank_meme_control_root` 指向的**现有** `cluster-reports/<mint>/latest.json` 只读枚举全部归档 CA，优先选择能通过**现有 Dashboard `/api/cluster-latest?mint=...` GET** 返回且 Mint 一致的报告。仅在没有可读归档时回退到候选/观察池（最多 24 个 CA）；不扫描链上，也不从用户钱包直接读取余额。大于现有 GET 读取上限的报告必须跳过、不可虚报找到；若无可读归档，明确记录 `LOCAL_ARCHIVE_CATALOG_NOT_READABLE` / `NO_LOCAL_CA` / `ARCHIVE_MISSING`。此路径不新增 HTTP 路由、不修改生产服务或归档文件。
- 只从固定 SHA Git blob 导出私有页面快照。自动在 Safari 同源 iframe 打开实际 C02 页面并点击“查看已有归档（只读）”按钮、等待页面明确回执、确认显示 CA 一致后自动截图 `c02-overview.png` 与 `c02-report.png`；额外 QA 页仅辅助导航，不改动受审产品静态源码。
- 不依赖 Safari 开启 JavaScript from Apple Events；仅使用 AppleScript 读取前台 Safari URL 来核对截图窗口，以及 macOS `screencapture -x -D 1` 捕获主屏。系统若要求首次授权，用户可按系统弹窗授权；若 Safari 不在前台、页面不回应或权限拒绝则拒绝有效 ZIP，保留已抓取图并写 `REJECTED.json`。
- **分阶段截图身份：** 同一路径的不同 `overview/report` 页面必须逐阶段核对完整 origin、path、随机 token 与 stage；收到后台 ready 回执并不等于前台截图页正确。Safari 激活后临近截图前和截图后都应独立核对目标 URL；任何错页或 token 漂移均拒绝有效 ZIP。
- **证据所有权：** ZIP 必须先写进每次运行独有的私有 staging 目录，再以原子、不覆盖（例如同卷 `os.link`）方式提交 Downloads，清理只能触及本次创建的暂存文件。不可使用 `Path.exists()` 推测 ZIP 所有权，更不能在冲突后删除另一个运行的文件。
- ZIP 另包含 `c02-automatic-acceptance.json`，记载候选 Mint 来源、页面返回状态、`backend_code_identity=UNVERIFIED`、准确审核 SHA、截图哈希、只读范围和异常原因。记录 `ARCHIVE_MISSING` 表示缺少历史数据，不可当作 C02 正向成功验收；主屏截图可能包含个人信息，仅保存 Downloads/当前聊天，严禁自动上传公共仓库。
- 任何自动验收代码改动都必须在独立 QA 分支走 CI 和外部 AI 审核，旧版 PR101/PR102 已批准 SHA 保持不变。
 
## Frank PR101 Mac/Safari 示例（已固定审批源码）

- 仓库脚本：`crypto-300-profit-mission/local-agent/scripts/frank_pr101_safari_evidence.py`。
- CLI 通过隔离浅克隆验证批准 SHA `e8bc450d836ac46df5224ce7b6fc048ea5720db0`，并且**不改用当前分支未经审核的 UI**；新 QA 分支中的 C02 已归档报告按钮仍需单独代码审核。
- 脚本自动启动仅绑定 `127.0.0.1` 的只读 GET 页面预览；现有 Frank localhost 控制台是唯一数据源。仅允许指定 JSON GET（包括 `/api/cluster-latest?mint=EXACT_CA` 的历史归档），对 POST、新 RPC、未审批端点拒绝。

Mac zsh 本地执行（从任何目录均可，脚本保存在 Git 中；临时 checkout 清理不会删除 Downloads 中的 ZIP）：

```zsh
(
set -e
QA_DIR="$(mktemp -d "${TMPDIR:-/tmp/}frank-safari-qa.XXXXXXXX")"
trap 'rm -rf "$QA_DIR"' EXIT
git clone -q --depth 1 --filter=blob:none --branch ops/frank-pr101-safari-evidence-and-c02-archive-20261018 https://github.com/lxxlx2/ChatGPT_mission_record.git "$QA_DIR/repo"
python3 -B "$QA_DIR/repo/crypto-300-profit-mission/local-agent/scripts/frank_pr101_safari_evidence.py"
)
```

截屏使用 macOS `screencapture -i -x` 交互框选实际 Safari 页面区域；依提示确认或跳过每个验收点。选择结束后脚本**自动**生成 ZIP，并调用 `open -R` 在 Finder 中选中 ZIP。不要将该 ZIP 提交 GitHub。
- 依次提示四类实际 screenshot：顶部机会及展开历史、交易统计、持续观察池及待核查记录、C02 历史资料（如果页面版本具备可用入口）；本地 `screencapture -i -x` 由用户框选实际可见区域，可按 `s` 跳过不适用阶段，`done` 提前完成。
- 脚本生成 `~/Downloads/frank-pr101-safari-evidence-YYYYMMDD-HHMMSS-e8bc450d.zip`，包含 `manifest.json`、截图的 SHA256、批准静态文件 SHA256、拍摄时间、read-only 声明，并调用 `open -R` 选中 ZIP。**不会自动上传、不会输出私有钱包/截图内容到日志或 Git。**
- 新 C02 按钮归属于另外的 QA 分支；只有该分支得到单独固定 SHA 审核后，才能在上述命令最后的 Python 调用中添加 `--candidate-sha <新审核的40位SHA>` 来选择当前 clean checkout 的新静态页面。脚本验证 exact HEAD、clean worktree；ZIP 标明 `CANDIDATE_REQUIRES_SEPARATE_INDEPENDENT_REVIEW`，不声称这个候选版本已获得生产批准。默认仍严格使用已批准 PR101 静态文件。
- 截图仅证明截图时间点的 UI；指标是本地索引范围，不等于 Solana 链完整性。未点击/未加载的控件保持 `NOT_VERIFIED`；报告截图不能代替真正的链上历史来源核验。

## 统一产物与命名

- 代码路径沿用模块现有目录，`<module>-<purpose>-YYYYMMDD` 分支名；新文档先读 `docs/REPOSITORY_STRUCTURE.md`，不得重命名既有运行路径。
- 分支 PR 记录：固定 parent SHA / head SHA、真实 `git diff`、测试命令/结果、独立 AI 评论以及真实 Mac 证据状态。版本变更应当使此前审核 SHA 批准失效，直到对新 SHA 再审核。
- ZIP 命名为 `<module>-<scope>-evidence-<local-timestamp>-<shortsha>.zip`，截图保存在 ZIP `screenshots/`，`manifest.json` 包含 SHA256 文件清单和 provenance。
- 除非用户显式同意公开，所有原始实机截图/真实钱包或含账户内容的压缩包**只能保存在本地并通过当前对话上传**，不能提交公共 GitHub 仓库。

以上规则规范证据采集和验收流程，不是新的运行时发布许可。
