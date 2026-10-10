# Monster: 2021–2026 全量已导出 5× 事件清单（用户 Mac 实测，2026-10-10）
 
## 样本与证据范围

记录来自用户本人 Mac 上的只读提取脚本终端输出。没有收到原 CSV；本表严格抄录该输出的 40 行，仅供重放样本定义，不声称此刻已重新验算每根 K 线/原始档案哈希、5m 成交、流动性、最高价有效性或个人真实收益。

三份实际读取的用户文件：
- TRAIN_2021_2023: `train-instrument-events.json`，共 **1,920** 条 GT 2× 事件，5×以上 **20**；
- VALIDATION_2024: `validation-instrument-events.json`，共 **442** 条 GT 2× 事件，5×以上 **4**；
- EXPOSED_2025_2026: `ground-truth-events-v1.json`，共 **1,542** 条 GT 2× 事件，5×以上 **16**；
- `MISSING_SOURCES=[]`；共 **3,904** 条 >=2× 事件，**40 条 >=5× instrument events，36 个不同交易 symbol**。

当中的 **5 个 Binance UP/DOWN 杠杆代币交易对事件**和 **1 个 PAX 稳定币交易对事件**须保留为“数据清洗反例”，**不能作为普通代币妖币正例**。因此首期研究主样本为 **34 条 >=5× instrument events、30 个不同 symbol**，仍须进一步验证极端 wick 的成交真实性。未来要做严格 entity 级回测还必须处理 PNUT/MMT/PEOPLE 双场所实体映射和 FIDA 两次独立事件。

> 数据语义：`max7d` 是锚点 close 到未来 168h 期间单根 high 的最大比值；这只足以构成 GT 候选。每条事件都需要补 `anchor quote/trades`、`peak UTC`、`quality_flags`、`crossing times`、`age/new_listing`、5m/1m bars、book/funding/OI 的确切覆盖。当前“理由”主要是**为何值得放进某类历史测试**，不是已确认的涨幅成因。

## 40 条全量登记

