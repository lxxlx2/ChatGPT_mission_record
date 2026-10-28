# Frank G4 — ACC/MULT 一次性前向报价可得性研究协议（2026-10-28）

**状态：PROTOCOL_DRAFT_ONLY / NO_COLLECTION_AUTHORIZATION / NO_PRODUCTION_TRADE。** 本文档只设计未来研究，不授权新生产读取、报价/API/RPC 调用、订阅、定时任务、通知、部署、交易、合并或购买服务。下列时间与请求数均为待独立审查的提议，不是当前运行许可。

## 0. 研究决策与证据边界

目标仅回答：Frank 的真实 ACC/正式 MULT 首次被本地研究进程看到时，假如用户明确指定一笔 USDC 研究金额，能否在预定延迟获得买入报价，并在预定研究退出时刻获得对应数量的卖出报价？统计未报价、超时、缺失及报价往返差额。**有报价 ≠ 可真实成交 ≠ 已实现盈利**。

固定来源为已独立审核 PR #239 SHA 990188c95291f910fdecbf9c19cff9321219b6a3、PR #238 的 episode 信号时间线、G0-A 历史模型研究集。PR #239 的旧退出侧因果错误使旧 16/16 非空历史代理失效，原预注册严格有效收益为 0/30；另 15/30 只是回溯敏感性。严禁将历史分钟 K 线、Frank 本人盈亏或未来才出现的 MULT 回填为当时跟单报价。此前 27 分钟 Mac 只读观察 326/326 样本、0 新 BUY，因此实时盈利与实时延迟都未得到评分。

## 1. 事件纳入与时间因果

一个单位为 (person_id, mint, episode_id, signal_kind, source_signal_id)。只接受观察窗口内**首次实际看到**且来源校验合格的新 ACC 或正式 MULT；保留所有来源异常、重复、过期、无 BUY 的原始分母。

- ACC 研究时钟：第一次成功观察到该 episode 合格 ACC 的 UTC 时刻。原始 BUY 的 blockTime 仅作为年龄与来源证据，不能作为用户可以当时买入的时间。
- MULT 研究时钟：正式 MULT 第一次成功观察的 UTC 时刻，与 ACC 独立重新计时；不能提前按将来升级 MULT 选择赢家。
- 同一 episode 的 ACC/MULT 是相关策略分支，不是独立 Mint 或两笔独立投资机会；同币跨 episode 应保留身份和簇。
- 单独保留 source_event_blocktime、signal_generated_at（若有）、indexed_first_at（若有）、first_local_observed_at、browser_first_visible_at（若真实有）、notification_delivered_at（若原来授权过且有回执）、quote_request_at、quote_response_at、quote_expiry_at、first_frank_sell_observed_at。没有数据的字段记 null；不能编造入库、页面或通知的时间。
- 本地采样最长每 5 秒一次，首次看到只构成可观测延迟上界；需要双时钟异常检测，使用 UTC 与 monotonic 记录，墙钟倒退则停止。
- F01 的 600 秒来源有效期维持不变。入场意图到达时若源事件已超 600 秒，则记 OUTSIDE_F01_600S、**不发报价请求**。某档时间已错过，也不能事后查询并冒充当时。
- FIRST_SEEN 不等于链上完整覆盖，现有本地 recent_trades 最多 100 条，不能声称对全链 Frank 交易零漏报。

## 2. 单次研究规模：所有值都是提案、不是授权

