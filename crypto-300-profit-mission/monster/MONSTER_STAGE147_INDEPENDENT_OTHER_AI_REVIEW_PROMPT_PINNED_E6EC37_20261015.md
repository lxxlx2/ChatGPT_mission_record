# Monster Stage147 — copyable independent AI code review request on pinned SHA

直接复制以下内容到 Claude / 其他独立 AI 对话。审核请求已经准备，**不代表获得外部 AI 的 APPROVE**。

---

请作为严格独立 AI Reviewer，审核 Mission Monster（妖币）Stage147 的**真实保存的 Binance USD-M 525合约买卖盘 BBO 可靠性核验模块及 G4 严格无成交伪证门禁**。要求实际检出代码并运行测试、核对保存的真实行情数据，重点寻找会让错误源/过时报价/薄顶档报价被错误当作“可交易盈利”的问题，不要为了凑问题数量不断扩大低价值边界。

- Repo: https://github.com/lxxlx2/ChatGPT_mission_record
- Original Monster Draft PR #30: https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
- Branch: `research/monster-v4-local-discovery-20261010`
- **待审核 Stage147 源代码 + GitHub Actions 固定 SHA：`e6ec373d00e368d249758d6887a4a5144afd7ae9`**
- **上一轮 Stage145 外部 Codex APPROVE 的固定源码 SHA：`51f2eca3646db72158c42e7cfca5322c76e58c83`**
- 对比SHA不得混淆：Stage145 APPPROVE不自动批准本轮新增脚本，PR当前浮动HEAD在新增Stage147报告或审核提示词后会前移到文档commit。严禁只读HEAD而不 checkout 指定 e6ec SHA。

