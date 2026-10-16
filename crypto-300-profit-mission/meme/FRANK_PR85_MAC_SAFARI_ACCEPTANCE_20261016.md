# Frank PR #85 — Mac 全新隔离源码预检与 Safari 业务验收关口

状态（2026-10-16，Asia/Bangkok）：F01 #83 + C02 #84 + F02 #73 已分别审查批准；QA Harness PR #85 固定 SHA `40febd8275c7710a8697af5a0503569a2bb5cb8d` 经另一独立 AI 只对代码和 synthetic HTTP 联合组装 **APPROVE**。本次不是 Mac Safari 验收、实时 32 Mint/ATA 或生产许可。所有 PR Draft、不合并、不部署。

## 0. 已核验来源与禁令

| 来源 | 不可变值 |
| --- | --- |
| 冻结旧 main 内容快照 | `662ba4aceb9d53cb7a541ad3f251f9e12b8c09ea` |
| F02 QA 源 #73 | `5755b8b96080f21635eaa5354588cbb8f6561ab0` |
| C02 已批准 #84 | `8d425e4d0e9db9f27abd8ad662e4d59e64b57e53` |
| F01 已批准 #83 | `d2eeebc1b49d2bae38e05d7d01f6839e3ba237f4` |
| QA harness 已批准 #85 | `40febd8275c7710a8697af5a0503569a2bb5cb8d` |
| 真实 Git 历史证据 ref | `b9fb6e6df9032a0e6f49c1274bb4ba61c9e4c2da` |
| 预期**文件内容 tree SHA** | `eea30efa09cb1509d7eee3fde3043ee7155257cf` |
| 联合最终 CI | https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38867026412 |

PR #85 外部审核另外独立重新组装得完全一致的 tree，联合 Python 132、全量 1773、旧夹具阴性反例、Node F01/C02/F02 和来源审计均 PASS。**这只证明代码和离线合同。**

未获得新版本实际 Safari 测试或 Mac 服务启动授权。不得使用上次已测试的 Mac HEAD `9479e33070189231d6be2ed1633a420296dfd1a0` 代替，也不要复制旧目录中的 Sidecar、SQLite、任何忽略的 .env 或日志。以下仅新建目录、联网 GitHub 下载公开/已授权的提交、在**全新 clone 内**执行 Git merge 和只读校验；不会启动测试程序、端口、浏览器、LaunchAgent、链 RPC、Gmail、交易，也不会改动、重置或清理原有生产目录。

## 1. Mac zsh 第一阶段：只做新的独立源码组装与精准预检

在 Mac 终端一次性复制执行以下完整 zsh 代码块。保留输出；失败后不可自行跳过断言或对现有目录 `git reset/clean`。每次运行都生成新的独立目录，旧记录不会自动删除。普通 GitHub clone 需要能连接 GitHub（**仅 Git 网络，不是 Solana RPC**）。

