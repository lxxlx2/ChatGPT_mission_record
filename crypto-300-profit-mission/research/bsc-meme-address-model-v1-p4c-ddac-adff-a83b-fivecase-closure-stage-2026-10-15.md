# BSC P4-C — DDAC / ADFF / A83B cross-owner original five-case historical inventory stage

**2026-10-15, Asia/Bangkok**. Same Mission research BSC Draft PR #40. **READ ONLY**. BSC UI proposal has been abandoned by the user for now; resume economic modeling, not Crypto信息流 UI, no website changes. **P4-C PARTIAL / P4-B global U unresolved / P5 BLOCKED / NO_GO / NO_MERGE / NO_DEPLOY.**

## Precommitted original P2 batch (not selected after new result)

`bsc-meme-address-model-v1-p4c-ddac-adff-a83b-fivecase-precommit-2026-10-15.json` pinned before new RPC calls. Reuses original exact 23×19 wallet/CA roster and frozen prior P2 source Git blob checks. This is an outcome-stratified 5-case sample and **NOT** an unbiased profitable-wallet success-rate or a model recommendation.

| P2 case | Original EOA | 2026 frozen major CA | Native owner **block scope** | Real owner exact ERC20 inventory | Complete original successful receipt / total |
| --- | --- | --- | ---: | --- | --- |
| #3 | DDAC | 我踏马来了 | **+0.030104517152956606 BNB** | in = out `196814410022627640097170` raw | 1/2 |
| #4 | DDAC | 我踏马来了 | **-0.446324586902254802 BNB** | in = out `180825179799407648337166` raw | 2/3 |
| #43 | ADFF | 龙虾 | **-0.000342158068328726 BNB** | in = out `58987593881963477971703` raw | 1/2 |
| #44 | ADFF | 龙虾 | **+0.005685807795852275 BNB** | in = out `32546033429758403566` raw | 0/2 |
| #48 | A83B | 龙虾 | **-0.174628064918928929 BNB** | in = out `751611704517547703910865` raw | 1/2 |

**Chain facts completed:** Fresh original exact-owner `eth_getTransactionByHash` 11/11 match BNB mainnet chain ID 56, wallet, hash and frozen block. `eth_getLogs` exact one-block CA-owner incoming/outgoing readbacks all 11 purchases/exits, originally signed token buys + sells and **5/5 zero token residual**. Historical `eth_getBalance` EOA N−1 and N independently complete **11/11** and sums exactly match frozen P2 original signed-block native balance changes. **5** full successful original transaction receipts, **6** full receipt responses truncated. The API returned fixed block WBNB event JSON bigger than the tool limit for **4 of 5** DDAC blocks, explicitly recorded as `TRUNCATED_OR_ERROR`; cannot treat it as zero WBNB or a failed sell.

**Important precise-log guard:** Original ADFF P2 #44 buy has **two distinct canonical ERC20 Transfer logIndex values** from the same original EOA signed buy hash, together equal `32546033429758403566` raw tokens. Both are counted. Duplicate receipt `(blockHash, transactionHash, logIndex)`, `removed=true`, wrong signer and unknown full receipt are rejected by source replay guards.

**Unresolved, not quietly rounded:** The prior P2 positive/negative results above refer to *selected EOA native account changes across the exact selected transaction blocks*, **not** individually proven original trade profit/loss, native quote after all router fees, or a potentially followable trade. Fresh receipts on multiple exits are truncated, so original quote asset and paid original Gas/route settlement are not fully independently reconciled. These **five samples contribute zero new independently confirmed native settled economic winning/losing rounds**, despite all inventories closing and source block signs. `NO_GO`. Avoid more repeated failed whole receipt/whole block WBNB RPC calls; continue other higher-grade complete-source candidates.

## Reproducible Git evidence and testing

