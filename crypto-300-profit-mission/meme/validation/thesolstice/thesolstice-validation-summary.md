# TheSolstice PERSON_PATTERN Historical Validation

Research date: 2026-10-03  
Mission: `$300 → $3000 Mission`  
Module: Meme  
Subject: `TheSolstice / @The__Solstice`  
Production trading: `NO_GO`  
Current research state: `PERSON_PATTERN = OBSERVE_ONLY`  
Final validation result: `NO_VALIDATED_PATTERN`

## A. Executive conclusion

### Bottom line

TheSolstice shows a real and repeated tendency to build positions through multiple buys, and STONK is a strong example of persistent accumulation plus long holding. The available evidence does **not** establish a reusable profitable trend-accumulation PERSON_PATTERN outside STONK.

The decisive counterexample is MARKET. In Fomp's dated public trade window, MARKET shows **22 buys and 0 sells**, with about **$36.4K** of tracked activity. This is even more buy-heavy than STONK's **13 buys and 4 sells** in the same public window. A later Pump profile snapshot shows the MARKET position at about **-$29,118.53 / -95.1%**. Repeated buying and continued commitment therefore fail as standalone positive signals.

EYE and PUMPRPG also do not reproduce the STONK structure:
- EYE: 3 buys and 4 sells in the tracked window, consistent with a short round-trip / trim pattern rather than a long pyramid.
- PUMPRPG: 1 buy and 1 sell, with a later Fomp holding snapshot around `$2.8K` and `-$7.1K` PnL.
- StonkDex is a smaller positive counterexample outside STONK: several buys, one tracked sell, later positive marked PnL. It shows that profitable multi-buy behavior can occur outside STONK, but the currently recoverable sample is too incomplete for replay qualification.

The current Pump profile displays total profit of **$7,473,255.25** and a STONK contribution of **+$7,259,420.10**. On that platform snapshot, STONK represents approximately **97.14%** of displayed profit. The residual after removing STONK is approximately **$213,835.15**, or **2.86%**. These are Pump platform display fields and were **not independently recomputed from the complete raw Solana ledger**.

No valid +1m / +2m / +5m / +15m executable-entry replay can be produced from the currently verifiable public dataset. The public Fomp history is capped and relative-time based, while exact minute-level trade timestamps, pool state, quote path, slippage and liquidity at `T_signal + delay` are missing. Filling those values would require fabrication, so they remain unavailable.

**Result:** keep `OBSERVE_ONLY`.  
**Research qualification:** not passed.  
**Production state:** unchanged, `NO_GO`.

---

## Repository authority checked

Latest Git state observed before this report:
- latest repository commit at retrieval: `8263345c32fdb2875a282ce54146b04fec9caa45`, created `2026-10-03T05:46:44Z`
- `crypto-300-profit-mission/meme/MEME_GPT_MONITOR_SPEC.md`
- `crypto-300-profit-mission/MISSION_SPEC.md`
- `crypto-300-profit-mission/STATUS_SCOPE_2026-10-03.md`
- `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`
- `crypto-300-profit-mission/token_trading_principles.md`
- `crypto-300-profit-mission/meme_trading_principles.md`

Relevant current rules recovered from the repository:
- Meme / tracked-person signals are the current development priority.
- Current source person is Frank.
- PERSON_PATTERN and TOKEN_CONSENSUS are distinct.
- New tracked people remain observation-only until identity and historical/replay qualification are accepted.
- Followability must be measured at the user's delayed executable entry, not copied from the tracked wallet's fill.
- Historical work must preserve timestamp separation and evaluate delayed entry, MFE, MAE, liquidity and false positives.
- Production trading remains `NO_GO`.
- No additional task creation is authorized by current scope.

---

## B. Wallet / identity map

