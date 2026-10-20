# Frank 方案 3 · P1 历史证据与字段盘点（2026-10-20）

**范围：公开 GitHub 内已归档的原始调查结果，只读证据二次核对。** 没有读取用户 Mac/生产 SQLite、没有重新请求 RPC、没有创造新市场价或收益。状态 `P1_ARCHIVED_EVIDENCE_INVENTORY_COMPLETE / LIVE_DATA_UNVERIFIED / NO_DEPLOY`。

## 来源与采样边界

- **来源 R1**：[`frank-six-observed-roundtrips-2026-10-10.json`](./evidence/frank-six-observed-roundtrips-2026-10-10.json)，6 个**非随机选出的历史代币 lot**，对固定 Solana 根钱包的 USDC 花费/回收和所见已平仓量的回顾；`case_results` 中有信号时间、最后平仓时间、USDC 变化及已核实的平仓交易签名。**属于事后复盘，不是当时买入提醒可用的未来收益**。五个属于以前 ACCUMULATION 路径选样，TWEETCRAFT 是明确不满足买入次数的对照。
- **来源 R2**：[`frank-d0-six-mint-finalized-2026-10-11.json`](./evidence/frank-d0-six-mint-finalized-2026-10-11.json)，对同一六代币集合在特定 finalized slots 的**余额快照**；这不是 10 月 20 日当前持仓、也不是钱包全量资产。正余额代币的 USD 市值返回 PRICE_NOT_FOUND。0 余额 ≠ 完整地址簇清仓。
- **来源 R3**：[`FRANK_MULTIMINT_ACTUAL_ONCHAIN_AND_FOLLOWABILITY_2026-10-10.md`](./FRANK_MULTIMINT_ACTUAL_ONCHAIN_AND_FOLLOWABILITY_2026-10-10.md)：RPC 预算严格限制，已知 ATA 只在部分对象完整；3/18 个历史价格代理有数据，后遇 HTTP 429。**不能复用为实时价格或可执行跟单价**。
- **代码字段**（PR142 的工程基线）：`mission_control/frank.py:candidates()` 只读 v1_states/signals/trades，已有 `mint/pattern/source_signal_id/source_signal_at/position_state/buy_count/sell_count/latest_side/latest_signature/latest_at/latest_buy_price_usdc/latest_buy_price_status`；`service.py:_quote()` 未提供用户金额即 `USER_ORDER_AMOUNT_NOT_SPECIFIED`。**P2 只依赖这些已存在字段**，缺行情必须报告缺失，不做网络采集。

表一和表二合计 **12 条历史观察 = 六笔 lot 结果 + 同六 mint 的六条后来余额核对**，不是 12 笔独立买入/独立候选，也不是随机收益样本。所有时间 Asia/Bangkok，mint 为不可变完整地址；symbol 尚未核实就标 UNVERIFIED。

## 表一：6 条真实历史交易 lot（R1，供事后验证，不用于“当时”信息推送）

| 编号 | mint 前缀 / 精确时间(买入信号 → 最后卖出，BKK) | 事后根钱包 USDC 支出 → 回收 | 事后净 USDC | 对方案 3 有用的事实 / 禁止的推断 |
| --- | --- | --- | --- | --- |
| E01 | `MukLDtJ8…` 9-06 04:00:55 → 09:54:40 | 42,500 → 50,952.838215 | **+8,452.838215** | 2 笔已核卖出，后来第三方无签名代币转入**不是 Frank 再买**；不可把收益提前到信号时 |
| E02 | `8K5X85PA…` 9-08 09:42:17 → 11:27:36 | 28,598.056732 → 28,582.603719 | **−15.453013** | 两笔已核卖出，后续非签名入账不可触发再次建仓 |
| E03 | `E4Ap4ic…` 9-11 10:24:02 → 10:47:54 | 50,000 → 40,912.316439 | **−9,087.683561** | 首笔卖出使用 Jupiter + Raydium，非只含 Meteora 的旧白名单；已闭合 lot 不代表没尾余额 |
| E04 | `PerPsCe2…` 9-12 23:37:15 → 9-14 06:58:00 | 27,000 → 61,919.993902 | **+34,919.993902** | 这笔最大盈利**独占超过样本合计正净额**，不能以 6 例平均收益推断跟单会赚 |
| E05 | `4K1m7gAM…` 9-23 00:12:49 → 03:44:02 | 25,000 → 15,524.767593 | **−9,475.232407** | Frank 同代币两笔真实签名 BUY（15,000+10,000 USDC，隔 8 秒）后仍亏损；“持续买入”不是获利保证 |
| E06 | `HzYCHqAN…` 10-08 08:46:16 → 10-09 08:26:47 | 6,715.734492 → 7,031.556770 | **+315.822278** | TWEETCRAFT **只有一次买入**，不满足冻结 ACCUMULATION 条件，不能误提升为买入信号 |

上述净值是 **历史已选根钱包 USDC 转入转出的条件性 lot 差额**，不包含全面 SOL gas、其它钱包/链、税费或用户延迟跟单真实利润；不得展示为“Frank 目前 PnL”。完整 mint、平仓签名与可复查成本精度都在 R1 的 `case_results[0..5]` 中。

