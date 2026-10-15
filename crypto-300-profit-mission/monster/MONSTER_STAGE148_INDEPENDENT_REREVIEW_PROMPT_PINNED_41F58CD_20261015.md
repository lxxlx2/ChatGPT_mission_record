# Monster Stage148 — immediately copyable independent other-AI re-review prompt

请直接复制下方完整内容给独立 AI Reviewer；此文档为**复审请求**，不是复审APPROVE。

---

你继续担任 Mission Monster（妖币研究）模块的独立审查员。本轮只审 Stage148 对 Stage147 两项来源校验缺陷的真实代码修复。**必须独立 checkout 固定 SHA、运行原始保存的真实525个合约数据及被篡改样本，不允许仅阅读开发者报告。**

GitHub 仓库：https://github.com/lxxlx2/ChatGPT_mission_record

原 Draft PR #30：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30

**本轮固定待审代码SHA：`41f58cd3a1bde8d9b01cffc74f04ae36f26685aa`**

上一轮真实独立 Codex **REQUEST_CHANGES** 固定SHA：`e6ec373d00e368d249758d6887a4a5144afd7ae9`。比较基线为该SHA。上一 Stage145 独立 Codex **APPROVE** 固定 SHA：`51f2eca3646db72158c42e7cfca5322c76e58c83`，该批准只适用于旧D0/D1来源模型，不自动批准此次新增Stage147/148代码。PR的浮动HEAD可能在上方固定SHA之后由于后续Markdown报告改变，必须以此固定源码版本为审核依据。

先阅读：
- `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`
- `crypto-300-profit-mission/monster/MONSTER_STAGE147_CODEX_REQUEST_CHANGES_E6EC_SRC_REVIEW_INTAKE_20261015.md`（上一审查者真实的P1/P2）
- `crypto-300-profit-mission/monster/MONSTER_STAGE148_FROZEN_CODEX_P1_RAW_STAGE133_ROSTER_AND_P2_WRAPPER_SOURCE_CLOCK_REPAIR_20261015.md`（本次在代码修改前冻结的要求）
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage147_saved_real_bbo_execution_readiness.py`
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage147_saved_real_bbo_execution_readiness.py`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage139_official_t0_and_saved_contractinfo_evidence.py`
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage133_manual_actual_t0_forward_proof.py` 和 `monster_v4_stage134_t0_population_readiness_bridge.py`
- `.github/workflows/monster-stage147-real525-bbo-G4-offline.yml`
- Stage140以前获授权、现在已保存在Git的原始来源目录：`crypto-300-profit-mission/monster/evidence/monster_stage140_user_authorized_real_www_mirror_20261015/t0_2026-10-14T175247096Z/`

**P1必须独立验证：原始525个合约名单是否真的由原始正文重建，而非派生文件的字符串宣称。**

旧Stage147只要求派生Stage139文件有525行、名称无重复、声明一个SHA。独立Codex先前在临时复制的原始证据目录中把派生 `stage139_original_T0_asof_contract_metadata.json` 的 INDEX `ALLUSDT` 改成 COIN `AAPLUSDT`，保持525行、类别计数、声称原始SHA不变。因为AAPLUSDT碰巧也在三份保存行情中，这种伪造通过了旧审核，并把INDEX样本删除、用新样本取代。

Stage148现在应读取原本2.5MB `stage133_original_three_HTTP_T0.json`，**复用** Stage139 `inspect(t0_packet)`（已有 Stage133/134原始3HTTP时钟、端点、全原始交换信息 SHA 和原始总体校验），并将 rebuilt 的完整 `initial_original_instrument_rows` 与单独已保存的派生Stage139逐行全字段对比，再核对原始source packet SHA、原exchangeInfo SHA和Stage140清单原始窗口时间。请自己构造并测试：
1. 只把派生 `ALLUSDT` 改成 `AAPLUSDT`（三个行情正文、525计数不动），**必须拒绝**；
2. 只改其中一行 `asof_instrument_scope` 类别、status、contractType、quoteAsset、onboard字段的任意一个，**必须拒绝**；
3. 原始 `stage133_original_three_HTTP_T0.json` 中 `raw_http_records.official_exchange_info.raw` 被改成 `{}` 但SHA未改，**必须拒绝**；
4. 删除原始Stage133源文件，不能继续声称验证了525；
5. 原始真实快照不改动时仍必须 **525/525** 完整， **523 COIN-typed issuer UNVERIFIED / 2 INDEX**；必须保持 issuer和source origin NOT_PROVEN，不得对源自行数字签名或者用派生值代替原始验证。

