# BSC 地址模型 P4：PancakeSwap V3 Swap 事件语义更正及 17 池首次活跃流动性复核

Status: VERIFIED_IN_NEW_UNIFIED_REPLAY / RESEARCH_ONLY / PRODUCTION_TRADING=NO_GO. This corrects event semantics **without mutating the immutable historical onchain source or older audit artifact**.

## Correction to the prior 4-pool handoff

The original legacy Niulai first-active proof file and helper `bsc_meme_address_model_v1_p4_competing_first4.py` label topic0 `0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83` as `first_mint_event`, `TOPIC_MINT_EVENT` and `V3_FIRST_IN_RANGE_MINT_AFTER_CREATION`. **Those labels are semantically wrong.** This topic is PancakeSwap V3 `Swap(address,address,int256,int256,uint160,uint128,int24,uint128,uint128)`, as confirmed by the indexed ABI in the BNB Pancake V3 contract ecosystem. Actual Pancake V3 Mint topic0 is `0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde`.

The Niulai pool `0xab058332a7279f1e64162be08f59ac0cd9601759` remained at **zero active liquidity at the creation block 115919188** after creation Initialize and an original Mint. Its source-proven **first positive in-range liquidity at block 115919205 (17 blocks later)** is supported by historical state and bounded pool logs, but the subsequent trigger observed there is **Swap**. It must not be called a later newly minted initial deposit. Legacy source fields are retained so their original Git checksums and historical reproducibility remain intact. The new authoritative normalized output uses `V3_FIRST_ACTIVE_ON_PANCAKE_SWAP_AFTER_17_BLOCKS`.

BULLA V3/USDT fee 10000 pool `0x802c7a20ecd42a383c5ce96a59af062bbaf887d3` was separately verified: pool created at block 50972700 with Initialize/Mint but active in-range liquidity zero; **full unfiltered original `eth_getLogs` for blocks 50972701 through 50972710 yielded one pool Swap at 50972710 and no preceding pool log in that bounded window**; raw `liquidity()` at creation and block 50972709 was zero, became positive at 50972710 and matched the Swap's emitted post-event liquidity word. First positive is thus 10 blocks after creation in this scoped pool, via observed Swap. This demonstrates why treating every Mint as activated tradability is wrong.

## Newly accepted P4-A scope

- 17 historically active competing PancakeSwap V2/V3 WBNB/USDT pools, **15** with positive in-range V3 liquidity or bilateral V2 reserves by their creation block end; **two** delay cases above.
- Original 13-indexed factory event matrix: `bsc-meme-address-model-v1-p4-competing13-exact-creation-events-2026-10-14.json`.
- New original creation evidence: `bsc-meme-address-model-v1-p4-competing13-creation-state-part2-2026-10-14.json` and `part3` (eight previously unread pools). Previously written `part1` retains five originals.
- Specific BULLA ten-block event/three-state source: `bsc-meme-address-model-v1-p4-bulla-v3-usdt-10000-delayed-active-proof-2026-10-14.json`.
- Normalized authoritative output: `bsc-meme-address-model-v1-p4-competing17-first-active-unified-2026-10-14.json`.
- Replay: `bsc_meme_address_model_v1_p4_competing17.py`. It independently rejects a fake factory/CA, fabricated Mint, missing pool, incorrect zero creation liquidity, wrong BULLA Swap type/amount, altered Niulai Swap and legacy four-pool source drift. Associated `test_bsc_meme_address_model_v1_p4_competing17.py`.
- First newly wired CI failure `38588048496` was genuine: validator incorrectly demanded that later same-block Sync events also belong to the creation transaction. Fixed by retaining all creation-block pool events but selecting only the factory transaction's events for its first deposit causal claim. Successful new HEAD CI `38588188157` on SHA `69be11f4f017ce0e5b2fdb2671331cc227ec7ae8`.

**Do not quote the old Niulai `first_mint_event` label or original `source_event_kind` as a Mint fact.** The onchain log fields are valid but their original human naming was invalid; the unified corrected matrix is the current authority. Historical proof remains immutable.

## Strict limits and next business gate

All 17 are **venue-scoped first-active-liquidity findings**. Their historical creation period may precede or follow launchpad trading; earliest **whole market U**, actual successful buy and sell at fixed size, transfer tax, real quote asset settlement, wallet capital at observer-visible time and follower execution with lag are still `UNRESOLVED`. The five alternative pools inactive at the original V2 baseline are retained as potential earlier-history negatives/unknowns and not silently excluded from P4-B.

Proceed to P4-B major opportunity U + historical executable quotes and negative controls in batches. No new auto-alerts, production, Frank, Monster or model-derived trade recommendations. Independent other-AI review remains pending. Draft PR #40 stays unmerged.
