# Frank: TWEETCRAFT Solana root-signed swap candidate (2026-10-09 audit)

Status: **ROOT-SIGNED / FOMO-COSIGNED / OPPOSING OWNED NET FLOWS CONFIRMED BY USER MAC OFFLINE CACHE**, but **EXECUTION INSTRUCTION SEMANTICS NOT YET VERIFIED**. This is NOT a production BUY signal, proof of holdings, realized PnL, or a repeatable PERSON_PATTERN.

## Mac operator-provided fixed-window evidence

Operator ran `scripts/audit_frank_root_execution_focus.py` from SHA `bfdf73e327e218744bd644671318460a711a51be`; `status=ROOT_EXECUTION_EVIDENCE_OFFLINE`, `rpc_attempts=0`, `root_count=173`, `root_signed_count=2`; categories: NO_NET_TOKEN_CHANGE=22, RELAY_PAY=1, SWAP_CANDIDATE=1, TOKEN_MOVEMENT=149; research candidates=2, exit=0.

**Root-signed TWEETCRAFT candidate**:
- Solana tx signature: `4sP6iSpctgnnbKsLcGRn1YvaPB7TF9EGc1A6KL4G7gGwLKdP1Jm6LfEH3fs9UhQLMFNPwJ6tmS4FaEAaGT9XCC9S`.
- Block timestamp `1791423976` = **2026-10-08 08:46:16 Bangkok (UTC+7)**; slot `454400785`.
- Frank root `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`: `root_signed=true`.
- FOMO co-signer present: `fomo_cosigned=true`.
- USDC SPL mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`; raw delta `-6715734492` with 6 decimals = **-6,715.734492 USDC**.
- Target token SPL mint `HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy`; raw delta `+4732220716414` with 6 decimals = **+4,732,220.716414 target tokens**.
- Offchain project label `TWEETCRAFT` independently matching the exact mint: Pump.fun `https://pump.fun/` surfaced this mint as TWEETCRAFT; DexTrading `https://dextrading.com/tokens/solana/HzYCHqAN2uoHGRnL9v2ChCfFQX3bvJuJd5zu2Hd5MZQy` and Vietnamese-language Gate official (non-Chinese website) `https://www.gate.com/vi/news/detail/gate-adds-trading-support-for-5-solana-based-meme-gems-including-dark-si-24817776` also match the identifier. Offchain label is not necessary to establish exact mint.
- **Net asset delta implied unit cost**: 6715.734492/4732220.716414 = **0.0014191507316440376 USDC per token**. Caveat: derived ratio of wallet delta, not a confirmed DEX swap execution price separated from fees, rebates or routing.
- `relay_or_swap_events[0]`: `kind=SWAP_CANDIDATE`; `reason=COSIGNED_OPPOSING_OWNED_BALANCES_ROUTER_PRESENT`; `order_id=null`; `trade_confirmed=false`; `needs_instruction_level_attribution=true`.
- The original local source report and 173 cached transactions are not attached to GitHub; this note relies on *user-pasted results* and trusted local invariant tests. We have NOT independently replayed the exact instruction bytes against a Solana RPC in this message.

**Separate 5,000 USDC Relay payment**, not a confirmed TWEETCRAFT purchase:
- Signature `KTW6qm2yw8PJC1cqUVejnG9yfYo3UQN5Y6dJJrwXeZQfbxL2ZvbtB4aymTPbPYr9BkhJrrhtswMGUytgqF5othS`, `block_time=1791391806`, slot `454281417`, `root_signed=true`, `fomo_cosigned=true`, owned USDC net `-5000000000` raw = **-5,000 USDC**, Relay `order_id=0xcb9a15b8ab25ecbbbb657b12fce469a196ef9efb3cea089e8b335aa78b2776ed`, `target_in_mints=[]`, `trade_confirmed=false`. Do NOT mislabel this as second TWEETCRAFT BUY or as a known Solana target token.

