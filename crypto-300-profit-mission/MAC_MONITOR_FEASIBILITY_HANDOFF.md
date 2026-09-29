# REVIEWED ADDENDUM v2 — 2026-09-29

This addendum supersedes conflicting parts of the original feasibility handoff below.

## A. Revised product decision: CONDITIONAL GO

Mac-side collection and deterministic ETL are feasible. The main risks are:
1. GPT consumer is hourly and therefore cannot provide <=5 min GPT judgement under the free/current automation model.
2. GitHub must not be treated as the primary queue/database.
3. Gmail exactly-once delivery cannot be mathematically guaranteed without an idempotency primitive from the mail provider; the design must explicitly choose an at-least-once or at-most-once bias.
4. External sources such as Solana public RPC and arbitrary NFT websites have no project-controlled SLA.
5. A local watchdog cannot detect Mac power-off/sleep while the entire machine is unavailable; remote stale-health detection is required.

## B. Security correction: current repository is PUBLIC

`lxxlx2/ChatGPT_mission_record` is currently public.

Therefore **runtime-v2 ingest/health/decision/delivery data MUST NOT be written to this public repository** if they contain wallet behavior, user holdings, private monitoring state, event queues, delivery state or other sensitive operational data.

Preferred production design:
- keep this public repo for specifications, model rules, non-sensitive reports and audit design;
- create/use a separate PRIVATE GitHub repository for runtime transport;
- do not put secrets, PATs, OAuth tokens, raw wallet archives or Gmail identifiers in Git.

No repository visibility change is authorized by this document.

## C. GitHub transport correction

Do not write high-frequency heartbeats into GitHub every minute.

Local SQLite is authoritative. GitHub only transports compact batches and external health summaries.

Recommended cadence:
- ingest candidate: event-driven, immediately when a candidate is created;
- compact health snapshot: every 10–15 minutes OR on health state change;
- decision/delivery receipt: event-driven;
- no per-tick/per-minute archive commits.

Because Mac git pushes and GPT Contents-API writes on the same branch can race, production runtime should use separate writer branches in the PRIVATE runtime repo:

- `mac-data`: written only by Mac; read by GPT.
- `gpt-data`: written only by GPT; read by Mac if needed.

GPT input files must contain:
- schema_version
- batch_id
- generated_at
- valid_until
- item_count
- payload_sha256

GPT decision receipts must include:
- input_batch_id
- input_payload_sha256
- consumed_item_count
- decision timestamp

Mac/health reconciliation must detect stale/mismatched receipts.

GitHub secondary limits currently document general content-generation limits of roughly 80 requests/minute and 500/hour, and authenticated REST commonly has a 5,000 request/hour primary limit. The proposed event-driven + 10–15 minute health cadence is far below these limits, but rate-limit headers/backoff remain mandatory.

## D. SLO split: collection vs judgement

Do not confuse low-latency collection with low-latency GPT decisions.

### Collection SLO
Mac-side targets:
- BTC/ETH/SOL/BNB freshness <10s while connected
- HYPE freshness <15s while connected
- local PRICE_CANDIDATE write <=5s from local observation
- Frank new-signature discovery p95 <=30s
- Monster lightweight universe age <=60s

### GPT consumer SLO under current free architecture
- nominal consumer interval: hourly
- target decision within next scheduled cycle
- acceptance target: >=95% scheduled-cycle completion during shadow test
- missed cycle must recover pending events on the next successful cycle
- no pending event may be silently dropped
- backlog must not grow for >2 consecutive consumer cycles

**Hard product limitation:** <=5 minute GPT final judgement for Monster/NFT is NOT FEASIBLE with the current free hourly automation. If <=5 min is required, use an API/trigger mechanism or allow a non-GPT factual alert.

## E. GPT dry-run Gate correction

The previous requirement of 100% scheduled completion is not realistic because the scheduler is an external dependency.

Revised Gate G:
- shadow period >=48h, not 24h;
- scheduled consumer success rate >=95%;
- 0 silently lost pending events;
- every missed consumer run must be recovered by a later run;
- oldest unconsumed event age <=2 nominal cycles during normal source availability;
- run a synthetic full-load test containing 40 normal candidates + urgent candidates + pre-existing backlog;
- compact input <=100KB;
- no connector response truncation;
- decision receipt must echo batch_id + payload_sha256.

If these fail, do not enable production alerts.

## F. Gmail semantics correction

