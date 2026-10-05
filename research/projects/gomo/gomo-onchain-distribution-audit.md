# GOMO / Gomo App 链上分发与卖压核验

Updated: 2026-10-06 Asia/Bangkok
Project domain supplied by user: https://gomofamily.life/
Canonical Solana mint verified on-chain: `9XKzy4KahcZaGJPJtz1PtqGPB3CiseoBrx7TcQhEpump`
Status: WATCH / PROJECT-WALLET IDENTITY UNRESOLVED

## Research policy for this review

This review uses an adversarial default:
- project statements, website copy and social posts are leads only;
- direct chain state and transaction history are the primary evidence;
- a Git repository counts as product evidence only when its relationship to the project can be independently established;
- a transfer proves token movement, not project/team ownership of the sending wallet;
- wallet labels such as team, treasury, investor or distributor remain UNCONFIRMED unless control/identity is independently linked.

## Current conclusion

CONFIRMED ON-CHAIN:
- GOMO is a Solana Token-2022 mint with 6 decimals.
- At the reviewed finalized slot, supply was `845,073,551.359334 GOMO`.
- Mint authority is null, freeze authority is null, and token metadata update authority is null.
- A wallet `FsYRQmoe8zCupamq3Jw4j1oZb1HnAFt3HcXZb8Dgggfi` accumulated GOMO through market interactions and later redistributed almost all of a 26.650701M GOMO balance to three wallets within 55 seconds.
- At 2026-10-05 18:10:18 Bangkok, tx `4vjZbT8KRf2CXC1YC1TsNvYqjGF9zhaWTCAf1m9DjLb3kmygw1qDa2KivjJBSZt9pWeptXthcj16ouAtYShrhPHy` transferred exactly `10,000,000 GOMO` to ATA `Ed5Cf1TRN9iv9DnT5uuTYnabLufjnmwqVZRNVGoR24VR`, owned by `GkxxSzvd4kh3hRkjHoG1KtH49xUj96jZZVBFoFkoeYaM`.
- At 2026-10-05 18:10:41 Bangkok, tx `5WVE7vKpqtC9ABM16R6yQajDNHrfV3RwhxQJpV7ExaGJXXjbD2LfosTT25NyCxV3UiWp6NiYyLsAeBwPgkyh3M61` transferred exactly `10,000,000 GOMO` to ATA `BbsQUMT1tyq2kR2hCbejxwdawzqu3DLivZn2beqbKE7y`, owned by `G7txkS3VsxFEGXbxNFS1jpSQELsNzt3kJVC9siJZSrvG`.
- At 2026-10-05 18:11:13 Bangkok, tx `2W8t7SS7Vi9JtQ4GDzyfFJ9VKfdBrTypERt7xW2mr4ic8vCS6HnUuPr2i5u8SjaZcB4NNmKt1D5tpadFvw4NdWKA` transferred exactly `6,000,000 GOMO` to ATA `82ZYkEV3S2ztJevA1HXXrdtKxxW7nPjsctJ2aD67vDT9`, owned by `E7utwT34S2ceBMCw4H4MiYWRxXB4jFW8ePwXSpx7x6Ky`.
- The three transfers total `26,000,000 GOMO`, approximately 97.56% of the source wallet's 26,650,701.345498 GOMO immediately before the split.
- The first 10M recipient then began a machine-like sell schedule. Its ATA `Ed5Cf...` repeatedly sends exactly `69,444.444444 GOMO` into the PumpSwap pool at intervals close to 15 minutes.
- The first confirmed scheduled sell in this sequence was tx `dVCv6K1qG4hjbktAyosmjb5MGfZELZ3iVKvSQQiFzNBcQ1mo242y4Y4bmPrpvHszEiCy4PoqfMYZ5oraRp6UQs9`.
- A later checked sell, tx `2JfivUX1Dz9JKgpT9ntE6LJZTByZxhEiATJE4P8KFq87EUDqcJHDoP4BrhaSwys5GU1cpPpdVTcEZgJY9oYecdi3` at 2026-10-06 00:34:46 Bangkok, again moved exactly `69,444.444444 GOMO` from that wallet to the pool token account.
- Current checked balance of that recipient ATA was `8,541,666.666676 GOMO`. Relative to its 10M receipt, `1,458,333.333324 GOMO` had left, exactly equivalent to 21 chunks of `69,444.444444 GOMO` at the inspected state.
- The second 10M recipient ATA still held exactly `10,000,000 GOMO` when checked and its ATA had only the original receipt transaction at that time.
- The 6M recipient ATA later held `7,666,461.677269 GOMO`, so it subsequently had net additional accumulation and cannot be classified as a simple one-way dump wallet from the current evidence.

