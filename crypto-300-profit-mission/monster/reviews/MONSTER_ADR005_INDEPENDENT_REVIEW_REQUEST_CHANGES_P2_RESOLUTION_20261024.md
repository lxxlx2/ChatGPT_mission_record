# Monster ADR-005：独立审核 REQUEST_CHANGES 与 P2 修复证据（2026-10-24）

## 审核对象和实际结论

- 审核固定 SHA：`06aa72fceeb63c73375b556e7f8d44509452207a`，并非当时的后续文档 HEAD `03a2b9af2142a9df6fe6335dc022716968127753`。
- 审查由用户转交的**其他 AI / 独立 detached worktree 报告**提供；审核者确切模型名称在本次反馈中**未独立核实**，因此仅记 `REVIEW_REPORT_USER_PROVIDED / REVIEWER_MODEL_UNVERIFIED`，不可伪写已被 ChatGPT 亲自复现于 Mac。
- 独立审查结论：**REQUEST_CHANGES**；该固定 SHA 的比较器数学、六根已闭合 5m、币/BTC 同一 UTC 时钟、SOURCE_CENSORED 语义没有发现 P0/P1；P2：既有 preflight CLI 测试引用错误的相对路径，完整队列重复 episode、G2/G3真实产品表现仍未验证。
- 报告所用用户 Mac Python 3.14.7、detached 固定 SHA、只读；实测九组 Monster CI `110/110 PASS`、原 Shadow `31/31 PASS`；扩展 `test_monster_v4_spot511*.py` 探索总计31项，**30 PASS + 1 ERROR**。此失败不得被错误改写为旧版本的31/31全通过。
- P2 准确位置：`crypto-300-profit-mission/local-agent/tests/test_monster_v4_spot511_replay_preflight.py:109`：
  - 旧：`Path(__file__).with_name("monster_v4_spot511_replay_preflight.py")`，错误寻找 `tests/` 下的脚本；子进程退出码2。
  - 新：`Path(__file__).resolve().parents[1] / "scripts" / "monster_v4_spot511_replay_preflight.py"`。
  - 预期行为：第一次将离线JSON preflight输出写入临时目录，第二次对相同路径返回 `REFUSE_EXISTING_PREFLIGHT_OUTPUT`；不会请求市场、交易或启动后台任务。

## 本轮实际修复与CI

