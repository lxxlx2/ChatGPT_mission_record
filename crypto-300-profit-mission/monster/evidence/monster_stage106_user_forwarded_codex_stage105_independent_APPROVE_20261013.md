**审查结论：`APPROVE`。**

固定受审 commit：`2f25f2b921a97ab864ced7a0bc93aab1c9e85169`\
审查范围：Monster 原 PR #30 的本地一次性 USD-M 研究快照采集器、隔离 Git 上传、执行后卸载及相关授权门禁。\
审查主体：**Codex**；底层精确模型标识：`UNKNOWN`。本次没有调用 Claude，也不能将报告归档为 Claude 审查。

**上轮 N-B2 与 N-B3 在本次指定范围内均判定 PASS。** 我完整读取了材料要求的 12 份文件，核对固定 SHA 和 blob 清单，实际重跑了 29 项测试与 5 个离线自测，并核实了准确 SHA 的 macOS/Ubuntu CI 日志。没有发现需要继续阻止该研究采集器进入“用户之后另行明确批准安装”阶段的实际阻塞问题。

**这个 APPROVE 是代码审查结论，不是安装授权，不代表真实 Mac 或真实 Binance 采集已验收。**

**读取与固定版本证据**

受审临时副本最终 HEAD 为上述完整 SHA，`git status --short` 为空。全文包的 12 个 blob 均与固定 commit 和本地原始文件计算结果一致；没有使用最新分支代码替代受审版本。[Stage105 完整审查包](https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/monster-v4-local-discovery-20261010/crypto-300-profit-mission/monster/MONSTER_STAGE105_FROZEN_REVIEW_FULL_SOURCE_20261013.md)

以下为实际全文读取清单。脚本均位于 `crypto-300-profit-mission/local-agent/scripts/`，两份文档位于 `crypto-300-profit-mission/monster/`。

| #  | 实际全文读取文件                                                            | 行数  | Git blob 前缀    |
| -- | ------------------------------------------------------------------- | --- | -------------- |
| 1  | `monster_v4_stage105_capture_universe_core.py`                      | 139 | `1431573db90d` |
| 2  | `monster_v4_stage97_one_shot_usdm_capture.py`                       | 240 | `1d4fb2dffed8` |
| 3  | `monster_v4_stage99_mac_launchd_one_shot.py`                        | 608 | `2543c2547366` |
| 4  | `monster_v4_stage102_claude_chat_review_gate.py`                    | 229 | `c73aedbbb503` |
| 5  | `test_monster_v4_stage99_mac_one_shot.py`                           | 438 | `df8705534297` |
| 6  | `test_monster_v4_stage103_git_worktree.py`                          | 159 | `e614326c0aa1` |
| 7  | `test_monster_v4_stage105_capture_import_isolation.py`              | 67  | `06f1cb796488` |
| 8  | `.github/workflows/monster-stage99-mac-one-shot-capture-safety.yml` | 63  | `74dc578ecb14` |
| 9  | `monster_v4_stage91_forward_oos_replay_gate.py`                     | 301 | `6f9db6dab450` |
| 10 | `MONSTER_MODULE_DEVELOPMENT_RULES.md`                               | 77  | `55668e29cac3` |
| 11 | `monster_v4_stage99_external_ai_review.py`                          | 22  | `429dac1b52de` |
| 12 | `MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md`       | 23  | `47d322c26425` |

**指定文件未读项：无。** 另已读取 Stage105 审查请求、整改报告、上轮 Codex BLOCK 归档和 Monster `AGENTS.md`。

**N-B2：PASS——历史模块导入链已从采集进程移除**

这次采用了实际减依赖的修复：