**Root-only coverage**: only 2/173 transactions in this fixed window have `root_signed=true`; the other 171 are not Frank root-signed. This does not exclude legitimate delegated execution, additional wallets or token-account-only settlement activity. Separately 684 owner-USDC-account-referenced signatures are root-absent; three sampled of those resembled third-party-funded fee/rebate distributions, not personally authorized buys.

## Next zero-RPC acceptance gate

Run PR #29 review-only `scripts/audit_frank_tweetcraft_instruction_offline.py` with the same immutable source report, root cache, readonly ledger, and pinned HEAD. It fails closed if the exact transaction hash, signers, amounts, mint, slot and window do not match user-provided evidence. It reports decoded outer and inner instruction program IDs, token transfer details, fee payer, and relevant logs, but **does not assign `executable_buy_confirmed=true` without independently verified DEX program/Swap instruction semantics**. No RPC calls, no monitors, production changes or network. Once done, only test a historical delayed-entry episode if execution attribution, follow-up price history and exit state can be independently established.

**Review-state gates:** PR #29 Draft. `TRADE_COVERAGE=UNVERIFIED`; `PRODUCTION_TRADING=NO_GO`, no alerts, email, wallet signing or production deployment.

## New real local instruction output (2026-10-09, strict execution mapping pending)

Operator executed `scripts/audit_frank_tweetcraft_instruction_offline.py` from pinned SHA `005406768b6a929717dd10d10e62fe1923d23ec2` on the Mac; output `status=ROOT_SIGNED_TWEETCRAFT_BUY_CANDIDATE_INSTRUCTION_REVIEW`, `rpc_attempts=0`, exit `0`, actual `instruction_count=38`, `instruction_details_truncated=false`, target tx/slot/time and owner USDC/TWEETCRAFT amounts match earlier cached audit. The report intentionally still said `executable_buy_confirmed=false` because program-specific opcode/call-stack binding had not yet been inspected.

**Exact Frank-authorized outgoing USDC transfers from account `6kD22oUQrV8tVpE2hkQzkoobwCQAy2iiZcipWn8AD5jF`:**
- `15.110402` USDC to `B218KQgaFwVt6CRrxYbuHLZ9qzbPs6mwhWL7c7YdpwJA` (`transferChecked`).
- `12.088322` USDC to `12xJHAvuCk3Hw38ywzRMjoRQ74GRpLrZm1uYMuDUvPSy` (`transferChecked`).
- `2.006560` USDC to `7Rb2u9SPGqJhtC9Y2UKttnUzKDW93VHEo1ZH6XX22dr8` (`transfer`), subsequently forwarded to `HrTf9CzXR1dRH4Sof5QrpmGWwpwAf3qZzwCsEjQpXcSq`.
- `6,686.529208` USDC to `2Y7HATmn9aJBcxCskE5V2U2epmjvkZmB51zTJBbhj4cU` (`transfer`), the largest route-sized leg.
- TOTAL = **6,715.734492 USDC**, exactly reconciled with Frank-owned USDC balance net change. Largest leg = 6,686.529208; three other outbound transfers sum 29.205284 USDC (0.4348784788% of the gross). Those recipients' **fee/settlement roles remain UNVERIFIED**; do not label the whole 29.205284 as a single proven platform fee.

**Exact incoming Token-2022 TWEETCRAFT instructions to Frank-owned ATA `7qujRSPgfbgiwMhBSc1znjaQoHM9jt6HQVw6TgxnLAsG`:**
- Source `yuF9W9QoeVQ8Qu7Dz3moCpsqPNVgUUaqw5M9GKGYt9S`, transferred 3,508,980.043008 TWEETCRAFT.
- Source `AN8Bp8AswcS3toaYHLD9hBaBGciKKG3E5YaRGrY3pujX`, transferred 1,223,240.673406 TWEETCRAFT.
- TOTAL = **4,732,220.716414 TWEETCRAFT**, exactly reconciled with the user's ATA change.

