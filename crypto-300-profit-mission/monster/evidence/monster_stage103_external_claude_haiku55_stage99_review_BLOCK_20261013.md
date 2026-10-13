我先读取审查材料，再逐个核对材料中列出的源码和测试。材料列出了 10 个源文件、测试和规范，我按顺序读取它们。核心脚本已读取。我记下几处需要核对的地方：`safe_git_commit_and_push_for_review` 在 `install` 中未被调用、`install` 中途失败不回滚、调度时间与审查材料中“05:45–06:00”的描述是否一致，以及 `verify_approved()` 的实际实现。接下来读取 Stage97 采集器和 Stage102 审查门禁。Stage97 的时点证据与时钟校验逻辑已读取。接下来读取 Stage102 审查门禁，这是 `install()` 调用的 `verify_approved()` 所在模块。Stage102 门禁已读取。它只校验用户提供的审查回执，核对 5 个源文件的 blob，并没有绑定 commit，也没有核对用户对安装的授权。接下来读取 Stage91（时间窗口和 `freeze_universe` 定义在这里）和测试文件。Stage91 已读取。它定义了固定窗口 `2026-10-14T06:00:00Z` 等，因此 Stage99 的 05:48 启动、05:45–06:00 采集窗口与审查材料一致。但 Stage91 不在 Stage102 的 5 文件 blob 绑定列表中，却在执行路径里。接下来读取测试文件和 CI 工作流。测试文件已读取。测试以 mock 为主，`verify_approved` 的 blob 比对用的是 `lambda _: "a"*40` 替身，`isolated_checkout_preflight` 没有在真实 Git 仓库上测试。接下来读取 CI 工作流和遗留 Claude CLI 入口。CI 工作流已读取。它的 `paths` 触发器不包含 `monster_v4_stage91_forward_oos_replay_gate.py`，而 Stage91 恰恰在执行路径中。接下来读取遗留的 Claude CLI 入口，确认它的安装路径是否真的被切断。遗留 CLI 入口已读取。`review-install` 在 argparse 层被拒绝，但 `review_with_claude` 和 `review_then_install` 仍然存在、可以被导入调用，并且保留了 `claude -p` 的调用代码。最后，我需要读取材料列出的三份设计和开发规范，确认代码是否符合其中约定的规则。开发规范已读取。其中第 6 条明确规定：未经用户逐项明确授权，严禁创建、启用、恢复或修改 launchd 定时任务，安装必须在审查通过后再次由用户授权。这与 `install()` 的实际门禁直接对照。接下来读取 Stage99 设计文档。设计文档已读取。它仍写着“用户运行 `review-install` 并调用 Claude Code CLI”，与当前代码中已撤回该流程的状态不一致。最后读取 Stage102 纠正与权限规则文档。我先把审查中确认的项目状态存入记忆，之后给出审查结论。**Review结果**：`BLOCK`

**审查主体/模型**：Claude Haiku 5.5（按当前会话配置；无法在对话内独立核实底层部署）。

**目标commit**：`fab11d34451388808c5045118f933d542c77ecbe`

**实际读取文件**（均为该 commit 的 GitHub blob）：

1. `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py`
2. `…/scripts/monster_v4_stage97_one_shot_usdm_capture.py`
3. `…/scripts/monster_v4_stage102_claude_chat_review_gate.py`
4. `…/scripts/test_monster_v4_stage99_mac_one_shot.py`
5. `.github/workflows/monster-stage99-mac-one-shot-capture-safety.yml`
6. `…/scripts/monster_v4_stage91_forward_oos_replay_gate.py`
7. `crypto-300-profit-mission/monster/MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md`
8. `crypto-300-profit-mission/monster/MONSTER_STAGE102_LOCAL_COLLECTION_CHAT_REVIEW_AND_PARALLEL_MODEL_BOUNDARY_20261013.md`
9. `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`
10. `…/scripts/monster_v4_stage99_external_ai_review.py`