Exactly-once external email delivery cannot be guaranteed strictly using:
`search Sent -> send -> readback`.

Required state machine:
- stable event_id is generated before GPT and may not be rewritten by GPT;
- one active delivery lease/fencing token per event;
- subject/body carries stable event_id;
- after send returns success, store provider message_id immediately when available;
- if send outcome is ambiguous, state becomes `DELIVERY_UNCERTAIN`;
- while uncertain, do not blind-send again;
- repeatedly search/read Sent for the stable event_id after a cooldown window;
- only a deliberate configured policy may resend after uncertainty.

Gate H must include:
1. send succeeds + readback succeeds;
2. send succeeds + receipt write fails;
3. send succeeds + immediate Sent search misses;
4. send call times out/ambiguous;
5. same event replayed >=3 times;
6. two consumers attempt same event concurrently.

Product owner must explicitly choose:
- AT_LEAST_ONCE bias: rare duplicate acceptable, missing ACTION minimized; or
- AT_MOST_ONCE bias: no automatic duplicate, but an ambiguous send may become a missed mail/manual recovery.

Until chosen, email design is not IMPLEMENTATION_READY.

## G. Health/watchdog correction

Local watchdog alone is insufficient because Mac sleep/power-off stops both collector and watchdog.

Every externally visible health snapshot must include:
- seq
- generated_at
- valid_until
- host_boot_id
- collector_version
- clock_offset_ms or NTP health
- source freshness fields
- queue depth
- sync lag
- last successful consumer receipt

GPT must treat:
- now > valid_until
as `UNHEALTHY_STALE_HOST`, even if the last written status said HEALTHY.

Mac deployment must explicitly decide:
- LaunchAgent vs LaunchDaemon;
- FileVault/reboot behavior;
- whether unattended boot before login is required;
- sleep policy while connected to power.

If LaunchAgent is used, it cannot be described as "automatic after every reboot" until login behavior is verified.

## H. Frank public RPC Gate correction

Before the 500-tx Gate, run an archival-availability probe:
- newest known Frank signature
- 25th percentile age
- median age
- oldest target signature

Use `getTransaction` with:
- commitment=finalized
- encoding suitable for deterministic parsing
- maxSupportedTransactionVersion=1

A null/not-found result must be recorded as `UNAVAILABLE_ON_PUBLIC_RPC`; it is not a parser failure.

If the oldest required target history is not available from `api.mainnet.solana.com`, the "public RPC only, no fallback" product requirement means full historical replay is **NOT FEASIBLE under the chosen source constraint**. Do not silently introduce another provider.

Define Frank evidence terms before implementation:
- wallet_is_signer
- wallet_is_fee_payer
- wallet_token_owner
- wallet_authority_evidence
- inner_instruction_authority
- SOL/token delta semantics

Do not use a vague boolean `wallet_is_authority` without evidence fields.

Manual validation must compare at least 50 samples against an independent explorer presentation plus raw RPC, not RPC against itself.

## I. Price replay correction

Live alert features must be reconstructable from the historical dataset used for Gate B.

If replay uses 1m candles:
- do not validate tick-only logic with those candles;
- define returns/high-low/reversal/volatility from 1m OHLCV in both replay and live canonical feature code;
- live tick/WS data may update the current 1m bar, but the alert rule must specify whether it uses completed bars or provisional bars.

Before 30-day HYPE replay, probe how much official/source history can actually be retrieved.

"Missed obvious move" must be defined before replay, e.g. an objective future excursion criterion, to reduce hindsight fitting.

After rule freeze:
- run a shadow period before production;
- do not tune thresholds from individual live misses without a new version + replay.

## J. Binance 2026 WebSocket correction

The developer must use current USDⓈ-M Futures WebSocket endpoint/path rules.

Binance's 2026 change log states a WebSocket base-URL/path migration and that the old URL was retired on 2026-04-23. Current docs must be checked at implementation time.

Do not hard-code an endpoint copied from pre-migration examples.

24h disconnect handling must be tested. Prefer make-before-break where the protocol/source permits:
1. establish replacement connection;
2. resubscribe;
3. deduplicate overlap using event time/sequence keys;
4. retire old connection.

## K. Monster historical replay limitation

Do not claim full historical replay of features that the upstream source no longer retains.

Before Gate D:
- probe actual available history for OI/funding/top-trader/taker endpoints;
- inventory delisted symbols separately;
- document survivor bias;
- distinguish reconstructed candle snapshots from live stream semantics.

