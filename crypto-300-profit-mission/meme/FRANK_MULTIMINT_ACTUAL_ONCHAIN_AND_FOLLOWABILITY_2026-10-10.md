# Frank multi-mint actual onchain rounds and delayed-copy research — 2026-10-10

**Research state: completed for six scoped, known Solana-mint lot examples; full-person replay and executable delayed-follow validation remain UNVERIFIED.** All work in Draft PR #29 review branch, no existing production service, Gmail, wallet, alerts, main or automation changed. All numbers below distinguish raw user-visible wallet/quote deltas from hypothetical follower performance. User provided no commands; public GitHub runner performed read-only requests without paid Alchemy or private Mac credentials.

## 1. Frozen population and evidence selection (no winner-only cherry-picking)

Archived study `meme/evidence/frank-trade-coverage-sol-usdt-complex-2026-10-04.json` (hash-verified existing raw-snapshot research) records **6,874 unique historical signatures**, **653 recovered/current active trades** under `M3`, **22 ACCUMULATION plus 10 MULTIPLE events** on **18 distinct Solana mints** in 2026-09-03–09-30 available-verified-subset history. `M3` is a historical **review/recovery** replay, not 32 real pushed alerts, untouched OOS or a wallet-lifetime full scan. Signal events can repeat within one token/episode. Other known Frank wallet/address ownership still THIRD_PARTY_ATTRIBUTED.

The independent chain follow-through used **the first 8 mints ordered by earliest archived ACCUMULATION trigger**, not tokens handpicked for returns, with max **34 public Solana RPC requests**, no retry or paid key. Actual run https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37967832133 completed 34 requests and stopped at explicit budget, after fully checking 7 of 8 *trigger transaction + ATA signature inventories*. Four of these had **all post-trigger transactions on that ONE known ATA decoded** (MukLD, 8K5, E4Ap, PerPs); 3 (STONK, HcRL, 4MMQ) required bounded time-spaced samples only and cannot support full lot PnL; eighth (CbyTN) stopped before RPC for it. Full-person/multi-ATA/existing prior closed accounts remains UNKNOWN. The complete page of public ATA signatures alone does not prove all Frank-person trading addresses.

Two additional historically relevant independently confirmed rounds were already studied: (a) qualifying **4K1m…meta** (Sep 23 Bangkok) and (b) non-ACC **TWEETCRAFT** (Oct 8–9 Bangkok). These two were outside the chronological-eight subset, intentionally separated from the strict eight-case cohort to avoid misrepresenting sampling.

## 2. Six source-grounded per-token round-trip wallet-quote cases

**Buy cost attribution**: For MukLD/8K5/E4Ap/PerPs, full *episode-level* gross USDC quote spent at the archived M3 ACC trigger is the buy-side cost source. The trigger transaction was separately checked root-signed and net USDC-decreasing, but this new investigation did **not independently rehydrate every pre-trigger buy**. The raw 6,874-sig study had previously hash-verified those active-buy prefixes; any source model misattribution, additional historic accounts, native SOL, taxes or offchain costs remains outside the current PnL calculation. For 4K1m and TWEETCRAFT, exact buy transactions were independently inspected onchain in this conversation. All listed sells were independently matched to root-owned token outflows + USDC receipts and DEX swap instructions.

| Token, exact mint prefix | Bangkok trigger / first demonstrated buy | Bangkok last active sale | Archived/chain buy-side USDC | Verified root-signed sale USDC net sum | Indicative net USDC margin | Return on gross quote | Final evidence |
|---|---|---|---:|---:|---:|---:|---|
| `PerPsCe2…` | Sep 12 23:37:15 | Sep 14 06:58:00 | 27,000.000000 | 61,919.993902 | **+34,919.993902** | **+129.333311%** | Both exit txs opcode/owner-delta confirmed; known ATA complete |
| `MukLDtJ8…` | Sep 6 04:00:55 | Sep 6 09:54:40 | 42,500.000000 | 50,952.838215 | **+8,452.838215** | **+19.889031%** | Both exits independently verified; bought lot all sold; later 33.586031-token passive receipt |
| `HzYCHqAN…` TWEETCRAFT | Oct 8 08:46:16 | Oct 9 08:26:47 | 6,715.734492 | 7,031.556770 | **+315.822278** | **+4.702721%** | Independent root buy + root sell, DEX opcode and ATA transfer confirmed |
| `8K5X85PA…` | Sep 8 09:42:17 | Sep 8 11:27:36 | 28,598.056732 | 28,582.603719 | **−15.453013** | **−0.054035%** | Both exits independently verified; original lot sold; later unsigned ~327,203.717034-token receipt |
| `E4Ap4icM…` | Sep 11 10:24:02 | Sep 11 10:47:54 | 50,000.000000 | 40,912.316439 | **−9,087.683561** | **−18.175367%** | Both exits independent; first is Jupiter SharedAccountsRouteV2 → official Raydium CLMM SwapV2; second is Meteora DLMM Swap2 |
| `4K1m7gAM…` | Sep 23 00:12:41 / 00:12:49 | Sep 23 03:44:02 | 25,000.000000 | 15,524.767593 | **−9,475.232407** | **−37.900930%** | Exact two root-signed buys 8 seconds apart + exact root-signed full DAMM v2 Swap2 exit, single ATA complete |