**Actual execution logs sampled**: `Instruction: Swap`, `Instruction: Buy`, `Instruction: GetFeesWithQuoteMint`, `Instruction: Swap2`, alongside `TransferChecked`. The transaction includes `DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH`, `BiSoNHVpsVZW2F7rx2eQ59yQwKxzU5NvBcmKshCSUypi`, and `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo`. Meteora's **official DLMM documentation** confirms `LBUZ...` is the `lb_clmm` deployed program (NOT Meteora Dynamic Bonding Curve), `swap2` supports Token-2022 exact-in swaps, and the swap discriminator is Anchor `sha256("global:swap2")[:8]` = `41 4b 3f 4c eb 5b 5b 88`. Citations:
- https://github.com/MeteoraAg/docs/blob/main/developer-guides/dlmm/index.mdx
- https://github.com/MeteoraAg/docs/blob/main/developer-guides/dlmm/program/instructions.mdx
- https://github.com/MeteoraAg/dlmm-sdk/blob/main/idls/dlmm.json
- DFlow aggregator V4 program ID independent description: https://github.com/no-limit-nodes/every-solana-program-decoded/blob/main/programs/dflow_aggregator_v4/instructions/swap.md
- `BiSoNH...` is publicly labeled BisonFi by Solscan, not cryptographically verified by this audit.

User-supplied log excerpt did NOT include full `Program <pubkey> invoke [N]` / success frames, nor raw Base58 data for DLMM instructions, so it is NOT yet possible from the pasted excerpt alone to bind `Instruction: Swap2` to the actual DLMM call or validate discriminator. PR-only `scripts/audit_frank_tweetcraft_execution_gate.py` now reads the **same cached** transaction (ZERO additional RPC) and fails closed unless program invocation frames bind the logs to Meteora DLMM `swap2`, an exact DLMM instruction discriminator exists in the raw tx, and both inbound/outbound amounts reconcile. Even if the gate passes, **Frank-person identity, episodic repeatability, P&L and production deployment remain UNVERIFIED/NO_GO**.

Gross-wallet-net implied ratio remains `0.0014191507316440` USDC/TWEETCRAFT; isolated largest USDC leg/total token receipt is `0.0014129791505302` USDC/TWEETCRAFT, **NOT** an independently proven single-pool execution price given multi-hop routing and no decoded event payload. Do not infer market cap from unverified circulating supply; do not count WSOL intermediate account lifecycle as separate Frank purchases or sales.

## Operator confirmed exact Meteora Swap2 execution gate and consolidated follow-through (2026-10-09)

**New operator Mac result at pinned SHA `39649318c9051973b8e7ff043f271d945e33f478`, zero RPC, exit 0**:
- `status=CONFIRMED_ROOT_AUTHORIZED_DEX_BUY_EVIDENCE`
- `onchain_buy_evidence_confirmed=true`
- `buy_log_bound_to_program=true`, `meteora_swap2_log_bound=true`
- `usdc_outbound_equals_owner_delta=true`, `target_inbound_equals_owner_delta=true`
- `largest_outbound_usdc_raw=6686529208`, `other_outbound_usdc_raw=29205284`.
- Invocation stack was `VALID`, `malformed=false`: DFlow V4 `DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH` → `Instruction: Swap` depth 1; pump program `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA` → `Instruction: Buy` depth 2; Meteora **DLMM** `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo` → `Instruction: Swap2` depth 2.
- Three DLMM instructions observed, one nested DLMM instruction at `inner:0` had 28-byte data prefixed by *actual matched* 8-byte Anchor `swap2` discriminator `414b3f4ceb5b5b88`. This ties executable program and parsed logs to the same original stored finalized transaction; not an unsupported guess.
- Therefore upgrade this **single** onchain trade to `CONFIRMED_ROOT_AUTHORIZED_DEX_BUY_EVIDENCE`. Pair with existing exact USDC spent and token acquired numbers above. This is **not** proof the offchain human Frank controls this root wallet (third-party attribution only), nor proof of repeated trend accumulation, realized PnL, token's eventual sale or copyable delay-follow returns.

