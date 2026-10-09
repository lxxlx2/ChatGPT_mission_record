# Frank Solana historical root-wallet evidence: 6 observed closed lots, outlier test and delayed-copy gate

**Date:** 2026-10-10 Bangkok. **Research-only / Draft PR #29 / live production NO_GO.**

## Final finding

Six **purposively selected, non-random, historically observable** Solana mint lots have demonstrable wallet USDC investment, sell proceeds and exits of their original observed token quantity. They are **not all of Frank's trades**, are not proof of full wallet lifetime coverage and are not a representative statistical sample. Most were chosen among previously frozen V1/M3 qualifying ACCUMULATION signals, with one later TWEETCRAFT negative control which does NOT qualify. An onchain root-address signer is cryptographically demonstrable; the mapping from that address to the offchain profile "Frank" is third-party attribution rather than signed identity proof.

**Numerical audit on observed wallet USDC net flows**: total capital spent across the six selected lots = **179,813.791224 USDC**; proceeds = **204,924.076638 USDC**; observed aggregate difference = **+25,110.285414 USDC** (**+13.964605% of summed spent notional**, not a sequential portfolio return). 3 positive / 3 negative. Top single winning lot `PerPsCe2...` yields **+34,919.993902 USDC**, greater than the whole six-lot net gain. **Exclude the top winner: remaining five net -9,809.708488 USDC**, **-6.419387%** of their summed 152,813.791224 USDC purchase notional. Thus extreme winner concentration is confirmed *for this selected six-lot subset*, NOT population-wide failure or a claim Frank has no skill. The positive sample mean or win rate must not be extrapolated to $300 copy trades.

## Ledger and cross-chain-safe execution evidence

All timestamps below are **Asia/Bangkok**, all spends/proceeds based on **root-owner USDC token-account transaction net deltas**, not DEX displayed prices. The lot's original token quantity exited in confirmed root-authorized DEX transactions; some token accounts subsequently received small unsigned third-party token receipts, which are **not** authorized repeat BUYs. Historical source M3 has `6874` verified raw signatures from a bounded Sep 03–Sep 30 interval, `653 ACTIVE`, `22 ACC`, `10 MULT`, `32` signaling observations on **18 distinct accumulation-signal mints**. Not 32 independently profitable opportunities, not complete offchain person history.

| Exact Solana mint prefix | Signal/buy timestamp (BKK) | Last exit (BKK) | Wallet USDC spent | Wallet USDC received | Net difference | Gross-on-USDC ROI |
|---|---|---|---:|---:|---:|---:|
| `MukLDtJ8…` | Sep 06 04:00:55 | Sep 06 09:54:40 | 42,500.000000 | 50,952.838215 | **+8,452.838215** | +19.889031% |
| `8K5X85PA…` | Sep 08 09:42:17 | Sep 08 11:27:36 | 28,598.056732 | 28,582.603719 | **-15.453013** | -0.054035% |
| `E4Ap4icM…` | Sep 11 10:24:02 | Sep 11 10:47:54 | 50,000.000000 | 40,912.316439 | **-9,087.683561** | -18.175367% |
| `PerPsCe2…` | Sep 12 23:37:15 | Sep 14 06:58:00 | 27,000.000000 | 61,919.993902 | **+34,919.993902** | +129.333311% |
| `4K1m7gAM…` | Sep 23 00:12:49 | Sep 23 03:44:02 | 25,000.000000 | 15,524.767593 | **-9,475.232407** | -37.900930% |
| `HzYCHqAN…` TWEETCRAFT | Oct 08 08:46:16 | Oct 09 08:26:47 | 6,715.734492 | 7,031.556770 | **+315.822278** | +4.702721% |

This ledger **does not represent total person-wide realized USD P&L**: native SOL gas/rent, potentially separate wallet funding and offchain costs/taxes have not been comprehensively reconstructed; price liquidity/executability for a $300 follower is not established. For 5 older cases, BUY lot costs and signal prefix are grounded in the *frozen historical M3 evidence*, with root-signed triggering BUY additionally re-observed publicly for 4 of them, while `4K1m` has both root-signed buys re-fetched and `TWEETCRAFT` has strict independent BUY instruction proof. Never silently promote this limited re-observation into full onchain independent recheck of every earlier fill.

**Onchain exits verified**:
- `MukLDt` has 2 root-signed SELLs, original token quantity split exactly in half, Pump AMM `Sell` + Meteora DLMM `Swap2` raw opcode and matching bound logs. Three post-trigger token-account signatures fully decoded; a later unsigned token receipt is not a new owner BUY.
- `8K5X` has 2 root-signed exits, Meteora DLMM `Swap` raw opcode bound to its instruction log. A later unsigned token receipt does not undo the original lot's exit.
- `E4Ap` has 2 root-signed exits. First uses **Jupiter V6 `SharedAccountsRouteV2` → Raydium CLMM `SwapV2`**, NOT Meteora. Initially missed by a restricted router allowlist, now **independently confirmed** on 2026-10-10 by raw Anchor discriminators (`d19853937cfed8e9`, `2b04ed0b1ac91e62`), exact source ATA outflow `1101462225622394` raw tokens, root sign, successful tx, valid nested program logs and USDC owner net `+20696377193` raw. The second exit has Meteora DLMM `Swap2`. This distinction is **research classifier coverage evidence**, NOT authorization to edit production allowlists.
- `PerPsCe2` has 2 root-signed exits with Meteora DAMM v2 `Swap2` and DLMM `Swap` bound raw opcodes.
- `4K1m` has **two** root-signed USDC BUYs 15,000 + 10,000, 8 seconds apart (2026-09-23 **Bangkok**, UTC date is Sep 22), then one full-sized root-signed Meteora DAMM v2 `Swap2` exit after ~3h31m. This passes the **frozen ACCUMULATION threshold** while losing **37.900930%** of transaction-net quote in the entire observed lot; no look-ahead was used to decide entry.
- `TWEETCRAFT` has 1 confirmed DFlow/Meteora DLMM/Token-2022 BUY and 1 confirmed Pump AMM `Sell` + DLMM `Swap2` SELL, original lot closed after 23h40m31s. As a **single** 6,715.734492 USDC BUY it fails both frozen ACCUMULATION count and notional gates.

