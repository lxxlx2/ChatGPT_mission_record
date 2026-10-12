# Monster Stage88：305 条 D1 之后 24h / 72h 真实历史分钟价格路径预注册

日期：2026-10-13（Asia/Bangkok）。原 Monster Draft PR #30。只做已曝光历史的 **价格代理验证**，不修改 V4 D0、Stage79 D1、原信号时刻、任何历史失败或原资金门槛。真实 BUY/邮件/本机部署/自动交易均 NO_GO。

## 一、研究目标与不可混淆的标签

Stage83 的七日窗口起点 OPEN→未来 HIGH 2× 是发现指标，不能回答「在 D1 之后才看到提醒，能否参与并退出」。Stage85 的全部305个研究 D1 有官方原始已闭合分钟特征，Stage87证实简单量价/减BTCETH不足以解决G3。Stage88只测 **D1之后、事先固定入场时点的单币多空不对称价格路径**，不根据已知赢家选币，不调整阈值。

- 原始 D1 人口严格锁定：`monster_stage85_all305_official_D1_asof_features.jsonl`，Git blob `622299fec16400e189cb8fa668ecbc8bc31ec630`；305/305，164首次DIRECT、141后续REIGNITION；原 519 D0 仍在 Stage83 文件，不能静默删掉未升级214条。
- 6个旧七日窗口全部保留，包括后验不达锚点2×、混合 USD-M 的TradFi、乘数映射未证实与一条 ETHUSDT。**总表是混合交易标的研究人口**，不能称为已验证的Crypto-only赚钱机会，也不能据此运行交易。
- 正式主入口代理：观察D1于`t`（分钟整点）成立，**等一根完整1m之后**，以`t + 1min`开始的分钟bar的 `open` 为 `entry_open_delayed_1m`。这是历史 K 线参考价，没有盘口、撤单延迟、资金冲击或保证成交，**不构成真实入场价格**。附加敏感性 `t`当分钟open，标记`OPTIMISTIC_NO_DELAY`；不作为主要成绩，也绝不声称它可立即成交。
- 24h 固定退出：从延迟入口`t+1min`开始满1440分钟，最后一根bar的close，即bar开始于`t+1440min`；72h为4320分钟，退出bar开始于`t+4320min`。首分钟OHLC指标从入场bar开始计算，不使用D1之前的价格路径。
- 每个长度窗口的 `fixed_exit_gross_return_pct = (exit_close / delayed_entry_open - 1)*100`；`MFE_high_pct=(max(high after entry)/entry_open - 1)*100`；`MAE_low_pct=(min(low after entry)/entry_open - 1)*100`；`max_close_to_close_drawdown_pct`从**入场价+观察路径实际close形成的运行最高价**计算最大跌幅，注明它是路径风险代理；另存退出min/max时间以供审计。所有数值 Decimal，不默认手续费、滑点、仓位、杠杆、资金规模。
- MFE来自历史HIGH，**不能当任何退出能实现的收益**，也不能以未来最高点确定策略卖点。负MAE或强回撤不等于实际止损已成交。24h与72h分别严格计算是否完整，不能拿24h完整证明72h完整。
- 若延迟入口bar的`num_trades<=0`或`quote_volume<=0`，标为`ENTRY_PRICE_PROXY_UNSUPPORTED`，保留D1但不记有效入场回报。来源ZIP、.CHECKSUM或K线缺失，按`SOURCE_CENSORED`独立保留24/72小时状态，不记0%收益。任何已有Stage83/Stage85日zip SHA与新下载相冲突直接FAIL。

## 二、官方来源与分片

只用 `data.binance.vision/data/futures/um/daily/klines/` 和 Stage38 `verified_1m_day`（官方每日发布方SHA核对+1440条连续1m价格成交额/笔数）。按D1`t`的自然UTC日到`t+72h+1m`所需日期逐日取数，按实际分钟整点检查缺口；绝不补造最后成交价。每个样本只需当前D1日及未来至多5个自然日，远小于 Stage83 的9日源包。与Stage85记录已核验日及Stage83原逐币日官方SHA进行交叉对账。

按6个旧日期、日期内字母升序 `symbol index % 4` 固定24个分片，覆盖305条，不按标签拆分。数据从GitHub Actions一次性只读下载，禁止新增任何长期自动监控。运行后36? **本轮固定为24个行情分片 + 1合同自测 + 1聚合持久化，共26个作业。** 每一条都要回写两段价差及源情况到长期证据文件。部分源缺失可以`PARTIAL_CENSORED`持久化，但不得算样本外或假称全量可评价。

## 三、冻结的输出与验收

- 305条逐币记录：date/symbol/venue/firstD0_UTC/D1_UTC/path/identity（只用于来源分组）、真实源SHA、delayed entry时刻与open、24/72固定退出时刻与close、毛价差、MFE/MAE、真实历史OHLC路径最大回撤、24/72是否完整、缺档、源一致性。
- 聚合层：attempted、valid24/censored24、valid72/censored72、fixed_exit_gross>0占比（分母只含完整样本，另报全305分母）、固定退出回报中位数、MFE/MAE及回撤中位、严重负波动计数；按**6个不同市场日期、DIRECT/REIGNITION、原固定锚点2×/非2×**分层，不只统计历史赢家。日期内多个币相关，必须显示6个日期个别表现，不把305视为独立前瞻交易。
- 不做真实净利润的计算/声称，不新增隐含固定20bps、历史30U/300U资金或新的交易阈值。历史交易资格/实际bid-ask/挂单深度/市值/上市身份尚不够，因此最终状态`REAL_EXECUTABLE_NET_PNL=UNKNOWN`。
- 失败时如实保留 CI 和原数据，不改参数救分；完成只读归因后，针对暴跌/回撤与错过机会研究一个真正可独立前瞻检验的后续确认层，不继续在旧2×上反复排序。

## 四、执行边界

严格遵守 `MONSTER_MODULE_DEVELOPMENT_RULES.md`、Stage77和Mission Spec。研究实行`HISTORICAL_EXPOSED_ONLY`、`OOS_NOT_DONE`、`OTHER_AI_REVIEW_NOT_DONE`、`DEPLOYMENT_NO_GO`、`GMAIL_OFF`、`AUTOTRADE_NO_GO`、`FRANK_UNCHANGED`。真正独立前瞻窗口仍为2026-10-14、10-28、11-11 UTC06各七日，今日尚未成熟，不能声明通过。
