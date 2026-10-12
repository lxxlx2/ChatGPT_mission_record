# BSC Address Model 4 — Stage 5: Full-cursor expansion and six owner-signed first-trade comparators

Date: 2026-10-12 (Bangkok). Frozen scope: 23 EOA wallets × 19 preselected canonical BNB Chain meme-token CAs. Mode: **RESEARCH_ONLY; OBSERVE_ONLY / NO_GO**.

## 1. Measured result, no simulated alpha

The 2026-10-11 baseline and V2 research overlay are retained. V3 now includes `0xd70ce47ec32625420640da206f0b3525c2bec678` after cursor-exhaustion of its 19 CAs. Of 437 wallet/CA combinations:

| Item | Confirmed |
|---|---:|
| Wallets with all 19 CAs both directions fully paginated | **14/23** |
| Complete history cells | **266/437** |
| Complete cells with ERC20 transfers | **55** |
| Complete cells with zero ERC20 transfers | **211** |
| Partial cells with known transfer prefix | **30** |
| Partial cells with no reliable decision | **141** |
| Source-exhaustive quantity-closed wallet/CA cells | **36** |

No zero-transfer cell is automatically a **missed trade**: token launch time, wallet existence/funding, original transaction provenance and all alternative venues are independent requirements.

### The newly completed wallet: D70CE

`0xd70ce47ec32625420640da206f0b3525c2bec678`: **8 inbound** and **74 outbound ERC20 Transfer logs**, with both direction pageKeys exhausted over 19 CAs. Only four selected contracts have movements:

| Token | ERC20 in / out logs | Full-cursor net raw units | Latest balanceOf reconciled |
|---|---:|---:|---|
| 4 | 1 / 31 | 160934 | Yes |
| 币安人生 | 2 / 13 | 0 | Yes |
| 哈基米 | 4 / 29 | 0 | Yes |
| BUBB | 1 / 1 | 0 | Yes |

The eight first-inbound/first-outbound **boundary** transaction probes (two per traded token) all had the wallet as original signer. The **74 outgoing logs cannot be equated to 74 signed sells**, as token fees and multiple movements may produce many events per transaction. No isolated cost/quote/gas PnL is claimed.

## 2. Two high-volume candidates previously hidden by partial pagination

- `0x498528e32b04bdaa73d5c8943a09aeffd15bd99a`, **MARSCOIN**: at least first 56 inbound and 56 outbound original ERC20 events, additional pages unread. Its earliest self-signed buy block is **112441470**, just **10 blocks after earliest sampled Four.meme pre-V2 pool event at 112441460**, and **450 blocks earlier than DDAC's previously confirmed first MARS entry at 112441920**. Two original 0.2 BNB buys were signed in block 112441470 and a third original 0.2 BNB buy in block 112441471; **0.6 BNB total original three-tx msg.value**. Wallet native N−1/N balances show `-400107298960000000` wei on the two-buy block and `-200051672480000000` wei on the third-buy block. The first sampled owner-signed exit at block 112442022 exhibits exact `floor(3% × MARS outgoing)` ERC20 Transfer split and `+399318753578522047` wei on its wallet native block. Because exit and all later trades are not yet isolated, no position profit claimed.
- `0x877af245c61289b24f0c619a4346cdbc68f1aaac`, **龙虾**: first 56 inbound / 56 outbound ERC20 events, still pending further pages. First buyer-signed original 0.14 BNB transaction at block **83636406**, **277 blocks after first sampled V2 pool event 83636129**, and first signed sell block 83636583. Native deltas of those two blocks `-140029684700000000` and `+102756484749829304` wei do not prove full-position PnL.

These wallet-specific first 56-event scans are **prefix-only** and MUST NOT upgrade original 19-CA census completeness.

## 3. Further early-wallet owner-signed boundary evidence

