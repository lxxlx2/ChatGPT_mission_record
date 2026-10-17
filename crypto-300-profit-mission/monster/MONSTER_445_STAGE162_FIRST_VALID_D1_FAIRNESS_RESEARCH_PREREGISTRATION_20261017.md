# Monster Stage162：同8槽下首次有效D1评价公平性研究 — 预注册（NOT_STARTED）

**缘由，严格引用Stage161真实证据**：GHA #39012150858，源445/28/18来源、3360同库poll、753次D1选中（首次269、重复484），原269个WATCH中93个LATE全部在15分钟deadline之后才第一次选中；单次98币高峰在+0m只有7个首次selected，+3m至+15m连续40个槽被同一老8个重复selected，+18m起剩余91峰值币首次selected但直接LATE，附近2个其他币也在+48m首次selected后LATE。原 `attempts=0`不是首次服务证据，原SHA / Git摘要 / 完整报告均在 `MONSTER_445_STAGE161_REAL_FIRST_SERVICE_CAUSAL_FINDINGS_20261017.md`。仅此已看过的Feb445不能做独立OOS，也不允许宣称91个潜在盈利交易。

## 研究目标（从业务效果而非减少测试出发）

在**相同445真实原分钟源/28片、同一D0 WATCH、原生产8槽/3m、每候选15m有效期、冻结原D1六根闭合K线特征与历史零quote语义**下，比较候选在有资格得到WATCH后首根闭合5m时，是否可以保证首次有效D1评价，而非前7个老候选在+0/+3/+6/+9/+12/+15轮重复占满8槽。

**严格冻结三个对照**（不能看未来SETUP/PnL再调）：

A. `BASELINE_FIFO8_REAL_V2`：真实原研究零quote V2同库结果，所有真实事件和队列必须与source SHA`370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`、新Stage161 trace逐字段一致；不重标为原生产成功。

B. `FIRST_VALID_5M_ONCE_PRIORITY_8`：每轮候选进入当前时点可见队列，只在 **已经有WATCH后真正闭合并可读的5m K线** 时，优先选择尚未完成首次有效D1评价的候选（仍处于15m期限且通过正常retry_after gate），剩余槽由旧FIFO正常复查；每轮绝不超过8，不插队至尚未形成后验闭合K线的信号，不能看任何候选后来的终态、赢家名单、回测收益或未来tick。对市场合法0成交额不补成正，也不得把不可评估源强行记成功；保留原始冻结研究V2意义并显式写明模型研究分支不同，不能直接取代生产源码。

C. `BASELINE_FIFO8_WITH_FIRST_SERVICE_METRICS_ONLY`：影子容量诊断，只重现真实观测数据，不改变选中顺序，用于检查B方案的修正是否会改变正常171币原有D1重服务和120个SETUP。

## 评估指标与拒绝自动升级条件

每个run必须输出全部269 WATCH的同ID来源关联、各tick8槽选择、候选首次selected和首次**有效D1评价**时间、LATE是否在deadline之前实际获得过有效评价、D1闭合K线重试次数、重新触发WATCH、合法零quote下的PENDING/WAIT/terminal、每轮需要但缺源的正负情形。分 **PEAK_98** 与 **OTHER_171** 对比：有效首评覆盖/延迟p50,p90,p99，首次服务成功/错过，峰值与非峰值SETUP实际召回变化（不能只看总120），生产D1既有SETUP损失的反例，重复slot减少是否伴随真正SETUP减少；不能把首次被点名直接定义为有效D1评价。

经济可执行性：原source仅历史OHLCV，缺当时PIT listing、盘口bid/ask、深度、手续费、滑点、实时广播送达及可卖出流动性；无论B上多少SETUP均 `PROFIT_UNVERIFIED/G4_UNKNOWN/G6_NO_GO`，禁止为“盈利最高的98币”调参。只要B对其它171普通币产生任一SETUP下降或D1兼容性误差，要在报告展示并解释，不得删除指标来宣称赢；不能有真实交易、推送或生产开关。后续必须新增**独立未来市场样本**才能作为盈利有效性证据，已看过的Feb445最多做机制可行性回归。

## 实现顺序与状态

1. **已完成**：真实原source、Stage161同库行为等价插桩与公平性缺口归因。
2. **预注册完成**：本文件中的B方案和统一指标/否决标准。
3. **待做**：研究者在独立分支研究实现B；不得更改原 `monster_v4_shadow.py`、`monster_v4_shared_spot_d0_d1_original_core.py`、历史V2或替换已有269条事件。
4. **待做**：隔离全445真实source回放A/B对照、其他AI独立review、回归与前瞻OOS验证。直到证明不会恶化整体有效SETUP/时效和具备交易成本实测之前，不进入Mac。
5. **禁止**：GitHub schedule、launchd/cron、ChatGPT Automation、新邮件任务、Frank资源侵占、PR merge、deploy、Gmail、trade。PR #30保持 Draft。

**当前Stage162 = DESIGN_FROZEN；CODE/RESULT/INDEPENDENT_OTHER_AI_REVIEW = NOT_DONE。**