```zsh
(
set -euo pipefail
root="$(mktemp -d "$HOME/.local/share/frank-pr85-mac-qa-XXXXXXXX")"
repo="$root/repo"
printf 'QA_ROOT=%s\n' "$root"
git clone --no-checkout --quiet https://github.com/lxxlx2/ChatGPT_mission_record.git "$repo"
main_pin=662ba4aceb9d53cb7a541ad3f251f9e12b8c09ea
f02_pin=5755b8b96080f21635eaa5354588cbb8f6561ab0
c02_pin=8d425e4d0e9db9f27abd8ad662e4d59e64b57e53
f01_pin=d2eeebc1b49d2bae38e05d7d01f6839e3ba237f4
qa_pin=40febd8275c7710a8697af5a0503569a2bb5cb8d
evidence_pin=b9fb6e6df9032a0e6f49c1274bb4ba61c9e4c2da
tree_pin=eea30efa09cb1509d7eee3fde3043ee7155257cf
git -C "$repo" fetch --no-tags origin "refs/heads/fix/frank-pr72-ignored-files-external-manifest-pin-20261015:refs/remotes/origin/fix/frank-pr72-ignored-files-external-manifest-pin-20261015" "refs/heads/fix/frank-c02-pr82-authority-presence-20261016:refs/remotes/origin/fix/frank-c02-pr82-authority-presence-20261016" "refs/heads/fix/frank-f01-pr81-js-range-20261016:refs/remotes/origin/fix/frank-f01-pr81-js-range-20261016" "refs/heads/qa/frank-f01-pr83-c02-pr84-f02-p73-isolated-20261016:refs/remotes/origin/qa/frank-f01-pr83-c02-pr84-f02-p73-isolated-20261016" "refs/heads/evidence/frank-ca-local:refs/remotes/origin/evidence/frank-ca-local"
test "$(git -C "$repo" rev-parse refs/remotes/origin/fix/frank-pr72-ignored-files-external-manifest-pin-20261015)" = "$f02_pin"
test "$(git -C "$repo" rev-parse refs/remotes/origin/fix/frank-c02-pr82-authority-presence-20261016)" = "$c02_pin"
test "$(git -C "$repo" rev-parse refs/remotes/origin/fix/frank-f01-pr81-js-range-20261016)" = "$f01_pin"
test "$(git -C "$repo" rev-parse refs/remotes/origin/qa/frank-f01-pr83-c02-pr84-f02-p73-isolated-20261016)" = "$qa_pin"
test "$(git -C "$repo" rev-parse refs/remotes/origin/evidence/frank-ca-local)" = "$evidence_pin"
git -C "$repo" cat-file -e "${main_pin}^{commit}"
git -C "$repo" checkout --quiet --detach "$main_pin"
for pin in "$f02_pin" "$c02_pin" "$f01_pin" "$qa_pin"; do
  git -C "$repo" -c user.name="Frank isolated review" -c user.email="frank-qa@example.invalid" -c core.hooksPath=/dev/null merge --no-ff --no-edit --no-gpg-sign "$pin"
  git -C "$repo" merge-base --is-ancestor "$pin" HEAD
done
git -C "$repo" merge-base --is-ancestor "$main_pin" HEAD
test "$(git -C "$repo" rev-parse refs/remotes/origin/evidence/frank-ca-local)" = "$evidence_pin"
actual_tree="$(git -C "$repo" rev-parse 'HEAD^{tree}')"
printf 'ACTUAL_TREE_SHA=%s\nEXPECTED_TREE_SHA=%s\n' "$actual_tree" "$tree_pin"
test "$actual_tree" = "$tree_pin"
test -z "$(git -C "$repo" status --porcelain=v1 --untracked-files=all --ignored=matching)"
printf 'MAC_PR85_SOURCE_PREFLIGHT=PASS\n'
printf 'QA_ROOT=%s\n' "$root"
printf 'LOCAL_EPHEMERAL_HEAD=%s\n' "$(git -C "$repo" rev-parse HEAD)"
printf 'SOURCE_TREE_SHA=%s\n' "$actual_tree"
printf 'SERVICES_STARTED=false\nREAL_RPC=false\nPRODUCTION_DEPLOYMENT=false\nPRIVATE_SIDECAR_READ=false\n'
)
```

如果 `MAC_PR85_SOURCE_PREFLIGHT=PASS`，可以报告：**Mac 源码树与 CI 相同**，没有证明 Safari、HTTP、任何实时仓位。输出 `QA_ROOT` 用来定位本次仅新建的 clone；不主动执行 `rm -rf` 或其他清理。若 `git clone`、历史证据、pin、tree、Git clean 失败，应原样保留报错，停止，不可换成 moving main 或使用旧 Mac HEAD 替代。短暂网络问题允许重新运行以上完整命令，创建新隔离目录。

## 2. Mac 业务验收（单独明确授权后才能执行）

`SOURCE_PREFLIGHT=PASS` 不会开始此步骤。必须用户**另外明确批准本次 Mac 新版 synthetic localhost HTTP + Safari**，才能准备仅 `127.0.0.1` 的短时、随机端口原生 F01/C02/F02 fixtures，禁止链接生产端口和生产 `SQLite`。不能因为本步骤此前某版批准过，就默认新版获授权。

固定验收内容：

