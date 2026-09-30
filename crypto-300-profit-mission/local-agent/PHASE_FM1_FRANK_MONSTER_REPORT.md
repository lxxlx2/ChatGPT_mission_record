# PHASE_FM1_FRANK_MONSTER_REPORT

PHASE_FM1_PARTIAL

2026-09-30。主线已改为 Frank → Monster。当前交付是真实官方数据获取、保守 evidence parser、历史 candidate queue/private test transport，以及 Monster universe/history inventory。**尚未完成 Frank 50 笔人工验收、真实 forward 验收和 Monster D1/D2/D3；不构成 FM1 PASS 或 production readiness。**

## FRANK

### 官方来源与 archival probe

钱包：`498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`。
Canonical source 仅 `https://api.mainnet.solana.com`。getSignaturesForAddress/getTransaction 使用 finalized；getTransaction 使用 jsonParsed、maxSupportedTransactionVersion=1。版本值按 [Solana 官方升级说明](https://solana.com/upgrades/larger-transaction-sizes)、[getTransaction](https://solana.com/docs/rpc/http/gettransaction) 和 [getSignaturesForAddress](https://solana.com/docs/rpc/http/getsignaturesforaddress) 核实。

本轮签名分页快照发现 **18,203 unique signatures**；没有把旧记录 7,106 写成当前事实。六个位置为 newest、第25条、25%、median、75%、oldest，零基索引分别为 0/24/4550/9101/13651/18202。六个 transaction 均 available，均通过完整性 normalizer 检查，RPC error 均为空。Oldest sampled transaction：slot 364489259，blockTime 1756944380（2025-09-04T00:06:20+00:00）。Probe 请求27次、重试1次。

**F-A=PASS（六点 probe）；F-B=PARTIAL（六点 available，全18,203笔 availability 尚未测试）。** 没有证据认定全历史 NOT_FEASIBLE，也没有证据认定全历史完整。未启动全历史 transaction fetch；先完成500 gate。

### 最近500笔真实结果

统计采用 immutable `processing-v4/process500-summary.json`，覆盖 2026-09-27T17:19:48+00:00 至 2026-09-30T09:39:20+00:00。

| 指标 | 实测 |
|---|---:|
| requested / available / parsed | 500 / 500 / 500 |
| RPC unavailable / request failure | 0 / 0 |
| parser errors / queue errors | 0 / 0 |
| ACTIVE_SWAP_LIKE | 13 |
| PASSIVE_RECEIPT_LIKE | 368 |
| TRANSFER_OUT_LIKE | 1 |
| UNKNOWN | 118 |
| 其他机械标签 | 0 |
| on-chain failed（包含在UNKNOWN中） | 4 |
| UNKNOWN且钱包为signer | 72 |
| wallet-owned mint数量 | 115 |
| active mint数量（含USDC对价） | 10 |
| active per-mint clusters / HFT clusters | 21 / 0 |
| raw candidates | 12 |
| 初次处理 duplicate records | 0 |
| 全500笔重复入库 | 500 DUPLICATE；unique evidence仍500 |

Raw acquisition实际541 requests、41 retries、744.63秒；请求间隔下限0.5秒，429/timeout最多3次请求，带backoff/jitter。原始缓存为gzip，重启复用逐文件检查身份和status，完整写入后fsync再独占发布；临时文件不会被当成已发布数据。

Evidence set SHA256：`205b0db8d37f144b1eeb0c1a3e040e2282237af7d513fccdc9209b09a539c065`。原始交易、签名列表、review packet、SQLite和cache manifest放在仓库外私有 evidence root，不写入Git。

### Parser修正与准确性边界

使用整数 raw token amounts，按accountIndex连接pre/post，保留mint/owner/decimals，wallet不拥有的delta不能算成其持仓。具体authority evidence保存outer/inner位置、program、type、field和account；initializer owner或approve recipient delegate不会被当成执行授权。Memo的parsed string、version legacy/0/1、token account creation/closure和失败交易均有处理。

当前DEX覆盖仅官方代码声明的 [Raydium AMMv4](https://github.com/raydium-io/raydium-amm/blob/master/program/src/lib.rs) 与 [Jupiter v6](https://github.com/jup-ag/jupiter-cpi/blob/main/src/lib.rs)。ACTIVE_SWAP_LIKE要求signer或具体authority、已识别DEX、swap/route instruction evidence以及不同wallet-owned mint的相反经济delta。未知程序内CPI transfer保持UNKNOWN，不直接称为普通转出。原生SOL包含账户租金；未解码出可靠swap consideration之前，token/SOL相反方向仍保持UNKNOWN。没有PnL、美元估值或投资判断。

初始尝试曾有raw uiAmount float哈希、parsed memo string、candidate超过2KB的问题，修正后分别保留旧attempt。本轮进一步收紧unknown-program transfer和native SOL/rent判定，最终以v4为准；v2/v3不是最终验证身份。

自动独立重算500笔：token integer delta、signer、SOL lamport delta均500/500一致；不能把它写成classification或authority accuracy 100%。

### 人工核验和生命周期

分层/随机review packet有50项，seed=20260930，覆盖active/passive/unknown、复杂inner、SOL-only或零token变化、较大raw unit变化；raw units跨币不可当成统一经济交易规模。**完整四轴人工核验=0/50；独立explorer pilot=2笔，authority审查未完成。** Classification/token delta/signer/authority agreement在要求的50笔人工样本上均未测得。

Pilot发现explorer swap summary的USDC gross与钱包净USDC余额变化不同；钱包net delta使用raw余额差，并在explorer Balance Changes中检查。两次pilot不能替代50笔验收。

机械候选仅描述RECENT_500_ONLY中first active observation或observed account balance zero exit。不能据此认定first lifetime entry、完整wallet-wide exit、holding duration、subsequent add、round-trip或历史收益。主动mint事实频次：

| Mint | active transaction出现次数 |
|---|---:|
| `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` | 13 |
| `7M3gDRgozcumFsiTeXwjB8cYxpg7Q9R7rH7rkw2Fpump` | 3 |
| `CARDSccUMFKoPRZxt5vt3ksUbxEFEcnZ3H2pd3dKxYjp` | 3 |
| `3iUTyNYW6xKv5kZUjtbrEDTsuJTrSVwvB3bQtxkLpump` | 1 |
| `7MYpDaZ1Uorg1QtkjWK25X2K4UoNk88854jfopAXxNKs` | 1 |
| `A71Uf3jwg57fNedSao9eFwm9eKSLYFbVJ85T4fuXpump` | 1 |
| `A7iQ8N5jKDrg1YUxJ7v8aN5AtkwJaUTNhq1jZ8YLFrAJ` | 1 |
| `C1mBfBoDkwWfd6uTFZp62ARHLjeVp3bDpCDMfMZtPngE` | 1 |
| `HCy7vxTApN2Lcv6Rw1MZazXsEofXFLxWCVbJBhF8pump` | 1 |
| `ZesMGYmokFiEuDvNzWeMhB7jxF6eUW8c512vwSKSTNK` | 1 |

USDC 13次是对价出现频次，不代表13次买入USDC；其余9个mint同样只报告出现次数，不推测买卖倾向。

Cluster按mint、已识别program、连续间隔<=60秒确定；>=3 transaction标HIGH_FREQUENCY_CLUSTER并抑制独立raw candidate。本样本无HFT cluster。各mint cluster的SOL context可能重复，不能跨mint相加当作总成本；账户间同mint转移和gross flow还需50笔人工验收覆盖。

### Forward、queue和真实private transport

Forward为手动skeleton，初始化明确要求500 parsed、>=50 independent explorer reviews和parser error=0；没有传入虚构PASS，没有开启真实forward。带durable cursor、分页boundary检查、missing boundary明确报gap、raw先fsync、SQLite atomic evidence/cursor、restart与dedupe。已修复cached historical duplicate不推进cursor的问题，重复内容校验与cursor推进现在同一事务提交。

真实new signature test=NOT_RUN；detection p95、normalized latency、cursor gap均N/A。合成故障测试中的cursor gap=0不能写成真实forward gap=0。当前skeleton尚未连接forward事件到candidate生成，acceptance input尚需绑定不可伪造的实际review receipt；FRANK_FORWARD_READY尚未成立。

最终12个历史RAW_FRANK_CANDIDATE进入既有SQLite candidate/outbox/delivery tables，event_id为frank namespace，payload有证据hash和sample-scoped context，禁止投资判断。被动接收不成为candidate。

真实 private transport：`lxxlx2/crypto-monitor-runtime` / `mac-data` / `runtime-v2-test/fm1-frank-rent-safe-20260930-01`。12 items，batch **19,843 bytes**，最大完整item **1,636 bytes**，满足75KB/2KB限制。remote hash/readback一致；新client restart readback通过；相同batch再次publish新增commit=0。最终run真实write commits=2，read commit=`852ce4fdc1b62d6819544e3a609a2a51605038c1`。v2/v3/v4三个独立test runs累计6个test-only commits，旧run未覆盖或删除。

继承batch_id `synthetic-local-v1:000000000001` 的安装命名；本批payload来自真实官方RPC，不能因ID名称写成合成链上数据。Offline validator验证12项schema/identity/hash/size；decision generated=false，delivery generated=false。原Phase1 synthetic-only consumer保持不变；未声称已完成真实GPT scheduled consumer。

### Frank acceptance gates

| Gate | 状态 | 依据/缺口 |
|---|---|---|
| F-A official probe | PASS | 6/6 available且结构完整 |
| F-B archival availability | PARTIAL | 六点可取；全历史尚未逐笔测试 |
| F-C 500 processing | PASS | 500 parsed，0 parser/queue errors |
| F-D >=50 manual validation | PENDING | 0/50完整审查；2 pilot |
| F-E active/passive accuracy | PENDING | classification/authority误差尚未测得 |
| F-F cursor/restart/dedupe | PARTIAL | 合成故障和真实500重复回放PASS；live cursor未验收 |
| F-G forward new signature | NOT_RUN | 手工parser gate未通过 |
| F-H candidate queue | PASS历史路径 | 12真实历史候选；forward生成未接通 |
| F-I private transport | PASS历史路径 | 最终12项真实test namespace readback/restart/dedupe |

## MONSTER

### 真实universe与historical coverage

此处仅M1 read-only inventory准备，不把它写成Frank500 gate已通过后的Monster模型并行开发。未依赖Price V3，也未运行Monster heavy enrichment或forward。

| 官方来源 | 全部records | TRADING records |
|---|---:|---:|
| [Spot exchangeInfo](https://data-api.binance.vision/api/v3/exchangeInfo) | 3,713 pairs | 1,367 pairs |
| [USDⓈ-M Futures exchangeInfo](https://fapi.binance.com/fapi/v1/exchangeInfo) | 919 contracts | 787 contracts |
| [Alpha exchange info](https://www.binance.com/bapi/defi/v1/public/alpha-trade/get-exchange-info) | 1,458 pairs | 707 pairs |
| [Alpha token list](https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list) | 682 token records | N/A，source无统一TRADING status |

上述是pairs/contracts/token records，未做跨venue去重，不能相加成为unique token数量。官方接口范围参照 [Alpha market data](https://developers.binance.com/en/docs/catalog/advanced-trading-alpha-trading/api/rest-api/market-data) 和 [Binance public data](https://github.com/binance/binance-public-data)。

官方public archive目录完成pagination：Spot **3,710 symbols / 4 pages**，USDⓈ-M Futures **1,018 symbols / 2 pages**。历史目录中不在当前TRADING集合的Spot **2,371**、Futures **269**。这些是symbol差集，可能包含下架、报价币变化、inactive状态或合约差异；不能写成精确delisted token数。

SURVIVOR_BIAS_LIMITATION：delisted candles available/unavailable=NOT_PROBED；没有逐symbol证明bar完整性；Alpha历史archive未建立。目录list complete仅指本次目录分页完成，不等于全历史market data complete。

### Ground truth / D1 / D2 / D3

Ground truth有效案例=0，约10个英文市场/社交来源历史案例尚未建立；2x/3x/5x/10x/20x分布均NOT_ESTABLISHED。24h/72h/7d event windows和未来标签隔离已在stage contract列为必需约束，但ground truth计算未实现，未冻结阈值。

D1 price/volume/BTC-relative causal replay=NOT_IMPLEMENTED；monster events、pre-hit、missed、recall、median/p25/p75 lead、candidates/day、false candidate proxy和逐个miss分析均N/A，不能写成0% recall或0 false positives。

D2尚未开始。OI/OI history/funding/taker/top/global long-short/mark-index endpoints加入read-only source allowlist；真实endpoint availability未逐一验证。合成404测试只能证明unavailable不会被当作数值0，不能宣称D2可用或已降低噪声。

D3 forward shadow=0小时；真实forward candidates=0；无Monster真实candidate private transport。通用queue adapter支持monster namespace/source，尚无Monster历史或forward端到端候选验收。没有Price V3依赖，缺口来自Frank先行验收顺序和Monster自身未实现步骤。

### Monster acceptance gates

| Gate | 状态 | 依据/缺口 |
|---|---|---|
| M-A current universe | PASS | 四个官方接口真实读取 |
| M-B history/survivor bias | PARTIAL | Spot/Futures历史目录完成；delisted candle availability未测 |
| M-C ground truth | NOT_DONE | 0 verified cases |
| M-D D1 replay | NOT_DONE | 未实现 |
| M-E metrics | NOT_DONE | N/A |
| M-F misses | NOT_DONE | 尚无replay可供分析 |
| M-G derivatives availability | NOT_DONE | 仅allowlist和合成failure test |
| M-H >=2h forward | NOT_RUN | 上游model gate未成立 |
| M-I candidate queue | PARTIAL | 共用adapter；无真实Monster候选 |
| M-J private transport | NOT_RUN | Frank传输不替代Monster验收 |

## SYSTEM / PROVENANCE / RESOURCE

基线branch：`codex/crypto-monitor-design-20260930`；本轮开始HEAD：`ec7a2ca02c59b27ad0f344ba2d843f476301fb9b`。fetch后origin/main=`e6a2fa3c7f806f75e8d367c89b4f7fa354483bde`，没有待合并main提交；未rebase、未改main。既有freeze/winner/forensic身份和Price V1/V2/V3草稿全部保留。

V2 freeze=`15753ad1092cc2b1b9bd36270dd770916c50aec0`；V2 winner=`0b3d0cff2199c2bab42d07b42d4e5b8b9259e654`；forensic freeze=`e30dd63c262d9575aec5be799de14fd6036eac09`。本轮只新增FM代码/tests/docs/report，开始时1,580 tracked repository paths（其中106 local-agent paths）均未改写。

Baseline Python3.14/3.12均282 passed，0 failed、0 skipped。最终Python **3.14.6：334 passed / 2.14s；3.12.14：334 passed / 2.04s**，0 failed、0 skipped。新增52tests。compileall和pip check两版本均PASS。Credential token-boundary pattern scan=PASS，0 hits；宽泛sk子串初扫匹配两个旧文章URL内单词，边界校正后无credential-shaped token，未输出匹配内容。

Frank覆盖429、timeout、null、duplicate/out-of-order、restart、SQLite lock、partial commit/parser metadata、legacy/0/1、unknown program、token close、SIGKILL rollback、cache atomic publication等。Monster覆盖timeout/429、partial symbol、重复symbol、新/非活跃symbol、应用错误、derivative404；**missing/duplicate candles、真实delist mid-run、collector restart/stale universe/BTC missing尚未完成**，因为replay/collector未实现。不得宣称完整Monster failure gate PASS。

500结构重算/重复回放实测 wall=0.22858550000819378s、CPU=0.22782999999999998s、peak RSS=45,187,072bytes（约43.1MiB）。这是短任务，不是持续collector平均CPU。私有evidence占用 **63,091,434 bytes**（约60.2MiB），5GB budget使用约1.26%，HEALTHY_DISK。没有持续CPU<10%或RSS<500MB的forward测量，资源gate不得写PASS。

5GB、80% DEGRADED/95% UNHEALTHY检查已有测试。缓存gzip+immutable manifest已实际生成；本轮不自动删审计证据。未来Monster aggregate retention/滚动压缩尚未实现。

Health当前Frank rpc_available=true表示本次获取成功、last_signature_age为已抓历史年龄，queue pending=0（12候选已publish）。cursor_gap和live normalized age为null；Monster market_data_age/candidate_scan_age/derivatives_age和symbols_failed均null。Universe size有真实库存。null不是0；不把静态inventory报告成collector healthy。

Gmail sends=0；ChatGPT App alerts=0；automation mutation=0；$300 monitor enable=0；production runtime-v2 writes=0；新增LaunchAgent=0。Private transport写入仅runtime-v2-test。没有真实GPT decision或delivery receipt，不推进既有delivery state machine到已送达。

## 未来GPT contract与下一验收gate

Frank输入：原始证据hash、active/passive/unknown证据、明确sample scope的history context、经验证的token lifecycle、trade size单位、cluster、wallet baseline；未知价格/生命周期必须为null或NOT_PROVEN。Monster输入：price/volume/BTC relative anomaly、可靠derivatives、历史模式与因果feature window、liquidity/risk和数据缺失状态。未来labels绝不进入live features。

GPT允许输出IGNORE/WATCH/ACTIONABLE_RISK/ACTIONABLE_OPPORTUNITY；Frank可额外ENTRY_LIKE/ADD_LIKE/EXIT_LIKE。Mac只产生机械raw evidence；本轮没有这些真实GPT判断。Scheduled consumer仍需用户单独授权。

下一gate：先逐项完成processing-v4的50笔rawRPC+explorer人工四轴核验，量化误差并修parser；绑定review receipt后接通forward candidate生成，手动真实new signature/restart/network recovery测试并测p95<=30s、normalize<=60s、gap=0、duplicate=0。Frank500 gate PASS且forward skeleton稳定后，继续Monster约10真实历史案例、因果D1 replay/recall/lead/load，再D2、真实>=2h D3及Monster候选private test transport。无需等待Price V3或全18,203笔完成。

正式报告与代码commit的最终SHA在最终回复和仓库外handoff receipt记录，避免在同一commit的report内制造自引用SHA。

Private evidence root：`/Users/jerson/Documents/ChatGPT/crypto-monitor-fm1-evidence-20260930`。
最新Frank evidence目录：`/Users/jerson/Documents/ChatGPT/crypto-monitor-fm1-evidence-20260930/frank/processing-v4`。
旧attempt保留；最终身份绑定processing-v4 evidence hash和当前代码commit。原始签名/交易只存private evidence，不在公开Git报告列出。

CORE PRICE V3 = PAUSED

NFT = NOT STARTED

$300 AUTOMATION = STILL DISABLED

PRODUCTION = NO_GO
