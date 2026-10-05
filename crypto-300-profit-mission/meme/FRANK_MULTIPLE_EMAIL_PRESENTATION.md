# Frank MULTIPLE mobile email presentation

EMAIL_CONTENT_CHANGE_ONLY = PASS (presentation commit scope).
MODEL_SEMANTICS_UNCHANGED = PASS. PRODUCTION_NO_GO.

Base/starting HEAD: `fd1bd37301263f4407104e980507d58695b7e668`.
The pre-sync local HEAD was `9126d87f08cde0506d9e3e840b327015e82b720b`.
The existing presentation work was retained throughout the separately authorized P0 repair.

## Presentation changes

- Keep `[Frank 多倍信号]`, original stage and signal-derived Bangkok minute in subject.
- Overview shows supplied symbol or short mint, complete CA, actual signal time,
  latest classified BUY, observed active buy/sell counts, cumulative original quote,
  first/latest buy times with explicit Asia/Bangkok, and observed inventory scope.
- 多倍信号 is a model-stage name, not a promise that price will rise several times.
- If latest BUY and triggering trade signatures differ, label the amount as the
  latest active BUY; do not infer the triggering SELL's direction/amount.
- Path A uses prior-cycle WATCH; only Path B mentions >=3 buys and >=45 minutes.
  Freshness describes the actual model gate without inventing a recent-60m BUY.
- Known reason codes are translated locally. Unknown codes display 未识别规则：code;
  the complete original code list is retained in final audit information.
- Audit retains full mint/signatures, signal/episode/policy IDs, policy hash,
  stage, delivery mode and original numeric quantities. Return/hash contracts stay unchanged.
- No current clock, API, price, market cap, PnL, ROI or symbol enrichment.
- Whitelist fields; never serialize arbitrary input, environment or credential objects.
- Historical/dry fixture content is marked as non-live at the top.

## Rendering authority and reliability boundary

Engine._emit freezes new MULTIPLE presentation in email_content.
The separately committed P0 repair makes Gmail sync consume frozen email_content,
and makes existing gmail_delivery authoritative for every status. This presentation
commit neither migrates old content nor changes identity, gate or recovery logic.
Old signal retains its old template; new signal gets the current template.
The full safety analysis is in FRANK_GMAIL_TEMPLATE_UPGRADE_SAFETY.md.
No outstanding template-upgrade coupling blocker remains in the tested offline code.
No production migration, restart, deployment or live validation is authorized/executed.

## Fixture provenance

Both complete emails use the exact same synthetic `tests/test_frank_v1.py`
`fixture_multiple()` signal. BEFORE was captured from the actual starting-HEAD
template before edits; AFTER is the final current renderer on that same input.
`mint1`, `third`, all 1970 times and quantities are fixture data, not live chain data.
Symbol and reliable USD estimate remain unavailable. Lifetime position is unknown.
No price/market-cap/PnL/ROI field is supplied or inferred.

## Validation

Initial related baseline: 70 passed. The final focused suite including upgrade,
header, local-signal, presentation and telemetry regressions: 139 passed, 0 failed,
0 skipped. Full suite: 546 passed, 0 failed, 3 skipped (unrelated missing numpy).
All Gmail and local notification tests are fake/mock/stub. Python compile,
model-boundary AST/byte checks, secret scan and git diff --check pass.

## BEFORE — FIXTURE / NOT LIVE DATA

```text
Subject: [Frank 多倍信号] mint1…mint1 | SUSPECTED_CONVICTION | 1970-01-02 11:31

Frank 多倍信号 — FRANK_LOCAL_SIGNAL_V1 链上行为模型触发

Signal ID: 3472bedf8b8b08fb751f37d301babd74f85ab8e7cd4841dba3fa801da20990f2
触发时间: 1970-01-02T11:31:40+07:00
Token: mint1…mint1
CA / Mint: mint1
Stage: SUSPECTED_CONVICTION
Episode ID: d851b09e2ca6aa1bd2901f9c0b4251e62452cc799291d348092af571b72f51f5
首次主动买入时间: 1970-01-02T10:46:40+07:00
最新主动买入时间: 1970-01-02T11:31:40+07:00
当前 buy_count: 3
当前 sell_count: 0
本次 BUY: 5000 USDC; 0.0001 token
累计 BUY: 31000 USDC
当前观察库存: 0.0003 token (OBSERVED_ACTIVE_SEQUENCE)
USD estimate: unavailable; USDC quote => direct numeric comparison
LIFETIME_POSITION_UNKNOWN; CURRENT_ACCUMULATION_SEQUENCE_KNOWN

触发规则:
- ACCUMULATION_BEHAVIOR_STAGE_ESTABLISHED
- MEANINGFUL_ACCUMULATION_T0_ESTABLISHED
- EPISODE_USDC_QUOTE_GE_10000
- PERSISTENCE_PATH_B_GE_3_BUYS_SPAN_GE_45M
- OBSERVED_INVENTORY_RETAINED_OR_RESUMED_NET_BUYING
- NO_UNRECOVERED_35PCT_ROLLING_DISTRIBUTION
- NO_CONFIRMED_HFT_EXECUTION
- FRESHNESS_BEHAVIOR_PASSED
- NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT

最新触发交易:
third

policy_hash: 83ebab1fbb8ec7e03950626137c5597a38b81b8a4085d9150610018cc78cedab
```

