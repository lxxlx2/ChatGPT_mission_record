我先读取复审材料，再逐项核对源码和修复证据。复审材料列出了 13 个必读文件，并指定了 commit `27c2c839…` 的固定地址。我按这些地址逐一读取。先并行读取核心执行文件。这个地址没有出现在之前的抓取结果中，工具拒绝了它。源码地址需要从已抓取的页面里取得。我先读取复审提示词中给出的 Stage103 整改文档，它应当包含源码的链接。这份整改文档给出了 27c2c839 版本的源码链接，我据此读取核心执行文件。Stage99 的 27c2c83 版本已读取。接下来读取 Stage102 门禁，`install()` 和 `run()` 中的 `validate_authorization()`、`interactive_install_consent()` 都在它里面。Stage102 页面返回 503。我先读取其他文件，稍后再重试。Stage103 的 worktree 测试使用真实的本地裸仓库，覆盖了远端新提交保留和远端归档冲突两个场景。Stage102 页面仍在报 503，我再重试一次。Stage102 仍然返回 503。我先读取 Stage91，稍后再尝试。Stage91 的 B4 修复已确认：符号正则允许 `_` 交割合约，缺字段时 fail-closed，交割合约保留在人口中但不计入候选。接下来读取 CI 工作流。CI 工作流的 `paths` 已补充 Stage38、80、91、97、102 与新测试，B2 的 CI 触发项已覆盖。Stage102 是 B1 的核心文件，我再重试一次。Stage102 仍然返回 503。Stage99 页面的面包屑里有 `local-agent/scripts` 目录链接，我可以从目录页读取其他脚本，稍后再重试 Stage102。目录页被 robots 规则禁止访问。接下来读取原 BLOCK 审查归档，它是提示词中给出的字面地址，也可能链接到其他源文件。原 BLOCK 归档已确认。它的正文混入了审查过程中的中间叙述，不影响结论。Stage102 是 B1 的关键文件，我再重试一次。Stage102 页面连续返回 503。我用搜索查找是否有其他可访问的来源。搜索没有找到 27c2c83 版本的 Stage102 源码。Stage102 是 B1 的核心门禁，我无法读取它。接下来检查复审材料引用的 CI 运行记录。**审查结论：`BLOCK`**

**审查主体/模型**：Claude Haiku 5.5（按会话配置；底层部署无法在对话内独立核实）。

**受审 commit**：`27c2c839d83dac11d1664d0fb6c9691844d0ca9a`

**CI 证据对应的 commit**：`0abc3046b6d9695e23b0f2af54c55ee30c7b4dff`，与受审 commit 不同（见下文）。

## 实际读取范围

**已读取（27c2c83 版本）**：

1. `monster_v4_stage99_mac_launchd_one_shot.py`（516 行）
2. `monster_v4_stage91_forward_oos_replay_gate.py`（401 行）
3. `test_monster_v4_stage103_git_worktree.py`
4. `.github/workflows/monster-stage99-mac-one-shot-capture-safety.yml`
5. Stage103 整改文档、原 BLOCK 归档文档
6. CI 运行页 `actions/runs/38372685819`（显示的 commit 为 `0abc304`）

**未能读取（受限范围）**：

- **Stage102 `monster_v4_stage102_claude_chat_review_gate.py`**：连续返回 503，搜索也未找到。`validate_authorization()`、`interactive_install_consent()` 都在这里，是 B1、B2、B3 的核心。
- **Stage97、Stage38、Stage80、`test_monster_v4_stage99_mac_one_shot.py`、`monster_v4_stage99_external_ai_review.py`、设计文档、Stage102 纠正文档、开发规则**：这些地址没有在已抓取内容中出现，工具不允许我自行拼接，因此没有读取，也没有猜测内容。
- `scripts` 目录页被 robots 规则禁止访问。
- Stage38 与 Stage80 在两轮审查中都未读取。

## B1–B4 与专项检查结论

