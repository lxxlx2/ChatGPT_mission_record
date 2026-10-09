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