**未读取（须说明）**：`monster_v4_stage38_usdm_original_v4_1m_pilot.py` 与 `monster_v4_stage80_dual_entry_core.py`。Stage91 在模块导入期导入它们，Stage97 与 Stage99 又导入 Stage91，所以它们的顶层代码每次安装和运行都会执行。材料未列出，我没有读取，因此无法排除导入期副作用（包括对 Frank 的读写）。这一项本身不足以支持 APPROVE。

**行号说明**：抓取文本未保留可靠行号，以下以函数名和常量名定位。

**阻塞问题**

**B1 安装门禁只看自证回执，没有用户授权**

- 位置：Stage99 的 `install()`（非 dry-run 分支）；Stage102 的 `verify_approved()`。
- 原因：`install()` 只调用 `ai_review.verify_approved()`，随后执行 `git push --dry-run` 和 `launchctl bootstrap`。代码里没有任何用户确认步骤，没有 `input()`，没有确认令牌，回执也没有用户授权字段。`verify_approved()` 自己的返回值标注 `USER_ATTESTED_NOT_CRYPTOGRAPHIC`。回执中的 `full_claude_reply` 只检查与自身 SHA 一致且长度 ≥160，`reviewed_risks_and_test_evidence` 只要求 ≥3 项。按 Stage102 文档，回执由研发侧构造，因此研发侧（包括能运行 shell 的自动化代理）可以自己生成 APPROVE 回执并直接安装。
- 与规范冲突：`MONSTER_MODULE_DEVELOPMENT_RULES.md` 写明“未经用户逐项明确授权，严禁创建、启用…launchd 定时任务”，且安装必须在审查通过后“再次得到用户明确授权”。回执也没有记录规范要求的 reviewer 模型、审查 commit 等字段。
- 修复：`install()` 必须要求用户手动输入一次性确认令牌，令牌绑定回执 SHA 和执行路径全部 blob 集合。回执增加 `reviewer_model`、`reviewed_commit`、`user_install_authorization`（逐字引用用户授权语句及时间）。`verify` 同时校验这些字段。

**B2 绑定范围缺失 Stage91 及其依赖，CI 也不会触发**

- 位置：Stage102 的 `REQUIRED_SOURCES`（5 项，不含 Stage91）；workflow 的 `on.push.paths`（不含 Stage91 与 Stage97）。
- 原因：`install()` 调用 `stage91.verify_window`、`stage91.WINDOWS`、`stage91.d1.utc_ms`；Stage97 使用 `stage91.EXCHANGE_INFO_URL` 与 `freeze_universe()`。这些决定窗口日期、调度时刻、官方端点和数据校验，却不在回执的 blob 绑定中。修改 Stage91 的 `WINDOWS` 或校验逻辑后，旧回执仍然 APPROVE，安全 CI 也不会运行。作者在 Stage99 的 `external_ai_review.py` 中的 `REVIEW_TARGETS` 已经包含 Stage91，但实际安装使用的是 Stage102 门禁，二者不一致。
- 修复：`REQUIRED_SOURCES` 覆盖全部执行路径（Stage91、38、80、97、99、102 及 CI 文件）；workflow paths 补充 Stage91、97、38、80；回执同时绑定 commit SHA。

**B3 运行期不复核代码，push 失败时 rebase 可能引入未审代码**

- 位置：Stage99 `safe_git_commit_and_push()` 的重试分支（`git fetch` 后 `git rebase FETCH_HEAD`）。`run()` 与 `execute()` 都不调用 `verify_approved()`，也不核对 blob。
- 原因：推送失败时，克隆会 rebase 到远端分支最新提交。该分支是活跃开发分支，远端可能有未审提交。之后各窗口的 launchd 任务都是新进程，直接执行磁盘上的 `Path(__file__)`。`isolated_checkout_preflight()` 只检查分支、远端 URL 和工作区是否干净，不检查代码是否为已审版本。
- 修复：`run()` 开始时校验执行路径全部 blob 与回执一致，否则拒绝执行。push 重试不得改动执行路径文件，证据提交应在不改动代码工作区的 worktree 中构造。

