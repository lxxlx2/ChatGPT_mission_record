# Monster Stage 10–11：不挑涨幅对照组与官方历史ZIP逐根交叉验证

日期：2026-10-11（曼谷）。状态：**真实历史数据研究已完成这一批；策略盈利仍未验证，独立AI Review未完成，Mac部署和真实邮件保持NO_GO**。

## Stage 10：先冻结再看行情的随机市场时间对照

- 首先读取官方 Binance `exchangeInfo`，记录当时现货可交易USDT对504个并**在拉取历史数据之前**提交完整名单、6个观察日期、固定FNV1a哈希抽样程序和24个抽中的符号。原始预登记表：[24例＋504冻结Universe](evidence/monster_stage10_neutral_preregistered_24case_20261011.json)。
- 按实际预登记的24例独立向Binance官方索取其历史1m数据；17份按时间要求获得每份连续3600根（60h），共 **61,200根已冻结在Git**；7份指定历史时间晚于第一根返回历史bar，保留[7例不可用证据](evidence/monster_stage10_fetch_status_20261011.json)，没有替换、更改日期或补造历史。
- 历史条件：以预先固定的 UTC 12:00 为**日历锚点，不是旧信号的WATCH**；先24h成交额预热，再对周围12h执行生产V4 `observe_snapshot`、`process_queue`，最后保留24h退出评估窗口。模拟每3分钟观察1m已收盘close，quote24以此前1440根实际1m quote成交额构成历史代理；过去真实ticker快照及当时上架状态未知。
- [初次稀疏版实际CI](evidence/monster_stage10_actual_neutral_17valid_ci_20261011.json)显示17例 240×17=4080理论轮次中3186轮末分钟有非零真实成交、894轮末分钟无成交；稀疏历史回放器跳过无成交轮次，观察159.3个“非零分钟采样小时”，WATCH=0/D1=0。这**不等于**交易所停更894轮，也不等于真实生产在这些分钟无法扫描。
- 为查清代理偏差，另用**同一生产D0/D1**执行两种历史行情输入：①每3分钟持续更新最新已收盘1m close+过去24h成交额的“持续ticker代理”（204个标的小时，4080观察点），②零成交末分钟跳过的“稀疏代理”（159.3个非零采样小时、3186观察点）。[真实并行敏感性CI数据](evidence/monster_stage10_ticker_sensitivity_actual_ci_20261011.json)及 [CI #38115342552](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38115342552)证实**两组在这17例都为WATCH=0/D1=0**。主研究以后采用持续ticker代理，稀疏版只当保守灵敏度测试。
- 每个交易对的0量分钟覆盖差异很大：ZRX样本182/240个3分钟观察点末分钟无成交；TNSR为180/240；而ENA、ADA、NEAR、ONDO、LTC全240有成交。这些**不是网络丢包或正式生产行情源缺失**，不能据此编造源覆盖率告警。
- 在这批17个随机对照12h窗口里**没有任何WATCH，所以没有任何30USDT交易可以估算收益**。模拟PnL字段为`null`，不能写成0%盈利或验证亏损。当前504列表在2026-10-11而观察日期在2025–26，存在明显幸存者偏差；本批6个日期、17个合格symbol×12h并不足以推断全年每日误报率。Stage7/9的事后涨幅案例无法与这份控制直接推为全市场precision。

## Stage 11：免费、可由云端自主复现的 Binance 官方批量原始数据渠道

官方项目：<https://github.com/binance/binance-public-data>，历史数据位于 `https://data.binance.vision/data/spot/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM-DD}.zip` 及对应 `.CHECKSUM`。**官方文档特别说明2025-01-01起Spot ZIP为微秒时间戳**；读取后须标准化为毫秒再与REST比对。

- GitHub Actions [#38115489739](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38115489739) 真实从该官方归档自主下载 4币×3个自然日＝12份ZIP和12份发布者SHA256并逐份验证。
- 4个此前固定在Stage10的2026-09案例：QUICK、TNSR、PORTO、LTC，截取各3600根1m（总 **14400根**）；独立ZIP与之前Binance REST冻结文件的毫秒时戳、OHLC、quote和成交笔数**逐根完全一致**。
- 完整的12个SHA256、来源、CI证据在 [Stage11 Git证明](evidence/monster_stage11_official_archive_rest_parity_ci_20261011.json)，下载/解压/校验逻辑在 [脚本](../local-agent/scripts/monster_v4_archive_crosscheck.py) 和对应单元测试，源错误不能静默吞掉。
- 这是**来源一致性证据**，不是算法正收益证据；但证明不需要用户Mac或付费数据服务，就能以官方文件扩展分钟历史研究。ZIP当前不能提供旧时真实orderbook和user实际手续费。

## 后续明确阶段

已在[Stage12全部504币单日预登记](evidence/monster_stage12_all504_spot_universe_preregistered_20261011.json)冻结2026-09-17 06:00–18:00 UTC的“**所有当前已上市USDT现货对**”（仍不是历史point-in-time全市场），用GitHub云端多线程抓官方日ZIP+SHA、重放生产D0/D1，并统计日历窗口全场WATCH密度和30USDT含费价差情景（仅有WATCH且有效退出时）。Stage12结果是否合格必须看真实CI后单独归档，**不能在任务仍运行时提前宣告成功**。

完整后续要求：多时段、多牛熊、真正历史场所universe、更多已知5x/10x漏报、全市场普通活动的通知预算、30USDT真实深度门槛/失败模拟；冻结策略与退出规则；其他AI实际独立Review和修复验证后才可考虑Mac与Frank并行部署。正式通知送达再独立验收，自动交易NO_GO。
