# Meme CA 链上尽调统一查询：准确性改造与验收标准

Status: PRODUCT REQUIREMENTS / IMPLEMENTATION NOT DONE / PRODUCTION UNCHANGED
Date: 2026-10-11 Asia/Bangkok
Owner: Mission 300-3000 overarching product governance. Engineering handoff: Frank/Meme module.
Authority: `WALLET_CLUSTER_ANALYSIS_SPEC.md`, `../MISSION_SPEC.md`, `../local-agent/config/follow_policy_v1.approved.json` (Frank *follow-decision only*).
Observed regression: user-provided four screenshots of localhost `CA 链上查询`, token `Agency`, showing multiple `未确认`, three scan presets, missing external narrative and an expired `$30` quote.

## 1. Product decision and scope

The user requires **one complete, evidence-backed query** with the same practical data categories and clarity they can expect when looking at GMGN/FOMO/OKX Wallet, while using **no paid GMGN API**. A successful result must help decide whether this exact contract is risky, how holders/funders/LPs are connected, what first buy and dev activity occurred, whether market liquidity is credible, and what verifiable external narrative is spreading.

- Remove the user-facing `快速 / 标准 / 深度` choice in the **CA research UI only**. Preserve automatic internal lightweight preview and progressively deeper indexed/on-chain collection, but a preview **cannot be titled completed analysis**. The user does not select completeness vs speed; final output must be completeness-governed.
- Preserve the separate live Frank wallet-follow signal/decision system. **Do not alter Frank frozen BUY/WAIT policy, historical signals, follow quote size, source writer, trading state or delivery.**
- The manual CA query is **pure read-only due diligence**, available for any valid Solana CA independent of Frank and not an investment order.
- Success = truthful coverage, correct definitions, independent source reconciliation, useful structured conclusion, and real-device verification. A high test count, a fast placeholder, a healthy service banner, 500 raw signatures or a green “分析已更新” with many gaps **does not satisfy success**.
- Do not silently replace unknown results by unsupported values, insist that every wallet has one controller, or claim impossible universal certainty. If required evidence cannot be obtained, mark `INCOMPLETE_EVIDENCE` with exact missing rows, cause, alternative attempted and next source; **not** `ANALYSIS_COMPLETE`.

## 2. Verified defects in currently committed main

The following are **code/document findings**, not claims from fresh running Mac logs:

1. Current `server.py` includes user-facing `CLUSTER_PRESETS`. The highest `deep` preset visits up to 20 holder owners with at most **100 target-token address signatures + 50 funding signatures each**. No current-data invariant establishes that these arbitrary caps reach wallet birth, first acquisition or actual first funding. `WALLET_CLUSTER_LOCAL_TOOL.md` still describes three bounded modes.
2. `cluster.py` calls official Solana `getTokenLargestAccounts`, which returns the top **20 token accounts** rather than the top 20 beneficial owners or an exhaustive holder list. The code then filters special addresses **inside that same 20-row list** to compute provisional exclusion Top10. If enough LP/vault addresses occupy top ranks, the resulting ten free-holder accounts must be drawn from positions beyond that raw Top20. Hence `KNOWN_EX_LP_TOP10_PCT` is **not generally the actual exclude-LP Top10**; a numerically tidy “已识别池后Top10” may be incomplete.
3. Strict `EX_LP_TOP10_PCT`, `EX_SPECIAL_TOP10_PCT`, `CLUSTER_ADJUSTED_TOP10_PCT` are unresolved absent registry `normalization_complete`. The provisional values displayed alongside the strict unknowns can mislead users into thinking all special-address normalization was done.
4. `LARGEST_PROBABLE_CONTROL_CLUSTER_PCT = 0` currently means **no qualifying control group established by this finite investigation**, not proof of zero hidden coordinated ownership. A sampled possible relation share (e.g. 23.77%) is not equivalent to proved common controller; both belong in appropriately qualified, distinct facts.
5. The dashboard `app.js` explicitly says `未接入 X/FOMO 外部叙事检索`. It only outputs DexScreener supplied website/social hints. This does not meet requested narrative research.
6. Generic CA query in `server.py` and `app.js` displays `execution_quote_30_usdc` and `$30 实际可成交价`. This is inherited from `follow_policy_v1.approved.json` with `quote_usdc_amount: 30` and does not belong in generic token due diligence. Its archived 30-second quote expires by design and becomes an overprominent useless headline.
7. UI status `分析已更新` appears even with `UNRESOLVED` roles, `errors`, incomplete normalization or funding coverage. This conflates an HTTP/job success with a verified analysis completion.

