# JUMP / Jumper Legion 公售参与计划与项目跟踪


Human-facing research copy: `research/projects/jump/jump-legion-sale.md`
Operational compatibility path retained for monitoring safety.

Updated: 2026-09-25 21:00 Asia/Bangkok

## Official / high-confidence sale frame
- Venue: Legion Curated Sale.
- Chain / payment asset shown in Legion app: Ethereum Mainnet / USDC.
- Applications open: 2026-09-29 13:00 UTC = 20:00 Asia/Bangkok.
- Legion app target: USD 2M; hard cap: USD 3M.
- Legion app estimated TGE: Q4 2026.
- Legion sales are merit-based, not FCFS; project reviews applications after the window.
- User Legion Score snapshot: 591/1000.
- Current widely indexed sale terms associated with the Sep-25 Legion announcement: USD 75M sale FDV, USD 0.075/JUMP, 40M JUMP / 4% total supply, 50% TGE unlock + remaining 50% linear over 4 months. Direct X post body was not machine-readable in the current tool environment, so final Legion TPA/Show Terms remains the execution authority if any field differs.

## Current PM / market signal
Polymarket FDV one day after launch snapshot:
- >60M: ~92%
- >75M: ~85%
- >100M: ~73%
- >150M: ~67%
- >200M: ~39%
- >300M: ~30%
- total FDV market volume only about USD 1.8K, so use directionally, not as precise probability.
Launch-by-Dec-31-2026 market is materially more liquid (tens of thousands of USD volume) and current market pricing is roughly low/mid-80s% Yes in fresh indexed data.

## Product / fundamental context
- Jumper official: >USD 40B lifetime volume, >100K MAU, #1 bridge aggregator by volume, >15% bridge-aggregator market share.
- DefiLlama current snapshots: roughly USD 1.0B 30d bridge-aggregator volume and roughly USD 200M+ 30d DEX-aggregator volume.
- Jumper is spinning out as an independent consumer-facing company; JUMP is intended by management to be the token-first ownership instrument and there is no separate equity round announced. This does NOT by itself guarantee token buybacks/dividends/revenue share.

## Allocation decision
Current direct-chain liquid USDC is about 782.385 USDC on Solana. Keep separate:
- 150 USDC hard short-window opportunity reserve.
- 100 USDC ETH trading reserve after Sep-25 options review.
- Separate low-risk 500 USD bucket remains isolated and must not be used.
- Therefore JUMP application target is **400 USDC**, leaving ~132 USDC extra uncommitted above the two reserves.
- This 400 is the application/deposit amount, not guaranteed allocation. A partial allocation is acceptable and likely possible given merit-based review/oversubscription.

Hard downgrade rules:
- If final Legion TPA/Show Terms differs and sale FDV >100M: reduce application to 250 USDC.
- If FDV >125M: skip/re-evaluate.
- If TGE unlock <50%, or new cliff/lockup is materially worse than 50% TGE + 4mo linear: reduce to 250 USDC or less depending severity.
- If material initial-circulation/team/airdrop unlock creates clearly excessive TGE sell pressure, do not force the 400.
- If 75M FDV + 50% TGE + 4mo linear remains final, apply 400 USDC.

## Profit map for a full 400 USDC allocation at 75M FDV
Tokens: ~5,333.33 JUMP.
TGE unlocked if 50%: ~2,666.67 JUMP.

FDV / total mark-to-market / gross P&L before vesting-price drift:
- 60M: USD 320 / -80 (-20%)
- 75M: USD 400 / 0
- 100M: USD 533 / +133 (+33%)
- 150M: USD 800 / +400 (+100%); unlocked half alone worth about USD 400, allowing principal recovery if liquidity is executable.
- 200M: USD 1,067 / +667 (+167%); unlocked half ~USD 533.
- 300M: USD 1,600 / +1,200 (+300%); unlocked half ~USD 800.

Do not treat the locked 50% at the TGE mark as realized. If TGE is around 150M and the four-month vested half averages only 100M FDV, total realized value would be roughly USD 667, about +67% on the full allocation after selling the TGE half at 150M.

## Hedge decision
- Do NOT buy Polymarket hedge before allocation.
- The timing market hedge is too expensive when Dec-31 No is around the mid-teens cents, and it only hedges delay, not token-price underperformance.
- FDV PM has only ~USD 1.8K total volume and wide spreads, so it is not suitable as a precise hedge.
- Reconsider a delay hedge only after allocation is confirmed if Dec-31 No <=10c with meaningful depth.
- Prefer a liquid JUMP premarket/perpetual hedge after allocation if available and if market-implied valuation reaches >=2x sale FDV; size only against unlocked exposure.

## Execution checklist
- Sale is not FCFS. Do not rush the first second.
- Before application, use Legion's authenticated Show Terms/TPA as the final authority for FDV, unlock, vesting, jurisdiction, min/max allocation and dates.
- Need Ethereum Mainnet USDC and enough ETH gas. Current primary EVM wallet has ~0.000922 ETH mainnet and 0 USDC mainnet, so bridge/fund before application. Current Solana wallet has ~782.385 USDC.
- Keep at least the 150 opportunity reserve + 100 ETH reserve untouched.


## Funding readiness update — 2026-09-25 evening
Fresh direct-chain read of the primary EVM wallet:
- Ethereum mainnet USDC: **400.308121**.
- Ethereum mainnet native ETH: **0.001667063838788351**.

The 400-USDC application reserve has therefore already been moved to Ethereum mainnet. Do not bridge the same reserve again.

Remaining preflight work:
- At the first Mission run on 2026-09-29 at or after 19:00 Asia/Bangkok, read the authenticated Legion Show Terms / TPA and re-check FDV, price, unlock, vesting, allocation limits, jurisdiction and initial circulation.
- Check current Ethereum gas and approval/application transaction requirements.
- Require at least 2x the estimated approval + application gas cost as native ETH buffer. If an execution-grade estimate is unavailable and ETH remains below 0.003 ETH, warn to top up gas before the 20:00 opening.
- If final terms remain approximately 75M FDV + 50% TGE + remaining 4-month linear and no new material float issue appears, keep the 400-USDC application target.


## TGE timing clarification — 2026-09-25
Latest high-confidence guidance is **Q4 2026**, with no exact calendar date announced yet.

There was a real documentation conflict on Legion/Jumper sale materials:
- one attached sale document stated TGE expected in Q4 2026;
- an older/conflicting round slide stated token launch 6 months after the end-of-September sale, which would imply roughly March 2027.

Jumper/LI.FI team member Arjun Chand (@arjunnchand) publicly replied to the conflict: **"updated, TGE is Q4"**. His public profile is affiliated with both LI.FI and Jumper, and current Jumper/LI.FI team references corroborate that affiliation.

Execution interpretation:
- Treat **Q4 2026 (Oct 1–Dec 31, 2026)** as the current authoritative expectation.
- Treat the "6 months later / March 2027" slide as stale/superseded unless a newer authenticated Legion TPA/Show Terms explicitly reinstates it.
- Exact TGE day remains **TBD**.
- The Sep-29 preflight must still re-read authenticated Legion documents. If they again conflict, do not infer; escalate the conflict and use the newest signed/dated TPA plus direct team clarification.