**Evidence run references, no private keys or Mac commands**:
- Frozen historical data: `meme/evidence/frank-trade-coverage-sol-usdt-complex-2026-10-04.json`, originally 6,874 raw-hash-verified.
- Eight-mint publicly queried ATA history: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37967832133 (four known ATA accounts complete, three only sampled, last stopped at hard 34 RPC cap; not fabricated complete).
- First seven of eight other root-exit opcode pair checks: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37968282422.
- `E4Ap` **first** Jupiter/Raydium exact opcode pair: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37977057963. It resolved the sole whitelist-incomplete exit from prior workflow. The exact token account has separate checked and unchecked transfer handling; source ATA was reconciled.
- `4K1m` two actual BUYs: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37967163318; sole full SELL: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37967581454.
- TWEETCRAFT sale: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37964537094; full buy/exit details in `meme/FRANK_TWEETCRAFT_ROOT_SWAP_EVIDENCE_20261009.md`.
- This run does **not** consider RH/EVM Relay PAYs as SOL-mint fills; only exact Solana SPL token mints.

## Delayed-followability: market history results, not actual execution backtest

A single public GeckoTerminal 5m OHLCV retrospective sampled **18 fixed signal-mint population entries**; the external provider returned HTTP 429 on the **7th HTTP attempt**, with **three mint-pool historical price series recovered and 15 missing**. Full research run: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37966679082. These three examples were `MukLDt`, `STONK`, and `HcRL...` with different subsequent spot-price trajectories.

Across just those **n=3**, after a 5-minute delayed entry, a **1h after signal** 5m-bar-close price proxy had 1 positive/2 negative, median **-15.677455%**; at **6h after signal** 2 positive/1 negative, median **+23.110932%**; at **24h after signal** 3 positive/0 negative, median **+10.503932%**. A 15-minute delayed entry gave 1h median -21.298263% (1 positive/2 negative) and 24h median +5.843537% (2 positive/1 negative). These different horizons illustrate that **exit timing changes sign and summary**, but do NOT prove an edge: prices are future candle CLOSES selected with a lookahead bounded by up to five-minute bars and a 15-minute matching window, pool choice is based on current API ranking, no execution depth/impact/spread/router quote fees are reconstructed. Holding blindly for 24h also fails to reflect Frank's actual dynamic exits. No realized $300 executable follower net returns are available.

A separate DefiLlama `/batchHistorical` batch attempt returned **HTTP 404**, not price data: https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37966976103. Its failure cannot be papered over by assuming token prices. TWEETCRAFT's two-pool 5m and 1m historical probes separately show unfavorable 5m/15m delay proxies, but with resolution sensitivity; see `FRANK_TWEETCRAFT_DELAYED_FOLLOW_CHECK_2026-10-10.md`.

**Therefore the original user target — repeatably profitable, sufficiently delayed, $300 executable meme following — is `NOT_VALIDATED`**, rather than a positive signal or a model failure proven by a small cherry-picked portfolio. Coverage for **12 of 18 accumulation mint signals' full lot economics** remains not analyzed here and more historical market data are missing. No winner-concentration-removed OOS causal executable portfolio test could honestly be completed with this source coverage. Explicitly differentiate historic wallet P&L anecdotes from a trading-system backtest.

## Decision and permanent boundaries

- **Question: Did this wallet ever conduct repeat buying?** YES: `4K1m` two verified USDC buys in eight seconds; archival M3 provides broader 18-mint signal evidence. This is not evidence that all such patterns are profitable.
- **Question: Does the six-episode wallet USDC sample stay positive after removing its largest winner?** NO: `-9809.708488` USDC for the other five; winner concentration is material.
- **Question: Is person-wide trade coverage or identity verified?** NO; root signed transactions are not signed offchain handle attestation; 8-mint scan partially covers named ATAs, 6,874 prior verified signatures only a bounded historical subset.
- **Question: Have we validated a 5m/15m/30m/60m follower on $300 executable liquidity with realistic fees and strong OOS/holdout coverage?** NO. Three price-proxy mints out of 18 after 429, no historical executable router quotes, missing costs and exit policy.
- **Frozen accumulation policy** (do not relax retrospectively): `>=2` ACTIVE BUYs `<=60m` and cumulative `>=25,000 USDC`; Path C single-large-BUY excluded. HFT/sticky, inventory, persistence and hourly MULTIPLE gates remain unchanged.
- **Permanent status**: `PERSON_PATTERN=OBSERVE_ONLY`, `TRADE_SIGNAL_ELIGIBLE=NO`, `PRODUCTION_TRADING=NO_GO`, `FULL_PERSON_PNL=UNVERIFIED`. No new monitoring, background automation, wallet interaction, mail, production config, live replay or PR/main merge.

Audit-friendly structured observations: `meme/evidence/frank-six-observed-roundtrips-2026-10-10.json`. Individual RPC raw result lines remain in linked GitHub Actions run logs, available under their retention windows. The report is a **finished bounded historical assessment**, not a promise that absent data or token prices were somehow recovered.