| Wallet | Token | Earliest verified owner-signed entry block | Original native input | Reference gap | First sale status |
| --- | --- | ---: | ---: | --- | --- |
| `0x11a732…` | BOB | 44007594 | 0.139320442060087755 BNB | +22 blocks from first sampled V2 pool | owner-signed; **50% of first buy token quantity** |
| `0xa83b73…` | GIGGLE | 61964958 | 0.5 BNB | +1203 blocks from first sampled V2 pool | owner-signed; **5% of first buy quantity** |
| `0xadffbe…` | 我踏马来了 | 73336282 | 0.06 BNB | +3 blocks later than DDAC verified first IFML buy, **not** a first pool reference | owner-signed at block 73336293; ~50% of first buy |
| `0x0abb84…` | GIGGLE | 61967915 | 0.1 BNB | +4160 blocks from first sampled V2 pool | owner-signed at block 61970077; ~7.69% of first buy |

The 11a BOB two-block native delta sum is `+203378044586670453` wei and a83 GIGGLE is `-66284091661989220` wei. ADFF IFML is `-23030128143168814` wei and 0ABB GIGGLE is `+148764209579754519` wei on their first buy and first sell blocks. **These are not PnLs.** Each first sale is partial relative to initial bought token quantity, and wallet balance may include co-occurring activity and quote assets.

The older `0x5c0c…` CHEEMS first inbound original signer is unreadable from a truncated transaction; first outbound is a signed plain ERC20 transfer (`transfer` selector), which **cannot be assumed to be a market sale**.

## 4. Research ranking, explicitly provisional

For finding true early source buys, prioritize **498528 / MARSCOIN**, **ADFF / IFML**, and **11a732 / BOB** for full transaction sequence, quote receipts, gas, launch-timing and per-order capital; 877AF merits repeated-trade analysis. These priority labels rank **amount of promising evidence to investigate**, not verified realized return, investment skill, or suitability for copying.

A high buy count or highly profitable-looking first sell does not pass strategy validation. The following work remains: remaining **9** wallets' bidirectional cursor exhaustions, 141 incomplete-unknown cells, 30 partially observed cells, all asset quote and gas proceeds, losses and partial exits, chronological eligible-opportunity denominator, and independent lag/slippage holdout backtests.

## 5. Verified and preserved sources

- `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V3_2026-10-12.json` (blob `93a4f7c29cfbeeaf6dce34533a2f71f3f72d81f0`)
- `BSC_MEME_D70CE_FULL_19_CA_BALANCE_AND_SIGNER_PROVENANCE_2026-10-12.json` (blob `61cff967a8d5ef2a7572fe9482ca1b067966fada`)
- `BSC_MEME_498528_MARSCOIN_FIRST_TEN_BLOCK_EARLY_BUYS_AND_TAX_QA_2026-10-12.json` (blob `182d442a74cfbe8fa2af13b2017f63524257120b`)
- `BSC_MEME_ADDRESS_MODEL_4_NEW_EARLY_TRADER_FOUR_WALLET_SIGNER_COMPARATOR_2026-10-12.json` (blob `f146d0061f97ef9cc3314874fd69a5f8a5694648`)
- `BSC_MEME_ADFF_IFML_0ABB_GIGGLE_FIRST_SIGNED_ENTRY_EXIT_2026-10-12.json` (blob `f2e0fb672069490230599292a8feabd764db1887`)
- `BSC_MEME_877AF_19_CA_FULL_CURSOR_2026-10-12.json` (blob `8f6aeb15e863f189717f4ee25dfd5b045a50e8ce`)
- `BSC_MEME_498528_19_CA_CURSOR_V1_2026-10-12.json` (blob `6d29e760df30553e6518baf2fe67790924f5eda5`)
- `BSC_MEME_23_EOA_REMAINING_WALLETS_TRIAGE_B01_2026-10-12.json` (blob `1fb23b8c18baa0faa65dc82d949dd0c2ce1535fb`)
- `BSC_MEME_23_EOA_REMAINING_WALLETS_TRIAGE_B02_2026-10-12.json` (blob `be2dc6e37a798f20e798f2cfd504c109f3c38af0`)

The persistent candidate queue has only evidence pointers and status updates; no trading thresholds, live monitors, wallets, execution configurations or automation schedules changed. **NO_GO**.