Evidence: `local-agent/mission_agent/meme/cluster.py`, `local-agent/mission_agent/mission_control/server.py`, `local-agent/mission_agent/mission_control/static/app.js`, `local-agent/config/follow_policy_v1.approved.json`, and uploaded user screenshots. The screenshot's displayed percentages should be treated as **historical screen observations**, not independently re-verified current-chain percentages.

Official data capability references:
- Solana `getTokenLargestAccounts` = **20 largest token accounts**: https://solana.com/docs/rpc/http/gettokenlargestaccounts
- DexScreener public token-pairs, token profiles and community takeover endpoints: https://docs.dexscreener.com/api/reference
- Solscan holder pagination is documented but requires Pro API authorization and must **not** be treated as free by default: https://pro-api.solscan.io/pro-api-docs/v2.0/referenc/v2-token-holders

## 3. Single-mode user-visible result contract

One CA input, one `查询` action, background progress/provenance, one completed evidence report. Present **verified fact / supported inference / third-party claim / prediction** separately.

The headline must answer, with evidence:
- Contract identity: exact CA, mint owner program, mint/freeze/update authorities, Token-2022 sensitive extension risks and on-chain burn/lock/transfer controls. Never infer creator authority absence from null mint authority alone.
- Market: actual selected pool/pair, source timestamp, price, market cap vs FDV and denominator, liquidity, 24h volume, current buy/sell activity; independently compare a second source where available. Historical ATH must be accurately dated and its source and calculation defined. Do not confuse DexScreener reported market cap, FDV, main-pair liquidity and direct DEX pool reserves.
- Holder ownership: supply at a controlled slot, current largest *token accounts*, resolved **wallet owners**, all known pool/vault/CEX/router categories, accurately computed “excluding special addresses Top10”, percent remaining, and distinct eligible holder counts.
- Wallet concentration and relationships: real direct transfers, funding and multi-hop provenance where material; dev/treasury/insider links, common control **only with adequate non-public independent evidence**; public router/fee payer/CEX false cluster exclusions. Show dominant wallets with confirmed acquisition type, amount, price/quote, transaction URL, timestamp and wallet role.
- Trading provenance: first verifiable token **acquisition** vs first **market buy** must be distinct; the earliest buy found *inside a 100-signature window* may not be the true first buy. Reconstruct complete material purchase/sale movements when data allows and identify hops, transfers, unsupported routed swaps, and unpriced flows without pretending to know realized PnL.
- Token narrative: what the meme or project is about, earliest identified origin, actual official/team account, current X/community/launchpad discussion, narrative catalysts, concentrated KOL/community coverage when supported, timing and links. Explicitly separate **external narrative exists** from **its owner adopted this exact CA**. If verified official recognition is absent, say so in that one field without blanking the whole narrative section.
- Final assessment: specific chain contract risk, LP/liquidity, holder manipulation/insider risk, market tradeability, narrative authenticity/traction; evidence status and concrete warning conditions. Never give an unconditional “安全/可买” based on a superficial score.

User-facing cards should show useful results, not nine repetitive `未确认` badges. One compact `尚缺哪些证据` section lists missing data with blocker and attempted sources, while uncertainty intrinsic to ownership remains honestly explicit.

