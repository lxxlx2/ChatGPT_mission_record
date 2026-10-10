# Monster 历史 5× 正例：真实 Mac 证据包第一轮 1h OHLCV 价格质量复核

日期：2026-10-10。状态：**READONLY_IMPORTED_EVIDENCE_AUDIT_PASS / NOT_EXECUTABLE_RETURN / NO_V4_MODEL_BACKTEST_YET**。

## 证据与审计范围

用户在本对话直接上传 `monster-backtest-packet-20261010.zip`，ZIP 文件 SHA256：

`5690f45856d6da15ef7e1c95f4f48ab5a803a45e53d5a4d640574de4388b26f7`

压缩文件内 **46 个成员**，单个成员 CRC 测试全部正常，`packet-manifest.json` 声明 **40/40 historical windows**、`missing=[]`。五份事件原始文件：两个 CSV + `train-instrument-events.json` (1,920)、`validation-instrument-events.json` (442)、`ground-truth-events-v1.json` (1,542)，总计 **3,904 条达到 2× 的 instrument 事件、40 条达到 5× 的 instrument 事件**。40 条的实际 1h K 线源窗口位于 ZIP 的 `bars/<period>/<venue>/<symbol>/<index>.json`，每条约 **锚点前 720h 至后 168h**；依源档长度可能短于 720h。

**此次计算确实逐条读取了已上传 ZIP 中 40 个 1h K 线窗口，并用每条 GT 原始事件的 `anchor_price/anchor_time/max7d` 逐项核对 `max(未来168h high)/anchor_price`**。没有联网重取 OHLCV，没有凭空补任何历史成交、资金费、OI 或盘口。与之前仅凭用户粘贴终端表/仓库报告的阶段不同，本次是实际文件数据的重新计算；但不是原始官方 ZIP 与 checksum 的独立重检。

## 最重要结论：最高价 5× 不等于可以跟随 5×

| 指标 | 40 条原始 GT 5× 事件 | 34 条剔除产品类型不匹配后的主研究事件 |
|---|---:|---:|
| 按未来168h 内最高单根 **high** ≥5× | 40 | 34 |
| 未来168h 最高 **1h close** 也达到 ≥5× | **16** | **15** |
| 未来168h 最高 **1h close <2×** | **8** | **5** |
| 单根峰值 K 线 high / 当根 close ≥3× | 10 | 7 |
| 有完整 24h 之前历史的事件 | 32 | 26 |
| 已上传 K 线窗口中存在小时断档的事件 | 11 | 6 |

余下 40 条里的 16 条介于最高小时收盘 2–5×；34 条主事件中有 14 条介于2–5×。小时收盘最高价本身仍不是可执行价格或 ROI，但能提示只统计高点会严重高估持续性。币种层面还需按 verified entity 而非 instrument events 去重，尤其 PNUT、MMT、PEOPLE 双场所与 FIDA 两次事件。

## 重点复算案例

| 标的 | 市场 | GT 7d high/anchor | 新计算 max 1h close/anchor | peak candle high / same-candle close | 数据意义 |
|---|---|---:|---:|---:|---|
| UNIDOWNUSDT | Spot | 45,644.163× | **1.336×** | 44,334.699× | 杠杆代币，不可当普通 Meme 涨幅 |
| PAXUSDT | Spot | 999.000× | **1.000×** | 999.000× | 稳定币异价，需要交易 / 锚点复核 |
| BABYUSDT | Futures | 87.897× | **1.149×** | 76.471× | 极端 peak high 与收盘严重背离，不能认作 88× 可跟随上涨 |
| BIFIUSDT | Spot | 77.526× | **1.509×** | 51.367× | 同上，极端 high 可能只是短促异常成交 |
| MIRUSDT | Spot | 16.626× | **1.992×** | 8.347× | 16× 并未持续到 2× 小时收盘 |
| FIDAUSDT | Spot，2021-10 | 14.234× | **1.804×** | 7.888× | 两次 5× 事件需分开，第一次极端插针 |
| OSMOUSDT | Spot，2022-12 | 12.588× | **1.293×** | 9.735× | 旧模型漏掉的 GT 极端高点；不一定是漏掉了真正可跟随的 12× |
| MMTUSDT | Futures | 14.951× | **9.380×** | 2.407× | 上市首小时但涨幅具有小时收盘持续性 |
| MMTUSDT | Spot | 10.324× | **9.245×** | 1.701× | 同币 Spot/Futures，不能算两笔独立代币 |
| BTWUSDT | Futures，2026-06 | 7.744× | **7.314×** | 1.457× | 较具有小时收盘持续性的上涨，适合作为“及时发现”的正例 |
| PNUTUSDT | Futures | 6.307× | **5.727×** | 1.136× | 上市早期成交条件与时间需单独重放 |
| PNUTUSDT | Spot | 5.893× | **5.377×** | 1.132× | 同币不同市场，实体级去重 |
| BROCCOLI714USDT | Spot | 5.500× | **5.468×** | 1.006× | 最高 high 与小时 close 几乎一致，优先保留为实际可跟随性候选 |
| ALPACAUSDT | Futures | 5.924× | **4.775×** | 1.344× | 退市结算约束须单独评估 |

