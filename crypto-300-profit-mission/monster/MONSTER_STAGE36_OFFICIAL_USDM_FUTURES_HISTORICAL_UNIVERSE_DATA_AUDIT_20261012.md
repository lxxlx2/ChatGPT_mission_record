# Monster Stage36：Binance 官方 USD-M 历史合约标的集合，现货758覆盖缺口事实核查

日期2026-10-12（Asia/Bangkok），[Monster原Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。本阶段仍为**事实数据分析，未进入新策略设计/回测**，不研究BTC交易或持仓时间，也没有修改Frank/Mac/Gmail/交易权限。

## 一、已完成官方来源、方法及持久交付

- 官方开源文档 [Binance Public Data](https://github.com/binance/binance-public-data)，列明USD-M Futures历史 `klines` 和文件旁对应 `.CHECKSUM`；目录仅表示曾经存在公开归档，不是各日期的实时 `exchangeInfo` 或 PERPETUAL 合约种类认证。
- 在请求USD-M目录前，先提交 [Stage36研究合同](evidence/monster_stage36_usdm_historical_archive_universe_prereg_20261012.json)，Git commit `05c0ca6d2f09ce6f758ac166f1328f94400a93e1`。研究来源限定官方 `data.binance.vision` 公共S3中 `data/futures/um/monthly/klines/` 和 `data/futures/um/daily/klines/` 的全部目录，使用S3 ListObjectsV2原生分页/游标；不挑2026年仍活跃的合约，也不把历史目录不存在的资产标作无暴涨。
- [只读官方S3原始枚举和分类器](../local-agent/scripts/monster_v4_stage36_usdm_archive_universe_inventory.py)，编译+隔离模拟XML/游标测试PASS，并对照Stage34已锁定Git blob的**758个曾在现货研究中的symbol**。S3四个响应XML的实际SHA256已保留，API观察时刻 `2026-10-12T04:54:45.277695+00:00`。
- [实际GitHub CI #38205690253](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38205690253) **SUCCESS**；完整[1061份官方USD-M历史符号目录及现货名单对照、分页源SHA证据JSON](evidence/monster_stage36_official_usdm_archive_vs_spot758.json)已经通过CI Git提交 `ba589911b8f6f2988908799d47d2ccabe182b5d1`，而不是仅停留在临时日志。原始artifact ID `11726714603`，ZIP SHA256 `0c61fea0f8fdf770d2dddbcb76725e906eca0de6468e15b68523d3ec6e58cc92`，已另行下载字节复核匹配。

## 二、实际全历史USD-M归档列表

| 历史归档目录分类 | 确认数量 |
|---|---:|
| 官方USD-M月度K线符号目录 | 1,056 |
| 官方USD-M日度K线符号目录 | 1,061 |
| 去重后的USD-M历史符号目录 | **1,061** |
| 无交割合约日期后缀、以USDT结尾的普通符号名 | **900** |
| 带六位日期后缀的 `USDT_YYMMDD` 命名 | 50 |
| 其它报价或命名格式 | 111 |
| 900普通USDT符号中，也在现货研究758名单内 | **472** |
| 900普通USDT符号中，不在现货研究758名单内 | **428** |

实际完整来源的两页月度和两页日度XML SHA256、分页边界、全部1061个符号和428个差集见永久机器JSON。集合对比是以 **symbol字面名称** 为单位，并不代表472个“相同经济标的”或428个“独立只存在于合约的妖币”。

## 三、主线价值：Spot历史样本真的漏掉大块合约世界

之前Stage34只覆盖现货758个候选。官方USD-M历史证据现在新增了**428个未在旧Spot清单中出现的普通USDT合约symbol名称**，例如 `1000PEPEUSDT`、`1000BONKUSDT`、`1000SHIBUSDT`、`AI16ZUSDT`；也发现 `AAPLUSDT`、`AMDUSDT`、`ANTHROPICUSDT` 这样的符号名。上述symbol仍仅为官方归档存在的事实，不推断它们对应的历史币种、实际交割/永续属性或当时交易资格，尤其不能把同名股票/RWA资产当成纯crypto妖币。

428个差集里有**12个**字符串以连续至少三位数字开头，含明显合约数量单位命名（例如`1000PEPEUSDT`）；其余也可能存在期货交易符号差异、上市退市或非数字标识的经济标的映射。**禁止凭名字去掉 `1000` 合并成现货 `PEPE` 计数**：经济标的确认需当前/历史官方合同元数据、价格单位与合约乘数，历史数据只能可靠地标为 `USD_M_ARCHIVED_SYMBOL_UNRESOLVED_ENTITY`。

**不能夸大**：`1061` 是曾经出现在USD-M官方公开目录的符号数量，**不是现在同时开放的1061合约，也不是1061个Crypto，更不是1061个未来妖币机会**。出现目录不证明有完整1h/1m历史分钟，也不证明官方发布者SHA恰好存在于2025–2026每一日期。真实涨幅与原V4的发现率尚未重放。

## 四、下一项研发任务的受限目标与退出门槛

完成USD-M历史归档**集合层**数据分析（DONE）；后续Stage37先进行**不看赢家结果的全900普通USDT符号 × 事前冻结七日日期**历史1h SHA验证与真实未来2×/5×/10×机会清点，保留每个404、停档和历史不完整案例，不将它们写成「无行情」；再利用校验后的分钟数据进行原V4因果WATCH发现统计、币安合同元数据分层和普通合约的噪声对照。某些标的可能是RWA、非币或交割合约，它们必须独立分类，不能合并到币种妖币召回率。测试期内没出现5×事件，也不允许报告“100%五倍召回”。

这条主线可以填补现货758来源固定后无法观察到的合约专属爆发机会。仍有现实限制：point-in-time `exchangeInfo` 与实际历史标的乘数/盘口、Solana/BSC链上meme源、真实通知延迟与独立另一AI Review都尚未完成。**不要以再做现货24小时持仓模拟代替这些市场覆盖问题。**

**STAGE36_USDM_DIRECTORY_FACTS = PASS；STAGE36_FULL_HISTORICAL_USDM_2X_5X_10X_LABELS = NOT_DONE；MONSTER_DATA_ANALYSIS = PARTIAL；INDEPENDENT_OTHER_AI_REVIEW = NOT_DONE；MONSTER_DEPLOYMENT = NO_GO；GMAIL = OFF；AUTO_TRADING = NO_GO；FRANK = UNCHANGED。**