## 4. Data acquisition and computation plan

1. **Canonical snapshot + source provenance**: timestamp + slot/block identity for on-chain balances/supply/owners, timestamp and provider for markets, report run ID, exact CA; non-synchronous reads need captured slot divergence/staleness and reconciliation. Use decimal raw units and avoid floating point rounding in holder percentages.
2. **Full holder-rank sufficiency**: get complete *top eligible owners* required for each requested metric. The raw first 20 token accounts **alone cannot prove** top10 ex-LP/ex-special or ownership grouping when special addresses push eligible owners past rank20. Prefer reproducible mint-account enumeration/indexer pagination and on-chain spot checks. If no permitted pagination/indexing exists, do not display a purported exact filtered Top10; identify the bound and classify it as a partial lower-rank sample.
3. **Special-address evidence registry**: dynamically identify DEX pool / vault / token program / escrow / lock / burn / liquidity, owner/authority and known router/exchange public infrastructure, with address/contract/transaction evidence. Version and date every label; unknown addresses cannot be auto-reclassified by name. Do not require a human-created special-address tag before attempting on-chain role attribution.
4. **Progressive holder funding/history**: follow target-token account, owner, separate SOL/USDC funding, routed swap, related addresses and documented transfers. Page beyond initial 100/50 when evidence still material. Stop only at chain-verified relevant origin/first event, complete pagination, a demonstrable irrelevant branch or a reported provider coverage/budget limitation. Put observed oldest/newest times, pages, signatures and explicit completeness state per owner into report.
5. **Cross-holder relationships**: distinguish exact transfer/transaction link, probable owner from multiple independent non-public indicators, common *execution* bot and coincidental public infrastructure. No blind merger from common CEX or popular router. A `0%` confirmed-control result must read “在已覆盖样本中未建立共同控制证据” and show unresolved owner share separately.
6. **Official/public data first**: Solana finalized RPC, protocol/DEX program accounts, launchpad token-page data and verified program instruction semantics; DexScreener for market/pair hints; independently compare GeckoTerminal/other accessible public indexed data plus raw pool accounts where feasible. GMGN/FOMO/OKX public visible data are **comparison references**, not paid API requirements, not authoritative proof of controller identity. Never require GMGN paid access, deposits or private GMGN keys.
7. **Narrative enrichment**: exact CA lookup in official launchpad/pump.fun pages, token profile URL and public project sites, X posts/official accounts where publicly accessible, then credible third-party community reporting. Persist link, author identity, publication UTC, text synopsis, first-seen vs updated date, whether it names the exact CA, whether official affiliation is verified, and evidence classification. Promotional placement/boost must be distinguished from organic discussion. Sources blocked by access controls should be marked and a non-Chinese alternate source attempted; never fabricate unseen X posts.
8. **Audit & resilient caching**: raw evidence/response hash, normalized derivation, per-source retry/page cursor and freshness policy; requery older cached data only where meaningful, and do not rebrand old quotes as live. Public RPC limitations warrant alternate legitimate endpoints and batching, not indefinite waits or a superficial report silently returned as DONE.

No unapproved wallet action, monitor, scheduler, Gmail delivery, trade or paid data purchase.

## 5. $30 quote removal and module isolation

- **Remove `$30 实际可成交价`, `$30 可成交报价` and `execution_quote_30_usdc` from the generic manual CA analysis output and job execution path.** No expired snapshot in a headline. If price exists, show dated market reference and main-pool metrics. Contract transfer restrictions, tradability and pool depth may be displayed as independent risk evidence without a user-invented order amount.
- Leave `follow_policy_v1.approved.json` and the **Frank signals/follow-decision $30 Jupiter quote** untouched. That historical user-approved separate follow strategy is outside this CA product correction. No silent change to Frank frozen policy.
- If a future user explicitly asks a concrete trade size, a separate on-demand trade quote can use that size; it is not a default CA requirement.

