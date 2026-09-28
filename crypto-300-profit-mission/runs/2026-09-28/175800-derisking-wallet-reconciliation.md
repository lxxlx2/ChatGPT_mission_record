# De-risking wallet reconciliation

run_time: 2026-09-28T17:58:00+07:00
status: completed
trigger: explicit user request after converting most liquid assets to USDC / Binance earn

## User-confirmed allocation intent

- keep Ink ETH for NFT participation
- keep SUI for Sui launchpad participation
- most other liquid crypto -> USDC or Binance earn
- ignore individual assets/NFTs below $0.10 in current presentation

## Binance USER_CONFIRMED

Screenshot:
- total earn ~682.40 USDT-equivalent
- USDC 382.27204197
- USDT 300
- no active futures/perpetual position

## Fresh direct-chain

Ethereum:
- USDC 400.308121
- ETH 0.001667063838788351
- WETH 0.000038313
- Credits #23042/#23232 ownership reconfirmed

Solana finalized slot ~451297915:
- USDC 444.679809
- SOL 0.015349154
- no material other fungible token identified above $0.10

Ink:
- ETH 0.010389022090321585

Base:
- ETH 0.000790061852162197

Linea:
- ETH 0.000283128973717299

Unichain:
- ETH 0.000231941590232335
- UNICRED #230 ownership reconfirmed
- CRED 0

World Chain:
- ETH 0.000106736504323280

MegaETH:
- ETH 0.000082071511230598

Robinhood:
- ETH 0.000080297765615110

Optimism:
- ETH 0.000065278581034767

All other individually priced known gas/token balances are below $0.10 or unpriced/spam and omitted.

## Sui

Canonical address:
0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101

Current connector cannot perform a Sui-specific direct read.

USER_CONFIRMED screenshot:
- SUI 40.192929
- contemporaneous wallet display ~$47.04

Market reference:
- SUIUSDT 1.1695
- mark ~$47.01

## NFTs >= $0.10

Credits:
- #23042 owned
- #23232 owned
- fresh Alchemy floor endpoint unavailable
- recent OpenSea-indexed collection floors roughly $67-$80
- conservative book mark $67.13 each / ~$134.26 total

UNICRED:
- #230 owned
- indexed floor 0.00359 ETH
- mark ~$9.54 at ETH 2656.93

Other measurable Ethereum NFTs:
- Survivor Dave #9347: 0.000049 ETH / ~$0.13
- Ten Years Of Ethereum #191404: 0.000251 ETH / ~$0.67
- Adventure Cards #3052: 0.00014 ETH / ~$0.37

Fresh INK #372:
- prior known inventory
- current Ink NFT endpoint unavailable
- no current mark assigned

## Valuation

Prices:
- ETH 2656.93
- SOL 118.59
- SUI 1.1695

Material on-chain liquid subtotal: ~930.30 USD
Material NFT subtotal: ~144.97 USD
On-chain + marked NFTs: ~1075.27 USD
Binance earn: 682.40 USD-equivalent

Total tracked asset reference: ~1757.67 USD

This is asset completeness, not Mission PnL.
