# Meme Wallet Cluster Analysis Spec

Updated: 2026-10-06
Status: MANDATORY for Meme / new-token CA analysis
Scope: Solana first; same logic applies to EVM where equivalent evidence exists.

Purpose: fix a gap in the previous Meme analysis flow. Raw Top10/Top20 holder concentration is not enough. Every serious Meme analysis must reconstruct wallet relationships before calling holder structure "clean", "distributed", or "healthy".

This is an analysis/research rule only. It does not create monitoring, automation, live validation, or production trading authority.

## 1. Mandatory rule

For every Meme/new-token CA analysis that reaches holder-structure review, wallet-cluster analysis is a required step, not an optional deep dive.

The analysis must answer both questions:

1. What does the holder table look like if every address is treated independently?
2. What does the holder table look like after related wallets, public infrastructure, LP/vault/escrow addresses and probable execution clusters are separated correctly?

Do not call holder structure "clean", "distributed", "healthy", or "low concentration" before the cluster step is complete.

If cluster reconstruction cannot be completed, write:

`WALLET_CLUSTER_UNRESOLVED`

and preserve that uncertainty in the final risk rating.

## 2. Minimum input set

At minimum collect:

- current mint supply;
- Top20 token accounts;
- real owner of every Top20 token account;
- LP / AMM pool / vault / escrow / CEX / protocol/public infrastructure classification;
- first observed acquisition of the token for material holders;
- funding source before first acquisition where available;
- direct token transfers between material holders;
- direct SOL/USDC/quote-asset transfers between material holders;
- common batch-funding transactions;
- common signer / authority / nonce relationships;
- synchronized buy/sell events;
- common destination / consolidation wallets;
- known shared routers, fee payers, copy-trading infrastructure and exchange hot wallets.

For very new tokens, the first minutes/hours of holder history matter more than only current balances.

## 3. Special-address normalization comes first

Before wallet clustering, classify and remove or separately label non-free-holder accounts:

- LP / AMM pool;
- protocol vault;
- escrow / Streamflow / vesting contract;
- lock contract;
- burn account;
- CEX hot wallet;
- bridge / router;
- platform fee payer;
- copy-trading / execution infrastructure;
- market-maker operational wallet when confirmed;
- creator/dev/treasury;
- ordinary EOA / trading wallet.

A token account is not the same thing as a wallet owner. Always resolve the real owner first.

## 4. Cluster edge taxonomy

Every relationship used in clustering should have an explicit edge type.

### 4.1 Strong ownership/control evidence

`COMMON_FUNDER_EOA`
- multiple wallets funded from the same ordinary EOA or small non-public wallet;
- stronger when funding occurs in the same batch, similar amounts, shortly before launch/trade.

`COMMON_SIGNER`
- same non-public signer/authority repeatedly authorizes actions for multiple wallets.

`COMMON_NONCE_OR_CONTROL_ACCOUNT`
- multiple wallets use the same non-public nonce/control account or equivalent execution authority.

`BATCH_FUNDING`
- one transaction or tightly grouped transactions funds several wallets that then enter the token together.

`COMMON_CONSOLIDATION`
- multiple wallets later send proceeds/tokens back to one non-public destination.

These edges can support a probable same-controller cluster when combined with independent behavior evidence.

### 4.2 Direct relationship evidence

`DIRECT_TOKEN_TRANSFER`
- holder A directly transfers the target token to holder B.

`DIRECT_QUOTE_TRANSFER`
- A directly sends SOL/USDC/other quote asset to B.

Direct transfer proves a relationship, but not automatically same ownership. It must not be silently upgraded to `same person` without additional evidence.

### 4.3 Behavioral/execution evidence

`SYNC_BUY`
- wallets buy within the same second/slot or a very narrow window.

`SYNC_SELL`
- wallets sell within the same second/slot or a very narrow window.

`IDENTICAL_SIZE`
- exact or highly distinctive matching input/output size.

`SAME_EXECUTION_PROGRAM`
- same router/bot/execution program.

`REPEATED_SYNC_BEHAVIOR`
- synchronized behavior repeats across multiple tokens or multiple episodes.

Behavioral evidence can establish a probable common execution strategy/bot cluster, but does not by itself prove common beneficial ownership.

### 4.4 Shared-infrastructure edges that must NOT be treated as ownership evidence

`COMMON_FUNDER_CEX`
- same Binance/OKX/KuCoin/Coinbase/etc. hot wallet.

