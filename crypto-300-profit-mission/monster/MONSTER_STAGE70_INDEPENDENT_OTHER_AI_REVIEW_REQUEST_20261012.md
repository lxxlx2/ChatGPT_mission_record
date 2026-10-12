# Monster Stage70：供另一 AI 独立Review的正式资料包（不是Review结果）

快照基线：Monster PR #30 分支 research/monster-v4-local-discovery-20261010，review target commit 4cd8c55a8596ee06fd031e24f368ef01cd6b8f60。该快照已包含Stage70代码/测试/证据；Review请求文件后提交不会修改待review代码。**这不是通过Review的声明。**

## 审查任务

请作为与原实现独立的代码审查者，读取本仓库真实代码、原始source-locked证据与开发规则，不要只看结论，也不要把研究CI通过视为代码安全的全部证据。就技术设计、数据来源、已实现范围和业务缺口给出阻断项、建议修复、复现步骤与明确的验收状态：

1. 审查 crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md、crypto-300-profit-mission/monster/MONSTER_STAGE70_WATCH_NEVER_DROPPED_SQLITE_PROJECTION_TECH_DESIGN_20261012.md。
2. 重点源码 crypto-300-profit-mission/local-agent/scripts/monster_v4_stage70_historical_watch_projection_sqlite.py。它仅是Monster独立、离线、需要显式数据库路径的历史资料投影，不是实时生产，也没有通知/自动交易权限。检查ACID事务、来源Git blob校验、timestamp排序、同分并发WATCH在P1之前、唯一ID幂等、来源变更、冲突时ROLLBACK、恢复后无记录丢失、去重与错误异常、数据标签误导及是否有无意触及其他模块。
3. 阅读 crypto-300-profit-mission/monster/evidence/monster_stage68_original2700_all252_D0_P1_watch_and_research_urgency_states.jsonl 和 crypto-300-profit-mission/monster/evidence/monster_stage69_older6_all685_WATCH_P1_replayed_budget_events.jsonl；各自原Git blob分别 8e5d3247aaf04ffd00e44d1ef214e4939d75fa6b、d34ff59b559023af0b0db67c818fb9b2649c0363。确认没有遗漏或虚构事件，不能把Stage70 WATCH状态错说成真实现货可买或实时新信号。
4. 重新执行源码 --selftest，并在完全隔离的临时目录创建SQLite运行 --db 与 --out；独立验证预期937原事件、715唯一WATCH、222个P1升级，其中493仍WATCH、161研究URGENT、61超配额仍保留，完全再导入=新增0，重新打开数据库状态不变。主动构造坏事件触发异常，判断原子回滚是否足够。不要触碰Mac已有Frank的任何进程/SQLite，不能擅自改生产配置。
5. 审查上游Stage68 P2状态机和Stage69真正时间定义的一致性，特别是原Stage52的22个D0早发现获预算和21个P1仍及时获预算的差别，确保没有混淆。Stage69已证明P2漏掉历史5× AIA，策略 REJECTED；Stage70不能因为read-model通过而改称策略通过。完整一览见crypto-300-profit-mission/monster/MONSTER_STAGE68_69_P2_HALF_DAY_PACING_FAILS_OLD6_AIA_GT5X_REAL_RESULTS_20261012.md。
6. 报告真正范围缺口：本轮仅第一次D0+第一次P1，原重复WATCH仍在更早原始数据；没有实时消息接入、API端点、Mac部署、链上CA或真实Spot/Alpha/DEX执行、手续费/用户金额与净回报。不能把未完成写为通过。

## 请提交可复现的Review结果

输出 Reviewer 实际使用的模型名称/版本及Review时间，目标commit SHA，独立运行的命令和完整实测输出/摘要；对于每项问题列文件+函数/行号、等级（P0/P1/P2）、为什么错误、最小复现输入、建议修改和会影响哪一项产品主线，最后给 BLOCKED/CONDITIONAL/REVIEW_PASS 的审查判定。只有实际收到的另一AI Review意见才能记为完成；本资料包、助手自查和CI本身不能代替Review。

此阶段只做只读研究功能。请不要部署、开启Gmail、下单、重命名任务/对话或修改Frank。本轮用户没有指定单笔交易金额。