| # | 时段 | 市场 | Binance symbol | 锚点 UTC | 7d最高/锚点收盘 | 预分组 | 纳入或单列理由 |
|---:|---|---|---|---|---:|---|---|
| 1 | TRAIN | spot | UNIDOWNUSDT | 2021-05-06T01:00Z | 45644.163150× | SPECIAL_LEVERAGED | Binance 杠杆代币；极端倍数需核对净值调整/锚价，不作为普通币上涨 |
| 2 | TRAIN | spot | PAXUSDT | 2021-07-19T02:00Z | 999.000000× | SPECIAL_STABLECOIN | 美元稳定币 PAX；999× 不是常规妖币证据，优先核查锚点与异常 high |
| 3 | TRAIN | spot | MIRUSDT | 2022-12-19T00:00Z | 16.625537× | PRIMARY_REVIEW | 2022 旧标的极端上涨；验证是否低流动性/插针，不能事先定性 |
| 4 | TRAIN | spot | FIDAUSDT | 2021-10-27T21:00Z | 14.233727× | PRIMARY_REPEATED | FIDA 第 1 次 5× 事件；与 2022 第二次复发对照 |
| 5 | TRAIN | spot | PNTUSDT | 2021-01-24T22:00Z | 14.178113× | PRIMARY_REVIEW | 旧标的 14×；检验前置成交量与成交持续性 |
| 6 | TRAIN | spot | OSMOUSDT | 2022-12-03T18:00Z | 12.588117× | PRIMARY_KNOWN_MISS | V3-062 已知遗漏的 10× 事件；旧报告标记低锚点流动性与极端波幅 |
| 7 | TRAIN | spot | CHRUSDT | 2021-03-06T04:00Z | 10.414258× | PRIMARY_CLUSTER | 与 CHZ、VITE 同一小时锚点；测试市场共振/同小时批量性 |
| 8 | TRAIN | spot | ADADOWNUSDT | 2021-05-12T13:00Z | 9.428571× | SPECIAL_LEVERAGED | Binance 下跌方向杠杆代币，非 ADA 普通现货 |
| 9 | TRAIN | spot | XLMUPUSDT | 2021-01-01T00:00Z | 9.391095× | SPECIAL_LEVERAGED | Binance XLM 上涨方向杠杆代币；起始日边界还需单列 |
| 10 | TRAIN | spot | CHZUSDT | 2021-03-06T04:00Z | 9.103960× | PRIMARY_CLUSTER | 与 CHR、VITE 同小时锚点；测试跨资产共同信号 |
| 11 | TRAIN | spot | FIDAUSDT | 2022-11-14T00:00Z | 7.242878× | PRIMARY_REPEATED | 同一普通代币的第 2 次独立 5× 事件，检验复发型模型 |
| 12 | TRAIN | spot | UNIUPUSDT | 2021-01-23T18:00Z | 6.783340× | SPECIAL_LEVERAGED | Binance UNI 上涨方向杠杆代币，非 UNI 普通现货 |
| 13 | TRAIN | spot | XLMDOWNUSDT | 2021-05-12T13:00Z | 6.479482× | SPECIAL_LEVERAGED | Binance XLM 下跌方向杠杆代币，非 XLM 普通现货 |
| 14 | TRAIN | spot | STPTUSDT | 2021-09-29T10:00Z | 6.359602× | PRIMARY_REVIEW | 普通旧币中等 5–10× 样本，检查报价活跃与回撤 |
| 15 | TRAIN | spot | DFUSDT | 2022-10-15T15:00Z | 5.963303× | PRIMARY_REVIEW | 2022 中等倍数旧币，检验低成交复活路径 |
| 16 | TRAIN | spot | VITEUSDT | 2021-03-06T04:00Z | 5.688448× | PRIMARY_CLUSTER | 与 CHR、CHZ 同小时锚点，控制整体市场驱动 |
| 17 | TRAIN | spot | ANCUSDT | 2022-05-18T11:00Z | 5.478983× | PRIMARY_REVIEW | 2022 特定事件风险样本；需核实停牌、成交与流动性 |
| 18 | TRAIN | spot | RIFUSDT | 2022-11-21T12:00Z | 5.375335× | PRIMARY_REVIEW | 普通旧币 5× 边界样本，检验量价筛选漏报 |
| 19 | TRAIN | spot | FUNUSDT | 2021-01-01T00:00Z | 5.177276× | PRIMARY_LEFT_EDGE | 训练集首日锚点，检查首次事件有无足够之前历史 |
| 20 | TRAIN | spot | NANOUSDT | 2021-01-01T00:00Z | 5.071686× | PRIMARY_LEFT_EDGE | 训练集首日锚点，检查 prior lookback 和非独立市场共振 |
| 21 | VALIDATION | futures | PNUTUSDT | 2024-11-11T13:00Z | 6.307215× | PRIMARY_LISTING_DUAL | 2024-11-11 Binance 合约上市；与同币现货成交及时间差对照 |
| 22 | VALIDATION | spot | PNUTUSDT | 2024-11-11T11:00Z | 5.893446× | PRIMARY_LISTING_DUAL | 2024-11-11 Binance 现货上市；对照 futures，观察可跟随窗口 |
| 23 | VALIDATION | futures | PEOPLEUSDT | 2024-01-01T00:00Z | 5.768931× | PRIMARY_LEFT_EDGE_DUAL | 2024 验证期首日锚点；与现货同币去重和跨段时效 |
| 24 | VALIDATION | spot | PEOPLEUSDT | 2024-01-01T00:00Z | 5.698437× | PRIMARY_LEFT_EDGE_DUAL | 与 PEOPLE 合约同小时同币事件，不能算两个独立代币 |
| 25 | EXPOSED | futures | BABYUSDT | 2026-05-29T10:00Z | 87.897228× | PRIMARY_WICK_AUDIT | 87.9× 极端 high；先核实 5m/1m 成交、mark 与可交易深度 |
| 26 | EXPOSED | spot | BIFIUSDT | 2025-12-17T21:00Z | 77.525667× | PRIMARY_WICK_AUDIT | 77.5× 极端 high；核实真实成交及异常价单笔影响 |
| 27 | EXPOSED | futures | MMTUSDT | 2025-11-04T13:00Z | 14.951270× | PRIMARY_LISTING_DUAL | Binance 2025-11-04 合约上市；历史 V3 迟到/漏报代表 |
| 28 | EXPOSED | spot | MMTUSDT | 2025-11-04T13:00Z | 10.323875× | PRIMARY_LISTING_DUAL | 与 MMT futures 同币同时锚定，双 venue 验证上新捕获 |
| 29 | EXPOSED | futures | PUMPBTCUSDT | 2025-09-18T23:00Z | 8.885641× | PRIMARY_RENAMED_CONTRACT | PumpBTC 衍生品，2025-06-13 Binance 从 PUMPUSDT 改名，需查合约历史不连续 |
| 30 | EXPOSED | futures | AVNTUSDT | 2025-09-09T16:00Z | 8.261457× | PRIMARY_PRE_SPOT_LISTING | 合约锚点早于 2025-09-15 Binance 现货上市，检验上市预热 |
| 31 | EXPOSED | futures | BTWUSDT | 2026-06-04T15:00Z | 7.743505× | PRIMARY_KNOWN_MISS | V3 确认较 V2 延迟 23 小时且曾出现另一次 BTW missed-alert 事故 |
| 32 | EXPOSED | futures | CUDISUSDT | 2025-10-28T22:00Z | 7.724886× | PRIMARY_REVIEW | 普通合约异常上涨；驱动与盘口仍未知 |
| 33 | EXPOSED | futures | LABUSDT | 2026-05-01T06:00Z | 7.228388× | PRIMARY_REVIEW | 普通合约 7× 样本；检验量价先行，未证实 OI 领先 |
| 34 | EXPOSED | futures | SLERFUSDT | 2025-10-11T06:00Z | 6.577941× | PRIMARY_POST_CRASH | 2025-10-10 市场大跌后窗口，考察广泛反弹与个币差异 |
| 35 | EXPOSED | futures | BLESSUSDT | 2025-10-13T11:00Z | 6.386258× | PRIMARY_POST_CRASH | 同一宏观冲击后几日窗口，考察恢复型上涨 |
| 36 | EXPOSED | futures | ALPACAUSDT | 2025-04-27T10:00Z | 5.923920× | PRIMARY_DELIST_RISK | 交易所已宣布 2025-04-30 合约结算退市；可能极难实际跟随 |
| 37 | EXPOSED | spot | BROCCOLI714USDT | 2025-12-24T20:00Z | 5.500407× | PRIMARY_MEME_SPOT | Meme 现货；测试是否存在可持续真实买盘而非高点插针 |
| 38 | EXPOSED | futures | ESPORTSUSDT | 2026-06-09T02:00Z | 5.207536× | PRIMARY_REVIEW | 5× 边缘普通合约样本，避免只优化极端赢家 |
| 39 | EXPOSED | futures | MUSDT | 2025-07-07T10:00Z | 5.109567× | PRIMARY_IDENTITY_AUDIT | MUSDT 原符号保留；不能把 M 与其他币种误认，需核对 baseAsset |
| 40 | EXPOSED | futures | CLOUSDT | 2025-10-14T12:00Z | 5.085550× | PRIMARY_REVIEW | 旧案例笔记遗漏的第 16 个 2025–2026 事件，重点检查历史全集漏样 |

