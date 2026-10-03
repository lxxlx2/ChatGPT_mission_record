# UNICRED / Unichain NFT Staking Exit & OpenSea Recovery

Status: **VERIFIED / completed onchain, 2026-10-01**

This record is intentionally privacy-redacted. The user wallet address, NFT token ID, user transaction hashes, local file names and unrelated fund movements are omitted. Public protocol/marketplace contract addresses are retained because they are needed to reproduce the workflow.

## Scope

This documents a real recovery/exit flow after the UNICRED frontend became unavailable with HTTP/Cloudflare **451 – Unavailable For Legal Reasons** while an NFT was still staked on Unichain.

The objective was:

1. recover any remaining staking/rental proceeds;
2. unstake the NFT without relying on the project website;
3. return the NFT to the owner wallet;
4. sell it through OpenSea despite a misleading network-fee error.

## Public contracts / chain

- Network: Unichain mainnet, chain ID `130` (`0x82`)
- UNICRED NFT / staking contract: `0xf60de24f228dc7ca6ff025958d2ee3a956ed88e5`
- OpenSea Seaport used by observed Unichain settlements: `0x0000000000000068f116a894984e2db1123eb395`
- OpenSea conduit used for NFT transfer approval: `0x1E0049783F008A0085193E00003D00cd54003c71`
- Unichain WETH: `0x4200000000000000000000000000000000000006`

## 1. Frontend failure did not imply contract failure

The project website returned 451, but the Unichain contracts remained callable. The recovery therefore used direct RPC simulation and wallet-signed transactions rather than the website.

Before sending anything, each state-changing call was simulated/read first.

Relevant calls observed and successfully used:

```solidity
claimMany(uint256[] tokenIds)
unstake(uint256[] tokenIds)
```

For the tested NFT, `claimMany([tokenId])` and `unstake([tokenId])` both passed gas estimation after the lock expired.

Observed selectors:

- `claimMany(uint256[])`: `0x925489a8`
- `unstake(uint256[])`: `0xe449f341`

The unstake selector/function mapping is no longer only inferred: the wallet-signed unstake transaction succeeded and returned the NFT to the owner wallet.

## 2. Safe execution pattern

The preferred operational method was a small local HTML page served from localhost. It connected to browser wallets and never requested or stored a private key.

Recommended local serving pattern:

```bash
cd ~/Downloads
python3 -m http.server 8080
```

Then open the local page through `http://localhost:8080/...`.

The wallet connector should use EIP-6963 discovery plus legacy injected-provider fallback so the user can explicitly choose among installed EVM wallets such as OKX Wallet, Rabby, MetaMask, Phantom, Backpack or Binance Wallet rather than relying only on `window.ethereum`.

Important lesson: using only `window.ethereum` can cause MetaMask to capture the connection when multiple browser wallets are installed.

## 3. Exit order that worked

The successful order was:

1. connect the correct owner wallet on Unichain;
2. verify the chain ID is 130;
3. verify the owner wallet and target token locally/onchain;
4. simulate `claimMany([tokenId])`;
5. wallet-sign `claimMany([tokenId])`;
6. wait for confirmation;
7. simulate `unstake([tokenId])`;
8. wallet-sign `unstake([tokenId])`;
9. wait for confirmation;
10. call `ownerOf(tokenId)` and confirm the NFT is back in the owner wallet.

Both claim and unstake completed successfully onchain.

## 4. OpenSea failure after unstake

After the NFT returned to the owner wallet, OpenSea showed:

> Not enough ETH on Unichain to cover the network fee

This error persisted after cache clearing/reconnection.

The native ETH balance was already vastly higher than the actual gas consumed by the earlier claim/unstake transactions, so the message was investigated instead of assuming a real gas shortage.

### 4.1 Check ownership and OpenSea approval

First verify:

```solidity
ownerOf(tokenId)
isApprovedForAll(owner, conduit)
```

The NFT was owned by the expected wallet, but OpenSea conduit approval was initially `false`.

The approval transaction used:

```solidity
setApprovalForAll(
    0x1E0049783F008A0085193E00003D00cd54003c71,
    true
)
```

Gas estimation passed, the wallet signed the transaction, and the final onchain state became:

```text
isApprovedForAll(owner, OpenSeaConduit) = true
```

OpenSea still displayed the same “not enough ETH” message after approval, so missing approval was not the final cause of the UI block.

## 5. Gas reality check

Recent real UNICRED marketplace settlements on Unichain were inspected. A seller-side Seaport settlement used only a small fraction of the owner wallet's available native ETH.

Therefore the displayed OpenSea warning was not consistent with the actual network fee required by comparable Seaport transactions.

The tested owner wallet had approximately `0.00025 ETH` before the workaround, while the displayed offer value was `0.0004 WETH`.

## 6. Workaround that succeeded

A small amount of native ETH was added so that the wallet's native ETH balance exceeded the numerical value of the `0.0004 WETH` offer (target balance was roughly `0.0005 ETH`).

After this top-up, OpenSea allowed the seller-side Seaport settlement and the transaction succeeded.

### Interpretation

**Confirmed:**

- the wallet already had enough ETH for normal Unichain gas before the top-up;
- NFT ownership was correct;
- OpenSea conduit approval was correctly set to `true`;
- the same OpenSea error persisted after approval;
- adding native ETH until the balance exceeded the offer's numerical value was followed by a successful Seaport settlement.

**Not proven:**

- the exact internal OpenSea frontend/backend condition that generated the warning;
- whether OpenSea was literally comparing native ETH balance to WETH offer value.

Accordingly, this should be documented as an **observed workaround**, not a proven OpenSea implementation bug.

## 7. Sale settlement verification

The final Seaport settlement succeeded (`status = 1`) and emitted the ERC-721 transfer from the owner wallet to the buyer.

Offer amount:

```text
0.000400 WETH
```

Settlement breakdown observed onchain:

```text
OpenSea/platform fee (1%): 0.000004 WETH
Creator fee (5%):          0.000020 WETH
Seller proceeds:           0.000376 WETH
```

This exactly reconciles:

```text
0.000400 - 0.000004 - 0.000020 = 0.000376 WETH
```

After settlement, the owner wallet interacted with WETH separately; personal post-sale wallet movements are intentionally excluded from this record.

## 8. Reusable checklist

When a project's staking frontend disappears but the contracts still exist:

1. identify the chain and actual staking/NFT contract;
2. recover the owner wallet and token ID locally, without publishing them;
3. derive/verify the claim and unstake functions from historical successful calls or verified ABI;
4. use `eth_call` / gas estimation before every state-changing action;
5. sign only through the user's wallet plugin; never put private keys into a web page or repository;
6. claim rewards first;
7. unstake second;
8. verify `ownerOf()` after unstake;
9. before marketplace sale, check `isApprovedForAll()` for the marketplace conduit;
10. if a marketplace says gas is insufficient, compare the wallet balance against real same-chain settlement gas before adding funds;
11. if a small balance threshold appears to block the marketplace UI, use the smallest practical top-up and label the result as a workaround unless the root cause is independently proven;
12. after the sale, verify the NFT transfer event and proceeds onchain.

## Privacy / repository rules

Do not commit:

- owner wallet addresses tied to the user;
- NFT token IDs if they can trivially deanonymize the wallet;
- the user's transaction hashes;
- private keys, seed phrases, wallet-export files or browser profiles;
- local helper pages containing personal wallet constants.

Public protocol contracts, generic method signatures, selectors and reproducible troubleshooting logic are safe to retain.