Gate D may be split:
- D1: historical price/volume candidate recall on available/delisted datasets;
- D2: forward shadow collection of OI/funding/top-trader features from now onward;
- D3: model evaluation once enough forward data exists.

## L. NFT Gate correction

NFT source reliability is heterogeneous and partially outside project control.

Use per-source classes:
- REQUIRED_DETERMINISTIC: sources the product promises to monitor
- BEST_EFFORT: third-party pages/APIs with anti-bot or availability risk
- DISCOVERY_ONLY: broad web/social sources

Only REQUIRED_DETERMINISTIC sources participate in hard source-coverage gates.

BEST_EFFORT/DISCOVERY_ONLY failures must appear as source gaps and must not block the whole system.

Untrusted webpage/social text must never be inserted verbatim into the controlling prompt. Use structured extraction, length limits and an explicit untrusted-content field to reduce prompt-injection risk.

## M. Missing engineering requirements

Before implementation, add:
- secret management: GitHub PAT / OAuth tokens / Gmail credentials in macOS Keychain or equivalent; never Git;
- schema migration/versioning for SQLite;
- backup/restore of SQLite;
- disk retention policy and raw Frank archive compression;
- rollback procedure for collector releases;
- dual-run/shadow comparison before enabling production;
- monotonic clock for local latency measurement;
- UTC timestamps internally, Bangkok only for presentation;
- disk-full failure injection;
- payload corruption/hash mismatch injection.

## N. Revised development order

Do not build all collectors first.

Risk-first sequence:
1. **Minimal fake-event E2E without real collectors**:
   Mac synthetic event -> private GitHub transport -> GPT dry decision -> delivery state -> Gmail canary -> readback -> receipt.
2. Validate scheduler recovery, hash receipts, delivery ambiguity and duplicate behavior.
3. CORE PRICE live + 30d replay + shadow.
4. Frank public-RPC archival probe -> 500 tx -> history/live separation.
5. Health/watchdog/sleep/reboot/failure injection.
6. Monster lightweight collector + replay/forward-shadow split.
7. NFT deterministic sources, then best-effort discovery.
8. 48h full-stack shadow.
9. Only then request authorization to re-enable existing `$300 Crypto资产状态监控`.

## O. Go/No-Go decisions still required from product owner

Implementation is not ready until these are explicitly decided:

1. Is worst-case ~1 hour GPT judgement latency acceptable?
2. For ACTION email uncertainty: AT_LEAST_ONCE or AT_MOST_ONCE?
3. Is a separate PRIVATE GitHub runtime repository acceptable?
4. Is Solana public RPC still the only permitted RPC even if the oldest Frank history is unavailable?
5. Is NFT scope accepted as deterministic known sources + best-effort discovery, not full X/firehose coverage?
6. Must the Mac recover before user login after a reboot, or is post-login LaunchAgent acceptable?
7. What maximum local disk budget is allowed?
8. Is 48h shadow with >=95% consumer-cycle success sufficient for production gate?

Until these are answered, status is `CONDITIONAL_GO / NOT_IMPLEMENTATION_READY`.

---

# Mac 本地监控重构：可行性评估与开发交接

> 状态：DESIGN / FEASIBILITY ONLY  
> 日期：2026-09-29  
> 约束：本文只定义需求、可行性、数据边界、故障模型、验收标准与交接；不代表已经实现。  
> 当前 ChatGPT 自动任务中，除 `美股每日晨报`、`Crypto 每日情报`、`全项目空投与TGE监控` 外，其余相关监控均应保持停用，直到本方案通过端到端验收。

## 1. 产品目标

构建一套运行在用户 Mac 上的 24h crypto opportunity monitor。

系统目标不是让本地脚本做投资判断。本地只负责：
1. 持续采集原始事实；
2. 对原始事实做确定性、可单元测试的数据整理和压缩；
3. 维护 cursor / queue / health / retry；
4. 把 compact evidence 同步到 GitHub。

GPT 负责：
1. 读取 compact evidence；
2. 做最终语义判断和投资判断；
3. 必要时补充少量 fresh public verification；
4. 输出 IGNORE / WATCH / ACTIONABLE_RISK / ACTIONABLE_OPPORTUNITY；
5. 只有 ACTION 类结果才通过 Gmail 发送给用户；
6. 写 decision/delivery receipt，支持去重和恢复。

设计原则：

