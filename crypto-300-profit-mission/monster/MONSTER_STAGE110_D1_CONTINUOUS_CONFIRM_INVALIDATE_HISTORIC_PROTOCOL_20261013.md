# Stage110 — 已曝光历史D1后连续1分钟确认与失效模型：先冻结策略

日期：2026-10-13，原Draft PR #30。Stage100/108/109都已按冻结参数完整历史回测且REJECTED：不能再用旧305条赢家反复调logistic、关注阈值和6/12/24h退出。用户要求的Monster主线是旧数据建模→完整回测→有问题改变策略层；已安装的Stage99仅为独立后台来源快照，不改动、不等其数据。

## 数据/人群和可审计准则

Stage83原519条D0、Stage79原305条D1（DIRECT164、REIGNITION141）全部保留。Stage85原D1收盘价、已闭合15m quote、原2×评价时点作为锁定输入；Stage88与Stage101对305条D1后真实官方1m ZIP及发布方SHA留痕。代码必须复查源日ZIP+CHECKSUM与Stage101报告逐日相同，缺源或SHA不符FAIL，不能删除负例。统一6个已曝光7天历史窗口，记录每个原519个币日期；214个无D1仅保留WATCH。未来独立数据不阻断历史研究，也不能用旧样本冒充OOS。

## 唯一固定的连续确认状态机 Stage110 V1（参数事先冻结）

- 原D0、Stage79 D1双路径、原首次D1评价时刻 t 一律不变。**Stage85源码 at(bars,t) 使用 bars[i-61:i]，所以评价t真正已知最后一根闭合1m bar的OPEN是 t-1m**，非t；Stage110实际从t+1m的bar开始最多30根新增闭合1m观察（刻意预留一整分钟，不偷窥t那根未闭合bar），新确认后再用下一根OPEN价格代理入场。首次官方CI #38415636244 因误用t的close对账而拒绝全部分片，此时间口径仅修正原已冻结数据对齐，不更改DIRECT/REIGNITION条件/阈值/24h退出。边界在UTC00:00时补读上一官方源日，并与Stage85 SHA精确核对，不直接跳过。任一根新1m bar的close与D1最后close相比≤-8%，在该分钟任何确认检查之前即INVALIDATED_EARLY_8PCT，不查看分钟HIGH/LOW决定成交。
- 每3根新已闭合1m形成一个非重叠3m block；检查点为第3、6、9……30根完成。D1前15m已观察quote额平摊到3分钟（quote15/5）为统一且>0的基线，区块实际成交笔数必须>0，源缺口报SOURCE_UNKNOWN。
- DIRECT首次入口：只能在第6、9……30根完成时确认，最近连续两个3m blocks各自quote额都≥该3m基线、实际交易笔数均>0、最新block的close≥前block的close且≥D1 close×1.02。
- REIGNITION后续重新点火：在第3、6……30根完成时，当前3m block quote≥3m基线×1.20、实际交易笔数>0、该block末close≥D1 close×1.01即确认。
- 只接受最早确认，确认信息须在该确认区块最后1m bar完成后才可观察；下一分钟open为严格价格代理入场，之后持有1440根完整1m，到最后1m close按价格代理退出。它不是orderbook的真实买卖价。30m未确认则EXPIRED_NO_CONTINUOUS_CONFIRM，D1_SETUP仍保留；已确认不得未来回溯改变。需记录每次的UTC、OHLC quote/trades来源、失效及EXPIRED原因。
- 原行情未来HIGH不可用于筛选。测试未来行情变化不得影响较早确认结果。若入场next1m bar没有交易，标ENTRY_UNTRADED_SOURCE_UNUSABLE，不可假算利润。

## 全量历史评价

- 对原519 D0保留，原305 D1逐条确认/过期/失效/无交易状态、路径、时点与数据源SHA，报告毛价格收益中位、上涨数、亏损≤-20%、盈利≥50%/≥100%、费边20/100bps固定敏感性（只能称PRICE_ONLY_PROXY、EXECUTION_UNKNOWN）。
- 用Stage83冻结的原2×首次HIGH UTC评价确认时刻相对2×最早时间是否≥5分钟，原本D0 early5m=28中至少80%才过G2；原27个D1提前的机会要逐条说明取消/延迟；5×/10×另列不漏报。G3按完整6×7=42个UTC06日全部确认PRIORITY自然日均≤5/天、单日峰≤12（不硬top-N删除）。历史毛收益中位需>0；所有指标标旧已曝光回测，不等于前瞻PASS。
- 全部24h收益来自确认后next-open→24h-close，原D1后入场+24h不可拿来冒充新模型表现。若无法证明真实盘前身份/bid/ask/notional/手续费，真实可执行费后净利润保持UNKNOWN；模型不能上线。
- 若本版失败，原样记录并REJECTED；不在同305样本上网格搜索确认阈值直到过关，再找新的可证伪交易逻辑。

## 工程顺序

1. 先提交冻结合同，才编写 Stage110 同一确认状态机及本地自测，必要时从真实官方日1m来源复核所有305 SHA。
2. 官方1m 6日期×4分片并行，汇总全305与519、负例和完整每日G2/G3、经济价格代理到原PR30；CI失败要修复，不能伪称PASS；严格不改Stage99与生产。
3. 新模型按G0-G5诚实判REJECTED或历史研究PASS，之后真实另一个AI独立Review；正式Mac模型部署、交易与Gmail需要新的独立用户授权。

当前：STAGE110_PROTOCOL=FROZEN_BEFORE_CODE；STAGE108/109=REJECTED；G0_CRYPTO=PARTIAL；REAL_NET_PNL=UNKNOWN；NEW_OOS=NOT_DONE；MONSTER_PRODUCTION=NO_GO；FRANK=UNCHANGED。
