# Broad all-chain wallet + claim scan

run_time: 2026-09-28T15:00:00+07:00
mode: manual_live_chain_reconciliation
status: completed

## Provider

Alchemy:
- selected app: ChatGPT Crypto Monitor All Chains
- app id: h6m5pairkgzet7vz

Known user addresses:
- EVM: 0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c
- Solana: BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp

Enabled non-EVM networks without a stored user-specific address:
- Aptos
- Bitcoin
- Starknet
- Sui
- Tron

These are classified UNAVAILABLE_USER_ADDRESS.

## Core fresh balances

Ethereum:
- USDC 400.308121
- ETH 0.001667063838788351
- WETH 0.000038313
- Credits #23042/#23232 direct ownership reconfirmed

Solana finalized:
- slot ~451261074
- USDC 430.483714
- SOL 0.135926955
- PAID 0 / absent current Token-2022 account list
- KARDASHEV 0
- SHARTCOIN 0
- prior SPC 1.745552 no longer present
- four 1-unit Token-2022 receipts unresolved because DAS asset lookup returned RPC -32001

Base:
- USDC 0.000252
- ETH 0.000790061852162197

BNB:
- BNB 0.000076956401760745
- USDC 0
- GSTOCK 0.096724707311314713 dust

Robinhood:
- ETH 0.000080297765615110
- PONS 0.000953441979624353 dust
- NFT count 0

Arbitrum:
- USDC 0.000001
- ETH 0.000003959328931033

Ink:
- ETH 0.010389022090321585
- Tydro Ink Points 7.665136656205785948

Unichain:
- USDC 0.021286
- ETH 0.000231941590232335
- CRED 0
- UNICRED #230 direct ownership reconfirmed

## Special chains

Optimism:
- ETH 0.000065278581034767
- USDT 0.000449
- USDC 0
- DAI 0

Polygon:
- POL 0.291295907607284273
- canonical USDC 0
- DAI 0

Avalanche:
- AVAX 0.000678889764814817
- canonical USDC 0
- canonical USDT 0
- tiny WAVAX / COQ / ARENA only

Hyperliquid EVM:
- HYPE 0.000234033730511199
- USDC 0.00172
- USD₮0 0.004646
- tiny USOL/NEST
- unpriced ALT / hypeify / wrhyper.com-style receipts excluded

Linea:
- ETH 0.000283128973717299
- LINEA 0.221708425875998735
- REX 0.101880947178375346
- USDC 0

Monad:
- MON 0.3817997
- canonical USDC 0.024112
- unpriced MONE/TEST/FGP/CHOG/MONKA/DAK excluded
- Unicode-lookalike fake USDC excluded

World Chain:
- ETH 0.000106736504323280
- WLD 0.04

MegaETH:
- ETH 0.000082071511230598

Plasma:
- XPL 0.009576790735189758

Sonic:
- S 0.577025845877296

Zero native:
- Berachain
- Blast
- Mantle
- RISE
- Scroll
- Sei
- zkSync

## Valuation

Market references:
- ETH 2646.43
- SOL 118.28
- BNB 762
- AVAX 10.36
- HYPE 88.89
- POL 0.11261
- MON 0.028532
- S 0.03811641049306892
- XPL 0.10208

Verified stable assets:
- 830.844301 USD-equivalent units

Native/gas subtotal:
- ~52.48552 USD

WETH:
- ~0.10139 USD

Tiny priced WLD / LINEA / REX / WAVAX / COQ:
- ~0.02259 USD

Strict directly priced on-chain liquid:
- ~883.45 USD

Material NFTs:
- Credits #23042/#23232 current collection floor 0.0262 ETH each; top offer 0.0252 WETH each
- Credits floor subtotal ~138.67 USD; top-offer subtotal ~133.38 USD
- UNICRED #230 floor 0.00359 ETH; top offer 0.0022 WETH
- UNICRED floor mark ~9.50 USD; top-offer reference ~5.82 USD

On-chain + material NFT floor marks:
- ~1031.63 USD

USER_CONFIRMED Binance earn:
- 659.9 USD-equivalent

Total tracked asset completeness reference:
- floor-mark: ~1691.53 USD
- NFT top-offer-oriented: ~1682.56 USD

Not Mission profit/progress because provenance remains unresolved.

## Claim scan result

result: NO_NEW_VERIFIED_CLAIM

Latest successful Airdrop/TGE monitor state also had no new verified ACTION.

No legitimate cash/token claim entitlement was established from the broad wallet scan.

Claim-bait / unsafe examples:
- Avalanche token advertising 1,000,000 PENDLE with a claim URL
- Avalanche NFT directing holder to a claim website
- Linea compensation-attestation NFT from unaffiliated domain
- Optimism malicious/spam NFT metadata
- Robinhood, BNB and Polygon unsolicited airdrop-style receipts

Do not interact with these.

Limitation:
- generic wallet reads cannot prove protocol-specific off-wallet staking/reward escrow is zero;
- Ink NFT ownership endpoint is not enabled;
- several special chains expose native RPC but not enhanced token/NFT APIs;
- Solana DAS asset endpoint was temporarily unavailable;
- Aptos/Bitcoin/Starknet/Sui/Tron cannot be attributed without canonical user addresses.

## State changes since 09:32

- Solana USDC 420.472536 -> 430.483714
- Solana SOL 0.127067295 -> 0.135926955
- PAID 0.000473 -> 0
- SPC 1.745552 -> no longer present
- Base USDC 0.252982 -> 0.000252
- Base ETH 0.000790846510479134 -> 0.000790061852162197
- BNB 0.007878625902744041 -> 0.000076956401760745
- Arbitrum ETH 0.000825005012848238 -> 0.000003959328931033
- Robinhood ETH 0.000815126815110326 -> 0.000080297765615110
- special-chain balances newly included
