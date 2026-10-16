# BSC PR #40 independent REQUEST_CHANGES H1/H2/H3/M4/L5 correction (2026-10-16)

**Status:** SOURCE-ONLY FIX PROPOSED, `PENDING_OTHER_AI_REVIEW`; no code self-approval. This report is scoped to the independent review against prior fixed SHA `d66aa8cb91ec037196e67e213311a29d7141cc74`. The earlier `APPROVE@da0799dbae2314659ea6b21799d86a879cd1066c` is NOT a review of any of this new V3 change. PR #40 remains Draft/Open/unmerged; `NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`.

## H1 — original V1/V2 cohort displacement disclosed, no result-selection laundering

The original five-case V1 precommit is **historically immutable**: original P2 indices **[13,31,38,46,42]**, 3 positive/2 negative source native-wallet-block signs. V2 original indices **[15,31,38,46,44]**, 2 positive/3 negative. Reviewer correctly found TWO changes: **P2#42→#44** (P2#42 IFML original trade actually **2025-12-29**, not 2026) **and P2#13→#15**. The latter was **not justified by date**: P2#13 8E6B Dragon original buy occurred **2026-04-20** and had already been given `SETTLED_NATIVE_DIRECT_WBNB_GAS` source grade. Both indices' native-wallet-block signs were previously known. V2 had mistakenly represented the batch as a transparent date correction; the change also silently removed the largest V1 positive. The original V1/V2 source files are not rewritten or deleted.

**No unbiased sampling claim survives.** [V3 post-review provenance amendment](./bsc-meme-address-model-v1-p4c-v3-review-corrected-six-episodes-2026-10-16.json) visibly combines original four valid-2026 V1 indices [13,31,38,46] **with** V2 cases #15 and #44: exactly **six** (not five) already-exposed original P2 episodes, **five distinct frozen EOA owners**, **four exact CAs**, **3 positive and 3 negative** source native scope. It is explicitly an **outcome-aware post-review expansion** rather than a preregistered outcome-blind sample, statistical success estimate, or P5 holdout.

| Version | Original P2 index array | Native-scope + / − | Sum of selected EOA-block net changes (wei) | BNB |
| --- | --- | --- | ---: | ---: |
| Immutable V1 | [13,31,38,46,42] | 3 / 2 | +223671359895044206 | +0.223671359895044206 |
| Immutable V2 | [15,31,38,46,44] | 2 / 3 | −400073738684035463 | −0.400073738684035463 |
| Post-review V3 | [13,15,31,38,46,44] | 3 / 3 | −146773456364646148 | −0.146773456364646148 |

These values are **historical owner account/block scopes**, not tax/fee-isolated owner realized trading profits, alpha, or observer-replicable return.

## H2 — original block header timestamp / UTC, not index exclusion

[Thirteen original BSC block header observations](./bsc-meme-address-model-v1-p4c-v3-original13-block-header-calendar-2026-10-16.json) now pin **12 first/last block headers for all six 2026 V3 episodes**, plus the excluded P2#42's first block. Each record includes exact original `block_hash`, `timestamp_hex`, `milliTimestamp_hex`, UTC from integer milliseconds and a flag disclosing when the RPC response for the full *block body* was clipped (no claim to possess a complete transaction list). Gate verifies 2026 **from raw header timestamps**, not source `is_2026_major_priority` boolean or merely a blacklist for #42.

- P2#13 8E6B Dragon: 836? No; actual first **93584281** = **2026-04-20T05:53:09.350Z**, last **94208823** = **2026-04-23T12:03:24.450Z**.
- P2#15 8E6B 我踏马来了: **76554500–76582674**, **2026-01-21**.
- P2#31 239E 龙虾 previously missing date: **86649314** = **2026-03-15T01:35:12.750Z**, **87876365** = **2026-03-21T11:36:16.150Z**.
- P2#38 877AF MARSCOIN: **2026-07-28**; P2#46 2ADF 牛来: **2026-08-15–16**; P2#44 ADFF 龙虾: **2026-09-14**.
- Excluded P2#42 ADFF 我踏马来了 original **73339965 = 2025-12-29T11:18:55.000Z**, despite earlier `is_2026_major_priority=true` source marker.

