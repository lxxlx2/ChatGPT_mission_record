# Loan Meme 宣传、实际运行状态与 $LOAN 代币核验

Updated: 2026-10-06 Asia/Bangkok
Project: Loan Meme
Official domain: https://loanmeme.io/
App supplied by user: https://app.loanmeme.io/analytics
Docs: https://loanmeme.io/docs/
Official X stated in DefiLlama submission: https://x.com/loanmeme
Status: PRE-DEPLOYMENT BY OFFICIAL DOCS / ANALYTICS DATA CONFLICT UNRESOLVED

## Current conclusion

CONFIRMED:
- Loan Meme publicly describes a future isolated-book lending design for borrowing stables against memecoin collateral.
- The official docs currently and explicitly state: no mainnet or testnet contracts, audit not started, no token address, zero open books and zero total borrowed.
- The official roadmap says the project is still in the parameter-finalization phase; public testnet, external audit and mainnet are later stages with dates TBD.
- The docs define a future branded token `$LOAN` / LOAN MEME. It is intended to be a memecoin bought on the open market with eligible protocol revenue after book reserves are satisfied.
- `$LOAN` is explicitly not a governance token. Holding it gives no protocol-parameter voting rights and it is not required to lend or borrow.
- What happens to tokens bought back, burn versus hold, is still TBD.
- No official token contract/address is currently published in the docs. Any circulating asset claiming to be official LOAN MEME is disclaimed by the project itself.
- DeFiLlama currently displays small Loan Meme fee/revenue figures, but its adapter does not reconstruct those figures from Ethereum events. It directly reads Loan Meme's own unauthenticated GraphQL analytics endpoint at `https://api.loanmeme.io/api/graphql`.
- The DefiLlama adapter starts at 2026-10-01 and labels that as the first UTC day with settled operations.
- The original Loan Meme DefiLlama PR was submitted by the `LoanMeme` GitHub organization / `lando-loan`. The PR says collateral sits in per-user custody wallets on Ethereum, loans are paid from the protocol, and positions/fees/interest are booked in a double-entry ledger.
- That PR explicitly answered `Token address and ticker if any: No`.
- The PR did not supply actual treasury/custody addresses in its on-chain-reference section; the text still contained placeholders `[address]` and `[list or endpoint]`.
- CodeRabbit's review of the adapter explicitly noted that upstream data semantic correctness remained unverified and that the upstream party controlling the analytics API can influence the reported totals.
- Loan Meme's public GitHub organization currently exposes a fork of DefiLlama `dimension-adapters`; no public lending-contract repository was found in this review.

UNRESOLVED / CONFLICT:
- Official docs say no contracts, no markets and zero borrowed today, while the project's DefiLlama submission claims settled operations on Ethereum from 2026-10-01 and its own API emits fee data.
- The most plausible reading is that the analytics/API may represent an off-chain or custodial/prototype ledger that is separate from the future smart-contract protocol described in the docs, but this is an inference. The project has not supplied enough public on-chain references to independently prove the claimed settled operations.
- DeFiLlama showing fees should therefore not be interpreted as independent evidence that the advertised smart-contract lending protocol is live.

## Official product claims versus current evidence

| Claim / feature | Public description | Current verifiable status |
| --- | --- | --- |
| Isolated lending books | one meme / one stable per book | DESIGN ONLY according to docs; 0 books live |
| Meme collateral borrowing | lock meme, borrow stablecoin | DESIGN ONLY according to docs |
| TWAP risk engine | TWAP-based LTV/liquidation | DESIGN / parameters partly TBD |
| Senior / junior tranches | ordered lender loss waterfall | NOT LIVE; docs say it ships only if safely implementable |
| External audit | audit before books open | NOT STARTED |
| Mainnet contracts | future audited contracts | NONE according to current docs |
| Current total borrowed | future protocol metric | OFFICIAL DOCS: 0 |
| Current protocol fees | app/API/DefiLlama reports small fees | PROJECT-API REPORTED; not independently on-chain verified |
| Buybacks | surplus protocol fees buy LOAN MEME | FUTURE MECHANISM; buyback schedule TBD |
| $LOAN | branded memecoin | PLANNED; no official CA today |
| Governance | team + multisig + timelocks | `$LOAN` has no governance rights |

## DeFiLlama data-quality finding

DefiLlama adapter:
`https://github.com/DefiLlama/dimension-adapters/blob/master/fees/loan-meme.ts`

Merged commit:
`ff0723a030fffcf71692a798363dbe651d52504c`

Original project PR:
`https://github.com/DefiLlama/dimension-adapters/pull/9877`

Important mechanics of the adapter:
- hard-coded project API endpoint: `https://api.loanmeme.io/api/graphql`;
- asks the project API for `fees(days: 366, networkId: "EVM:1")`;
- reports the returned `totalUsd` as fees and protocol revenue;
- does not query Ethereum logs/contracts for the fees;
- start date is `2026-10-01`.

At review time DeFiLlama displayed low single/double-digit cumulative USD fees and $0 TVL. This should be treated as PROJECT-API-SOURCED evidence, not chain-verified protocol activity.

## $LOAN token status

There is a token design, but no issued/confirmed official token yet.

Official docs say `$LOAN` is intended to:
- carry the project's meme/brand;
- be bought on the open market using eligible protocol revenue;
- remain outside lending books;
- have mint/freeze authority revoked and contract/wallets published before use.

It does NOT:
- govern protocol parameters;
- provide voting rights;
- need to be held to lend or borrow;
- currently have an official published contract address.

Revenue-routing design:
1. lending-book fees/interest/liquidation revenue accumulates in stables;
2. book reserve/bad debt is paid first;
3. surplus is routed to a buyback contract on a schedule that is still TBD;
4. buyback contract buys LOAN MEME on the open market;
5. whether bought tokens are burned or held remains TBD.

Therefore current token classification:
`PLANNED MEME / VALUE-CAPTURE TOKEN; NOT ISSUED; NOT GOVERNANCE`.

## Risk / credibility assessment

Positive:
- docs are unusually explicit about unresolved parameters, risks and the absence of deployment;
- docs do not falsely claim a live audited smart-contract protocol;
- the fee adapter is public and the API is unauthenticated.

Concerns:
- the analytics/DefiLlama operations narrative conflicts materially with the current official roadmap/status page;
- current fee figures depend on a project-controlled API rather than independently reproducible chain events;
- the project's DefiLlama submission describes per-user custody wallets / off-chain double-entry accounting but does not publish the promised on-chain reference addresses;
- no public contract source/audit exists yet for the advertised future protocol;
- no official token CA exists.

Current research classification:
- Product concept: CONFIRMED.
- Live audited smart-contract lending protocol: NO / NOT DEPLOYED per official docs.
- Off-chain/custodial prototype operations: PROJECT-CLAIMED, not independently verified.
- DeFiLlama fees: REAL DEFILLAMA DISPLAY, but PROJECT-API-SOURCED.
- $LOAN platform token: PLANNED, NOT ISSUED.

## Primary sources

- https://loanmeme.io/docs/
- https://github.com/DefiLlama/dimension-adapters/blob/master/fees/loan-meme.ts
- https://github.com/DefiLlama/dimension-adapters/pull/9877
- https://github.com/DefiLlama/dimension-adapters/commit/ff0723a030fffcf71692a798363dbe651d52504c
- https://defillama.com/protocol/loan-meme