| 要素 | 提议上限/方案 | 不可突破 |
|---|---|---|
| 启动 | 用户未来重新明确批准的手工一次性前台启动 | 无 cron、LaunchAgent、schedule、隐性等候或自行开始 |
| 绝对时间 | 最长 120 分钟，并需用户指定具体曼谷开始/截止时间及对应 UTC | 达截止强停，不重试不延长；未授权日期与时刻不得启动 |
| 源观察 | 现有 V1/F01 可审计的只读本地源，每 5 秒至多 1 次、最多 1440 轮 | 生产 SQLite mode=ro/query_only、WAL/SHM 禁写，OS 隔离，禁止停/重启现有进程 |
| 新 episode | 最多 2 个不同 episode、每个最多 ACC+MULT，共最多 4 个合格信号事件 | 时间先到先冻结，不能因涨跌结果选择样本 |
| 对照延迟 | 30/120/300/900/3600 秒 | 900/3600 在 F01 600 秒资格窗外，不查交易报价，只记录 STALE |
| 可尝试报价档 | 30、120、300 秒，且单档仍处于真实来源 600 秒内 | 未按时采到/无新事件记缺失，不能回填 |
| 退出 ① | 每个成功买入 quote 接收后 +600 秒一次反向报价 | 只是固定十分钟研究窗口，不是实际交易 |
| 退出 ② | 首次真实可见且与该 episode 对应的 Frank SELL 事件后一次反向报价 | 不等于完整平仓；窗口内没有 SELL 记右删失，不推断卖出价 |
| Jupiter 预算 | **最多 36 次 GET**（4 信号×3 可报档×最多 3 次：入场、固定退出、Frank SELL 退出） | 最慢至少间隔 3 秒，无重试；401/403/429/5xx/异常立即停止 |
| 新 RPC | **0 次** | 本地来源不可核验则 SOURCE_UNVERIFIED，禁止临时增加 RPC |
| 交易 | **0** | 不得连接钱包、导入私钥、签名、调用任何 POST、swap execute 或 sendTransaction |
| 用户金额 | **user_notional_usdc = null** | 必须由用户在**以后单独授权**给出明确金额；不允许借用历史 $30/$300 等数字 |

若观察到 0 新 BUY/信号，结果是 NOT_SCORABLE，不是模型失败或 0% 收益。若金额未知，保留 SOURCE_ONLY / NOT_ASSESSED_USER_AMOUNT_MISSING，**不得进行任何金额相关 GET quote**。已提交旧的 18 次 GET 额度不可继承。源、权限、预算、进程、安全或截止门禁任一失败就 fail closed。

## 3. 官方报价接口与未验证条件

拟采用 Jupiter 官方 Swap API V2 的 **只读 GET https://api.jup.ag/swap/v2/order**；这是未来经过用户授权才可调用的唯一外部行情服务。

一手文档（2026-10-28 查阅）：
- https://developers.jup.ag/docs/swap/order-and-execute — GET /order 在不传 taker 时可以仅获得报价，不返回需要签名的交易；存在路由、手续费、有效期与无成交路线等限制。
- https://developers.jup.ag/docs/portal/rate-limits — Keyless 0.5 RPS；免费密钥 1 RPS。为防压限，提议单线程间隔不少于 3 秒。文档其他页提到 API key，说明 Keyless 对此路径的实际适用性未来需要授权后一次性验证；如果需要购买、提供新 key 或改变来源，停止并回报，不自动升级。
- 只允许 GET /order；禁止 /execute、/submit、/swap、/build、链上交易方法、钱包地址或任何交易签名。请求时必须不传 taker；若返回 transaction 非 null，拒绝而非生成签名。
- 官方正在从旧 lite-api 迁往 api.jup.ag；不依赖旧域名，不把当前配额文档当成确定可访问性。

每个实际前向信号及可报档：在 t_visible + lag **之后、接近该目标**请求 USDC → Mint 的按金额 BUY quote，记录原始返回值、路由、金额最小单位、状态、出入金额、全部费项、请求/响应/到期时间、证据 SHA256。报价未及时成功则记 MISSED_LAG/NO_ROUTE/HTTP_FAILED/QUOTE_STALE，不能用未来分钟价格补齐。

退出时用该次入场 quote 返回的**假想代币数量**作为反向 Mint → USDC quote 的输入，而非 Frank 自己的持仓。每档两种退出方案独立记录。没有真实 BUY quote 就不能构造虚拟持仓与 SELL quote。到实验绝对截止后，未发生的退出记 CENSORED_AT_STOP，不进行追补。

报价代表服务在响应时给出的条件性意向，并不是已签名、可落地或保证成交。没有用户钱包，quote-only 还无法验证余额、ATA、SOL gas 和真实路由落地风险。可能的 RFQ 报价也有有效期和 last-look 风险。完整交易手续费、滑点、gas/priority、失败成本若缺失，则只能展示条件性**报价差额**，不允许报“可实现净利润”。