## 身份与边界核验（外部官方来源）

- 杠杆产品：Binance 官方发布 `UNIUP/UNIDOWN` (2020-09-29)、`ADADOWN` (2020-07-15)、`XLMUP/XLMDOWN` (2020-12-09)。它们是以永续头寸为基础的特殊杠杆产品，而非相应 UNI/ADA/XLM 现货正常涨幅。官方公告：https://www.binance.com/en/support/announcement/detail/979821ae853e4b95a4c309792c9b66e9 ; https://www.binance.com/en/support/announcement/detail/73a5d3352ae944fe8e899d2602bee27c ; https://www.binance.com/en/support/announcement/detail/90505420e14c41c2b0853947cdb7dd08
- PAX 是 Paxos Standard 美元稳定币，于 2021-09 更名为 USDP，原设计为 1:1 美元稳定；999× 极端 K 线值目前来源可疑，须以历史交易、锚点价、API/ZIP 原始单根及盘口复核。https://www.binance.com/en/support/announcement/detail/627ea984daa44ee4a5ac27fe658cc180 ; https://www.paxos.com/newsroom/paxos-launches-new-stablecoin-paxos-standard-pax
- PNUT 2024-11-11 Binance 现货 10:00 UTC、合约 12:30 UTC，历史锚点分别现货 11:00、合约 13:00，是可用的“新币首小时”多市场案例。https://www.binance.com/en/support/announcement/detail/d16d96c136154680a6373225d592bca1 ; https://www.binance.com/en/support/announcement/detail/f689ebe21cdb4eda91bd0071de48e6f8
- MMT Binance 2025-11-04 合约上市，现货同日，交易公告：https://www.binance.com/en/support/announcement/detail/c18b1bfd706648189e9f7ac9097351cc
- AVNT 合约信号发生在 2025-09-09；Binance Spot 2025-09-15 05:00 UTC 才上市，不能拿 spot 成交提前当成可执行入口：https://www.binance.com/en/support/announcement/detail/50ff03bc1d94471181887c43b930d3f0
- PUMPBTCUSDT 是 PumpBTC 衍生品合约，Binance 于 2025-06-13 关闭旧 `PUMPUSDT` 并推出新命名合约；主样本仍保留但须核对历史断点，不能与 Pump.fun `PUMP` 不加区分：https://www.binance.com/en/support/announcement/detail/38a74ee47cdc43ebbc672e1dc6968358
- ALPACA 合约在 2025-04-30 09:00 UTC 预定强制结算退市，公告发布于 2025-04-24；2025-04-27 的历史 high 必须评估真实可跟随性和停牌/结算限制：https://www.binance.com/en/support/announcement/detail/0274f9d47da1437990bc13eb17b0ec99

