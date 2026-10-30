# BSC Meme 地址模型 V1：C0 审核口径修复与 2026 五钱包 P4-B U 门禁

Date: 2026-10-15 Asia/Bangkok. Same [Draft PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40). Research-only; no new chain RPC in this batch, no funds, no live alerts, no Mac runtime.

## What code actually does

- `bsc_meme_address_model_v1_c0_review_gate.py` reads six *byte-pinned* original Git sources and deterministically distinguishes the five-round baseline (5 rounds / 4 wallet×CA cells / 433 unreviewed) from the expanded seven-round *review-pending candidate* (7 / 5 / 432). The latter already contains **8E6B / token 「4」 P2 #16/#17**, one mixed CA cell. Prevent duplicate promotion; keep loss and win.
- The selected 19 original **2025** token4 transaction native BNB deltas sum to **+13.164987453603066615 BNB**. The code separately computes the first-to-last sampled wallet BNB balance change, selected-vs-whole-wallet residual and two interstitial gaps from five prior saved historical RPC readbacks. It marks intervening transaction attribution **UNRESOLVED**. No claim of entire wallet lifetime PnL, causal token4 fees, 2026 fresh activity or follower alpha. The UTC 2025 boundary is re-derived from block-header epoch timestamps.
- `bsc_meme_address_model_v1_p4b_2026_crossowner_u.py` reads four *byte-pinned* existing 23×19/P3/P4-B/P4-C source matrices. It freezes **5 distinct 2026 wallets and 3 major CAs**, explicitly **reused from existing evidence (not randomly sampled, not untouched holdout)**. It keeps historic source owner PnL vs P2 balance evidence vs historical V2 router quote separate. A V2 math quote is explicitly not an actual fill or first public executable U.

## Bounded P4-B case matrix

| EOA | Major exact CA label | Preserved source role | Present claim |
| --- | --- | --- | --- |
| DDAC | 龙虾 | Original earlier pre-DEX signed owner purchase plus real negative source round | Still no external observer executable entry/exit |
| 239E | 龙虾 | Same CA original owner negative **and** positive signed cashflow rounds | 1 positive + 1 negative, not two winning CAs |
| 877AF | MARSCOIN | Closed original token inventories, truncated receipts/non-native quote and Gas not settled | Still economic UNKNOWN |
| 2ADF | 牛来 | Source P3 recent original-owner true swap, older P2 selected episodes | Not validated as a true eligible first-market follow |
| A83B | 牛来 | Source P3 recent original-owner true swap, negative P2 control | Not validated as a follower alpha |

All five are original candidates from the frozen 23 EOAs; three exact CAs remain within the frozen 19. In the existing source cohort the prior **DDAC/龙虾** original earlier signed-buy example is confirmed. The other wallet-specific early-action cells remain evidence-qualified per exact source; a signed buy by a *different wallet* must not become a wallet-specific purchase.

**Qualified observer U: 0 / 5 at this source evidence grade.** This means no case has the minimum *proven* public observer trigger, then-accessible executable buy **and** sell, historic funds, taxes, gas and capacity. It does **not** mean all five markets were untradeable, none of the wallet trades happened, or any tested follower lost money. P5 1/5/15 minute returns are still `UNRESOLVED`.

## Actual CI evidence and what it does not prove

