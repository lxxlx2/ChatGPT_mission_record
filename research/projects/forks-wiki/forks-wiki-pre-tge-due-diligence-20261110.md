# Forks.wiki / FORK 预 TGE、可领取性、链与安全尽调（2026-11-10）


## 2026-11-11 deeper chain forensic: #308 claim rank, exact collector provenance, fee history, unrelated token mints

**Independent evidence:** Alchemy Solana finalized RPC; publicly versioned \`forkwiki/fork\` GitHub; user's authenticated claim page and official X. Research only, no wallet transactions or automation.

### Link between claim collection wallet and public treasury, confirmed

1. The collection wallet's **first-ever signature** [Tme3YTx...](https://solscan.io/tx/Tme3YTx2RASmWD18VfAxTTD77T4kqx18u7DV3ucFH8fPLBnSSn6ferf2DqqNbUhkJQPSM5Dv2GZ35w8KArh92hq), slot \`467805824\`, **2026-11-10 17:32:56 UTC / Nov 11 00:32:56 Bangkok** was signed by public config treasury \`61468ik7HhYNg8ixQYeF9caMNVm57PqTy3tyQ28F6Y5e\` and **sent exactly 0.15 SOL to \`Da71cES3NeUMLpW3MuNGkCVTht3jceik1RtNLrbqC6jV\`**. Receiver balance prior = 0, after = 0.15 SOL. This is a direct, strong operational link previously missed.
2. Only **86 seconds later**, [tx 3mrTo8...](https://solscan.io/tx/3mrTo8Tg51J5HgsWmJb8hPjLmyMjLCJ8r6h1UK3zmY5HNnE2jUe5LSGk91z9UJ4YRMzbuTHcVmVtwUY1ympmph5E) at 2026-11-10 17:34:22 UTC **has this collection wallet as transaction signer** and calls pump.fun \`UpdateFeeSharesV2\`, \`DistributeCreatorFeesV2\`; involved Mint \`HTaBmiNnLkMZEcgmpAFU76LG3akLKPSfJxfXu3pffork\` with onchain Token-2022 metadata \`doge / DOGEP\`. This wallet participates in real pump.fun development/fee collection operations, **not** merely an unknown third-party payment wallet.
3. Solana account data: collector \`owner=11111111111111111111111111111111\` / \`executable=false\` / \`space=0\`, verified on-curve and independently observed signing. **Not a deployed custom program or claim escrow**. Fee collector recorded ~**9.768090614 SOL** at finalized slot \`468163312\`; this is a mixed operational wallet balance including creator-fee distributions and user claim payments, **not proof of an airdrop reserve, a tally of paid fees, or 308 claim users**.

### Queue #308 versus actual payments

- User exact fee tx: [21HaGm...](https://solscan.io/tx/21HaGmHa9suUiXpfee4TYUQ1Bn8yA4MjUoAYDMwNLc3vZp97W9DqL68WJzBKPhuq3SsjgDHkofG2RmM5n5KNFUux), 2026-11-11 14:23:48 UTC. 0.002 SOL transferred to collection wallet; 0.000011 SOL separate chain fee; no token approval, custom token/claim program or claim-state receipt in transaction. User's queue \`#308\` and 12,600 FORK are only website-server fields.
- I paginated **all 145 receiving-wallet signatures before the user's transaction back to the first transaction**: **only 7** prior signatures had the exact memo \`forks.wiki $FORK claim fee\`; the other 138 involved mostly pump.fun trade/fee activities, including \`SweepCreatorFee\` and \`DistributeCreatorFees\`. Hence **#308 cannot be proven as payment sequence number for this address and memo**; it may instead be a backend reservation queue, different payment route, or other design. The data do NOT establish the rank is fabricated, nor provide an external way to audit it.
- Six of those seven prior fee-memo payments were \`0.002 SOL\`; an older [payment dZqU...](https://solscan.io/tx/dZqUAPss9F4TgXhpMpmnt6FuTUFtBacN97TtxNPZ2DVKd9jzeTwBNCz3zy3pzFPEndujvBDgKHo765oHqTxJu74) from 2026-11-11 12:37:47 UTC with the **same exact memo** transferred **0.02 SOL**, 10× the user amount. Pricing policy, test transaction vs separate tier are **UNCONFIRMED**; do not infer a particular explanation. Additional 155 same-memo receiving-wallet signatures were observed from 2026-11-11 14:30:52 through 14:52:34 UTC in a 180-signature sample, proving continued fee receipts, not successful token payouts.
- Onchain receipt does not store a 308 index, distribution commitment, frozen Merkle root, 12,600-token claim entitlement or payout enforceability. Website still reported \`0 of 0 wallets sent\`. The current /claim queue/fee backend and fee address **do not appear in the public GitHub main** (last known SHA \`f807abf...\`, Nov 6); no live production backend or JavaScript/network-source audit was possible in read-only Browser. This is a material verification gap.

### Exclude other pump.fun mints from official FORK

- Direct Token-2022 mint reads, metadata extracted from raw account bytes:
  - \`DSjhrziLzcFcVQZnK8fXxkMbYYo4KN51MT5Aqvy7fork\`: metadata symbol \`HIGHIQP\`, not \`FORK\`.
  - \`BPHH5U39dbgts1fbCvLjEvSJ8tfeq3nihK8hrHWifork\`: metadata \`MEOW CAT / MEOWP\`.
  - \`HTaBmiNnLkMZEcgmpAFU76LG3akLKPSfJxfXu3pffork\`: metadata \`doge / DOGEP\`.
  - \`3UuwDcYf3Q5SjNoxhUrXAR24PTH8A1KpG5ywxaCm3crH\` held by public treasury: metadata \`dogecoin / DOGECOINP\`.
- **None of these checked mints is official $FORK.** A \`fork\` vanity suffix is not a canonical issuer Mint. Public \`src/config.js\` \`token.ca:''\`; issuer X bio says \`CA: not live yet\`; issuer announced approx TGE 2026-11-12 01:20 Bangkok, **schedule not onchain execution**. No independently verified official mint, FORK token custody, distributor, ERC/SPL entitlement, or user payout transfer at this observation.

### Updated assessment

Fee wallet attribution upgraded from \`UNKNOWN_UNLINKED\` to **\`TREASURY_FUNDED_ACTIVE_PUMP_SIGNER\`**. This reduces concern that the receiver is completely unrelated to the official platform. It **does not** establish rank #308, code security of production distribution, token launch completion or future credit to user. User's one-time signing transaction has no dangerous ongoing approvals, but token delivery is still dependent on operator's later decisions. **No additional fees, no paid meme launch solely to unlock remaining 12,600, no trading of imitations until canonical Mint and actual transfers are verified.**

---

## 2026-11-11 ~21:24–21:30 Bangkok: wallet claim-fee safety verification, OFFCHAIN_QUEUE_ONLY, no official FORK mint

**Current evidence priority:** direct Alchemy Solana finalized RPC > authenticated forks.wiki live /claim and first-party @wikifork X post > old public fork GitHub source. No token sale, token claim, wallet signing, monitoring, notification or automation performed by this investigation.

### User participation and promised delivery
- Connected official `https://forks.wiki/claim?auth=ok` shows X account `@lxx794`, wallet `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`, **25,200 FORK pending** (prior 20,700 pending outdated); **12,600 "Available to claim"**, **12,600 "Unlock to claim"** only after launching a coin on forks. Three social tasks on new claim flow counted +250 each. The "Claimed" label belongs to queue **#308**, indicating paid spot in distributor queue, **NOT an actual token transfer**. Sending panel explicitly stated **0 of 0 wallets sent**, 0%; project states it will transfer FORK to wallet at launch, at its discretion. Exact final entitlement and redeemable amount are not onchain binding.
- Source X: https://x.com/wikifork/status/2120522026117181787 ("launch $fork in 4 hours; claim is live"; first 500 launched coins +5,000 FORK project claim). Tweet Snowflake creation time **2026-11-11 14:20:23 UTC / 21:20:23 Bangkok**. Announced **approximate scheduled launch 2026-11-12 01:20 Bangkok**, not a confirmed TGE; do not convert announcement into actual launch or give exact-second launch assurance.
- Official site's /market latest indexed content says `$FORK not launched yet`; public GitHub `forkwiki/fork` main head `f807abf1248ceadf47542cf7e223b223819e84f0` from Nov 6 still hardcodes `token.ca:''`; treasury wallet's latest signatures checked have **no verified official FORK create** at evidence time. Search results contain numerous same-name "FORK"/"Forkwiki" meme mints: **not canonical without first-party project mint corroboration**. Official CA, liquid market, contract-enforced claim, batch distribution remain **UNCONFIRMED**.
- At the ~21:29 Bangkok Solana finalized RPC context, user Tokenkeg and Token-2022 token account listing found **no confirmed FORK issuance into that wallet**. This does not establish what might happen later.

