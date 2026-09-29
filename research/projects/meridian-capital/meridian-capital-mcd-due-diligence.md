# Meridian Capital / MCD 项目背景、团队履历、资金来源与链上结构调查

Updated: 2026-09-30 Asia/Bangkok
Chain: Robinhood Chain (chain id 4663)
State: LIVE / HIGH-VOLATILITY LAUNCH / REDEMPTION ACTIVE
Official: https://www.mcdao.io/
Official contracts: https://www.mcdao.io/contracts
Canonical MCD: `0x378A50eaC56f45Fb74e4cE7F1962dbCA33515c14`
Canonical gMCD: `0x296182D54dc5cBe6d960b9cFe3882dD5c87d51fd`

## Current conclusion

CONFIRMED:
- Meridian Capital is a live Robinhood Chain DeFi launch built around a treasury/accumulation mechanism, Genesis farming, non-transferable gMCD and delayed MCD redemption.
- The public face/founder is pseudonymous `lordpemby` / Pemby. His prior Yeet core-team involvement is independently verifiable from Berachain governance/forum records and a 2024 blocmates interview.
- No verified institutional seed/private/VC financing round for Meridian Capital was found. Genesis deposits/TVL and the gMCD conversion event are protocol capital formation, not VC funding.
- The canonical MCD/gMCD contracts and launch allocations can be reconstructed directly from Robinhood Chain.
- No confirmed centralized-exchange listing for canonical MCD was found at the time of review.
- The launch did use a very high initial effective buy-side tax. Direct transfer reconstruction shows an early trade diverting ~89.76% to the token contract; later observed trades show ~5%.
- MCD admin is controlled through a Safe rather than one EOA. gMCD remains owner-administered and exposes mint/redeem-setting/whitelist controls.

INFERRED:
- The design is intentionally reflexive: users deposit ecosystem assets, receive gMCD, then redeem into MCD subject to time-dependent forfeiture/burn mechanics.
- The initial 1.55M MCD vesting bucket is insider/long-term-allocation-like, but its exact label is not established by a first-party allocation table and must remain UNRESOLVED.
- The project has a real operator history and real deployed mechanics, but admin power, pseudonymous team identity and launch-stage liquidity remain material risks.

SPECULATIVE:
- Future CEX listings, sustained treasury growth, buyback effectiveness and long-run valuation cannot be inferred from launch-day price action.

## Project background and mechanism

Official site describes Meridian as “THE ACCUMULATION ENGINE.”

Official contract documentation describes:
- `GenesisFarm.sol`: MasterChef-style farm. Users deposit listed assets, pay deposit fees and earn non-transferable gMCD.
- `gMCD.sol`: escrow token that redeems into MCD over a configurable 0–7 day period.
- `Convertible.sol`: genesis participants can convert eligible stake at the launch-price mechanism during a limited window.
- All canonical contracts are on Robinhood Chain.

Official vesting UI/documentation states:
- gMCD redemption supports multiple simultaneous positions;
- shorter vesting forfeits more MCD;
- 7 days yields the full stated redemption ratio;
- forfeited MCD is burned.

## Founder / prior-project record

### Pemby / lordpemby

Primary evidence:
- Berachain forum proposals dated 2025 list `pemby@yeetit.xyz`, project `Yeet`, affiliation `Yeet core team`, and the Yeet official account.
- A July 2025 Yeet governance proposal from the same identity describes Yeet protocol revenue from Yeet BGT Auction, BakerDAO and other sources and proposes a buyback vault.
- blocmates interviewed LordPemby in May 2024 specifically about Yeet, including product mechanics, liquidity, emissions, NFTs and roadmap.
- Pemby later publicly described a Uniswap v4 experiment on Robinhood Chain as his own project.