- Original precommit: `bsc-meme-address-model-v1-p4c-ddac-adff-a83b-fivecase-precommit-2026-10-15.json`
- Source signer + full/truncated receipt readbacks: `bsc-meme-address-model-v1-p4c-ddac-adff-a83b-original-rpc-part1-2026-10-15.json`, `-part2-`
- Original exact owner directed ERC20 CA events: `bsc-meme-address-model-v1-p4c-ddac-adff-a83b-exact-ca-events-part1-2026-10-15.json`, `-part2-`
- Original N−1/N query precommit and actual historical native balances: `bsc-meme-address-model-v1-p4c-ddac-adff-a83b-native-balance-precommit-2026-10-15.json`, `bsc-meme-address-model-v1-p4c-ddac-adff-a83b-native-balance-part1-2026-10-15.json`, `-part2-`
- Bounded WBNB source outcomes: `bsc-meme-address-model-v1-p4c-ddac-adff-a83b-wbnb-mint-burn-part1-2026-10-15.json`. Most exact-block OR Deposit/Withdraw event RPC responses were >8 KB truncated, not evidence of no transfer.
- Standard normalized evidence: `bsc-meme-address-model-v1-p4c-ddac-adff-a83b-five-inventory-closed-2026-10-15.json`; immutable 8-source Git SHA list inside, deterministic offline replay `bsc_meme_address_model_v1_p4c_ddac_adff_a83b_five.py`, adversarial tests `test_bsc_meme_address_model_v1_p4c_ddac_adff_a83b_five.py`.
- Initial code-only CI exposed a **non-economic test gate error**: a deliberately status-tampered `TRUNCATED` receipt caused `KeyError` rather than an explicit `ValueError`. Corrected: now missing/invalid claimed full receipt fails with source-readable ValueError; frozen source JSON and economics not rewritten. Verified next exact HEAD CI [BSC run #38698051690](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38698051690) **SUCCESS**: 322 source-specific primary unittest cases, 9 supplementary, **328 full BSC tests**, the three other source-replay CI workflows likewise SUCCESS. For subsequent document-only HEAD, recheck exact SHA CI again.

## Cohort denominator and forward research

Prior high-grade matrix `bsc-meme-address-model-v1-p4c-23x19-five-native-rounds-mixed239e-2026-10-15.json` **unchanged**: 5 actual owner-native settled selected rounds (**3 positive / 2 negative**), **4 distinct wallet×CA cells**, **433 not economically fully audited** across frozen original **23×19=437**. This new bounded five-case batch is evidence of real signed activity and full token quantities, not additional settled economic results and does not reduce the 433. User-facing current followable recommendations remain **zero**. P4-B observer global U and P5 true delayed fill/slippage/tax/gas/exit remain unproven.

**Next high-value priority**: do not blindly repeat failed full receipt calls. Reuse original `SETTLED_NATIVE_DIRECT_WBNB_GAS` candidates from Stage24 (8E6B token `4` both original +/− episodes) in a **precommitted, bounded** QA batch and cross-validate Stage24 source receipts/BNB historical facts. This provides a third distinct major CA positive/negative control within the original 19 CA, without ignoring other original wallets or elevating owner profit to follower profit. Continue looking for additional **different** original EOA with full quote/gas evidence, and in parallel pursue actual globally first observable & executable U and P5 lagged follower opportunity.

**Independent review:** Previous user-supplied other-AI `APPROVE` applies exclusively to SHA `ea6684a3478d301534ff9d26b5984367eb7530f3`, not these newer P4-C model/economic code SHAs. Last reviewed request on PR #40 concerns `95d3c5eb9094567f329c59f95ffeddf17298de2f` and is **PENDING_OTHER_AI_REVIEW**. This turn's additional five-case result is *only source closure* and does not promote a new economic profit tier. If another AI independent stage review is requested, provide a complete copy-ready fixed-current-SHA prompt directly to user per `bsc-meme-address-model-v1-development-rules-2026-10-15.md`. No PR merge, Mac service, live trading, notification or monitoring changes authorized.
