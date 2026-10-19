# Frank G0-A 探索性数据盘点报告（2026-10-19）

状态：**EXPLORATORY / NOT_A_BACKTEST / NO_STRATEGY_VERDICT**
基线：`origin/main` `4e2bf056438830cf69a171d30474fdf489dd93f0`；G1 架构依据 PR #114；C 节依据 PR #115。
方法：只读本地 SQLite（`mode=ro`）、已归档 JSON 和本地 RPC 缓存。**未调用任何新 RPC、第三方价格 API，未修改 Frank 生产代码、配置、SQLite、LaunchAgent 或冻结策略。** 可复现脚本：`crypto-300-profit-mission/meme/g0a/g0a_inventory.py`（只读，输出见下表）。

## 1. 核心结论（先看这一节）

1. **BUY 分母不能直接用 634 或 653。** 634 是 J0 的 `ACTIVE_TRADE`，包含 BUY 与 SELL；653 是 M3 恢复后的 ACTIVE。归档 JSON **没有逐签名方向列表**，只有 9 笔 SOL 案例（全部 SELL）和 63 笔 USDT、47 笔 COMPLEX 的子集。因此 **J0 的 BUY 数量无法从归档 JSON 直接得出**，需要重新从 6,874 签名原始证据推导（见第 4 节，尚未完成，属于下一步本地工作，不需要 RPC）。
2. **可以确定的 BUY/SELL 数字只来自运行时 SQLite 快照**（2026-10-03→10-12，93 笔 ACTIVE 交易）：BUY 48 签名、SELL 45 签名，二者无重叠。这是另一个窗口，不能与 J0 的 634 合并计数。
3. **价格覆盖率几乎为零。** 本地没有任何按时间序列的 meme 币池价格：
   - 运行时 DB `trades` 只有 raw 数量，无价格字段；
   - Coinbase SOL-USD 6 个 K 线 receipt 只能作为 SOL 换算参考，不是 meme 币价格；
   - GeckoTerminal 仅覆盖 18 个信号 mint 中的 **3 个**，且 5 分钟 pool close 不是可执行报价，采样因 HTTP 429 中止，并存在当前池子排名导致的事后选择偏差（`FRANK_MULTIMINT_..._2026-10-10.md` §4 原文）；
   - fm3 shadow `meme_facts` 6 条，**USD_estimate 全部为 null**（`NO_CAUSAL_USD_MARK`），`followability` 字段全部为 `NO_EXECUTABLE_DELAYED_ENTRY_PRICE`。
4. **可用于 episode 研究的信号样本很小**：M3 归档 32 条信号 = 22 ACCUMULATION + 10 MULTIPLE，覆盖 22 个 episode、18 个 mint；运行时 DB 另有 5 条信号（4 ACC + 1 MULT，3–4 个 mint）。合计不超过约 40 条信号事件，且 episode 相关性很强。

## 2. 分类计数（逐项可复现）

| 数据源 | 窗口（UTC） | 结果 | 备注 |
|---|---|---|---|
| 10-04 study `history` / J0 baseline | 2026-09-03 → 09-30 | 6,874 签名：ACTIVE 634、PASSIVE 4,433、ATA 265、FAILED 900、UNKNOWN 642 | `AVAILABLE_VERIFIED_SUBSET_NOT_WALLET_LIFETIME`；raw_missing=0，raw_hash_verified=6,874 |
| 10-04 study 归档子集 | — | SOL 9 案例：SELL 9、BUY 0；USDT 63 案例；COMPLEX 47 案例 | **无完整逐签名方向列表** |
| 10-04 study M3 信号 | 同上 | 32 条：22 ACC + 10 MULT；22 episode；18 mint | 信号记录 ≠ 独立交易 ≠ 已发通知 |
| 运行时 forward.sqlite（10-12 快照） | 2026-10-03 00:50 → 10-12 10:12 | `trades` 93 行：BUY 26、ADD 20、REENTRY 2、EXIT 17、SELL 7、SELL_POSITION_UNRESOLVED 21 | 按签名去重：**BUY-like 48、SELL-like 45、重叠 0**；28 episode、26 mint |
| 运行时 `signatures` 分类 | 同上 | 2,058 签名：PASSIVE 1,649、ATA 114、FAILED 124、UNKNOWN 78、ACTIVE 93 | |
| fm3 shadow raw evidence | 2026-10-03 → 10-04 | 536 raw 交易：PASSIVE_RECEIPT_LIKE 383、ACTIVE_SWAP_LIKE 53、UNKNOWN 94、FAILED 4、TRANSFER_OUT 2 | `ACTIVE_SWAP_LIKE` 是机械分类，需与 study 分类口径核对，不等于 BUY |
| fm3 与运行时 BUY 交叉 | — | 运行时 BUY-like 48 签名中仅 **7** 个在 fm3 原始集合中 | 两个窗口基本不重叠，不能互相补全 |
| 本地 RPC 缓存 | 2026-10-07 → 10-08 | 173 条 raw `getTransaction` 响应 | **不含任何价格序列** |

## 3. 价格覆盖率：按信号组与 mint 的现状

