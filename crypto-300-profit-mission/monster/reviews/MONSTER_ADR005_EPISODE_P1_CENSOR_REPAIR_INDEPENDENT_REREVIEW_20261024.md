# Monster ADR-005：独立 episode 源删失 P1 — 审核结果、修复证据与下一次复审

**旧审核固定SHA**：`da4862c604a254008ba488f7948124d9ecb6e77f`，**结论永久保留 `REQUEST_CHANGES`**。
**P1 修复及新云端测试固定SHA**：`3d79beaa30ef859fd914823837d50df99f501e02`。
**PR**：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
**状态**：`P1_PATCH_CI_PASS / NEW_SHA_INDEPENDENT_REREVIEW_NOT_DONE / NO_MERGE_NO_DEPLOY`。

## 用户转交的独立真实审核结论

- 审核主体：用户提供的 **Codex 主代理**独立 detached/read-only 工作区、Python **3.14.7**，底层模型具体型号 `UNVERIFIED`。用户Mac真实执行新episode 15项：**15 PASS、0 FAIL/ERROR/SKIP**；未操作生产、真实市场数据或Git仓库提交。
- 真正新增的 **P1 来源负例污染**：`local-agent/scripts/monster_v4_d1_rbtc15_episode_research.py` 在截止点收到有效 `RESEARCH_NO_SETUP_YET`，将全episode直接标 `NO_SETUP`，却没有查该episode此前是否有 `source_censored_count>0` 的缺失时刻。越过deadline的另一路终结已会保留 `SOURCE_UNSCORED`，造成两条路径不一致。
- 审核方真实复现：原WATCH `first_seen_ms=3240000`、deadline `4140000`；`3600000` BTC缺档返回 `SOURCE_CENSORED`；`4140000` 最新已闭合5m有效但不通过，旧版终态错误为`NO_SETUP`、`source_censored_count=1`。这不是模型收益争议，而是会导致 G2/G3 评估使用污染负例的真实 P1。
- 其他边界：公开 `event_key()` SHA只能核查字段结构/一致性，**不能证明某WATCH真的存在于原Core event ledger**；完整真实源接线必须通过原只读SQLite的events表及对应source出处对账。FIFO每次最多8个并非pending总容量8，状态机集成和历史PIT仍未知。

## 已完成的最小代码修复

1. [`dee1a3170bc456270fbead41f98bc8474cba4b1f`](https://github.com/lxxlx2/ChatGPT_mission_record/commit/dee1a3170bc456270fbead41f98bc8474cba4b1f) 修改原函数单一终结分支：若本轮实际正面判定则`RESEARCH_SETUP`；若截止时负面且`source_censored_count>0`则`SOURCE_UNSCORED`；只有没有记录过来源删失才可在截止时终结`NO_SETUP`；截止之前继续`PENDING`。**保守缺档记录一直保留**，除非未来独立设计逐缺档时刻的合法回填机制；不得仅凭后续一次有效负值解除之前未知时段。
2. [`3d79beaa30ef859fd914823837d50df99f501e02`](https://github.com/lxxlx2/ChatGPT_mission_record/commit/3d79beaa30ef859fd914823837d50df99f501e02) 新增三个真实SQLite回归：（a）早期BTC缺档、deadline有效且下跌→`SOURCE_UNSCORED`，重启仍一致；（b）无删失deadline有效负结果→`NO_SETUP`；（c）早期BTC缺档、deadline有效正结果→`RESEARCH_SETUP`，首次成功锁定；原有15项保持。
3. **远端真实云端执行**：[GitHub Actions #40105768989](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40105768989)，固定commit `3d79beaa30ef859fd914823837d50df99f501e02`，Job `120907019330`，`completed / SUCCESS`，12组`13+5+6+11+19+12+12+14+18+18+9+31=168/168 PASS`，新episode专项 `18/18 PASS`（本轮3例均在日志中为`ok`）。仅离线合成数据，不读取真实511源，不在用户Mac启动任何操作。

## 固定新SHA的独立复审任务（可转发给Codex / Claude）

请独立只读复审仓库 `lxxlx2/ChatGPT_mission_record` PR #30 的**固定提交 `3d79beaa30ef859fd914823837d50df99f501e02`**；不要改用后续文档HEAD。上一轮固定 `da4862c604a254008ba488f7948124d9ecb6e77f` 的结论是 `REQUEST_CHANGES`，其唯一P1是“早期BTC缺档 → 截止点有效负结果 → 错误NO_SETUP”。

按 SHA 严格比对两次修复的完整diff，检查 `crypto-300-profit-mission/local-agent/scripts/monster_v4_d1_rbtc15_episode_research.py` 及 `local-agent/tests/test_monster_v4_d1_rbtc15_episode_research.py`。优先独立构造上述 P1 的实际临时SQLite再现，检查早期缺档后终结`SOURCE_UNSCORED`、重启后状态不变，以及无缺档负例仍`NO_SETUP`、缺档后成功仍`RESEARCH_SETUP`。检查两个终结路径（`tick_ms>deadline` 和 `tick_ms==deadline`）的一致性，禁止靠后续有效数据清零历史删失；检查独立research表不会写入原事件库。

请实际运行：

```zsh
PYTHONPATH=crypto-300-profit-mission/local-agent:crypto-300-profit-mission/local-agent/scripts python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p 'test_monster_v4_d1_rbtc15_episode_research.py' -v
```

提供 `APPROVE / REQUEST_CHANGES / BLOCKED`、精确SHA、审核者模型及环境、真实运行结果、P0/P1/P2定位和步骤，明确旧P1是否`CLOSED`。**只允许批准P1终结分类修复**，不能因此宣称真实原事件身份来源、511币全市场时钟重放、G2/G3、G4盈利、G5整体或G6上线通过。不得 merge / deploy / trade / Gmail / automations / Mac持续部署。

## 未解决的正式验收

- P1复审：`PENDING_INDEPENDENT_AUDIT`，不自动采用旧固定SHA的APPROVE。
- Episode: 真实原 WATCH 来源需从原SQLite读取并验证（哈希算法不是完整的真实性证明），原原Core与新研究账本独立；缺少同时间线的4,088或4,599份官方Minute replay和Fair8 comparison。即使P1修复全部通过，这些仍为未完成。
- G0=`PARTIAL`、G1=`NOT_SCORABLE`、新G2=`UNKNOWN`、新G3=`UNKNOWN`、G4=`UNKNOWN`、G5本模块`REQUEST_CHANGES_FIX_PENDING_REREVIEW`、G6=`NO_GO`。继续 `NO_MERGE/NO_DEPLOY/NO_MAC/NO_SCHEDULE/NO_GMAIL/NO_TRADES`。
