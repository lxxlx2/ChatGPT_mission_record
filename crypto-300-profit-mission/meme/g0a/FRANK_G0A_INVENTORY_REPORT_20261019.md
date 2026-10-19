# Frank G0-A 历史数据盘点修复结果（2026-10-19）

**状态：G0_A_COMPLETE（已知历史数据盘点完成；等待独立审核）。** 这表示 J0/M3 分母、episode 和现有价格证据等级已可复现，不表示延迟报价齐全、G0-B 通过或策略 GO。

PR #117 修复基线 `4726fccbc2012a9bc2e6ccd581928c924074ffad`；main 基线 `4e2bf056438830cf69a171d30474fdf489dd93f0`。架构按 PR #114 用户批准正文 `e4d61d1c8f246a7b04ea46ba674855346625a243` 与 PR #115 交接执行，未重新设计。修复针对[独立审核评论](https://github.com/lxxlx2/ChatGPT_mission_record/pull/117#issuecomment-6271623446)。Codex 是本轮唯一代码写入方。

## 1. 已完成的核心业务结果

| 模型 | 唯一 ACTIVE BUY | 唯一 ACTIVE SELL | ACTIVE 合计 | 非 ACTIVE 是否进入分母 |
|---|---:|---:|---:|---|
| J0 / 归档 M0 | **301** | **333** | **634** | 否 |
| M3（研究模型） | **315** | **338** | **653** | 仅纳入经 M3 重建恢复的 19 条 |
| M3 − J0 | **14** | **5** | **19** | 原分类全为 UNKNOWN_NEEDS_REVIEW |

这不是把审核意见中的 14/5 硬编码进统计。脚本从完整历史库读取 6,874 条记录，核验 raw SHA256、raw 与签名绑定、分类器结果及唯一 wallet+signature。再对 47 条 COMPLEX 候选用原研究的 `complex_candidate()`、`research_market_record()`、`reconstruct()` 重建，逐条核对归档原分类、category 与完整 shadow_trade。实际得到 19 个唯一恢复签名，14 BUY/5 SELL；全部属于原始 UNKNOWN，与 J0 ACTIVE 无重叠，全部存在于已核验原始集合。M3 不是 J3/rolling-HFT 模型，也不是生产分类升级。

完整历史分类：ACTIVE 634、PASSIVE_TRANSFER 4,433、ATA_CREATE 265、FAILED_TX 900、UNKNOWN_NEEDS_REVIEW 642，合计 6,874。窗口 UTC 2026-09-03T16:32:58 → 2026-09-30T09:39:20；这是 available verified subset，不是钱包终生覆盖。

方向按历史生产分类结果 `body.classification == ACTIVE_TRADE` 后读取 `body.trade.direction`，仅认可 BUY、SELL；未知 ACTIVE 方向使重建失败，不默认为 SELL。计数单位为唯一 `(wallet, signature)`，重复使脚本拒绝结项。本次重复为 0。研究 helper 依签名索引，脚本另验全输入 signature 单独唯一，防止跨钱包归属歧义。

## 2. 来源、代码版本和复现链

找到了真正的 **`history-shadow-ledger-verified.sqlite`** 及其 raw 文件。它位于本机私人 Frank 历史证据目录；未上传数据库、raw、钱包明细或个人绝对路径。旧报告把 fm3 的 536 条机械分类样本当成 6,874 原始入口是错误的，已撤回；fm3 不再用于 J0 分母。

