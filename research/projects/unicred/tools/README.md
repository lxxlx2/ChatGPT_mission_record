# UNICRED recovery helper

Public helper: `unicred-recovery-helper.html`

Purpose:
- connect an injected EVM browser wallet via EIP-6963 / legacy injected providers;
- switch to Unichain mainnet (chain ID 130);
- enter the user's own UNICRED Token ID;
- call `ownerOf(tokenId)`;
- simulate and submit `claimMany([tokenId])`;
- simulate and submit `unstake([tokenId])`.

The helper contains no user wallet address, private key, seed phrase, API key, or historical transaction hash.

## Local use

Download `unicred-recovery-helper.html`, then from the download directory run:

```bash
python3 -m http.server 8080
```

Open:

```text
http://localhost:8080/unicred-recovery-helper.html
```

Select the installed wallet extension, enter Token ID, then execute each action separately. Every state-changing action requires an explicit wallet confirmation.

Public UNICRED NFT/staking contract:

`0xf60de24f228dc7ca6ff025958d2ee3a956ed88e5`

OpenSea approval and marketplace troubleshooting are intentionally documented separately from this recovery helper.