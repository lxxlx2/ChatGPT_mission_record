# Stage103 仅供 Claude **普通对话** 的完整独立复审提示词

目标固定Git commit：`27c2c839d83dac11d1664d0fb6c9691844d0ca9a`（不因为后续新增审查材料文档而改变代码），原Draft [PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，仓库 `lxxlx2/ChatGPT_mission_record`；**不授权部署、安装、设置任何定时任务**。首份Claude Haiku 5.5 独立审查结果是`BLOCK`，[原审查文字归档](evidence/monster_stage103_external_claude_haiku55_stage99_review_BLOCK_20261013.md)；这次是另一次针对**修复后代码**的审核，不能沿用旧批准。

## 请复制以下正文到Claude聊天

你是另一个独立AI代码审查者。请锁定`lxxlx2/ChatGPT_mission_record` Git commit `27c2c839d83dac11d1664d0fb6c9691844d0ca9a`，完成Monster **Mac本地研究原始市场名单采集器**修复后独立Review（不是交易策略或Frank生产部署）。先阅读此前Claude Haiku 5.5给出的[BLOCK原报告](https://github.com/lxxlx2/ChatGPT_mission_record/blob/27c2c839d83dac11d1664d0fb6c9691844d0ca9a/crypto-300-profit-mission/monster/evidence/monster_stage103_external_claude_haiku55_stage99_review_BLOCK_20261013.md)和[Stage103逐项整改及CI证据](https://github.com/lxxlx2/ChatGPT_mission_record/blob/27c2c839d83dac11d1664d0fb6c9691844d0ca9a/crypto-300-profit-mission/monster/MONSTER_STAGE103_CLAUDE_BLOCK_REMEDIATION_REAL_CI_AND_REVIEW_GATE_20261013.md)。

**必须完整独立阅读**以下源码及规范：
1. `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage38_usdm_original_v4_1m_pilot.py`
2. `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage80_dual_entry_core.py`
3. `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage91_forward_oos_replay_gate.py`
4. `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage97_one_shot_usdm_capture.py`
5. `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_mac_launchd_one_shot.py`
6. `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage102_claude_chat_review_gate.py`
7. `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage99_mac_one_shot.py`
8. `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage103_git_worktree.py`
9. `.github/workflows/monster-stage99-mac-one-shot-capture-safety.yml`
10. `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage99_external_ai_review.py`（核对已不含可运行Claude CLI审查/安装功能）
11. `crypto-300-profit-mission/monster/MONSTER_STAGE99_MAC_ONE_SHOT_GIT_CAPTURE_DESIGN_20261013.md`
12. `crypto-300-profit-mission/monster/MONSTER_STAGE102_LOCAL_COLLECTION_CHAT_REVIEW_AND_PARALLEL_MODEL_BOUNDARY_20261013.md`
13. `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`

GitHub完整地址规则：`https://github.com/lxxlx2/ChatGPT_mission_record/blob/27c2c839d83dac11d1664d0fb6c9691844d0ca9a/<上述相对文件路径>`。如果不能读取任何关键文件，请列出受限范围并给`BLOCK/UNVERIFIABLE`，**不得装作已审查或猜测源码**。

特别逐条复核旧审查B1–B4、N1–N12：
- B1：Claude聊天审查结果与用户单独安装授权必须完全分离；无人授权、没有独立Git授权记录、无手工TTY短语、审查结果BLOCK、不属于用户明示范围或代码已变更时，任何Mac`launchctl bootstrap`必须绝对不会被调用。判断自证回执+终端提示是否存在实际绕过路径，承认SHA/TTY不能密码学识别人。
- B2：审查范围包括Stage38/80/91/97/99/102及测试/CI全部核心blobs，锁定`reviewed_commit`祖先关系；Stage91任意`WINDOWS`变化必须使旧回执失效；CI真实修改这些文件会触发。
- B3：在运行时再次校验已审执行文件；Git上传使用临时worktree，任何冲突或远端改动不得rebase/reset/checkout已审核代码；已经采集的SHA不能丢，Git上传失败后只能重传原始字节不能事后再抓。
- B4：Binance USD-M交割合约`BTCUSDT_261225`等下划线符号被保存在完整人口但不计入永续候选；缺`status/contractType/quoteAsset/baseAsset`报错；注意脱敏合成样本不等于当日实盘Binance成功。
- N1/N2/N3/N4/N8/N9/N10：单次安装全部预检查及逆序回滚、Frank只读label快照无副作用、币安快照时点在联系Git前、没有伪装bot身份、已彻底关闭错误Claude CLI入口且规范同步。
- 查验真实Mac/Ubuntu CI及测试用例：原[CI #38372685819](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38372685819)、Stage103后续增加真实**本地Git裸仓库**冲突/远端提交保存及安装回滚案例。CI不是实时Binance采集/Frank共存真实性证明。
- 另外查查：独立review后才创建的授权manifest究竟能否被不当代拟？`input()`是否真实TTY并带审核指纹？在Git远端并发修改时上传的源记录有无覆盖/错报？`launchctl`的月日调度（无年份）是否会产生不可接受的残留？进口Stage38/80副作用是什么？`bootout`超时能否覆盖执行退出状态？

**输出格式必须完整**：`APPROVE`或`BLOCK`；你当前实际Claude模型（不知道填UNKNOWN）；受审确切40位commit；逐文件真实读取列表及未读取列表；对B1/B2/B3/B4各自PASS/FAIL与证据；新发现的每个阻塞问题含函数/具体触发条件和修改建议；非阻塞项含优先级；对测试/虚拟数据与真实Mac状态的区分；最终只给“是否足以**等待用户随后单独明确批准研究快照采集任务安装**”的结论，**不代表用户已经批准安装**。如果确有任何阻塞问题必须写`BLOCK`，别用“CI绿灯所以通过”推断。

不要创建任务、不要修改Git、不要索取API Key、不要要求本地Claude CLI。你仅在Claude对话中独立审查真实 Git 源码；审查完成把**完整原始回复**交回用户，由研发负责人另行归档。未经用户明确授权绝不安装。

## 当前状态

`FIRST_REVIEW=BLOCK_ARCHIVED`、`STAGE103_FIXES=COMMITTED`、`CI_MAC_AND_UBUNTU=SUCCESS`、`SECOND_REAL_CLAUDE_REVIEW=NOT_DONE`、`USER_INSTALL_AUTHORIZATION=NOT_GIVEN`、`MAC_INSTALL=NOT_DONE`、`BINANCE_FUTURE_CAPTURE=NOT_DONE`、`MONSTER_DEPLOY=NO_GO`。