## 历史研究的下一步（用户暂不批准模型代码开发）

1. 输入完整真实 CSV（包括 quote、quality flags）或原本不可改的 `train/validation-instrument-events.json` 与 `ground-truth-events-v1.json`，核对 40 行哈希/价格数据与每个事件 peak UTC。
2. **34 个主正例不能全部视作正向可成交机会**：BABY/BIFI 单根极端 high 必须单独证实；PNUT/MMT 同币双市场；FUN/NANO/PEOPLE 属分段首日，可能有样本 warmup 左截断风险；SLERF/BLESS 在市场整体闪崩后；ALPACA 临退市；2022 OSMO 被 V3 漏报。
3. 从**全部 3,904 个 2× 事件**抽出 2–3×、3–5× 同币对照，再抽普通非 2× 候选；按总体 GT 年份/venue 记录样本量。
4. 只用因果过去数据，按历史可观察时刻重放第一 WATCH / SETUP / IGNITION；逐个计算 signal lead to 2×、未来5m/15m可成交代理 MFE/MAE、成交额/深度、通知延迟、正常与极端跳价的分布，不以 high 当真实买价。
5. 逐币第一轮结果先交用户审核，**不改 V4 参数、不启用新的本地监控或 Gmail、不动 Frank**；2024/2025/2026 结果均为暴露样本，不能再称独立验证。

**研究和分类结论的权威顺序：** 用户本次 Mac 实测文件/原始 Binance 档案 > 官方 Binance 产品公告 > 原项目已记录的汇总。此表没有私钥/邮箱/钱包/生产 DB 字段。
