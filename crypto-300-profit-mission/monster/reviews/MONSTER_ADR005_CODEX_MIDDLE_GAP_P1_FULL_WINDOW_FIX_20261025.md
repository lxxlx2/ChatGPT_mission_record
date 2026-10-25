# Monster ADR-005：Codex 第三次 REQUEST_CHANGES / 中间K线漏评完整性修复（2026-10-25）

**门禁结论：CODE_FIXED_INTERNAL_EVIDENCE_COMPLETE / G5_EXTERNAL_RE_REVIEW_PENDING / G6_NO_GO。禁止MERGE、DEPLOY、Mac/Frank操作、Gmail、定时自动化、交易和额外RPC。**

## 1. 被审版本与独立P1反例

用户转述的独立审查主体是**Codex主代理**，底层具体模型型号**UNVERIFIED**，在用户Mac、Python3.14.7、隔离detached worktree下真正审查固定 `787219809b92fe2c60538f95476a7277ffa07e78`，核销207项原回归+real69 8项、Actions #40190452211/#40190516624，返回 **REQUEST_CHANGES**。该报告来自用户提供的原文；不可冒充其他AI对本轮新SHA已给APPROVE。

它正确证明“最后K线被评估过”不等于“此前所有独立5m K线都被评估过”：

- WATCH `3240000`，在`3420000`评估阴性；
- 在`3600000`未得到队列服务，但**同一不变的币/BTC 5m历史**在该时点已能满足`RESEARCH_SETUP`；
- deadline `4140000`最后一次5m K线负评，即使真实最后K线open `3600000`已评估，也不能据此认证中间无信号；
- 原研究队列会结成`NO_SETUP`，且重开SQLite后保持，错误低估漏报/高估确认负例；本次必须判为`LATE_UNSCORED`，**不能事后补发交易信号**。

## 2. 不更改任何策略阈值的代码修复

实际提交及待审固定源码SHA：**`d743acb6746cde869eb78d321cea98dc94e7b860`**（包含本次唯一一次性验收workflow，无schedule；后面文档提交不改变此源码）。

- `local-agent/scripts/monster_v4_d1_rbtc15_episode_research.py`：独立研究SQLite ledger schema由V1提升至**V2**，旧V1账本仍为只读历史证据，新的V2只能另建、禁止覆盖旧文件。新增持久化字段`first_reviewed_open_ms`、`reviewed_closed5_count`、`missed_closed5_count`，已有`last_reviewed_open_ms`保留。
- 严格定义原WATCH后首个合法5m open为`floor(WATCH/300000)*300000`；deadline前最后可被评价的5m open为`floor(deadline/300000)*300000-300000`。在3m服务tick的独立“新bar”成功评分中，若新open严格晚于`上次已评估5m open+300000`（首次为首个合法open），持久化中间遗漏数。重试/SAME_BAR不增加已评估的独立bar数；最近一个有效负评**不能清理此前遗漏证据**。
- 只有首尾时间都符合、`reviewed_closed5_count == (last-first)//300000+1`，且`missed_closed5_count==0`、`source_censored_count==0`时，`NO_SETUP`是有根据的“完整无触发”。已报来源删失优先`SOURCE_UNSCORED`；无来源删失却缺任何一根应评估5m（早、中、晚）即`LATE_UNSCORED`。无论中途漏评与否，**deadline内真正观察到正信号**仍可以正常记录`RESEARCH_SETUP`；deadline外永不补发。
- `local-agent/scripts/monster_v4_adr005_real53_original_sqlite_replay.py`：以前53条已曝光参考的`LATE→NO_SETUP`认可条件与V2完整性一致，不能仅凭首尾时间或无缺源通过；任何其他状态/SETUP时间改动继续fail closed。

## 3. 冻结固定历史+新增补充测试

