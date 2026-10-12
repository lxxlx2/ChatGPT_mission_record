# Monster Stage100：先做旧数据模型，不等2026年10/11月采集 — 冻结历史日期递进回测

冻结于2026-10-13 Asia/Bangkok，原 Monster PR #30。**主要研发任务为历史妖币模型**；Stage97未来市场快照采集是完全独立的辅助研究，不构成Stage100训练/开发/CI/Review的前置条件。用户授权历史模型研究与修改，未授权真实自动交易、生产邮件或Monster生产部署。

## 1. 真实数据基线（已核验Git blob）

- Stage85真实官方 SHA 1m，完整305个原Stage79 D1信号时点的因果特征：`monster_stage85_all305_official_D1_asof_features.jsonl` blob `622299fec16400e189cb8fa668ecbc8bc31ec630`。
- Stage88真实官方SHA 1m，完全相同305个信号后延迟1m开盘、固定24h/72h退出真实历史毛价格代理：`monster_stage88_all305_D1_post_signal_24h72h_price_paths.jsonl` blob `86e96b726f677a15f5a7c8d740e3caca5c83e3fc`。
- 6个旧UTC06七日市场窗口依时间排序为2025-01-30、2025-06-02、2025-08-01、2025-10-02、2026-06-21、2026-07-28。每日不同币信号相关、USD-M混合Crypto/TradFi/映射未知；所有305逐条保留，不仅使用极端5个赢家。旧Stage79 G3 7.26条/天、最大52；原D1固定24h收益中位-2.80%，72h -6.35%。

## 2. 固定且实际可运行的旧数据模型研究试验

目标不再是给旧赢家量身设计阈值，而是产出一套**确实有规则、有逐日历史回放、可以与原D1比较、发现效果差就修改/弃用**的第一版研究模型。此版是`D1_SETUP → PRIORITY_RESEARCH`**候选排序**，原WATCH、原D1及所有当时已出现信号仍保留，不冒充真实BUY或G3已通过。

- 训练目标事先固定：`D1后延迟一分钟K线open → 24h固定退出K线close` 毛价格方向 `return_24h > 0`；不是旧2x锚点、交易净利润或赢家 HIGH。保留24h收益、72h收益、24h MAE/最大close回撤及原七日2×（评价时才查询）作为风险/右尾副指标。
- 特征只取D1当时可看到的有限信息，最多7项：`ret60_pct`、`log1p(quote15_USDT)`、`log1p(trades15)`、`log1p(normalized_quote15_prev45)`、`ret_from_D0_pct`、`log1p(delay_minutes)`、`is_REIGNITION`（0/1）。不使用任何D1之后的数据预测，不用日期作为输入。
- 采用带L2正则的确定性logistic二分类（纯Python，无调参黑箱）；所有均值标准差**只从训练日期**学得，L2、学习率、迭代数在读取研究结果之前冻结，不因成绩差改本轮参数。零方差置为1。日志记录每一折train日期、train行数、测试日期、分布和特征分数，保存便于复现的模型系数。任何NaN/缺档/键错直接FAIL。
- 严格历史按日期前推四折：训练Jan+Jun 2025测试Aug 2025；训练前三日测试Oct 2025；训练前四日测试Jun 2026；训练前五日测试Jul 2026。各测试日期样本进入训练**只能在下一折**。这是旧数据内的模拟前推，不是此前从未曝光的独立OOS，始终标`EXPOSED_CHRONOLOGICAL_DIAGNOSTIC_ONLY`。
- 在每折中，用训练日期的模型分数决定唯一**训练期**阈值：只让训练日期平均每UTC06日最多5个`PRIORITY`（取训练分数排序中位于合计 `5 × 已完成训练7日窗口数`名额的阈值；严格大于/等于、相同score按symbol稳定处理，明确平分数不得悄悄强行topK测试币）。测试日期原样应用训练阈值；**不得事后限制测试某天最多12条、强行挑topN或删去WATCH**。通过阈值只减少`PRIORITY`标签，不隐藏其它SETUP；是否值得发真正提示取决于独立评估。
- 预先固定对照：原D1全305行；在这四折测试窗口比较每折`PRIORITY`数量、均值/日、峰值/UTC06日、固定24h胜率/中位、72h毛中位、24h固定退出≤-20%的严重跌幅比例、原`early5_gt2_evaluation_only`正例保留数及后72h≥100%右尾保存率。训练期24h/72h结果不可混进测试统计，输出被过滤掉但未来涨的逐币漏报列表。
- 预设研究候选接受门槛：对测试四窗`PRIORITY`非空，固定24h毛中位 >0，整体平均≤5/日、单日峰值≤12；原D1提前五分钟2×机会在研究候选中保留≥80%（如正例太少标UNDERPOWERED而不冒充有效），并尽量不牺牲72h≥100%极端样本。考虑真实手续费/滑点和盘口未知，**不得宣称真实净盈利、G3生产策略通过或自动执行**。失败则报告失败原因，再换一种有明确经济逻辑的策略重新冻结开发，而不是暗改刚才这版阈值让结果看起来好看。

## 3. 工程顺序与独立审查

此文件先Git冻结 → 用现有官方数据实现同一历史样本读取/因果建模代码 → 运行真实GitHub CI → 保存全部系数/单币历史研究评分及坏例至原PR30 → 进入 Claude **对话**的真实独立AI review（用户不用本地CLI）→ 根据审查修复、继续历史模型迭代。不要因未来10/14、10/28、11/11的市场数据没有就停工；那三次采集仅为另一个辅助研究通道。

状态：`STAGE100_MODEL_EXPOSED_HISTORY_ONLY`; `D0_ORIGINAL_UNCHANGED`; `D1_ORIGINAL_UNCHANGED`; `OOS_NOT_REQUIRED_FOR_HISTORICAL_DEVELOPMENT`; `REAL_EXECUTABLE_NET_PNL=UNKNOWN`; `DEPLOYMENT_NO_GO`; `GMAIL_OFF`; `AUTOTRADE_NO_GO`; `FRANK_UNCHANGED`。
