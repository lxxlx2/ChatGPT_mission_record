# Crypto Research Migration Map

Updated: 2026-09-26
Status: staged migration, monitoring compatibility preserved

This map decides where existing mixed Mission content belongs. It does not require immediate deletion of operational files.

## Positions

| Current operational file | Human-facing category | Target research location | Migration rule |
| --- | --- | --- | --- |
| `positions/credits.md` | NFT | `research/nfts/jack-credits/` | research copy created; keep operational compatibility path during monitor validation |
| `positions/jump.md` | Project | `research/projects/jump/` | research copy created; keep operational compatibility path during monitor validation |
| `positions/pons.md` | Token | `research/tokens/pons/` | keep operational current-state authority; split long-form buyback/market research on next substantive update |
| `positions/gstock-plan.md` | Meme | `research/memes/gstock/` | keep active position state; move long-form thesis when next researched |
| `positions/kardashev.md` | Meme | `research/memes/kardashev/` | keep live accounting; move narrative/market analysis later |
| `positions/shartcoin.md` | Meme | `research/memes/shartcoin/` | historical operational record; future research goes to Meme library |
| `positions/unicred.md` | NFT | `research/nfts/unicred/` | keep live NFT/rent/unlock authority |
| `positions/xrp-variational.md` | Token | `research/tokens/xrp/` | keep private-position state operational |
| `positions/xrp-bitget-hack-event.md` | Token/event | `research/tokens/xrp/` | move long-form event analysis later; keep if runtime still references it |
| `positions/eth-conditional.md` | Token/derivatives | `research/tokens/eth/` | stored setup remains operational; research can be separated later |
| `positions/flop-close-call.md` | Project/competition | `research/projects/flop-close-call/` | keep active competition rules operational |

## Watchlists

| Current file | Category | Long-form destination | Operational rule |
| --- | --- | --- | --- |
| `watchlists/alchemists-robinhood.md` | Project | `research/projects/alchemists/` | eventually keep only compact watch state in watchlists |
| `watchlists/btc-regime-jasonleo.md` | Token | `research/tokens/btc/` | machine regime model may remain in watchlists |
| `watchlists/famous-token-launch-radar.md` | Monitoring | none required | keep machine radar in watchlists |
| `watchlists/monster-squeeze-v2.1.md` | Token/model | `research/tokens/monster-squeeze/` | frozen machine model remains operational |
| `watchlists/nft-mint-radar.md` | Monitoring/NFT | none required | keep machine radar in watchlists |
| `watchlists/robinhood-fomo-mev.md` | Token/model | `research/tokens/robinhood-fomo-mev/` | compact machine thresholds remain operational |
| `watchlists/saga-squeeze-cycle.md` | Token | `research/tokens/saga/` | separate long-form token thesis from machine state later |

## Frameworks

Current framework files remain in place during monitor-safe migration:
- `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`
- `crypto-300-profit-mission/token_trading_principles.md`
- `crypto-300-profit-mission/meme_trading_principles.md`

Future cleanup can move/copy these into the appropriate research library only after reference checks and a real monitor validation.

## Do not migrate

These are operational/current-state files and should stay where they are:
- `AUTOMATION_RUNTIME.md`
- `MISSION_SPEC.md`
- `RUNBOOK.md`
- `portfolio/current.md`
- `performance/current.md`
- `state/latest.md`
- `health/current.md`
- automatic `runs/` history
