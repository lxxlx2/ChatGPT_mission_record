# Monster Stage83：完整519条原D0连续3m回放预注册协议

日期：2026-10-13 Asia/Bangkok。范围仅原 Monster Draft PR #30，明确承接 Stage77/78/79/80/81/82。不更改原始 V4 D0/P1/P2/First5 或 Stage79 双入口参数，绝不运行生产系统。

## 一、完整数据边界（在任何 Stage83 新下载前锁定）

严格复用 Stage64 全量**519条首次原D0**，Git blob `8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a`：旧6个日期 `2025-01-30, 2025-06-02, 2025-08-01, 2025-10-02, 2026-06-21, 2026-07-28`。完整币日期涵盖事后普通币和所有旧2×币，包含非Crypto、历史退市、单位乘数不明对象；只允许为**正式Crypto模型评分**另外标记分类，不能从519研究总体偷偷删除任何一个。

每个日期对519行按 symbol 排序，以 `index % 6` 分为 6 份，完整为 `6 x 6 = 36` 个时间/分片组合。冻结的是完整事件人口而非某次 CI 成功子集。缺档按 `CENSORED_DAILY_OFFICIAL_1M_MISSING`、原有首次61m特征不匹配按 `SOURCE_PARITY_FAIL` 阻断；不能将缺档当无信号、非2×或亏损。对确定股票/RWA跟踪的 USD-M 永续合约保留 D0/D1 探索性结果，但标记 `OUT_OF_CRYPTO_SCOPE`。对其它没有正向官方加密标的身份来源的保留 `CRYPTO_IDENTITY_UNVERIFIED`，不合并为已证实的Crypto可执行交易机会。

## 二、官方取数与同代码因果回放

复用原 Stage38 的 `verified_1m_day`，它对 Binance USD-M 每日1m ZIP 和发布者同日 .CHECKSUM 校验、检查1,440根连续分钟、2025后的微秒时间戳归一化。为降低请求量，仅取首次 D0 之前61分钟起至其后48小时结束或原UTC06起点之后168小时（先到）所需自然日，通常2至4天。用 Stage64 已保存的同日期 ZIP SHA 和原真实前61分钟收益、quote成交额、成交笔数、15m/45m标准化量比逐字段核对。严禁根据未来价格选择币日期、时间窗口或重试替身；暂时不可获取的归档保留错误类别和请求日期。

所有已闭合 K 线连续后，每3分钟调用**原 Stage80 相同纯函数** `evaluate` 和 `from_archived_closed_bars`，其合约 Git blob `292e0cefe2089214dbde48ee50d6baf6cf590f8e`，首次D0时间不许更改；直通与二次点火条件均仍来自已冻结合同。48小时之内首次 D1 后停止重评；不创设额外 P2 / 预留/第2次 D1。

**研究时钟要分离**：源末根 K 线收盘时刻、首次D0、D1观察时刻、未来2×首次HIGH分钟为不同时间轴。旧 Stage52 全5400条真实来源案例 Git blob `ad7544f97e8a0d6c1f2635aa54052cca42d08cf1` 只作为**回放完成后**的评分标签和交叉账本。首次 HIGH 对应的是固定七日锚点 OPEN → HIGH，不能当 D1 可成交卖价。不得更改 Stage52 的历史标签和漏报情况。

## 三、严格提前指标与交付

**只在全36个分片成功对账后**作聚合；如果某分片失败或缺档，只能注明 `PARTIAL`，不得拿成功样本声称完整519验证。保存每条 `date, symbol, D0 UTC, D1 UTC/path, original 2×/5×/10× and first crossings (evaluation-only), source/identity status, SHA receipts, source missing`，按日期统计 D1 首次/再次、唯一候选、42个完整UTC06 24h桶的平均/峰值/配额与超额情况。

D0已提前至少5分钟的旧2×集合，用D1确实**在第一次2× HIGH发生前至少5分钟**的保留数 / 这个 D0 eligible 数，预设阈值≥80%。同时列出D0严格/5分钟提前、5×/10×逐案、普通非2×D1总量和拥挤日。若本次只是混合USD-M完整519回放，记 `EXPOSED_MIXED_VENUE_DIAGNOSTIC`；正式 G0 Crypto 独立检验及真正新日期 OOS 仍 `NOT_DONE`，不得挪用历史标签冒充新样本。

现有阈值：D0≥90%严格与≥85%提前5分钟，D1≥80%保留，平均≤5条/天、单日≤12条，重大5×/10×遗漏逐案；如任一失败，不改参数救结果，记 `REJECTED_EXPOSED`。**若真正Crypto身份/盘口来源缺失，保持 `EXECUTION_UNKNOWN`，不以0交易/未知资格声称模型准确率好坏。**

## 四、执行及安全

分片作业只读 Git 仓库与 Binance 公共历史行情，可通过 CI 严格核验发布者SHA并上传有限期分片工件；聚合以全部原519和原Stage52来源SHA为准，能持久提交到同 PR 时必须实际核查 commit/push 回读。GitHub Actions的临时成功日志不能替代长期成果；本轮不创建自动监控、不调用邮箱、不触发任何本地服务/Frank、无自动交易/通知。

此处全部是已曝光历史资料的**新策略探索性回测**：`HISTORICAL_EXPOSED_ONLY`，`OOS_NOT_DONE`，`D2_REAL_NET_PROFIT_UNKNOWN`，`INDEPENDENT_OTHER_AI_REVIEW_NOT_DONE`，`MONSTER_DEPLOY_NO_GO`，`GMAIL_OFF`，`AUTO_TRADE_NO_GO`。