`SHARED_INFRA`
- same public router, DEX program, FOMO/copytrade fee payer, launchpad authority, relayer, RPC/paymaster or public bot service.

`SAME_POOL`
- interaction with the same AMM/pool.

`SAME_POPULAR_ROUTE`
- same Jupiter/Raydium/PumpSwap/Orca/etc. path when that route is broadly used.

These can create Bubblemaps/graph visual links without implying common control.

## 5. Evidence levels

### CONFIRMED_RELATION
Use when a direct on-chain relationship is confirmed, for example A directly transfers target tokens to B.

This means the wallets are related. It does not necessarily mean one person controls both.

### PROBABLE_CONTROL_CLUSTER
Use only when at least two independent strong indicators support common control, for example:

- common non-public EOA funder + synchronized trading;
- batch funding + repeated synchronized buys/sells;
- common signer + common consolidation;
- direct transfers + common funder + coordinated exits.

### PROBABLE_EXECUTION_CLUSTER
Use when wallets appear to be driven by the same bot/strategy/operator but beneficial ownership is not proven, for example:

- same second/slot;
- identical distinctive order size;
- same execution program;
- same prior batch transaction;
- repeated coordinated behavior.

### SHARED_INFRA_ONLY
Use when the apparent link is explained by public infrastructure or CEX funding.

### UNRESOLVED
Use when evidence is insufficient or conflicting.

Never convert `PROBABLE_EXECUTION_CLUSTER` into `PROBABLE_CONTROL_CLUSTER` without additional ownership/control evidence.

## 6. Required concentration metrics

Every completed holder analysis must report, when data permits:

1. `RAW_TOP10_PCT` — raw leaderboard including everything.
2. `EX_LP_TOP10_PCT` — Top10 after removing LP/AMM.
3. `EX_SPECIAL_TOP10_PCT` — after removing LP, protocol vault, escrow, CEX/public infrastructure as appropriate.
4. `LARGEST_CONFIRMED_RELATION_GROUP_PCT` — directly related wallets, without claiming same owner.
5. `LARGEST_PROBABLE_CONTROL_CLUSTER_PCT` — strongest same-controller estimate.
6. `LARGEST_PROBABLE_EXECUTION_CLUSTER_PCT` — bot/strategy cluster when ownership is unresolved.
7. `DEV_LINKED_CLUSTER_PCT` — creator/dev/treasury-linked free supply.
8. `CLUSTER_ADJUSTED_TOP10_PCT` — concentration after accepted control clusters are merged and special addresses are normalized.
9. `UNRESOLVED_MATERIAL_HOLDER_PCT` — material share that cannot yet be classified safely.

If a metric cannot be computed, use `UNAVAILABLE` or `UNRESOLVED`; do not invent it.

## 7. Required per-cluster record

For each material cluster record:

- cluster id;
- wallet addresses;
- current balances;
- combined balance and supply percentage;
- edge types;
- first target-token acquisition time for each wallet;
- first-acquisition type: market buy / transfer / airdrop / unknown;
- quote amount and route when available;
- funding source before acquisition;
- direct transfers among cluster members;
- synchronized buys/sells;
- common destination/consolidation behavior;
- public-infrastructure/CEX explanations checked;
- confidence: CONFIRMED_RELATION / PROBABLE_CONTROL_CLUSTER / PROBABLE_EXECUTION_CLUSTER / SHARED_INFRA_ONLY / UNRESOLVED;
- evidence transaction signatures.

## 8. False-positive controls

The following are not enough by themselves to merge wallets into one controller:

- same CEX hot wallet funding;
- same DEX/router;
- same public fee payer;
- same launchpad;
- same minute buy;
- same token transfer program;
- same token account creation program;
- same popular bot/copytrade infrastructure;
- Bubblemaps color/line alone;
- social-media accusation alone.

Bubblemaps/GMGN/FOMO/other analytics are discovery tools. Their graph must be reconstructed from raw transactions before a material conclusion is accepted.

## 9. Hidden-concentration patterns to detect

Flag these patterns explicitly:

### WALLET_SPLITTING
One holder sends chunks of the token into multiple wallets so the leaderboard appears more distributed.

### BATCH_SNIPER_CLUSTER
Multiple wallets are pre-funded or funded in one batch and buy in the same launch window.

### COORDINATED_EXECUTION
Multiple long-lived wallets execute the same strategy at the same time; ownership unresolved.

