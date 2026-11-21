# Base fee and lending QA — 2026-10-18

Scope: independent address-analysis module, read-only research.

Previous Base fee calculation omitted the `l1Fee` field. Corrected total is `gasUsed × effectiveGasPrice + l1Fee`. Missing Base L1 fee now returns `PNL_UNRESOLVED`. The previous four-receipt audit recorded only L2 gas for row 045; it remains preserved as historical evidence.

Row 045: L2 cost 382277850000 wei, L1 data fee 3235250376 wei, combined 385513100376 wei ETH.

Row 051: two complete Base receipts demonstrate Aave lending deposit and withdrawal, not DEX swaps. Deposit: USDC -395415 raw, aUSDC +395414. Withdrawal: USDC +395414, aUSDC -395414. Total Base gas charges 2450909212621 wei ETH, including L1 fees. The observed one-unit USDC difference is NOT a verified realized loss; the full wallet history and FX are unresolved.

The fixed Python program and tests were run in an isolated local standard-library environment: 25 tests passed, 0 failures. Source blob a7e6a2432ed14b797dfa62d2ecd3e51633e8f479, test blob 80b543dd2fdf969eabaa95665c1222947f0530db.

Original full receipts are in fixtures/base-row051-aave-supply-withdraw-receipts.json; checked flows and Base fee reconciliation in evidence/base-l1-fee-and-lending-facts-20261018.json.

The historical sauce route receipts could not be independently decoded because returned data was truncated. No new closed PnL or wallet ranking is authorized. Mac live RPC end-to-end and external review remain unverified. Batch007 not started.

RESEARCH_ONLY / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE.