| Item | Result | Evidence grade | Notes |
|---|---|---:|---|
| Public identity | `TheSolstice / @The__Solstice` | Confirmed as public handle | Visible on Fomo/Fomp and other public profiles |
| Solana wallet | `4ugDhHJ8XDXAeABmrNmGffFaLbJb9BkPyiFGVSV9ocwo` | **High confidence, not fully cryptographically confirmed to X identity** | Pump profile URL for this address renders username `The__Solstice`; Vaulted independently says it recovered a Solana wallet ending `ocwo` with 25 position matches; Fomo Wallet Finder secondary export gives the same full address |
| EVM wallet | `0xd1c77a04b87393e98a1220532e72e8f7d0a31c5a` | High confidence, not central to this Solana study | Dutable Fomo Wallet Finder; Vaulted independently reports Robinhood-chain address ending `1c5a` with 6 position matches |
| Earliest public Fomo activity | `2026-03-10` | High confidence, third-party API snapshot | Vaulted says profile is on Fomo since Mar 10, 2026 and had 1,559 trades by Sep 6 |
| Pump profile join date | `2026-04-17` | Platform fact | Pump profile |
| Wallet first-ever Solana activity | **Unable to verify** | — | Full raw-history pagination to genesis was not completed in this run |
| Initial funding source | **Unable to verify** | — | No reliable first-funding transaction recovered |
| Old Solana wallet | **Unconfirmed** | — | No reliable old-wallet mapping recovered |
| Address switch | **Unconfirmed** | — | No evidence sufficient to claim a switch |
| Multiple Solana execution wallets | **Unconfirmed** | — | One Solana wallet is strongly linked; existence of more execution wallets remains unresolved |
| CEX / bridge transfer history | **Unable to verify** | — | Fomp route labels include DFLOW/Jupiter/OKX, but route labels do not prove CEX funding or withdrawal |
| Does all profile history belong to this wallet? | **High confidence but not completely confirmed** | High | 25-position match supports the mapping; the complete 3,000-trade history was not independently mapped to raw signatures |
| Third-party PnL independently chain-recomputed? | **No** | — | Platform/provider snapshots were cross-compared, but a complete raw-ledger PnL reconstruction was not achieved |

### Direct-chain check performed

Alchemy Solana mainnet was queried directly for `4ugDhHJ8XDXAeABmrNmGffFaLbJb9BkPyiFGVSV9ocwo`. Finalized account-involvement signatures were returned. Sampled latest transactions included inbound associated-token-account creation / token transfer activity where another wallet was the signer. Those samples confirm raw-chain account activity around the address but do not establish that the TheSolstice controller signed those specific latest transactions.

Because the earliest signer-controlled transaction and first funding were not recovered, wallet continuity before the public Fomo record remains unresolved.

---

## C. Historical coverage and data completeness

### Profile-level coverage

| Source | Coverage | What it provides |
|---|---|---|
| Vaulted/Fomo API snapshot | 2026-03-10 → 2026-09-06 | 1,559 trades, follower count, 30d/7d PnL, median swap, open-position statistics, wallet-position matching |
| Fomo Wallet Finder secondary export | through 2026-09-30 | ~3.0K lifetime trades, ~$7.2M profile PnL, ~$3.0M volume, full Solana wallet |
| Pump profile | joined 2026-04-17; page crawled last week | current/open-position marks and platform profit fields |
| Fomp detailed trade view | displayed period 2026-08-15 → 2026-09-06 | 38 tokens, 75 buys, 90 sells, ~$234.1K tracked activity; detailed page capped at 150 rows |

### Important completeness issue

Fomp's aggregate says:
- `75 buys`
- `90 sells`
- `$234.1K across 38 tokens`

That is 165 classified buy/sell events.

Its route totals are:
- DFLOW 107
- Jupiter 44
- OKX 15

That totals 166 routed swaps.

The page simultaneously says `Trade history 150`. Therefore the public row-level history is capped and cannot be treated as a complete ledger.

### Coverage required by this validation