**P2必须独立验证：三份行情HTTP包装的endpoint和response UTC与原始清单严格绑定。**

旧Stage147只验证raw body的SHA，对包装URL仅核对主机前缀，wrapper response_end_ms 只检为正整数顺序。原审查者成功只把BBO wrapper `response_end_ms` **1792000368089** 增加一整天（+86400000），使事件年龄中位数从1103ms漂移为86401103ms，审核却通过；另把 BBO URL 改成同一主机 `/fapi/v1/premiumIndex`，也被接受。

Stage148应要求：
- BBO URL exactly `https://www.binance.com/fapi/v1/ticker/bookTicker`；
- 24h ticker exactly `https://www.binance.com/fapi/v1/ticker/24hr`；
- mark exactly `https://www.binance.com/fapi/v1/premiumIndex`；
- 每一逻辑来源 wrapper的 `response_end_ms` 与Stage140 manifest `optional_all_market_marketdata_receipts[...].response_end_utc` 精确匹配毫秒UTC；包装 `request_start_ms` 是正整数且不得晚于响应；
- `raw_sha256` 仍必须重新哈希原始 UTF8正文，同时对照包装和原始清单，并核对原始行数及去重symbol。

请实际复现：单独修改 BBO response_end_ms +86400000、不碰raw SHA；BBO换 premiumIndex URL；24h ticker换 bookTicker URL；mark换24h ticker URL；都应拒绝。原始包保持通过。判断是否还有任一关键输入能被改掉而仍产生“原始来源已验证”的报告，且影响 G0/G4意义。

**实际 CI，在相同不可变代码 SHA 上独立核对：**

https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38702462928

固定 HEAD `41f58cd3a1bde8d9b01cffc74f04ae36f26685aa`，Ubuntu (job 116313706571) 与 macOS (job 116313706983) **各9/9 PASS**，运行原保存525 HTTP与新增篡改测试；实际GitHub日志已查看有 `Ran 9 tests`, `OK`, `STAGE147_REAL_SAVED525_NO_DEFAULT_NOTIONAL_NO_FAKE_G4=PASS`, `STAGE147_EXPLICIT_SCENARIO_ONLY_NEVER_EXECUTION=PASS`, `STAGE147_NO_LIVE_GET_NO_SCHEDULE_NO_GMAIL_NO_TRADE_NO_FRANK_NO_DEPLOY=PASS`。中间修复阶段旧synthetic测试未附新增必需的时间清单而一度CI失败，在最终SHA只补synthetic证据，没有放松真实验收条件。

可复现命令，在克隆并检出**固定 SHA**的 `crypto-300-profit-mission/local-agent/scripts` 目录：

```bash
python3 -B -m unittest -v test_monster_v4_stage147_saved_real_bbo_execution_readiness
python3 -B monster_v4_stage147_saved_real_bbo_execution_readiness.py --out /tmp/monster-stage148-source-review.json
```

**既有研究/交易门禁：** Stage147仍是单个真实但 **WWW FAPI镜像源独立等价性 UNVERIFIED** 的2026-10-14 17:52 UTC历史初始市场快照，525是交易所挂载的合约数，不是525笔成交或525个可执行妖币。Stage120原合约交易规则，Stage90原D2执行证据引擎，Stage137/138原冻结D0/D1没有改；没有真实完整7日上市事件普查、3个独立真实前瞻窗口、盘口多档深度、市场准入PIT发行者确认、fee/funding与完整日后退出证据。顶档 `bidPrice*bidQty` 只叫代理值，explicit scenario 100只为测试，实际用户金额未知。绝不可凭一个历史BBO给出 BUY/G4 PASS/可实现净收益。

请按以下结构返回：独立审核者身份和确切版本(无法核验标 `UNVERIFIED`)、实际检出固定SHA、本机Python/系统和真正运行的命令、`APPROVE / REQUEST_CHANGES / BLOCKED`、上一轮P1/P2是否已被实际修复并附最小源码输入复现、任何新P0/P1/P2（文件位置/影响和最小修复，不为了凑边界而滥报）、冻结原D0/D1/Stage120/Stage90和G0-G6是否未被擅改。**即使本次代码APPROVE也不代表模型通过盈利验收，仍保持PR #30 Draft、NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE，Frank和手动采集节奏不变。**