Precise trade mints:
- PerPs `PerPsCe2SJ7Q25CN4R5TTX4fmBdmknE2hQmqCt96fHL`
- MukLD `MukLDtJ8Cx9DxLbeyLRSWPSposTMWuwHANbuaudpump`
- TWEETCRAFT `HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy`
- 8K5 `8K5X85PAJHAAVSvYaAzgVPPAPsqqHmvx16ZyBiscYF8L`
- E4Ap `E4Ap4icMLwKot8rkkTbq5JkS5kZxt5XCE3yfxbzYBjHx`
- 4K1m `4K1m7gAMDKzrxQn68yuZAd767w57Fw7Ykw69dG3umeta`

The 4K1m UTC Sep 22 evening = **Bangkok Sep 23**; do not accidentally count its September UTC and Bangkok dates as two episodes. In all six observed active-sale cases, summed token sold for the specific known episode matches the M3 observed position lot (or independently verified purchase lot). MukLD and 8K5 later received additional *non-root-signed* small token credits, so **the whole wallet's later balance cannot be declared exactly zero**. These passive receipts are not new buys, and are not treated as gains, cost basis or discretionary exit.

## 3. Independent sale opcodes and precise validation limitations

Public finalized transaction calls from *separate GitHub Actions jobs*, with signers, quote/target owner token deltas, original deployed DEX program ID + raw Anchor instructions, and log-program binding:

- https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37968282422 — **7/8** specified root-signed exit txs passed exact DEX opcode+log tests: MukLD 2, 8K5 2, PerPs 2, E4Ap second 1. E4Ap first returned `UNVERIFIED` **solely because** this initial audit's approved DEX set excluded Raydium CLMM/Jupiter. That failure was never hidden or counted as a clean auto pass.
- https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37968750708 — E4Ap first exit `2aemk5Ho...` independently identified **Jupiter `JUP6...` SharedAccountsRouteV2** (raw Anchor `d19853937cfed8e9`) invoking official **Raydium CLMM `CAMMCzo5...` SwapV2** (raw Anchor `2b04ed0b1ac91e62`), with root signed target token **−1,101,462.225622394** and USDC net **+20,696.377193**, successful balanced log. Final `CONFIRMED_JUPITER_RAYDIUM_CLMM_EXIT` was TRUE. Official Raydium program address verified at `raydium-io/raydium-library/Raydium.toml` and SwapV2 official code `raydium-io/raydium-clmm/programs/amm/src/instructions/swap_v2.rs`. Thus **all 8/8 exit signatures are now supported by instruction-level evidence**, not by a broad inference from program presence alone.
- https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37967163318 and https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37967581454 — 4K1m independently confirmed 15,000 + 10,000 USDC buys 8 seconds apart, then 15,524.767593 USDC net returned while exact 156,402.214732 mint lot was debited via **checked and unchecked SPL transfers together** and actual Meteora DAMM v2 `Swap2` executed.
- https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37964537094 — TWEETCRAFT confirmed Pump AMM `Sell` and Meteora DLMM `Swap2` instructions, exact wallet flows; first reviewed in `FRANK_TWEETCRAFT_ROOT_SWAP_EVIDENCE_20261009.md`.

These are **identified onchain trading activities attributed to the fixed public wallet**, not an independent cryptographic assertion about the real-world Frank persona. USDC net changes include visible routed USDC transfers but do not equal tax/native SOL/multiwallet-adjusted total PnL; values in this table are `CONDITIONAL_EPISODE_NET_USDC`, not person lifetime return.

## 4. Quantitative winner-concentration / repeatability diagnostic

