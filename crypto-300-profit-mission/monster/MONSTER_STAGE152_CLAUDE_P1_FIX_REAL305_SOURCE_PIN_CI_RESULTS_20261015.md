# Monster Stage152：独立 Claude REQUEST_CHANGES P1 修复与真实原305历史模型再审报告

2026-10-15 Asia/Bangkok；唯一当前Monster [Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。**本轮状态=原用户独立Claude审查REQUEST_CHANGES后已完成P1工程修复+历史再复算，新增SHA尚需另一AI实审；经济模型仍不能上线**。

## 1. 审核基线、修改边界、不可回溯的外审

用户上传Claude（准确底层模型 `UNVERIFIED`）审核回复，固定旧代码SHA `b309bf75a46a48cde1aa6b14c17d3e6b7c1b53c2`，明确 **`REQUEST_CHANGES`**；P0=0、P1=3、其余P2；其审查环境只在Linux Python3.12.3执行本地11/11测试，原始publisher 305个历史事件无法在其环境独立访问数据源，因此其原始行情完整复算标 `UNVERIFIED`。外审评审者做了原Stage83/85/88保存证据与Stage151全305行交叉核对，这和真正读实时官方原日ZIP两个证据层级不能混淆。

**先冻结再修**：[Stage152一次性修复协议](MONSTER_STAGE152_FROZEN_STAGE151_CODEX_CLAUDE_P1_REMEDIATION_20261015.md) Git commit `58c5cd0a98869143d35ee8238a1c92f69d966e2c`。修复后的 **源+测试+workflow不可变代码审核/CI SHA=`f12d6635c6f8a5e2ba8fbb2feeca29688583245b`**；此后原分支CI仅新增Stage152的研究证据文件，未改变待审源码。Stage151原审核SHA上的REQUEST_CHANGES结论不能被覆盖改称旧版APPROVE。

代码变动恰好集中于现有 `monster_v4_stage151_post_d1_pullback_reclaim.py`、`monster_v4_stage151_aggregate_post_d1_research.py`、两份相应unittest和原Stage151 workflow，不改任何Stage38/80/85/88/90/101/110/118/120/127/132/137/138/150冻结研究模型及Frank。新模型核心`DROP=.97 / RECLAIM=1.01 / MAX_BARS=120 / HORIZONS=(360,1440)`没有调阈值。

## 2. 原始Source和成功CI

真正 GitHub Actions [Stage152 源绑定 #38731042245](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38731042245) status=`completed/success`、固定trigger SHA=`f12d663...`。GitHub job真实读取 **27/27 success**：

- Ubuntu **24.04** job `116408600379`：`Ran 18 tests`、`OK`；macOS job `116408599900`：`Ran 18 tests`、`OK`。
- 6个已曝光旧日期×4 shard=24个官方Binance历史1m publisher ZIP+CHECKSUM档案复验数据Job success，各shard绑定同一 `GITHUB_SHA` 和本轮核心源码SHA256，不得通过未来价格挑赢家。
- 聚合归档Job `116409060326` success，真实日志 `STAGE152_ACTUAL_GIT_EVIDENCE_PUSH_CONFIRMED`；reconcile按触发 `github.sha` checkout、对比每个shard的源SHA和trigger SHA、聚合报告再写自身源码hash、Git push前检查rebase未改变五个待审源码/测试/workflow对应git blob。代码push触发的**有限次数研究证据回写**不是scheduled后台采集，不改Mac和Frank。
- CI中间失败运行真实保留，例如 `#38730751356`、`#38730840181` 是单元测试对新统计schema字段层级和新错误标签断言沿旧方式使用所导致；之后纠正测试而非重调经济阈值。最终 #38731042245 重新成功并完整存档。

**独立机器输出，旧Stage151文件未覆盖**：
- [Stage152真实305完整收益/稳定性/敏感性摘要](evidence/monster_stage152_original305_integrity_and_economics_summary.json)，Git blob `f0dedc011d8518146f8c023ac61ebc5f7ff8b9a0`。
- [Stage152全305信号+全SHA+逐笔分钟成交活跃度/1m3m延迟模型真实行](evidence/monster_stage152_original305_integrity_and_economics_rows.jsonl)，提交后该文件必须保留原始逐币证据；该输出取自重新运行的24分片，而非旧305自述粘贴。
- 机器摘要中 `trigger_commit_sha=f12d663...`，`stage151_core_sha256=cf1624048af1349266ceeae0171536c7c9dabc24c8300092caeb4c4c6ac11c10`，`stage152_aggregator_sha256=80645d5b046393717e8017e91692ee9497bfc4cc2e199d28a71902c673cf0019`。这三个来源身份可独立核验。
- 本轮CI完整出版者日源回放是 **本模块自动测试**，并不代替新SHA的独立Claude/Codex从真日ZIP重复验证；自审不能声明第三方APPROVE。

## 3. P1-1：所有经济尾部分布和相同184件历史对照

| 真实原已曝光情形 | 样本 | 24h毛价格代理中位 | 均值 |
|---|---:|---:|---:|
| 原D1全部触发后直接入场 | 305 | **-2.799213%** | **+1.861635%** |
| 冻结新回撤恢复规则确认并有完整价路径 | 184 | **-2.446284%** | **+3.727669%** |
| *只限这184事件* 的原D1直接入场 | 184 | **-5.913492%** | **-0.601075%** |
| 逐对相同事件新策略减原D1，**不同退出时钟** | 184 | **+3.129194百分点** | **+4.328745百分点** |
| 113个被本规则跳过的无回撤事件，若原D1直入 | 113 | **+3.123373%** | **+6.724928%** |
| 回撤但无恢复8事件，原D1直入 | 8 | -10.004079% | -10.190059% |

**184确认中80件24h毛价正收益、25件≥+20%、3件≥+100%、12件≤−20%。** 最大5个赢家：MEMEFIUSDT +215.67%、MYXUSDT +170.56%、SYNUSDT +104.50%、BLESSUSDT +77.96%、AGLDUSDT +63.58%，合计贡献约632.27 个“百分比点总和”，占全部184条求和685.89的约 **92.18%**。剔除前5后179个事件毛价 **均值+0.29958%**、中位 **−2.69923%**；不能拿均值正值宣传稳健获利。这里的逐事件百分比之和不是持仓组合收益，未假设账户本金、复利或真实交易。

Stage151不改变原305历史G1/G2判定：原D1提前5m的2x历史评价标记 **27例**，其中确认184内16例，即16/27=59.26%仅为研究性筛选保留率，低于冻结G2 80%且非新真实OOS，**不允许把这个确认条件当成唯一D1高优先级正式过滤器**。原519 D0中的214个D0-only始终继续可检索WATCH。

六个已曝光日期的184确认样本24h毛价格中位依次 2025-01-30 +5.5400%、2025-06-02 −6.2125%、2025-08-01 −3.3204%、2025-10-02 0%、2026-06-21 −5.6990%、2026-07-28 −0.8857%，仍**只有1/6 日期中位为正**。

## 4. P1-2：预冻结交易活跃度和入场时延，不冒充盘口

新逐事件正式保存恢复信号bar `quote_volume/trade_count` 和假设入场、退出OPEN对应 **整分钟市场总 quote turnover USDT和trade count**，以及0/1/3分钟的入场时延敏感性；用户的研究notional依旧 `UNSPECIFIED`，这是市场换手金额，不能当盘口挂单深度或者本人的订单成交量。

| 184个确认的24h未成交价格代理研究分层 | 通过样本 | 毛收益中位 | 毛收益均值 |
|---|---:|---:|---:|
| 不额外设置整分钟成交额门槛 | 184 | −2.4463% | +3.7277% |
| 入场和退出各自1m全市场成交额均≥10,000 USDT | 124 | +1.8971% | +8.0198% |
| 入场和退出各自1m全市场成交额均≥100,000 USDT | 39 | +7.6684% | +19.0251% |

该+7.6684% **绝不代表实际可成交收益**，只是一组早已曝光的历史子集；筛选高成交额和少数正收益大赢家可能共同驱动其表现。实际买卖价差、盘口L2、潜在冲击、下单量和资金费率仍未知。不能据此偷偷把≥100k添加到原策略/初始WATCH上，必须经全市场独立OOS和G4才能评估真实交易。

同184个信号，零额外延迟原24h毛中位−2.4463%；再延迟1分钟（进场/退出时钟整体后移）历史毛中位**−1.8708%**；延迟3分钟毛中位**−2.0102%**。这是不同分钟OPEN到OPEN的毛价代理，**并非真实网络延迟、真实报价、可成交VWAP**；不能误断“多等一分钟更赚钱”。

其余完整状态：未产生研究入场121；已确认但因0成交额或0笔成交拒绝0；中间缺档/退出分钟缺失0，CI负向synthetic数据分别拒绝不完整、时间漂移和不可信收益。该0只是本305实际复盘样本的计数，不保证未来每段数据都完整。

## 5. P1-3、P2工程修复及仍未关闭的经济瓶颈

- 原workflow先每个24 shard源完整复算、再按 **trigger commit** checkout，而非漂移的branch head重算；每shard `GITHUB_SHA`与核心源码sha256必须相同；回写Git前比较分支代码Git blob与触发SHA，发现真正代码漂移就FAIL，不做静默源切换。
- `frozen_parameters`直接引用Stage151常量而不是重复硬编码字符串。
- 原退出丢失误报`SOURCE_RIGHT_CENSORED`、1439行误报SHA、恢复扫描缺少数据被H24漂移遮蔽的问题已更改为明确来源错误；决策逐根仅验证当时可见的分钟（确认后不回看未来坏bar）；确认为零交易时保存原因，不会假设真实成交。
- 新增7项外审核心回归，包含实际分钟表验错、源码/触发SHA错配、24 shard/305删损、亏损/大赢家均值与分层来源；与原11个回归总18个/OS。Ubuntu runner固定`ubuntu-24.04`，没有创建任何schedule。
- 旧Stage151统计仍然留在原路径，所有此次扩展统计只有新 `monster_stage152_` 证据文件；历史模型失败不能被新报告洗成APPROVE。

当前经济局限仍为：历史早报保留率不足、日期中位数不稳定、真实可成交成本/逐档L2不可验证，G0 PARTIAL / G1 NOT_SCORABLE / G2_G3 NOT_PASSED / G4 UNKNOWN / G5_FULL_RELEASE NOT_PASSED / G6 NO_GO。NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE，Frank不变，Stage99已停、不会恢复。

**新代码独立其他AI审核结论=待提交独立复审**。不能因为本次自己修复了P1就先填APPROVE。见同PR固定SHA独立复审提示词。
