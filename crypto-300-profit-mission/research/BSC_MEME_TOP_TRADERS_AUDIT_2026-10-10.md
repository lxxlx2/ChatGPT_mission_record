# BSC Meme Top-Traders Cross-Token Audit — 2026-10-10

Research-only. Scope: the **18 previously identified** BSC native / BSC narrative Meme tokens considered for Binance Alpha, Futures or Spot in 2025–2026. This is a **candidate universe, not an exhaustive Binance launch universe**.

PRODUCTION_TRADING=NO_GO; PERSON_PATTERN=OBSERVE_ONLY; no new alerts/automation, no live validation, no portfolio actions.

## On-chain findings so far

Primary detailed raw evidence and tx links: [binance-bsc-meme-cross-token-v1-2026-10-10.md](binance-bsc-meme-cross-token-v1-2026-10-10.md).

| Wallet | Sample tokens closed profitable | Approx total PnL (BNB) | Recency / qualification |
| --- | --- | ---: | --- |
| `0xd70ce47ec32625420640da206f0b3525c2bec678` | 4, 币安人生, 哈基米 (3/3 selected) | +12.3027 | Last documented token outgoing Dec 24, 2025; STALE |
| `0x57c98bc732f0e9ed7156d21f74c17bee4bb0cbf4` | 币安人生, 哈基米 (2/2 selected) | +0.7303 | Last documented token outgoing Dec 19, 2025; STALE |
| `0xe54bdcaff91ed27e53a19bb1203b10bc5e2dc568` | 币安人生, 哈基米 (2/2 selected) | +5.8701 | Latest token outgoing Aug 7, 2026; native transfer Sep 15; no confirmed Meme swap in most recent 30d |
| `0x239e74bfbd02d71cdc70fecc2d505dc13acfb337` | 我踏马来了, 龙虾 (2/2 selected) | +0.2965 | Additional 2026 Meme trades include 1 profit and 2 losses; combined 5 selected positions +0.2593 BNB. Last documented true Meme swap Sep 4, 2026, native transfer Sep 18 |

**NOT full-history win rate; NOT proven high-PnL top-ranked wallets.** PnL is estimated from wallet's BNB balance delta for tx-containing blocks, validated against token send/receive and tx signer, but not against every internal accounting movement / non-BNB quote asset.

### Proven wallet-wallet link, not identification

- 0x57c98 -> 0xd70ce: 5 BNB, BscScan tx [outbound](https://bscscan.com/tx/0xb5e153902bedc8246633c476525b7c1f5bac843692efa16fdfa9a5937ce695b2).
- 0xd70ce -> 0x57c98: 5 BNB, BscScan tx [return](https://bscscan.com/tx/0x49260f6dd65211c5373d77569234276936ed1bf632bae662d0e5617675c65585).
- Both have funding flows from 0x66fa07aae14e110013fb1a8835413ea77fe1b5c6 (the funder is high volume) and 0x5d146231bbb42c2289a827d5c18e13d12e1c39d1. Shared funders can be custodians or a bot disperser. Identity/common control **UNVERIFIED**.

## Coverage matrix

| Layer | Status | Limitation |
|---|---|---|
| 18 ERC-20 identities | COMPLETE for selected 18 | Binance Alpha universe not exhaustive |
| 18 Pancake V2/BNB pair addresses and first observed outgoing transfers | COMPLETE for selected 18 | Does NOT establish earliest trade across all DEX/launchpads |
| First and latest 10 V2-pool outgoing transfer rows per token | SAMPLED 18/18 | Not complete history / not profit ranking |
| All-time Top 100 realized-profit wallets x 18 tokens | NOT COLLECTED | Connected session has no callable GMGN/Birdeye authenticated top-trader API; read-only public key exists for GMGN testing |
| Historical profit and loss for ALL trades in each candidate wallet | NOT COMPLETE | Wallet-level all-chain routes, sold and lost tokens need full index |
| Shared funding / common control | PARTIAL | Direct transfer link confirmed for two wallets only; actor inference unconfirmed |
| True <=30d Meme swap on recurring profitable candidates | NOT CONFIRMED | Native activity ≠ Meme swap; target candidate profits mostly older |
| 5/15/30m delayed follow profitability | NOT VERIFIED | No executable signal, no delay replay data |

## Critical primary-source warning: 2026 牛来

GMGN's own English research article based on August 19, 2026 reported **19 of the top-100-by-profit 牛来 traders had zero direct buys**, having received inventory by transfers; 65/70 earliest buyers had sold out. A wallet which gets transferred tokens and sells them is NOT a valid zero-cost supertrader. Exact BSC CA `0xbeea1d618e533a387d941f58a7d4c9b7bd377777`. Their article also shows token creation Aug 13 whereas the audited V2/BNB pair first outgoing transfer occurs Aug 16, demonstrating launchpad-stage history is missing in a V2-only approach.

Source: https://gmgn.ai/blog/what-to-check-after-finding-a-trending-memecoin/ (English, GMGN first-party).

## Read-only Top Traders collector committed

Script: [bsc_meme_top_traders_readonly.py](bsc_meme_top_traders_readonly.py). It is a **manual one-shot research tool**, not a scheduler, bot, swap application or production trading component.

Official upstream documentation:
- https://github.com/GMGNAI/gmgn-skills/blob/main/docs/cli-usage.md
- https://github.com/GMGNAI/gmgn-skills/blob/main/skills/gmgn-token/SKILL.md

Prerequisite: official `gmgn-cli` on an Internet-connected computer. GMGN documents public read-only test key `gmgn_solbscbaseethmonadtron`, while substantive use may require a personal key. No private key, trading key or wallet authorization needed.

```bash
# Read-only, once, no scheduled jobs. Do not run inside production pipeline.
npm install -g gmgn-cli
python3 crypto-300-profit-mission/research/bsc_meme_top_traders_readonly.py --mode both --root /tmp/bsc_meme_top100
```

Produces raw responses under `raw/` for 18 x 2 ranking sorts (profit and sell volume), and:
- `analysis/coverage.csv`
- `analysis/token_trader_samples.csv`
- `analysis/cross_token_wallets.csv`
- `analysis/summary.json`

The collector does **not** verify GMGN market rankings as fact: provider PnL is **CANDIDATE / NEEDS_ONCHAIN_VERIFICATION**. Both `profit` (which the vendor's response field describes as realized + unrealized) and `realized_profit` are preserved independently. Excludes zero-direct-buys and transfer-in-cost-unknown from provisional success. Never attribute multi-user router address profits to single wallet.

If the CLI is unavailable, this file was **not executed against live GMGN** during creation. Do not claim 1,800 top wallets or any actual ranking until the real, time-stamped output is collected.

## Next true-completion gate

1. Collect 18 x top-100 vendor exports, preserving provider timestamp. Verify exact CA per row; include fully exited wallets and don't use holder ranking as trader PnL.
2. Reconstruct all-venue entry/exit via Four.meme, Pancake V2/V3, aggregator and quote assets. Verify claimed realized profit and sale receipts; exclude transfer-ins, LPs, CEX/bot routers.
3. Cluster only on noncustodial funding, repeated bilateral flows and timing; distinguish person from shared service.
4. Audit full wallet loss history, recent genuine buys/sells (30d), followable holding times and 5/15/30 minute delayed fills with fees/slippage; out-of-sample validate. No go until gates pass.
