# Crypto Daily 2026-11-23 16:21 Asia/Bangkok — bounded collector PARTIAL

mode: COLLECTOR_ONLY
report_sent_today: CONFIRMED
gmail_sent_id: 1a206fec44c5cfa7
canonical_path: crypto-daily/reports/daily/2026/2026-11/2026-11-23.md
no_repeat_delivery: true
rules_blob_sha:
  PIPELINE_CONTRACT.md: 29ffbc1d32ca87a744d2990e8d55639ebb84a6f9
  EDITORIAL_RULESET.json: 2ed51528d230508ae4e0015762b1d60c9d72e299
  REPORT_SPEC.md: 2e70414c8fdb8d23a292cc3bf7797425a403e179
  REPORT_ACCEPTANCE.md: 1925f143dce75efa40d3b3ddf3f2899dfb355cbd
  COLLECTOR_SPEC.md: 7c0983fbed7f8b6185118e2cb51dd5da8c88a98c
  SECURITY_SOURCE_POLICY.md: 7266f425982aebb695c2ad4b718bf8d3d0b363bf
  DELIVERY_RUNBOOK.md: 2712ab51fee99d47c9a3b07da3883784dca51d07
  state/daily-event-ledger.json: 0b4acf861b4a8a755759b5c6ab3d2cf5469609b1

## Delivery and dedupe
Gmail Sent search (2026-11-23 date) returned exactly one formal Crypto Daily, 1a206fec44c5cfa7. Git canonical fetched; this was a manual-recovery edition. Do not send another email for 2026-11-23. Other 2026-11-22 formal Sent ID 1a2034b8ca694f60. No production unattended recovery proven. Git research directory listed successfully via connected GitHub REST contents.

## Discovery receipts
checked_at: 2026-11-23T16:21+07:00 (approximate execution window, web results checked during this invocation)
method: fresh English web/news index batched queries; these are discovery only, not proof of official primary checks.

- cross-market ETF: https://www.theblock.co/news/markets/2026-11-23-spot-bitcoin-etfs-shed-1-79-billion-in-past-week-444857 published 2026-11-23; candidate weekly US spot BTC ETF outflows ~1.79bn USD, requires Farside/issuer confirmation and cross-day novelty. VERIFYING, not asserted as final.
- protocol bridge security: https://www.theblock.co/news/markets/2026-11-23-spot-bitcoin-etfs-shed-1-79-billion-in-past-week-444857 mentions Nov22 Fusionist ACE bridge exploit in linked headline; candidate family_key fusionist:ace-bridge:2026-11-22, material_version secondary_headline_unverified_v1; source_published_at 2026-11-22; independent official issuer/advisory and original chain TX needed. VERIFYING, do not assert exploit amount as confirmed.
- Chainflip: https://cryptoticker.io/en/chainflip-hack-12-million-vaults-drained-signing-key/ published 2026-11-23; same incident family already reported 2026-11-22, potential bounty deadline but no first-party changed state verified. EXCLUDE_UNCHANGED.
- wallet malware: https://www.kriptofoni.com/en/iphone-crypto-wallet-malware-47-countries/ published 2026-11-23; claims Confiant iPhone wallet-recovery phrase targeting; no original Confiant research verified in this run. VERIFYING, not confirmed.
- security VMware: https://shattered.io/vmware-vcenter-zero-day-cve-2026-123890-armory-castle-cvss-9-8-kev-nov-23/ published 2026-11-23; secondary claim CVE-2026-123890, require Broadcom/CISA primary proof and actual vulnerability/patch versions. VERIFYING.
- Arkham/Lookonchain search yielded only older secondary BTC transfer stories, e.g. https://financefeeds.com/bitcoin-whales-dump-nearly-500m-into-coinbase/ dated Oct28; no new TXID independently verified. ONCHAIN_SOURCE_GAP.
- Galxe shutdown prior user action already separately sent; no new official material_version verified. EXCLUDE_UNCHANGED.
- macro and policy search broad; no official regulator document independently read this run. MACRO_POLICY_SOURCE_GAP.
- spot and derivatives official Binance API not fetched this run; latest stored canonical quote is ~12:58 ICT and MUST NOT be called 16:20 live price. SPOT_DERIVATIVES_SOURCE_GAP.
- Farside official issuer page not fetched this run. ETF_SOURCE_GAP.
- six security lanes security/web_runtime_rce/web_pki_tls/ai_package_supply_chain/cloud_secrets_identity/backend_framework_auth: no independent first-party source receipts in this run. SECURITY_SOURCE_GAP (all six); generic news query is insufficient.
- TGE/Early/NFT, third_party_ipo_access, official_x: official primary source not retrieved; SOURCE_GAP, BROWSER_SESSION_UNAVAILABLE.

## Outcome
PARTIAL_SOURCE_GAPS. No new Gmail/App notice. Candidate discovery only. No change to original task, no cron, no paid API, no trading or other monitoring action. Do not claim QA_PASS or CI_PASS. Next normal collector should prioritize first-party confirmation of Fusionist ACE and wallet-malware claims and six security lanes, with prior seven-day sent family/version dedupe.