| 输入/核验 | 本轮结果 |
|---|---|
| 历史 SQLite SHA256 | `c67a2dd05b246882c94c1964774b4243b0cc8b18066ce69ca5a9bc859d56f685` |
| 6,874 raw 全量哈希及绑定 | 全部重新通过；无缺失；历史库文件运行前后 SHA256 相同 |
| chronology SHA256 | `7dd4cb90f0dc3bcd3d527421742fa45b55ac1807967deb4f81f7ee30b20f6ed3`，与归档一致 |
| study JSON SHA256 | `0d1dce59566d1471f59eb72f14a2f5d1b55ad7bbe2a1ac9e5357c697245fe93d` |
| 历史分类/engine 代码 Git 对象 | `89135131dc1a8ae48890dbe6bfd4b98a03ad2b20`（归档 production_boundary.starting_HEAD） |
| 历史代码与策略配置 | 导出本地 Git 对象至临时目录；逐项匹配归档 protected SHA256（mission_agent 与 config） |
| 私人 `v1-history-replay-final.sqlite` SHA256 | `106f815286cf2ddbc10cf6fbd99c155b402e0587d88fc4466b45f830a963fa3a` |
| J0 baseline 验证 | 31 个完整信号对象与私人 baseline 及归档 M0 全部相同 |
| M3 验证 | 32 个完整信号对象与归档 M3 全部相同；ACTIVE 总数匹配 653 |

**为何固定历史代码：** 当前 main classifier 已增加 route/amount 字段，直接拿它复核旧 body 会出现 `CLASSIFICATION_DRIFT_trade`。脚本固定并哈希校验研究时期的 classifier/parser/engine/policy，不忽略漂移、不用当前规则重写旧分类。raw 验证逻辑沿用 `import_verified()` 的检查步骤，局部适配为 `mode=ro` + `query_only`，并把已验证记录留在内存。episode 和信号通过现有 `frank_trade_coverage_historical_replay.replay()` 在临时 SQLite 中重建；结束即清理，无持久影子平台。

价格读取使用离线 adapter，仅消费 study 的 6 个已归档 Coinbase receipt；不调用原 `HistoricalPrices` 的联网 fallback。脚本另装 Python audit hook，禁止 socket connect、DNS 与 urllib 请求。Git 只读取本地历史对象；未自动 fetch 历史代码。

复现命令（`PRIVATE_EVIDENCE`、`RUNTIME_SNAPSHOT`、`RAW_CACHE` 由持有私人证据者设置，不写入仓库）：

```sh
python3 crypto-300-profit-mission/meme/g0a/g0a_inventory.py \
  --source "$PRIVATE_EVIDENCE/history-shadow-ledger-verified.sqlite" \
  --baseline "$PRIVATE_EVIDENCE/v1-history-replay-final.sqlite" \
  --runtime-db "$RUNTIME_SNAPSHOT" \
  --cache-dir "$RAW_CACHE"
python3 -m unittest discover -s crypto-300-profit-mission/meme/g0a -v
```

`--runtime-db` 和 `--cache-dir` 可省略，只报告这些辅助输入 UNRESOLVED。默认不打开任何个人/生产路径。缺失 source 返回 G0_A_PARTIAL；空历史、raw/hash/分类漂移或模型信号不匹配均拒绝结项并返回非零。source 中的 raw_reference 必须仍能解析到本地原始文件；迁移机器时需恢复私人证据目录或制作经审核的本地路径映射，不应改 raw 内容或用 536 子集替代。需要完整 Git 历史对象和 Python 3.12+；shallow clone 缺对象会失败并报告 PARTIAL。

## 3. BUY、事件、episode、Mint 分母

下表 BUY 数量是**完整历史窗口内属于该 episode 的全部 BUY**，包含信号触发后的 BUY；用于盘点，不能当成因果筛选或可交易信号数。信号事件按归档 signal 对象计数；episode 按原 Engine 的 `v1_evaluations(kind=ACTIVE_TRADE)` 映射，不按 mint 或当前最终持仓猜测。MULTIPLE episode 与 ACCUMULATION 有重叠，不能相加；Mint 也可跨 episode 或组重叠。

| 行为组 | BUY 签名 J0 / M3 | episode J0 / M3 | Mint J0 / M3 | 信号事件 J0 / M3 |
|---|---:|---:|---:|---:|
| 全部 ACTIVE BUY | **301 / 315** | **180 / 188** | **153 / 160** | 不适用 |
| 冻结 ACCUMULATION 所属完整 episode | 117 / 123 | 21 / 22 | 17 / 18 | 21 / 22 |
| 冻结 MULTIPLE 所属完整 episode | 55 / 43 | 10 / 10 | 9 / 9 | 10 / 10 |
| ACC + MULT 并集 | 117 / 123 | 21 / 22 | 17 / 18 | **31 / 32** |
| 其他 ACTIVE BUY：未产生上述信号的 episode | **184 / 192** | **159 / 166** | **145 / 151** | 0 / 0 |