## 表二：6 条真实 finalized 余额状态（R2，不冒充当前）

| 编号 | 对应 E 编号 / mint 前缀 | 2026-10-11 finalized slot | 真实余额（token） | P2 可显示的事实 / 严禁推断 |
| --- | --- | --- | --- | --- |
| B01 | E01 MukLDtJ8… | 455413478 | **33.586031** | 归档快照**仍有正数尾余额**，USD PRICE_UNAVAILABLE，不表述为继续加仓 |
| B02 | E02 8K5X85PA… | 455413479 | **327.203717034** | 归档正余额不证明金额重大或经济收益；没有可核 USD 价 |
| B03 | E03 E4Ap4ic… | 455413478 | **0** | 只证明该观察账户在该 slot 为零；不证明 Frank 所有账户已经清仓 |
| B04 | E04 PerPsCe2… | 455413480 | **0** | 历史 slot 零余额与此前盈利 lot 是两种不同时间的事实，不能混同 |
| B05 | E05 4K1m7gAM… | 455413479 | **0** | 曾持续买入后来归零，不应当继续推送“仍在买入” |
| B06 | E06 HzYCHqAN… | 455413480 | **0** | 10-09 已有真实 SELL，10-11 仅是零余额复核，仍不是正式 ACC/MULT 信号 |

R2 中零余额均为 `ZERO_AT_SLOT_VERIFIED`，正数为 `NONZERO_VERIFIED`；其 `executable_usd_value_status` 均为 `PRICE_UNAVAILABLE_NOT_ASSUMED_ZERO`。不能把日期过期的余额、价格状态伪装成现在。

## 业务字段可用性、缺失和优先级

| 要给用户展示的字段 | 当前可用性 | 证据/来源 | 处理 |
| --- | --- | --- | --- |
| mint/CA、现有 ACC/MULT/re-entry 模式 | **已具备（在运行数据库中只读可得）** | `FrankView.candidates()` + V1 `signals` | 优先直接复用；原 V1 发信路径完全不动 |
| 最近买/卖、事件时间、签名、次数、持仓状态 | **已具备候选字段，准确性依赖 V1 已识别交易** | `FrankView.candidates()` | 显示“已观察到”，不当作全历史或完整地址簇 |
| Frank 最新买价 | **部分可得**，USDC_DIRECT 或 SOL_EVENT_TIME_USDC_VERIFIED 才可比较 | `latest_buy_price_status` | 其他币种/组合成本为 UNKNOWN，不补数 |
| 当前同 mint 市场参考价、观察时间、池子 | **未证明新鲜/可用**；旧 OHLCV 仅 3/18 且数据有 429 | R3；market 模块可能有其他历史源 | P2 参数允许传入明确来源的新鲜快照；没有就 `PRICE_UNAVAILABLE`；不新增 API 调用 |
| 市场价格距 Frank 买价变化 | **需要两个可比较的价与时间** | 上两行 | P2 用 Decimal 计算百分比，并标明“参考价变化，非实际可执行收益” |
| honeypot、流动性深度、用户金额滑点 | **NOT_VERIFIED/NOT_ASSESSED** | 缺来源或者缺用户选择交易金额 | 不假装知道；不能作为买/卖推荐 |
| 真实总 PnL / offchain Frank 身份 | **未核实** | R1 与 R2 的 scope guard | UI 永远不冒充全球钱包表现 |
| 市场风险跃迁提醒 | **需要新观察时间和可比前态** | 现阶段无完整实时流 | P2 只算研究标签；P3 才实现幂等新通知审阅 |

## P1 达标判断与 P2 输入契约

- 已找到 **12 条实际历史观察（6 + 6）**，含盈利/亏损、正式积累与非积累买入、卖出与余额不一致、USD 市价缺失、旧市场数据截断。**没有对 Mac 生产数据库读写**；非全域现实，仍需 P4 用 Mac **一致性只读副本**核对最新 live field 格式。
- P2 用**纯函数**输入候选与可选市场快照、`as_of`、明确指定的价格新鲜度容忍期，不做 RPC、Gmail、Jupiter、DB、网络调用；既有 `_quote()`、V1 信号策略和生产服务完全不改。
- P2 输出**信息性标签** `FRANK_CONTINUES_BUYING / FRANK_RECENT_SELL_OBSERVED / REENTRY_WATCH / PRICE_UP_FROM_VERIFIED_BUY / PRICE_UNAVAILABLE / DATA_STALE`，**不输出投资级风险评分、止损、默认下单量或执行层 BUY/SMALL_BUY**。
- 验证回放必须明确**回放时点可用的信息边界**：R1 最终卖出/收益与 R2 的后来余额不能回填到当时信号决策，防未来数据泄漏（lookahead）。

**下一阶段** P2 离线引擎→P3 页面/模拟提醒。P1 只有这次明确的历史子集盘点，不再为扩样而申请大量付费 RPC 或追求随机代表性样本；如果要代表性跟单收益须另立研究项目。

**安全门禁**：`NO_MERGE / NO_DEPLOY / NO_SIGNING / NO_LIVE_GMAIL / NO_OS_NOTIFY / NO_TRADES`。