- `local-agent/tests/test_monster_v4_d1_rbtc15_episode_research.py`：新增完全静态、与调用顺序无关的币/BTC 5m OHLC及quote历史，实际验证`3420000`评估负面、漏掉`3600000`本可RESEARCH_SETUP、`4140000`最后负面 → `LATE_UNSCORED`；复核`reviewed_closed5_count=2`、`missed_closed5_count=1`，重开SQLite终态不变。还用真实`limit=1`/老事件优先场景模拟容量冲突让中间bar漏评，及完整三根独立5m负评确实可`NO_SETUP`。
- `local-agent/tests/test_monster_v4_adr005_real53_original_sqlite_replay.py`：端点都被阅读但中间缺一个bar，参照比较必须`DIFFERENCE_FAIL_CLOSED`。
- 云端原14组回归 [Actions #40191821423](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40191821423) `SUCCESS`，实际日志分别 `13/6/7/11/19/12/12/14/18/28/14/17/9/31` **211/211 PASS**，Python3.11。中间开发提交曾失败，唯最后真实成功定责，不宣称每次旧SHA都通过。
- 真实官方分钟回放 [Actions #40191914954](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40191914954) `SUCCESS`，复用**42个已留存官方发行方来源Shard**，Stage166验收精确69个符号日需要及原3,360轮D0 WATCH。实际SQLite新Artifact **`12597793739`**（`real69.sqlite`及`real69.json`）；冻结旧对照Artifact `12596924379`。
- 助手另从GitHub独立下载两包并在容器原生SQLite read-only逐行检查：69个WATCH的`status、research_event_id、research_observed_ms`均与旧版一致；两版**47条research_setup数据库完整行（含payload）完全一致**；新数据仍 `47 RESEARCH_SETUP / 18 NO_SETUP / 4 SOURCE_UNSCORED / 0 LATE_UNSCORED`。新V2 `NO_SETUP`的**18/18项全部拥有`reviewed_closed5_count=3`、`missed_closed5_count=0`**；SQLite PRAGMA integrity_check返回ok。老V1与新V2**字节当然不同，绝不误称SQLite/JSON逐字节不变**。新JSON SHA256 `2f5e27d37c2b7ae333079b08155e392d78413212571bc681d149b4e91a1cf84c`，新SQLite SHA256 `66afb34b2d486ae5ed5014bef598d4a94fb8ea8f0ddc9f375a23a680acbd82d7`。

## 4. 限定的下次独立审查要求

其他AI下一轮必须**固定** `d743acb6746cde869eb78d321cea98dc94e7b860` 隔离只读审查，核对`78721980→d743acb`确切源码/测试diff，而非用前次Codex拒绝版再次测试；重点重演新的固定静态中间正信号被漏掉案例、实际limit1容量冲突、SQL重启、首次合法bar/3m与5m对齐/截止边界、SOURCE优先、不补发超期SETUP、末bar误判修复、未覆盖中间bar不能在比较器被认可。读取`12597793739`，至少独立比对69原ID与47 SETUP payload及18条完整三根负评，不能仅相信本文件或CI通过。

**无法证实部分**：十月样本早已曝光、不是未来预注册OOS；发行方事后minute档案不是当时可收取PIT快照；T0的511不是动态全市场上新；独立审查未读取全部4599组原始发行方ZIP；只有真实期货/Spot成交BidAsk、滑点/税费才能证明G4的可交易费用后净利。已曝光研究 G3原47/7=6.71、官方类型证据正面普通Crypto40/7=5.71均超过5的上限。继续明确 `G0 PARTIAL / G1 NOT_SCORABLE / G2 UNKNOWN / G3 EXPOSED_NOT_PASSED / G4 UNKNOWN / G5 INDEPENDENT_POST_FIX_REVIEW_PENDING / G6 NO_GO`。

**行动安全界限：** NO_MERGE / NO_DEPLOY / NO_MAC / NO_AUTOMATIONS / NO_GMAIL / NO_TRADES / NO_NEW_RPC；不会修改Frank现有监控。
