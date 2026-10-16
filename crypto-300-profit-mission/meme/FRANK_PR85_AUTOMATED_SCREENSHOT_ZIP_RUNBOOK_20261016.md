# PR #85 — 一条 zsh 命令自动展开/长图/ZIP（Mac，已批准 synthetic QA）

> **2026-10-17 QA 工具门禁更新：后继 Draft PR #88 的唯一固定 SHA `ad0ac61c42520caed6a915d4dc90c84e97c45da9` 已获另一 AI 独立 `APPROVE`（用户提供 REVIEW、commands 与真正 WebKit 合成重放证据）。旧 PR #87 SHA `cfa0ae1e6cdf02dbb200157e3530df6e07e42fd1` 的 `REQUEST_CHANGES` 仍有效。下一阶段获准在用户 Mac 上**手动运行 QA-only** 截图 ZIP 命令，上传 ZIP 后核查视觉/Console/实际退出回执；**没有授权合并、部署、真实 RPC、交易、Gmail 或生产数据修改**。用户 Mac 上这一新 SHA 的实际运行结果仍为 NOT RUN，不可替代已有原生 Safari.app 的照片。 [CI #38899261682](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38899261682)。**



生效：2026-10-16。用户已有原生 Safari 14 张合成网页截图，旧手动逐图上传方式不再作为首选。该流程只读冻结源，在同一已批准 QA_ROOT 内另开 synthetic HTTP 临时监听并自动捕捉当前网页全部指定状态，关闭监听后打包单个 ZIP，供用户手动上传。禁止实盘 RPC/生产服务/Gmail/交易/清理。无新版产品源码变化。

