# Frank V2 J7 RPC evidence provenance clarification — 2026-10-12

## Scope

This dated clarification supplements, **does not overwrite**, the original 2026-10-11 J7 research evidence:

- `frank-v2-j7-onchain-three-transfer-origin-2026-10-11.json` (contains an 82-character transcription error).
- `frank-v2-j7-raw-rpc-responses-sha256-2026-10-11.json` (archived original provider response strings with SHA256).
- `frank-v2-ata-index-scope-correction-2026-10-11.json` (the corresponding dated correction, including `direct_mainnet_rpc_*_lookup` summary keys).

## Precise meaning of "direct_mainnet_rpc"

The 2026-10-11 `direct_mainnet_rpc_*` keys mean that a **live Solana Mainnet `getTransaction` query was made via the connected Alchemy provider**. They do **not** imply a separate unauthenticated connection to a public Solana RPC validator, or any independent second provider. The research tool's underlying provider connection selected the read-only "ChatGPT Crypto Monitor All Chains" Alchemy app.

The corrected 88-character signature is:

`4JMFca46bpxkkVfykETjzwytqP9cNPtYFc9yKJD9cUnz1pKDf2MiHVgugTPxQp6HqVFpVCjpKXsYd243DCQi4LUU`

Its `getTransaction` result was checked as finalized, `slot=454705939`, with the returned `transaction.signatures[0]` matching the requested signature and `meta.err=null`. The originally transcribed 82-character string was rejected by that provider with Solana JSON-RPC `WrongSize`.

## Evidence limitations

The bad-signature `WrongSize` check and the corrected-signature connected-provider query were directly observed during the earlier assistant-side check; the old 2026-10-11 summary did **not** archive the complete rejected-RPC error envelope. Hence the bad-signature rejection must not be described as independently archived raw evidence. The corrected-signature on-chain transaction is supported by the separate original raw response/SHA256 archive.

These details do not establish market BUY, acquisition cost, realized PnL, complete history, or the identity of the upstream sender. The original archived source strings and previously cited evidence are unchanged.
