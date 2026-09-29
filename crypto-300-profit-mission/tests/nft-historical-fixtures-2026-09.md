# NFT Historical Discovery Fixtures — September 2026

Purpose: regression controls for the $300 Mission NFT radar.
These fixtures test discovery/state classification. Marketplace discovery alone does not satisfy the canonical-issuer alert gate.

| ID | Historical item | Evidence available to discovery | Expected radar result |
|---|---|---|---|
| NFT-H01 | Jack Butcher “8” X Money open edition | high-profile creator, user-captured first-party post, short window, very high engagement; contract initially not known | PREMINT_CANDIDATE after first-party identity verification; contract absence alone must not hide it |
| NFT-H02 | Mintropolis Genesis | OpenSea Sep 2026 mint, 5,555 supply, public mint evidence | DISCOVERED; current replay on Sep 29 = STALE/ENDED, no new alert |
| NFT-H03 | Misfits NFT | OpenSea Sep 2026 Robinhood-chain mint stages | DISCOVERED_PENDING_IDENTITY unless canonical issuer link independently verifies; no marketplace-only alert |
| NFT-H04 | Mnodes | OpenSea Sep 2026, 4,444/4,444 sold out | STALE_SOLD_OUT; no new mint alert |
| NFT-H05 | Sundazed | OpenSea Sep 16-17 mint, fully ended | STALE_ENDED |
| NFT-H06 | The Sweepers | OpenSea page exposes mint metadata but public schedule ended Sep 23 | date/state conflict must resolve to STALE/NO_ACTION on Sep 29; page label alone cannot override deadline |
| NFT-H07 | Arc x OpenSea: The Arc Begins | very large free mint, 543k items, mint ended | historical DISCOVERED; current STALE_ENDED |
| NFT-H08 | Magic Caps | OpenSea Sep 2026, public stage shown through Nov 12 | CURRENT_DISCOVERY_CANDIDATE, but actionable alert requires canonical issuer + opportunity gate |
| NFT-H09 | JeanPhil Punks | OpenSea Sep 24-28 public stage | historical DISCOVERED; current STALE_ENDED |
| NFT-H10 | Archetype | OpenSea Sep 16, 700/700 sold out | STALE_SOLD_OUT |
| NFT-H11 | Collectr September edition | OpenSea open edition, active mint | CURRENT_DISCOVERY_CANDIDATE; canonical creator/project verification required before alert |
| NFT-H12 | Smilers NFT | OpenSea Sep 9-19 mint | STALE_ENDED |

Deterministic safety fixtures:
- copied creator account with near-identical name but wrong root domain -> REJECT_IDENTITY;
- canonical X but payment address/domain conflicts with official mint page -> REJECT_CONFLICT;
- all external sources unavailable -> PARTIAL_SOURCE_GAP, never NO_CANDIDATE;
- official PREMINT within 24h and contract not live yet -> may pass PREMINT after issuer identity + >=2 opportunity signals;
- one KOL post only -> DISCOVERY_ONLY / no alert.

Source controls:
- repository: `crypto-daily/research/2026-09-21/manual-jack-butcher-x-money-open-edition.md`
- OpenSea collection pages discovered in the Sep 29 smoke pass for Mintropolis Genesis, Misfits NFT, Mnodes, Sundazed, The Sweepers, Arc x OpenSea, Magic Caps, JeanPhil Punks, Archetype, Collectr and Smilers NFT.
