# Frank Solana USDC: three FOMO-cosigned third-party payout traces (2026-10-09)

Status: **CHAIN_TX_TRACES_OBSERVED / ECONOMIC_PURPOSE_UNCONFIRMED / FRANK_TRADES_NOT_CONFIRMED**.

## Provenance, scope, and limitations

User ran the review-only `scripts/audit_frank_partial_trace.py` from pinned PR #29 code `f70952ae97655e00691173bf753ff66cfe1a73a2` on Mac. Operator-pasted result: `status=TRACE_REVIEW_ONLY`, `rpc_attempts=3`, `all_sample_traces_complete=true`, exit 0. That script checks each fetched `getTransaction` against the SHA-256 digest of its existing local decoded receipt, then saves trace receipts. This document records **the provided output**. It does not claim independent new RPC access or that the unprinted unparsed instruction bytes/order IDs were independently decoded.

Fixed audit scope: Frank Solana main wallet `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`; known owned USDC token account `6kD22oUQrV8tVpE2hkQzkoobwCQAy2iiZcipWn8AD5jF`; USDC mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`. Root-only cached list had 173 main-wallet-referenced signatures, while the unfinished USDC-account scan collected 686 in-window signatures, 684 absent from the root list. **Signature membership does not prove 684 Frank BUY/SELL events.**

## Three real transaction traces, separate from Frank's root wallet

| Tx signature (prefix) | Fee payer | Frank-owned USDC net receipt | Funding/source in same tx | Program and signer evidence |
|---|---|---:|---|---|
| `VTj1ZEHE8SRA...` | `AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51` | +0.265050 USDC | `GnvuWxnim8pTf8c83rPBtg3eKn7RByn55WAukQSnqwkQ` owns USDC account `43n5tkYnvyoBDr5oMRfwc7gf17fUpD3eABxHrh1NpgPp`, -33.135284 USDC; split +32.472658 elsewhere, +0.397576 elsewhere, +0.265050 to Frank | FOMO cosigner present; `DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH` present; other-owner token/W SOL movements; no Frank target token delta |
| `5e4Yhedz6hVhWQK...` | same FOMO cosigner | +0.475000 USDC | `3ZnJCjxJqj2YSaDTxbPAnFNXBjA6i8C8UCvhoJf9J43V` owns USDC account `BPpVKs57AEeWVy22BXVcGn5NG8zsgn655Uio7cupZXiM`, -100 USDC; split +97.425580, +1.624420, +0.380000, +0.095000, +0.475000 (Frank) | FOMO cosigner; `JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4` present; other-owner token/W SOL movements; no Frank target token delta |
| `5S6iHKmP5NBCyqv...` | same FOMO cosigner | +0.475000 USDC | `BafcHutB6YAA29XJvwThwR6Nust813q2fKMikLMGr1PG` owns USDC account `8mb39MavteRoUmEvByR3UErHkEL4wKcMJF2mr4BLRgq5`, -100 USDC; split +99.050000, +0.380000, +0.095000, +0.475000 (Frank) | FOMO cosigner; `proVF4pMXVaYqmy4NjniPh4pqKNfMmsihgd4wdkCX3u` present; other-owner pump-token/W SOL movements; no Frank target token delta |

Exact signatures:
- `VTj1ZEHE8SRAjJcpWiTu1RMr6xZoxoYKUidtSK9XCucgviF4vaExybXHS7FKnk1pZNEbxzngNmeMgwTKBZX2P2r`
- `5e4Yhedz6hVhWQKjrKgobyfVEQR4Gz33BY13dgiQko5tywZqy9j4WknTAAoNM3EL9PUc3ECuRyfFdun7n3YM4BxM`
- `5S6iHKmP5NBCyqvjsftqVLMLWc3SM18QDsmGqNk7SPsiURDqmD49fdFoPrmZJP4HRKoqwaz7pRxXUKgvw1Snjvem`

For **all three**, `tx_succeeded=true`, `frank_root_signed=false`, `fomo_cosigned=true`, `relay_solver_signed=false`. Their trace instructions directly show non-Frank USDC source accounts paying Frank's USDC associated account, with other participants executing token movements. Combined sample Frank receipt is **+1.215050 USDC**; this is NOT measured profit, trading P&L, or confirmed sale proceeds.

## Interpretation / decision

**Confirmed:** these three root-absent signatures are FOMO-cosigned third-party funded **USDC credit/distribution events to an account belonging to Frank**, not Frank-root-signed swaps. In tx 2 and tx 3 the identical 100-USDC funded transactions both allocate 0.475 to Frank, 0.095 to another recipient, and 0.38 to another recipient. The consistent split strongly suggests a **route fee share, rebate or referral distribution**; none of these economic explanations is independently proved from decoded order identifiers or platform records.

**Not confirmed:** Frank initiated these trades, Frank sold or bought the other participants' tokens, Frank received trading P&L, the three samples are representative of all 684 root-absent signatures, or the economic identity behind the FOMO distribution/fee recipients. Do not count three Frank buys/sells. `has_known_router=true` alone is insufficient for attributed trading.

**Classifier caution:** `mission_agent/meme/fomo_crosschain.py::solana_events` starts with a root-wallet-present-in-transaction check, so it ignores root-absent FOMO-cosigned receipts. This is a **coverage issue for settlement/receipt observation**, not proof that safe BUY/SELL classifier should accept unsigned third-party routed transactions. Keep receipt/payout signals separate from person trading signals. Do not promote fee income into `PERSON_PATTERN` or `TOKEN_CONSENSUS`.

## Next investigation without blind account scans

1. Use already persisted hashes and full instructions to establish whether a fee-sharing/referral order ID can be recovered; if not, report `FEE_SHARE_HYPOTHESIS_UNCONFIRMED`.
2. Investigate a bounded second small sample of *other* root-absent USDC signatures (not these same 3). Stratify by date and whether Frank-owned USDC is positive, negative, or zero; **balance polarity requires actual transaction decode**. Keep samples clearly distinct from confirmed trades.
3. Only if there is real Frank-owned USDC outflow paired with target acquisition and externally verifiable beneficiary/authority relationship should the hypothesis of missing active BUY/SELL be escalated. Fee distributions remain `OBSERVE_ONLY`.

No production, main branch, LaunchAgent, monitor, email, wallet or autotrading changes. PR #29 remains DRAFT; `PERSON_TRADE_COVERAGE=UNVERIFIED`; `PRODUCTION_TRADING=NO_GO`.