- 冻结联合产品 tree：`eea30efa09cb1509d7eee3fde3043ee7155257cf`；Mac ROOT：`/Users/jerson/.local/share/frank-pr85-mac-qa-R1c6kmCU`。
- 历史截图工具旧 SHA `cfa0ae1e6cdf02dbb200157e3530df6e07e42fd1` 独立 `REQUEST_CHANGES`。**新版本固定独立审核通过 SHA** `ad0ac61c42520caed6a915d4dc90c84e97c45da9`，来源分支 `fix/frank-pr87-screenshot-evidence-p2-20261016`，对应仍然 Draft/unmerged 的 PR #88。审核批准仅涉及启动回收、symlink 路径隔离与失败 Console 保存。
- 原 [GitHub Actions #38878225375](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38878225375) 只证明旧版本**正常主路径**，但旧 SHA 被独立 REQUEST_CHANGES。新版 [Actions #38899261682](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38899261682) **SUCCESS**：7 个新增 P2 回归 + 原完整 10 PNG/ZIP + 3 监听器回收；且另一 AI 已对同 SHA 独立 APPROVE。使用真正 Playwright WebKit v1.56 在全新 Git clone 构建精确产品 tree，启动 3 个 localhost 监听，完成 F02 32 Mint fresh + 筛选、F01 当前与全部展开、C02 两个同名不同 CA 各摘要与全部展开、F02 120s TTL 到期及搜索，共 **10 张全页 PNG**、ZIP、`manifest.json`、`index.md`、Console 日志、SHA256SUMS；ZIP 完整性和数量断言 PASS；独立 HTTP smoke 监听退出、产品仓库洁净、tree SHA 不变 PASS。之前两轮 CI failure 是 QA launcher 参数/会话个数断言错误，最终已修正且测试真实重跑。临时 QA HTTP 的正式两业务页面和内部 F02 通过 CSS/HTML 由 QA 层加入明显 `SYNTHETIC QA · 模拟数据 · 禁止交易`，不修改批准产品源码。
- **Playwright WebKit `≠` macOS Safari.app**：它解决自动截图、自动展开及单包上传；用户此前真正 Safari 截图独立保留。不得把自动 WebKit 结果标记为 Safari.app 的本地业务验收或真实钱包证明。

## 复制到用户 Mac 的完整 zsh 命令

以下仅产生新的 synthetic/QA 截图 ZIP；保留已有 Mac 资料与本地原生 Safari 证据。运行时会安装独立 venv 中的固定 Python/Playwright 依赖、下载 WebKit 并等待 F02 120 秒 TTL。成功后 Finder 自动选中新 ZIP。日志保留在 QA runtime，不得误将上一次 ZIP 当成新的通过结果。

```zsh
(
set -euo pipefail
umask 077

ROOT="$HOME/.local/share/frank-pr85-mac-qa-R1c6kmCU"
REPO="$ROOT/repo"
TREE="eea30efa09cb1509d7eee3fde3043ee7155257cf"
QA_SHA="ad0ac61c42520caed6a915d4dc90c84e97c45da9"
QA_BRANCH="fix/frank-pr87-screenshot-evidence-p2-20261016"

[[ -d "$REPO/.git" ]] || { print -u2 "QA_REPO_MISSING"; exit 1; }
[[ "$(git -C "$REPO" rev-parse 'HEAD^{tree}')" == "$TREE" ]] || { print -u2 "QA_FROZEN_TREE_MISMATCH"; exit 1; }
[[ -z "$(git -C "$REPO" status --porcelain=v1 --untracked-files=all --ignored=matching)" ]] || { print -u2 "QA_REPO_NOT_CLEAN"; exit 1; }

for target in "$ROOT" "$REPO" "$ROOT/qa-runtime" "$ROOT/qa-evidence" "$ROOT/qa-runtime/frank-pr85-safari.py" "$ROOT/qa-runtime/frank-browser-bundle.py" "$ROOT/qa-runtime/venv"; do
  [[ ! -L "$target" ]] || { print -u2 "QA_SYMLINK_REJECTED=$target"; exit 1; }
done

git -C "$REPO" fetch --no-tags origin "refs/heads/${QA_BRANCH}:refs/remotes/origin/${QA_BRANCH}"
[[ "$(git -C "$REPO" rev-parse "refs/remotes/origin/${QA_BRANCH}")" == "$QA_SHA" ]] || { print -u2 "QA_SHA_MISMATCH"; exit 1; }

mkdir -p "$ROOT/qa-runtime"
git -C "$REPO" show "${QA_SHA}:crypto-300-profit-mission/local-agent/scripts/frank_pr85_synthetic_safari_qa.py" > "$ROOT/qa-runtime/frank-pr85-safari.py"
git -C "$REPO" show "${QA_SHA}:crypto-300-profit-mission/local-agent/scripts/frank_browser_screenshot_bundle.py" > "$ROOT/qa-runtime/frank-browser-bundle.py"

if [[ ! -x "$ROOT/qa-runtime/venv/bin/python" ]]; then
  python3 -m venv "$ROOT/qa-runtime/venv"
fi

PY="$ROOT/qa-runtime/venv/bin/python"
"$PY" -m pip install --disable-pip-version-check --no-input --no-cache-dir --only-binary=:all: "pytest==8.3.5" "websockets==15.0.1" "numpy==2.3.3" "playwright==1.56.0"
"$PY" -m playwright install webkit

cd "$REPO/crypto-300-profit-mission/local-agent"
LOG="$(mktemp "$ROOT/qa-runtime/capture-XXXXXXXX.log")"
env -i PATH="$PATH" HOME="$HOME" TMPDIR="${TMPDIR:-/tmp/}" LANG="en_US.UTF-8" PYTHONNOUSERSITE=1 PYTHONPATH="$PWD" NO_PROXY="127.0.0.1,localhost" "$PY" -B "$ROOT/qa-runtime/frank-browser-bundle.py" --qa-root "$ROOT" --launcher-file "$ROOT/qa-runtime/frank-pr85-safari.py" | tee "$LOG"

ZIP="$("$PY" -B - "$LOG" "$ROOT" "$TREE" <<'PY'
import json
import sys
from pathlib import Path
log=Path(sys.argv[1]).read_text()
root=Path(sys.argv[2]).resolve()
tree=sys.argv[3]
receipts=[]
for line in log.splitlines():
    try:
        data=json.loads(line)
    except json.JSONDecodeError:
        continue
    if data.get("status")=="WEBKIT_SCREENSHOTS_CAPTURED_NOT_SAFARI_PASS":
        receipts.append(data)
assert len(receipts)==1, "QA_SUCCESS_RECEIPT_NOT_UNIQUE"
receipt=receipts[0]
assert receipt["source_tree_sha"]==tree
assert receipt["screenshots"]==10
assert not receipt["errors"]
archive=Path(receipt["zip_file"]).resolve(strict=True)
assert archive.parent==(root/"qa-evidence").resolve()
assert archive.is_file()
print(archive)
PY
)"

printf 'UPLOAD_THIS_ZIP=%s\n' "$ZIP"
open -R "$ZIP"
)
```

**注意 zsh 冒号陷阱**：所有 `SHA:path` 和 `branch:ref` 的冒号相邻变量必须 `${SHA}:path` 或 `${BRANCH}:ref`，不能使用裸 `$SHA:path`，避免 zsh 的 `:r` 修饰符破坏 refspec。上面命令已明确使用花括号。

## ZIP 内容及验收

运行时默认启动 3 个合成 localhost Handler、真正执行 WebKit DOM 和整页截图，等待 F02 120 秒来源过期，随后仅关闭本次 QA 监听，不动以前源文件。应打印：

```
BROWSER_EVIDENCE_ZIP_SELFTEST_PASS
WEBKIT_SCREENSHOTS_CAPTURED_NOT_SAFARI_PASS
UPLOAD_THIS_ZIP=/Users/jerson/.local/share/frank-pr85-mac-qa-R1c6kmCU/qa-evidence/frank-safari-<UTC>-eea30efa09cb.zip
```

单一 ZIP 包含 10 张 PNG 和完整 `manifest.json`/`index.md`/`browser-console.json`/`launcher.log`/`errors.txt`/`SHA256SUMS.txt`。用户只需要上传 ZIP，不必逐张图片发消息；如果失败也会保留 PARTIAL/FAILED 的包，并明确真实错误。自动浏览器完成不代表 F01 已可真金白银跟单、C02 获得真实发行权限证明或 F02 现在仍有记录的历史余额。

已批准的 #83/#84/#85 产品/集成 PR 均仍 Draft；生产 `NO_MERGE/NO_DEPLOY/NO_NEW_REAL_RPC/NO_GMAIL/NO_TRADES/NO_PRODUCTION_SQLITE_WRITE/NO_FILE_CLEANUP` 门禁不变。