What is NOT confirmed:
- no first-party evidence was found for claims that Pemby is an “OHM OG”;
- the available primary record proves Yeet core-team involvement but does not establish a public legal identity/CV;
- Yeet had an explicit protocol relationship with BakerDAO, but Pemby's exact founder/developer role at BakerDAO is not independently established.

Team transparency therefore remains pseudonymous / partially verifiable.

## Financing / capital formation

No credible first-party announcement of a Meridian seed, strategic, private or VC round was found.

Keep three concepts separate:

1. External investment round:
   - VERIFIED: none found / UNKNOWN.

2. Genesis TVL:
   - Meridian's own public communication reported more than USD 10M in Genesis farms.
   - This is user/protocol deposited capital, not company financing.

3. gMCD launch conversion:
   - the launch mechanism was built around roughly 15M gMCD at a USD 0.10 reference conversion value, implying about USD 1.5M of economic conversion capacity.
   - Partner/community corroboration reported that this capacity filled extremely quickly.
   - This is protocol launch capital formation, not a VC round.

## Canonical token contracts

### gMCD
Address:
`0x296182D54dc5cBe6d960b9cFe3882dD5c87d51fd`

Direct-chain facts:
- name: Genesis MCD
- symbol: gMCD
- decimals: 18
- non-proxy contract
- Solidity 0.8.19 source partially verified through Sourcify/Blockscout
- deployer: `0x29c1Df08da7BF2BEc8b17Ce9898684090B27777D`
- current total supply at review: ~15,525,875.5241 gMCD
- direct `mcdToken()` resolves canonical MCD to `0x378A50...`
- direct holder count observed through Blockscout: 697

At the same state snapshot, the gMCD contract held ~15,525,875.5241 MCD, essentially matching gMCD supply 1:1.

Admin:
- owner: `0x98762476d4f05c35240773BE4A5cE545a05B5074`
- owner address is a Safe proxy
- Safe owners:
  - `0xc03ce5a3a706cb7cce14119fb0fdbdbf5e855ca5`
  - `0x6f58633cb68281a739f6acc0ff2c3214cf9bf905`
  - `0x29c1df08da7bf2bec8b17ce9898684090b27777d`
- threshold: 2-of-3

Verified gMCD ABI includes:
- `mint`
- `redeem`
- `finalizeRedeem`
- `cancelRedeem`
- `updateRedeemSettings`
- `updateTransferWhitelist`
- `updateWhitelister`

This is meaningful admin/control risk even though authority sits behind a multisig.

### MCD
Address:
`0x378A50eaC56f45Fb74e4cE7F1962dbCA33515c14`

Direct-chain facts:
- name: Meridian Capital
- symbol: MCD
- decimals: 18
- owner: same 2-of-3 Safe
- current total supply at review: ~18,553,058.6461 MCD

The contract bytecode exposes a minter permission system including `mint` and `setMinter`-type functionality. Active minter rights still need a complete permission-state audit before treating the supply ceiling as immutable.

## Launch allocation reconstruction

Canonical MCD deployment tx:
`0x244d263f9b61c9d81704bc030ddf92ad462ded74fd5d94ff16e4054f79a98c9f`

Timestamp:
2026-09-29 12:21:32 UTC.

The same deployment transaction minted:

| Destination | Initial MCD | Interpretation |
| --- | ---: | --- |
| gMCD contract `0x296182...` | 15,500,000 | redemption backing |
| MCD contract itself | 1,000,000 | immediately used to seed launch liquidity path |
| owner Safe `0x987624...` | 550,000 | admin/operational allocation; exact label unresolved |
| vesting contract `0x7c70ad...` | 1,550,000 | time-locked allocation; exact official label unresolved |

Initial minted supply: 18.6M MCD.

Current supply at review was ~18.5531M, about 46,941 MCD below the initial mint. This is consistent with the documented forfeiture/burn mechanism. Treat this as net supply reduction since launch, not an independently reconstructed gross-burn total.

## 1.55M vesting allocation