- `849c76e2be7751d26b770cf5b85ba1fd7f593365`：**只改 preflight 测试的CLI文件路径**，不改研究候选、原D0/D1或历史ZIP、事件ID。
- `9b049dd32bee0a34940fa61f73791377ae883cd9`：让常规 `.github/workflows/monster-spot511-manual-source-batch-ci.yml` 的 push/PR path触发条件、语法检查和单元测试**显式纳入** `test_monster_v4_spot511_replay_preflight.py`（9项）、`test_monster_v4_shadow.py`（31项）及被测preflight脚本；此前111项之类不完整计数须以实际日志为准。工作流**没有**schedule、市场下载、实盘、Mac操作、邮件或新后台监控。
- 新版[GitHub Actions #40103975065](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40103975065)：Job `120901708104`，实际 `SUCCESS`，11组分别`13+5+6+11+19+12+12+14+18+9+31=150/150 PASS`，新preflight CLI组`9/9 PASS`，`test_cli_report_written_once_without_network`在GitHub Runner上确实通过并验证拒绝覆盖；新增后的原shadow`31/31`，预注册研究比较器`18/18`。该工作流Python 3.11，不代表修复后的Mac 3.14.7已由独立reviewer重跑。
- 上述结果是**P2修复后云端回归已过**，而不是将原审查 SHA `06aa72...` 的 `REQUEST_CHANGES` 改为 `APPROVE`。

## 后续审核和产品门禁

- **固定旧 SHA 的独立审核历史仍为 `REQUEST_CHANGES`**。
- 新HEAD的P2更改属于测试文件和CI，研究比较器Git Blob必须保持 `9d32d03f4b64f1dcfa1c7016cead6a377df27271`，原 `monster_v4_shadow.py` Git Blob必须保持 `bc958b3d90a8a52afa51515cb53f7e5fafaffaaa`。如要将新HEAD代码审核升级为真正独立 `APPROVE`，须让审查者核对修复diff并实际回执 `APPROVE/REQUEST_CHANGES/BLOCKED`，不能靠现有AI自查或Github CI假冒独立审核。
- 新比较器仍只是**纯离线 research function**，尚未接线原SQLite episode恢复/超时/重试/去重，不能证明 G2 提前>=5min召回>=80%，不能证明新G3日均<=5/峰值<=12，也不能从OHLC推导真实D2净收益。
- ADR-005 已预注册未来不可择优替换的UTC三段`2026-11-02..09`、`11-16..23`、`12-01..08`，未来资料尚未读；原 `2026-10-24`完整Publisher日仍需实际闭日且ZIP/CHECKSUM发布后才计入511/511。
- 当前强制边界：`G0 PARTIAL / G1 NOT_SCORABLE / G2 NOT_PASSED / G3 NEW_VERSION_UNVERIFIED / G4 UNKNOWN / G5 REQUEST_CHANGES_FIXED_P2_CI_PASS_PENDING_INDEPENDENT_REREVIEW / G6 NO_GO`；`NO_MERGE / NO_DEPLOY / NO_MAC / NO_TRADES / NO_GMAIL / NO_AUTOMATIONS`。

## 对新固定SHA的最小独立复审提示词（可直接复制到Claude网页）

> **独立代码复审：仅检查上一轮 P2 修复，不混入下一阶段完整D1集成准入。**
>
> 仓库：`lxxlx2/ChatGPT_mission_record`，PR #30，分支 `research/monster-v4-local-discovery-20261010`。**新审核固定SHA：`9b049dd32bee0a34940fa61f73791377ae883cd9`**。上一轮旧固定SHA `06aa72fceeb63c73375b556e7f8d44509452207a` 的审核结论是 `REQUEST_CHANGES`，P2位于 `crypto-300-profit-mission/local-agent/tests/test_monster_v4_spot511_replay_preflight.py:109`。本次只批准审查修复差异；不要重新批准旧SHA，也不要将后续仅文档提交纳入本次审查。
>
> 请使用只读独立 detached checkout，读取 Stage77 标准、ADR-004/ADR-005、Monster 模块开发规则，逐行比较旧SHA与新SHA：`tests/test_monster_v4_spot511_replay_preflight.py` 从 `Path(__file__).with_name(...)` 改为 `Path(__file__).resolve().parents[1] / 'scripts' / ...`；检查 `.github/workflows/monster-spot511-manual-source-batch-ci.yml` push和PR的路径触发、py_compile及单元测试组里加入 preflight CLI 与 `test_monster_v4_shadow.py`。确认没有修改原D0/D1核心、ADR-005数学与将来三段日期，也没有增加自动任务、交易、Mac、Frank或邮件副作用。
>
> 请在有 Python 的只读隔离目录实际重跑如下命令（使用自身环境，不要让用户Mac启动监控）：
>
> ```zsh
> cd crypto-300-profit-mission/local-agent
> PYTHONPATH=.:scripts python3 -B -m unittest discover -s tests -p 'test_monster_v4_spot511_replay_preflight.py' -v
> PYTHONPATH=.:scripts python3 -B -m unittest discover -s tests -p 'test_monster_v4_shadow.py' -v
> PYTHONPATH=.:scripts python3 -B -m unittest discover -s tests -p 'test_monster_v4_d1_rbtc15_last5_research.py' -v
> ```
>
> 云端参考证据：[GitHub Actions #40103975065](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40103975065)，job `120901708104`，11组总`150/150 PASS`，包含 preflight 9/9、shadow 31/31、RBTC15 18/18；但不能引用云端PASS代替实际独立复审。重点确认 CLI首次创建JSON成功，第二次拒绝覆盖并返回错误。
>
> 请输出 `APPROVE | REQUEST_CHANGES | BLOCKED`，明确新固定SHA、审核者模型和版本、实测环境、每组真实结果、P0/P1/P2问题及文件/行号与复现步骤，并明确**`P2原阻断是否关闭`**。如修复通过，只批准测试路径/回归覆盖修复；**不批准新D1完整 episode生命周期、原 D0/D1产品G2/G3、历史盘口G4、样本外验证与上线G6**。未知写UNKNOWN。最后重申 `NO_MERGE/NO_DEPLOY/NO_TRADES/NO_GMAIL/NO_AUTOMATIONS`。