| 信号组 | 分母（事件/episode） | 有可执行价格证据 | 有代理价格（非可执行） | 缺口原因 |
|---|---|---|---|---|
| 全部主动 BUY（J0） | 需从原始证据推导，**尚未完成** | 0 | 0 | 无 meme 币逐笔价格序列 |
| 全部主动 BUY（运行时窗口） | 48 签名 / 28 episode / 26 mint | 0 | 0 | `trades` 无价格字段 |
| 冻结 ACCUMULATION（M3） | 22 信号 / 22 episode / ≤18 mint | 0 | GeckoTerminal 3 mint（5m pool close，有 429 与选择偏差） | 其余 15 mint 无数据，采样被限流截断 |
| 冻结 MULTIPLE（M3） | 10 信号 | 0 | 与上相同来源，无单独覆盖 | 同上 |
| 其他候选行为 | 未定义 | — | — | G0-B 之前需冻结 |

**覆盖率结论**：任何按 mint/episode 计算的“可执行价格覆盖率”当前为 **0%（可执行）**；代理覆盖率最多 3/18（约 17%），且样本有选择偏差。

## 4. 无法验证或尚未完成的部分

1. **J0 的 BUY 精确数量**：需对 6,874 条原始证据逐条解析方向。原始 raw 归档路径存在（`crypto-monitor-fm3-evidence-20261001`、`frank-fomo-rpc-cache`），但本轮**未完成逐条重推导**，因此本报告**不给出 J0 BUY 的最终数字**。这是下一步纯本地工作，不需要 RPC 授权。
2. **episode 与 BUY 的完整映射**：运行时 DB 有 28 个 BUY episode，但 J0 窗口的 episode 映射未重建。
3. **生存偏差与前视偏差**：GeckoTerminal 池子排名是当前时点的排名，存在事后选择偏差；M3 恢复交易（653 vs 634）的恢复规则是研究期产物。
4. **可执行性所需的全部要素**：滑点、价格冲击、手续费、用户通知延迟、用户实际可成交性——本地没有任何证据。
5. **独立样本**：6,874 签名及 M3 信号都已被用于规则与模型研发，**不存在未参与参数选择的独立 holdout**。按 G1 §5，在独立前向数据出现之前，任何结论只能是 NEED_MORE_DATA。

## 5. 可复用数据清单

| 数据 | 位置 | 用途 | 注意 |
|---|---|---|---|
| 6,874 签名 raw 证据 | `crypto-monitor-fm3-evidence-20261001/frank/shadow/`（raw/ 36 文件 + forward.sqlite） | G0-B 样本分母与方向重推导 | 需验证哈希；本地存在 |
| 运行时 forward.sqlite 快照 | `~/Library/Application Support/FrankMeme/release-backups/mission-loop-20261012T145714Z-6720/` | 运行时 BUY/SELL 结构与 episode 映射 | 只读打开；非生产当前库 |
| M3 信号与 episode | study JSON `models.M3` | 信号事件清单 | 不含方向列表 |
| 173 条 raw 交易缓存 | `frank-fomo-rpc-cache/` | 交易事实核对 | 无价格 |
| GeckoTerminal 3 mint 价格 | 仓库 2026-10-10 报告（文字表，非原始 JSON） | 仅作方法反例 | 原始响应未归档在仓库，不能复算 |
| Coinbase SOL-USD 6 receipt | study `price_receipts` | SOL 换算参考 | 不是 meme 币价格 |

## 6. 需要新数据时的请求（未获批准，本报告不执行）

| 项目 | 内容 |
|---|---|
| 目标 | 补齐 M3 22 个 ACC/MULT episode 的 T+30s/120s/300s 池子价格，验证覆盖率 |
| 来源 | 链上 Solana 池子 swap 事件（`getSignaturesForAddress` + `getTransaction`，限定池子地址）或 DexScreener/GeckoTerminal 历史 OHLCV |
| 请求上限（建议） | 先做 **≤ 50 次 RPC/API 请求的探针**，只测覆盖率与可用历史深度，不做全量 |
| 停止条件 | 任何 429 立即停止，不自动重试；超过探针上限即停止 |
| 预期价值 | 判断 22 个 episode 中多少能获得可执行价格证据；若覆盖 <50%，则 G0-B 只能 NEED_MORE_DATA |
| 成本 | 免费公共 RPC 为主；**不购买 API 额度**，不启用付费 key |
| 需要你批准的事项 | 探针的确切端点、请求上限与是否使用 Alchemy 现有 key（当前 `solana_rpc_urls` 配置存在，但需你确认） |

## 7. 本轮不做的事

- 不计算任何收益、胜率或 PnL（G0-B 之前禁止）。
- 不修改冻结阈值、信号规则、V1 policy 或生产服务。
- 不推断“Frank 买入即可跟单”；不把 3/18 的代理样本外推。
- 不声称 G0-A 通过或 G0-B 结论。

## 8. 下一步（按顺序，均不需要新 RPC）

1. 用 fm3 `frank_transactions` 与 study 口径逐签名推导 J0 BUY/SELL 数量（纯本地，产出可复现计数）。
2. 对照运行时 48 个 BUY 签名与 fm3 原始证据的重叠与缺口。
3. 将第 6 节探针请求单独提交你审批。