注：`peak candle high / same-candle close` 衡量最大 high 出现的那根小时 K 线内的上影相对大小，**不是** `max(high)/max(close)`；报告使用这两种完全不同的时间/统计口径时不得混用。

## 时间序列完整性

- **40/40 条样本均有覆盖未来168h的小时 K 线观察**，且其最高 high 能重算符合对应 `max7d` GT（误差审计低于1%；报告展示数值经四舍五入）。
- 其中 **11/40 个窗口的小时序列存在 1–2 个相邻行时间跳步**：分别是 UNIDOWN、CHR、ADADOWN、XLMUP、CHZ、UNIUP、XLMDOWN、STPT、VITE、FUN、NANO；剩余29个无检测到的时间断档。后续策略/价格穿越计算必须显式按时间戳，而不能以连续数组行号视作连贯时间。
- **8/40 个事件锚点前不足24h有效历史**，对应 MMT 现货/合约、AVNT、BTW、PNUT 现货/合约、MU、CLO。这是从被打包的规范化缓存文件得到的窗口事实，不代表交易所此前不存在另一个产品或外部市场；这些样本不能被要求先有30天历史才发 early WATCH。
- 本次 K 线的 `quote_volume` 是小时区间的总成交额，即使峰值小时成交额很大，也不能证明交易者能够在 high 极值获得对应大额成交。只有当时逐笔和时间戳盘口才能更接近可执行价。

## 阶段划分（不得重新用暴露样本声称独立验证）

**A 组：独立交易所 1h 收盘 ≥5×**，优先研究早发现、连续放量、真实价差深度、按未来下一根5m/1m可观察入场的回撤与 MFE；现在仅知道 15 条普通代币 instrument events 符合这一组，不等同 15 个独立可交易代币。

**B 组：历史 high ≥5× 但最高 1h close <2×**，至少包括 BABY/BIFI/MIR/FIDA(2021-10)/OSMO，以及杠杆代币 UNIDOWN/ADADOWN 与稳定币 PAX（后3不属于普通主样本）。重点确认插针/价源异常/盘口规则，避免误把极端 high 包装成失去的盈利机会。

**C 组：上市/更名/退市等产品限制**，PNUT、MMT、AVNT、PUMPBTC、ALPACA；这些币能用于发现引擎回测，却不一定代表用户当时可以按 30 USD 现货订单跟随。

**负对照**：另外 **3,864** 条 2× 至不足 5× 的历史 instrument events 在 ZIP 中目前**只有事件元数据，没有对应全部非赢家的 1h K 线**，故当前不可能基于 ZIP 完成无偏精确率、所有 D0 原始时间的误报率或持续发现的全市场重放。下一步若需真正“全市场评估”，必须用 Mac 私有档案计算其特征或导出必要时间窗口；优先做摘要聚合，避免上传整套 19m K 线/GB 数据。

## 当前执行状态

- 完成：40 条真实 K 线窗口全部分析；完整正例历史价路径质量第一次归类；源文件哈希/ZIP完整性/缺口记录。
- 未完成：1m/5m、真实盘口与资金费 OI 完整匹配；样本外模型验证；持仓/滑点扣费 PnL；全市场负对照因果特征。
- `MODEL_CODE_NOT_STARTED`、`LIVE_MONSTER_NOT_RUNNING`、`GMAIL_NOT_ENABLED`、`FRANK_UNCHANGED`、`PRODUCTION_TRADING=NO_GO`。

特别说明：不因为“BABY/BIFI/OSMO 的 peak close 不高”而从历史标签集删除它们；原 GT 依旧完整保留，但实际投资回测按不同“可交易机会”层次标记和分层汇报。
