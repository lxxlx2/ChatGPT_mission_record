# Local Meme Wallet Cluster Tool

Status: local read-only research utility.

Goal: turn the mandatory wallet-cluster specification into a repeatable local command without paid data providers.

## Data sources

Primary evidence source is finalized Solana JSON-RPC. No paid provider is required.

The Dashboard/CLI now supports multiple free endpoints because public Solana RPC is rate-limited. Default mainnet order is:

- `https://api.mainnet.solana.com`
- `https://api.mainnet-beta.solana.com`
- `https://rpc.ankr.com/solana`

The client paces requests per endpoint, honors `Retry-After`, cools down nodes that return 403/429/5xx, rotates to the next free endpoint, and keeps the existing local SQLite cache.

Overrides:
- `SOLANA_RPC_URL=<primary>`
- `SOLANA_RPC_URLS=<comma-separated endpoint list>`

Raw finalized RPC remains authoritative for ownership, authorities and transaction evidence.

The tool uses:
- getTokenSupply
- getTokenLargestAccounts
- getMultipleAccounts
- getSignaturesForAddress
- getTransaction

All calls are read-only.

Raw transaction evidence is passed through the existing conservative swap classifier. Third-party PnL, Bubblemaps colors and social accusations are not accepted as ownership proof.

A local SQLite RPC cache is used so historical transactions do not need to be downloaded repeatedly.

## Fast default run

From `crypto-300-profit-mission/local-agent`:

    PYTHONPATH=. python3 scripts/meme_wallet_cluster.py <MINT>

Default deep scan:
- resolves Top20 token-account owners;
- deep-scans the first 10 holders;
- inspects up to 30 target-token-account signatures per deep holder;
- inspects up to 12 owner signatures for pre-acquisition SOL funding;
- caches historical transactions locally.

This is deliberately bounded so a public free RPC remains usable.

For a deeper pass:

    PYTHONPATH=. python3 scripts/meme_wallet_cluster.py <MINT> \
      --deep-holders 20 \
      --history-per-holder 100 \
      --funding-lookback 50

## Outputs

The tool writes:
- `cluster-report.json`: machine-readable evidence and metrics;
- `cluster-report.md`: compact human-readable report.

Required metrics:
- RAW_TOP10_PCT
- EX_LP_TOP10_PCT
- EX_SPECIAL_TOP10_PCT
- LARGEST_CONFIRMED_RELATION_GROUP_PCT
- LARGEST_PROBABLE_CONTROL_CLUSTER_PCT
- LARGEST_PROBABLE_EXECUTION_CLUSTER_PCT
- DEV_LINKED_CLUSTER_PCT
- CLUSTER_ADJUSTED_TOP10_PCT
- UNRESOLVED_MATERIAL_HOLDER_PCT

## Trust model

The tool intentionally fails conservative.

It may automatically establish:
- direct token-account transfer relation;
- exact same funding source when visible in bounded raw history;
- same funding transaction;
- same non-owner signer;
- same-second/near-synchronous buy/sell;
- identical quote amount;
- shared execution-program evidence.

It does not automatically call a wallet CEX/dev/LP merely because it looks familiar. Those roles require explicit local labels or independently verified evidence.

The default registry is `config/meme_special_addresses.json`. Add only addresses whose role has a verifiable source.

Automatic cluster rules follow `meme/WALLET_CLUSTER_ANALYSIS_SPEC.md`:
- direct transfer alone -> CONFIRMED_RELATION, not same owner;
- probable control requires multiple independent strong/control + behavioral indicators;
- execution clusters never imply beneficial ownership;
- shared public infrastructure does not count as a control edge.

## Important limitation

A free public RPC is not an indexed historical analytics service. Bounded history can miss old funding, consolidation and multi-token coordination. If material evidence is missing, the correct result is unresolved, not a guessed clean-holder conclusion.

## Verified address labels

Global infrastructure labels live under `addresses`. Token-specific dev/LP/treasury/escrow labels belong under `tokens.<MINT>.addresses` so an address is not accidentally treated as the same role for every token.

Strict normalized concentration fields stay `UNRESOLVED` until that token's registry explicitly sets:

    "normalization_complete": true

Before that point the tool still emits `KNOWN_EX_*` metrics, but they are labelled as partial known-label calculations rather than complete holder normalization.

Example:

    "tokens": {
      "<MINT>": {
        "normalization_complete": true,
        "addresses": {
          "<POOL_AUTHORITY>": {"role":"AMM_POOL","source":"verified pool account"},
          "<CREATOR>": {"role":"CREATOR","source":"verified create transaction"}
        }
      }
    }

This gate is intentional: an unlabelled CEX hot wallet or LP authority must not be silently treated as an ordinary independent holder.


## Dashboard integration

The localhost Mission Meme dashboard now has two top-level views:

- `Frank 信号`: existing live Frank/Mission Control view.
- `CA 链上查询`: interactive wallet-cluster research.

From any current Frank candidate, `链上查询` carries that CA directly into the research tab.

The research view supports three bounded presets. All three resolve Top20 token accounts to actual owners. The difference is how many owners receive historical deep scan and how far that scan goes:

- `快速`: deep-scan first 6 unique owners; up to 12 target-token-account signatures plus 8 pre-acquisition funding signatures per scanned owner. Use for first-pass screening.
- `标准`: deep-scan first 10 unique owners; up to 30 target-token-account signatures plus 12 pre-acquisition funding signatures. Default formal analysis.
- `深度`: deep-scan all Top20 unique owners; up to 100 target-token-account signatures plus 50 pre-acquisition funding signatures. Use for important projects, suspected wallet splitting or hidden clusters; it puts the most pressure on free RPC.

Queries are asynchronous so a long public-RPC scan does not block Frank signal rendering. Only one cluster job runs at a time to avoid turning the free Solana RPC into an uncontrolled fan-out.

Reports are persisted under the existing Mission Control root:

    <control-root>/cluster-reports/<MINT>/

The web result separates:

- strict concentration metrics;
- Top20 resolved owner rows;
- confirmed relation groups;
- probable control clusters;
- probable execution clusters;
- unresolved relation evidence;
- RPC/cache coverage and limitations.

The UI never converts an `UNRESOLVED` strict metric into a numeric value.


## Research report v2

The CA page is no longer only a wallet-cluster table. It produces a structured Meme research report with separate evidence layers.

Chain-authoritative section:
- token program;
- supply/decimals;
- mint authority;
- freeze authority;
- metadata update authority when parsable from the mint account;
- Top20 token account -> actual owner;
- bounded first confirmed market acquisition for deep-scanned owners;
- pre-acquisition SOL funding when visible;
- direct transfers / common funding / signer / consolidation / synchronized execution clusters.

Secondary market section:
- DexScreener token-pairs API is used only for current market/pair metadata: name/symbol, reference price, market cap, DEX/pair, liquidity, volume, buys/sells and price change;
- Jupiter official quote remains the source for a current read-only $30 USDC executable quote and price impact;
- neither source is allowed to override raw-chain ownership or authority facts.

Conclusion section:
- chain permission status;
- holder / wallet-cluster status;
- current market snapshot;
- explicit unresolved narrative status;
- next checks such as exact-CA official recognition, creator-fee claim, creator buy, lock/treasury relationship and verified ATH/key levels.

The tool does not automatically claim that a public X/social link means the narrative owner adopted the exact CA. Creator claim/buy/lock or official recognition needs separate first-party or on-chain evidence.

The persisted JSON and Markdown reports carry the same separation between chain facts, secondary market data, inferred cluster conclusions and unresolved narrative claims.
