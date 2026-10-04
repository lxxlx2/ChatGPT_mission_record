# Frank trade coverage historical replay — 2026-10-04

本轮只做隔离历史研究。确认 19 笔用户交易被 CURRENT 分类为 UNKNOWN；恢复后新增 1 个 ACCUMULATION 和 1 个 MULTIPLE，同时 STONK 的补齐买入触发原 sticky HFT，移除其原 MULTIPLE。MULTIPLE 总量不变不能解释为没有新增信号。生产代码、阈值、HFT、服务和通知均未修改。

## 数据与 CURRENT parity

窗口：2026-09-03T16:32:58+00:00 → 2026-09-30T09:39:20+00:00。6874 个唯一签名，raw missing=0，raw hash verified=6874；仅为 available verified subset，不是 wallet lifetime。chronology SHA256：`7dd4cb90f0dc3bcd3d527421742fa45b55ac1807967deb4f81f7ee30b20f6ed3`。

| Classification | Count |
|---|---:|
| ACTIVE_TRADE | 634 |
| PASSIVE_TRANSFER | 4433 |
| ATA_CREATE | 265 |
| FAILED_TX | 900 |
| FEE | 0 |
| UNKNOWN_NEEDS_REVIEW | 642 |

ACTIVE quote：USDC=625，SOL=9，other=0。原始分类重新验证；CURRENT 与既有 verified V1 replay 的 31 个信号精确一致：ACCUMULATION=21、MULTIPLE=10。无 BASELINE_DRIFT。

## 方法与因果约束

四模型均使用原 production engine/evaluator/policy、原 sticky HFT、rapid roundtrip、persistence、inventory、distribution、freshness。一个 signature 最多恢复一笔用户交易，不按 CPI hop 计数。市场绑定要求官方 program ID、实际 invocation 调用栈及该程序自身 Swap 指令日志，再核对 Frank signer、success、owned net flows 和一个明确目标资产。没有阈值调整、未来 PnL 筛选、dust 删除或未证实 opcode 猜测。

SOL 使用 Coinbase Exchange SOL-USD 60 秒 candle 的前一个完整分钟 close；bucket end ≤ transaction time、age <60 秒，拒绝未来/current-minute close、插值与现价。所有估值标记 RESEARCH_ESTIMATE。6 个历史请求均 HTTP 200，receipt 留存 endpoint、获取时间、原响应 hash、candles 与选价时间。后续 replay 复用冻结缓存。USDC 保持原始数量的直接数值比较，不声称独立美元估价。换算的经济金额仅在隔离数据库中作为原金额 gate 的 USDC 数值代理，原 quote legs 完整保留，不能写回 production DB。

