# Monster Stage165 — 原445源、实际27次Fair8首次D1评价：为什么一个新SETUP都没有（2026-10-18）

## 一、答案先行

**这是原生产D1逻辑与原历史minute SHA锁定来源下的指标级证据，不再是基于最终queue错误字符串的猜测。** 在Stage162完整445历史来源、实际269个WATCH和Fair8真实选中的27次新增有效5m首次评价中，全部27个未满足原生产D1的`recent_vs_earlier_15m_quote_ratio >= 1.5`。这条成交额确认门槛是**本次27个新增SETUP=0的共同直接阻断条件**；其他两条门槛也有部分失败，但不能取代这个共同失败原因。

- 27/27 历史quote中位比率未达`1.5x`；最小 **0.116856**、中位 **0.365063**、最大 **0.760111**。这是历史评价时点的**最近15m与先前15m的5m成交额中位比值**，不是币价涨幅、现在成交额、24h交易额或真实净收益。
- 唯一失败：成交额比率不足 **18**。
- 双重失败：成交额比率与最近三根5m价格上涨步数不足 **8**。
- 三重失败：成交额比率、上涨步数、最后收盘价未维持先前15m收盘价 **1**（GPSUSDT）。
- 单独按指标统计（可重叠）：成交额比率失败27、上涨连续性失败9、最后收盘价格比较失败1；上涨步数分布1步9个、2步15个、3步3个；价格维持通过26/27。
- 27个事件均来自**确实推进D1的真实选槽时点**，不是读取全周剩余行情或事后寻找最有利一根K线。原FIFO8有效首评172 → Fair8 199（新增27），该27个原FIFO LATE；原120 SETUP事件全部保留、没有新增SETUP。
- **阶段性经营决策**：不能把公平排队改善当成盈利策略改进，更不能直接降低`1.5x`、延长15m、放弃quote过滤来回测这27个已曝光币并宣称更优。这类阈值研究只能提前预注册并在**独立时间窗口、完整市场分母和真实买卖成本**中检验。

## 二、事实来源与复现

**原始身份与原算法不变**：