```
Mac = eyes + memory + deterministic ETL
GitHub = durable transport + audit
GPT = reasoning / investment judgement
Gmail = final actionable delivery
```

不得让 GPT 自动任务重新承担全市场原始抓取、Solana 大 JSON 逐笔解析、全天候 WebSocket、批量历史 RPC、cursor 维护。

## 2. 当前已确认的问题

### 2.1 ChatGPT connector 不适合批量原始 Solana transaction ETL

已在 2026-09-29 诊断确认：通过当前 Alchemy connector 获取的 Solana `getTransaction` 返回在约 8k 字符附近出现截断，导致完整 JSON 无法可靠解析。单笔 RPC 能返回，但连续大批量读取后上下文和完整性不可控。

结论：Frank 原始交易采集必须移出 ChatGPT scheduled runtime。

### 2.2 ChatGPT scheduler 不适合承担实时采集

现有 scheduled task 只能按小时级执行，且实际运行时间存在分钟级抖动。它适合作为“批量读取 compact evidence + GPT 判断”的 consumer，不适合作为秒级/分钟级 market collector。

因此完全免费、仍要求 GPT 做最终判断时，存在硬限制：

- 本地发现延迟可以做到秒级/分钟级；
- GPT 最终判断最坏约接近 1 小时；
- 若要求 GPT 在 1-5 分钟内自动判断，则需要可从 Mac 主动调用 GPT 的 API/其他触发机制；现有 ChatGPT hourly automation 本身无法满足这一 SLA。

这必须在开发前接受，不能上线后再把它当 bug。

## 3. 可行性结论

| 模块 | 本地采集可行性 | GPT 判断可行性 | 免费方案主要限制 | 结论 |
|---|---|---|---|---|
| BTC/ETH/SOL/BNB/HYPE 价格异常 | 高 | 高 | GPT 最终判断为小时级 | 可开发 |
| Frank 实时地址监控 | 高 | 高 | Solana public RPC 无 SLA | 可开发 |
| Frank 30D/7106 历史采集 | 高 | 中-高 | GPT 历史分类需分批消费 | 可开发 |
| Binance Monster/妖币扫描 | 高 | 高 | 全量数据必须先本地筛成小候选集 | 可开发 |
| NFT 已知创作者/平台/页面/链上监控 | 高 | 高 | 站点反爬/页面变动 | 可开发 |
| NFT 全互联网/X 热点发现 | 低-中 | 高 | 免费稳定的 X 全量发现不可保证 | 只能做有限覆盖 |
| Gmail 最终 ACTION 通知 | 高 | 高 | ChatGPT runtime 失败可造成延迟 | 可通过幂等恢复设计 |
| 24h 无人值守运行 | 高 | N/A | Mac 睡眠/断网 | 可通过 launchd + watchdog + sleep policy |

整体结论：**方案工程上可实现，数据量对一台普通 Mac 很轻；最大的真实限制不是算力，而是免费条件下 GPT consumer 的小时级触发延迟，以及 Solana public RPC / 外部网页源没有 SLA。**

## 4. 数据源与约束

### 4.1 主流价格

监控：
- BTC
- ETH
- SOL
- BNB
- HYPE

BTC/ETH/SOL/BNB：
- Binance public market WebSocket。

HYPE：
- Hyperliquid official WebSocket。

Binance 官方文档当前说明：
- 单 WebSocket 连接最多 1024 streams；
- 单连接 24h 后会断开，需要重连；
- 客户端必须正确处理 ping/pong 和 reconnect。

Hyperliquid 官方文档明确要求自动客户端处理 server-side disconnect 并重连，重连后可通过 snapshot/info 恢复遗漏数据。

参考：
- https://developers.binance.com/en/docs/products/derivatives-trading-coin-futures/websocket-market-streams/Connect
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket

### 4.2 Frank Solana

唯一 RPC：
- `https://api.mainnet.solana.com`

不使用 Helius，不设计 fallback provider。

官方当前公开限制：
- 每 IP 每 10 秒 100 requests；
- 单一 RPC method 每 IP 每 10 秒 40 requests；
- 40 concurrent connections；
- 100 MB / 30 sec。

官方同时明确 public RPC 不用于 production SLA，限制可变，也可能 429/403。

本项目属于低流量个人监控，目标限速：
- historical backfill: <= 2 `getTransaction` / sec；
- live signature polling: 15-30 sec 一次；
- new tx detail 按实际新增量拉取。

