# Address Analysis 4 | DDAC MARSCOIN 16/16 upstream route closure

Date: 2026-10-12, Asia/Bangkok  
Wallet: `0xddac928a240bdace3994c2cc0783d4e29a002127`  
Status: **HISTORICAL RESEARCH / OBSERVE_ONLY / NO_GO**

## Evidence-based result

The previously open **four** SPCXB/MARSCOIN owner-signed upstream routes have now been reconstructed with exact same-transaction ERC20 Transfer joins on BNB Chain. Original transaction signers and router targets were read directly, and all four historical native wallet balance changes are retained exactly.

Across the frozen **16** SPCXB/MARSCOIN owner pool actions:

| Route classification | Actions | Validation |
| --- | ---: | --- |
| USDT/SPCXB Pancake V3 via known 0x977D / 0x51A fee-tier pools | 13 | Earlier 12 exact two-pool Swap joins plus one newly recovered exact USDT input and SPCXB output Transfer pair |
| WBNB/SPCXB Pancake V3 0x66faad, fee=2500 ppm | 2 | Direct original V3 Swap topic 0x19b472... and matching ERC20 quote transfers |
| SPCXB → USDT through Uniswap V4 PoolManager 0x28e2ea, then USDT → WBNB Pancake V3 0x172fcd | 1 | Exact same-hash five-leg ERC20 transfer reconciliation, but V4 Swap PoolId is not yet independently decoded |
| Unassigned upstream route identity | **0** | No remaining path identity gap for the frozen 16 actions |

This is **route identity completion**, not an independently completed lifetime profitable-trade reconstruction.

### Newly resolved transactions

| Block | Side | Directly observed route | Gross quote/input | Wallet BNB block delta | Implied gasUsed under exact 1% model |
| --- | --- | --- | ---: | ---: | ---: |
| 112643175 | SELL | SPCXB → V4 → USDT → V3 → WBNB | 0.529317 WBNB | +0.523957 | 552589 |
| 112964866 | BUY | BNB → WBNB → USDT → SPCXB | 1.000000 BNB input | -1.000060 | 504957 |
| 115522575 | SELL | SPCXB → WBNB V3 | 0.098134 WBNB | +0.097103 | 408319 |
| 119938551 | SELL | SPCXB → WBNB V3 | 0.040884 WBNB | +0.040427 | 401351 |

- Block 112643175: 2.690421549396182003 SPCXB moves from MARS pool via execution router into BNB Uniswap V4 PoolManager. PoolManager pays 300.469119930046341453 USDT to the router; router sends the *same* USDT to Pancake V3 0x172fcd; pool pays 0.529316564670653425 WBNB. All five transfers are independently located by original hash/block and indexed sender+recipient.
- Block 112964866: owner spends exactly 1 BNB, routes 0.99 WBNB to USDT/WBNB Pancake V3, receives 567.267028203488200885 USDT, sends that to 0x51a45a USDT/SPCXB V3, and receives 4.985442910027358206 SPCXB into MARS pool. Four exact-hash ERC20 Transfer legs verified; the original high-density V3 Swap event is still unreadable.
- Blocks 115522575 and 119938551: SPCXB moves from MARS pool through router to WBNB/SPCXB V3 pool 0x66faad; exact original V3 Swap events and WBNB transfers yield 0.098133787173063699 and 0.040884390654375947 WBNB, respectively. Pool token0 WBNB, token1 SPCXB, fee 2500 ppm verified via original `eth_call`.

### Fee consistency

For all three sales, raw integer equation

`wallet_native_delta_wei = gross_wbnb_output_wei - floor(gross_wbnb_output_wei / 100) - implied_gas_used * tx_gas_price_wei`

holds **exactly** with positive integer gasUsed inside each signed original transaction gas limit. For the one buy, `1 BNB - 0.99 WBNB` is consistent with 1% input cut; the native delta minus signed BNB input yields an integer gas amount. The inferred gasUsed values are recorded above.

**Caveat:** original `gasUsed` receipt field was not independently recovered for these previously truncated large receipts. This is compelling **arithmetic compatibility**, not a completed independent receipt readback. The Uniswap V4 PoolId and Swap event remain **UNVERIFIED**. A raw V4 token transfer to PoolManager does not by itself establish its specific PoolId.

### Scope and remaining priority

- Source MARS pool remains subject to the previously documented historical V2 3% MARS tax on directly decoded V2 Swap events; its 2 truncated Swap events retain exact quote Transfer fallback. Separate USDT/MARS V3 venue has fee=1% and lacks that observed MARS quantity tax on its 2 trades.
- Original 29 MARS token event hashes include external/unknown-signer receipts and open residual inventory; 16-route accounting must remain separate from 2 USDT/MARS V3 owner trades.
- Now assess net transaction-level proceeds, true open inventories, adverse trades and 23-wallet × fixed 19-CA opportunity denominator without retrospectively changing token universe or thresholds.
- Do not interpret native BNB block change across an incomplete scope as fully verified realized PnL, and do not promote this wallet to validated followable trader.

Machine-verifiable proof: `BSC_MEME_DDAC_MARSCOIN_FOUR_OPEN_UPSTREAM_ROUTES_V3_V4_EVIDENCE_2026-10-12.json`. Original historical evidence remains under `BSC_MEME_DDAC_MARSCOIN_18_POOL_TRADE_V2_V3_TAX_AND_QUOTE_RECONCILIATION_2026-10-11.json` and `BSC_MEME_DDAC_MARSCOIN_29_NATIVE_BLOCK_CASHFLOW_2026-10-11.json`.

No production configuration, trading, alerts, monitors or schedulers were changed. **NO_GO**.
