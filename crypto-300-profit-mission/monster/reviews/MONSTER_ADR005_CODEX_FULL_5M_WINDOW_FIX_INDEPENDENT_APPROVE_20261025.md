# Monster ADR-005：Codex 对完整5m评估覆盖修复的独立批准（2026-10-25）

状态：**INDEPENDENT_REVIEW_APPROVE_SCOPE_LIMITED**。本文件记录用户带回的真实其他AI独立审查意见，并非GitHub上的Codex身份评论，亦非整体Monster产品/盈利/部署批准。

## 1. 固定审核来源与审查边界

- 审核主体：**Codex 主代理**，底层具体模型型号 `UNVERIFIED`，未委托其他代理。真实审核执行环境是用户Mac、Python **3.14.7**、独立detached worktree，审查工作区全程只读。
- 固定审核SHA：**`d743acb6746cde869eb78d321cea98dc94e7b860`**。由先前被驳回的 `787219809b92fe2c60538f95476a7277ffa07e78` 增量审查；**文档提交SHA `8a2f86c1fe1dc1477a9a089f19c74d9192acc7a6` 不是替代审核目标**，也不把移动PR HEAD当作固定审核版本。
- 审查结论原文：**`APPROVE @ d743acb6746cde869eb78d321cea98dc94e7b860`，只针对`monster_v4_d1_rbtc15_episode_research.py`的完整5m覆盖、漏评终态，以及旧53条语义修正比较器；本轮未发现新增可操作 P0/P1/P2。**
- 实际审核范围包括固定Git源码diff、专门保留的历史不变中间K线反例、3m WATCH相对5m边界五种余数、SQLite重启/Source优先/limit1容量、原GitHub Actions回执和两次真实回放Artifact的SQLite只读逐行核对。本次审核不是对市场实时触发、账户成交、全部原始来源或完整产品的批准。

## 2. 真实复审核查结果

| 独立审核实际项 | 结果及限制 |
|---|---|
| 14组真实本机回归（Mac Python3.14.7） | **211/211 PASS**，0失败组 |
| real69原生专项回归 | **8/8 PASS**，合计 **219 PASS** |
| 历史固定中间漏评反例（WATCH `3240000`，`3420000`负评，漏掉`3600000`会触发的机会，deadline `4140000`负评） | 新代码终态 **LATE_UNSCORED**，`reviewed_closed5_count=2`，`missed_closed5_count=1`，无研究SETUP，SQLite重启仍保留；P1 **CLOSED** |
| 有效5m历史连续覆盖 | `NO_SETUP`必须同时要求首根=WATCH后首次合法5m open、末根=deadline前最后允许5m open、已评估数=应有独立bar数、漏评0及来源删失0；SAME_BAR/重试不重复计数，SOURCE优先 |
| 原始GitHub #40191821423 | completed SUCCESS，211项，实际绑定 `0acf484d80f6c92006bb059bad45aed7899cb932`；与固定审核SHA只有一个单次源码回放workflow的增量 |
| GitHub #40191914954 | completed SUCCESS，实际绑定固定审核SHA `d743acb...`，新Artifact `12597793739` |
| 与旧Artifact `12596924379` 的数据库独立对账 | 69个WATCH ID/状态/时间、47行`research_setup`全部字段和payload一致，18条NO_SETUP都已评价3根独立5m且无漏评；两边SQLite integrity_check=ok；V1/V2原始SQLite字节**不同** |
| 新Artifact固定SHA256 | `real69.sqlite=66afb34b2d486ae5ed5014bef598d4a94fb8ea8f0ddc9f375a23a680acbd82d7`；`real69.json=2f5e27d37c2b7ae333079b08155e392d78413212571bc681d149b4e91a1cf84c` |

以上数字作为**用户实际提供的Codex审查记录**入档；本研究此前GitHub Actions #40191821423/#40191914954自身回执亦已由本项目读取确认，不擅自宣称用户Mac被本助手远程操作。

## 3. 分关口结论，禁止扩大解读

- **G0=PARTIAL**：旧T0 511 ×9日官方历史归档已取得4599组原源，但审查者没有独立读取全部4599组原发行方ZIP字节。历史实时`available_at`、动态Listing/Eligibility PIT尚未核实，独立全量源验证为`BLOCKED`。
- **G1=NOT_SCORABLE**：已曝光十月数据没有可用预注册样本外2×获胜事件量/严格首次提前通知证据；冻结未来三个窗口 `2026-11-02..09`、`2026-11-16..23`、`2026-12-01..08` 不得改动或提前宣布完成。
- **G2=UNKNOWN**：本次已修复漏评的工程归因，但未证明未来2×事件早于5m的原D0 WATCH被新D1保留≥80%。
- **G3=EXPOSED_NOT_PASSED**：47条研究SETUP/7日=**6.71/日**，在排除已确认证券和Chiliz单独分层后，40条普通Crypto正面身份类型SETUP/7日=**5.71/日**，都高于冻结≤5/日；且动态历史交易资格仍UNKNOWN，不能通过调整旧阈值改写结论。
- **G4=UNKNOWN**：缺>=30完整真实bid/ask买卖两侧价、滑点、手续费、金额/资格和退出证据。无用户指定名义额不得默设交易金额；不能从事后分钟OHLC推导可执行利润。
- **G5=APPROVE_FOR_THIS_V2_PATCH_ONLY**：`d743acb...` 的独立漏评修复复核**已完成通过**；这不等于Monster全场所策略/数据/通知/执行的完整稳健性审核通过。
- **G6=NO_GO**：仍不可合并、部署Monster、创建/启用定时任务、开始真实邮件或交易。

## 4. 真正下一步（不是继续证明这个已关闭的P1）

按照 `monster/MONSTER_MODULE_DEVELOPMENT_RULES.md` 与ADR-004交付优先级，应回到**Spot/USD-M 的 D0→D1→D2及用户机会通知产品主线**。优先评估**G1/G2/G3/G4**尚未达成的核心收益/漏报和可成交性，而非重复测试已经独立批准的旧代码或将BSC边缘研究冒充主要进度。保持原G3历史曝光判败、保留原ADR005冻结设计和未来样本外窗口；后续实际只读公开数据采集只能手动或一次性授权触发，绝无`schedule`。

边界：**NO_MERGE / NO_DEPLOY / NO_MAC / NO_NEW_RPC / NO_AUTOMATIONS / NO_GMAIL / NO_TRADES**；不接触Frank生产。