7106 笔历史交易按 2 tx/sec 的纯请求理论时间约 59 分钟，实际加重试/节流预留 1-3 小时。数据量远低于公开速率和带宽限制。

如果 public RPC 发生 429：
- honor Retry-After；
- exponential backoff；
- SQLite 保持 cursor；
- health = DEGRADED；
- 恢复后继续。

如果发生 403：
- health = UNHEALTHY_RPC_BLOCKED；
- 不切 provider；
- 不伪造成功；
- 等人工处理或 RPC 恢复。

参考：
- https://solana.com/docs/references/clusters

## 5. Mac 端职责

### 5.1 本地绝不做的事情

不得输出：
- BUY / SELL 作为投资结论；
- IGNITION / EXHAUSTION 作为最终市场结论；
- FORMAL_ENTRY / FORMAL_EXIT；
- “值得买/卖/做多/做空”；
- 最终 NFT 价值判断。

这些属于 GPT。

### 5.2 本地允许做的确定性处理

允许：
- timestamp/order/cursor；
- rolling return；
- OHLC / high / low；
- realized volatility；
- volume/OI/funding 等数值整理；
- signer / authority / program id；
- token/SOL balance delta；
- page hash/diff；
- mint count / supply / price；
- stable event_id；
- duplicate suppression；
- hard prefilter。

hard prefilter 只能定义成 `RAW_CANDIDATE`，不能定义成交易信号。

## 6. CORE_PRICE_ALERT

资产：BTC / ETH / SOL / HYPE / BNB。

第一版候选触发门槛：

1. 15m absolute return >= 3%
2. 1h absolute return >= 5%
3. 4h absolute return >= 8%
4. 24h absolute return >= 12%
5. 15m local high/low reversal >= 4%
6. break 24h high/low by >= 1% and remain beyond for two consecutive samples
7. 5m realized-volatility proxy >= 3x trailing 24h same-scale median AND absolute 5m move >= 2%
8. non-BTC asset 1h return differs from BTC by >= 4 percentage points
9. non-BTC asset 4h return differs from BTC by >= 6 percentage points

这些阈值上线前必须用至少 30 天历史数据回放；允许最终按资产分别校准，但校准后冻结版本号，禁止运行中临时调参。

Mac 输出：
- `RAW_PRICE_CANDIDATE`

GPT 输出：
- IGNORE
- WATCH
- ACTIONABLE_RISK
- ACTIONABLE_OPPORTUNITY

只有后两种允许 Gmail。

## 7. 数据规模与资源预算

### 7.1 Price CORE

5 个资产即使每秒处理 tick，计算量极低。

长期落盘不保存每个 tick，只保存：
- 1m/5m rollup；
- candidate；
- health。

1m bar：
- 5 * 1440 = 7200 rows/day；
- 对 SQLite 属于极小负载。

### 7.2 Monster / Binance 全市场

不应把每个 symbol 的所有 trade/kline raw stream 永久落盘。

建议：
- 一个 all-market lightweight ticker stream 做实时价格面；
- 内存维护 rolling state；
- 每 5 分钟持久化 compact universe snapshot；
- 只对 RAW_CANDIDATE 拉 1h klines / OI / funding / taker/top-trader 深数据；
- candidate/audit 永久保存；
- universe compact snapshots 仅保留 7-14 天。

假设 500-600 个活跃合约：
- 5min persistence 约 144k-173k symbol rows/day；
- 仅保存 price/volume/reference fields，SQLite/Parquet 都可轻松处理；
- 30 天无需保存全部明细，rolling retention 后存储可控制在数百 MB 级，而非数十 GB。

资源验收目标：
- collector 平均 CPU < 10%
- RSS < 500 MB
- SQLite DB + retained market snapshots < 2 GB
- 单日网络流量实际压测记录，不预先假定；如果 > 3 GB/day，必须优化 stream / sampling。

### 7.3 Frank

live：
- getSignaturesForAddress 15-30s polling；
- 只对新 signatures 拉 tx details；
- 原始完整 JSON 仅本地存档，可 gzip；
- compact evidence 才同步 GitHub。

history：
- 7106 signatures 一次性 backfill；
- raw archive + compact evidence 分离；
- GPT 不读取 raw transaction JSON。

### 7.4 GPT 输入上限预算

每次 GPT scheduled consumer 必须控制输入，不允许重新出现“大 JSON 堆上下文”。