- **源与隔离**：启动前重新核对 QA 根目录、`HEAD^{tree}`、原本关闭的生产/Loop/Gmail 端口，空随机 loopback 端口，不读私有 Sidecar、不进行真实 Solana RPC，所有数据仅 synthetic；原生产 service 不重启、不替换。
- **F01「Frank 信号」**：正常 BUY/SMALL_BUY 同一 validated quote 绿色可跟；旧 SELL/NO_BUY 不跟，过期及 0/NaN/underflow quote 不跟、价格/冲击/偏离均不可用；正小价以非零科学记数法展示；已确定不跟的内容不留在正式可跟列表。
- **C02「CA 研究」**：exact CA，不以 symbol/name 合并；原生 VERIFIED 权限显示，缺少 Mint authority 时不显示绿色安全，真实活动权限为 RISK；链上证据和权限卡一致；失败来源仍可查看，但全部来源 Slot/SHA 隐匿于正式 UI（内部审计保留）；HTML 输入不能注入。
- **F02（仅研发 QA）**：真实合成 32 Mint/ATA 两个 Token Program、非零/零/不明区分，SOURCE_UNAVAILABLE 不等于零或 SELL；已加载页面跨 TTL 到期自动遮罩、切回后台、搜索、页签重新可见时不复活旧值；不宣称真实当前钱包余额。
- **页面**：正式两个导航仅 signals、cluster；F02 不增加正式业务入口；检查用户先前圈出的重复/无用技术来源字段，在正式页面不得出现；Safari 完整操作截图包括源固定 tree、浏览器/系统日期与页面状态。
- **退出**：仅关闭本次显式启动的隔离 loopback servers，留下有价值的合成证据/截图；不清理任何 Mac 旧目录、不触碰 Frank V1、生产 SQLite、Gmail 或 LaunchAgent。失败记录清楚区分真实浏览器缺陷与仅源 fixtures 的测试缺陷。

## 3. 后续分阶段门禁

`APPROVE` #83/#84/#85 只覆盖本轮固定修复和 QA 组装。**未运行**本版 Mac Safari、真实现时 32 Mint/ATA/Sidecar/RPC、完整 arbitrary CA 的 Narrative/Dev/LP/Funder、市价交互、持续可用性、部署与交易。后续按目标业务功能验收，禁止把 synthetic PASS 转换成现时币仓保证。

始终保持：`NO_MERGE / NO_DEPLOY / NO_NEW_REAL_RPC / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_MAC_SERVICE_START / NO_NEW_AUTOMATION / NO_FILE_CLEANUP`，只有单独用户批准对应具体阶段才能改变该阶段门禁。


## 2026-10-16 Mac 新联合源码实际预检结果（用户提供原始终端输出）

- 用户发来此次 Mac 终端实际执行记录，`QA_ROOT=/Users/jerson/.local/share/frank-pr85-mac-qa-R1c6kmCU`，`LOCAL_EPHEMERAL_HEAD=c019f365d834dbd4f1d1ca39a8b2d95c63d753d6`，`MAC_PR85_SOURCE_PREFLIGHT=PASS`。
- 四次真实 `git merge --no-ff` 输出显示 F02 #73、C02 #84、F01 #83、QA harness #85 均 `Merge made by the 'ort' strategy`，没有冲突报告。最后内容树 `ACTUAL_TREE_SHA=eea30efa09cb1509d7eee3fde3043ee7155257cf`，完全等于 `EXPECTED_TREE_SHA`，也完全等于独立 reviewer 与 CI 已通过的精确联合树。**临时 merge commit 不要求与 CI 相同**，不可据此推断部署或发布成功。
- Mac 输出还明确：`SERVICES_STARTED=false`，`REAL_RPC=false`，`PRODUCTION_DEPLOYMENT=false`，`PRIVATE_SIDECAR_READ=false`。这些为此次预检脚本对**自身行动**的声明，不能推出别的 Mac 服务状态。旧 Mac 组装根目录及生产部署均未被本轮命令主动修改或清理。
- 因此下一关口从 `MAC_SOURCE_PREFLIGHT_PENDING` 更新为 `MAC_SOURCE_PREFLIGHT_PASS`；**`MAC_SYNTHETIC_HTTP_NOT_RUN / MAC_SAFARI_NOT_RUN / F02_REAL_CURRENT_POSITION_NOT_VERIFIED / RELEASE_NO_GO`** 仍然成立。不可把 GitHub CI 132 /1773 PASS 当作当前 Mac 真实 Safari QA。
- 下一步仅在**用户针对本版本另行明确批准**后，从上述已核验的新 `QA_ROOT/repo` 使用 `127.0.0.1:0` 与临时合成数据进行短时 native HTTP 服务及 Mac Safari 手工操作；执行前再次核对 `HEAD^{tree}`，不能启动生产 Frank V1 服务、不能真实 Solana RPC、不能读用户私有 Sidecar、不能写生产 SQLite/Gmail/发起交易。保存新浏览器截图、操作回执、实际退出结果及失败证据，保留旧数据与旧临时目录。