For these **six selected/reconstructable** cases only:
- **3 positive and 3 negative** wallet-quote outcome examples.
- Combined archived buy gross quote = **179,813.791224 USDC**; sum of six observed conditional quote-net deltas = **+25,110.285414 USDC**. The sum does NOT imply $179k of capital was concurrently required, a 30-day profit rate, or $300 follower performance.
- Largest winner **PerPs +34,919.993902 USDC** is **139.1% of the six-case combined NET result** (not 139.1% of all profitable trades' gross gains). It dominates the combined result. Without it, the other five sum **−9,809.708488 USDC**.
- Arithmetic mean of six individual percentage returns = **+16.299122%**, inflated by PerPs. Without PerPs, five-case equal-weight average becomes **−6.307716%**. Neither mean is an estimator of out-of-sample ROI or a signal to trade.
- Median of the six percentages = **+2.324343%**, heavily dependent on sample composition.
- The **4K1m** episode actually passes archived frozen ACCUMULATION's >=2 active buys / >=25,000 USDC in <=60m, and later a historical `MULTIPLE` observation at Sep 23 01:29 Bangkok, but its realized wallet USDC exit margin is **−37.900930%**. Accumulation cannot be equated with future positive return; post-MULT delayed-copy price at market execution remains unmeasured.
- **E4Ap** had a ~24-minute closed lot and lost ~18%. This case only had archived ACCUMULATION, not independently a formal MULTIPLE; don't assume a follower would have bought at the first ACC trigger.
- **TWEETCRAFT** had one active buy <25k and **did not meet ACCUMULATION**; it is an extra negative control for model eligibility even though the wallet profited.

The sample is **outcome/availability-conditioned**, not random or holdout: four early signal mints with few after-trigger signatures, plus one explicit 4K1m alert example and separately investigated TWEETCRAFT. Other hundreds of transactions, other account paths and many historical signal episodes are not reduced to complete lifetime PnL. Do NOT project the 3/6 win fraction or +25,110 USDC to Frank's entire 30-day history.

## 5. Lagged copying and frozen release decision

A separate public GeckoTerminal five-minute **pool-close, not executable quote**, one-shot probe sampled the earliest three of 18 historically signaled mints before public HTTP429 stopped further collection (job https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37966679082). For the 3 priced mints, proxy 5m-delayed/24h-trigger-horizon price returns were **+2.910526%, +53.344658%, +10.503932%**, while immediate 1h horizon returned two negative outcomes. Three is far too few to generalize; the sample is time-ordered and censored by rate limit, not random. Price is a later Kline close from the **first currently API-ranked pool that existed before trigger**; current pool ranking creates hindsight selection bias, and 5-minute candle close shifts the nominal execution time. No $300 historical quote, execution failure, price impact, slippage, fees or user follow latency is verified.

A second independent price-source attempt through free DefiLlama public `coins.llama.fi/batchHistorical` returned **HTTP 404** (job https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/37966976103); **no 18-mint external corroboration** was thereby obtained. Do not pretend it was successful; no source response was fabricated. Tweetcraft's separate *two-pool* 5m and 1m lag proxy results remain sensitive to bar granularity (see `FRANK_TWEETCRAFT_DELAYED_FOLLOW_CHECK_2026-10-10.md`), often negative for 5m/15m follower delay. A qualified signal's timestamp need not equal the time the follower actually receives an actionable MULTIPLE/BUY event. **Market-price proxy results do not establish profitable delayed following**.

Frozen live `ACCUMULATION` gate in `MISSION_SPEC.md` is >=2 independently active buys within 60m and >=25k direct USDC; formal downstream MULTIPLE requires persistence/inventory/distribution/HFT checks. Do not change those rules because a winner looks profitable. No evidence here establishes robust, outlier-excluded, market-executable positive alpha across multiple independently sampled profitable loss cases. Therefore:
- `OBSERVED_SOLANA_ROOT_DEX_ROUNDS`: MULTIPLE, with six bounded numeric lot examples and historical M3 multi-mint leads.
- `FULL_FRANK_PERSON_TRADE_COVERAGE`: **UNVERIFIED**.
- `REPEATABLE_ACCUMULATION_PERSON_PATTERN`: **NOT_VALIDATED / OBSERVE_ONLY**.
- `DELAYED_COPY_$300_EXECUTABLE_ROI`: **UNVERIFIED**.
- `PRODUCTION_TRADING`: **NO_GO**. Existing notifications / email / LaunchAgents / dashboard / main repo untouched.
- **No Mac command requested** and **no new recurring monitor**. Public one-shot research workflow definitions used for this audit should be removed from the final PR tree after saving evidence; their original GitHub Actions run receipts and commit history remain accessible.

## Source and reproducibility

Stored upstream actual chain and price probe runs, not assistant-invented successes, are linked above. Source 18-mint universe and program freeze in repository archived study; eight-token deterministic public RPC helper `local-agent/scripts/audit_frank_multimint_lifecycle_public.py` with 34-call cap and no retries; separate public, read-only OHLCV helper `local-agent/scripts/audit_frank_historical_signal_followability.py` with 36-public-request cap and 5s+ pacing. Both returned actual partial or complete results as indicated, without production effects. Shared USD/USDC display assumes one USDC approximately $1 only for the user-friendly labels; all calculations are directly based on raw USDC token deltas, not a measured USDC/USD FX observation.

**Research complete within its explicit evidence scope; global forecast/replay completeness not supported.** No request for user commands or screenshots. Do not silently reinterpret `NOT_VALIDATED` as proven unprofitable Frank trading in general.