目标：
- `current-batch.json` <= 100 KB；
- 单 candidate compact evidence <= 2 KB；
- 每轮最多 40 个 normal candidates；
- urgent candidates 优先；
- backlog > 40 时按 oldest + severity 处理，其余留队；
- historical Frank replay 与 live consumer 分离，不允许历史 backlog 挤占 live alert。

如果 backlog 连续 2 个 GPT cycle 增长：
- health = UNHEALTHY_CONSUMER_BACKLOG；
- 不能继续声称监控正常。

## 8. Frank compact evidence

本地从完整 RPC 提取事实，例如：

```json
{
  "event_id": "frank:<signature>",
  "signature": "...",
  "slot": 0,
  "block_time": "...",
  "wallet_is_signer": true,
  "wallet_is_authority": true,
  "program_ids": ["..."],
  "sol_delta_lamports": 0,
  "token_deltas": [
    {"mint": "...", "delta_raw": "...", "decimals": 6}
  ],
  "tx_err": null
}
```

本地可以用硬事实过滤“既非 signer/authority 且没有 wallet value delta”的明显无关事件，但：
- 必须保留 raw archive；
- 必须记录 filtered_count；
- 过滤规则需单元测试；
- 不得基于项目价值/交易意图做过滤。

GPT 再决定 active swap / passive / HFT / WATCH / ENTRY / EXIT。

## 9. Monster compact pipeline

本地阶段：
1. 获取 Binance futures active symbols；
2. 维护 last price / 1h / 4h / 6h / 24h relative return；
3. 维护 lightweight volume/liquidity proxy；
4. 异常资产进入 RAW_MONSTER_CANDIDATE；
5. 只对 candidate 拉精确 1h klines、OI、funding、taker-buy 和必要 top-trader 数据；
6. compact evidence 写 GitHub。

GPT 阶段：
- 根据冻结模型判断 STRUCTURAL / PRESSURE / IGNITION / EXHAUSTION；
- 需要时查当前项目/新闻/安全背景；
- 只有真正需要用户行动才发 Gmail。

必须先用历史妖币回放验证 recall，不允许上线后以“今天没报”为第一种健康检查方式。

## 10. NFT 可行边界

### 可稳定本地化

- 已知创作者/项目官方网页；
- Manifold/Zora/OpenSea 等公开页面/API 可用部分；
- mint page diff；
- contract deployment / mint count / supply / mint velocity；
- configured creator/platform watchlist；
- domain/official-page changes。

### 无法承诺完全免费且稳定覆盖

- 全量 X/Twitter 实时社交发现；
- 任意新 NFT 项目“全互联网不漏”；
- 被 Cloudflare/登录墙/动态反爬阻断的网站。

因此 NFT 必须拆成：
- local deterministic watcher：已知源和可机器读源；
- GPT/Crypto Daily web discovery：补充 broad discovery。

验收报告必须展示 source coverage，不能把 source gap 写成“没有机会”。

## 11. GitHub 传输模型

GitHub 不是 primary database。

primary source of truth：
- Mac SQLite。

GitHub：
- compact transport + audit。

路径必须分离，避免 Mac 和 GPT 写同一个文件：

```
crypto-300-profit-mission/runtime-v2/
  ingest/
    current-batch.json        # Mac only
    archive/YYYY-MM-DD/*.jsonl
  health/
    current.json              # Mac only
  decisions/
    current.json              # GPT only
    archive/YYYY-MM-DD/*.jsonl
  delivery/
    current.json              # GPT only
```

同步原则：
- Mac 不因 GitHub 失败删除本地 event；
- GitHub 同步成功后记录 synced_at；
- GPT 用 event_id 去重；
- GitHub 文件 read/write failure 不得导致 event 丢失；
- Mac 和 GPT 不写相同 path。

## 12. Email 可靠性设计

Gmail API 本身的 quota 对本项目不是瓶颈。当前官方 quota 远高于本项目预计的少量 ACTION 邮件。

真实风险来自：
- ChatGPT scheduled runtime 某轮没跑；
- send 后 GitHub receipt 写失败；
- send 返回不明确；
- 重试造成重复邮件。

必须使用 stable event_id + Gmail Sent readback。

建议邮件 subject：

```
[MISSION:<event_id>] <human readable title>
```

发送状态机：

