# Frank FOMO multi-chain source V1 — evidence-only

Updated: 2026-10-09 Asia/Bangkok  
Scope: Frank/Meme; read-only research; no signal authority; NO_GO trading.

## Why this exists

Mac's `2026-10-07/08` production 24-hour audit of Solana
`498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ` was:

- finalized RPC signatures = 173, stored signatures = 173, difference = 0;
- `PASSIVE_TRANSFER/FRANK_NOT_SIGNER=152`;
- `ATA_CREATE/THIRD_PARTY_ATA_CREATE=18`;
- `UNKNOWN_NEEDS_REVIEW=2`;
- `ACTIVE_TRADE/BUY=1`, zero `ACTIVE_TRADE` unpersisted.

This only proves signature completeness for one address and one time window.
FOMO's app may pay from Solana and receive the bought token on another chain,
where a solver signs the fill; `FRANK_NOT_SIGNER` does not independently establish
`NOT_A_PERSON_TRADE`. **Never claim Frank only traded once.**

Sources:
- FOMO architecture and order joining: https://github.com/chainstacklabs/fomo-solana-rh-listeners
  (`docs/01-how-it-works.md`, `docs/02-trade-lifecycle.md`, `docs/05-relay.md`,
  `docs/07-addresses.md`).
- Robinhood mainnet chain ID 4663 and public RPC:
  https://docs.robinhood.com/chain/connecting/
- THIRD-PARTY Frank identity leads:
  https://hoodwatch.dev/trader/frankdegods and
  https://hoodwatch.dev/trader/A5SEXYJY4jTEi6sjMLfZs5KAP8SVFvLDPDV67GgSSZSk

## Address provenance and authorization

| Chain | Address | Role | Source / trust |
|---|---|---|---|
| Solana | `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ` | Current monitored cash/profile wallet | User-approved local monitor, independently audited for one Solana window |
| Solana | `A5SEXYJY4jTEi6sjMLfZs5KAP8SVFvLDPDV67GgSSZSk` | Candidate alternative wallet | Hoodwatch Frank page; **third-party identity attribution only** |
| Robinhood Chain | `0x696d1265c8fc4f14797abebfae3c43ebfa9d8e28` | Candidate FOMO EIP-7702 wallet | Hoodwatch Frank page; **third-party identity attribution only** |

The onchain EIP-7702 code and a wallet's authentic ERC-4337 UserOperation
prove *how an address transacts*, **not** that it belongs to this particular
Frank persona. FOMO attribution must be established independently for production.

## Implemented research modules

- `local-agent/mission_agent/meme/fomo_crosschain.py`: deterministic pure
  read-only decoders. Solana FOMO co-signed Relay payments, payout memo,
  own-balance multi-asset same-chain swap candidates; Robinhood Chain
  ERC-4337 v0.8 per-operation scoped SELL evidence and Relay-executor delivered
  BUY token receipts, Relay order ID pairing across both chains.
- `local-agent/scripts/audit_frank_fomo_crosschain.py`: bounded historical
  Solana `getSignaturesForAddress` + `getTransaction`, Robinhood `eth_chainId`,
  EIP-7702 `eth_getCode`, event `eth_getLogs` + per-receipt verification.
  Uses HTTPS public Robinhood Chain RPC by default and existing private Solana
  RPC file without printing its endpoints/credentials.
- `local-agent/tests/test_fomo_crosschain.py`: offline fixtures: exact-order
  payment/receipt join, delegated co-signing, unrelated third-party transfers,
  bundled multi-user user-operation isolation, ambiguous routes, RPC pagination,
  missing ordering/ownership evidence.
- `.github/workflows/meme-fomo-crosschain-tests.yml`: pin-dependency offline
  regression on PR pushes, with all of Git history for frozen contract tests.

Research output does **not** import legacy Frank `Ledger` or `MissionMemeService`,
write `forward.sqlite`, change `FOLLOW_POLICY_V1`, create monitoring
LaunchAgents, touch `mission-control.sqlite`, or send notifications.

## Classification gates

| Signal | Required proof | Prohibited inference |
|---|---|---|
| Solana PAY | Signing wallet + recognizable Relay depository instruction, nonzero order ID, **negative owned USDC balance**, additional FOMO co-signer to establish FOMO identity | PAY alone does NOT reveal token bought |
| Robinhood BUY fill | Correct Relay Router transaction + successful receipt + ERC-20 transfer from Relay executor to candidate wallet + order ID from router call | Delivery alone ≠ Frank BUY |
| Robinhood SELL executed | EIP-7702 wallet + successful UserOperation **scoped to this wallet**, token transfer OUT + Relay depository event with same operation scope | Shared bundler receipt cannot be attributed by transaction hash alone |
| Solana payout | Relay settlement solver signed + explicit order memo + wallet's positive owned USDC balance | Payout alone ≠ Frank SELL |
| PAIR | Exactly one SOL PAY and one RH BUY fill sharing exact order ID; or one RH SELL and one SOL payout sharing exact order ID | No time-only, token-symbol-only, unrelated-fee-transfer matching |

Statuses `PAIRED_BUY_EVIDENCE` and `PAIRED_SELL_EVIDENCE` are
**research evidence only**, subject to candidate address attribution.
`attribution=THIRD_PARTY_UNVERIFIED` and `signal_eligible=false`
are invariant, even for both legs observed.

Partial/RPC-capped/missing data must be labelled `PARTIAL` and never reported
as complete. Unknown decimals stay unknown; no made-up price, trade PnL,
valuation, CA correspondence, or performance metrics.

## Operator verification and next release gate

First read-only run from exact reviewed Git commit (no service restarts):

```bash
cd <fresh-fomo-review-worktree>/crypto-300-profit-mission/local-agent
PYTHONPATH=. python -B -m pytest -q tests/test_fomo_crosschain.py
PYTHONPATH=. python -B scripts/audit_frank_fomo_crosschain.py --hours 6
```

Expected output: completeness of *each chain/address* separately,
`RELAY_PAY/RELAY_PAYOUT/SWAP_CANDIDATE/RH_BUY_FILL/SELL_EXECUTED` counters,
exact paired vs unpaired order IDs, and `THIRD_PARTY_UNVERIFIED`.
The public Robinhood RPC is rate-limited; `PARTIAL` is an audit failure
for completeness, not evidence of zero activity.

**Before any production signal integration**:
1. Independent address↔Frank identity confirmation.
2. Live three-source replay of an overlapping window with exact tx hashes,
   order IDs, token addresses, time and amounts, plus completeness audit.
3. Historical bias-safe replay of per-person (not payment-only) BUY/SELL
   decisions; verify old 24h passive receipts for relayed fills vs airdrops.
4. Explicit separately reviewed source/policy change and no shadow-to-live
   promotion without tested rollback, deduped email receipts and approval.

Current installed Frank/Mission Loop intentionally stays on its approved
Solana-only data source while this read-only crosschain design is audited.
