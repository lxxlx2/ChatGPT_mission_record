# Mission Performance / Starting-Capital Provenance and Realized PnL

Updated: 2026-10-10 Asia/Bangkok
Status: `MISSION_PNL_UNRESOLVED`
Current position/balance authority: `../portfolio/current.md`.
Operational authority: `../state/latest.md`.

## Mission objective and starting inventory

- Target: **$3,000 equivalent net liquidation value** of the **original Mission starting asset set**, with auditable cashflows.
- Original starting cash principal: **$300**.
- Original six Credits NFTs: **#21646, #21753, #22857, #23042, #23232, #23328**. These are part of starting-set provenance and must be valued and attributed separately from later cash contributions.
- **Current original Credits held: 0; historical exited: all 6.** Ethereum owner-specific Alchemy check at block 26163166 (2026-10-10 16:15:59 UTC) confirms zero current Credits for the canonical wallet. Historical sale provenance is recorded in `../positions/credits.md`.
- UNICRED #230 is not owned (verified Unichain block 60900610 on 2026-10-10); closed historical asset, not current holdings.

## Current asset reference (not Mission performance)

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
