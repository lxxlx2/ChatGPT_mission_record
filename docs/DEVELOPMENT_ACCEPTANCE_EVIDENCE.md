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
7. 用户上传 ZIP 后再根据截图和来源记录标注 `PASS / PARTIAL / BLOCKED / NOT_VERIFIED`，附 PR comment 证据，明确仍缺什么。不能把仅静态展示说成生产部署验收。
8. 仅在独立审核、相关验收和**用户另行明确授权**后，才能进入 merge/deploy。默认保留 `NO_MERGE / NO_DEPLOY / NO_NEW_RPC / NO_GMAIL / NO_TRADES / NO_PRODUCTION_SQLITE_WRITE`。

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
- 截图仅证明截图时间点的 UI；指标是本地索引范围，不等于 Solana 链完整性。未点击/未加载的控件保持 `NOT_VERIFIED`；报告截图不能代替真正的链上历史来源核验。

## 统一产物与命名

- 代码路径沿用模块现有目录，`<module>-<purpose>-YYYYMMDD` 分支名；新文档先读 `docs/REPOSITORY_STRUCTURE.md`，不得重命名既有运行路径。
- 分支 PR 记录：固定 parent SHA / head SHA、真实 `git diff`、测试命令/结果、独立 AI 评论以及真实 Mac 证据状态。版本变更应当使此前审核 SHA 批准失效，直到对新 SHA 再审核。
- ZIP 命名为 `<module>-<scope>-evidence-<local-timestamp>-<shortsha>.zip`，截图保存在 ZIP `screenshots/`，`manifest.json` 包含 SHA256 文件清单和 provenance。
- 除非用户显式同意公开，所有原始实机截图/真实钱包或含账户内容的压缩包**只能保存在本地并通过当前对话上传**，不能提交公共 GitHub 仓库。

以上规则规范证据采集和验收流程，不是新的运行时发布许可。