## 6. Milestones and pass/fail gates (in this order)

### Gate A: source/data semantics

- Token account vs owner, raw vs eligible holder Top10, pool/vault classification, precision, same-slot supply, and `0 no detected evidence` vs `proved none` test cases.
- Chain-verified synthetic and real historical cases with leading pool/vault holders forcing lookback past rank 20. Wrong Top10/ex-special metric must fail, not downgrade truth silently.
- Arbitrary owner with first acquisition/funding **older than 100/50 signatures**, including a swap-route intermediary, must be traced with honest pagination or flagged specifically `incomplete`.
- Reproduce both `GOMO` historical known wallet-split/public-infra examples and the **Agency** screenshot scenario with the exact mint from the original submitted CA input. Screenshots alone are visual evidence, not a verified ground-truth balance.

### Gate B: independent data parity and narrative

- Compare the **same CA, same time window, same definitions** against accessible GMGN/FOMO/OKX Wallet views, DexScreener and at least one independent pool/holder data method; save case IDs, timestamps, raw evidence and explain materially different numbers. Market cap/FDV/LP vs liquidity/Top10 definitions may differ legitimately; explain definitions instead of blindly forcing exact agreement.
- Three required distinct market situations: recent pump.fun graduation, mature active token and LP-heavy/vault-heavy token, plus at least one Token-2022 extension-risk case and one suspected multi-wallet-funded token.
- For every test CA, public narrative section includes **specific externally attributable posts/site evidence**, or a documented exhaustive accessible-source attempt. Narrative must never be dropped solely because official owner recognition is unproven.
- No public-site scraping bypass or paid GMGN API. If a source is not legally/technically accessible, use another allowed source and record coverage difference.

### Gate C: single-mode working UX

- Only **one query mode**; no quick/standard/deep control. Historical filters/caps are no longer exposed as accuracy choices.
- Progress UI may update immediately but must label output `FETCHING/PARTIAL`; `COMPLETE` requires all mandatory facts covered or a documented explicit `INCOMPLETE_EVIDENCE` outcome. HTTP 200/job DONE is not a product PASS.
- No overprominent red/green “safe” judgment unsupported by evidence; compact primary conclusion with drilldown evidence; no `$30` quote in CA.
- User can copy exact CA, inspect chain transaction signatures and source links, read timestamp and missing coverage without hunting through raw 500-transfer lists.

### Gate D: independent review and real Mac acceptance

- Submit real code diff + actual result JSON/HTML of sample CAs for **independent AI review** (e.g. Claude/Codex), including adversarial scenarios and source parity. Review must explicitly cover algorithms and data truth, not screenshots only. All substantial reviewer findings repaired and retested.
- Run unit/integration tests, representative full real CA queries, source-outage/fallback test and repeat-query cache invalidation; report elapsed time and unresolved data by **importance**, not just counts.
- Demonstrate on the user's actual Mac Dashboard that the new **one-mode** output materially resolves formerly unknown LP Top10, wallet first acquisition/funding, quoted-market definitions and external narrative where data exists. Validate no Frank writer/signals/delivery regression.
- **No merge/deploy/production change solely because CI passes.** Get explicit rollout authorization for any new Mac installation/restart; preserve snapshot/rollback path. `PRODUCTION_TRADING=NO_GO`.

## 7. Status and engineering handoff

**Current state: `REQUIREMENTS_RECORDED / CODE_NOT_CHANGED / TESTS_NOT_RUN_FOR_THIS_SPEC / NOT_DEPLOYED`.**

The module implementation conversation should first reconcile this requirement against actual head and propose an evidence-oriented design; then implement, independent review, test and request rollout approval. The 300-3000 general-governance conversation will review evidence, completion gates, provenance and priority, not pretend the engineering milestone has been executed. No new automation, Gmail, runtime task or Git PR was created by this requirements record.
