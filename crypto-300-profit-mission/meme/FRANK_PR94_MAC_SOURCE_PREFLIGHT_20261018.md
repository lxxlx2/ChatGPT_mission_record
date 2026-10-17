# PR94 — Mac 源码只读预检（独立隔离；不启动服务）

2026-10-18。仅验证 Mac 本地全新隔离 Git checkout 与固定 GitHub CI 的 PR94+C02+F01+QA 联合 tree 完全一致，不启动 localhost 服务、Safari、RPC、Sidecar、Gmail、交易，也不读写生产 SQLite。此过程需要访问公开 GitHub 拉取源码。

固定 PR94 SHA: 19d5d8be92b944f1c9814a1f527d233290bf2dfc；联合 tree: e2b291a29decad536c8c10b4b1a4f9b5688d22b4；最终 CI: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39064373331 。不要沿用旧 PR85 的 eea30efa tree。

## Mac zsh 复制运行（仅需源码预检时使用）

```zsh
(
set -euo pipefail
umask 077
root="$(mktemp -d "$HOME/.local/share/frank-pr94-preflight-XXXXXXXX")"
repo="$root/repo"
pr94=19d5d8be92b944f1c9814a1f527d233290bf2dfc
f01=d2eeebc1b49d2bae38e05d7d01f6839e3ba237f4
c02=8d425e4d0e9db9f27abd8ad662e4d59e64b57e53
qa=40febd8275c7710a8697af5a0503569a2bb5cb8d
ev=b9fb6e6df9032a0e6f49c1274bb4ba61c9e4c2da
expected=e2b291a29decad536c8c10b4b1a4f9b5688d22b4
file=crypto-300-profit-mission/local-agent/mission_agent/mission_control/server.py
view=crypto-300-profit-mission/local-agent/mission_agent/mission_control/follow_view.py
printf 'QA_ROOT=%s\n' "$root"
git clone --no-checkout --quiet https://github.com/lxxlx2/ChatGPT_mission_record.git "$repo"
git -C "$repo" fetch --no-tags origin refs/heads/fix/frank-pr93-executable-quote-binding-p2-20261018:refs/remotes/origin/fix/frank-pr93-executable-quote-binding-p2-20261018 refs/heads/fix/frank-c02-pr82-authority-presence-20261016:refs/remotes/origin/fix/frank-c02-pr82-authority-presence-20261016 refs/heads/fix/frank-f01-pr81-js-range-20261016:refs/remotes/origin/fix/frank-f01-pr81-js-range-20261016 refs/heads/qa/frank-f01-pr83-c02-pr84-f02-p73-isolated-20261016:refs/remotes/origin/qa/frank-f01-pr83-c02-pr84-f02-p73-isolated-20261016 refs/heads/evidence/frank-ca-local:refs/remotes/origin/evidence/frank-ca-local
[[ "$(git -C "$repo" rev-parse refs/remotes/origin/fix/frank-pr93-executable-quote-binding-p2-20261018)" == "$pr94" ]]
[[ "$(git -C "$repo" rev-parse refs/remotes/origin/fix/frank-c02-pr82-authority-presence-20261016)" == "$c02" ]]
[[ "$(git -C "$repo" rev-parse refs/remotes/origin/fix/frank-f01-pr81-js-range-20261016)" == "$f01" ]]
[[ "$(git -C "$repo" rev-parse refs/remotes/origin/qa/frank-f01-pr83-c02-pr84-f02-p73-isolated-20261016)" == "$qa" ]]
[[ "$(git -C "$repo" rev-parse refs/remotes/origin/evidence/frank-ca-local)" == "$ev" ]]
git -C "$repo" checkout --quiet --detach "$pr94"
git -C "$repo" -c user.name='Frank isolated QA' -c user.email='frank-qa@example.invalid' -c core.hooksPath=/dev/null merge --no-ff --no-edit --no-gpg-sign "$c02"
if ! git -C "$repo" -c user.name='Frank isolated QA' -c user.email='frank-qa@example.invalid' -c core.hooksPath=/dev/null merge --no-ff --no-edit --no-gpg-sign "$f01"; then
  [[ "$(git -C "$repo" diff --name-only --diff-filter=U)" == "$file" ]] || exit 1
  git -C "$repo" checkout --ours -- "$file"
  git -C "$repo" add -- "$file"
  [[ -z "$(git -C "$repo" diff --name-only --diff-filter=U)" ]]
  git -C "$repo" -c user.name='Frank isolated QA' -c user.email='frank-qa@example.invalid' -c core.hooksPath=/dev/null commit --no-edit --no-gpg-sign
fi
git -C "$repo" -c user.name='Frank isolated QA' -c user.email='frank-qa@example.invalid' -c core.hooksPath=/dev/null merge --no-ff --no-edit --no-gpg-sign "$qa"
for sha in "$c02" "$f01" "$qa"; do git -C "$repo" merge-base --is-ancestor "$sha" HEAD; done
[[ "$(git -C "$repo" rev-parse "HEAD:$view")" == "$(git -C "$repo" rev-parse "${f01}:$view")" ]]
[[ -z "$(git -C "$repo" status --porcelain=v1 --untracked-files=all --ignored=matching)" ]]
actual="$(git -C "$repo" rev-parse 'HEAD^{tree}')"
printf 'ACTUAL_TREE=%s\nEXPECTED_TREE=%s\n' "$actual" "$expected"
[[ "$actual" == "$expected" ]]
QA_REPO="$repo" QA_F01="$f01" QA_FILE="$file" python3 - <<'PY'
import ast,os,subprocess
from pathlib import Path
repo=Path(os.environ['QA_REPO'])
file=os.environ['QA_FILE']
original=subprocess.check_output(['git','-C',str(repo),'show',os.environ['QA_F01']+':'+file],text=True)
combined=(repo/file).read_text()
def method(source):
    klass=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='DashboardState')
    return ast.dump(next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='follow_opportunities'),include_attributes=False)
assert method(original)==method(combined),'F01_AST_DRIFT'
print('MAC_PR94_F01_AST_IDENTICAL=PASS')
PY
printf 'MAC_PR94_SOURCE_PREFLIGHT=PASS\nQA_ROOT=%s\nSERVICES_STARTED=false\nREAL_RPC=false\nPRIVATE_SIDECAR_READ=false\n' "$root"
)
```

完成标识 MAC_PR94_SOURCE_PREFLIGHT=PASS 仅能证明源码 tree 和 F01 审核函数 AST 相同，不证明真实 Safari、当前钱包、当前 F01 BUY、C02 风险、32 Mint / ATA 或部署。任一校验失败应原样保留输出，不执行 git reset、git clean、rm -rf、服务启动。

## 随后的实际验收（单独授权）

第一阶段：固定联合源码的真实 Mac Safari.app 和两业务标签，只使用隔离 localhost 合成数据；验证 BUY/WAIT、quote price/impact/time C8、不同时效、同名不同 CA、历史零余额和未知分离、2 个业务入口、Console、服务退出。必须始终显示 SYNTHETIC QA / 禁止交易。

第二阶段：另行明确授权后，使用只读真实 Solana RPC/Sidecar 检查 A05 32 Mint 所有 ATA（Token 与 Token-2022）、wallet identity、source freshness、C02 exact CA 的实际权限、LP/funder/holder。任何来源不可用须标 UNKNOWN，零余额不证明 SELL。

门禁：NO_MERGE / NO_DEPLOY / NO_NEW_REAL_RPC / NO_PRODUCTION_SQLITE_WRITE / NO_GMAIL / NO_TRADES / NO_NEW_AUTOMATION / NO_FILE_CLEANUP。