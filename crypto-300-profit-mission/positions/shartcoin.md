# SHARTCOIN Position

Updated: 2026-09-24 09:01 Asia/Bangkok

## Identity
- User wallet: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Canonical planned mint: `UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids`
- Campaign: `9FjwHicbkzP17NEW94UasBa3LfWtqmsmddzstq8UqKxP`

## Cost / allocation
- Committed: 1 SOL
- Refunded: 0.600039112 SOL
- Accepted principal: 0.399960888 SOL
- Estimated initial allocation: 173,982.98628 SHARTCOIN
- Fixed participation-price reference at SOL = 115 USD: about 0.00026437 USD/SHARTCOIN

## Executed ladder, user reported
| Level | % of original allocation sold | Approx tokens | Gross proceeds |
| --- | ---: | ---: | ---: |
| 2x | 10% | 17,398.30 | 0.079992178 SOL |
| 3x | 25% | 43,495.75 | 0.299970666 SOL |
| 5x | 20% | 34,796.60 | 0.399960888 SOL |
| Total | 55% | 95,690.64 | 0.779923732 SOL |

Approx net proceeds after a 2%–2.5% swap fee, before slippage/network fees: 0.76433–0.76043 SOL.

## Estimated remaining position
- Remaining: 45% of original allocation
- Estimated balance: 78,292.34 SHARTCOIN
- At exactly 5x participation price, estimated mark value: about 0.899912 SOL.
- Accepted-position realized + remaining mark at exactly 5x: about 1.679836 SOL versus 0.399961 SOL accepted principal, or about 4.20x on the accepted position before fees/slippage.
- Including the 0.600039112 SOL refund, gross wallet value recovered/marked from the original 1 SOL commitment at exactly 5x is about 2.279875 SOL before fees/slippage.

## Remaining sell plan
| Level | Sell % of original | Approx tokens | Gross SOL at exact target |
| --- | ---: | ---: | ---: |
| 8x | 20% | 34,796.60 | 0.639937421 SOL |
| 15x | 10% | 17,398.30 | 0.599941332 SOL |
| Runner | 15% | 26,097.45 | dynamic |

## Risk rules
- No automatic averaging up after the 5x move.
- 5x has already been monetized; preserve recovered principal.
- A fall back below 3x after reaching 5x is a material momentum warning requiring fresh volume/liquidity/holder review.
- A fall below 2x with deteriorating liquidity/volume favors aggressive profit protection.
- Security/authority/LP anomalies override all price targets.
- Final runner uses a wide, meme-appropriate trailing framework only after further extension and only while market structure remains healthy.

## Verification status
The quantities above are accounting estimates from the user's confirmed refund and reported target fills. Direct wallet token balance and swap transaction verification remain pending because the connected Solana RPC authorization was unavailable at this update. Do not label the estimated balance as chain-confirmed until direct RPC/explorer evidence is obtained.


## Live identity discrepancy discovered after launch review
- Fresh public social evidence from YokaiCapital's current profile explicitly posted: `solana:GKpNJz7yMuhZka9izamv6sDUxCsDr58pFMUaw1TQpump` alongside the kids.fun Shartcoin commitment announcement.
- The public GitHub `deployment/mainnet/campaign-plan.json` still names `UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids` as the planned mint.
- Therefore the previous assumption that `UpBB...kids` alone was the live canonical trading mint is no longer treated as confirmed.
- Until a direct Solana RPC/explorer read resolves the mismatch, both addresses must be tracked and the actual mint received by wallet `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp` must determine the live asset identity.
- This discrepancy is material and must not be silently ignored in future monitoring.


## Remaining SHART management refinement — 2026-09-24

Based on the user-reported execution through 5x, treat about 45% of the original allocation as remaining until direct chain balance verification replaces the estimate.

Primary upside ladder:
- 8x fixed participation price, about USD 0.002115 at SOL=115: sell 20% of the ORIGINAL allocation, approximately 34,796.6 SHART. This is about 44.4% of the currently estimated remaining position.
- 15x, about USD 0.003966: sell another 10% of ORIGINAL allocation, approximately 17,398.3 SHART.
- Final 15% of ORIGINAL allocation, approximately 26,097.4 SHART: runner.

Downside / failed-momentum rules after the 5x touch:
- A normal pullback from 5x is not by itself a sell signal.
- If price loses the 3x participation level (about USD 0.000793 at SOL=115), fails to reclaim it on roughly a 30-60 minute structure, AND volume/liquidity/net-new buyers deteriorate materially, reduce roughly 15% of the ORIGINAL allocation (one-third of the estimated remaining 45%) rather than waiting blindly for 8x.
- If price subsequently loses the 2x level (about USD 0.000529) with continuing liquidity/volume deterioration or evidence of concentrated large-wallet distribution, exit most of the remaining position; at most keep about 5% of ORIGINAL allocation as a lottery runner.
- If 8x is reached and the planned tranche is sold, do not allow the remaining 25% of original allocation to round-trip back through 3x without a fresh market-structure review.
- After 15x, manage the final 15% runner with a wide 25%-30% trailing framework from a meaningful local/high-timeframe high, adjusted for live liquidity; do not use a tight stop during first-hour meme volatility.
- Do not add new USDC to SHART merely because it has already run 5x. Any re-entry/add requires a new consolidation, verified live liquidity/holder data, and a fresh catalyst.

Identity update:
- YokaiCapital's fresh public post explicitly publishes `GKpNJz7yMuhZka9izamv6sDUxCsDr58pFMUaw1TQpump` for this kids.fun Shartcoin launch. Track this as the live public CA candidate while preserving the GitHub planned-mint discrepancy until direct wallet/launch-transaction chain verification resolves it.
