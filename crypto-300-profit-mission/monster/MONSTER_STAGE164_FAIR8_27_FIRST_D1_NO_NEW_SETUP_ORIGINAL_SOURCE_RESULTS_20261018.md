# Monster Stage164 — 原官方源A/B：Fair8新增27个有效D1首评为何未变成新SETUP（2026-10-18）

## 结论：减少漏审，但旧业务转化增益为零

**作者通过完整Stage162真实历史A/B Artifact原始958,656字节JSON逐候选核查，确定新增的27个D1首评：** 原FIFO8全部`LATE`；Fair8全部`EVALUATED`，27/27最终`candidate_queue.last_error=NO_SETUP_WITHIN_WINDOW`，**新增SETUP=0、丢失旧SETUP=0**，原120个SETUP原始事件IDs保留。此结果仅说明：这些候选在**该冻结历史研究的原D1实现和15分钟窗口中**获得可用首评，但最后没有出现SETUP；**不能由`NO_SETUP_WITHIN_WINDOW`单独推断它们在每根5m K线上具体哪个价格/成交量指标失败**，本Stage162 Artifact不包含逐次原始5m指标断言与每币种逐栏原因，标注`UNVERIFIED`。

因此Fair8原“首评覆盖更高”的工程收益真实成立，却**没有得到新可操作研究信号或历史净利润改善的实证**。不能据此放宽D1阈值、追加成交或推荐买币。

## 原始证据身份、不可覆盖与可复现方法

- 原公开源是Stage162单次官方445完整市场历史研究[Actions #39068290868](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39068290868) 的已有 Artifact ID `12113719899`，名称`monster162-real445-first-valid-5m-fair8-ab-once-v4`，文件`monster162_actual_445_fair8_ab.json`，**958,656字节、SHA256 `c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2`**。本轮作者独立下载ZIP并算SHA，明确原完整445仅属于原758的可用445，313删失，**非新独立OOS或真实上市PIT**；没有重新抓Binance、未获取实时行情。
- 新**完整逐27次候选证据**：[Stage164原445新27明细JSON](evidence/monster_stage164_original445_fair8_new27_nonconversion_actual_v1.json)，真实Git Blob `40aeb187320ea3efc3b8b6bd8a0a8ae1d4d10098`；每行保留原queue ID、token symbol、cohort、first_seen_ms、baseline/alternative最终状态、新有效首评延迟、Fair8选择次数、原队列末次D1说明，没有以币种名代替队列episode ID，更没有将最终`last_error`伪装成准确历史as-of发生时间。
- 研究脚本`local-agent/scripts/monster_v4_stage164_fair8_nonconversion_audit.py`、独立最小反例回归`local-agent/tests/test_monster_v4_stage164_fair8_nonconversion_audit.py`，一次性push触发离线workflow `.github/workflows/monster-v4-stage164-fair8-new27-nonconversion-once.yml`。所有输入限定到原Artifact ID及原文件**固定SHA256**；错误源SHA、重复queue ID、ID丢失、事件身份漂移、15分钟以后伪首评、源人口/SETUP数量不符均fail-closed；输出目标已存在则拒绝覆盖。没有schedule、Mac、网络新采集、Frank、Gmail、交易/钱包权限。
- 完成证据的**原代码/CI触发SHA `d0a7ad450a0369f25dc30024aa72ed3ec703f83c`**；固定[GitHub CI #39130595768](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39130595768)唯一Job `original_archive_new27_source_audit` **SUCCESS，11/11步骤完成**，原始GitHub原Job日志实际`Ran 6 tests ... OK`、原文件`sha256sum -c: OK`、真实逐27结论输出、Artifact成功以及 `MONSTER164_RESEARCH_ONLY_NEW27_EVIDENCE_ARCHIVED_NO_DEPLOY`。Git落证据提交SHA `2166f552873092e2114fc009f3c42c71d0f8d013`，已实际从PR远端分支重新读取Git Blob和27行验证。
- 旧最早CI [#39130523311](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39130523311) **FAIL**，原因是新合成测试没有`schema`字段，严格模式按`j["schema"]`产生`KeyError`而非预期显式源漂移错误；修改`j.get("schema")`保留fail-closed `ValueError(STAGE164_FROZEN_ORIGINAL_445_AB_SEMANTIC_DRIFT)`后，在最终官方原档案跑通。这个失败轨迹保留，不删除、不伪装首次即过。
  
## 全量269 D0 WATCH下的27次增量明细复算

| 冻结原始指标 | 数量 |
|---|---:|
| 实际纳入队列的 WATCH episode | 269 |
| 原FIFO8有效首次5m评价 | 172 |
| Fair8有效首次5m评价 | 199 |
| **净新增有效首评** | **27** |
| 损失原有有效首评 | 0 |
| PEAK_98 新增有效首评 | 25 |
| OTHER_171 新增有效首评 | 2（GPSUSDT、LUNAUSDT） |
| 新增27个原FIFO最终状态LATE | 27 |
| 新增27个Fair8最终状态EVALUATED | 27 |
| 新增27个原队列最终诊断NO_SETUP_WITHIN_WINDOW | 27 |
| 新增SETUP / 原SETUP丢失 | **0 / 0** |
| 保留原SETUP原始Event IDs | 120 |

27次首次有效D1评价相对WATCH的实际延迟（不是交易通知延迟）：

| 首次有效5m评价延迟 | 人数 |
|---|---:|
| +6分钟 | 1 |
| +9分钟 | 8 |
| +12分钟 | 8 |
| +15分钟 | 10 |

同源原调度槽对这27名的使用次数：10名各1槽、17名各2槽；**不把“2次被选中”理解成两次有效评价或两个新信号**。25名在`PEAK_98`一轮98币WATCH爆发，另外两名属于`OTHER_171`。原时钟分布在11/12/2025等不同日研究群体，不和Stage30或Stage152相加求同一投资胜率。

**解释证据级别**：
- **已证实（冻结字节）**：所有新增27都从FIFO最后LATE变成Fair8最后EVALUATED；最终队列`NO_SETUP_WITHIN_WINDOW`；事件级SETUP新增0、120原SETUP保持不变。
- **只能推论**：改善队列覆盖本身没带来这批候选的SETUP，需要分析是否D1条件、15m窗口、行情不足；这并不代表另一时期必为0。
- **仍未确认**：原5m判定各指标失败细节、事件实际下单是否能够成交、Bid/Ask真实深度、手续费层级、真实成交和退出、实际净利润；Stage163旧T0+静态报价不能用于这批旧WATCH成交回填。

## 研发决策与独立审查门禁

**不将Fair8推生产，不改原D0/D1阈值、不以扩大研究时间窗或追寻事后赢家来优化这27个旧样本。** 先用真正冻结的2026-10-17T22:06Z→2026-10-24T22:06Z同venue新源完成后（至少2026-10-24T22:06Z之后）拿齐当时市场人口、官方逐分钟价、source可见性及原D1全机制，做未来样本同槽 FIFO/Fair配对并报告净新SETUP、损失SETUP和实际买卖盘/退出净成本。若仍新增SETUP=0，则`NO_PRODUCT_LIFT`，仅保留为研究级服务公平性改善。

**新Stage164研究代码/结果独立其他AI复审：NOT_DONE**。旧 Stage162 独立审批、Stage163 V3审核批准、Operator查询器 Codex `6dd74eb...` 旧SHA APPROVE都不自动批准新增Stage164脚本。但Stage164来源真实CI与计算已完成，无开发者授权的Mac安装、实时扫描、自动买币行为。所有门禁保持 `G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。
