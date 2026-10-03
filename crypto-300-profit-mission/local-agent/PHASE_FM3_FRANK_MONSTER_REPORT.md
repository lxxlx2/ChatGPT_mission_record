# PHASE_FM3_FRANK_MONSTER_REPORT

PHASE_FM3 = PARTIAL

Evidence snapshot UTC: 2026-10-03T03:34:35.441075+00:00

FRANK_SHADOW_READY = PASS；FRANK_ACTIVE_E2E = PASS。MONSTER_D1_V2 = NEEDS_REDESIGN：所有 243 个 TRAIN 配置均超过 candidate ceiling，winner = NONE，不能打开 holdout 评价或启动 D2 shortlist / D3。PRODUCTION = NO_GO。

## Required 54 fields

| # | Field | Actual result |
|---:|---|---|
| 1 | LaunchAgent | `com.jerson.crypto-monitor-frank-shadow`；enabled / RUNNING；恰好 1 个 Frank agent，Monster agent = 0 |
| 2 | uptime | 当前进程 0.05 h；从首次启动 2026-10-02T22:02:49.509370+00:00 起观测跨度 5.53 h；中间有记录的受控重启 |
| 3 | polls | 664；service RPC requests 671；默认 cadence 30 s；独立人工 RPC/readback 复核另计 |
| 4 | new signatures | 5 |
| 5 | real ACTIVE | 1 |
| 6 | real candidates | 2（同一真实 ACTIVE 的 2 个 mint candidate） |
| 7 | active E2E | `FRANK_ACTIVE_E2E_PASS`；独立官方 RPC 重取和 private batch readback 均通过 |
| 8 | latency | 首个 ACTIVE：detection 27.010 s；normalization 0.175 s；candidate 0.203–0.206 s；transport 19.907–19.910 s；total 47.297 s |
| 9 | RPC errors / 429 | errors 0；429 0；timeouts 0；retry 0 |
| 10 | gap | current 0；unresolved 0；candidate duplicate 0 |
| 11 | restart | 8 次重启；真实 ACTIVE 后重启 PASS；候选/观测/batch 数和远端 current blob 不变；SQLite integrity = ok |
| 12 | history progress | 6105/18,203（起点 4,724）；parsed 6105；unavailable 0；本次读取的 latest ERROR 0。机械分类：ACTIVE 473、PASSIVE 4171、UNKNOWN 601、FAILED transaction 857、TRANSFER_OUT 3 |
| 13 | private transport | `runtime-v2-test/frank-forward-shadow/20261002T220249Z/`；1 batch / 2 items；exact readback、hash、identical republish zero writes、restart dedupe PASS；production = 0 |
| 14 | Frank status | `FRANK_SHADOW_READY` + `FRANK_ACTIVE_E2E_PASS`；LaunchAgent 继续后台运行 |
| 15 | V2 freeze | spec `b5ac7ab`；先推送的含 spec ancestor `30335ed0ef776cc30bad7400a5072d4e1f08bb6f`；本次 TRAIN 拒绝决定冻结于 `b4d8adf6ee583d3e668fbad98851186a4f365e0d` |
| 16 | historical period | TRAIN 2021-01-01–2023-12-31；VALIDATION 2024-01-01–2024-12-31；warm-up 2020-10–12；2025–2026 仅 EXPOSED_DIAGNOSTIC。2024 下载/预处理完成，GT outcome/指标未评估 |
| 17 | instrument count | inventory 1,724；历史非空 954（Spot 519 / Futures 435）；770 个无本区间归档；总有效 1h bars 19,160,427 |
| 18 | entity count | 657 个保守 entity IDs；802 instruments 使用 verified exact base 身份，152 个歧义 instrument 保持独立；歧义 ID 不能称为已核实独立 token |
| 19 | >=5X events | TRAIN instrument 20 / entity 20；VALIDATION 未评估 |
| 20 | >=10X events | TRAIN instrument 7 / entity 7；N<10，不能称 10X 已验证；VALIDATION 未评估 |
| 21 | >=20X events | TRAIN instrument 2 / entity 2；仅 descriptive；VALIDATION 未评估 |
| 22 | D1 pathways | A Momentum breakout / B Volume ignition / C Old-shell reactivation / D New-listing ignition / E Relative-strength acceleration；独立 OR |
| 23 | configs | 243 个 frozen TRAIN configurations；ceiling eligible = 0；winner = NONE；未扩大网格或重选年份 |
| 24 | D1 train recall | 无赢家。最低流量 TRAIN 诊断 V2-237：entity / instrument >=5X 20/20、>=10X 7/7、>=20X 2/2（均 100%）；它仍然流量超限，不是可部署配置或 holdout 证明 |
| 25 | D1 validation5X | NOT_RUN_NO_ELIGIBLE_TRAIN_WINNER；不借用 TRAIN 100% 填充 validation |
| 26 | D1 validation10X | NOT_RUN_NO_ELIGIBLE_TRAIN_WINNER |
| 27 | D1 validation20X | NOT_RUN_NO_ELIGIBLE_TRAIN_WINNER |
| 28 | before2X | 最低流量 TRAIN 诊断：>=10X strict-before2X 7/7；VALIDATION 未评估，N=7 不足 10X 验证 |
| 29 | lead time | 最低流量 TRAIN 诊断：>=5X entity median lead-to2X 119.5 h、lead-to5X 144.5 h；>=10X lead-to2X 143.0 h。GT 允许 anchor 前 24h 到峰值窗口内 activation，非执行收益预测 |
| 30 | D1 median entities/day | 全网格范围 148–327；最低流量 148 > gate 100；instrument median 175 |
| 31 | D1 p95/day | 全网格范围 215–376；最低流量 215 > gate 150；instrument p95 264；TRAIN 1,095 天含零候选日 |
| 32 | V1→V2 improvement | OR 高召回结构和分块内存管线已实现；TRAIN recall 描述性提升，但 V1/V2 时段、样本及口径不同，不能据此宣称验证性能改善。V1 NEEDS_CALIBRATION 永久保留；V2 流量 gate FAIL |
| 33 | MMT diagnostic | EXPOSED V2-001：Spot/Futures 均 A path，2025-11-04 19:00 UTC，2X 后 4h；V1 range 条件失败。2 instrument misses，身份与区间满足规则后 1 entity sequence；仍为晚报 |
| 34 | AVNT diagnostic | EXPOSED V2-001：A path，2025-09-09 22:00 UTC，2X 前 19h；V1 return/range 失败；不参与 validation |
| 35 | BTW diagnostic | EXPOSED V2-001：A path，2026-06-04 21:00 UTC，2X 前 3h；V1 range 失败；不参与 validation |
| 36 | D2 endpoint availability | 真实 public REST / archive audit PASS。当前 OI 与近期统计可得；2021 统计 REST 5 项 HTTP400；2021 metrics/funding/mark/index ZIP 及 CHECKSUM 实际通过。BTC 样本不是全 universe coverage |
| 37 | D2 historical features | 已核实样本：archive OI/ratios/taker、funding、mark/index aligned basis；verified dual venue aligned candles；causal path/persistence/quote/age。实际评分实现只用 cheap structure，未把 derivatives 样本扩称全历史 feature coverage |
| 38 | D2 forward-only features | 短保留 REST OI/taker/global/top ratios/current basis、current order-book liquidity；历史不能用 current-only snapshot 替代。prior spikes 未计算，在 candidate 中显式缺口 |
| 39 | D2 median shortlist/day | SKIPPED_D1_TRAIN_GATE；未测量，不写 0 来冒充低噪声 PASS |
| 40 | D2 recall retained | SKIPPED_D1_TRAIN_GATE；source audit 不等于 D2 recall PASS |
| 41 | D3 duration | 0 h；D1 ceiling 未达 gate，因此未启动条件授权的 >=4h D3 |
| 42 | D3 candidates | NOT_STARTED；无 real forward Monster candidate |
| 43 | Monster transport | NOT_STARTED；未写 monster-forward-shadow private 路径；未安装 Monster LaunchAgent |
| 44 | Monster status | `MONSTER_D1_V2_NEEDS_REDESIGN`；GT V2/spec 冻结、expanded history、TRAIN、D2 source audit COMPLETE；VALIDATION / D2 shortlist / D3 按 frozen gate 跳过 |
| 45 | pytest | Python 3.14：362 passed / 1 optional NumPy module skipped；Python 3.12：362 passed / 1 skipped；NumPy Python 3.13：372 passed。起点 baseline357 双版本通过；compileall / 两环境 pip check / diff check / credential scan PASS |
| 46 | Frank CPU/RSS | 91 个采样：平均 CPU 0.230%、峰值 4.2%；平均 RSS 48.49 MiB、峰值 54.39 MiB |
| 47 | Monster replay CPU/RSS | authoritative prepare peak RSS 155,746,304 B (148.53 MiB)，TRAIN 199,671,808 B (190.42 MiB)。同结果 TRAIN 资源复核 mean CPU 99.95%，采样 peak CPU 100.0%，peak RSS 139.31 MiB；均 <1 GiB，优于 V1 ~4.31 GiB |
| 48 | disk | FM2 + FM3 logical bytes 4,400,038,021 (4.098 GiB) < 5 GiB soft budget；保留原始 ZIP/CHECKSUM、2 个 rejected archive 和原始 TRAIN 结果；资源复核复用 SQLite，未复制 raw |
| 49 | Gmail | 0；App alerts = 0；GPT calls = 0 |
| 50 | automation mutations | ChatGPT / $300 automation mutations = 0；唯一明确授权的本地 Frank LaunchAgent creation = 1；Monster LaunchAgent = 0 |
| 51 | production writes | 0；钱包操作 / 交易 / portfolio mutation = 0 |
| 52 | branch | `codex/crypto-monitor-design-20260930`；merge --no-ff 保留历史；无 rebase/force push |
| 53 | SHA | 本报告验证 implementation / TRAIN decision commit `b4d8adf6ee583d3e668fbad98851186a4f365e0d`；最终包含报告的提交 SHA 见交付回复，避免自引用 commit hash |
| 54 | next gate | 提交评审 FM3 PARTIAL：Frank ready + real ACTIVE E2E PASS；Monster TRAIN ceiling FAIL。新一轮 D1 redesign / 新 frozen grid 需评审授权；保持 2024 outcome holdout 未评估，禁止自行换第二名、放宽 ceiling、启动 D3 或生产 |