| 项目                     | 结论                   | 依据                                                                                                                                                                                   |
| ---------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| B1 独立用户授权              | UNVERIFIABLE         | `install()` 在非 dry-run 分支中，先调用 `validate_authorization()` 与 `interactive_install_consent()`，再做 preflight，最后才写 plist 并 `launchctl bootstrap`。调用顺序 PASS；门禁内容不可读，无法确认是否要求 TTY、是否绑定审查指纹。 |
| B2 审查范围与提交绑定           | PARTIAL              | CI `paths` 已覆盖 38/80/91/97/99/102 及测试，PASS。`REQUIRED_SOURCES` 和 `reviewed_commit` 的祖先关系在门禁中，不可读，UNVERIFIABLE。                                                                        |
| B3 运行期完整性与 worktree 上传 | FAIL（运行期检查）/ 上传 PASS | 上传用临时 worktree，不改动已审代码，PASS。但运行期检查不足，见阻塞项 N-B2。                                                                                                                                      |
| B4 Binance 交割合约兼容      | PASS（离线逻辑）/ 实盘未验证    | 符号正则为 `[A-Z0-9]+(?:_[A-Z0-9]+)*`，交割合约保留在人口中、不计入永续候选；缺 `status/contractType/quoteAsset/baseAsset` 时 fail-closed。测试只用合成样本。                                                             |

**专项检查**：

- **用户独立授权**：UNVERIFIABLE，理由同 B1。
- **Claude 审查记录防绕过**：UNVERIFIABLE。原 BLOCK 归档正文混入了审查过程中的中间叙述，哈希只能证明文本完整性，不能证明来源。
- **执行时代码完整性**：FAIL，见 N-B2。
- **Git worktree 上传**：PASS。`test_monster_v4_stage103_git_worktree.py` 使用真实本地裸仓库，覆盖远端新提交保留和远端同名不同内容的拒绝覆盖。缺少“远端在 fetch 与 push 之间前进”的测试。
- **安装失败回滚**：FAIL，见 N-B1。
- **Frank 隔离**：UNVERIFIABLE。指纹只匹配标签名中的字符串 `frank`，且相关测试不可读。
- **Binance 真实数据兼容性**：逻辑 PASS，实盘未验证。

## 阻塞问题

**N-B1：安装回滚无法证明服务已卸载**

- 位置：`install()` 的 `except BaseException` 分支；`bootout()`。
- 触发：某个窗口已 bootstrap 成功，后续窗口失败或 Frank 标签变化，触发回滚。
- 原因：`bootout()` 先删除 plist，再调用 `launchctl bootout`，返回码被忽略。回滚分支无条件写入 `INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED`。
- 后果：若 bootout 失败，已加载的 launchd 服务仍在内存中，即使 plist 已删除，到 StartCalendarInterval 时刻仍会运行一次未授权的采集。状态文件却声称服务未启用。
- 修复：bootout 返回非零或超时都视为失败；回滚后用 `launchctl print gui/$UID/<label>` 确认服务不存在；确认失败则写 `ROLLBACK_FAILED_SERVICE_STILL_LOADED` 并以非零退出；只有确认后才写回滚成功。

**N-B2：stage99 运行期没有自身的代码完整性检查**

- 位置：`isolated_checkout_preflight_local()`，以及 `run()` 中的调用顺序。
- 现状：原来的 `git status --porcelain` 检查已被删除（为容忍未跟踪归档文件）。新函数只检查分支、origin 和脚本路径，不检查 HEAD 是否为受审 commit，也不检查执行路径文件是否与受审 blob 一致。
- 唯一保护是 `review_gate().validate_authorization()`，而该文件不可读。
- 修复：在 `run()` 中直接校验：HEAD 等于回执中的 `reviewed_commit`；`git status --porcelain -- <执行路径>` 为空；执行路径全部 blob 与回执一致。归档文件排除在外。

## 不可验证项（APPROVE 的前置条件）