- Stage97 第 17–20 行改为导入 `monster_v4_stage105_capture_universe_core`。
- Stage99 第 21–26 行仅导入 Stage97 和 Stage105；变量别名虽然仍叫 `stage91`，实际对象已经是 Stage105。
- Stage105 只导入标准库，提供冻结窗口、时间转换与人口验证，没有导入 Stage91、Stage38、Stage80、Shadow 或历史回放模块。
- Stage91 研究端直接复用 Stage105 的 `freeze_universe()`、`verify_window()` 等函数；依赖方向是研究端使用采集核心，没有反向进入采集进程。
- Stage102 第 31–40 行冻结清单覆盖四个实际采集/门禁 Python 文件、三个测试文件和 CI 工作流。[Stage97 导入](https://github.com/lxxlx2/ChatGPT_mission_record/blob/2f25f2b921a97ab864ced7a0bc93aab1c9e85169/crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py#L17)、[Stage99 导入](https://github.com/lxxlx2/ChatGPT_mission_record/blob/2f25f2b921a97ab864ced7a0bc93aab1c9e85169/crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py#L21)、[冻结清单](https://github.com/lxxlx2/ChatGPT_mission_record/blob/2f25f2b921a97ab864ced7a0bc93aab1c9e85169/crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py#L31)

**新增导入隔离测试有效。** 它将四个实际采集/门禁文件复制到临时目录，将五个历史模块替换为“导入立即写磁盘标记并抛错”的夹具，然后通过 `subprocess.run([sys.executable, "-c", ...])` 启动新解释器。断言包括子进程成功、危险模块未进入 `sys.modules`、危险标记不存在，以及 Stage97 与 Stage99 使用同一个 Stage105 模块对象。它不会受父进程已导入模块的缓存影响。[新进程测试](https://github.com/lxxlx2/ChatGPT_mission_record/blob/2f25f2b921a97ab864ced7a0bc93aab1c9e85169/crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage105_capture_import_isolation.py#L34)

真实本地 Git 测试也已把修改目标从 Stage91 改为**实际采集依赖 Stage105**，分别验证未提交修改被 dirty 检查拒绝、提交后的未经审查修改被 tree blob 检查拒绝。

因此，上轮“遗漏历史模块在门禁前执行，同时八文件检查仍通过”的具体路径已经消除。这个结论不扩展为抵御 Python 入口自身被任意替换或操作系统被控制的安全保证。

**N-B3：PASS——状态文件持续磁盘满不再中断剩余回滚**

Stage99 `install()` 第 284–314 行将卸载与状态记录分成独立异常处理：

1. 每个已创建窗口都先尝试 `bootout()`。
2. 卸载失败加入内存中的 `rollback_failures`。
3. 状态写入失败加入独立的 `journal_failures`，输出 stderr 诊断。
4. 继续处理更早创建的窗口。
5. 最后汇总失败并抛出异常，不返回安装成功。

严格的 `bootout()` 仍保留：非零返回拒绝；成功后调用 `assert_unloaded()` 检查 `launchctl list` 与 `print`；核对通过才删除 plist。[回滚处理](https://github.com/lxxlx2/ChatGPT_mission_record/blob/2f25f2b921a97ab864ced7a0bc93aab1c9e85169/crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py#L284)

两个新增测试覆盖了上轮实际故障路径：

- `test_stage105_enospc_status_write_does_not_interrupt_other_bootouts`：第二个窗口 bootstrap 后首次状态写入失败，两次回滚状态也失败；核对调用顺序为两次 bootstrap、两次 bootout，并检查两个 plist 均删除。
- `test_stage105_disk_full_and_one_failed_unload_still_attempts_every_service`：状态持续失败，同时第二个窗口 bootout 返回非零；仍卸载第一个窗口，第二个窗口的 plist 保留，最后抛错。[磁盘满测试](https://github.com/lxxlx2/ChatGPT_mission_record/blob/2f25f2b921a97ab864ced7a0bc93aab1c9e85169/crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py#L223)

我还按上轮复现方式额外验证了原始 `install()` 的控制流，结果为：
```
bootstrap_calls: 2
rollback_attempts:
  ['2026-10-28T06:00:00Z', '2026-10-14T06:00:00Z']
first_successfully_bootstrapped_job_rolled_back: True
fallback_diagnostic_lines: 2
raised:
  STAGE105_INSTALL_ROLLBACK_SAFETY_UNVERIFIED
  services=
  journal=2026-10-28T06:00:00Z,2026-10-14T06:00:00Z
```

上轮被跳过的第一个窗口，现在得到回滚尝试。这里的服务操作仍为模拟；没有操作用户真实 launchd。

**测试与 CI 核实**

我通过 GitHub API、job 步骤状态和日志核实：

| 项目         | 实际结果                                         |
| ---------- | -------------------------------------------- |
| CI Run     | `38383381420`                                |
| `head_sha` | `2f25f2b921a97ab864ced7a0bc93aab1c9e85169`   |
| Ubuntu job | `115249067908`，`success`                     |
| macOS job  | `115249068099`，`success`                     |
| 每个平台测试     | 24 项安全/故障测试 + 4 项本地 Git 测试 + 1 项新进程导入测试，全部通过 |

日志中两项 Stage105 磁盘满测试、新进程导入测试、源码 dirty/recommit 测试和推送竞争测试均有实际执行记录。[准确 SHA 的双系统 CI](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38383381420)

本地临时副本也实际通过 **29 项测试和 5 个离线自测**。测试真实性需要区分：

- **真实行为：**新 Python 子进程、临时文件导入副作用检测、本地裸仓库的 clone/fetch/worktree/commit/push。
- **模拟行为：**launchctl、Frank 标签、授权交互和故障注入。
- **合成数据：**Binance 时间与市场响应夹具。
- **尚未验收：**用户真实 Mac 服务生命周期、实际 Frank 共存、未来窗口的真实 Binance 响应与远端上传。

**附带复核与非阻塞建议**

授权、数据与上传主路径未见本轮引入的阻塞回归：

- Stage102 支持用户提供的 Codex 或 Claude 聊天来源，但仍要求结构化 `APPROVE`、空阻塞列表、完整答复哈希、受审源码 blob 和祖先关系。旧 `BLOCK` 不会仅因新增 Codex 来源选项而自动通过。
- 安装仍需要独立授权 manifest，以及 stdin/stdout 为 TTY、现场输入指纹绑定短语。哈希只证明内容一致性，真实用户与审查来源仍需按人工归档流程核对。
- Stage105 保留交割合约下划线兼容、完整人口与永续候选分离、缺字段拒绝；Stage97 继续使用独立 `/time` 前后校时及三段原始 SHA。
- Git 上传继续使用临时 worktree；不改执行目录 HEAD、不 rebase、不强推，同名不同字节拒绝覆盖，fetch/push 竞争有真实本地 Git 覆盖。

保留三项非阻塞建议，不作为本轮继续 BLOCK 的理由：

1. **`uninstall()` 幂等性：**某个窗口已自动卸载时，严格 bootout 失败会提前结束，后面的窗口未处理。可在明确核实不存在后继续处理其余窗口。
2. **备用诊断输出：**回滚分支的 stderr `print()` 本身未隔离写入异常。如果安装时另外将 stderr 重定向到失败设备，可能再次中断循环；建议把诊断输出也做成尽力记录、不能影响卸载。这是额外的输出通道失败条件，当前新增 ENOSPC 测试没有覆盖。
3. **设计文档同步：**Stage99 设计文档仍描述旧 Stage38/80/91 冻结清单及 Claude 专用措辞，应同步为实际 Stage105 清单与 Codex/Claude 来源。当前执行门禁已经使用新清单。

**放行范围**

本次 `APPROVE` 足以进入：**由用户之后另行明确批准，才考虑在 Mac 安装仅研究快照采集器**的阶段。它没有放行 Monster 策略部署、Shadow、交易、邮件或 Frank 变更；历史模型研发继续独立推进，不需要等待这三个未来采集窗口。

本轮仅做审查与离线验证，没有修改受审代码，没有提交或推送，没有安装、部署、创建或启用任何定时任务。**用户安装授权仍为 `NOT_GIVEN`，真实 Mac 与真实采集验收仍为 `NOT_DONE`，Monster 生产部署继续保持 `NO_GO`。**