```
PENDING_DECISION
  -> GPT ACTION
  -> DELIVERY_PENDING
  -> search Gmail Sent by exact event_id
       -> found: mark DELIVERED, do not resend
       -> not found: send once
  -> readback sent message
       -> success: DELIVERED(message_id)
       -> ambiguous/fail: remain DELIVERY_PENDING
```

下一轮永远先查 Sent，再决定是否 resend。

这样覆盖：
- Gmail send 成功但 GitHub 写失败；
- runtime 在 send 后中断；
- 上轮状态不确定；
- duplicate retry。

禁止同一轮连续多次 blind send。

参考：
- https://developers.google.com/workspace/gmail/api/reference/quota

## 13. 健康模型

系统正常不能依赖“今天有没有预警”。

`health/current.json` 至少包含：

```json
{
  "overall": "HEALTHY",
  "collector_version": "...",
  "price_assets_live": "5/5",
  "price_max_age_sec": 0,
  "frank_rpc_last_success_age_sec": 0,
  "frank_cursor_gap": 0,
  "monster_universe_age_sec": 0,
  "nft_source_success_ratio": 0.0,
  "sqlite_last_commit_age_sec": 0,
  "github_sync_lag_sec": 0,
  "unsynced_events": 0,
  "gpt_pending_events": 0,
  "oldest_pending_age_sec": 0,
  "last_e2e_canary": "PASS",
  "last_e2e_canary_at": "..."
}
```

建议硬标准：

- price BTC/ETH/SOL/BNB age < 10s
- HYPE age < 15s
- price assets 5/5
- candidate SQLite write latency <= 5s
- Frank signature discovery p95 <= 30s
- Frank evidence generation p95 <= 60s
- Frank cursor gap = 0
- Monster lightweight universe age <= 60s
- Monster raw candidate latency <= 120s
- configured NFT source success ratio >= 95% over rolling window
- GitHub sync p95 <= 60s
- no unsynced event older than 5min
- GPT consumer backlog does not grow for >2 cycles
- duplicate Gmail per event_id = 0

连续违反硬标准：
- overall != HEALTHY。

不得把 runtime/source failure 写成 NO_ACTION。

## 14. Watchdog

独立 launchd watchdog，只检查基础设施，不做投资判断：

- process alive
- last heartbeat
- source freshness
- SQLite writable
- disk free
- queue depth
- GitHub sync age
- restart count
- sleep gap
- network gap

collector crash 后 launchd 自动重启。

Mac 必须配置：
- 接电时不进入 system sleep；
- display 可以关闭；
- 重启后 LaunchAgents 自动加载。

## 15. 开发阶段与验收 Gate

任何阶段失败都不能启用真实 $300 GPT monitor。

### Gate A：unit tests

- rolling returns boundary tests；
- event_id deterministic；
- SQLite cursor transactional；
- duplicate suppression；
- reconnect；
- retry/backoff；
- GitHub sync idempotency；
- Gmail decision state machine pure logic tests。

要求：100% mandatory test pass。

### Gate B：price 30d replay

BTC/ETH/SOL/HYPE/BNB 至少 30 天。

输出：
- 每个阈值触发次数；
- triggers/day median/p95/max；
- false/noise sample；
- asset-specific calibration proposal。

冻结 `price_rule_version` 后才进入 live shadow。

### Gate C：Frank 500 tx test

连续 500 tx：
- fetched 500/500；
- raw persisted 500/500；
- compact evidence 500/500；
- cursor gap 0；
- random manual sample >= 50，signer/token delta/program 对原始 RPC 一致。

然后才允许完整 7106 history backfill。

### Gate D：Monster historical replay

必须使用多个已知历史 monster/妖币样本。

至少输出：
- candidate recall；
- first candidate lead time；
- false-positive/day；
- missed cases + reason。

不能只展示成功命中的案例。

### Gate E：NFT simulation

模拟：
- page change；
- mint open；
- price change；
- supply change；
- source timeout；
- duplicate update。

所有 configured deterministic events 必须 100% 落 queue。

### Gate F：failure injection

必须主动做：
- network off 5min；
- GitHub unavailable；
- Solana 429 simulation；
- kill each process；
- SQLite locked/error simulation；
- Mac reboot；
- process restart。

验收：
- local event 不丢；
- cursor 不倒退；
- backlog 恢复；
- duplicate = 0；
- health 正确变 UNHEALTHY/DEGRADED 后恢复。

### Gate G：GPT dry-run

真实 Gmail 关闭。