- Requested minimum: current confirmed wallet full history, or at least 6 months.
- Achieved at aggregate/profile level: roughly Mar 10 → Sep 30, over six months.
- Achieved at detailed row level: only a capped late-August/early-September window.
- Exact token-level episode count: **unable to compute**.
- Minimum unique token groups in the detailed Fomp aggregate: **38**.
- Exact all-history token count: **unable to verify**.
- Exact all-history swap count: **unable to verify**; secondary Fomo Wallet Finder snapshot reports ~3.0K profile trades as of Sep 30.
- Old wallet discovery: **not completed**.
- Raw-chain PnL reconstruction: **not completed**.
- Minute-level historical executable prices: **not recovered**.

This coverage is enough to reject simplistic signals. It is insufficient to qualify a production-grade PERSON_PATTERN.

---

## D. STONK reconstruction

Canonical mint:
`6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx`

STONK was listed on Aug 5, 2026. Third-party reports relaying Arkham say TheSolstice accumulated about `$80.3K` on launch day around a `$2.73M` market cap. Stalkchain separately reported that by Aug 7 the wallet had accumulated `18.49M STONK` for about `$84.5K`, becoming the second-largest wallet at that time.

The dated Fomp window later shows:
- 13 buys
- 4 sells
- about `$85.3K` tracked STONK activity in that window
- repeated later buy rows while the position was already large
- partial sells while maintaining a large runner

A later Fomp thesis/live snapshot showed multiple additional STONK buys of roughly `$4.8K` to `$9.8K` each, while adjacent platform marks on those rows were positive. Because the UI field semantics are not independently documented here, those adjacent percentages are not promoted into verified “pre-add unrealized PnL” numbers.

The current Pump snapshot shows:
- position: `20.9M STONK`
- marked value: `$7,380,740.48`
- displayed contribution: `+$7,259,420.10`
- displayed ROI: `6,071.6%`
- `Spent $119.6K`
- average entry field: `$5.1M MC`
- current field: `$322.6M MC`

The quantity comparison from Stalkchain's Aug 7 snapshot (`18.49M`) to Pump's current snapshot (`20.9M`) implies roughly **1.13x token quantity growth** after the early accumulation snapshot.

STONK therefore strongly supports:
- persistent holding;
- repeated adds;
- partial profit-taking without full exit;
- continued commitment after a favorable move;
- a large retained runner.

STONK alone does not prove cross-token repeatability.

---

## E. STONK vs MARKET vs EYE vs PUMPRPG

### MARKET

Mint:
`DUZN7M6ezXez9UVrou4N8UEGRkwnbWmXqqZgEKiZCrnN`

Fomp shows:
- 22 buys
- 0 sells
- about `$36.4K` tracked activity

The current Pump snapshot later shows:
- `26.3M MARKET`
- marked value `$1,494.28`
- displayed PnL `-$29,118.53`
- displayed ROI `-95.1%`
- `Spent $30.6K`
- average entry `$1.2M MC`
- current market-cap field `$56.8K`

This is the strongest negative case for the proposed model. Continued commitment occurred and the result was extremely poor.

### EYE

Mint:
`RmtMAYVTTFv2iK9muMrXEoAnSSsZPPgRPbqZCKwNDYk`

Fomp shows:
- 3 buys totaling about `$14.5K`
- 4 sells totaling about `$8.6K`
- about `$23.1K` total tracked activity
- EYE absent from the later current-holdings block in that snapshot

This looks more like rapid entry/trim/exit behavior than a persistent pyramid. Exact realized PnL cannot be recovered from the public row data.

### PUMPRPG

Mint:
`61nBtbHTfxCJikoUQJUizYv2tKSHg2KJ3r9YsdLxpump`

Fomp shows:
- one buy around `$9.8K`
- one sell around `$2.5K`
- later holding mark around `$2.8K`
- displayed holding PnL around `-$7.1K`

This does not reproduce a repeated accumulation pattern.

### Structure comparison