### Actual signed transaction, programs and cost
- Successfully finalized user fee transaction [Solscan](https://solscan.io/tx/21HaGmHa9suUiXpfee4TYUQ1Bn8yA4MjUoAYDMwNLc3vZp97W9DqL68WJzBKPhuq3SsjgDHkofG2RmM5n5KNFUux), slot **468155590**, timestamp **2026-11-11 14:23:48 UTC / 21:23:48 Bangkok**, `meta.err=null`.
- Parsed instructions: ComputeBudget x2, **SystemProgram.transfer** `2,000,000 lamports = 0.002 SOL` from user wallet `BP7h…4dSp` to **`Da71cES3NeUMLpW3MuNGkCVTht3jceik1RtNLrbqC6jV`**, and Memo `forks.wiki $FORK claim fee`. Network transaction fee `11,000 lamports=0.000011 SOL`. Exact native wallet prebalance 55,849,243 -> postbalance 53,838,243 lamports, net decrease **0.002011 SOL**. No inner instructions, SPL token program invocation, approve, delegate, setAuthority, native program invoke to an untrusted dApp. **NARROW wallet-signature finding: no ongoing/token-spending approval granted by this transaction; no guarantee other site interactions are safe.**
- Verified independent OTHER wallet payment [example](https://solscan.io/tx/3TjUrJLbDRcJ6cRCBrCmSubD1EfRozTXo1HX6fTBTpQRRtHANrLX1dPZn2G5Dera9zRUC2Bf4QpnsFkuGtsNHMr) transfers **another 0.002 SOL with same memo to same recipient**. The recipient is a **System Program owned basic account** (not a Solana smart contract / escrow). Its observed balance at slot 468156442 was **9.381677141 SOL**, which does **not** mean SOL is reserved for air drops or that all money came from claim fees.
- **CORRECTED RECIPIENT IDENTITY**: the claim wallet `Da71cES3NeUMLpW3MuNGkCVTht3jceik1RtNLrbqC6jV` differs from the public GitHub launch.treasury `61468ik7HhYNg8ixQYeF9caMNVm57PqTy3tyQ28F6Y5e`, **but direct onchain funding and pump.fun signing now STRONGLY VERIFY their operational association**: treasury funded 0.15 SOL to fee wallet, which immediately signed pump.fun fee sharing. Human ownership is still unverified. The website Claim-specific backend remains absent from public Nov 6 code; no contract-escrowed FORK entitlement exists in the inspected user transaction. See newer forensic section above.
- Risk assessment: **wallet-transaction authorization LOW for this exact signed transfer**, **project distribution/issuer counterparty risk HIGH/UNVERIFIED**, **production claim and queue implementation NOT AUDITED**. Fee receiver is strongly chain-linked to public treasury, while delivery remains unsecured and official FORK Mint unverified.
- User recommendation: **DO NOT pay another fee, do not launch a coin or buy a homonymous FORK to unlock the remaining 12,600**, until issuer links the exact mint and a traceable payout batch from identified operator wallet. Confirm claimed queue 308 only in site ledger; actual payout requires real SPL token `Transfer` from attributable distributor to recipient mint-associated wallet. A "Paid"/"Claimed" badge is not delivery.

### Evidence/source links
- https://forks.wiki/claim
- https://forks.wiki/market
- https://x.com/wikifork/status/2120522026117181787
- https://github.com/forkwiki/fork/blob/f807abf1248ceadf47542cf7e223b223819e84f0/src/config.js
- https://solscan.io/tx/21HaGmHa9suUiXpfee4TYUQ1Bn8yA4MjUoAYDMwNLc3vZp97W9DqL68WJzBKPhuq3SsjgDHkofG2RmM5n5KNFUux
- https://solscan.io/account/Da71cES3NeUMLpW3MuNGkCVTht3jceik1RtNLrbqC6jV

---


Status: WATCH / PRE_TGE / NO_GO_FOR_FUNDED_TRADING。  
证据时点：2026-11-10 18:33 起，曼谷时间。仅执行公开数据读取、GitHub 检查、只读链上 RPC 和用户已登录网页读取。未进行钱包签名、交易、自动化或监控。
本报告遵守 Mission 项目分析框架、Evidence Workflow、token_trading_principles、MISSION_SPEC。

## 1. 项目身份及实际阶段

官网 https://forks.wiki/ ；指南 https://forks.wiki/guide ；发行页 https://forks.wiki/launch ；市场 https://forks.wiki/market ；官方 X https://x.com/wikifork ；项目网站和官方 X 所链接源码 https://github.com/forkwiki/fork 。

业务是：GitHub 仓库血缘树/搜索、绑定仓库的 Solana meme 币发射台、市场终端及自家 FORK 预发行积分。拟使用 Solana mainnet 与 pump.fun，调用 Jito bundle，面向其他 Solana 代币交易经 Jupiter；项目明确说明与 GitHub、pump.fun、Jupiter 或仓库作者无官方隶属。

**官方 FORK 尚未发行**：官网市场显示“FORK not launched yet”及“On forks 0”，官方指南称官方币将与 forkwiki/fork 仓库对应，其他同名币均不可据此认定为官方币；源码 src/config.js 中 token.ca 为空字符串，chain=solana，launch.reserved 包含 forkwiki/fork。未核实官方 Mint/CA、交易池、Token Metadata、token supply、TGE、Claim、锁仓地址及 LP。外部同名币不得作为发行价或行情来源。

网页当前可运行 GitHub 仓库图谱、X OAuth 登录、计入 pending 积分、GitHub 可选关联、社交任务进度显示；这证明是一个公开可用的网站服务，但其核心发币模块**未发现独立成功主网发射证据**。官网 /launch 同时使用“Season 0 live”、0 coins，首页有“launches open soon”，不能把推广任务上线等同成功发币。成熟度按框架暂列 Level 1 网页产品/源码存在，链上发币 Level 3 尚未核实。

源代码 GitHub main 的最后已查提交为 f807abf1248ceadf47542cf7e223b223819e84f0，时间 2026-11-06 12:48:03 UTC。代码有客户端、Netlify 后端、Supabase SQL、链上 Jito/pump.fun 构造，且有多次更新。**生产源码一致性警示**：Git main src/config.js 仍含 x.post='20', postBy='jack' 的示例值，而在线用户任务链接指向 @wikifork 自己的近期帖子。这表明官方公开 main 与线上配置至少有差异；开源代码审查不能等于生产环境已通过安全审计。

## 2. 业务证据、团队与资本

有效在线功能：仓库图谱、代币市场界面、积分数据库用户账户。网站自报 On forks 0 coins、Season 0 0 devs；截至本轮没有可独立确认的成功发行交易、真实链上交易手续费入账、付费用户、收入、TVL、重复交易量、留存或净利润。**不得将社交活动量、免费激励参与者或 Jupiter 已存在的第三方代币交易归属于 forks 的收入和客户。**

源码配置的计划收费：在 forks 交易终端交易或发币时初始购币附加 0.5% 平台费用，绑定仓库创作者费分配中 forks 自己占 10%。这是设计/收费参数，未核实实际持续收到的 SOL/USDC 费用。官网团队实体目前只确认 forkWiki GitHub owner/X 账户身份；**创始人真名、历史项目/退出、融资金额、投资机构、私募成本、审计机构均未核实**。官方 X 于 2026 年 11 月新建，互动与关注/转发激励强相关，无法证明有自然付费用户。

## 3. FORK 用户奖励与可领取性

用户已登录官网网页最近一轮状态：X scan 11,700 pending；社交五项任务 4/5、已计 6,000；GitHub 公开账户 OAuth 绑定已经计入 +3,000；合计为**20,700 FORK PENDING**。第五项 Quote 尚未完成，网站显示可能 +3,000；最终所得需网站服务器确认，不能提前按已到账计。官网仍显示“add a Solana wallet ... so the airdrop knows where to land”，因此**用户还没有在该页面确认保存 Solana 收款地址**。网页存入的是公开钱包地址字符串，代码不要求空投登记时的私钥/助记词或交易签名。

官方规则：邀请完成三项任务的好友 +2,000 pending，连接 GitHub +3,000，五项社交任务总计 +9,000，X scan 按账号历史计分。Season 0 的 200,000,000 FORK 是**该赛季声称的奖励预算池**，不是 FORK 总供应量。按项目方规则，发射仓库币并在同笔 bundle 购买才有 +1,000 起的积分资格；市值里程碑和迁移最高累计 +1,000,000 pending/币，市值需至少两次间隔 10 分钟被观察到等条件。赛季结束为池用完或另发公告，未公布确切结束日。

**FORK TGE：未确认；官方 Mint：未确认；总供应量、初始流通、解锁、团队份额、VC 成本：未确认；快照时间：未确认；领取开放日：未确认；领取方式（主动 Claim 或自动派送）：未确认；领取合约：未确认。** 当前 Solana 钱包里没有由页面积分本身构成的真实 FORK 余额。官方指南明确写 pending allocation 不是代币余额、也不保证价值。

注意区别：作者如果在某仓库对应的 pump.fun 币分成中有权利，可在 pump.fun 用 GitHub 身份领取**creator fees**。这和 FORK 预发行活动的空投 Claim 是两套不同机制，前者不能用来提前领 FORK。

Mission TGE readiness：T1 发行意图存在；T2 网站后台积分账本存在（链上奖励资金未证实）；T3 空投 Claim 架构不明；T4 正式 FORK Mint 未确认；T5 分发金库与 LP 未确认；T6 官网空投 Claim 尚未开放；T7 市场不存在官方可核实交易对；T8 发行完成没有证据。

## 4. 安全检查：登录、地址、签名和奖励规则

- X OAuth 源码 netlify/functions/auth-start.mjs 使用 OAuth2 + PKCE，声明 users.read tweet.read 两个只读 scope，无 tweet.write；GitHub 可选 OAuth 在 auth-github.mjs 不请求写 scope，仅读取用户公开资料。以上是源码的意图，不保证部署不变，实际应核对 X/GitHub 授权页面的权限。
- netlify/lib/server.mjs 对网站 session cookie 使用 HMAC 封装和 HttpOnly / SameSite=Lax / HTTPS Secure 选项，并对 JSON 修改请求检查 Origin；属合理基础安全措施但不是第三方审计。
- **具体安全边界**：auth-callback.mjs 与 auth-github.mjs 中授权 token 的 revoke fetch 未等待返回结果，失败被静默忽略；因此不能保证 OAuth token 立刻或一定成功撤销。这不是已经发生泄漏的证据，但“源码声称一定撤销授权”的说法无法成立。
- 免费 FORK 地址登记页面只要求**Solana 公钥**，不应索要 seed/private key。建议用一个独立、低余额钱包地址并核对保存结果；不要因为空投诱导链接去签署未知 Solana 交易。
- 积分仍是项目控制的 Supabase 账本。没有合约托管的确定 claim entitlement。运营方可决定未来换币、快照、供应及规则；这种中心化信用风险远高于只读 X OAuth 的技术风险。
- 奖励质量缺陷：公开 supabase/migrations/0003_refs.sql 的 Follow/Like/Repost/Comment 大多只检查打开任务、等待指定时间而非独立查询 X 实际互动；Quote 主要验证 X 链接形态、username、tweet ID 对应发布时间及不重复，不验证内容一定为官方 quote。这降低了项目激励规则防滥用/公开评分对真实参与度的证明力，并留下日后人工审核/修订规则风险。只作为安全与收益证据，不提供刷取方式。
- **付费发币/交易流程风险显著不同**：官方指南称由用户 Solana 钱包签名 3–4 笔交易并作为 Jito bundle 提交，包括 pump.fun 账户 rent、fee sharing accounts、Jito tip 和可选预先买币金额（源码最大 20 SOL）；交易终端默认 5% 滑点，forks 平台费 0.5%，另有 pump.fun 费用。Netlify 代码宣称校验签名交易字节且不持有用户私钥，但与生产一致性未证明，也缺独立审计；任何真实签名应人工核对收款人、花费和授权。
- 官网源码配置公开 treasury 61468ik7HhYNg8ixQYeF9caMNVm57PqTy3tyQ28F6Y5e ，Solana 主网 finalized slot 467706334 读得 189691374 lamports（0.189691374 SOL），有最近链上签名。这仅证明源码声称的公开地址活跃，不代表官方 FORK Mint 已存在、已发行或该账户已核实为团队控制。

## 5. Tokenomics、风险收益、市场与 PM

当前没有可验证的 FORK 发行总量、FDV、初始流通、投资人成本、主池深度、真实成交价格、解锁/分发机制。200M 赛季积分预算不可当成完全流通供给；20,700 pending 也不能按其他冒名 FORK 市价计入投资组合或可清算 NAV。

下行情景：无 TGE / 无可兑换 Claim / 分配被取消，币值无法确认；中性情景：发行并分配，但锁仓/低流动性限制可实现收益；乐观情景：存在独立真实交易需求及足够退出流动性。缺少关键参数时不虚构 FDV、收益倍数、TGE 时间或成功概率。平台通过鼓励用户主动买入自发币来换积分，成本可以是确凿 SOL 损失，而奖励仍是 pending，当前不具备“投入资金刷积分”的正期望值验证。

预测市场项目专属检索：2026-11-10 查了 Polymarket、Kalshi、Limitless、Predict.fun 的 forks.wiki / wikifork / FORK 组合，**未检索到可验证的项目专属 PM 市场**；网页索引检索不代表彻底扫描每个平台全部未索引盘口。无真实赔率可填。

## 6. 判断、可执行动作与状态边界

**WATCH**：可保留免费获得的 pending 资格；风险/收益考量上不建议为“发币赚最高百万 FORK”主动投入 SOL，也不建议在未知第三方页面购买同名币、签授权或将高余额主钱包用于实验。

建议用户完成尚未完成的官方 Quote 验证，并在准确的 forks.wiki 免费任务页面填写独立 Solana 收款地址；保存后验证页面显示。该建议不代表 ChatGPT 已代用户操作，且最终空投资格和到账仍未确认。

未来能升级 SETUP 的硬条件：官方 X/官网/源码统一公布官方 Mint；Solana 直接核验 Mint、发行/销毁/冻结权限和真正 LP；正式总供应/奖励/团队比例和 unlock；有可信分发金库/Claim 合约/公开日期，官网真实 Claim 成功，并独立评估交易深度、可兑现净收益。没有这些不预测 TGE 或代币价格，也不建立新监控。

## 原始核查来源

官方网站：https://forks.wiki/ ; https://forks.wiki/guide ; https://forks.wiki/launch ; https://forks.wiki/market ; https://x.com/wikifork

官方固定源码：https://github.com/forkwiki/fork/tree/f807abf1248ceadf47542cf7e223b223819e84f0

配置：https://github.com/forkwiki/fork/blob/f807abf1248ceadf47542cf7e223b223819e84f0/src/config.js
X OAuth：https://github.com/forkwiki/fork/blob/f807abf1248ceadf47542cf7e223b223819e84f0/netlify/functions/auth-start.mjs
X callback：https://github.com/forkwiki/fork/blob/f807abf1248ceadf47542cf7e223b223819e84f0/netlify/functions/auth-callback.mjs
GitHub OAuth：https://github.com/forkwiki/fork/blob/f807abf1248ceadf47542cf7e223b223819e84f0/netlify/functions/auth-github.mjs
奖励 SQL：https://github.com/forkwiki/fork/blob/f807abf1248ceadf47542cf7e223b223819e84f0/supabase/migrations/0003_refs.sql
奖励和钱包页面：https://github.com/forkwiki/fork/blob/f807abf1248ceadf47542cf7e223b223819e84f0/src/quest.js
发币后端：https://github.com/forkwiki/fork/blob/f807abf1248ceadf47542cf7e223b223819e84f0/netlify/functions/launch.mjs
公开配置钱包：https://solscan.io/account/61468ik7HhYNg8ixQYeF9caMNVm57PqTy3tyQ28F6Y5e
