# Monster Stage163 — V3 后置盘口时钟误差与异常尺寸处理，Claude 第二次 REQUEST_CHANGES 修复（2026-10-18）

## 一、批准范围和实际版本（不能把作者修复当独立APPROVE）

**作者代码修复/源码再生/测试/证据治理：DONE；新固定 SHA 独立其他AI实际复审：NOT_DONE。** 用户转交 Claude 聊天窗口，准确模型 UNVERIFIED，针对之前固定 `4c6bff916bb432ba778c59e6283c5a75e2902293` 给 `REQUEST_CHANGES`：原始时间前视和511人口等**原缺陷确认已修复**，另指出P1-E历史V1证据废止与V2入树版本差异、P2-A跨客户端与交易所的时钟差未输出量化置信范围、P2-B薄/锁定盘口单行导致全批中止。这个审核针对历史固定树，不能否定该固定树**之后**发生的Git证据写入。旧版 REQUEST_CHANGES 记录不能反溯更改。

- **唯一供这次定向复审的证据完整固定 SHA：`15edf022d8b99071701357dfd51d7534f3470409`**，精确比较基线是上轮被拒绝代码`4c6bff916bb432ba778c59e6283c5a75e2902293`。新可执行代码与CI触发 SHA为`59c546af14cc42ab2be6e8e2af9a5c1d7d55f7be`；此后到`15edf022...`只有归档JSON、V1/V2旧文档状态标注、新版本继承登记，没有进一步修改可执行脚本/测试/Workflow。应**审核证据完整SHA**，并分别验证CI的准确原代码SHA；不要在旧代码SHA树中寻找后续Git生成的证据。
- 已验证真实 [GHA #39084681931](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39084681931) 的触发头是`59c546af...`、job `SUCCESS`，完整日志 `Ran 12 tests ... OK`，新V3原ZIP读取和511行实际计算通过，artifact及成功Git push记录。旧审查方未核实的CI日志在本轮由GitHub连接器真实独立读回，但**这不等于新的其它AI已复核**。
- 原始官方Binance Spot原HTTP ZIP SHA256 `b47e206345c0a04b16b37c38795d726553ef83ca679f443f9fba89805483216b` 不变；V3输出永久 [511原始行研究JSON](evidence/monster_stage163_spot_post_t0_original511_quote_friction_v3_clock_actual.json)，Git Blob`f87ea5342642055af4e8ea8f15dd4efa76e1eb7d`，`schema=MONSTER_STAGE163_SPOT_POST_T0_CLOCK_BRIDGED_511_FRICTION_NO_TRADES_V3`。
- 版本证据继承锁定在[不可覆盖的 supersession JSON](evidence/monster_stage163_spot_quote_friction_evidence_supersession_register_20261018.json)，Git Blob`23912f5cac28ea1b051baa00ba30508a318c0eb4`。旧V1 `d2df270708b48d1b374aa314b25e848ae12cbd75` 保留**但T0当刻盘口标签和全Spot含义已废止**，旧V2 `0f6e63829c39ff28ce41b02e5ae08ed536414f2c` 实际存在于本次审核固定树，受V3替代（V2已存在于Git SHA`0d2a4c45147e23b04bfee9c60df93826c848db4c`；V3实际落树SHA`e26fee10d3b8864f8689c364e5656818fb09cd34`）。旧报告顶部加废止提示，**绝不改写历史原机读JSON**。原Git只有V1时的固定`4c6bff9...`并不构成当下V2不存在。

## 二、P2-A：真实双 clock 探针和跨时钟误差，非伪精确市场时间

已有源两次官方无密钥 `/api/v3/time` 返回Binance `serverTime`，并有每次的client请求开始、接收结束UTC。新工具把 `serverTime - client_request_window_midpoint` 称作**服务器与客户端时钟差估计**；请求窗口半长为保守不确定项，分别推导上下界。此模型假定单个HTTP往返中的实际serverTime事件处于请求和收包之间，**没有证明上下行对称，更未校准两次探针之间时钟漂移**，故不能冒充真实行情逐币时间戳。

| 冻结原始时间证据 | clock_before | clock_after |
| --- | ---: | ---: |
| server−client中点估计(ms) | +337.799 | +227.823 |
| client请求RTT半窗(ms) | ±418.004 | ±306.728 |
| 保守单探针server−client区间(ms) | [-80.204,+755.802] | [-78.905,+534.551] |

两次探针的联合包络：`[-80.204,+755.802]ms`。把原**未校准的**bookTicker相对T0客户端请求偏移`[+2561.682,+4349.393]ms`加上上列时钟差条件包络，得到 `[+2481.478,+5105.196]ms`；对ticker24原`[+4349.727,+6835.464]ms`得到 `[+4269.523,+7591.266]ms`（原报告机器值请以JSON逐字段为准；本表中的小数末位保留量化误差）。这两个区间**只表示收包窗口相对于T0的条件性界限**，与每个价格实际上最近何时改变没有直接对应，尤其 `clock_drift_between_samples=UNVERIFIED` 和 `conditional_interval_not_certified_exchange_event_timestamp=true`。错误或倒序client回执、跨端点顺序错乱、下界不能确定在T0之后则拒绝`post-T0`时间资格；不会据此升级G0/G4。

## 三、P2-B：逐币薄盘口留痕，来源基础错误才整批拒绝

新的`quote_status`明确三类：`DISPLAYED_TWO_SIDED` / `LOCKED_QUOTE` / `ZERO_DISPLAYED_SIZE`。真实本批511个币各有双向正显示和正价差，当前数据三类数分别`511/0/0`；对合成样本分别给出锁定与零档时，也保存原511行、不悄然缩小分母。卖一/买一`displayed_depth`分位统计只对`DISPLAYED_TWO_SIDED`做分母`displayed_depth_distribution_evaluable_count`，excluded行仍在输出且计数；`both_sides_show_positive_size`不再恒真。可选用户明确研究金额只计真实双边可展示，不能把锁定/无货币的买卖近似成交。真正交叉 ask<bid、非正价格、负数量、NaN、来源缺行或重复符号依然fail-closed；不是“为了留住所有数据”就把损坏源当作合法。

单点价差总体p10/median/p90仍`2.060793 / 11.217050 / 28.971511 bps`（本批无异常盘口）；首次“价差”是独立的上行成本描述，非现实双向fill/net盈利验证。没有真实未来退出价、交易费用tier与账户资金；全部 `G4 UNKNOWN/G6 NO_GO`。

## 四、完整可复制的独立其他AI修复审核任务（尚未完成）

请将以下任务发给Claude聊天窗口或另一独立审核AI，**审核固定证据完整SHA**，不要再次仅在旧已过时代码SHA的固定树里找后来的Git证据：

> 请定向复审Mission Monster PR #30，仓库`https://github.com/lxxlx2/ChatGPT_mission_record`，分支`research/monster-v4-local-discovery-20261010`，**唯一证据完整审核SHA `15edf022d8b99071701357dfd51d7534f3470409`**，比较上轮REQUEST_CHANGES `4c6bff916bb432ba778c59e6283c5a75e2902293`。新研究脚本/测试/CI触发SHA `59c546af14cc42ab2be6e8e2af9a5c1d7d55f7be`；该SHA之后只有机器证据与文档写入，审核时不得将两个SHA混淆。上一轮指出的T0盘口前视、全Spot人口误称、跨端点3币问题已获Claude确认关闭；本次只审其新P1-E/P2-A/P2-B及直接回归，不对旧已独立重算的511币价差反复重做无关模型。逐字节核对3个不同版本历史机器文件：V1`d2df270708b48d1b374aa314b25e848ae12cbd75`已失效T0和完整Spot标签；V2`0f6e63829c39ff28ce41b02e5ae08ed536414f2c`已落Git但被V3替代；V3`f87ea5342642055af4e8ea8f15dd4efa76e1eb7d`是当前511行真实研究，及独立supersession登记Git Blob`23912f5cac28ea1b051baa00ba30508a318c0eb4`；确认原旧V1/V2字节未被覆盖，旧结果文档顶端已更新废止提示。审核`crypto-300-profit-mission/local-agent/scripts/monster_v4_stage163_spot_t0_quote_friction.py`、对应`local-agent/tests/test_monster_v4_stage163_spot_t0_quote_friction.py`、`.github/workflows/monster-v4-stage163-offline-spot-t0-511-friction.yml`，实际从6份SHA吻合的官方原ZIP重算`clock_before/after`的`serverTime - client_mid`两值`337.799/227.823ms`及RTT半窗`418.004/306.728ms`，包络[-80.204,+755.802]ms。确认这仅是条件性回执时间界限，绝不认证逐币行情可T0使用或精确未来报价；真实时钟漂移UNKNOWN。构造clock probe/收包时序反例、locked ask=bid、bidQty或askQty零值单币样本，预期整批仍保留511行但0/locked分类保留且深度分母剔除；对真正交叉和NaN应失败。实际运行`python3 -B -m unittest discover -v -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_stage163_spot_t0_quote_friction.py`及`python3 -B crypto-300-profit-mission/local-agent/scripts/monster_v4_stage163_spot_t0_quote_friction.py`；校验 [CI #39084681931](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39084681931) 触发真实SHA、12/12测试PASS与实际GHA push V3成功。审核独立表头时也注意本次代码**不属于**实盘D0/D1/D2、Frank、Mac、邮箱/交易/任何定时监控；不等于真实市场净盈。给`APPROVE / REQUEST_CHANGES / BLOCKED`、P0/P1/P2、准确冻结审核SHA/路径行号、独立复现结论和无法验证标`UNVERIFIED`。保持`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE / G4 UNKNOWN / G6 NO_GO`。

当前研究源与CI`DONE`，其他AI对**新定向完整SHA**的最终复审仍`NOT_DONE`。新代码不放行策略；新完整7日Spot真正前瞻验证窗口[2026-10-17T22:06Z,2026-10-24T22:06Z)尚未成熟；有无真实成交与可盈利仍UNKNOWN。