**User workflow correction**: Previous piecemeal Mac commands imposed unnecessary user effort. The review branch now adds a single **opt-in, bounded** `local-agent/scripts/audit_frank_one_pass.py` that (1) reuses the immutable 173-root cache and performs the strict confirmed-buy gate offline; (2) with `--allow-network` traverses signatures only of already confirmed root-owned TWEETCRAFT ATA `7quj...` **after** the actual buy; (3) decodes newer transactions in chronological order up to a budget and reports net token/USDC/WSOL changes, potential sell/outflow, signer and FOMO evidence; (4) persists research-only page/receipt checkpoints; (5) returns an explicit PARTIAL status upon budget/429/page cap; and (6) never touches trading, alerts, email or production DB. Strict minimum 5 seconds spacing, no retries, default max 24 and absolute 32 RPC in any run. No new alert/automation was created. Actual historical lifecycle RPC on the user's Mac **NOT RUN YET**. The program cannot see user's private cache from cloud GitHub, so one local execution is still required to answer sell history after purchase.

**Permanent gates**: `PERSON_PATTERN=OBSERVE_ONLY`; `TRADE_COVERAGE=UNVERIFIED`; `PERSONA_IDENTITY=THIRD_PARTY_UNVERIFIED`; `REALIZED_PNL=UNVERIFIED`; production `NO_GO`. If post-buy ATA fully indexed but no sell, do not generalize to unknown closed/additional ATA or cross-wallet behavior.

## 2026-10-09 One-pass TWEETCRAFT exit candidate

The user's real Mac run at code `fe3616255ddd231a602873d529163897a77d06dd` completed this specific original TWEETCRAFT token-account's post-buy history: one signature-page RPC, three transaction-decode RPCs, zero reported errors. `history_status=COMPLETE`, `after_buy_signatures_observed=3`, `after_buy_transactions_decoded=3`, `candidate_count=1`, `rpc_attempts=4`, `stop_reason=null`, exit 0. This is coverage of a single known ATA after the pinned buy, NOT all possible Frank trading accounts.

The identified sell candidate `5wqKv5YuurRKUaJAK5fZtFrNg6GocVZuTTiAPWYrYDaswyUArwAZurpbZFU6WBjHp5z5Bt5bPCkLNKVQHfS6yigx` at slot 454718132, blockTime 1791509207 (Bangkok 2026-10-09 08:26:47), was signed by the root wallet AND the FOMO co-signer; Meteora DLMM, pump AMM and token programs appear among program IDs. Frank-owned TWEETCRAFT decreased **4,732,220.716414 tokens**, exactly matching the previous confirmed buy inflow; USDC increased **7,031.556770**; WSOL net unchanged. This is strong exit evidence, yet current decoder appropriately retains `OPPOSING_FLOW_SELL_CANDIDATE`/`trade_confirmed=false` pending sale instruction-level verification.

Prior confirmed buy: 2026-10-08 08:46:16 Bangkok, spent 6,715.734492 USDC, received exactly 4,732,220.716414 TWEETCRAFT. Block-time holding interval: 23h 40m 31s. Comparing these two transactions' wallet USDC deltas yields **+315.822278 USDC** and **+4.702721%**, on the assumption both are the complete lot consideration. These are conditional net changes, not a finalized, gas/tax-inclusive realized PnL. Original user console omitted the other 2 decoded transaction details; no assumption that they have zero economic impact. Offchain Frank identity/other accounts, repeatable delayed-entry alpha and complete PERSON_PATTERN validation remain UNVERIFIED; production remains NO_GO, PR Draft.
