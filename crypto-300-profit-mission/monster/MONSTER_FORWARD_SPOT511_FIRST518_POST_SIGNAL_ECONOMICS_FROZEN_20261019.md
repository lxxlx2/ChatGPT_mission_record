# Monster 前瞻 Spot511 第一段8 WATCH与8 SETUP事前固定短时价格经济协议（2026-10-19）

## 冻结对象和为什么做

此协议在取得所列事件的任何后续固定期限收益统计前创建；不允许从已知未来正收益挑选币或择时。唯一信号源为原CI [#39226387610](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39226387610) SHA `7a3b50f433bc4259fd8f1994e849fe46e3078fca` 真正产物，原始full JSON SHA256 `d51ce0faa70609dfa24659eed29958cef167c068838ad3986c6a8a0e297b0c2d`，Git文件 `evidence/monster_forward_spot511_first518_official_minute_causal_fifo8_actual_v1.json`（2026-10-19已入Git Blob `b2420434b00778d3578ac7f0c46edae1d13eaa69`）。

原冻结T0 511个Spot USDT TRADING及原发行方三天共1533个 `2026-10-16..18` ZIP/CHECKSUM经当次全源 SHA验证；此协议研究其中最早518个3m tick（2026-10-17T22:06Z至2026-10-19T00:00Z）生成的**全部8个WATCH和全部8个SETUP**。两种信号均逐条纳入，包括亏损、无量、24h不足源与无法入场；WATCH与SETUP属于两套互斥的交易替代视图，不双算16个同时仓位。

## 事前固定计价口径，不可用未来信息过滤

- 每个信号独立以原 `observed_ms+3min` **第一根完整未来1m的OPEN价格**作为价格代理入场（该分钟内成交额和成交笔数不能用来作入场前决策）。
- 入场前只允许检查紧邻前一分钟已闭合 `quoteVolume/trades` 的零/非零；未成交或先验零量的样本记 `CENSORED_PREENTRY_ZERO_TRADES_OR_QUOTE`，不得称有实盘下单机会。
- 固定三种持有期：**15、60、360分钟**；退出统一取 `entry+hold` 对应分钟的OPEN。退出资格只读退出前已闭合1m价格/成交证据，并显式标注零量；不因事后盈利挑选其他退出时间。
- 返回所有有效价代理的 `gross_pct` 和同一预设假设 `fee=10bps/side, slippage=20bps/side` 扣减后的 `net_price_proxy_pct`。这只是实验假设，非实际费率或真实ask/bid成交。不使用任何默认用户交易金额、不计算真实美元利润、不把价格代理称实盘资金收益。
- 缺少退出时间所属分钟档、窗口截止后的完整出处、异常/停牌或源缺失，都单独记录 `CENSORED_EXIT_SOURCE_NOT_AVAILABLE`；没有价代理就不填0收益。也单列 24h 退出观测可用性，不以Oct18源缩短固定24h。
- 按每个信号原 `event_id,observed_ms,symbol` 固定身份，不从后来上榜币过滤。只描述同一个币的WATCH与SETUP先后时差，不以未来SETUP标记在WATCH时作oracle筛选。
- 对每种固定期限逐类列全分母、可评价、盈亏、median、mean、删失；少量样本不外推为盈利率、广义G1/G4或完整7日OOS。对于500+币源全覆盖但D0仅处理509 ASCII的源口径保持不变。
- 严禁真实交易、Gmail、Mac/Frank/Stage99改动或新定时任务；所有结果继续 `G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。

## 必须产出的下一证据

同一已获哈希校验原Actions artifacts 1018+4+511中的对应原始issuer ZIP/CHECKSUM；原模型8+8信号的原SHA与唯一event_id；每币每单逐条件评价的可追溯机器输出；有可证伪反例的时间因果测试与成功原始CI；独立其它AI审核前标`NOT_DONE`。结果如果继续亏损就接受真实负结果，不在此日期改D0/D1阈值。