先阅读冻结协议 `crypto-300-profit-mission/monster/MONSTER_STAGE147_FROZEN_REAL_525_BBO_SOURCE_GATE_AND_G4_NO_FAKE_FILL_PROTOCOL_20261015.md`、长期规范 `crypto-300-profit-mission/monster/MONSTER_MODULE_DEVELOPMENT_RULES.md`、[Stage146历史真实数据分析](https://github.com/lxxlx2/ChatGPT_mission_record/blob/research/monster-v4-local-discovery-20261010/crypto-300-profit-mission/monster/MONSTER_STAGE146_SAVED_REAL_525_USDM_BBO_G4_SOURCE_QUALITY_BASELINE_20261015.md)。重点审查：

1. `crypto-300-profit-mission/local-agent/scripts/monster_v4_stage147_saved_real_bbo_execution_readiness.py`（新增纯标准库离线解析与G4禁止虚构成交）
2. `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_stage147_saved_real_bbo_execution_readiness.py`（真实525 + 人工破坏原始SHA、重复、缺失、无效盘口等）
3. `.github/workflows/monster-stage147-real525-bbo-G4-offline.yml`（必须没有schedule/live GET/trade/Gmail/Frank/部署）
4. `crypto-300-profit-mission/monster/evidence/monster_stage140_user_authorized_real_www_mirror_20261015/t0_2026-10-14T175247096Z/` 中保存的 `stage140_evidence_manifest.json`, `stage139_original_T0_asof_contract_metadata.json`, `usdm_all_best_bid_ask_raw_http.json`, `usdm_all_24h_ticker_raw_http.json`, `usdm_all_mark_price_raw_http.json`
5. 老的独立 `monster_v4_stage120_exchangeinfo_execution_rules.py` 与 `monster_v4_stage90_d2_execution_proof.py`，确认 Stage147 没有自建绕过原始合约过滤/实际深度门禁的新交易决策引擎；
6. 原已获审核但不应被 Stage147 修改的 `monster_v4_shadow.py`、Stage80 D1 和 Stage137/138 研究回放文件。

**必须主动验证以下问题**：

A. 真实525全市场 population join 是否保留 original venue 523 COIN-typed + 2 INDEX、完整525个初始尝试，不能“只显示成功join的赢家”。源出现重复或SHA不匹配应当失败，单一标的BBO/ticker/mark缺失或0价/交叉/无效数量应明确UNKNOWN，不能视为no-WATCH、失败2x或不可交易。跨三个保存的 `raw` 响应是否对原始 `raw_sha256` 与Stage140 manifest同时做重计算校验，说明 SHA只能证明保存字节内部一致，不能证明www镜像与标准FAPI源相同。

B. 严格比对 `row.time` 与保存的 `bookTicker.response_end_ms` 而不是和未来T0/当前机器时间比较；`bidPrice*bidQty` / `askPrice*askQty` 只作为 best-visible quote proxy，不可称为完整L2/可达USDT真实名义/能退出盈利。Binance官方 GET `/fapi/v1/ticker/bookTicker` 是best quote，不是 GET `/fapi/v1/depth`，即使后者也必须时间吻合、验证深度且不代表真实成交。特殊 `1000*` 符号单位和合约精度不能猜测，COIN也不等于已证实crypto issuer；美股/INDEX必须保留独立分类。

C. 交易金额/仓位缺省必须是UNKNOWN，禁止使用用户其他任务的300U作为默认为实际Monster资金；明确 `--scenario-quote 100` 仅为用户/测试显式历史顶档代理比较。原始525真实单时点 source，在该 **研究性** 场景下 ask <100 191/525、bid <100 236/525，仅说明单个最优价层显示代理，不代表订单在其他价格层不能完整成交，更不代表正或负净 PnL。检查是否任何分支错误地把 BBO 包装成 `G4_verified_executable_case=true`, `actual_fill=observed` 或 `G4 PASS`。

D. 对接真实G4能力不能凭空假设：现有 Stage140 **没有**多档 L2、没有入场和退出两个时间点、没有经过实际验证的MARKET_LOT_SIZE/合同单位映射、实际费率tier/资金费率成本、明确合法买入额、真实撮合成交。Stage120已要求真实订单过滤与MARK notional，Stage90和Stage119实际D2门禁不能被Stage147旁路。产品真实净收益门槛依旧至少30个独立真实可成交双边进出研究样本、必要fees/slippage/funding。任何单次快照模拟结果不能升级G4。

E. 真实源的原始捕获时钟：Stage140 T0前WWW FAPI备用域名2026-10-14 17:52:47Z，标准 fapi主端点在 GitHub美国出口 HTTP451，镜像内部exchangeInfo serverTime旧31,452,652毫秒，事件来源/当前资格未独立证明。没有新7日publisher 1m和完整上市事件流。原Stage116 06:00 首窗口失败不可回填，Stage118/127早期方法已被拒绝，Stage132追高即买负回报代理。G0 PARTIAL, G1 NOT_SCORABLE, G2/G3 NOT_PASSED, G4 UNKNOWN, G6 NO_GO。**Stage145 代码审核在旧 SHA 已通过并不等于新 Stage147 自动通过，也不代表利润验收**。

F. 安全：源码和CI是离线只读，无真实HTTP/交易账户/私有凭证，无ChatGPT Automation、GitHub cron、launchd/Stage99恢复、Gmail、Frank生产改动或本地部署。PR仍Draft，NO_MERGE, NO_DEPLOY, NO_GMAIL, NO_TRADE。

**固定SHA真实CI**：
https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38700244780
- head `e6ec373d00e368d249758d6887a4a5144afd7ae9`，macOS job 116306419541 和 Ubuntu job 116306419963 都 completed/success、**各5/5 PASS**；
- 实际log有 `STAGE147_REAL_SAVED525_NO_DEFAULT_NOTIONAL_NO_FAKE_G4=PASS`，`STAGE147_EXPLICIT_SCENARIO_ONLY_NEVER_EXECUTION=PASS`，`STAGE147_NO_LIVE_GET_NO_SCHEDULE_NO_GMAIL_NO_TRADE_NO_FRANK_NO_DEPLOY=PASS`。这只代表保存的525真实SHA核验和工程逻辑测试，不是“525次完成成交”。

可独立复现 (纯读取，无网络，clone repo checkout e6ec固定SHA之后在 scripts 目录运行)：
`python3 -m unittest -v test_monster_v4_stage147_saved_real_bbo_execution_readiness.py`
`python3 monster_v4_stage147_saved_real_bbo_execution_readiness.py --out /tmp/monster-stage147-review-no-notional.json`
`python3 monster_v4_stage147_saved_real_bbo_execution_readiness.py --scenario-quote 100 --out /tmp/monster-stage147-review-illustrative-only.json`
查看原始完整525行与标记 `full_L2_depth=MISSING`, `actual_fill=NOT_OBSERVED`, `net_executable_profit=UNKNOWN`，并用一份篡改过raw的副本确认SHA失败，绝不要触发新真实行情获取。

**请独立返回**：审核方名称/确切模型版本(UNVERIFIED如未知)、固定审核SHA、是否自行复跑上述原始保存525样本、`APPROVE / REQUEST_CHANGES / BLOCKED`、P0/P1/P2真实问题列表（精确文件及行号、复现输入与实际/预期、对真实早报/可交易性/净盈利误报的影响、最小修复建议）。如果无阻断问题，不要虚构。代码APPROVE也只针对Stage147新增纯离线代码，**不能提升G0–G4模型成熟度，不批准任何订单/部署/邮件/Frank/自动采集任务**。