J0 BUY 分区 117 + 184 = 301；M3 为 123 + 192 = 315。所有 BUY episode 均成功映射，缺失为 0。M3 ACC 的 22 个事件由 22 个唯一 BUY 签名触发；MULT 的 10 个事件也分别对应 10 个 BUY 触发签名。原规则定时评估时引用 BUY signature 不等于该秒又发生一笔新 BUY。

作为其他明确主动行为，SELL 单独列出：J0 **333 SELL / 161 个可映射 episode / 185 Mint**，其中 **64 个 SELL 签名无 episode**；M3 **338 SELL / 169 episode / 189 Mint**，其中 **61 个 SELL 签名无 episode**。这反映不完整前史中的 SELL 等现有 engine 语义；不虚构 BUY 或补造 episode，也不影响 BUY 分母。

独立运行时快照只作为旁证：10-03→10-12 的 93 行交易 = 48 BUY-like / 45 SELL-like；BUY 28 episode / 26 Mint。方向计数 BUY 26、ADD 20、REENTRY 2、EXIT 17、SELL 7、SELL_POSITION_UNRESOLVED 21；本次未知 side 0。脚本明确枚举 SELL/EXIT/SELL_POSITION_UNRESOLVED，任何新 side 单列 UNKNOWN。此窗口不拼接到 J0/M3。173 个缓存 JSON 均实际检测为 getTransaction wrapper；是否包含独立价格序列的语义判断标为 MANUAL_SOURCE_INSPECTION。

## 4. 价格证据：单位、精度和每个延迟档

价格分为三个等级：

- **Frank 自身交易时点的 quote/token 数量比值**：raw 已绑定，按 Decimal 和各自 decimals 计算；可用性检验逐笔检查正数、非零及有限值。它是钱包净数量的平均交换代理，单位为原 quote/token，精度受链上 block_time 秒级时间约束；不是逐池成交单价，不额外假定 USD、费用完整或跟单可执行。
- **历史池价/OHLCV 代理**：旧 10-10 报告记录 GeckoTerminal 5m pool close 覆盖 M3 信号 18 Mint 中的 3 个，采样因 429 中断，按当前池排名选池，有事后选择偏差。仓库未附该次原始响应和可复算的 event-time join，本轮不重新下载，不能确认任何一个 T+30/120/300 episode 的精确覆盖。
- **跟单者延迟可执行报价**：需要具体交易规模、池/路由、精确时点、费用/冲击/滑点/失败等证据。当前检查范围内 **0 条已验证记录**，这不是证明市场没有价格。

原始事件数量比值的覆盖（signature / episode / Mint）：

| 行为组 | J0 | M3 | M3 附加限制 |
|---|---|---|---|
| 全部 ACTIVE BUY | 301 / 180 / 153 | 301 / 180 / 153 | 14 个恢复 BUY 不把 synthetic USD shadow_trade 纳入原始成交比值；保留 raw 经济流与研究重建证据 |
| ACC episode BUY | 117 / 21 / 17 | 117 / 21 / 17 | 总 BUY 分母为 123 / 22 / 18 |
| MULT episode BUY | 55 / 10 / 9 | 41 / 9 / 8 | 总 BUY 分母为 43 / 10 / 9；M3 episode 成员变化，不能沿用 J0 的 55 |
| 其他无信号 episode BUY | 184 / 159 / 145 | 184 / 159 / 145 | 总 BUY 分母为 192 / 166 / 151 |

以下每行适用于 J0/M3 全部 BUY、ACC、MULT 和其他 BUY 组，分母取上一节各组。**价格证据表为 MANUAL_SOURCE_INSPECTION**：归档报告、DB 实际字段清单及缓存 schema 检查的结论，脚本明确输出此标记；不是通过没有 price 字段便断言世界上没有价格。

