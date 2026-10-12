# Monster Stage63：完整全市场519个原始V4 D0 WATCH，避免已达到P1的166个幸存者偏差

日期：2026-10-12 Asia/Bangkok。只做Monster妖币模块，仍是原Draft PR #30。研究合同在获取本次519个源价路径之前固定，绝不移动原Stage52的P1 v0.3 REJECTED结论。

## 真实、预先固定的样本与源

- Stage52全900币×六个新日期=5,400币日期，3377个Binance官方1h/1m双源一致且成功回放原V4。原36个真正原始源SHA收据已被Stage52固定，且全市场每日期D0_WATCH币日期计数分别为161、34、54、75、100、95，合计**519**。
- 使用crypto-300-profit-mission/monster/evidence/monster_stage52_all5400_originalV4_P1v03_true_minute_source_cases.jsonl（原Git blob ad7544f97e8a0d6c1f2635aa54052cca42d08cf1），完整读取5400历史案例，严格保留全部原始5,400个状态及官方数据不可用的来源信息，提取且仅提取source_status=COMPLETE_REAL_USDM_1M_SHA_CAUSAL_V4及有第一次WATCH_UTC的519个币日期；不得按未来2×/5×标签挑样本。
- 其中有166个最终达到P1条件；另外**353个从未达到P1条件**，必须作为D0研究总体的重要普通对照，不能当坏币静默舍弃。
- 冻结原Stage52汇总Git blob 42d455a6cc9d0164a8dd94aa12a475bad5ed126e，Stage61首次D0 UTC Git blob 89634d4b8d049ad607be1f553515d11ff6e82573 与Stage62全166第一次D0后续价格及官方SHA Git blob 962b1ae289aa0af3f612499e169a686fc63645a1。

## 信号后K线算法与准确性闸门

- 使用与Stage60、Stage62同一个经过SHA锁定的价格路径核心 monster_v4_stage60_exposed_all166_post_signal_futures_price_paths.py，Git blob 6a638e84cf837ffc84a301649612e8f2f5dc1deb。
- 每个币首次D0 WATCH t后，独立从Binance USD-M官方真实每日1m ZIP和发布者CHECKSUM重新核验连续1440个1m真实bar。统一以 t 时刻开盘、t+1分钟闭合的第一根后信号收盘价作为事后价格代理，然后计算15分钟/1小时/6小时/24小时close、后续HIGH、后续LOW。严禁当作成交或净利润。
- 对已研究过的166条重叠案例，第一次D0 UTC、第一根后信号分钟close和所有四期限收益、高点、低点必须**逐值与Stage62独立真实SHA证据完全一致**。必须包括从未达到P1的353条，513/519等部分完成不能假报全覆盖，源损坏、缺档记录原状，绝不补数。
- 分组先于读取未来数据明确：原全519、最终达到P1的166、未达到P1的353、原未来固定日历GT2x与普通案例、不同六个日期。只做同源描述，不拟合新的动量、时长或评分阈值。
- 样本大小不能转换成“519条真实可现货买入”，链上、Binance Alpha和Spot实际可参与证据与USD-M风险要分开记录。单笔交易金额用户未指定，任何交易金额、盘口真实成交/盈利一律UNKNOWN。
- 新研究失败或总体D0表现不佳时，必须如实标注，不得只强调之前166个被筛选子集的较好表现，也不得回头改变旧失败门槛。

后续只有设计明确可证伪的新策略和技术方案、提前冻结新日期、跑完整全市场历史因果回放、独立其他AI review、测试修复全部过线，才考虑Mac本地部署。当前MONSTER NO_GO，GMAIL OFF，AUTOTRADE NO_GO。