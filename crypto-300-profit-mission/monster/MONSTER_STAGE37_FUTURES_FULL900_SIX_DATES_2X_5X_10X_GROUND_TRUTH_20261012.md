# Monster Stage37：全部900个USD-M历史普通USDT符号 × 六个自然日，真实七日2×/5×/10×事件与完整来源分母

日期：2026-10-12，Asia/Bangkok；归属唯一 Monster [Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。主线仍是**妖币发现事实数据分析**，不是BTC交易，不做持仓时长优化。不改原生产V4/Frank/Gmail/Mac/交易。

## 一、数据和开发程序已经实际执行

- 先查Binance官方USD-M所有历史归档，锁定[Stage36 1,061个USD-M归档目录，其中900个普通USDT符号](evidence/monster_stage36_official_usdm_archive_vs_spot758.json)，正式Git blob `91b0f99ef85adb48494c5be5c7cc13a7cedcb686`。
- 在读取本轮月度K线之前先提交[Stage37冻结实验合同](evidence/monster_stage37_all900_usdm_sixdate_7d_GT_prereg_20261012.json)，原始commit `868950053ddbb34edc3364528a5064d15bd3eda6`。每个日期原样遍历全部900符号，不在看涨幅后挑币。日期取Stage30现货对照的六个UTC06点起点：2025-01-19、04-19、07-19、10-19；2026-04-19、07-19，每个向后168小时。
- 原 [Binance Public Data](https://github.com/binance/binance-public-data) 中USD-M月度1小时官方ZIP与发布者 `.CHECKSUM` SHA256双验证；[Stage37完整源码](../local-agent/scripts/monster_v4_stage37_usdm_sixdate_full900_hourly_labels.py)按UTC时间顺序读取168根1h的open/high/close，按首根open设定固定历史价格基准，只有所有168根连续且来源SHA通过才计入可评分母。每个无法下载的月度ZIP标 `SOURCE_404_MONTHLY_1H_NOT_OBSERVABLE`，历史1h缺口标 `CENSORED_NOT_168_CONTIGUOUS_HOURS`；不将缺档=无妖币。支持官方USD-M CSV列名表头而非照搬Spot无表头解析器；K线high触及2×/5×/10×仅为**事后价格标签**，不是卖出成交价或实盘利润。
- 第一轮[原始失败CI #38205975221](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38205975221)因官方月度USD-M CSV包含header而误判 `BAD_CSV_ROW`，确实FAIL；读取日志后修复表头与纯数据行严格区分并加入真实ZIP模拟回归测试，commit `26c878a13522002bafe2ee9bcdaa63ac1a7f2127`。**失败CI没有被计为成功来源，也没有把CSV失败计作阴性。**
- 修复后[真实6日期×6分片×150符号的完整USD-M 1h源CI #38206141845](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38206141845) **36/36 SUCCESS**。另一个[重新下载全部36份原始Artifact、SHA重算并独立汇总CI #38206247576](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38206247576) **SUCCESS**，永久机器登记[逐分片36原ZIP及原JSON SHA、全部日期分母和类别结果](evidence/monster_stage37_sixdate_all900_source_SHA_historical_GT_summary.json)。
- 全部[5,400条源状态和真实GT标签CSV](evidence/monster_stage37_sixdate_all5400_usdm_source_and_GT.csv)与[52笔1h HIGH翻倍的真实币日期事件清单](evidence/monster_stage37_all_source_verified_2x_winner_registry.csv)由聚合CI写回原Monster分支Git commit `0a9876d4a52e1cfca24d0166213194a74285bd05`。正式聚合Artifact ID `11727591560`，ZIP SHA256 `ca11af35b9c8745e35bac494e7235521459d7c0a5b746485e785bc8d9dc10276`，另行下载本地核算ZIP及内部5400行/源完整数/GT数字一致。

## 二、六日期真实USD-M历史标的机会分母

| UTC实验起始日 | 官方1h完整币日期 | 高价未来达到2× | 达到5× | 达到10× |
|---|---:|---:|---:|---:|
| 2025-01-19 | 385 | 1 | 0 | 0 |
| 2025-04-19 | 434 | **19** | **1** | 0 |
| 2025-07-19 | 493 | 8 | 0 | 0 |
| 2025-10-19 | 574 | 10 | 0 | 0 |
| 2026-04-19 | 664 | 9 | 0 | 0 |
| 2026-07-19 | 783 | 5 | 0 | 0 |
| **合计** | **3,333** | **52** | **1** | **0** |

900×6 = **5,400次公开归档符号/日期尝试**。来源完整3,333（61.72%）；来源删失2,067（38.28%），其中官方所需月度1h没有归档的2,012币日期和虽然有月度档案但七日缺小时的55币日期。S3有符号目录不等于每个历史月份都上市或有可交易合约，更不说明404期间没有涨幅。

**对比旧现货758名单：**

| 原USD-M symbol与Spot 758名单关系 | USD-M尝试币日期 | 官方完整 | 首根开盘价七日后HIGH≥2× | ≥5× |
|---|---:|---:|---:|---:|
| 名字也在Spot研究758中的472种 | 2,832 | 2,399 | 31 | 1 |
| **名字不在旧Spot758中的428种** | **2,568** | **934** | **21** | 0 |

这 **21个** 2×案例证实了一个重要研究缺口：**仅分析过去现货758个symbol名字，会直接漏掉在USD-M其他符号名下出现的部分爆发行情。** 但禁止声称它们一定是21种独立仅在合约交易的Crypto：部分合约采用乘数命名，亦可能有RWA、标的更名或历史Spot symbol不在该冻结集合里。

21个历史USD-M相对Spot名字增量事件（币种仅指交易对原始symbol，未映射经济标的）包括：

- 2025-04-19：`BROCCOLIF3BUSDT`（最高约3.39×）、`NEIROETHUSDT`（约4.49×）、`ZEREBROUSDT`（约4.83×）、`JELLYJELLYUSDT`（约3.00×）、`GRIFFAINUSDT`、`KOMAUSDT`、`MYROUSDT`、`SWARMSUSDT`。
- 2025-07-19：`PORT3USDT`、`VINEUSDT`。
- 2025-10-19：`AIAUSDT`、`EVAAUSDT`、`HUSDT`、`LIGHTUSDT`、`PIPPINUSDT`、`RIVERUSDT`、`XPINUSDT`。
- 2026-04-19：`BASUSDT`、`BSBUSDT`、`PIEVERSEUSDT`。
- 2026-07-19：`ONUSDT`。

最高5×的唯一源完整合约币日期为 **2025-04-19 `ALPACAUSDT`**，7日期间1h HIGH / 起点open 约 **5.7158×**；最接近5×的还有 `SPKUSDT`（2025-07-19约4.954×）以及 `ZEREBROUSDT`（2025-04-19约4.828×）。**不存在源完整的10×合约事件，不得假报10×召回率。** 

## 三、该怎样推进妖币发现主线，而不是把合约误包装成现货交易盈利

本轮完成的是USD-M市场的**真实历史7日期机会底册和正常合约对照**，未做到真正发现模型回放。下一项应保留整批3,333个已验证完整1h标签为研究分母，从官方USD-M 1m归档及发布方SHA因果运行同一份V4 `observe_snapshot/process_queue`，严格要求信号时间小于首次触及2×的**真实分钟HIGH时刻**。不能只拿52个事后赢家跑2分钟信号，把其它3,281个正常币、上市/退市删失和通知压力丢掉。

1. **真正历史身份分层。** 区分 USD-M 现货同名 / 非同名、`1000*` 乘数合约、RWA/非Crypto、曾上市但已退市；任何未有官方合约元信息/历史资格的标为 `ENTITY_OR_CONTRACT_TYPE_UNVERIFIED`，不得将其纳入可现货买入建议。
2. **原V4在合约市场的发现回放。** 1m真实完整记录需要因果闭合、真实滚动成交额和同源D0/D1；共享队列容量另行分类。先报告3m扫描发现的真实2×/5×召回、提前量、普通合约WATCH、漏报、不准把未来高价当交易价。
3. **市场覆盖和模型关系。** 现货18日期Stage35已得到持续动量与短时极端放量的描述性差异，但USD-M模型不能未经数据验证就沿用这套结论。之后再完成统一的WATCH/IGNITION指标方案、技术方案、源回测、独立AI真实review与修改测试；生产部署直到允许前一律 NO_GO。

**Stage37 USD-M official 900×6 hourly source and GT truth = PASS；USD-M 1m historical V4 signal recall = NOT_DONE；FULL MONSTER DATA ANALYSIS = PARTIAL；NO NEW BUY MODEL VALIDATED；OTHER AI REVIEW = NOT_DONE；Gmail/Mac/auto trading = NO_GO；Frank = UNCHANGED。**