### DEV_DISTRIBUTION_CLUSTER
Creator/dev/treasury directly distributes tokens or quote asset to several material holders.

### CONSOLIDATION_CLUSTER
Multiple wallets later return token/proceeds to one non-public address.

### PUBLIC_INFRA_FALSE_CLUSTER
A visual cluster is explained by a CEX/router/fee payer/public execution service and should not be counted as insider concentration.

## 10. GOMO regression example — 2026-10-06

Token:
`9XKzy4KahcZaGJPJtz1PtqGPB3CiseoBrx7TcQhEpump`

This example exists to prevent future regressions; balances can change after the observation time.

### Example A — synchronized execution cluster

`FseZVHyF8dmB79mvw1BX2EEAJiioBgEFTaZgnka2iqLA`
`F9tv2SN5WE4cezCGbZTU4v1Tu2MSFtxcSGxPTqDm3J8N`

Observed facts:
- both entered GOMO at 2026-10-05 04:48:41 ICT;
- both used the same execution program;
- both used exactly `1.190665697 SOL` as a distinctive input size;
- both histories also contain the same earlier batch transaction `EZqyAbQtMwxw4YECmwghm9MiYmEvNRVMhoMLJDZEscLFUXrDHGLuidUHXSLYvWXVPQL4GtUw5hMQP6dBxwA5CbQ`.

Classification:
`PROBABLE_EXECUTION_CLUSTER`

Do not automatically call them the same owner until funder/control evidence closes the loop.

### Example B — direct token relationship / wallet splitting candidate

`6TypmyduvHENRuS5F5Wiwk6MqKt1tLw6vkynLuT7Dguv`
→ `6APTEtXf3m7K9L3R1cRs6X6sF2zG1YT392rEG3cvuba7`

Confirmed transaction behavior:
- sender created the recipient GOMO token account;
- sender directly transferred `10,000,000 GOMO` to the recipient;
- sender retained a material GOMO balance afterward.

Classification:
`CONFIRMED_RELATION` + `WALLET_SPLITTING_CANDIDATE`

Do not claim same beneficial owner without more evidence, but do not treat the two holdings as fully independent either.

### Example C — another direct split

`FsYRQmoe8zCupamq3Jw4j1oZb1HnAFt3HcXZb8Dgggfi`
→ `G7txkS3VsxFEGXbxNFS1jpSQELsNzt3kJVC9siJZSrvG`

Confirmed:
- sender created the recipient GOMO ATA;
- direct transfer of `10,000,000 GOMO`;
- sender retained GOMO afterward.

Classification:
`CONFIRMED_RELATION` + `WALLET_SPLITTING_CANDIDATE`.

### Example D — public-infrastructure false link

`AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51`

Known from prior raw-transaction reconstruction as FOMO execution/fee-payer infrastructure.

If several holders touch this address, that alone must be classified as:
`SHARED_INFRA_ONLY`

not as common ownership.

### Example E — CEX-funding false link

A known exchange hot wallet funding multiple traders is not enough to merge those traders. Common KuCoin/Binance/etc. origin is `COMMON_FUNDER_CEX`, not common-controller proof.

## 11. Final risk-language rule

Allowed only after cluster analysis:

- `holder structure appears distributed after cluster adjustment`;
- `largest probable control cluster is X%`;
- `no material dev-linked cluster found`;
- `wallet cluster remains unresolved`.

Do not say:
- `Top10 is low, so distribution is healthy`;
- `Bubblemaps shows links, therefore scam`;
- `same funding source, therefore same owner`;
without the required classification and evidence.

## 12. Standard Meme output integration

For every serious CA analysis, the holder section must now contain:

`Raw holder concentration`
→ `Special-address normalization`
→ `Confirmed direct relations`
→ `Probable control clusters`
→ `Probable execution/bot clusters`
→ `Shared-infrastructure exclusions`
→ `Cluster-adjusted concentration`
→ `Dev-linked concentration`
→ `Unresolved material share`

If this sequence is not performed, holder analysis is incomplete.

## 13. Mission consequence

A token may not be upgraded to a high-confidence setup solely because raw Top10/Top20 looks distributed.

Material unresolved wallet clustering is a risk factor and can keep the token at `WATCH` even when mint/freeze permissions, liquidity and headline holder concentration look good.

Conversely, visual graph clustering alone must not force a `SCAM` label when the links are explained by CEX/public infrastructure.