## H3 — partial receipt provenance and conservative success grade

Initial 14 original source queries remain unchanged: **5/14 parseable complete success receipts**, six clipped text sources with apparently visible `status=0x1`, three clipped without status. The reviewer questioned the absent gas with visible status. A [separate, timestamped requery with nine clipped-receipt source excerpts](./bsc-meme-address-model-v1-p4c-v3-nine-truncated-receipt-source-excerpts-2026-10-16.json) proves why initial source classification cannot be generalized: Alchemy's tool output keys are **not in a stable order**. A literal `status` may appear at string offset 21 and the `gasUsed` key be outside the 8098-character limit; another response shows gas at offset ~274 but no status. This second pass found **8/9 partial responses with visible status and 1/9 without**, whereas the frozen *earlier* pass saw 6/9 and 3/9. Both are source observations, **neither is a full receipt**. The excerpt record preserves per-call exact literal source prefix/key positions and truncation flag, not entire byte-for-byte wire response. No fabricated full receipt, no silent missing→zero and no permanent success upgrade.

The V3 classification is intentionally **5 full receipts + 9 truncated/unverified** from the original 14. The missing original three full receipts are **still unresolved**; direct public JSON-RPC from this runtime lacks network DNS and the alternative Blockscout connector reports chain ID 56 unsupported. The two newly reinstated P2#13 original signed transactions, [buy and sell source](./bsc-meme-address-model-v1-p4c-v3-restored-p2-13-original-two-transactions-2026-10-16.json), are **both full parseable `status=0x1`** on this provider. Thus the expanded six-case **16** original signed transactions have **7 full parsed successes and 9 truncated/unverified**, all 16 original signer and block checked. This **does not** prove fully attributed quote-token profit or eliminate routing and internal settlement ambiguity.

## M4 — executable fail-closed verification

[Canonical V3 pinned replay](./bsc_meme_address_model_v1_p4c_v3_review_gate.py) validates 12 immutable original JSON Git blob pins, exposes V1/V2/V3 and all three native-scope sums, checks source episode CA/grade, verifies every 2026 first/last integer-timestamp BNB header and the excluded 2025 date, 16 original signer/block identities, correctly distinguishes complete receipts from clipped payloads, and retains `P4C=PARTIAL / P5=BLOCKED / PRODUCTION=NO_GO`. [V3 adversarial tests](./test_bsc_meme_address_model_v1_p4c_v3_review_gate.py) cover the missing P2#13 positive, changing outcome composition, hiding V1, upgrading posthoc to holdout, altered 239E header/date, missing header, forged clipped status, forged full status and missing original transaction.

Prior [V2 gate](./bsc_meme_address_model_v1_p4c_fiveowners14_gate.py) and its 14 original tests remain as historical evidence, but the CI labels V2 **POSTHOC/HISTORICAL/NOT CANONICAL** and separately runs strict V3 as the canonical post-review source grade. No old source file or negative round is deleted.

## L5 — exact-CA canonical alias map

`IFML = 我踏马来了 = 0xc51a9250795c0186a6fb4a7d20a90330651e4444`; `Dragon = 龙虾 = 0xeccbb861c0dda7efd964010085488b69317e4444`; `MARSCOIN = 0xfe189e97832da1573e4e4ff034f4ffc3a15c7777`; `牛来 = 0xbeea1d618e533a387d941f58a7d4c9b7bd377777`. External aliases do not modify exact CA or source labels.

**Next necessary work:** independently review this new exact SHA and primary RPC source snippets; then pursue bounded, free full-receipt extraction for nine truncated transactions and origin quote-token causal accounting. Stop if no free RPC/full receipts rather than looping/guessing. Public actionable U remains `UNRESOLVED`; 1/5/15-minute follow-backtest P5 `BLOCKED`.
