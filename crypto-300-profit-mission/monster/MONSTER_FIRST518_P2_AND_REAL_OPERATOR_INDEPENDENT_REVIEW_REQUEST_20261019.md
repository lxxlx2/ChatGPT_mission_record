# Monster First518 P2与真实机会查询器 — 独立其他AI审阅完整任务（2026-10-19）

请作为**真正独立**的Codex/Claude审阅者，复核Monster原PR #30 新修复与机会功能闭环，**不重审已批准的Publisher P2/Stage165/历史300U旧成果**。

仓库：https://github.com/lxxlx2/ChatGPT_mission_record
分支：`research/monster-v4-local-discovery-20261010`；**唯一完整审核固定SHA**：`eed4ea67e7868770367fbacffc1e9058ce59b635`；**比较基线**：`9fb392ad2ce07a4ee90680ad83214d25a50a74b0`。

真实源码和执行关联：输入代码/一次性Workflow触发SHA `07b82ff76c786c95706808aec1c9f6fdfea4129c` → [作者侧GitHub真实CI #39233361177](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39233361177) SUCCESS → 机器结果自归档commit `eed4ea67e7868770367fbacffc1e9058ce59b635`，原Artifact ID `12178242713`。修P2-1原预注册必须追到 `ea69b6a462b8d9f60f7120c1c1f6840972a0791b`，追加事后澄清不允许被误描述为事前改收益规则；旧代码独立报告审查SHA `03eaddcfb95d630e26b98c55796a9f835243387e` **仍BLOCKED**，旧经济结果实际产物提交为 `d673bd57e2ce9bf136da4de0c5b934be06337acf`。

新重点代码：
1. `crypto-300-profit-mission/local-agent/scripts/monster_v4_forward_spot511_first518_postsignal_economics.py`，三个固定True去掉，1533目录名完整性+8币24份Publisher原SHA复验、原CI1533全源证据出处单独分级。
2. `crypto-300-profit-mission/local-agent/scripts/monster_v4_forward_spot511_first518_fifo8_bridge.py`新增可选`--operator-view`，直接在原生产D0/D1研究SQLite中通过已有 `monster_v4_opportunity_snapshot.read_snapshot` 读取，不制造D2状态或用户可以买标签。
3. `crypto-300-profit-mission/monster/MONSTER_FORWARD_SPOT511_FIRST518_POST_SIGNAL_ECONOMICS_FROZEN_20261019.md`后加的P2-1说明，以及新增 `.github/workflows/monster-v4-first518-p2-operator-replay-once.yml`。
4. 真实归档 `crypto-300-profit-mission/monster/evidence/monster_first518_real_operator_d0_d1_d2_no_buy_research_p2_fixed_v1.json`，原CI log/Artifact和 `MONSTER_FIRST518_CODEX_BLOCKED_P2_FIXED_OPERATOR_REAL_CI_HANDOFF_20261019.md`。

请在独立detached checkout 锁住上述完整审核SHA，检查Git diff和原源码导入，分别运行相关两组单元测试、现有Operator read-only SQLite测试；必要时按原流程直接下载三批官方Binance Publisher原始ZIP/CHECKSUM Artifact（旧CI run `39212800265/39213387756/39214007356`，artifact ID `12167818438/12168243737/12168334522`），独立校验原511 T0每日1533对、微秒日1440根/校验和，独立518个3分钟原生产D0、研究V2 FIFO8 D1队列重放。若你的环境仍然无法取回原始bytes，**诚实标记该项BLOCKED，保留已有作者CI，仅凭Git收据、原CI PASS不可声称独立重算完成，也不要循环盲目重复数十次**。

功能方面须直接从临时真实SQLite运行read-only运营查询器，核对8 WATCH/8 SETUP，全部原event_id与旧结果相同；研究asof `2026-10-18T23:57Z`，8/8 `EXPIRED`（先排除过期），8/8 `d2_status=NOT_CAPTURED`，推荐`RESEARCH_REVIEW_ONLY_NO_BUY`。严格核对spot冻结511、原生产D0仅509有效/Unicode2不支持、来源健康`STALE_OR_DEGRADED`即便观察年龄0秒；不要通过静默缩小511人口或伪造当时L2/实盘ticker24把该缺口变成PASS。检查新经济结果15/60/360/1440与旧8+8逐条相等，24h均缺源应右删失，不许算0利润。原原始分析经济总体负，不得改变阈值去找正结果。

此外审查失败日志 [#39233103771](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39233103771) 是否仅测试错误假设SOURCE_STALE而实际EXPIRED；新作者CI #39233361177是否成功6+6+16=28项、原1533 bytes重核、518 SQLite、Git归档。新源码尚未获得独立批准，另需要商业真实D2档案、完整七日前瞻和G0/G1/G2/G4门槛，不得把本审核的源/研究功能范围扩大成盈利、实际买入、通知或Mac上线的批准。

请给出**APPROVE / REQUEST_CHANGES / BLOCKED**、审核者名称及精准底层模型版本（不可核验写 `UNVERIFIED`）、唯一固定SHA、独立运行命令与结果/出处、P0/P1/P2(有无阻断)及业务相关性，清楚说明是否重新获得了1533原ZIP的真实bytes。**审核完成只代表本固定研究代码，不批准实盘；`G0 PARTIAL / G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`均不变。**