| Feature | STONK | MARKET | EYE | PUMPRPG |
|---|---|---|---|---|
| small initial probe | Unresolved | Unresolved | Unresolved | No evidence |
| repeated buys | **Yes** | **Yes, strongest count** | Limited, 3 | No, 1 |
| adds after confirmed price rise | Supported qualitatively, exact path unresolved | Unresolved | Unresolved | No |
| adds after pullback | Unresolved | Unresolved | Unresolved | No |
| position expansion | **Yes** | **Yes** | Limited | No |
| high buy frequency | **Yes** | **Yes** | Moderate | No |
| long accumulation | **Yes** | Several days | No clear evidence | No |
| partial profit taking | **Yes** | 0 sells in tracked window | **Yes** | One sell |
| runner retained | **Yes** | Position still open later, but failed | No later holding shown | Held remainder in dated Fomp snapshot |
| trend continuation | **Yes** | **Failed eventually** | Unresolved | Failed/weak |
| pattern alignment with STONK | Reference case | Behavioral overlap, outcome contradiction | Low | Low |

---

## F. Hypothesis tests

### Hypothesis A: trend confirmation followed by accumulation

STONK supports the hypothesis qualitatively. MARKET proves that repeated accumulation alone does not identify profitable trend persistence. Exact price movement between MARKET adds was not recovered, so the stronger version requiring favorable price movement before each add remains untested.

Result: **UNVALIDATED**.

### Hypothesis B: winners are pyramided while already profitable

STONK contains strong qualitative evidence. The available dataset lacks a complete cross-token sample of pre-add unrealized PnL.

Result: **SUPPORTED AS A LEAD, NOT VALIDATED**.

### Hypothesis C: hidden trend-persistence filter

Required features:
- volume expansion;
- liquidity expansion;
- market-cap trend;
- holder growth;
- narrative/social momentum.

Exact add-time values were not recovered across the sample.

Result: **NOT TESTABLE TO REQUIRED STANDARD WITH CURRENT DATA**.

### Hypothesis D: losers stop adding quickly

Mixed result:
- PUMPRPG: one buy, one sell, consistent with stopping quickly.
- EYE: three buys and four sells, consistent with relatively quick de-risking.
- MARKET: 22 buys, 0 sells in the tracked window, later about -95.1%.

MARKET directly contradicts the general rule.

Result: **REJECTED AS A GENERAL RULE**.

---

## G. Winner vs loser behavior

| Dimension | Winner evidence | Loser evidence | Current conclusion |
|---|---|---|---|
| Buy count | STONK 13 tracked buys; StonkDex multiple buys | MARKET 22 buys | High buy count is not sufficient |
| Accumulation duration | STONK extended | MARKET several days | Long accumulation is not sufficient |
| Continued commitment | STONK yes | MARKET yes | Not discriminative alone |
| Partial sells | STONK trims and retains runner | EYE/PUMPRPG reduce earlier | Potentially useful, requires full replay |
| Add while profitable | STONK likely / qualitatively supported | MARKET exact pre-add PnL unavailable | Key missing discriminator |
| Market-cap trend at adds | STONK broadly rising | MARKET exact path unknown | Needs exact historical price series |
| Liquidity/volume expansion | Missing | Missing | Cannot validate |
| Stop adding on loser | PUMPRPG supports | MARKET contradicts | General hypothesis fails |

The most promising research direction is not `continued commitment` alone. It would have to combine continued commitment with verified favorable price movement and an external trend-persistence filter. That combined rule has not yet been replayed.

---

## H. STONK exclusion / robustness

Current Pump profile snapshot:

- total displayed profit: `$7,473,255.25`
- STONK displayed contribution: `+$7,259,420.10`
- STONK share: **97.14%**
- residual after STONK: **$213,835.15**
- residual share: **2.86%**

These are platform display values. They are not a chain-recomputed lifetime realized-PnL series.

