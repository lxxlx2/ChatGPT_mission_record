# Monster Stage128：原始5400样本来源删失、上市窗口与漏报分母真实对账

日期：2026-10-14 Asia/Bangkok。原 [Monster PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。**研发结果，不是新实盘行情，不是 Stage118/127 策略过关，也不是新独立前瞻。** 本次没有修改交易策略、原阈值、历史标签、已有自动采集状态、Frank、Gmail 或 Mac 程序。

## 1. 核心问题与结果

先前 Stage93 已有按历史六个七日锚点、每个锚点900个事后登记的 USD-M 合约样本的全市场尝试，原历史519仅包含已 WATCH，不能替代全部分母。最新 Stage127 提前关注候选失败（16/22=72.73%且日均6.86、峰值18），明确禁止对已曝光519重新调参。本轮**直接复用先前真实原始5,400全市场数据**而不是再设计一个追涨过滤器，检查历史来源缺失中哪些可能涉及当时的尚未挂牌/窗口内新挂牌，避免因为忽略新上市币导致漏报率虚高。

### 两层原始数据完整度，不混淆

| 样本数 | 已保存资料与实际结果 |
| --- | ---: |
| Stage37 全原始 symbol-date 历史尝试，6×900 | **5,400** |
| 官方 SHA 验证 168h 小时数据完整 | **3,333** |
| Stage37 历史小时数据不完整 | **2,067** |
| Stage39/93 进一步成功取得完整、价格与小时源一致、按旧 V4 回放的 1m 数据 | **3,283** |
| Stage93 一分钟级最终删失 | **2,117** = 2,067 小时缺失 + 47 官方1h/1m价源冲突 + 3 一分钟缺档 |
| 完整一分钟历史下真的触及固定锚点2× HIGH | **51** |
| 其中首次 D0 提前至少5分钟 | **48**（48/51=94.12%，历史子人群，仅 gross HIGH） |
| 其他重要2× | CETUSUSDT 晚320分钟；PENGUUSDT 无任何 WATCH；FUSDT 同一分钟 WATCH（无法证明早于上涨） |

这个 **94.12%只限3,283个来源完整的、已曝光历史 USD-M 混合标的尝试**。整体被删失2,117条，缺真实当时上架资格与独立 crypto 发行资产身份，正式 G0/G1 `NOT_SCORABLE`，绝不视为真正未见过的新三窗口OOS或者净盈利。

### 使用后来的 Stage123 exchangeInfo 做诊断，仅标明可能的来源解释

历史 Stage37 2,067 条小时不完整，对照 **2026-10-14T09:48:24.840Z** 已归档的 Binance USD-M 927项现有 exchangeInfo 完整源：

| 比对所见（不当作历史上架事实） | 原小时不完整样本数 |
| --- | ---: |
| 后来的 onboardDate 落在历史七日窗口**之后或结束点** | **1,869** |
| 后来的 onboardDate 落在历史七日窗口**中途** | **31** |
| 之后的 exchangeInfo 已不含该 symbol | **167** |
| 后来 onboardDate 等于或早于历史开始且小时数据不完整 | **0** |
| **合计** | **2,067** |

另外 **15 条原小时完整**，但后来 Binance exchangeInfo 当前记录的 `onboardDate` 却晚于那个观察锚点；**25 条原小时完整**却已在后来的现有 metadata 中找不到该 symbol。15 条冲突包含跨日期重复出现的 CTK、CVC、CVX、LIT、SLP 及历史 PUMP/AIA 等具体符号；原官方 1h 历史证据不会被后来的字段覆盖。这证明现有 `onboardDate` 不能自动作为 2025 年实盘交易资格证明，可能牵涉重新挂牌、符号重用或源定义差异，原因尚 **UNVERIFIED**。

其中 **31 个窗口内的 later-onboard 案例**是真正值得后续调查的 G1 重大缺口：原 Stage37 以「整整168小时连续K线」为准入要求，若合约从窗口中途才上市，便会因不能提供完整七日K线而退出研究分母，即使它在上市后快速涨了两倍也不能从旧 G1 判断出来。**本批31个只证明后来的 metadata 日期位于观察窗口，没有逐个验证当时的官方挂牌公告、第一笔合约交易、真实1m完整性或上市后价格倍数，不得说31个真有2×、或称自动修复了G1。**

## 2. 研发实际执行与可复算证据

- 提前冻结 [Stage128 研究合同](MONSTER_STAGE128_FROZEN_HISTORICAL_UNIVERSE_CENSOR_LISTING_RECONCILIATION_20261014.md)，commit `3490151df6ffa4d228343246dc8bc180140743e2`；随后实现 [离线5,400全量对账程序](../local-agent/scripts/monster_v4_stage128_historical_listing_censor_audit.py) 和 [测试](../local-agent/scripts/test_monster_v4_stage128_historical_listing_censor_audit.py)。
- 源字段全量来自 Git 中不可变 Stage37 历史 CSV（Git blob `4b02019195a7a48ef6d33606db9b57d6a3429f4b`）、Stage93 原始完整历史模型结果，以及 Stage123 八文件市场源；Stage124 原始 loader 独立校验927、525及source shape。不另用当下市场网络代替原历史。
- [Stage128 Ubuntu/macOS CI #38561158512](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38561158512)：Ubuntu job `115842276788` 和 macOS job `115842276999` 均实际 SUCCESS，源码 SHA `df9468901ff863623c33aa621f062e9f745fb36b`；本轮新单元测试 + 5,400源真实全量对账，两OS输出的完整 stdout 研究字段逐项一致。没有按源码返回0就假设 CI 实际成功。
- 永久 Git 机器结果：[Stage128全5,400汇总 JSON](evidence/monster_stage128_original5400_later_metadata_censor_machine_summary.json)；特别保留 [31个潜在窗口内上市+15个历史源冲突，46条逐事件证据清单](evidence/monster_stage128_31_later_listings_and_15_historical_clock_conflicts.json)。此外两OS完整诊断 JSON 作为CI artifact归档，可由原源+同代码随时重算。
- 未写入新的监控、未调整 Stage77 G0–G6，未产生任何 BUY、收益率、交易资金默认值、仓位、Gmail 或用户Mac操作。

## 3. 下一步主线按重要性

1. **优先核实31个候选窗口内上架实例**：结合官方历史上市公告、按上架前后时间实际公布的一分钟档案和第一笔真实成交记录，拆分真正中途上市、符号重命名/重用与数据源变更。计算上市后整个剩余观察时间里的真实 2x 候选，不能用窗口开始时该币尚未上市的价格作为虚假零价格或负例。必要时作为独立 `NEW_LISTING_CENSORED` cohort 保留。
2. 15条“历史完整但当前 onboardDate 较晚”优先做源定义冲突证据复查，不根据日期假设伪造旧挂牌资料。167条后来元数据已缺席的小时不完整实例同样留审计，不标未上市。
3. 拟定一个**新样本完整动态上市覆盖**准入协议，独立锁定上市前/后全量交易对、第一分钟及无 WATCH 的所有赢家分母，再将原 V4 D0 和事先冻结的新 D1 放到真正未知市场区间验证，不能在历史名单和现有涨幅倒推阈值。
4. G4 仍需用户明确notional、同一实际 D0 时间的多档深度/有效费率、以及后续真实退出报价；Stage126 可见 L1 挂单不等于进场/退出净盈利。等 G0–G4 实证成立再申请其他 AI 独立review与独立 Mac 部署审批。

现状：`STAGE128_REAL5400_SOURCE_COHORT_RECONCILED=YES`; `STAGE128_CI_MAC_UBUNTU=PASS`; `STAGE93_48_OF_51=EXPOSED_SOURCE_COMPLETE_ONLY`; `STAGE118=REJECTED`; `STAGE127=REJECTED`; `G0=PARTIAL`; `G1_NEW_FULL_CRYPTO_MARKET=NOT_SCORABLE`; `G2_G3=REJECTED_EXPOSED_STRATEGIES`; `G4=UNKNOWN`; `INDEPENDENT_OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOY=NO_GO`; `FRANK=UNCHANGED`; `NO_AUTO_CAPTURE_OR_TRADING_OR_MAIL`.