## 4. 安全、来源隔离与停止

使用至少两个安全边界：① DB 观察器只能对生产已有文件只读，OS 禁写且**禁出站**；② 网络报价进程不能读取 Mac 生产 DB、钱包/邮箱/交易所凭据，仅能访问经过防火墙/代理核准的 Jupiter 域名，只具备只读 GET 能力。若无法建立并核验该隔离则 PREFLIGHT_NO_GO，不放宽保护运行。只把不含密钥的匿名化信号事件和用户批准的研究金额经过受控单向传递发送给报价进程。

所有网络响应和错误保留 status、请求时刻、响应时刻、摘要、原始数据的内容哈希和对应来源。不得把任何私有钱包/密钥、生产数据库或机密原始数据推到公开 GitHub。只允许在隔离的私有研究目录写研究证据与清理回执。

停止条件：用户设定的绝对截止、人工终止、任何文件写入权限不满足、原生产 PID 出生身份漂移、异常重启、资料来源不明、金额缺失、报价器不能禁用交易或不能限制出站、预算超限、429/5xx/401/403、超时、时钟异常或无法保证两个进程清理。停止后验证生产服务与 Dashboard 8766 保持原样，不遗留观察器、监听端口、后台任务；不得安装 cron/Agent 或推送通知。

## 5. 输出分母和投资评价门禁

逐 episode 和策略/延迟档报告：
1. SOURCE：本地首次新 BUY、合格 ACC、正式 MULT、其各自来源签名与 blockTime；漏索引/异常单列。
2. VISIBLE：首次实际看到的上界延迟、是否在 600 秒窗内；浏览器/通知未测时只记 null。
3. BUY_QUOTE：指定金额、指定时刻、指定 token 的报价可得/不可得、原始回执、到期与失败码。
4. ROUNDTRIP_QUOTE：每个 BUY quote 对应两种退出方案的实际时点反向 quote；未发生的 SELL、用户金额不足、无路由和观测截止均保留分母。
5. EXECUTED：**始终禁止**，本研究不成交也不计算实际实现收益。

只有入场、退出 quote 都有且时钟、身份与金额一致，才允许计算 conditional_quote_spread_pct = (quoted_sell_usdc / approved_user_notional_usdc - 1) × 100。这个数不是可执行收益。费用、滑点和失败风险不全时 estimated_net_return_pct = null；绝不默认扣 2% 或基于某个幸运样本给策略放行。

**评审状态**：
- 现在：PROTOCOL_READY_FOR_INDEPENDENT_REVIEW（仅审核文档）。
- 未来授权缺任何一项：PREFLIGHT_NO_GO。
- 无新来源合格样本：NOT_SCORABLE。
- 只有部分买卖报价或退出被截断：QUOTE_FEASIBILITY_PARTIAL。
- 就算得到完整报价，策略结论最高仍是 STRATEGY_NEED_MORE_DATA；真正 STRATEGY_GO 需要预先锁定的独立前向样本、可验证成本、失败与极端风险、实际可成交证据，并另外授权。
- 交易始终 NO_PRODUCTION_TRADE。不得以报价研究成功反推出可以跟单。

## 6. 实际执行之前必须由用户独立批准（现在均未批准）

- 用户自己指定的单一 USDC **研究金额**。
- 某次明确的曼谷及 UTC 绝对开始/结束时间，最长 120 分钟；不是等待下一次事件的永久任务。
- Jupiter Keyless 可用性和最多 36 次 GET、至少 3 秒间隔、0 新 RPC 的限定请求预算；验证失败不换供应商。
- Mac 生产源的隔离只读读取与独立网络报价进程的权限边界。

正确顺序：只读协议 Draft PR → 独立 Claude/Codex 固定 SHA 审核 → 用户就四项独立授权 → 离线预检/安全门禁 → 才可能单次真实前向数据收集 → 第二方原始回执复核。此前原始 PR #239、G0-B/G0-A/F01、生产进程、钱包、交易与已有定时任务均不改变。
