# Monster Stage103：Claude Haiku 5.5 BLOCK 修复及本地采集器二次审查前交付

2026-10-13 Asia/Bangkok；原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。此轮仅开发/离线测试**本地来源采集器**，严禁创建、恢复或修改用户ChatGPT任务或Mac launchd服务。本轮**未**取得独立二次Claude APPROVE，**未**取得用户单独安装授权。

## 审查记录与结论

[用户实际提交的 Claude Haiku 5.5 旧代码版本 BLOCK 审查记录](evidence/monster_stage103_external_claude_haiku55_stage99_review_BLOCK_20261013.md)；被审代码commit：`fab11d34451388808c5045118f933d542c77ecbe`，不能复用该旧Review作为批准。归档为用户转交的审查文字，非从Claude后台自动读取或由Git密码学证明审查主体。Claude指出四个阻塞问题 B1-B4 和十二个其他观察，按以下代码修复；**独立审查者尚未验证修复后结果**。

## 四个阻塞问题逐项对应

| 原问题 | 修复源码 | 实际修复，不可夸大 |
|---|---|---|
| B1 单凭自证Claude回执就安装，无用户同意 | [Stage102/103双重审核与授权关口](../local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py)、[Stage99 install()](../local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py) | 完整真实Claude**对话**答复、reviewer_model及reviewed_commit与代码blob校验；另有**独立**`monster_stage103_explicit_user_local_install_authorization.json`（只在用户对修复后版本重新明确授权后建立，记录原话、时间、scope、源hash）和现场TTY手输与审查摘要绑定的确认短语。审查回复本身不是用户授权。任何缺项拒绝。SHA仅证明文字完整性，不能密码学证明是人实际输入，必须保证工作流不代拟用户授权 |
| B2 Stage91和上游代码未纳入review，CI不触发 | [Stage102/103`REQUIRED_SOURCES`](../local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py)、[Stage99专项GitHub CI](../../.github/workflows/monster-stage99-mac-one-shot-capture-safety.yml) | 完整执行链含Stage38/80/91/97/99/102、原安全测试与CI文件共8个Git blobs；reviewed_commit必须在当前Git HEAD祖先链，blob逐个一致；CI paths与Python编译添加Stage38/80/91/97以及新Gate/测试 |
| B3 运行时可执行未审代码、Git rebase可能改变运行程序 | [Stage99 Git临时worktree上传与run()](../local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py) | 真正run和旧原始SHA retry均再次校验Claude审查＋单独用户授权记录；**先获取Binance原始数据**，再联系GitHub；上传时Git `fetch` → 在临时worktree基于远端最新HEAD只写一个原始证据文件 → 非强推push；远端更新有限重试，绝不对已审执行代码仓库rebase、reset、force-push；远端已有不同原始证据拒绝覆盖 |
| B4 underscore交割合约导致整个exchangeInfo失败 | [Stage91 freeze_universe()](../local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py) | 按`[A-Z0-9]+(_[A-Z0-9]+)*`允许合法delivery合约symbol，保留在完整人口，不把非PERPETUAL当扫描候选；缺`status`、`contractType`、`quoteAsset`、`baseAsset` fail-closed。回归合成`BTCUSDT_261225`记录人口而不计合格永续；并校验重复与字段缺失 |

## 高优先级其他问题

- N1 **安装全有或全无**：安装前一次性检查全部目标plist无冲突；其中一个bootstrap失败或Frank快照变化时，逆序仅卸载本轮已创建的目标plist并写`INSTALL_ROLLED_BACK_NO_SERVICE_ENABLED`，不卸载其他label。
- N2 **无需rebase**，解决冲突与残留rebase状态；临时Git worktree离线实测独立远端有新commit时，能成功保存当前证据且不覆盖远端内容，原执行目录分支HEAD不动；远端同名不同内容则拒绝。
- N3 **GitHub失败不能破坏采集机会**：源获取前运行时只读取本地仓库元信息，跳过`ls-remote`；捕获并保存原始bytes后再执行网络Git上传。Git失败保留本地sha和状态，过期后只能重新上传旧字节，绝不重新向Binance索取旧日期“快照”。
- N4 **提交作者不再冒用GitHub Actions bot**：本地采集仅使用显式`monster-local-capture`和非冒用邮箱。
- N5/N6：来源记录只是本机标准HTTPS TLS与官方时钟`/time`比对，非Binance独立签名；元数据缺字段fail-closed。
- N7：macOS`StartCalendarInterval`不支持年份，若整天关机可能在下一年同月日触发一次，然后因冻结UTC窗口过期拒绝、删除自己的plist；不能宣称已可靠回收一直睡眠的机器。
- N8：安装前后读取现有Frank launchd标签快照，若标签变化只回滚自己三个任务；Frank端口/进程从未被本代码主动访问或修改，但这不是在用户真实Mac上做过的资源隔离实测。
- N9：旧`monster_v4_stage99_external_ai_review.py`全部Claude CLI调用与可导入`review_then_install()`已替换为仅报告不可安装的tombstone，自始至终不要求用户安装Claude Code CLI。
- N10：此前过时的Stage99设计已修正为`Claude普通对话→真实BLOCK/APPROVE报告归档→用户对修复后版本**再次**授权→交互确认→本地安装`。
- N11：除Mock单元测试，还新增 [Stage103本地真实Git裸仓库集成用例](../local-agent/scripts/test_monster_v4_stage103_git_worktree.py)：Git真正clone/fetch/worktree/commit/push、远端新提交保留和证据同名冲突不覆盖，均无公网请求；macOS/Ubuntu两环境运行。**还没有真实用户Mac launchctl/Frank进程/真实未来Binance窗口实测**，不能把CI描述为这些真实部署证据。
- N12：任务仍在`finally`路径卸载自己对应label；若launchctl自身异常，需要在真实Mac批准后做额外只读检查，此前绝不擅自安装。

## 实际测试结果与不能提升的状态

- [Stage99/103跨平台专项CI #38372685819](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38372685819)：macOS-latest和ubuntu-latest **2/2 SUCCESS**，包含新装机失败逆序回滚、Frank标签变化拒绝、Stage91 underscore与完整字段、Claude聊天审查/独立用户授权门槛、真实本地Git worktree上传/远端新提交/不覆盖回归。
- 现有原Monster Research Baseline不改变Stage79生产模型/阈值；继续旧数据D1建模，不需要等新数据。**Monster本地来源快照任务不是D0/D1监控系统部署**。
- 未执行Mac启动/创建/修改任何launchd任务，没有创建ChatGPT automation，没有发交易/邮件。Stage97未来真实官方快照仍未获取。
- **当前正式结论**：`FIRST_CLAUDE_REVIEW=BLOCK_ARCHIVED`、`BLOCK_REMEDIATION_CODE=COMMITTED`、`STAGE103_CI=PASS_MAC_UBUNTU`、`SECOND_CLAUDE_CHAT_REVIEW=NOT_DONE`、`USER_SEPARATE_INSTALL_AUTHORIZATION=NOT_GIVEN`、`USER_MAC_TASK_INSTALLED=NO`、`FUTURE_REAL_SNAPSHOT=NOT_DONE`、`MONSTER_DEPLOYMENT=NO_GO`。

## 下一步唯一正确交付

生成修复后**新完整commit SHA**的独立Claude普通对话复审提示词（10+文件含Stage38/80和临时真实Git测试）；用户把Claude真实APPROVE/BLOCK全文发回，由研发负责人记录并修复，再经**用户另外明确同意安装**才交付可执行的一条Mac zsh安装命令。旧`BLOCK`仍保留原始证据，不可直接变成APPROVE。