## Evidence and limits

GT V2 TRAIN discovery retained 1920 instrument episodes and 1615 entity episodes. Cumulative >=2X / >=3X / >=5X / >=10X / >=20X entity counts are 1615 / 77 / 20 / 7 / 2. Eligible TRAIN anchors 12,228,043; segment-right-censored anchors 358,713; additional episode split-right-censor exclusions 8. Frozen V1 objective tiers, future-only offline labels, 7d window, refractory and gap semantics remain unchanged. Eleven >=5X instrument episodes have extreme intrahour-range flags and nine have low-anchor-liquidity flags; flags overlap and were not used to redefine GT or tune the screen.

Expanded source inventory contains 1724 instruments, including empty/unavailable-in-period listings. Verified monthly archive count 26,682; two checksum-valid archives failed candle-contract validation: BTCUSDT_210326 February2021 and AUDUSDT November2020. Their original ZIP/CHECKSUM and rejection receipts are preserved privately. No synthetic bars fill these gaps.

Spec freeze was committed/pushed before 2021–2024 expansion. The initial pre-expansion streaming probe processed 1,651 files / 17,093,461 bars at about135 MiB RSS; the later full16-feature/243-slice probe measured about123 MiB. The latter happened after download started and is not presented as pre-expansion proof. Full expanded preprocessing and TRAIN now independently meet the memory gate. The original CPU sampler stopped on an atomic temporary-file rename; its failure log is preserved. A separate, unchanged TRAIN replay supplied CPU measurement and byte-identical grid/winner results. It did not evaluate validation, revise parameters or change selection.

