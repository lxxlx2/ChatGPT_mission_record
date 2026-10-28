# Frank G4 — 一次性正式 MULT / ACC 退出时点历史价格补证结果（2026-10-28）

**实际运行：`ALL_FROZEN_CASES_VISITED / 18_HTTP200 / STRATEGY_NEED_MORE_DATA`。** 这是一轮已完成的**真实公开 GeckoTerminal 分钟 K 线数据采集**，不是未来计划，也不是历史真实可成交报价、跟单净利润回测、独立 OOS 样本或交易建议。

## 1. 执行与来源

- 一次性 [GitHub Actions Run #40663663748](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40663663748)：`event=push`、`run_attempt=1`，workflow 总结果 `SUCCESS`；执行代码固定 SHA `0815303604f61e77e2962fc4bdb25cb380afcfbc`，job `122732652001`。
- [Artifact #12805017729](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40663663748/artifacts/12805017729)：`g4_price_once_receipts.json`，保留 HTTP attempts、响应 SHA256、原始池发现和 OHLCV JSON、冻结选择及全部逐档结果。Artifact 由 GitHub Actions 实际上传，**本次审核通过 job log 与 artifact 元数据确认存在；尚未独立下载并重放原始 ZIP**，不能冒称独立 raw 复算完成。
- 原始研究：Git blob `a31a2bbcd1fe7c70951152f2a23edca6c934dc40`；精选历史 USDC 收支 blob `b44cc2140927246f9a428c8c455a6793eb80b662`。6 案例在采集前冻结于 `G4_PRICE_ONCE_PREREG_20261028.md`；本次 manifest SHA256：`5407db116ce0b755e0b38b1ce67331e6ac4b87a875e60665f63f75e351fe38ed`。
- **实际 18 次公开 HTTPS GET、18 次 HTTP 200、HTTP429 0、0 重试**；单通道有源码 `>=12.5s` 间隔限制。仓库 workflow 不提供 schedule/workflow_dispatch，且通过第一次提交父 SHA 与 `run_attempt=1` 保护。本结果提交不再触发公开 API。
- 离线单元测试 **6/6 PASS**、无网络默认模式及严格单次提交门禁均通过。无 Mac/V1/Loop/生产 SQLite 读写、Solana RPC、钱包、Gmail、交易、通知、定时任务或默认跟单金额。

## 2. 逐案例真实历史分钟 *收盘价代理*（非跟单可执行收益）

各列均为**进入该行预注册信号 T0 后不同延迟**，到该行预注册退出锚点的 `(1m_exit_close / 1m_entry_close - 1)*100%`，未扣除任何费用和滑点。价格以**未来完成**的 1 分钟 K 线收盘值计算，部分时刻无正成交 K 线会显示缺失。

- M2/M3/M4：**正式 MULT** 为 T0，退出为 **正式 MULT+24h**。
- A2/A3：**ACC** 为 T0，退出为历史核查的 **Frank 最后一次退出时刻**附近的 K 线；这不是模拟“跟到 Frank 的 SELL 通知时间”。
- C3：没有冻结 ACC/MULT 的 BUY，对照 T0，退出 T0+24h；不是随机无信号组。

| 案例 | T0 | +30 秒 | +120 秒 | +300 秒 | +900 秒 | +3600 秒 | 有代理档数 |
|---|---|---:|---:|---:|---:|---:|---:|
| M2 | 正式 MULT | +5.250% | +4.774% | +2.194% | -3.104% | +0.256% | 5/5 |
| M3 | 正式 MULT | +87.714% | +87.285% | +95.609% | +76.263% | +100.636% | 5/5 |
| M4 | 正式 MULT | — | — | — | — | — | 0/5 |
| A2 | ACC | — | — | — | — | — | 0/5 |
| A3 | ACC | -8.750% | — | — | — | — | 1/5 |
| C3 | 无信号 BUY | -51.665% | -56.766% | -67.521% | -59.651% | -66.820% | 5/5 |

`—` 是缺失或不符合入场/退出因果的档次，不代表 0% 收益。**A3/E4Ap 的 +3600s 档发生在已冻结退出时点之后**，严格为 `ENTRY_AT_OR_AFTER_EXIT`。其余 A3 缺失档、M4 与 A2 全部档均为 `MISSING_NONZERO_VOLUME_CANDLE`，不可假装某价格可成交。

## 3. 重要新发现及限度

1. **正式 MULT 后仍可能存在价格上涨空间。** M3/PerPs 正式 MULT +300s 到 MULT+24h 粗收盘价代理 **+95.608658%**；M2/HcRL 同档 **+2.194465%**，但 HcRL +900s 档 **−3.104130%**。单币样本和统一固定 24h 退出不支持重复性策略盈利结论。
2. **不能把 PerPs 老试验 ACC+300s 的 +118.154% 与新试验 MULT+300s 的 +95.609% 简单相减当作延迟损失**：不同时刻触发，退出时刻也分别为 ACC+24h、MULT+24h，选池可能不同。必须保持两种独立策略因果锚点。
3. **Hg5 全部五档仍无合格正成交分钟 close**，与老报告中极低历史 1m 成交额的风险相符；但不推断该市场在所有历史路由都无法交易。
4. **8K5 到 Frank 最终退出附近的五档全缺失**；E4Ap 只有 +30s 档的粗价格代理 **−8.749709%**，+3600s 时 Frank 已退出。不能只保留成功样本。
5. **C3/H1kX** 无信号、价格代理 +300s 至 24h **−67.520742%**，仅为从重建 UNKNOWN BUY 挑出的偏样本；它的负收益不能证明 ACC 策略优于无信号。
6. **总体覆盖：3/6 完整五档（含 C3 对照），另外 3/6 不完整。仅研究的五个信号案例总共 11/25 个延迟档有分钟价格代理**；能证明特定金额、路线、时间与入/出场费用的可执行跟单报价配对仍然 **0**。
7. Artifact 内有原始 1m 成交额字段，但**此报告尚未独立取得原始 ZIP 与分钟成交额复算**；不能将仅见数值上涨的价格代理晋升为有历史深度或真实跟单收益。数据源当前排行选池仍有幸存者偏差。

## 4. 后续策略判定与门禁

`G4_HISTORIC_PRICE_PROXY_COLLECTION_COMPLETED / FORMAL_MULT_CLOCK_PROXIES_AVAILABLE_FOR_M2_M3 / LIQUIDITY_EXECUTION_NOT_VALIDATED / STRATEGY_NEED_MORE_DATA / NO_PRODUCTION_TRADE`。

下一步不应继续盲目扩大 API 请求；应先**独立下载并复算已留存的 raw Artifact，检查每档分钟成交量、池身份及 close 时间的因果性**，并在核实其限制后，决定是否有必要用前向数据和用户明确设定的规模进行可执行深度研究。任何新公开 provider GET、私有 Mac 访问、长期监控、交易或发布都需要另行授权，原 18 次额度已经完全执行完毕。
