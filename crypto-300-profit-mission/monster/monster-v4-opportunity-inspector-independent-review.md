# Monster V4 只读机会查询器独立代码与业务安全审核包

更新：2026-10-18。仅用于现有PR #30的研究代码审核；用户Mac、Frank、Gmail、交易均未变更。

## 精确审核对象

- 仓库：https://github.com/lxxlx2/ChatGPT_mission_record
- Draft PR：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
- 分支：`research/monster-v4-local-discovery-20261010`
- **唯一审核固定SHA**：`5a54ef90823c4e8f51b8fed557de4fbd6c44a1b1`
- **唯一比较基线**：`51fcf066ef144d1526146a952e6b190961092a3a`
- 已复核Git compare：ahead 3、behind 0、仅3文件差异：新增`crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py`、新增`crypto-300-profit-mission/local-agent/tests/test_monster_v4_opportunity_snapshot.py`、在`.github/workflows/monster-v4-research-baseline.yml`添加触发路径和测试步骤（7行新增，无删除）。
- 实际CI：https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39075413068 ， `historical-baseline` job success，全部22/22步骤完成；新增8/8 unittest PASS（log原始`Ran 8 tests in 0.095s / OK`）；旧Shadow/D2回归也pass。
- Stage162已由Codex独立APPROVE的固定SHA `b85dee96ec6f567e1f0b90f0d50cc5b19c79018b` 不属本轮修改，不必重复同代码审核。本轮新增功能未经其他AI Review，状态 `NOT_DONE`。

## 研究问题与不许升级状态

此前D0/D1/D2事件入SQLite，但`monster_v4_shadow.py status`仅输出健康计数。操作人员看不到明确的币、首次WATCH时间、是否过期、SETUP强度及对应D2检查状态。新工具只读已存在的Monster研究SQLite，输出带时间戳的机会清单；正确处理不同queue episode、场所、15m deadline、过期、无源或degraded、D2的用户未知真实费率，不产生BUY/交易/通知。没有部署Mac。

真实市场业务负证据：旧Stage30六日期已曝光样本430笔可评价WATCH后24h价代理133赢297亏，单交易无上限独立PnL+17.575264U但用户资金约束300U十槽乐观未知退出仍-79.489406U；它是历史代理非实际订单。Stage162已曝光同一445源Fair8新增有效首评27、净新增SETUP=0；来源不能冒充真PIT与新盈利验证。Stage163 2026-10-17T22:04:40.094Z Binance Spot官方原HTTP T0 已有511活跃USDT对，但未来7日（10月18~25日曼谷）未完成，没有动态真实入出场L2。G4 `UNKNOWN`、G6 `NO_GO`、`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`保持不变。

## 发给独立Claude/Codex的完整审核提示词

你是独立代码与业务安全审核者，请**实际获取GitHub固定提交的源码和逐文件Diff**，不要仅评论PR文字。

目标GitHub仓库：https://github.com/lxxlx2/ChatGPT_mission_record 。审核Draft PR #30，research分支 `research/monster-v4-local-discovery-20261010`；审核固定SHA `5a54ef90823c4e8f51b8fed557de4fbd6c44a1b1`，唯一比较基线 `51fcf066ef144d1526146a952e6b190961092a3a`。仅本diff三文件为本轮审核对象：
1. `crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py`
2. `crypto-300-profit-mission/local-agent/tests/test_monster_v4_opportunity_snapshot.py`
3. `.github/workflows/monster-v4-research-baseline.yml`

业务目标：把既有Monster Shadow研究SQLite中持久化D0 WATCH、D1 SETUP、D2盘口审查输出为**真正只读、不含BUY误导**的机会摘要，正确显示首次观察时间、source可用性、15分钟窗口/过期、futures-only、不同queue episode、独立D2源与费用假设。严禁更改已冻结D0/D1/Fair8、历史回测、Frank生产、Gmail、launchd、GitHub schedule、ChatGPT Automation、真实交易。不得把历史代理收益、旧30U D2场景或当前HTTP报价冒充真实可成交交易/净收益。

独立验证原始提交Diff及目标代码完整性；复现新增8项SQLite单测，并自行构造至少这些真正会影响用户的反例：
- 一个币旧SETUP已过期、新WATCH刚产生，能否避免用旧SETUP或旧D2标记新回合；
- `d2_reviews=CHECKED`但盘口/费率来自旧固定金额或有缺口，是否会错误宣称BUY/真实可成交；
- source缺失/DEGRADED、最新poll没有所有官方eligible交易对、时间戳倒流/过期，是否错误显示为可跟进；
- SETUP在期内或多次重复WATCH时，event_key与queue_id是否精确映射；SPOT与USD-M是否隔离；
- sqlite`mode=ro/query_only`是否确实不变更原库、丢文件时是否禁止创建假库，是否有意外联网、定时启动、发邮件、交易代码；
- `--asof-ms`仅为已保存现态评价钟，是否仍可能被误认为历史PIT回放；测试与CLI说明是否充分。
着重指出真正影响完整功能性和可用性的P0/P1/P2，避免仅审美或极端低价值边界建议。检查原`monster_v4_shadow.py`事件ID与D2字段契约，不能只根据新增测试假定一致。核查实际GitHub Actions #39075413068的触发HEAD/原始日志，不只看报告摘要。

请按固定结构返回：`APPROVE | REQUEST_CHANGES | BLOCKED`；准确审核SHA及比较基线；每个P0/P1/P2的代码行号、实际复现步骤、结果、修复方向；检查是否会改变WATCH、D2/BUY解释、Frank隔离或G0–G6放行；明确剩余真实源/样本外/手续费与可成交缺口以及`NO_MERGE / NO_DEPLOY`是否仍生效。不能访问固定源码或运行测试请标`UNVERIFIED/BLOCKED`，禁止凭文字自称完成独立审核。

## 当前状态

`CODE_TEST_CI=PASS`；`EXTERNAL_INDEPENDENT_REVIEW=NOT_DONE`；`LOCAL_MAC_ACCEPTANCE=NOT_DONE`；`ACTUAL_PROFIT_G4=UNKNOWN`；`G6=NO_GO`。仅研究代码与CI完成，禁止合并/部署/通知/交易。
