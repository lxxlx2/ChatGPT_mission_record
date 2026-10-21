# Major onchain-event missed by 2026-10-21 Crypto Daily

Status: CONFIRMED_ARKHAM_ANALYTICS / MISSED_IN_EMAIL / NEEDS_NEXT_NEW_MATERIAL_REPORT_ACCOUNTING
Checked: 2026-10-21 Asia/Bangkok
event_key: btc:clifton-collins:2026-10-20:tranche-5
family_key: btc:clifton-collins
material_version: tx:eb0bde50049e924590a1812af2d2699c13d513415d3f03bbe3d10f316b3d6756
asset: BTC
quantity: 500
contemporaneous_estimate_usd: 41500000
source_tier: PRIMARY_ANALYTICS_ATTRIBUTION (Arkham's own address labels/research, not governmental ownership proof)
primary_research: https://info.arkm.com/research/clifton-collins-fifth-500-btc-40m-transfer-from-drug-dealers-lost-stack
tx_explorer: https://arkm.com/explorer/tx/eb0bde50049e924590a1812af2d2699c13d513415d3f03bbe3d10f316b3d6756
entity: https://arkm.com/explorer/entity/clifton-collins
published_at_as_displayed: 2026-10-20 1:25 pm EST (site label; US DST/time-zone abbreviation ambiguity retained)
reported_receiver: Arkham-tagged Coinbase Prime deposit wallet

## Verified at source vs not established

Arkham's fresh Oct20 research identifies another distinct 500 BTC movement from a Collins-tagged wallet to a Coinbase Prime-labeled address, the fifth 500 BTC transfer in 2026. Earlier tranches included March, May, July and August, so comparing transfer *amount* alone and deduping 500 BTC as an existing event is wrong. Its estimate is USD 41.5 million at that time. Cumulative amount moved is 2,500 BTC; estimated 3,500 BTC remain out of the initial 6,000 BTC linked to the case.

Arkham's txid deep link above is available, but the linked dynamic explorer's transaction inputs/outputs were not independently decoded by this investigation. Label ownership and ultimate custody are therefore attributed to Arkham. Earlier March seizure matched an Irish police announcement; Arkham explicitly says no equivalent law enforcement announcements accompany the subsequent four transfers, including this fifth. Government execution of this specific transfer, actual sale of BTC, realized USD proceeds, and current recipient account beneficial owner: UNCONFIRMED. Coinbase Prime *deposit* is not proof of exchange sale.

## Exact omission and priority

The 2026-10-21 delivered Crypto Daily `crypto-daily/reports/daily/2026/2026-10/2026-10-21.md` (Gmail ID `1a15c49e3ff24c51`) has 13 chapters and 65 numbered items. None contains `Collins` or Arkham's 500 BTC fifth movement, despite dedicated sections for institution/exchange and whale onchain flows. Multiple already-reported Qubic, Cysic, JPMD, HTX and StandX threads occupied repeated numbered items without verified novel event deltas.

Correct story classification: user-facing material onchain whale/labelled government-linked custody transfer; Category Section Five plus at most one compact top highlight. NOT evidence of sale; NOT an individual buy/sell recommendation. Event must be accounted for as a fresh fifth tranche, distinct by txid, not suppressed by family label or the four older 500 BTC tranches.

No second Oct21 full daily is authorized by this investigation; original Sent/Git canonical remains immutable. Future genuine new updates use the distinct event key, verified facts and material delta, not boilerplate repetition.

## Regression / publisher requirements

- Source discovery: English Arkham Research and its X posts, onchain-labeled transfers via Lookonchain/Onchain Lens, official explorer links; bounded lookup and explicit source-gap where unavailable. No paid Arkham subscription or GMGN API.
- Internal default review threshold: labelled BTC transfer >= USD 10,000,000, major exchange/government-related movement, or otherwise high materiality. This is a discovery trigger, not a trade signal or alert-only threshold.
- Gate: `crypto-daily/scripts/daily_event_gate.mjs` with distinct `event_key`, `family_key`, `material_version`, source URL/timestamp and `material_delta`; no repeats without delta and no more than two top+deep numbered mentions of the same event.
- Idempotency: successful Gmail Sent and canonical date must never be silently overwritten or emailed a second time without an explicit user-requested corrected edition.

## Resolved: actual full corrected edition sent after user approval

The initial original Oct21 email omitted this fifth tranche; user explicitly requested a resend. The corrected, complete 13-section email was sent as Gmail ID 1a15c6d25715d6ca with the Collins-specific TXID and the Arkham original-source attribution, then independently read back from Gmail and archived byte-for-byte at crypto-daily/reports/daily/2026/2026-10/2026-10-21.md (commit da084972cdd5b05ef2e6bfcd343ff6eda867ee67). Earlier Sent ID 1a15c49e3ff24c51 remains a superseded historic artifact. The event ledger has now marked this exact fifth tranche delivered; only distinct newer on-chain transactions or material verified changes merit another daily mention.

Scanner: crypto-daily/scripts/arkham_primary_discovery.mjs plus 12 offline Node test definitions, with 13 equivalent pure-source V8 fixture validations passed; no full production or live HTTP autonomous verification claimed.