2024 candle acquisition and causal preprocessing are explicitly permitted by the pushed D1 V2 spec. No 2024 GT outcomes or metrics entered selection; no validation outcome file was created. PROJECT_UNEXPOSED_BEFORE_V2 means this project had not searched that history for V2, not globally unseen. Existing V1 2024Q4 warm-up archives were reused with provenance. The TRAIN rejection and skipped gates are recorded in config/monster_d1_v2_winner.json, monster_d2_v1_winner.json and monster_v2_validation_gate.json.

The real Frank ACTIVE occurred after the prior WAITING snapshot. Official RPC was independently re-requested and normalized exactly against the durable raw/evidence; the private remote batch was independently read back exactly. The first batch ID inherits the baseline install_namespace prefix synthetic-local-v1; that metadata string does not indicate synthetic payloads. Both transported items bind to one official real finalized forward ACTIVE observation. Original batch bytes are preserved. Full signatures, transaction bodies, mint details, remote receipts and raw responses remain in the private evidence root, not this Git report.

Frank available-history lifecycle snapshot: active mints 147; observed round trips 116; observed reentries 19. First available blockTime 1789061246; last available-history ACTIVE blockTime 1790724124. Scope is referenced token accounts in available history, not wallet lifetime entry/exit or PnL. Lifecycle snapshot precedes the slightly later progress count; neither is a fabricated lifetime total.

Private evidence root: /Users/jerson/Documents/ChatGPT/crypto-monitor-fm3-evidence-20261001. Key files: monster-v2-freeze.json; monster/expanded-coverage.json; monster/train-grid-results.json; monster/train-winner.json; monster/train-gt-coverage.json; monster/prepare-resources.json; monster/train-resources.json; monster-resource-recheck/train-resources.json; monster/d2-audit/endpoint-audit.json; frank/shadow/active-e2e-independent-readback.json; frank/shadow/post-active-restart-after.json; frank/shadow/health.json; fm3-final-snapshot.json. The dated root name is an identifier; actual evidence timestamps are October2–3 UTC.

Related source-backed documentation: docs/FRANK_SHADOW_FM3.md; docs/MONSTER_D2_SOURCE_AUDIT_V1.md; docs/MONSTER_V2_EXPOSED_DIAGNOSTICS.md. D2 audit uses current official [Binance market-data documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) and [public-data publication/checksum documentation](https://github.com/binance/binance-public-data), plus actual private raw endpoint/archive receipts. Archive capability does not imply all candidate coverage.

Frank LaunchAgent remains active after interactive completion. Manual Monster download / preparation / TRAIN / resource recheck jobs are bounded and finished. No Monster scanner or scheduler has been installed.

CORE PRICE V3 = PAUSED

NFT = NOT STARTED

$300 AUTOMATION = DISABLED

PRODUCTION = NO_GO