body_hash: `2e54809f9ca6289fd36d3f8024991ee75bd568c477eb76147278e1e6c2e72e1a`

content_hash: `f5c48805d18f7a56601c7e88502c0c9ed8346585a02c0ddbdef4fd941fb4bd2a`

## AFTER — FIXTURE / NOT LIVE DATA

```text
Subject: [Frank 多倍信号] mint1 | SUSPECTED_CONVICTION | 1970-01-02 11:31

Frank 多倍信号（历史 / 演练，非当前实时交易）
“多倍信号”是 Frank 持续建仓行为模型的阶段名称，不代表价格将上涨数倍。

状态：疑似高确信度
Token：mint1
CA：mint1
时间：1970-01-02T11:31:40+07:00（Asia/Bangkok）

本次：
BUY 5,000 USDC
获得 0.0001 token

累计：
本轮观察到 Frank 主动买入 3 次；主动卖出 0 次
累计投入 31,000 USDC
首次主动买入：1970-01-02T10:46:40+07:00（Asia/Bangkok）
最新主动买入：1970-01-02T11:31:40+07:00（Asia/Bangkok）
当前观察库存：0.0003 token
仅代表本轮已观察主动交易序列，不代表 Frank 的完整历史持仓。

为什么触发：
- 此前已形成持续建仓行为
- 本轮累计 USDC 买入金额达到模型要求
- 本轮至少 3 次主动买入，首笔到最新买入持续 ≥45 分钟

链上事实
首次主动买入时间：1970-01-02T10:46:40+07:00（Asia/Bangkok）
最新主动买入时间：1970-01-02T11:31:40+07:00（Asia/Bangkok）
当前 buy_count：3
当前 sell_count：0
最近一次主动买入 quote：5,000 USDC
最近一次主动买入 token：0.0001 token
累计 quote spent：31,000 USDC
当前观察库存：0.0003 token
最新触发交易：third

触发说明（全部）：
- 此前已形成持续建仓行为
- 已确认有效建仓起点
- 本轮累计 USDC 买入金额达到模型要求
- 本轮至少 3 次主动买入，首笔到最新买入持续 ≥45 分钟
- 观察到的仓位仍在保留，或近期重新转为净买入
- 未触发模型的未恢复减仓否决条件
- 未触发模型的高频交易否决条件
- 该建仓行为仍满足模型的新鲜度要求
- 价格、流动性、GPT 判断等非 Frank 链上行为条件不参与阻止该信号

风险 / 不确定性
当前只能确认本轮观察到的建仓序列，无法保证这是 Frank 对该 Token 的完整历史仓位。
USD 估值：暂无可靠数据
金额按原始 quote 记录；USDC quote 直接进行数值比较。
本邮件展示模型研究信号，不构成收益保证。
投递模式：DRY_RUN_AUDIT；不是当前实时交易。

审计信息
signal_id: 3472bedf8b8b08fb751f37d301babd74f85ab8e7cd4841dba3fa801da20990f2
episode_id: d851b09e2ca6aa1bd2901f9c0b4251e62452cc799291d348092af571b72f51f5
policy_id: FRANK_LOCAL_SIGNAL_V1
policy_hash: 83ebab1fbb8ec7e03950626137c5597a38b81b8a4085d9150610018cc78cedab
stage: SUSPECTED_CONVICTION
CA / Mint: mint1
latest_trade_signature: third
triggering_signature: third
latest_buy_signature: third
delivery_mode: DRY_RUN_AUDIT
reason_codes:
- ACCUMULATION_BEHAVIOR_STAGE_ESTABLISHED
- MEANINGFUL_ACCUMULATION_T0_ESTABLISHED
- EPISODE_USDC_QUOTE_GE_10000
- PERSISTENCE_PATH_B_GE_3_BUYS_SPAN_GE_45M
- OBSERVED_INVENTORY_RETAINED_OR_RESUMED_NET_BUYING
- NO_UNRECOVERED_35PCT_ROLLING_DISTRIBUTION
- NO_CONFIRMED_HFT_EXECUTION
- FRESHNESS_BEHAVIOR_PASSED
- NON_BEHAVIOR_VETO_GATES_REMOVED_BY_USER_REQUIREMENT
inventory_scope: OBSERVED_ACTIVE_SEQUENCE
lifetime_position: LIFETIME_POSITION_UNKNOWN
USD estimate: unavailable
latest_quote_amount_raw_quantity: 5000
quote_asset: EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
latest_buy_token_quantity: 0.0001
current_token_position_raw: 300
gross_quote_spent: {"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "31000"}
```

body_hash: `836480edfa7024790d2965d502d55ec946d7688ee9d195e852a99383536d6b5a`

content_hash: `a8abe4725f060691481f47d81da55200450410e9427f5a25da1f7baa34c44ce8`
