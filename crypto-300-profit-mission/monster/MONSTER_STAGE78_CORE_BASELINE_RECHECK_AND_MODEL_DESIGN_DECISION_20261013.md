# Monster Stage78：固定源自动复算及下一版核心模型设计决策

日期：2026-10-13（Asia/Bangkok），仅研究原 Monster PR #30。首先已提交 [Stage77验收和研发边界冻结](MONSTER_STAGE77_CORE_MODEL_ACCEPTANCE_AND_BOUNDARY_FREEZE_20261013.md)，再实施 [Stage78实际只读审计代码](../local-agent/scripts/monster_v4_stage78_core_baseline_audit.py)。**没有新策略调参、没有下载未来测试行情、没有修改旧冻结样本。**

## 1. 本轮真实执行与可复现来源

- 源代码用 Python 标准库验证 Git blob SHA（严格包含 `blob <bytes>\0` 头）及八份原机器JSON，检查跨文件分母、源删失、原D0发现、原P1容量命运、SQLite event journal、Spot缺失来源分类，任何来源字节变化或样本总数矛盾 fail-closed。
- [Stage78 GitHub CI #38298469005](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38298469005) **SUCCESS**：selftest+全部原始来源锁+统计复算通过；随后因区分首次和最近一条WATCH的命名修正，新版本 [CI #38298646920](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38298646920) **SUCCESS**，对应标准文档与程序修正后head `01932e93180fd60c2abe5bfc8fa564defa16c716`。CI核验的是仓库已有官方SHA机器证据，**本阶段没有重新下载八阶段的所有交易所ZIP**，不重复声称做了新的官方行情实测。
- 输入的8份Git blob按代码中 `PINNED` 固定：Stage34 `b7501f5ee504833b60efa4504183a4d233dd8bb8`，Stage35 `95d6d435be98cbe6bf7b694861fcc7bb7646b869`，Stage39 `d4dae1d2a2cd4e43bd8f1cb0fcb16b0724240080`，Stage52 `42d455a6cc9d0164a8dd94aa12a475bad5ed126e`，Stage66 `6c5cb45c23e57c3e4e1e844efe16b5af46cbd9b3`，Stage70 `79a10a59e36ebe0e8240c5deb2f21e182cef018f`，Stage74 `d7ab49a3bcb994129677e9c3b2e57df87cdc7e74`，Stage75 `13380febf0d03816bf9e7a1581055cfc05fcb595`。
- 复跑命令（只读，无网络）：`python crypto-300-profit-mission/local-agent/scripts/monster_v4_stage78_core_baseline_audit.py`。

## 2. 重新复核的主要事实，严格分开市场

| 已曝光历史窗口 | Spot原V4 Stage34 | USD-M原V4 Stage39 |
|---|---:|---:|
| 原币×日期尝试 | 13,644 | 5,400 |
| 双源可评分 | 7,776 | 3,283 |
| 缺源/冲突未评分 | 5,868 | 2,117 |
| 七日窗口起点OPEN→后续HIGH≥2× | 88 | 51 |
| 首次WATCH严格在首次2×HIGH分钟之前 | 84/88 = **95.4545%** | 48/51 = **94.1176%** |
| **最近一条**2×前WATCH至少提前5分钟 | 78/88 = **88.6364%** | 46/51 = **90.1961%** |
| WATCH币日期（去重） | 1,227 | 483 |
| 有WATCH但未达窗口起点2× | 1,141/1,227 = **92.9910%** | 433/483 = **89.6480%** |

**时钟校正**：Stage34/39给出的78和46是「首次2×之前最后一次提前WATCH至少早5分钟」的保守统计，Stage77的正式G1 **首次 WATCH ≥5分钟**在下一个新验证集必须单独输出；不要拿这个旧指标冒充首次或样本外G1通过。

这些非2×例是「未来固定起点未达到2×」的分类，不能被说成真实交易失败率或诈骗币。2025/2026背景暴露、上市/退市、非纯Crypto USD-M符号的完整人口仍有边界；更不能把Spot与期货两个表合起来算一个全市场召回率。

## 3. 当前真正卡住的环节：D1与可实现利润

| 旧失败对照（不同冻结日期，不允许合并分母） | 已核对事实 | 结论 |
|---|---|---|
| Stage52 P1 v0.3 | 原D0提前≥5min的28个2×里仅21获预算且P1也提前≥5min；21/28=**75%** | 冻结≥80%门槛失败 |
| Stage66/67 D0_FIRST5 | 新三日期只有5个源有效2×；原D0 5个均提前≥5min，但紧急队列仅2/5=**40%** | REJECTED且样本不足20 |
| Stage70只读SQLite | 715个首次D0 WATCH +222后续升级 =937 journal events；715 =493普通WATCH+161研究URGENT+61保留未放行升级 | **离线持久化结构通过**，不等于真通知 |
| Stage74/75 Spot场所 | 原196期货D0中101条同名Spot/USDT在前一分钟有成交证据；其余95查USDC/FDUSD/BTC/BNB没有新增t-1成交证据 | 剩余95交易资格/Alpha/DEX同刻可成交为UNKNOWN |

[Stage33原损益归因](MONSTER_STAGE33_ORIGINAL36_FUNDED_LOSS_ATTRIBUTION_20261012.md)锁定实验中，原3m策略300U资金账本净 **-166.727270U**，1m候选净 **-218.490855U**，使用历史固定每单30U、20bps/边滑点及24h退出和部分退出删失返本假设。**只是历史价格代理且旧金额不代表当前用户金额**，但足以拒绝「提高轮询频率=买入收益提高」的推断。

[Stage63全519首次D0的真实24h价格路径](MONSTER_STAGE63_FULL519_D0_NO_P1_SURVIVOR_BIAS_REAL_RESULTS_20261012.md)表面中位+2.56%，但六个日期有五个日期组内的中位数为负；主要正贡献集中2025-01-30，说明跨日期行情背景强烈影响总分。不能将这519看作独立同分布的盈利交易，也没有历史真实盘口支持净利润。

## 4. 新增的策略设计约束：独立的双入口，不能只等「第二次WATCH」

已曝光[Stage45原V4完整历史](MONSTER_STAGE45_46_SIX_DATE_P1V02_REJECTED_FULL_SHA_AND_MAJOR_5X_10X_POSTMORTEM_20261012.md)真实有41个2×，其中**40个**原D0提前至少5分钟。[Stage47重复WATCH审计](MONSTER_STAGE47_ALLMARKET_REPEAT_D0_SECOND_WATCH_CAUSAL_EVIDENCE_20261012.md)实际发现其中 **31/41** 在第一次2× HIGH之前出现第二次D0 WATCH。若一个D1方案**强制只有第二次D0 WATCH才能升级**，则即使所有31个重复事件全部被正确升级，其在本队列原40个可提前机会上的理论留存上限仅 **31/40=77.5%**，还未扣除其中太接近2×而早报不足5分钟者。因此在该历史对照上**任何「必须等第二次WATCH」方案先天无法满足80%留存门槛**。这个是事后历史数学上界，不能当未来预测胜率。

与此同时，[Stage42](MONSTER_STAGE42_FIRST483_FROZEN_P1_ACTUAL_SHA_FAILED_GATE_20261012.md)已证明「首次WATCH后接下来两次3m收盘不得低于首次价格」会严重漏报；[Stage55](MONSTER_STAGE55_ALL166_ASOF_CANDIDATES_MARKET_FEATURE_DIAGNOSTIC_20261012.md)166个P1候选中赢家与普通候选的60m动量中位几乎重叠；[Stage64b](MONSTER_STAGE64_ALL519_REAL_ASOF_TAKER_QUOTES_SAMEDATE_CONFOUNDING_20261012.md)同日期成对比较中60m涨幅排序只有0.543、15m主动买入占比只有0.512，不能把这些弱证据当强预测指标。

**因此确定的新策略设计边界**：

1. D0全部首次异常即时入持久 WATCH，不受后续筛选影响，也不等同于 BUY。
2. D1必须有**首次D0当场可资格化的直接入口**，同时允许**后续回撤后的再点火入口**；两者用同一个完整事件状态机、严格已闭合数据、仅一个有效升级去重。不能用「等待重复」排除第一波机会，也不能要求短线绝对无回撤。
3. 高优先级证据先评价**同日期/同市场阶段的真实成交额、笔数、可交易性与后续独立增强**，不能直接把单一60m涨幅、quote加速或taker占比设为经验证的赢家排序阈值。
4. 将24h内全市场共振/同分钟密集候选作为负担测试；用户可查看全部WATCH，有限紧急提醒只能依据当时可见的预注册准则排序，不能先来先占5条就永久丢重要候选。
5. 执行层必须从信号后的可买报价和真实可退出路径检验，期货2× HIGH只能评早报；没有历史bid/ask/深度以及用户订单金额，就保留 `EXECUTION_UNKNOWN`，不编造费后盈利。

这五条是**由真实已曝光失败推导的下一候选设计限制**，**还不是**已经通过独立验证的 D1 新模型或它的最终打分参数。

## 5. 下一项唯一主线和研发状态

按 Stage77：下一批首先写一套**双入口D1状态机的可证伪业务合同、技术输入字段、全市场拥挤与过期优先级规则**，明确具体可计算的数值参数及负例/弃用条件；同时冻结全部已曝光日期、数据可获得性与下一段真正未用验证日期/前向窗口。然后离线实现与原V4共享同一核心决策函数，回放完整源有效普通币，不单挑历史大涨币；得不到新的独立样本则承认 `NO_OOS`。未验证前不得进入用户Mac或真Gmail。禁止再开多交易场所考古新分支。

结论：`STAGE77_STANDARD=FROZEN`，`STAGE78_PINNED_SUMMARY_CI=PASS`，`D0_HISTORICAL_DISCOVERY=PROMISING`，`D1_PRIORITY=REJECTED_NEEDS_NEW_DUAL_ENTRY`，`EXECUTABLE_NET_PROFIT=UNKNOWN`，`INDEPENDENT_OOS=NOT_DONE`，`OTHER_AI_REVIEW_OF_NEW_STAGE=NOT_DONE`，`DEPLOYMENT=NO_GO`，`GMAIL=OFF`，`AUTOTRADE=NO_GO`，`FRANK=UNCHANGED`。