**B4 真实 exchangeInfo 含交割合约时，`freeze_universe()` 很可能拒绝整份快照**

- 位置：Stage91 `freeze_universe()` 的 symbol 校验：`not symbol.isalnum()` 触发 `STAGE91_MARKET_SYMBOL_DUPLICATE_OR_INVALID`。
- 原因：`isalnum()` 对含下划线的字符串返回 False。Binance USD-M 交割合约代码形如 `BTCUSDT_YYMMDD`，含下划线。依据这一命名规则，真实响应会在此处抛错，`verify_time_proof()` 随之失败，Stage99 重试 3 次后得到 `SOURCE_FAILED`，三个窗口全部失败。这是高置信度推断，我未能抓取当日真实响应复现，本次审查也不应为此获取未来数据。自测只用合成符号 `SYNTHUSDT`、`CATUSDT`，所以测试没有覆盖此情况。这一缺陷是 fail-closed，不会产生伪证据，但会使采集功能整体失效。
- 修复：校验改为只拒绝重复与非法字符，允许 `_` 和数字；非 PERPETUAL 合约保留在 population 中但不计入候选。加入脱敏的真实 exchangeInfo 样本（含交割合约）作为离线回归测试。

**非阻塞问题**

- **N1（高）安装非原子**：`install()` 循环中逐个 bootstrap，若第 2 个窗口 plist 已存在则抛错，第 1 个已加载任务无回滚。应先检查三个 plist 均不存在，失败时逆序 bootout 并删除已写入的 plist。
- **N2（高）rebase 冲突无 abort**：`safe_git_commit_and_push()` 中 rebase 失败后仓库停留在进行中的 rebase 状态，`git branch --show-current` 返回空，之后 `isolated_checkout_preflight_for_saved()` 永久失败。应在失败时 `git rebase --abort`，并把 `TimeoutExpired` 纳入重试。
- **N3（中）采集依赖 GitHub 可达**：`run()` 在采集前调用 `isolated_checkout_preflight()`，其中 `git ls-remote` 最长等待 35 秒。若此刻 GitHub 不可达，即使 Binance 正常也不会采集，窗口失效。时间敏感的部分应先采集，再上传。失败后 launchd 不会自动重试上传，只能手工 `retry-push`，设计文档应写明。
- **N4（中）提交作者冒用 github-actions[bot]**：`user.email=41898282+github-actions[bot]@…`。证据与审查归档会被误认为 Actions 产出，应使用明确的本机身份。
- **N5（中）authenticity 标签超出证据能力**：SHA 与时间戳均由 Mac 自算自记，只有 TLS 与时钟漂移检查，没有 Binance 签名。`RECORDED_HTTPS_…` 标签可保留，但文档和回执应明确写“自记录，非密码学证明”。
- **N6（中）数据不完整不拒绝**：`freeze_universe()` 对缺失 `status`、`contractType`、`quoteAsset` 的行静默视为非候选但仍计入 population，与“数据不完整如何拒绝”的要求不符。
- **N7（低）调度残留**：`StartCalendarInterval` 无年份。若某窗口当日 Mac 关机，plist 会残留到次年同日再次触发，之后 MISSED 并卸载。plist 中的 `TZ=UTC` 对 launchd 日历调度无效，launchd 按系统本地时区解释。
- **N8（中）Frank 共存未校验**：规范要求“先校验共存、资源占用、隔离”，`install()` 未检查 Frank 的 label、端口或资源。测试 `test_uninstall_can_only_mention_our_exact_three_labels` 只做字符串检查，不是隔离测试。
- **N9（中）死代码与遗留路径**：`Stage99 external_ai_review.py` 中的 `review_with_claude()`（含 `claude -p`）、`review_then_install()`、`safe_git_commit_and_push_for_review()` 仍可导入。`…_actual_external_claude_ai_review.json`与 Stage102 门禁读取的`…_actual_claude_chat_independent_review.json`路径不一致。argparse 拒绝只切断了 CLI 入口，“本地不依赖 Claude CLI”仍只是口头承诺。
- **N10（中）设计文档过时**：`MONSTER_STAGE99_…_DESIGN` 仍写“用户运行 `review-install`”和“Claude Code CLI”，与当前代码（已撤回）及开发规则（用户使用 Claude 对话、不假定本地有 CLI）冲突。安装前必须修订。
- **N11（中）测试可信度有限**：大部分测试以 mock 替换 git、launchctl 与校验函数。`verify_approved()`的 blob 比对用`lambda _: "a"*40`替身；`isolated_checkout_preflight()`从未在真实 Git 仓库上执行；`job_plist()`默认`user_tz=None`路径的 StartCalendarInterval 未断言。CI 绿灯不能证明真实 Binance 或真实 launchd 行为，设计文档也已如此说明。
- **N12（低）bootout 的异常路径**：`execute()`的`finally`调用`bootout()`，其中`launchctl`超时20秒会抛出`TimeoutExpired`，覆盖退出码。plist已先被删除，服务可能残留到重启。