Contract:
`0x7c70ad71754f2ae414c0c8d5f705dba00617a48d`

Its bytecode and callable interface match an OpenZeppelin-style VestingWallet.

Direct reads:
- beneficiary: `0x816abc97c82b2e42696916d4ecd01f25251e2fd5`
- start: 2026-11-28 12:21:32 UTC
- duration: 5,184,000 seconds = 60 days
- current released MCD at review: 0
- current releasable MCD at review: 0

Therefore the 1.55M MCD bucket has a ~60-day cliff from launch, followed by 60-day linear vesting, ending around 2027-01-27.

The beneficiary is itself a Safe:
- 4 owners;
- threshold 3-of-4.

Do not describe this as a simple “90-day lock.” The contract state gives the stronger evidence.

## Main AMM pool / liquidity

Main pair found directly on Robinhood Chain:
`0x1c7d14d2147795daf0b534521fec5dbb6579b2d6`

Direct contract reads identify:
- token0: WETH `0x0bd7d308f8e1639fab988df18a8011f41eacad73`
- token1: canonical MCD
- Uniswap-V2-style pair interface.

The MCD deployment transaction seeded 1,000,000 MCD into the initial liquidity path.

At a later direct read, reserves were approximately:
- 69.878 WETH
- 330,345.618 MCD

This implies ~0.00021153 WETH per MCD at that exact chain snapshot. Launch volatility is extreme, so this must not be reused as a current quote later.

## Launch tax reconstructed on-chain

An early pair-to-buyer transfer sequence showed:
- ~12,029.6977 MCD diverted to the MCD contract;
- ~1,372.3719 MCD delivered to the buyer.

Observed effective diversion:
~89.76%.

A later pair-to-buyer sequence showed:
- ~22.6088 MCD to the MCD contract;
- ~429.5669 MCD to the buyer.

Observed effective diversion:
~5.00%.

Therefore the social claim that MCD opened with a very high launch tax is directly supported by chain data. The tax/transfer mechanism materially decayed after launch.

## CEX / exchange status

As of this review:
- no reliable Binance, Coinbase, Kraken, Bybit, OKX, Gate, MEXC, Bitget or KuCoin listing announcement for the canonical MCD contract was found;
- current verified trading path is on Robinhood Chain DEX liquidity;
- multiple unrelated/same-name “Meridian Capital / MCD” tokens exist, so ticker-only searches are unsafe.

Canonical identity must always be anchored to:
`0x378A50eaC56f45Fb74e4cE7F1962dbCA33515c14`

## Security / governance observations

Positive:
- owner authority is behind a 2-of-3 Safe;
- the large 1.55M vesting allocation is enforced by a vesting contract whose beneficiary is another 3-of-4 Safe;
- gMCD redemption activity is live on-chain;
- MCD backing held by the gMCD contract matched gMCD supply at the observed snapshot.

Risks / unresolved:
- pseudonymous core team;
- gMCD owner can change redemption/whitelist settings and has mint authority;
- MCD has minter-role functionality; active role/state still needs a full audit;
- official site mentions a Genesis audit, but the indexed first-party material did not expose enough information to independently identify the auditor/report scope;
- official Meridian X account is suspended; the website currently tells users to use Telegram and only trust `@lordpemby`, increasing impersonation/source-verification risk;
- no confirmed CEX liquidity;
- launch-stage price, tax and liquidity are extremely unstable.

## Preliminary research state

Project reality: CONFIRMED / live.
Founder prior crypto work: CONFIRMED for Yeet core team.
Institutional funding: NONE VERIFIED.
Genesis deposited capital: project-reported >USD 10M.
CEX listing: NONE CONFIRMED.
Canonical contracts: CONFIRMED.
Initial allocation: reconstructed on-chain.
Large vesting allocation: contract-confirmed, purpose UNRESOLVED.
Admin/minter risk: MATERIAL / requires deeper permission audit.