[Coinbase candle 官方文档](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles)；市场 program 官方来源：[Orca](https://github.com/orca-so/whirlpools/blob/main/README.md)、[Meteora DAMM v2](https://github.com/MeteoraAg/damm-v2-sdk)、[Manifest](https://github.com/Bonasa-Tech/manifest)。官方 program identity 不等于已证明某笔 swap；缺少 invocation 内可验证指令语义仍保留 UNKNOWN。

## SOL

9 笔 ACTIVE、9 mints，BUY=0、SELL=9；1 个可归属 observed episode、8 个 orphan SELL，不创建虚构 opening BUY。9 笔 amount UNDETERMINED 是已记录交易的金额覆盖缺口，不是 classifier false negative。M1 新增 ACC=0、MULT=0。±2% 全模型回放均 21/10；SOL BUY threshold candidates=0，ROBUST_PASS/BOUNDARY_SENSITIVE/ROBUST_FAIL 对 BUY 信号均无候选，不能把缺少 BUY 样本包装成 robust recall 证明。

## USDT

用户提供的 `Es9vMFrzaCERmJfrF4H2FYDSEVQScAY5NJQTSQ1jD3b` 不是本轮证实的 USDT mint，raw mentions=0。官方 Solana USDT mint 为 `Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB`，依据 [Tether supported protocols](https://tether.to/en/supported-protocols/)。

官方 mint 的 63 笔 raw mentions：59 ACTIVE（40 为 owner USDT net=0、19 非 owner），3 UNKNOWN owner net=0，1 FAILED owner net=0。真实 Frank USDT quote swap=0，USDT_ACTIVE_CASES=0，新增 ACC=0/MULT=0。历史偏离检查 NOT_APPLICABLE_NO_CONFIRMED_WALLET_USDT_QUOTE；没有无条件硬编码 USDT=$1。结论仅限本窗口。

## Complex / other signed routes

CURRENT UNKNOWN=642。候选 47 个唯一 signature：18 个原 AMBIGUOUS_USER_EXCHANGE_ASSETS，另 29 个 Frank 签名、相反 owned flows、未绑定市场程序的交易。研究官方市场绑定后恢复 19 笔（14 BUY、5 SELL），涉及 13 mints、11 known shadow episodes。原 ambiguous 子集仅恢复 3 笔；只审计这 18 笔会漏掉其他市场案例。

| Category | Count |
|---|---:|
| RECONSTRUCTABLE_USER_SWAP | 19 |
| TRUE_MULTI_ASSET_ACTION | 14 |
| LP_ROUTING_INVENTORY_OPERATION | 0 |
| INSUFFICIENT_EVIDENCE | 14 |

14 insufficient 中，12 缺少可审计的实际市场指令证明，2 为 transient WSOL 与 fee-adjusted native 流量不一致。14 true multi-asset 不满足一个清晰 target 的 reduction；不能把它们强行合并为单一 BUY。其余 595 个 UNKNOWN 也未证明为本研究可恢复的用户 swap。仅上述 19 笔计入 confirmed classifier false negatives。每个 candidate 的 owned flows、program combinations、quote legs、分类原因和 predicate 在 JSON 中保留。

## Model comparison

| Model | ACTIVE | ACC | MULT | New ACC | New MULT | Lost MULT |
|---|---:|---:|---:|---:|---:|---:|
| M0 | 634 | 21 | 10 | 0 | 0 | 0 |
| M1 | 634 | 21 | 10 | 0 | 0 | 0 |
| M2 | 634 | 21 | 10 | 0 | 0 | 0 |
| M3 | 653 | 22 | 10 | 1 | 1 | 1 |

M0=CURRENT；M1=历史 SOL 估值；M2=再加入 USDT recognition；M3=再加入证据充分的 complex/other market 恢复。新信号与失去信号均按 episode+signal type 独立比较。M3 的 SOL ±2% 两端仍为 ACTIVE=653、ACC=22、MULT=10；新增两个信号都是直接 USDC 数值路径。新增 observed sequence mints 清单见 JSON 各 model，不将它误写为新增 wallet lifetime position。

## 新增信号逐一审计

两个新信号属于同一 mint `4K1m7gAMDKzrxQn68yuZAd767w57Fw7Ykw69dG3umeta`，episode `32e5cdb79080580d60f21e728998079c511c218886352bfd3f95065153189f88`。没有擅自绑定名称。两个 BUY 原生产均 UNKNOWN / INSUFFICIENT_MARKET_EXCHANGE_EVIDENCE，研究按 Meteora DAMM v2 自身 Swap2 invocation 重建为 ACTIVE BUY。

### FRANK_ACCUMULATION_SIGNAL

Trigger：2026-09-22T17:12:49+00:00；kind=ACTIVE_TRADE；signature=`2352K9kgpndgb9A39xyWGJsCruHgJgVf6PheQECWrSmPfKndKT8uF83DcFoNJaoQrCc8wpiaKdaVCoqTcrmfvzqv`。

First BUY：2026-09-22T17:12:41+00:00，`3yRk6QKSGRs6HNMp3VNt7jUAFRyHA9ZnnuZqcVoKkKqpVB31oDbyiSqCEf6iUNV1UUZ7s6ZcXCmm4rWAebTcKgUf`。第二/最后 BUY：2026-09-22T17:12:49+00:00，`2352K9kgpndgb9A39xyWGJsCruHgJgVf6PheQECWrSmPfKndKT8uF83DcFoNJaoQrCc8wpiaKdaVCoqTcrmfvzqv`；原 quote=10000 USDC，第一笔=15000 USDC；累计25000 USDC，buy_count=2、buy span=8秒、sell_count=0。

Inventory=156402.214732 tokens（raw 156402214732）；distribution=PASS、HFT=PASS、inventory=PASS、persistence=FAIL。

金额使用 USDC direct numeric comparison，无 SOL/USDT conversion。signal/evaluation/完整 causal reconstructed trade prefix、各 gate 与原分类见 JSON。

### FRANK_MULTIPLE_SIGNAL

Trigger：2026-09-22T18:29:00+00:00；kind=HOURLY_29；signature=`2352K9kgpndgb9A39xyWGJsCruHgJgVf6PheQECWrSmPfKndKT8uF83DcFoNJaoQrCc8wpiaKdaVCoqTcrmfvzqv`。

First BUY：2026-09-22T17:12:41+00:00，`3yRk6QKSGRs6HNMp3VNt7jUAFRyHA9ZnnuZqcVoKkKqpVB31oDbyiSqCEf6iUNV1UUZ7s6ZcXCmm4rWAebTcKgUf`。第二/最后 BUY：2026-09-22T17:12:49+00:00，`2352K9kgpndgb9A39xyWGJsCruHgJgVf6PheQECWrSmPfKndKT8uF83DcFoNJaoQrCc8wpiaKdaVCoqTcrmfvzqv`；原 quote=10000 USDC，第一笔=15000 USDC；累计25000 USDC，buy_count=2、buy span=8秒、sell_count=0。

Inventory=156402.214732 tokens（raw 156402214732）；distribution=PASS、HFT=PASS、inventory=PASS、persistence=PASS。

金额使用 USDC direct numeric comparison，无 SOL/USDT conversion。signal/evaluation/完整 causal reconstructed trade prefix、各 gate 与原分类见 JSON。

ACC 使用冻结 Path C 重复买入分支：2 笔、60分钟内累计25000；15000 单笔分支仍 NOT_ACCUMULATION。MULT 在 HOURLY_29 用原 Path A prior hourly WATCH 达成 persistence，触发时没有新 BUY；不能把两笔仅8秒的跨度误称为 Path B 的三笔/45分钟买入。

## Top coverage cases 与已知 winner

1. 上述未命名 mint：两笔原 UNKNOWN BUY 合计25000 USDC，新增 ACC 与稍后 hourly MULT，提供本样本最直接的 entry-signal coverage loss。
2. STONK `6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx`：补齐4笔早期 BUY（epoch 1788661718、1788661729、1788661881、1788662717）；连同原 BUY 1788661711，前3笔跨度18秒触发原 sticky HFT。M0/M1/M2=ACC1/MULT1；M3=ACC1/MULT0。交易覆盖修复可能纠正原有的 HFT 漏识别，不能以 MULT 总量不变为由忽略损失。
3. 原 ambiguous 的 USDC+SOL refund：3GX…pump、4aje…pump、GZik…：USDC支出2500/3500/2500与SOL退款0.225256739/0.282607716/0.000000001合并为净 quote 2476.63637103092/3470.67944946500/2499.99999990091；不删1 lamport，不重复计CPI。没有新增entry signal。

PAID `98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump`：四模型均 ACC3/MULT1，影响=无。Pistacio、PERPSPAD、fone、Pumpcat、CATE 均 UNRESOLVED_NAME_TO_MINT。经济结果 PNL_UNAVAILABLE，不用未来收益判断 BUY 或 signal 应否成立。

## Coverage 与建议

| Module | Coverage | Recommendation | Evidence / missing |
|---|---|---|---|
| SOL | LOW | NEED_MORE_DATA | 9 SELL已ACTIVE、0 BUY，缺SOL BUY金额gate样本 |
| USDT | LOW | KEEP_CURRENT | 本窗口0真实净quote，不能外推所有USDT历史 |
| COMPLEX | MATERIAL | RESEARCH_FIX_CANDIDATE | 19确认漏交易、gross新增1ACC+1MULT；正式实现需另轮设计 |

最大的已证实 classifier coverage loss 是 C：19/634≈3.0%的额外主动交易。M3 与 sticky HFT 的交互减少 STONK MULT。整体仍 NEED_MORE_DATA：12个缺指令绑定、2个native mismatch、14个真实multi-asset不符合当前单target语义；不得称所有UNKNOWN都是漏报，不推荐本轮 production patch。

## Production boundary 与验证

生产 SHA before/after 全部一致，完整清单在 JSON production_boundary。包含 classifier/evaluator/engine/scanner/policy/parser/rpc/V1 config，以及store/service/registry。PID=85524、restart_count=3保持；loaded commit=46c989c3ef35d63fc02808c519f73aa3e6ea1513、source_drift=false。只读现有 health，不做 live validation。

| Health | Before | After |
|---|---|---|
| pid | 85524 | 85524 |
| restart_count | 3 | 3 |
| code_commit | 46c989c3ef35d63fc02808c519f73aa3e6ea1513 | 46c989c3ef35d63fc02808c519f73aa3e6ea1513 |
| last_successful_poll | 2026-10-04T05:59:02.771956+00:00 | 2026-10-04T10:36:14.646449+00:00 |
| source_drift | False | False |
| raw_pending | 0 | 0 |
| model_unprocessed | 0 | 0 |
| loaded_source_sha256 | 599f2f05f197725a25fd85a82501504a772f253866c0556183bbfd82da00a0ce | 599f2f05f197725a25fd85a82501504a772f253866c0556183bbfd82da00a0ce |

PRODUCTION_FILES_CHANGED=NO；LIVE_SERVICE_RESTARTED=NO；LIVE_SIGNAL_SENT=NO；没有Gmail/notification、automation、main merge。PRODUCTION_TRADING=NO_GO。

完整 pytest：570 passed, 3 skipped；13个本研究测试覆盖因果价格、owned净流、USDT脱锚、refund、dust、多资产、CPI去重、native mismatch、市场自身指令日志绑定、原证据不可变、原sticky HFT交互。3个skip为缺numpy的其他Monster测试。

## Reproduce / artifact

Starting research HEAD：`89135131dc1a8ae48890dbe6bfd4b98a03ad2b20`；ending HEAD/remote HEAD 以承载此报告的研究提交及最终回复为准，避免自引用提交hash。

从 local-agent 运行（必须全新 work，已有目录 fail closed；private原始数据与缓存不进public repo）：

```sh
python -m scripts.frank_trade_coverage_historical_replay --source <private>/history-shadow-ledger-verified.sqlite --baseline <private>/v1-history-replay-final.sqlite --work <NEW_PRIVATE_DIRECTORY> --price-cache <private>/frank-trade-coverage-historical-replay-20261004/price-receipts --policy config/frank_local_signal_v1.json --output ../meme/evidence/frank-trade-coverage-sol-usdt-complex-2026-10-04.json
```

helper 生成模型/审计JSON；本报告与 production_boundary/tests 是本次真实运行的封存结果。重复运行 helper 会重新生成模型部分，边界封存应重新只读核验，不能复用旧live状态作为当前证据。
