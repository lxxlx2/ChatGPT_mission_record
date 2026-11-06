# 1609SAT / MetaDAO Apps Program：SAT 备考产品、公售估值、早期流通与退出风险调查

## 2026-11-06 user additional SAT contribution verified at 10:26 Bangkok

**Evidence class: DIRECT SOLANA MAINNET RPC, successful transaction / per-user FundingRecord.** This section **supersedes the previous $300-only position snapshot** elsewhere in this historical research. User explicitly reported adding funds, and requested read-only on-chain confirmation; no user-requested additional action beyond research record update.

- User-specific [successful second Fund transaction](https://solscan.io/tx/5hSMbGTKmRMtskd8RTg3RBFHBWsiFDzvSjjg8Pv2WLPUYnTpR4riuX1Vt3XEZszhMEuoDCyhZxCv7kJwzxfZg5Qk) at **slot 465957443**, **2026-11-06 03:26:44 UTC / 10:26:44 Bangkok**: `meta.err=null`; nested SPL Token transfer **318,190,000 raw USDC units = 318.19 USDC**, signed by user wallet `BP7h…4dSp`, from USDC token account `AaHmxVnUryLCrSr32zxrDGzfafXTvuHATURZbBy6XQ6A` into SAT canonical USDC escrow `3HixScNNPUDXU4XLf1QqYkFQCqcUimoW1Bck95fw1AZh`; instruction `Fund` succeeded.
- Previously established first successful Fund transaction [ajQNxZ...](https://solscan.io/tx/ajQNxZKFbMQoxp5axvKJ9tFpsFWyaLLoZyhAf2KKXPqM3hroGc4WNSPVoknG8HPEyyKJK5TXTZggD2ViGbzi4KG) at slot 465815490, 2026-11-06 02:00:28 Bangkok, **300 USDC**.
- The exact user FundingRecord `45jwzpest3hPhhDXoS6WqxJ2t3Z2kLDZUrQxMXQ84FNg` was independently read and decoded at **slot 465962174**: `committed_amount=618190000` raw (**618.19 USDC total**), `approved_amount=0` (**not yet settled**), `is_tokens_claimed=false`, `is_usdc_refunded=false`; transaction history for this PDA has precisely **two successful Fund signatures** listed above. This record is direct evidence of *escrowed subscription rights*, **not** 618.19 SAT cash investment cost, actual SAT token allocation, spendable wallet USDC, or final realized P&L.
- New spending since previous historical snapshot: **318.19 USDC**. Economic status `COMMITTED_618_19_USDC / ALLOCATION_PENDING / REFUND_PENDING / NO_SAT_CLAIMED / NO_ADDITIONAL_TRADE_EXECUTED_BY_CHATGPT`. Continue to distinguish nominal commitments from eventual actual accepted amount and refundable remainder; founder/program approvals and final per-SAT price remain unknown.

**No monitoring, alert, new automation, email, additional contribution, wallet action or production changes** performed in this audit.

---


## 2026-11-06 SAT live raise and user $300 direct funding proof

**As-of:** 2026-11-05 19:03 UTC / 2026-11-06 02:03 Asia/Bangkok, live read-only Solana mainnet RPC. The observed funds and orderbook are snapshots during an actively changing raise, not final allocations or token price forecasts.

### Direct on-chain evidence

- SAT v0.7 Launch address `B9QX36vNtxsSr3o1A2wNpihUC2bELehqP7hvYUsDcuRT`, Token Mint `BSwp4GjLnejXKqvmjueJmPXC7UZhNoF6RuMQJRpSmeta`, canonical USDC Escrow `3HixScNNPUDXU4XLf1QqYkFQCqcUimoW1Bck95fw1AZh`. Program `moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM` verified and decoded against official pinned [v0.7 Launch struct](https://github.com/metaDAOproject/programs/blob/e2ba4e9be712248ae4874f3b0621eaac69376c98/programs/v07_launchpad/src/state/launch.rs).
- `StartLaunch` succeeded; `unix_timestamp_started=1793905201`, i.e. **2026-11-05 19:00:01 UTC / 2026-11-06 02:00:01 Bangkok**. LaunchState `Live=1`, `seconds_for_launch=345600` (4 days), so **scheduled on-chain contribution-window expiry 2026-11-09 19:00:01 UTC / 2026-11-10 02:00:01 Bangkok**, absent a valid contract-level extension. `unix_timestamp_closed=None` until close is executed.
- Read account at slot **465816407**: `total_committed_amount=482942520000` raw USDC = **482,942.52 USDC**; `total_approved_amount=0`; `state=Live`; minimum raise **100,000 USDC**. Direct `getTokenAccountBalance` of USDC Escrow at slot **465816159** was **479,942.38 USDC** and rose rapidly; differences across nearby slots reflect new inflows, not an unexplained deficit. The browser's same-window Public Sale was ~433K with MetaDAO $50K shown separately. Original user screenshot at 02:00 shortly after launch showed 260,787 USDC; later amounts must not be retroactively attributed to the screenshot instant.
- **USER POSITION CONFIRMED:** user’s wallet identity redacted in readable narrative (`BP7h…4dSp`). Exact [successful Fund transaction](https://solscan.io/tx/ajQNxZKFbMQoxp5axvKJ9tFpsFWyaLLoZyhAf2KKXPqM3hroGc4WNSPVoknG8HPEyyKJK5TXTZggD2ViGbzi4KG): slot **465815490**, blockTime `1793905228` = **2026-11-05 19:00:28 UTC / 2026-11-06 02:00:28 Bangkok**, 27 seconds after actual StartLaunch. Successful status `err=null`, **300.000000 USDC** debited from user's USDC ATA and credited to SAT launch USDC Escrow. User ATA postbalance **7.570752 USDC**. User-specific on-chain FundingRecord PDA `45jwzpest3hPhhDXoS6WqxJ2t3Z2kLDZUrQxMXQ84FNg`, direct decode at slot **465816407**: `committed_amount=300000000`, `approved_amount=0`, `is_tokens_claimed=false`, `is_usdc_refunded=false`, `last_accumulator_update=1793905228`. `approved=0` is an expected pre-settlement status, NOT failed participation.
- Browser's top-4 commitments at this snapshot were ~**402,004.89 USDG/USDC** split **200,005.49 + 100,000 + 51,999.70 + 49,999.70**, about **83.2%** of this 483K snapshot. **This is an official page UI aggregate**, not independently audited funder classifications or proof that all four are non-affiliated. They can affect raw capital-weighted allocation; early-fill and Ownership Score weights mean raw wallet amounts alone do not calculate final token share. The UI showed user's Ownership Score **1,125.33**, rank **#26,409**, not a verified on-chain multiplier.

### Valuation and allocation caveat: important correction to any fixed $0.01 assumption

- Official [sale docs](https://metadao.com/docs/sale) permit a **discretionary approval amount** after close; the 100K amount is a minimum and target, not necessarily an immutable hard cap. Verified official [v0.7 SetFundingRecordApproval](https://github.com/metaDAOproject/programs/blob/e2ba4e9be712248ae4874f3b0621eaac69376c98/programs/v07_launchpad/src/instructions/set_funding_record_approval.rs) permits per-funder approval after `LaunchState::Closed`, bounded by each funder's actual commitment; `total_approved_amount` is the sum of approvals, not preset at 100K.
- **On-chain completion price:** official [complete_launch.rs](https://github.com/metaDAOproject/programs/blob/e2ba4e9be712248ae4874f3b0621eaac69376c98/programs/v07_launchpad/src/instructions/complete_launch.rs) computes `price_1e12 = total_approved_amount * 1e12 / TOKENS_TO_PARTICIPANTS`, with fixed **10M participant tokens**. Official [claim.rs](https://github.com/metaDAOproject/programs/blob/e2ba4e9be712248ae4874f3b0621eaac69376c98/programs/v07_launchpad/src/instructions/claim.rs) computes user's SAT as `approved_amount * 10M / total_approved_amount`. If approved total is exactly 100K, effective price = **$0.01/SAT**, FDV~**$1M** at nominal 100M. If 150K is approved, **$0.015/SAT** and ~$1.5M FDV; if 200K, **$0.02/SAT** and ~$2M FDV. These are **conditional scenarios, NOT predictions**. There is no evidence yet of any final approved amount; the *Live* Launch account read `total_approved_amount=0`.
- Under a **simple equal-weight pro-rata illustration only** at 482,942.52 gross commitments, 50K MetaDAO pre-commit approved first, exactly 50K accepted from remaining 432,942.52 public pool, a $300 public contribution would correspond to **~$34.65 accepted**, **~3,465 SAT** at $0.01 and **~$265.35 refunded**. **This is NOT an allocation forecast**: final commitments can increase over four days, the actual algorithm applies time accumulated, early-fill boost, Ownership Score, pre-reserved Aligned Party priority, per-user cap and possible founder discretionary accepted amount. Do not treat it as user entitlement. Full $300 accepted only if `approved_amount` actually reaches $300.
- After close, [v0.7 approvals](https://github.com/metaDAOproject/programs/blob/e2ba4e9be712248ae4874f3b0621eaac69376c98/programs/v07_launchpad/src/instructions/set_funding_record_approval.rs) occur in a **2-day post-close authority window**; then completion and claims may follow. A contribution-window expiry is **NOT** a token claim time. Monitor only if separately explicitly authorized; none created here.

### PM investigation (as of this scan)

- Dedicated searches of **Polymarket, Kalshi, Limitless, Predict.fun, Opinion** for `1609SAT`, `1609+`, `SAT MetaDAO`, and project-specific FDV/fundraise returned **NO VERIFIED project-specific tradable market or quoted probability**. This is search coverage and NOT proof none can be privately listed/newly opened.
- A verified Polymarket event exists for **another unrelated issuer**, [over.computer MetaDAO commitments](https://polymarket.com/event/total-commitments-for-the-over-computer-public-sale-on-metadao); its prices/probabilities must never be applied to SAT. Do not invent a SAT PM probability.

**Updated user-specific decision:** current status `COMMITTED_300_USDC_CONFIRMED / SAT_FUNDING_RECORD_READ / ALLOCATION_NOT_APPROVED / LIVE_SUBSCRIPTION_4D / OVERFUNDED_DEMAND_NOT_FINAL_SALE / PM_SAT_MARKET_UNVERIFIED / CLAIM_NOT_OPEN / NO_ADDITIONAL_FUNDING`. This is a read-only audit of a transaction the user already completed; do not submit any additional funds, open PM positions, or modify automations.

---


## 2026-11-05 Apps Program investment model and economic checks

**Evidence class**: MetaDAO official documentation and live issuer page are PLATFORM/ISSUER CLAIMS unless separately validated. The Ecosystem Fund governance vote is independently visible as a passed MetaDAO decision, but fund transfers and the particular 1609SAT investment are **NOT** independently proven settled.

- MetaDAO official Apps Program entry: https://metadao.com/apps . It says the platform commits first, the app raises publicly, and founders earn compensation against performance milestones. This is a platform operating model, not a guarantee of returns for any given new token.
- MetaDAO decision `METADAO-042` (passed): https://metadao.fi/decisions/metadao-042 . The motion authorizes donating the former Ownership Capital escrow to a MetaDAO LLC Ecosystem Fund. It quotes a historic escrow balance of **1,908,771.32 USDC** and proposed individual investments of **$50K-$150K** in **$50K-$300K** early-stage raises, prioritizing consumer apps. The decision's passed status is verifiable; actual fund movement to a new Ecosystem Fund multisig and the **1609SAT-specific $50K transfer** have not been separately verified. The directly inspected SAT escrow at slot 465768722 remains **0 USDC**.
- The 1609SAT issuer on https://metadao.com/companies/1609sat reports **400+ paying users**, **$5,000 monthly revenue**, **$3,500 monthly profit**, and **15,000 users**, all issuer-stated. Annualized $5,000 MRR gives **$60,000 annual revenue run rate**, and the **$1M token FDV** is **16.7x issuer-reported annualized revenue**. This P/S-style number is a narrative sensitivity only: tokenholders' value capture from company profit is **not established**, and revenue, profit, retention and CAC are not audited.
- The $100,000 target less **20% reserved for initial USDC pool capital** implies about **$80,000 of launch-raise treasury USDC** if fully raised and those generic mechanics apply. At the onchain **16,000 USDC/month** spending limit, this funds **5 months of allowed spending without other income or spending changes**. This is a scenario, not observed escrow funding or a measured cash burn.
- The issuer's nominal **87.1% team additional allocation** is a large long-term concentration, yet the issuer claims 90-day price average milestones (2x, 4x, 8x, 16x, 32x) and a **$25K/30-day team sale cap during the first 18 months**. Current direct Launch `additional_tokens_amount=87.1M SAT`; the designated additional recipient has not been independently bound to the specific downstream restrictions. Do not assume 87.1M tokens are initially tradable, and do not assume contract enforcement until verified.
- At the intended $100K gross raise, the generic rule dedicating 20% USDC to LP is about **$20K on the USDC side**, versus a public sale allocation of **5M SAT**. This implies potentially high early exit slippage and uncertain realizable ROI even if quoted FDV rises. LP existence and depth remain to be checked after launch.
- Generic official docs https://metadao.com/docs/sale and https://metadao.com/docs/whats-new describe a 4-day funding accumulator, early fill boost, Ownership Score and reserved Aligned Parties. Public commitments may be partially accepted and refunded; a $300 commitment is **not** equivalent to $300 confirmed allocation. This is independent from the unrelated SLOP auction's 300 USDG budget.
- Token economic framing: MetaDAO describes an 'ownership coin' through control of treasury and key IP (https://metadao.com/docs/ownership-coins), but platform Terms (https://metadao.com/terms) do not promise ordinary equity or contractual profit distribution. Do not convert issuer revenue multiples mechanically into token intrinsic value, dividends or a guaranteed claim.
- External user signal is limited and mixed: a few small Reddit SAT prep discussions include both supportive comments about past-paper question banks and skepticism about paying for AI-assisted practice. These are unverified anecdotes, not validated subscriber churn or company financials.

**Decision gate**: Platform architecture worth tracking; 1609SAT remains `WATCH / NO_GO` for position sizing until (i) the SAT `StartLaunch` succeeds and quote escrow or funding record is reconciled against the stated $50K, (ii) actual public accepted subscriptions, (iii) project-specific performance package recipient/program and lock enforcement, and (iv) real post-close LP exit quotes and revenue evidence are checked. No change to user budget, alerts, execution or trading.

---



## 2026-11-05 direct SAT Solana account and funding audit

**Observed:** Solana slot 465768722 at 2026-11-05 16:13:33 UTC / 23:13:33 Bangkok; read-only Alchemy Solana mainnet; no wallet signatures, trades or automation. This section supersedes the earlier identity and contract-address unknowns, but preserves the earlier historical research.

**Onchain identity and transaction:**

- Official MetaDAO v0.7 Launchpad program: moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM. Direct decoded Anchor Launch account: [B9QX36vNtxsSr3o1A2wNpihUC2bELehqP7hvYUsDcuRT](https://solscan.io/account/B9QX36vNtxsSr3o1A2wNpihUC2bELehqP7hvYUsDcuRT), account discriminator 903333a3ce55d526, 785 bytes, owner matches program. Successful InitializeLaunch transaction on 2026-11-04 18:56:58 UTC: [2wB8pyVHwxTNvRsmCkwmRRG4DsMJSjmgWt5K7QKFw24ZdaGti3nJYbGrRiJWd6NVSKEGKEtvVRszQqrvvGbGAupz](https://solscan.io/tx/2wB8pyVHwxTNvRsmCkwmRRG4DsMJSjmgWt5K7QKFw24ZdaGti3nJYbGrRiJWd6NVSKEGKEtvVRszQqrvvGbGAupz).
- SAT Mint: [BSwp4GjLnejXKqvmjueJmPXC7UZhNoF6RuMQJRpSmeta](https://solscan.io/token/BSwp4GjLnejXKqvmjueJmPXC7UZhNoF6RuMQJRpSmeta). Direct Solana Metaplex Metadata account 2SJ32k2vxBGhKfzRnDVenxCLadySwA15g2S7VsUUKbWZ decodes name SAT and symbol SAT; URI: https://tokens.metadao.fi/token-metadata/841/6bf836d53427b5f379c3c5cb9e72ec313c7e974cee9a20642b7514da2d660c27.json .
- Launch config directly decoded against official [v0.7 Launch Rust struct](https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/state/launch.rs): minimum_raise_amount=100000000000 raw USDC (100,000 USDC), monthly_spending_limit_amount=16000000000 (16,000 USDC), additional_tokens_amount=87100000000000 raw SAT (87,100,000 SAT), performance_package_token_amount=1000000 raw SAT (1 SAT), seconds_for_launch=345600 (4 days). These exact values plus SAT metadata establish a **strong, project-specific 1609SAT attribution**, but the production page-to-Mint identity binding has not been extracted from JavaScript/network or directly published, so label issuer-linked identity **HIGH_CONFIDENCE_INFERRED** rather than separately issuer-attested.

**Funds and timing:**

- Dedicated canonical USDC quote escrow: [3HixScNNPUDXU4XLf1QqYkFQCqcUimoW1Bck95fw1AZh](https://solscan.io/account/3HixScNNPUDXU4XLf1QqYkFQCqcUimoW1Bck95fw1AZh), quote mint EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v. Direct getTokenAccountBalance and getAccountInfo at slot 465768722: **0 USDC**. getSignaturesForAddress(escrow) returned only the Nov4 initialization transaction, no later successful transfer. Direct Launch total_committed_amount=0 and total_approved_amount=0.
- The public website displays MetaDAO Pre-Committed 50K, a **platform pledge**; **NOT verified as 50,000 USDC in this Launch escrow**. No assumption that the funds are absent from separate MetaDAO treasury accounts or that the promised transfer will fail.
- Direct Launch state=Initialized (0), unix_timestamp_started=None, unix_timestamp_closed=None, launch duration 4 days. Its actual start and close timestamp are **UNCONFIRMED**; only *if* the advertised Nov5 19:00 UTC / Nov6 02:00 Bangkok opening executes on time is the implied end Nov9 19:00 UTC / Nov10 02:00 Bangkok. Official [StartLaunch source](https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/start_launch.rs) sets the true start timestamp only on successful execution.
- Direct getTokenSupply at slot 465768719 gives **100,000,001 SAT**, six decimals. All 100,000,001 SAT were in dedicated token vault [DKKygjCaqWRTzjaGHtydA4haF3JJUqFn7eHhwK8Wbh2q](https://solscan.io/account/DKKygjCaqWRTzjaGHtydA4haF3JJUqFn7eHhwK8Wbh2q) at slot 465768722. The 1 SAT amount beyond issuer nominal 100M corresponds to the Launch performance allocation of 1 SAT. Do not invent how or whether it will be burned.
- The 87.1M additional-token recipient UkkkU6yNnLYeSfPW46L6Y1JC5bu6o6wx7M45Yr4iWmS currently has zero account data and a System Program owner; its pubkey is off curve, suggesting a PDA, but **the specific downstream enforcing program and advertised 90-day price unlock plus 25K/month team sell cap remain UNVERIFIED**. Generic [v0.7 additional allocation handler](https://github.com/metaDAOproject/programs/blob/develop/programs/v07_launchpad/src/instructions/claim_additional_token_allocation.rs) allows release to the configured recipient after LaunchState Complete; cannot infer the recipient's future unrestricted custody from this fact alone.
- Excluded superficially nearby program launches FINAL (4WSZkN6p4wfqGqQSwTnvpCTnjNMdazDebYQJu14nmeta, 50K minimum) and SENDR (AuYQ5Y2zmFppLUhWT1i2AQPdswChgQ9vuMu9Ts61meta, 250K minimum) after direct Metaplex verification. v0.6 and v0.8 Launchpad program latest observed transactions were from July 2026, while v0.7 was active during Nov4/5.
- Generic filtered getProgramAccounts calls failed with **RPC 429 compute-per-second limit**. Individual getAccountInfo, getTokenAccountBalance, getTokenSupply, getSignaturesForAddress and reconstructed source parsing succeeded. Browser exposed authenticated DOM but this chat's Browser read tool did **not** expose full production JavaScript bundle/network request capture. Do not claim full frontend reverse engineering or exhaustive enumeration.

**Decision:** WATCH / NO_GO. Hard chain evidence upgrades token deployment and named Launch identity, not actual raise readiness, verified MetaDAO cash deposit, investor fill, performance vesting execution, or realized ROI. No monitor, mail, wallet signing, bid, or task created.

---


- 更新：2026-11-05，Asia/Bangkok；研究时点约 11:11–12:00。
- 阶段：**PRE-SALE / RESEARCH ONLY / NO FUNDS COMMITTED**。
- 项目分类：Solana MetaDAO Apps Program，消费级 AI 教育产品与 $SAT 新币公售。
- 研究决策：**WATCH**；发行配置、实际募资合约、$SAT Mint、流动性和交易退出深度尚未核验，**NOT SETUP / NO_GO execution**。
- 依据：`crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`、`PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md`、`token_trading_principles.md`、`MISSION_SPEC.md`；`AGENTS.md` 和 `docs/DEVELOPMENT_RULES.md`。
- 权威区分：MetaDAO 官网直接读回为 **LAUNCHPAD-FIRST-PARTY**；产品和收入来自公司网页时为 **ISSUER CLAIM**；平台通用合约源码和 Solana 可执行账户为 **PLATFORM CODE/CHAIN VERIFIED**；尚未与此具体 $SAT 发行配置关联。

## 1. 项目身份及确定的募资规则

- 官方发行页：https://metadao.fi/companies/1609sat
- 官方产品页：https://www.1609sat.com/app
- 项目 X：https://x.com/1609SAT
- 平台官方：https://metadao.fi 和 https://x.com/MetaDAOProject
- CEO：Alikhan Altaev（个人 X https://x.com/altalikh）；CTO：Ramazan Shalgynbay。均为项目方在 MetaDAO 页面自报身份；Alikhan 另见 1609plus LinkedIn 的 Altayev 拼写，团队同一身份/经历未做身份证明级独立审计。
- 计划开放：**2026-11-06 02:00 GMT+7 / 2026-11-05 19:00 UTC**。日期从 MetaDAO 直接读取的页面和 Google Calendar 真实 UTC 时间核对；**开放日不是已确认的 TGE、Claim 或 DEX 交易开始日**。
- 名义募资目标 **100,000 USDC**；MetaDAO **预承诺** $50,000，公开部分 **目标** $50,000。预承诺尚无本轮独立链上出资收据，**不要认定已结算 $50k**。
- 页面写明 `$100K for 10%`、`$0.01` / token、`$1M` at price。由数学得知隐含总供应 **100,000,000 SAT**，**尚非链上查证的 Mint supply**。
- 公开认购分配总额 5% 即按 $0.01 为 5,000,000 SAT；MetaDAO 对应 5,000,000 SAT；LP 2,900,000 SAT；团队绩效包 87,100,000 SAT。
- 截至访问时，官网只显示倒计时、目标和预承诺，不显示有效 Sale/PDA/Mint、认购交易和实际到账/接受额度。**SAT 官方 Mint = UNVERIFIED；募集启动和 TGE = NOT LIVE**。
- 具体截止时间、minimum threshold、单地址 cap、Aligned Parties 预留规模、超募时最终 accepted/gross、实际 USDC escrow、claim 和退回时点：**UNVERIFIED**；不得简单把一般文档的四天窗口视为本项目已发布的准确结束时点。
- 平台通用分配文档：https://metadao.com/docs/sale 和 https://metadao.com/docs/whats-new 。当前规则以 commit 资金时间权重、早期池稀缺 boost、Ownership Score、可能的 Aligned Parties 保留份额为变量；这意味着公共 $50K 目标 **不等于任意公开钱包均能拿满认购**。
- **条款冲突**：项目页面 Terms & Conditions 同时写 `All contributions ... final and non-refundable`，及 `If the minimum funding threshold is not reached, all contributed funds will be returned`；同一文本又同时写 capped USDC raise 与 `no in-protocol cap on amount that may be claimed beyond the stated minimum`。参与前需要以发售实时链上配置和可执行函数确认退款、accepted cap 与 founder claim 权限。不可按一句营销语自动消除冲突。

## 2. 产品真实性及实测边界

- 官网 1609SAT/app 有公开可读的 Dashboard、题库、词汇、错题回顾、模拟测试、AI Study Plan、排行榜和 Pro 定价；Pro 页面显示 **$20/month**，支持月付取消。**已确认网页展示和产品入口存在，尚未实测真实学生登录、付费回调、题目评分和后端留存**。
- 1609plus 的英文/俄文/哈萨克文活动历史和 SAT bootcamp 招生页面曾在 2026 年 9 月运营，提供额外的品牌在募资前已有实际教育活动的旁证，**不能据此独立验证产品收入**：https://t.me/s/plus1609 ； https://www.reddit.com/r/Sat/comments/1wxd7cq/best_paid_subscription/（小样本社区反馈，非财务/质量审计）。
- 应按产品可访问与非独立营收证明分层：公开 Web 产品页面 **CONFIRMED**；生产级用户操作 **PARTIAL**；真实付费订单、收款和留存 **ISSUER ONLY**。不因漂亮网页升级为已经独立核验 Level 5。

### 业务指标，均来自 MetaDAO 项目方提交的 2026-11-03 数据

| 指标 | 范围/数值 | 证据及限制 |
|---|---|---|
| 月营收 | 约 $5,000（截至 Nov 3） | **ISSUER CLAIM**，无支付流水、财务对账、银行/Stripe/链上收据 |
| 月利润 | 约 $3,500 | **ISSUER CLAIM**，成本口径、税费及创始人薪酬未知 |
| 用户数 | 15,000 | **ISSUER CLAIM**，累计或当前独立账户口径未披露 |
| 近 30 天练习学生 | 3,500+ | **ISSUER CLAIM**，未审计去重、留存 cohort |
| 近 30 天完整练习卷 | 2,200+ | **ISSUER CLAIM**，不是 2,200 个付费客户 |
| 首三个月付费学生 | 400+ | **ISSUER CLAIM**，累计付费者不等于月活跃付费订户 |
| 产品覆盖地区 | 40+ 国家 | **ISSUER CLAIM** |
| iOS 原生应用 | 已开发、即将发布 | **ISSUER CLAIM**，未找到已发布的具体 App Store 产品页 |
| 增长来源 | SAT 内容创作者、Instagram | **ISSUER CLAIM**，CAC、付费获客、转化归因未披露 |

交叉一致性：如果所有 $5K 都来自标价 $20/月的 Pro，无折扣、无年度/bootcamp/其他收费，则约 **250 个当月付费订户等值**。这只是算术敏感性，不证明真实活跃订户数，也不与 400+ 累计付费用户相矛盾。$3.5K/$5K 表面利润率为 70%，未审计。

## 3. 团队及资本结构

- 创始团队为 Alikhan Altaev / Ramazan Shalgynbay；Alikhan 的 LinkedIn 搜索结果 https://kz.linkedin.com/in/alikhan-altayev-in 与 1609plus 相关；Ramazan 的个人档案 https://kz.linkedin.com/in/ramazan-shalgynbay-b796232a8 同样展示 1609plus 关联。社交资料为自我声明，不能证明具体开发能力、股权结构或历史成功退出。CEO 的拼写 `Altaev`/`Altayev` 保留差异。
- 未取得独立历史融资、已完成机构轮次或原私募 Token Warrant。MetaDAO 是当前 **预承诺出资/发行平台**，不等于外部基金已完成打款。
- 官网拟用资金：内容与营销约 $6,000/月；团队约 $8,500/月（含募资后增聘开发者）；题库/AI/服务器及其他约 $1,500/月；**拟预算合计 $16,000/月**。这不是已花掉的资金。
- **现金跑道情景**：若营收保持项目自报 $5K/月且拟预算全额发生，经营净流出约 **$11K/月**。若符合 MetaDAO 通用分流规定，募资 $100K 有 20% 即约 $20K 用于 LP，则剩余可用约 $80K，静态跑道约 **7.3 个月**（忽略交易费、税费、营收/预算变化）。这不是链上 treasury 余额或公司实际 burn，只是风险敏感性，未经实际募集和支出核验。
- 官网声称 SAT 市场 TAM 100M 美元，并链接 College Board 的 SAT 报考人数新闻；SAT 报考人数最多证明市场存在，**不能直接证明本企业可获得的付费市场或 TAM**。

## 4. 代币经济和团队抛压

总供应隐含 100M，按官网规划：
- MetaDAO **5%**，认购成本 $0.01/枚、$50K 预承诺；实际到款/锁仓未核验。
- Public **5%**，成本 $0.01/枚，对应公开目标 $50K；实际 accepted 不明确。
- Liquidity **2.9%**，2.9M 枚；实际建池 quote 侧及池曲线未公布。
- Team **87.1%**，87.1M 枚，分 5 份，各 **17.42M**。
- 假定 MetaDAO/public/LP 全部流通且团队未解锁，初始名义 float **12.9M（12.9%）**、按 $0.01 约 $129K 名义流通市值。**未经 Mint/holder/LP 链上验证，不等于实际可交易 float**。
- 90 日价格 TWAP 达到 $0.02、$0.04、$0.08、$0.16、$0.32，分别累计解锁团队 20%、40%、60%、80%、100%。同一观察期可跨多个门槛；已解锁之后不因跌价重新锁定。**网页没有传统 18 个月 cliff，最早仍需要完整价格观察期，不是当日翻倍就能全部卖**。
- 前 18 个月 **团队合计每 30 天最多卖出 $25K 已解锁币**；未用额度不累计。18 个月之后美元出售上限结束，仍未达标奖励留锁。$25K/月相对 $100K 认购目标并不小，且相对可能较薄的早期 LP 可能产生显著卖压。
- 若首次达 2x TWAP，则 17.42M 团队币“可解锁”规模超过原名义 12.9M 初始 float，但**受 $25K 每 30 天的退出限制，不能将 17.42M 自动全算可出售流通**。

### 平台源码、Git 和 Solana 只读直接核验

- MetaDAO 官方代码 https://github.com/metaDAOproject/programs 的 `develop` 固定源码 commit：**e2ba4e9be712248ae4874f3b0621eaac69376c98**（2026-11-04 18:20:52 UTC）。
- 源码 `programs/price_based_performance_package/src/instructions/withdraw_via_sell.rs` 在卖出前检查解锁余额、window token cap；卖出后按实际成交 USDC 和卖前估值取较大值检查 quote cap，超限时整个交易回滚。
- `withdraw_tokens.rs` 亦检查窗口 token/quote 限制，避免通过简单提币忽略同一额度。\
  `state/performance_package.rs` 定义可更换的 withdrawal policy；`propose_change.rs` / `execute_change.rs` 要求团队 recipient 与 package authority 两方参与变更流程。因此通用源码中的限额 **不是单方随意修改，但也不是绝对不可修改**。项目对应 authority 的实际身份尚未核实。
- 通过 Alchemy 对 **Solana mainnet finalized slot 465567499** 读取 `pbPPQH7jyKoSLu8QYs3rSY3YkDRXEBojKbTgnUg7NDS`：返回 `executable:true`、owner 为 BPF Upgradeable Loader；对 Launchpad v8 `moonDJUoHteKkGATejA5bdJVwJ6V6Dg74gyqyJTx73n` 在 slot 465567497 亦返回 `executable:true`。**这是平台程序部署事实，不证明 1609SAT 使用的版本、实际绩效配置、token Mint 或关联仓位已经建立。**
- 尚无官方可归属 **1609SAT 自己的 GitHub**。GitHub 项目名及代码检索仅返回无关结果；MetaDAO 平台 Git 不能充当 1609SAT 产品代码开发证据。无法查代码更新频率、测试覆盖、后端账单真实性或发布管道。
- 暂未取得本项目 Mint、sale escrow PDA、vesting account、LP 池地址、审计结果、首次交易签名。任何貌似 `SAT` 的第三方 SPL Mint 都不能当作本项目正式资产。

## 5. 本项目独立 FDV / 出场模型

按 $0.01 ICO 价、总供应静态假设 100M、初始浮动静态假设 12.9M，**均是预测情景，不是市场报价、期望值或成交保证**：

| 情景 | 价格 | FDV | 静态初始 float 名义市值 | 相对 ICO 价格 | 每 $100 满额获配理论标值 |
|---|---:|---:|---:|---:|---:|
| Downside | $0.005 | $0.5M | $64.5K | 0.5x | $50 |
| Conservative/break-even | $0.010 | $1M | $129K | 1x | $100 |
| Base/upside sensitivity | $0.020 | $2M | $258K | 2x | $200 |
| Strong launch | $0.030 | $3M | $387K | 3x | $300 |
| Speculative | $0.050 | $5M | $645K | 5x | $500 |
| Extreme speculation | $0.100 | $10M | $1.29M | 10x | $1,000 |

- $1M FDV / 公司自报简单年化营收 $60K = **16.7x**；$3M = **50x**；$5M = **83.3x**；$10M = **166.7x**。企业收入真实性尚未独立核实，且 SAT 代币不应自动当作企业权益或有收入分红，因此这些倍数只能衡量商业故事要求有多高，不能当作 token 的权益收益率。
- 假设项目仍按通用 MetaDAO ICO 文档将募集额 20% 用于初始 LP，则目标 $100K 可导出 $20K USDC 侧资金规划，但**1609SAT 真正实缴流动性、币池个数、价格曲线、Meteora/内部 AMM 分配均 UNVERIFIED**；不能给出实际 $100/$500/$1,000 卖出滑点。
- 参与者真实 ROI = **最终实际 accepted USDC、获配 SAT、Claim 时点、卖出的真实 quote、滑点、网络费和手续费**共同决定。名义 2x 不代表可大额兑现 2x。
- 团队绩效的潜在 $25K/月卖压相对规划初期 LP 规模较高；此处讨论的是最大可能卖出额度，不是已经发生卖单。

## 6. PM 强制检查

2026-11-05 Asia/Bangkok 实际英文网页搜索：
- Polymarket：`1609SAT` / `1609 SAT` / `MetaDAO SAT raise`，未查到身份匹配的 live 合约。
- Kalshi：同样检索，未查到身份匹配的 live 合约。
- Limitless：同样检索，未查到身份匹配的 live 合约。
- Predict.fun：同样检索，未查到身份匹配的 live 合约。
- MetaDAO Decisions：https://metadao.fi/decisions 中未读到独立 **1609SAT** 治理/价格预测问题。其他项目/同名 `PREDICT` 市场不属于本项目。
- 结果：**未检索到可验证的项目专属 PM 市场**。没有可报告的概率、成交量或盘面。未检索到不等于概率 0，也不能借其他 MetaDAO 项目的 ROI 代替。

## 7. 关注度及初期市场需求

- 官方 MetaDAO 于 2026-11-04 推介 Apps Program，1609SAT 为其首发试点；Solana 官方传播也转发这一模型。**可确认分发曝光，不可确认额外外部买盘规模**。
- 1609plus 在 9 月有 bootcamp 招募、社媒创作者任务，说明早期营销存在，但不能与 crypto 买方关注度直接等同。
- Reddit SAT 讨论出现零星正面使用反馈和对 AI 题库的负面意见，样本不足以判断付费产品净推荐值或加密代币情绪。

## 8. 决策与实操门槛（没有任何交易授权）

当前 **WATCH，计划出资 $0，研究期 NO_GO**。转入条件性 SETUP 必须至少满足：
1. 官网显示真正 live launch ID、原始可执行募资合约/USDC 账户，确认开盘、截止、minimum、accepted cap 和实际退款机制，消除公告与协议矛盾；
2. 发布并通过独立 RPC 对照 $SAT 官方 Mint 的 total supply、mint authority、发行及绩效 package vault，确认 87.1M 的实际可卖限制和可更改授权者；
3. 确认 MetaDAO $50K anchor 已实际承诺或 onchain 存入、公共 $50K 实际可分配及 Aligned Parties 保留，确认此钱包的真实 Ownership Score 及预期有效填充量；
4. 上线建池时核验真正的 Quote liquidity、LP ownership、初始成交价格和 $100/$500 的真实可成交卖出深度；
5. 独立付费收入/实际付款证据和真实留存优先，未能取得时严格将 $5K MRR、$3.5K profit 视为营销声明。

**主要风险**：87.1% 团队绩效分配、18 月后可能放大的解锁兑现；低初始 float 和极薄 LP；未核实商业指标；$16K/月计划开支对 $5K/月声称收入的扩张压力；新 Apps Program 机制缺少本项目 live configuration；公售条款退款和 cap 文案冲突。

**最有希望的事实**：项目产品网页可访问、有事先在运营的教育营销/课程；有具体定价和可核算的付费用户声称；$1M FDV 对真实月收入达标时可能具有早期估值优势；MetaDAO 平台通用链上程序已有真实部署和双边修改/限额执行机制。所有优势仍需要从公司口径升级到可独立验证的证据。

## 9. 本轮核查的准确范围

- `DIRECT_BROWSER`：登录浏览器中原有 https://metadao.fi/companies/1609sat 页面文本，读取公告、官网计划、团队、数据和 Terms（未提交表单、未签名、未播放/互动交易）。
- `DIRECT_GITHUB`：Mission 四份权威研究规则、AGENTS、开发和目录规范；MetaDAO 官方 programs Git fixed SHA + 绩效包提币/卖出限制源代码。
- `DIRECT_CHAIN`：Alchemy Solana finalized `getAccountInfo`，只证明平台两个程序地址可执行；未查询到 $SAT 官方 Mint，因此 **无本项目可证实 token supply/锁仓/LP/入金收据**。
- `PUBLIC_WEB`：1609SAT 产品页、MetaDAO 文档、团队 LinkedIn 索引、项目社交和学生社区的小样本、项目特定 PM 的四平台查询。
- **没有**投资、申购、签名、邮件、自动化、生产监控或资产操作。没有运行任何 1609SAT 应用代码或做独立端到端登录付款测试。

## 10. 一手和辅助证据索引

1. MetaDAO 项目官方：https://metadao.fi/companies/1609sat
2. 1609SAT 官方产品：https://www.1609sat.com/app
3. MetaDAO 通用认购规则：https://metadao.com/docs/sale
4. MetaDAO 2026-10 分配变更：https://metadao.com/docs/whats-new
5. MetaDAO Apps Program：https://metadao.com/apps
6. MetaDAO 合约源码（固定 SHA）：https://github.com/metaDAOproject/programs/tree/e2ba4e9be712248ae4874f3b0621eaac69376c98
7. 绩效包卖出限制实现：https://github.com/metaDAOproject/programs/blob/e2ba4e9be712248ae4874f3b0621eaac69376c98/programs/price_based_performance_package/src/instructions/withdraw_via_sell.rs
8. 绩效包提币限制实现：https://github.com/metaDAOproject/programs/blob/e2ba4e9be712248ae4874f3b0621eaac69376c98/programs/price_based_performance_package/src/instructions/withdraw_tokens.rs
9. 政策变更双边执行：https://github.com/metaDAOproject/programs/blob/e2ba4e9be712248ae4874f3b0621eaac69376c98/programs/price_based_performance_package/src/instructions/execute_change.rs
10. 公司收入新闻转述（**不是独立财务证明**）：https://solanacompass.com/news/metadao-launches-apps-program-for-consumer-app-raises-starting-with-1609sats-100000-round
11. 学生/旧营销渠道：https://t.me/s/plus1609

不可将这些来源机械累加为独立采样：平台页、媒体稿、项目官方 X 对同一募资数字属于同一信息链。