| 延迟 | 已验证延迟可执行报价 | 可复算的精确延迟池价/OHLCV | Frank 自身价格 | 缺失/无法验证 |
|---|---|---|---|---|
| T+30s | 0 条已验证记录 | UNRESOLVED；5m close 不能解析 30s | 上表是 T0 交易时点比值，无 T+30 匹配证明 | 各组精确延迟 event/episode/Mint 覆盖均 UNRESOLVED |
| T+120s | 0 条已验证记录 | UNRESOLVED；5m close 不能解析 120s | T0 比值不能替代 T+120 | 同上 |
| T+300s | 0 条已验证记录 | UNRESOLVED；旧报告有 3/18 Mint 的5m代理文字记录，但缺原始响应、边界与事件对齐验证 | T0 比值不能替代 T+300 | 同上；不得转换为 3/18 episode 或 3/18 可执行覆盖 |

Coinbase 6 个 receipt 只有 SOL-USD 的历史分钟换算参考，不是目标 meme 池价。M3 shadow_trade 的 USDC 字段是研究 USD amount-gate 代理，不表示实际 USDC 支付，不用其金额冒充真实成交价格。本轮未计算收益率、胜率或回测。

历史价格来源人工检查依据：`meme/FRANK_MULTIMINT_ACTUAL_ONCHAIN_AND_FOLLOWABILITY_2026-10-10.md` §4；`meme/FRANK_TWEETCRAFT_DELAYED_FOLLOW_CHECK_2026-10-10.md` 的其他窗口 1m/5m 样本不自动扩展到本研究 18 Mint。

## 5. 验证、剩余缺口和 G0-B 依据

实际执行：

1. 完整脚本：6,874 raw 重核、J0 301/333、M3 315/338、19 恢复案例重建、episode 分区和原始数量比值检查、J0 私人 baseline 完整信号匹配及 M3 归档完整信号匹配，输出 G0_A_COMPLETE。
2. 独立只读 SQL 交叉检查原始 history 库和已归档 M3.sqlite：分别得到 BUY/SELL 301/333、315/338；两库 wallet+signature 重复均为 0。
3. 标准库 unittest：**5 passed**，覆盖未知 side 不计 SELL、NULL episode、SQLite 写入拒绝、缺路径不创建库、空历史/缺 source 的 UNRESOLVED/PARTIAL、网络 guard 和非零数量比值。环境没有 pytest，本轮使用不需安装依赖的 unittest；未声称运行全仓库测试。
4. 无参数实际执行返回 G0_A_PARTIAL，source 和辅助路径明确 UNRESOLVED；没有默认生产读取。
5. `git diff --check`；最终 PR diff 仅 `meme/g0a/`。仅聚合结果写入 `inventory_result.json`，不保存私有路径、wallet、signature 清单或 raw。

G0-A 已完成 A/B 的完整历史分母与 C 的分组盘点、D 的必要脚本修复。**未解决的数据缺口**：各延迟档可执行报价、Gecko 原始响应与 episode 对齐、SELL 的不完整前史、钱包终生覆盖、独立 OOS。它们被明确保留，不以测试通过替代数据完成。

G0-B 的判断依据：已有 315 个研究主动 BUY、188 episode，但信号并集仅 22 episode / 18 Mint，重复事件相关，且已参与模型研发。可以据此界定前向收集对象和成本，不能宣称策略 GO、盈利或预测价值。没有纯净独立 holdout，仍为 **NEED_MORE_DATA**；后续阈值必须先冻结再取得独立前向数据。

**本轮未执行、也不延续原 ≤50 次探针建议。** 未形成可批准的唯一 provider/endpoint/池目标与成本方案；没有隐藏请求配额或 pending 执行任务。如后续选择新采集，必须另交具体端点、目标、请求上限、费用、停止条件及能填补的缺口，由用户单独授权。G1 批准不是 API 授权。

全程不改生产 SQLite、信号引擎、冻结策略、Mission Control、LaunchAgent、Gmail 或部署；未购买额度，未使用新 key，无新 RPC/Alchemy/GeckoTerminal/DexScreener 或其他市场 API 请求。GitHub PR 读取、原分支 push 和交付评论属于本次明确授权范围。