**已核实通过的部分**

- **本地定时**：官方 WINDOWS 为`06:00Z`，安装05:48 UTC（曼谷12:48）与采集窗口05:45–06:00严格检查一致；错过窗口为MISSED且不补抓。
- **Binance真实性**：官方URL白名单、重定向与JSON类型检查、原始字节SHA、5秒时钟漂移检查、`serverTime`不作为时钟来源、因果时序检查、重复symbol与空快照拒绝，均已实现。
- **Git上传**：分支、远端URL精确白名单、非强推、staged路径白名单、凭证不进日志（git stderr被丢弃）。
- **失败恢复**：push失败时保留SHA，重试不再采集，已有测试覆盖。
- **执行后退出**：`execute()`的`finally`中有`bootout`，且plist先删除。
- **Frank**：执行路径代码未引用Frank，label与目录独立。

**回归检查要求**（真实Mac与无网络场景）

1. 断网运行`run`：应SOURCE_FAILED，无push，无伪造状态；`launchctl print`确认job已卸载。
2. 用脱敏的真实exchangeInfo样本（含`_`交割合约）离线运行`freeze_universe()`：应通过，或以明确原因拒绝，不得误报为DUPLICATE_OR_INVALID。
3. 修改Stage91的`WINDOWS`一个字符：回执校验必须失败；未经确认令牌执行`install`必须拒绝。
4. 模拟push失败，并让远端分支新增修改Stage99的提交：`run`必须拒绝执行未审代码。
5. 两次install中第二个窗口plist已存在：第一个窗口的plist必须被回滚。
6. 非UTC的macOS时区（如Asia/Bangkok）：`launchctl print`显示的调度对应05:48 UTC；睡眠跨过06:00时为MISSED且无补抓。
7. 安装前后对比`launchctl list`，确认Frank相关label、端口和进程无变化。
8. 执行后确认`launchctl print gui/$UID/<label>`不存在，且plist文件已删除。

**结论与允许行为**

- 本次判定`BLOCK`。不允许在Mac安装或启用任何launchd任务，也不允许据此进入“用户批准安装”阶段。
- 对你关心的几个问题的直接回答：能否绕过？**能**。伪造回执即可通过安装门禁（B1）；旧回执对Stage91等未绑定文件的改动不会失效（B2）。未经用户明确授权的安装**未被代码阻止**（B1）。
- 修复B1–B4，并处理与安装相关的N1–N4、N8–N10后，须在新commit上重新提交Claude对话审查。旧回执对新commit无效。
- 本审查不构成Monster策略部署、Frank变更或交易授权；Monster部署仍为`NO_GO`。
- 本回复原文需由研发负责人原样归档到PR #30。我不能自行生成回执，也不能把本回复当作用户的安装授权。