GitHub [BSC main CI #38731104023](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38731104023) on code+workflow SHA `27975b1a55bb27983c8734d6dd73c8139da2198e`: `SUCCESS`. Independent fetched job log showed **369/369** model-discovery tests, **9/9** supplementary, and **375/375** complete `test_bsc*.py` tests. New C0 six adversarial tests and P4-B six adversarial tests were run by GitHub. Three other BSC runs on that exact SHA all `SUCCESS`. Named cached-JSON replay steps were changed from misleading live/RPC descriptions to **static replay**.

These CI results verify bounded offline code and frozen-source invariants only. They do **not** constitute fresh Alchemy/BSC readback, full receipt raw-blob independent validation, an external AI `APPROVE`, eligibility U proof, a valid P5 strategy or real-market profitability.

## Forward contract and stop condition

The correction pass ends with two distinct source grades, 19-vs-5 prior-source scope, unresolved owner balance attribution and explicit 2025 UTC. Do not spend further mainline cycles chasing token4's unbounded other-asset BNB movements. C0 is **code+CI complete, independent fixed-SHA review still pending**.

Next primary P4-B action: using this frozen 5-wallet/3-CA case table, obtain **bounded new free read-only chain/ABI evidence** of the earliest publicly observable actionable market, valid buy/sell route, actual historical quote/tax/fee/gas and observer-sized capacity, then corresponding available owner capital at public U. Record eligible/ineligible/unknown as a denominator including failures. If a free endpoint truncates, preserve source limitations and move to next preselected case. P4-C source economics is separate; only after meaningful U evidence freeze 1/5/15-minute observer replay on untouched 2026 data with negative/no-fill controls. Do not retune the original frozen thresholds.

Status: **P4-C PARTIAL, P4-B U UNRESOLVED, P5 BLOCKED, OTHER_AI_REVIEW_PENDING, NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE**.


## 2026-10-15 fixed-SHA independent review and P2 recent swap repair

Received external AI independent review of **fixed SHA `9b82f932d60ef8945375091ec5b0dd0bf2753b53`** against base `dd6e399903facba99fa26a5770a06f4e302586f7`: **`REQUEST_CHANGES`**, specifically **one P2** evidence-state output defect in `bsc_meme_address_model_v1_p4b_2026_crossowner_u.py` prior lines 71–72. The review found no separate blocking errors in the C0 five-versus-seven denominator, 2025 token4 attribution, signed market-witness ownership, or V2 math-only labeling. External reviewer directly re-read **19/19 original 2025 token4 transactions, 19/19 complete success receipts, and 38/38 historical N-1/N wallet balances** from BNB mainnet, not as part of GitHub CI. The reviewer confirmed source native scope sum `+13.164987453603066615 BNB` differs from first-to-last BNB wallet movement `+4.702488415584707741 BNB`; unattributed gap `-8.462499038018358874 BNB`. This does **not** close whole-wallet profit, internal trace or follower U. This paragraph records the user's supplied independent report, not an additional fresh RPC capture or archived raw response from this developer session.

P2 issue: original pinned P3 matrix `3252e05c3ef1a4de14a5e10aed3e5ba80566154f` records 239E and 877AF as `p3_verified_recent_19CA_swap=false`, last UTC/hash `null`, and `p4_research_qualification=RECENT_SIGNED_SWAP_UNRESOLVED`. Old five-case output labeled `recent_signed_swap=false` without qualification: readers could incorrectly classify lack of verified evidence as **confirmed no activity**. The original P3 30-day freeze is `2026-09-13T08:37:36Z`–`2026-10-13T08:37:36Z` inclusive, across **all original 19 exact CAs**, not necessarily the selected row's CA (e.g., recent A83B witness is TST although selected row displays 牛来).

Repair on the same Draft PR branch:
- Replace ambiguous `recent_signed_swap` with `recent_signed_swap_state = CONFIRMED_ACTIVE | UNRESOLVED` for the evidence actually present. **`CONFIRMED_INACTIVE` remains a third possible research category only with independent full-window negative evidence; this source has none, so it must never be derived from Boolean false.** Preserve evidence-scoped Boolean `verified_recent_19CA_swap_found`.
- Carry `recent_swap_frozen_window_UTC`, `recent_swap_scope = WALLET_LEVEL_FROZEN_19_EXACT_CAS_NOT_DISPLAYED_ROW_CA`, original P4 research qualification, last signed `recent_swap_tx_hash`, and original UTC; add an explicit `recent_swap_row_CA_attribution = NOT_CLAIMED_WALLET_UNIVERSE_ONLY` so the source wallet-wide recent hash is not silently assigned to selected row CA.
- Gate false only to source `RECENT_SIGNED_SWAP_UNRESOLVED` with null date/hash; require confirmed true to have actual signed tx hash, and parsed UTC inside frozen 30-day range. Reject fake inactive classification, invented unknown witness hash, altered frozen window and out-of-window confirmed witnesses. Six new tests use original frozen sources, covering both unknowns and all three confirmed wallets.
- Original 23 × 19 identity, source blob pins, five-wallet/three-CA investigation batch, economic cashflow source, public U `UNRESOLVED`, P5 `BLOCKED`, and `NO_GO` are unchanged.

CI nuance from independent review: four successful PR CI runs for previous SHA `9b82...` checked out generated **merge-context** commit `2c77e725c295c1bc4860023addf01c59b88212bb`, not a direct checkout of the standalone target commit. Reviewer separately executed **375/375** broad BSC tests and **6+6** new tests in a detached target-SHA worktree. Do not claim PR CI itself ran live RPC or ran directly from the SHA's checkout.

**Status:** Old `9b82...` verdict remains `REQUEST_CHANGES`, unaffected by later commits; P2 fix is only proposed for acceptance once new fixed SHA and corresponding CI tests are verified. Another independent reviewer must decide `APPROVE/REQUEST_CHANGES/BLOCKED_INSUFFICIENT_EVIDENCE` on the **new SHA**. No merge, deploy, Gmail, trade, monitoring or wallet interaction.
