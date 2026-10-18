# Monster主线 — 已冻结120个实际SETUP后价格与占用资金经济审计（2026-10-19）

## 为什么是120个、而不是更多代码/测试

已独立审核APPROVE的Stage162来自2026-02-04起计、758原宇宙中的445个原历史全源币，原同一SQLite实时研究3min时钟269 WATCH、实际120个`SETUP_ACTIVE`事件，其原真实完整A/B归档位于[Actions #39068290868](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39068290868) Artifact ID`12113719899`，内部JSON SHA256`c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2`。120个SETUP实际对应56个不同symbol，故不能把120个当独立市场事件。Stage164/165已解释Fair8新增27 D1首评但无新增SETUP，本阶段不再重复调公平队列、不改原D0/D1/D2。

本阶段固定之后才计算历史利润与尾部风险，禁止因为结果不好改交易规则。全部官方2026年2月历史一分钟来源沿用已受独立Codex验证的 **28份publisher artifact archive**（原445 symbol、28份ZIP+proof及issuer daily receipts），强制全档SHA/proof和完整身份核对。历史 **trade eligibility/PIT上市全人口、真实双向盘口/fees/真实成交未知**，仅可标`HISTORICAL_PRICE_PROXY_EXPOSED`。

## 预定义唯一主口径与补充口径

- 纳入原A/B `raw_alternative_events`中精确`event_type=SETUP_ACTIVE`的120个**原事件ID、币种、真实observed_ms**，不得根据最终涨幅先筛；事件id必须唯一。以原始真实分钟行，严格把SETUP时钟后的**至少+3分钟**作为入场价格代理：第一根时钟刚好落在`SETUP observed_ms + 180000`的合法1m `OPEN`，**不选历史low，不用SETUP发生那分钟的OPEN**。冻结24h作为主要收益/亏损口径，15m/60m/360m为预先确定的额外敏感性窗口（各自由相同入场后固定分钟间隔`OPEN`退出），结果不因胜率选择持仓期。
- 固定**每边10bps假定手续费、每边20bps假定滑点**，以`(exit_open/entry_open)*((1-.002)/(1+.002))*(1-.001)^2-1`计算净收益率；同时给每边100bps压力滑点，禁止称作真实账户tier/实盘收益。没有真实历史ask/bid L2、盘口资金深度、通知到达时间，所以进/退价仅是分钟OPEN**不可证明可成交**，不可把价代理升格BUY。
- 固定源质量拒绝：缺完整该根minute、入场/退出`quote <= 0`或`trades <= 0`、任一端`quote < 30 USDT`、**退出及前5根minute有零成交**则`CENSORED`，不是0盈利。零成交市价不代表可成交；任何未来数据**仅能作为退出/风险后验统计，不可用来改变入场候选的名单或下单规则**。每条原事件完整保留`source_error/censor_status`。
- 同一symbol再次SETUP若前一个被计入的事件尚未达到固定24h结束，标`SKIP_SAME_SYMBOL_24H_CAPITAL_OCCUPIED`；其他每条eligible按原observed UTC、事件ID稳定排序。**不以全市场资金约束自动选最赚钱的币**：输出单笔互不重叠假定30U作为**历史可比性情景**，并显式列出与其它符号同时交易占用程度，不把30U等于用户交易授权。若结论需要300U组合，应另以冻结现金规则重算，不可由单笔互不重叠收益乘起来当有限资金净值。
- 报告每个退出期限事件数、成功价代理数、赢/亏/持平、净收益分布中位/平均/排序尾部、盈利前5条贡献（**纯后验归因，不用来筛币**），同币重叠与source删失明细；保留全部120行完整事件结果。24小时单价代理可评价数必须按真实数据算，不预填、不得套用Stage30其它日期133/297的数据。
- 任何source或publisher proof字节不完整，自动fail-closed；不得从2026年10月T0的活跃币反推2026-02可交易上市身份。Stage30旧760 WATCH回测、Stage152旧305D1不与本120历史同分母做胜率混合。

## 目标业务决策和放行边界

回答“**有D1 SETUP之后，按不偷看未来的入场时间，24h后的价格代理收益是否仍大面积为负？与单纯WATCH的旧经济失败是否方向一致？**” 给出独立且可证伪的直接数据，不以盲目提高SETUP数量说成功。若出现强烈正收益也只可能是历史价格代理，仍因上市PIT、成交/通知、前瞻净正收益门禁未知而`G4 UNKNOWN/G6 NO_GO`。

本轮允许原PR#30单次离线GitHub Actions读取**既有**28官方封存ZIP（不依赖任何新在线报价，不创建schedule），输出全120条机器JSON、来源SHA、独立审计报告；新增代码必须经其他AI独立review才可记`G5`批准。无真实交易、资金、私钥、Mac/Frank、Gmail/自动交易、LaunchAgent。继续`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。