1. 原Stage162 full A/B [Actions #39068290868](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39068290868)的JSON SHA256 `c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2`，真实source含269候选、753个D1选择槽和选中时刻记录。
2. [Stage164已归档的27个确切Queue Episode ID](evidence/monster_stage164_original445_fair8_new27_nonconversion_actual_v1.json)，Git Blob `40aeb187320ea3efc3b8b6bd8a0a8ae1d4d10098`。
3. 原2026年2月10天连续历史官方1m已经封存的**28个完整原始source ZIP + publisher SHA proof**，由 [Stage162原仓库来源收集器](../local-agent/scripts/monster_v4_shared_445_archive_replay_runner.py)读取之前GitHub Actions已经归档的18个历史Artifact，`verified_shard_paths`逐ZIP SHA/manifest/proof校验。新工作流没有向Binance请求当前行情，也没有以新收集取代旧证明。27币各12960连续1m，经[原`shared.prepare_symbol`](../local-agent/scripts/monster_v4_shared_spot_d0_d1_original_core.py)生成闭合5m。
4. 对Stage162选槽原记录中仅这27个 `valid_5m_evaluation_marker_advanced=True`的准确tick，从原缓存调用未更改的 `verified_closed_5m_for_original_d1()`，最终由原生产 `monster_v4_shadow.evaluate_closed_5m()` 计算；同时用原Decimal中位值重新判三个组合条件、检查结果相同。这27名共被D1选中44槽，但**确实推进5m评价游标的只有27槽**。不能把其余17个未推进槽也算独立判断。
5. 真实工作流[Stage165 #39131879722](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39131879722)，固定代码+测试SHA **`dc9d09ebce688bd33d901fbfed2b00ea49ae5910`**，单Job **11/11步骤Success**，`Ran 6 tests ... OK`，原Stage162 SHA验真、原28个原始ZIP SHA校验、27行source明细和Git写回均成功；封存 [Stage165源证据机器JSON](evidence/monster_stage165_original27_real5m_d1_feature_failures_actual_v1.json)，Git Blob **`c891a18cb970baff793e31ddb611fdfde578bff9`**。
6. 初次 #39131804513 FAILURE 保留：作者最初误以为本次所有第一次负面5m评价都应`PENDING/NO_SETUP_YET`；原真实Shadow明确在**等于15m截止时**将负面评价写成`EVALUATED/NO_SETUP_WITHIN_WINDOW`（27个中10个发生于+15m），其余17个更早才是PENDING。定向更正**研究事件状态预期**后没有修改原生产Shadow/D1或研究参数；复跑成功并记录精确失败原因。不得删除旧失败证据。

## 三、真实代码与当前状态

本轮新增`local-agent/scripts/monster_v4_stage165_original27_d1_feature_causal_audit.py`、`local-agent/tests/test_monster_v4_stage165_original27_d1_feature_causal_audit.py`、显式push触发**仅一次/无定时**`.github/workflows/monster-v4-stage165-original27-d1-feature-source-once.yml`；研究需求与原始条件在代码之前已冻结至 [Stage165原预注册](MONSTER_STAGE165_FROZEN_27_D1_REAL_5M_CAUSAL_THRESHOLD_DIAGNOSTIC_20261018.md)。源固定代码SHA`dc9d09ebce688bd33d901fbfed2b00ea49ae5910`，结果由CI提交到同PR分支。

**已确认**：原生产D1三条件、确切原27 episode、原5m tick原字节来源、全部失败条件组合。

**未确认**：真实同信号时刻Spot订单簿、是否真实可买、用户真实手续费等级、能否在已冻结退出窗口以可成交卖盘盈利、新独立OOS转化、Stage165新代码其他AI独立审查；Stage164/Stage165样本来自已曝光2026年2月445/原758删失313，不得泛化到2026年10月。

**本轮代码审查**：`AUTHOR_CODE_AND_OFFICIAL_ARCHIVED_EVIDENCE_PASS`，`INDEPENDENT_OTHER_AI_STAGE165_REVIEW=NOT_DONE`。以前Codex批准的Operator及Stage163 V3固定SHA不能覆盖新Stage165分析脚本。不得部署/发信/下单，保持`G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。

## 四、给独立其他AI的固定SHA局部审查任务

> 你是独立Claude或Codex审核者。请针对仓库 `https://github.com/lxxlx2/ChatGPT_mission_record` 的Draft PR #30，审查唯一Stage165原代码/测试/工作流固定SHA `dc9d09ebce688bd33d901fbfed2b00ea49ae5910`，对比Stage165方案冻结提交 `4f1e2f791a8239bb547b6224d03c50b2ae15d0a1`；审查时以固定SHA detached checkout而非后续PR HEAD。核对原Stage162 full A/B真实归档 SHA256 `c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2` 和原Stage164 27 episode Git Blob `40aeb187320ea3efc3b8b6bd8a0a8ae1d4d10098`，核对全部28原publisher source ZIP与proof的GitHub artifact来源独立，不新增现时行情。新`monster_v4_stage165_original27_d1_feature_causal_audit.py`必须只以Stage162 `valid_5m_evaluation_marker_advanced`真实tick原27/44D1选槽，调用**真实原`monster_v4_shadow.evaluate_closed_5m`**且Decimal比率不得用四位显示近似代替`>=1.5`判断。独立计算每一候选三项条件、完整27的失败组合(单quote18、quote+steps8、三项全部1)、比率min/median/max约0.116856/0.365063/0.760111和`setup_candidate=False`。另检查10个截止时实际EVALUATED/NO_SETUP、17个截止前PENDING/NO_SETUP，原27都来源可证、原120 SETUP保持，不得夸大为完整758/独立OOS/策略净收益。实际复核[Stage165 #39131879722](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39131879722) fixed SHA、原CI日志测试6/6/来源SHA/衍生Git blob，以及原失败[#39131804513](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39131804513)的原因与修复是否仅研究元数据，不改Shadow/D0/D1或交易。给出`APPROVE/REQUEST_CHANGES/BLOCKED`、审查者、精确底层模型版本或UNVERIFIED、准确SHA、P0/P1/P2、源码行号、独立测试与不能验证之处。仅审核新Stage165原D1指标取证范围，不重新审核已批准的Operator/Stage163静态价格，保持`G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。不要冒充已经盈利或可以发BUY。

## 五、Codex 取得全原始Publisher Artifact后的独立复审：APPROVE（2026-10-19）

**本次用户转交的独立Codex最终结论：`APPROVE`，新增P0=0/P1=0/P2=0。** 唯一审核SHA `dc9d09ebce688bd33d901fbfed2b00ea49ae5910`，预冻结比较基线 `4f1e2f791a8239bb547b6224d03c50b2ae15d0a1`，审核者Codex，精确底层模型版本`UNVERIFIED`，独立 detached checkout `/tmp/monster165-review-dc9d09eb`。先前Claude聊天针对该SHA的`BLOCKED`是**当时因无法取得原Publisher Artifact而不能独立核验**，不能追溯改写；Codex现已另外取得源并实际完成独立复算，故当前新证据的独立代码/数据审核门禁关闭。

Codex **未执行上传的`verify_independent.py`**，而是自行从GitHub Actions取得Stage162完整A/B（原 SHA256 `c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2`）与28份官方归档source ZIP，校验**全部445个符号**源ZIP、inner manifest与28份proof字节绑定和publisher日级回执，目标27币每币12,960根1m连续。另写独立脚本以Decimal对原Stage162新增27个首次有效D1实际tick、6根封闭5m、三项AND条件逐行复算，同新Stage165结果**27/27行一致**；成交额比率失败27、上涨步数失败9、价格维持失败1，互斥失败模式18/8/1、新增SETUP 0，原27非PIT交易不可买卖身份。比率边界用Decimal未依赖四位显示。

独立按原Stage162 trace确认首次有效D1延迟+6m 1、+9m 8、+12m 8、+15m 10；截止之前17个`PENDING/NO_SETUP_YET`、截止时10个`EVALUATED/NO_SETUP_WITHIN_WINDOW`，故早前一次CI [#39131804513](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39131804513)失败和只改研究断言的修正真实成立。Codex实际执行6/6单测、编译、独立重算、冻结CLI；冻结CLI整文件与[成功CI #39131879722](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39131879722) Artifact**逐字节一致，SHA256 `1690078cb41fc6c0c46a44f2c33910d52c63c9fe53daea338a5a592dc0539216`**；CI固定SHA精确匹配、11/11步骤成功。

**审核边界**：Codex未单独向Binance重下载并验证445币全部原publisher日ZIP/CHECKSUM（此层`UNVERIFIED`）；未重跑其他418币的完整策略；不能声称全758、上市当时真实PIT、可执行真实买卖、利润或OOS。对同一已APPROVE SHA不再重复修P3或重复向别的AI发同一任务。Stage165研究源代码、生产D0/D1/D2、Frank、Mac没有新执行代码变动。

**下一主线只允许**按原已冻结 `2026-10-17T22:06:00Z..2026-10-24T22:06:00Z` 的完整未来Spot OOS官方来源成熟后，固定全市场分母与同时间 D0→D1（FIFO8/Fair8）及真实交易成本判盈利价值；样本尚未成熟前不得宣称正净收益，也不部署。维持`G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。