至少连续 24h：
- GPT 每轮只读 compact batch；
- 每个 pending event 有 decision receipt；
- no stale event silently dropped；
- 输入文件 <= 100KB；
- consumer backlog 不增长；
- runtime completion evidence 100%。

### Gate H：Email dry-run / canary

人工构造 ACTION test event：

```
Mac -> SQLite -> GitHub -> GPT -> ACTION decision -> Gmail -> Sent readback -> delivery receipt
```

至少连续 3 个不同 event_id 全链路 PASS。

再测试同一 event_id 重放 3 次：
- Gmail 实际邮件数量必须 = 1。

### Gate I：真实启用

只有 A-H 全部 PASS：
- 才允许重新启用现有 `$300 Crypto资产状态监控`；
- 不创建新的 ChatGPT monitor；
- 首周每天审计 health metrics 和 missed-event test fixtures；
- 不以“没有报警”作为健康证明。

## 16. GPT consumer 的正式职责

恢复后的 `$300 Crypto资产状态监控` 应非常小：

1. read `runtime-v2/health/current.json`
2. 如果关键 health UNHEALTHY：不做“市场无机会”结论；记录 consumer status
3. read `runtime-v2/ingest/current-batch.json`
4. 按 event_id 去重
5. 对候选做 GPT 判断
6. 必要时少量 fresh verification
7. 写 decisions
8. ACTION 才进入 Gmail delivery state machine
9. Gmail Sent readback
10. 写 delivery receipt

不得在 GPT task 内：
- 全 Binance 扫描；
- Solana 批量 raw tx；
- NFT 全网 crawling；
- 7106 历史 RPC；
- 大规模 price history fetch。

## 17. 免费方案的明确 SLA

在不使用 OpenAI API 主动唤醒 GPT 的前提下：

### 可以承诺为开发目标

- Mac raw data detection: 秒到分钟
- local queue durability: 分钟内同步 GitHub
- collector 24h unattended while Mac awake/network available
- GPT consumer: hourly
- Gmail idempotent delivery once GPT consumes event

### 不可以承诺

- GPT 1-5 分钟内最终判断
- Solana public RPC 100% uptime
- 免费全量 X social firehose
- Mac sleep/offline 时继续采集
- 任意网页 source 永远不变

如果业务要求“Monster/NFT 机会必须在 5 分钟内由 GPT 判断并邮件”，完全免费的当前 ChatGPT automation 架构判定为 **NOT FEASIBLE**；需要改变触发/调用方式。

## 18. 开发者必须先回答的 Go/No-Go 问题

开始写代码前必须给出书面答案：

1. 是否接受 GPT 最坏近 1 小时判断延迟？
2. 是否接受 Solana public RPC 无 SLA 且不配置 fallback？
3. Monster 需要的最大可接受 alert latency 是多少？
4. NFT local scope 是否接受“configured/known sources + GPT broad discovery”，而非免费 X 全量实时？
5. Mac 是否能长期接电并禁止 system sleep？
6. GitHub transport 的最大可接受 sync lag 是多少？
7. health failure 需要什么独立告警渠道？仅 GitHub health 是否足够？
8. historical Frank replay 是否与 live consumer 分离执行？

这些未确认前，不得把项目状态标成 IMPLEMENTATION_READY。

## 19. 当前任务状态约束

截至本文创建：
- `美股每日晨报`：保持启用
- `Crypto 每日情报`：保持启用
- `全项目空投与TGE监控`：保持启用
- `$300 Crypto资产状态监控`：停用
- `Frank 30D 全量回测`：停用
- 其他原已停用任务：保持停用

不得在开发验证阶段私自重新启用 $300 / Frank automation。

## 20. 交接结论

这不是一个“大数据”问题。

普通 Mac 足够处理：
- 5 个主流币实时价格；
- 数百 Binance futures symbols 的 lightweight screen；
- Frank 地址增量 Solana RPC；
- 几十个 NFT configured sources；
- SQLite 状态与队列。

真正要防的是：
- source/rpc failure；
- Mac sleep；
- scheduler latency；
- GitHub sync failure；
- GPT input 过大；
- candidate backlog；
- Gmail send 成功但 receipt 失败；
- source gap 被误写成 NO_ACTION。

所以开发重点必须是 **durability + observability + idempotency + bounded GPT input**，而不是继续堆搜索来源或 prompt。

只有可量化 Gate A-H 全部 PASS，才能说“功能正常”。