1. **Stage102 必须可读**，并核实：`validate_authorization()` 的全部检查；`interactive_install_consent()` 是否要求 `sys.stdin.isatty()`、是否绑定审查指纹与受审代码 hash；`REQUIRED_SOURCES` 覆盖的 blob；`reviewed_commit` 是否在 HEAD 的祖先链上。
2. **CI 必须绑定到受审 commit**。运行 `38372685819` 对应的是 `0abc304`，页面显示总时长 20 秒，日志需要登录才能查看。需要在 `27c2c839` 上取得 macOS 与 Ubuntu 的成功日志，或证明两个 commit 之间执行路径的 blob 完全相同。
3. **Stage97** 的 27c2c83 版本需要确认与 fab11d3 相比没有变化。
4. **`test_monster_v4_stage99_mac_one_shot.py`** 需要读取，以确认安装回滚、Frank 标签、授权门禁的测试是否真实。
5. **Stage38/80、外部审查 tombstone、设计文档、开发规则**需要读取。

## 非阻塞问题

- **P1**：`execute()` 的 `finally` 中，`bootout()` 若抛出 `TimeoutExpired`，会覆盖退出码（上次的 N12 未修复）。
- **P2**：缺少 push 竞争测试。远端在 fetch 与 push 之间前进时，`_git_in_worktree(push)` 失败后的重试路径没有覆盖。
- **P2**：Frank 指纹只匹配标签中的 `frank`。若 Frank 标签不含该字符串，检查恒为空集合，比较总是通过。应在真实 Mac 上只读列出实际标签，并在代码中固定期望集合。
- **P2**：`validate_authorization` 在 Stage103 测试中被 mock，授权门禁没有被真实 Git 测试覆盖。
- **P3**：`safe_git_commit_and_push` 的 `finally` 中，`git worktree remove --force` 失败会掩盖原异常。应改为捕获异常，并在下次运行前执行 `git worktree prune`。
- **P3**：`install()` 仍调用带 `git status --porcelain` 的完整 preflight，而 capture 会在克隆中留下未跟踪归档，之后重装会被拒绝。应只检查执行路径中的 tracked 文件。
- **P3**：N7 未修改。StartCalendarInterval 无年份，plist 中的 `TZ=UTC` 对 launchd 无效。文档已说明，可接受。
- **P3**：BLOCK 归档正文含中间叙述文字。用于回执哈希的文本应只包含最终审查正文。

## 测试真实性区分

- **真实 Git**：`test_monster_v4_stage103_git_worktree.py` 使用本地裸仓库，无公网请求，属于真实 Git 行为的验证。
- **Mock**：授权门禁、Stage99 测试中的 launchctl（测试文件不可读）、Binance 夹具。
- **合成数据**：Stage91 的 `SYNTHUSDT`、`CATUSDT`、`BTCUSDT_261225` 都是合成记录，不是当日 Binance 响应。
- **未覆盖**：真实 Binance 响应、真实 launchctl、真实 Frank 共存、真实 Mac 睡眠与窗口行为。CI 绿灯不能替代这些验证。

## 需要的回归检查（真实 Mac 与无网络场景）

1. 在 `27c2c839` 上模拟安装回滚：让第 2 个窗口 bootstrap 失败，并让 bootout 返回非零，确认服务最终不在 `launchctl print` 中。
2. 不经 TTY 调用 `install`，必须失败。
3. 修改执行路径中的一个 tracked 文件后运行，必须拒绝。
4. HEAD 不等于受审 commit 时运行，必须拒绝。
5. 远端在 fetch 与 push 之间前进，验证重试且不覆盖远端内容。
6. 用脱敏的真实 exchangeInfo 样本（含交割合约）离线运行 `freeze_universe()`。
7. 真实 Mac 只读列出 Frank 标签，安装前后对比。

## 结论

**不足以等待用户单独批准安装。** 需先修复 N-B1 与 N-B2，并取得 Stage102 的可读内容、将 CI 绑定到 `27c2c839`、读取不可读的测试文件，之后才能进入新一轮审查。当前不授权安装。

本次审查未修改 Git、未安装任何定时任务、未执行部署。