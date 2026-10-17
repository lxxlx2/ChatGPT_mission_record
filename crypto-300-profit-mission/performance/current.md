# Mission Performance / Starting-Capital Provenance and Realized PnL

Updated: 2026-10-17 Asia/Bangkok (SurfBoard #5396 on-chain sale cashflow recorded separately; Mission overall PnL still unresolved)
Status: `MISSION_PNL_UNRESOLVED`
Current position/balance authority: `../portfolio/current.md`.
Operational authority: `../state/latest.md`.

## Realized NFT sale cashflow, return unresolved — SurfBoard #5396 (2026-10-17)

- **Direct-chain observation, no inferred authorization:** Robinhood Chain ERC721 `0x18c9719ab6ae4e1a6f95f281ef288e3af5d58602` token **5396** sold/transferred out of canonical EVM owner `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c` to `0xd90825b15f70b64f81bab600f7f56fe3f86747ce` at **2026-10-17 03:34:38 Bangkok**, successful Seaport tx [`0xb222259e480d4b9264af49cbbcd9709b7296d0ee35aec35b264fff35fdde91e9`](https://explorer.robinhood.com/tx/0xb222259e480d4b9264af49cbbcd9709b7296d0ee35aec35b264fff35fdde91e9), block `0x562e5dd`. OwnerOf and getNFTsForOwner confirm the NFT is **not currently held**.
- **Seaport gross consideration:** `0.04 ETH`; successful `OrderFulfilled` event's three native consideration amounts **0.0376 ETH to seller (canonical wallet)**, **0.0004 ETH** and **0.002 ETH** to other recipients. These other-recipient amounts are not user proceeds; the buyer's gross 0.04 ETH must **not** also be counted as user assets. The sale has already happened; the USD equivalent at sale-time and actual original economic cost basis are not independently reconstructed. Historical annual Surf PRO subscription **$228** was paid for a service that generated a free NFT claim, and cannot automatically be booked as NFT cost or return.
- **Follow-up transfer:** wallet external successful tx `0xb02baa0892b9f24f0e5dda49ed76c8d48e8cbb027b447b2a8a87129c733b1be2` at **2026-10-17 05:01:50 Bangkok**, **0.03783 ETH** sent from canonical wallet to `0x4cd00e387622c35bddb9b4c962c136462338bc31`; downstream ownership/use `UNVERIFIED`. This outbound amount is not identical to 0.0376 ETH seller payment and must not automatically be equated or subtracted as trading costs. Current Robinhood native balance only **0.000020785408780798 ETH**, separately priced under $1 and excluded from current displayed investment NAV.
- **PnL treatment:** mark `SURFBOARD_5396_POSITION=CLOSED_BY_ONCHAIN_TRANSFER`, `SURFBOARD_5396_SALE_CONSIDERATION=CONFIRMED`, `SURFBOARD_5396_NET_PNL=UNRESOLVED`. This does not change the recorded GANG ICO realized loss **−96.210562 USDC before SOL gas**, and no external Surf subscription or NFT sale should be attributed to the original $300 Mission starting set without traced funding. No changes to `MISSION_PNL_UNRESOLVED`.

## New realized result — GANG ICO complete exit (2026-10-12)

**This is a separately attributable realized position PnL, NOT proof of Mission-wide PnL or original $300-to-$3000 target progress.** Ledger sources: `../positions/gang.md`, Solana finalized FundingRecord, actual wallet pre/post exit balances and direct indexed sale signature.

| Ledger item | Cashflow / treatment |
| --- | ---: |
| Original escrow deposit | −500.000000 USDC (2026-10-08) |
| FundingRecord refund of rejected allocation | +19.507520 USDC (2026-10-12; processed, already part of wallet USDC) |
| Approved investment principal converted to 8008.208 GANG | 480.492480 USDC at $0.06 each |
| Full token sale net USDC cash receipt | +384.281918 USDC (2026-10-12 01:51:52 Bangkok) |
| **Total recovered cash from original escrow** | **403.789438 USDC** |
| **GANG position realized trading PnL** | **−96.210562 USDC** |
| ROI on actual approved 480.492480 USDC token cost | **−20.023323%** |
| ROI on original 500 USDC commitment incl. refund | **−19.242112%** |
| Post-sale GANG inventory | **0**; position status **CLOSED** |

Sale original Solana transaction (successful finalized, slot 455756451):
https://solscan.io/tx/2cGKrncYix2AK2kAqtepgWJ1ipBsuH95TYwPHohRhAEkkbNRiwDbUUzLUyTG5RhA5D1xdi4Cbj9PUajsx8gGJNDk

Direct finalized wallet balance reconciliation across this sale:
- Before: 8008.208 GANG, 87.434841 USDC (slot 455756240).
- After: no positive GANG, **471.716759 USDC** (slot 455757417).
- Only one USDC account transaction between snapshots; receipt is 471.716759−87.434841=384.281918 USDC.
- Native SOL gas and any additional denominated fees in SOL are not included in the exact USDC PnL; one recorded transaction network fee 0.000352350 SOL, broader SOL balance change 0.000552350 SOL is not wholly attributed.
- **Do not count the $500 escrow, $19.507520 refund or 384.281918 sale proceeds again as incremental current assets**. All current amounts are represented by updated wallet USDC. Account screenshot profit figures do not establish trade profit.

Mission-wide starting-asset PnL remains `MISSION_PNL_UNRESOLVED` because full attribution of the initial $300 plus six Credits NFT original basis, withdrawals, external deposits, transfers, and other investments is still outstanding. Do not present the GANG loss as the Mission's full profit/loss.


## Mission objective and starting inventory

- Target: **$3,000 equivalent net liquidation value** of the **original Mission starting asset set**, with auditable cashflows.
- Original starting cash principal: **$300**.
- Original six Credits NFTs: **#21646, #21753, #22857, #23042, #23232, #23328**. These are part of starting-set provenance and must be valued and attributed separately from later cash contributions.
- **Current original Credits held: 0; historical exited: all 6.** Ethereum owner-specific Alchemy check at block 26163166 (2026-10-10 16:15:59 UTC) confirms zero current Credits for the canonical wallet. Historical sale provenance is recorded in `../positions/credits.md`.
- UNICRED #230 is not owned (verified Unichain block 60900610 on 2026-10-10); closed historical asset, not current holdings.

## Historical asset reference (2026-10-10; superseded by 2026-10-12 position and portfolio observations)

As of this report, separately verified >=$1 chain positions consist of:
- Solana wallet USDC **58.047629**, approximately **$58.10** using the sampled USDC/USD quote.
- Solana wallet SOL **0.038163041**, approximately **$4.21** using sampled Binance SOLUSDT spot.
- **Known material on-chain subtotal ~$62.31** (2026-10-10 chain and quotes).
- Binance flexible USDC last observed by **2026-10-09 user screenshot**, UI ~$656.07; **not independently refreshed October 10**.
- **Mixed-freshness total reference ~$718.38**; *neither verified comprehensive NAV nor Mission-earned profit*.
- The GANG **500 USDC** sale commitment is separately encumbered historical cost and excluded from liquid subtotal, with allocation/refund pending.
- The entire Bybit account is personal living/rent money, excluded from all Mission investment and performance calculations.
- Incomplete/unpriced token/NFT or unsupported-chain holdings remain **UNRESOLVED**, not zero or <$1 by assumption.

## Permanent display/valuation rule

- **An individual asset/position must have a supportable current USD valuation >= $1.00 to be included in displayed marked holdings or USD subtotals.** Exclude each individually marked asset valued < $1.00; do not combine dust positions to reach the threshold.
- Unpriced tokens, claim-bait, spam and unverified NFT asks are not valued as dollars; keep unresolved economic rights separate. The $1 display filter does **not** delete the chain history or convert unknown values to zero.
- Use source classes `DIRECT_CHAIN`, dated `USER_CONFIRMED`, `MARKET`, `UNAVAILABLE/UNRESOLVED`. All CEX quantities need a new authenticated or user-supplied observation to become current.
- Historical cost and escrow commitments are not necessarily recoverable NAV.

## Performance methodology and open accounting

Mission PnL and target progress **remain UNRESOLVED**, pending full transaction-level reconciliation of starting $300, six Credits' acquisition/sales, fees, subsequent transfers, deposits and attribution. In particular:
- All six Credits have been exited; their prior floor/ask marks from 2026-09-28 must not be carried forward as current inventory.
- No separate historical NFT sale proceeds may be stacked atop wallet balances without tracing transfers/redeployment.
- Transfers between wallets, CEX accounts, bridges and escrow are not realized profit.
- Refunds (including the already refunded **1,000 USDC JUMP sale deposit**) are capital return, not income.
- External deposits, other project/private-sale balances and Binance savings are not automatically part of the original $300 Mission return merely because included in a broad asset-completeness view.
- Positions below $1 are excluded from the current *display* view under user instruction, but actual fees/losses from such positions still affect accurate historical cashflow accounting when reconciling realized performance.
- Do not infer any ROI, return multiple, drawdown or claim of $3,000 target progress from the mixed-freshness holdings subtotal.

## Historical snapshot policy

The earlier 2026-09-28 tracking snapshot reported two then-owned Credits and one UNICRED, Binance 682.40 and a $0.10 display threshold. Those values and that threshold are now **superseded**, retained only through prior Git history and original dated evidence. `performance/current.md` is a current pointer, not an append-only historical daily report.

No wallet signing, transaction or account transfer performed by this accounting correction.