| Metric | All | Ex-STONK | Ex-Top1 | Ex-Top3 | Ex-largest-theme | Delay1m | Delay2m | Delay5m | Delay15m |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| Pump displayed profit | $7,473,255.25 | $213,835.15 | $213,835.15 | UNAVAILABLE | UNAVAILABLE | N/A | N/A | N/A | N/A |
| STONK concentration | 97.14% | 0% | 0% | UNAVAILABLE | UNAVAILABLE | N/A | N/A | N/A | N/A |
| Realized PnL | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| Win rate | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| Median return | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| Profit factor | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |

Why Ex-Top3 is unavailable: the complete historical contribution ledger and closed-position attribution were not obtained.

---

## I. Delay replay and followability

Required replay:
- `T_signal + 1 minute`
- `T_signal + 2 minutes`
- `T_signal + 5 minutes`
- `T_signal + 15 minutes`

### Status

`NOT_RUN_DUE_TO_SOURCE_GRANULARITY`

Reason:
1. no validated machine `T_signal` exists;
2. public Fomp trade rows use relative-day timestamps and have a 150-row display cap;
3. exact swap timestamps were not recovered for the full sample;
4. pool state, liquidity and route quote at +1/+2/+5/+15m were not recovered;
5. full raw wallet ledger was not normalized into swaps;
6. open episodes require censoring logic.

No positive-expectation claim is made for user-following latency.

---

## J. Candidate signal-time analysis

A naive candidate would be:

```text
first buy
→ repeated buy
→ cumulative exposure grows
→ no major sell
→ signal
```

This candidate is **rejected** because MARKET would likely have triggered it and later showed approximately -95.1% on Pump.

A stronger research candidate would need:

```text
repeated buys
+ position growth
+ no major sell
+ verified favorable price move since first buy
+ add while already profitable
+ persistent liquidity/volume/holder expansion
```

The current data cannot fill those fields across a complete validation sample, so no threshold is emitted and no `T_signal` is declared.

---

## K. PERSON_PATTERN candidates

### Validated patterns

None.

`NO_VALIDATED_PATTERN`

### Rejected / incomplete research leads

1. `repeated_adds_no_sell`
   - rejected as standalone rule;
   - MARKET is a high-quality false positive.

2. `continued_commitment`
   - behavior repeats;
   - profitable expectation is unproven.

3. `trend_accumulation_after_profit`
   - STONK supports it qualitatively;
   - exact pre-add PnL and cross-token replay are missing.

4. `losers_stop_adding`
   - contradicted by MARKET.

No candidate reaches research qualification.

---

## L. Frank comparison

The current repository scope identifies Frank as the current source person. A separate Frank episode/replay dataset was not surfaced in this research retrieval, so no quantitative Frank-vs-TheSolstice performance comparison is invented.

---

## M. Sources and evidence grades

Strong / primary-ish platform or direct-chain sources used in the source research include Pump profile tied directly to the Solana address, official EYE/STONK listing sources, and direct Alchemy Solana queries. High-quality secondary/analytics sources include Vaulted, Fomp, stonk.fyi and Raiden Terminal. Secondary leads such as Fomo Wallet Finder/Stalkchain mirrors were not upgraded to chain-recomputed facts.

---

## Final answer to the research question

The available evidence supports this narrower statement:

> TheSolstice has a repeatable tendency to add repeatedly to selected positions, and STONK is an exceptional profitable example of that behavior.

The evidence does **not** support the stronger required statement:

> repeated trend-confirmed accumulation across multiple independent tokens produces positive expected returns that remain followable after 1/2/5/15 minute delay.

MARKET is the key falsifier for a simple accumulation trigger, STONK dominates current displayed profit, EYE and PUMPRPG do not reproduce the same structure, and the minute-level replay dataset is incomplete.

**Final state: `OBSERVE_ONLY`.**  
**Pattern artifact state: `NO_VALIDATED_PATTERN`.**