UNCONFIRMED:
- No on-chain proof currently links `FsYR...gggfi` to the GOMO project, deployer, team or treasury.
- Therefore the 26M split is a confirmed coordinated wallet redistribution, but it cannot yet be labeled an official/project distribution.
- No public GitHub repository that can be independently tied to Gomo/Gomo Family was found in the reviewed GitHub search. Searches for the project domain, social identity phrase and exact mint returned third-party scanners/trading datasets, not an attributable official source-code repository.
- Product/software claims therefore have no independently verified public source-repository support in this review.

## Adversarial interpretation

The strongest adverse interpretation supported by current evidence is:
1. a large buyer wallet accumulated GOMO;
2. it then split 97.56% of that balance into three recipient wallets in under one minute;
3. one 10M recipient subsequently executed equal-size DEX sells on an approximately 15-minute cadence;
4. this is consistent with deliberate inventory segmentation plus scheduled market distribution/selling.

This pattern is materially more concerning than an ordinary holder transfer because the receiving wallet's behavior is systematic and executable on-chain.

However, the missing identity link matters. Calling this a team dump, treasury distribution or insider vesting release would exceed the evidence. Until the sender/recipients can be tied to the project, classify them as `COORDINATED_WALLET_CLUSTER / PROJECT_IDENTITY_UNRESOLVED`.

## Current chain references

Mint:
`9XKzy4KahcZaGJPJtz1PtqGPB3CiseoBrx7TcQhEpump`

PumpSwap pair owner observed for the main GOMO pool:
`5a7QurJLARt146JajJYPe5nh6vLyFpN2QrHUSLqbsCZy`

Pool GOMO token account:
`2evpdAHgYwJtGM5JDeSUDq2FXfJp9t3rkeeqfzKEfpWp`

Distribution source wallet:
`FsYRQmoe8zCupamq3Jw4j1oZb1HnAFt3HcXZb8Dgggfi`

Source GOMO ATA:
`Dfr1Ne1yDSpWqQN4vdRnAxSJEm3SPdHbpSErnQcRWvLa`

Recipients:
- `GkxxSzvd4kh3hRkjHoG1KtH49xUj96jZZVBFoFkoeYaM` / ATA `Ed5Cf1TRN9iv9DnT5uuTYnabLufjnmwqVZRNVGoR24VR`
- `G7txkS3VsxFEGXbxNFS1jpSQELsNzt3kJVC9siJZSrvG` / ATA `BbsQUMT1tyq2kR2hCbejxwdawzqu3DLivZn2beqbKE7y`
- `E7utwT34S2ceBMCw4H4MiYWRxXB4jFW8ePwXSpx7x6Ky` / ATA `82ZYkEV3S2ztJevA1HXXrdtKxxW7nPjsctJ2aD67vDT9`

## Decision state

`WATCH`

Reason: there is real on-chain activity and a clearly identifiable coordinated redistribution/scheduled-sell pattern, but the crucial project-wallet identity link is unresolved. Any claim that the project itself has recently distributed tokens remains `UNCONFIRMED` until that identity link is established.
