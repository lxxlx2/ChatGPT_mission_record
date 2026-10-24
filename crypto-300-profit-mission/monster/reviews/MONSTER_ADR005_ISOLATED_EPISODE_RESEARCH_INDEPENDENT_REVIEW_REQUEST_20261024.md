# Monster ADR-005：独立 SQLite episode 原型代码独立复审请求（不同于旧P2）

**审核固定源码 SHA**：`da4862c604a254008ba488f7948124d9ecb6e77f`
**PR**：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
**分支**：`research/monster-v4-local-discovery-20261010`
**状态**：`REVIEW_REQUESTED_NOT_APPROVED` / `RESEARCH_SYNTHETIC_ONLY` / `NO_MERGE_NO_DEPLOY`。

本审核包提交后HEAD会继续前进，**本次审核固定的源码就是上述SHA，不得自动换成后续HEAD**。上一轮 `APPROVE@9b049dd` 只关闭 preflight P2，绝不覆盖本轮新episode原型。

## 用户可直接给 Codex/Claude 的完整独立审核提示词

请作为独立只读第二AI审核 **Monster PR #30固定Git提交 `da4862c604a254008ba488f7948124d9ecb6e77f`**。如无法访问仓库/运行环境，请标 `BLOCKED`，不要猜测审核成功。不得merge、部署、发信、设定时任务、操作交易或改Frank。

1. 首先读 `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`、`MONSTER_STAGE77_CORE_MODEL_ACCEPTANCE_AND_BOUNDARY_FREEZE_20261013.md`、`monster/adr/ADR-004-monster-product-mainline-scope-and-delivery-order-20261023.md`、`monster/adr/ADR-005-spot-d1-btc-relative-confirmation-preregister-20261024.md`，验证未改变冻结阈值/未来未曝光时间窗。
2. 本次新代码为`crypto-300-profit-mission/local-agent/scripts/monster_v4_d1_rbtc15_episode_research.py`，测试`crypto-300-profit-mission/local-agent/tests/test_monster_v4_d1_rbtc15_episode_research.py`。审查其对原`monster_v4_shadow.py`的`WATCH_EARLY`真实SHA身份认证、独立SQLite `research_setup`不可与原`SETUP_ACTIVE`混淆、一个symbol至多1 pending、15min deadline、每3分钟最多8 FIFO槽、首次成功后永久锁定、持久化恢复重启防双发、BTC缺根/币缺根`SOURCE_UNSCORED`而非NO_SETUP、同一根闭合K线重复核查、异常时不会伪造负例，以及SQLite日志/事务原子性和意外进程停止。
3. 与原`local-agent/scripts/monster_v4_shadow.py`、`monster_v4_spot511_paired_sqlite.py`比较：原D1一旦SETUP便立即EVALUATED；本独立队列不能将原D1已结束episode直接当成新版队列持续性。**本轮仅独立队列原型，尚未把原真实WATCH时间流和Binance闭合5m源做全局对照；还不能叫full integration**。务必检查只凭`event_key()`哈希是否足以绑定真实来源、短时重放是否会重复WATCH、重复poll导致SQL数据竞争、错位/跨源错误是否被误删失、SOURCE_CENSORED在deadline的状态以及无真实BSTOCK身份过滤的限制。
4. 本轮云端CI参考：GitHub Actions `https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40104961821`，12组`13+5+6+11+19+12+12+14+18+15+9+31=165/165 PASS`（原有150加新增15项），Python 3.11。不能只引用此结果：独立用 `PYTHONPATH=crypto-300-profit-mission/local-agent:crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p 'test_monster_v4_d1_rbtc15_episode_research.py' -v` 实跑，检查新文件SHA。历史审核 `APPROVE@9b049dd` 只适用于旧P2路径，不代表本模块已review。
5. G1需要>=20个独立2×且3个独立窗口、90%/85%提前；G2>=80%早期2× D1覆盖且保留首次D0真实发现；G3<=5 SETUP/日/峰值<=12，不能将G4账户Monitoring Tag抵扣G3；G4需真实买卖bid/ask和金额/手续费滑点退出、至少30个独立完整交易观察；G5须真实外部审查+全源同核心集成；G6仍NO_GO。
6. 尚缺真实4,088/4,599来源 **新队列** 全源并排回放；2026-10-24 UTC完整511份未发布可取且完成校验前不能冒充4599/4599；ADR-005三个未来窗口（2026-11-02..09, 11-16..23, 12-01..08 UTC）不能提前读或从10月样本冒充OOS。全部研究不授权BUY、真实邮件/生产运行/调度。

**输出格式**：`APPROVE | REQUEST_CHANGES | BLOCKED`、准确审核SHA和reviewer模型（若未知标UNKNOWN）、真实执行测试/环境、P0/P1/P2及行号和复现、原WATCH/D1/源缺失下的episode因果性、影响G0–G6、后续真实数据集成缺口、`NO_MERGE/NO_DEPLOY/NO_TRADES/NO_GMAIL/NO_AUTOMATIONS`。不批准真实策略表现或生产。 
