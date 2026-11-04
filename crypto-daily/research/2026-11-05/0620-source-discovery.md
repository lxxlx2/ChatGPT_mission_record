{
  "run_date": "2026-11-05",
  "slot": "06:20",
  "timezone": "Asia/Bangkok",
  "status": "PARTIAL_SOURCE_GAPS",
  "purpose": "bounded discovery only; no Gmail delivery in collector slot",
  "rules_sha": {
    "PIPELINE_CONTRACT.md": "29ffbc1d32ca87a744d2990e8d55639ebb84a6f9",
    "EDITORIAL_RULESET.json": "2ed51528d230508ae4e0015762b1d60c9d72e299",
    "X_FIRST_PARTY_SOURCE_POLICY.md": "20abfed8a287307bb2d6017b3b9e7ff509bbeebe"
  },
  "gmail_recent_sent_ids": [
    "1a1a4869ded9decd",
    "1a19f3b5e950e16d",
    "1a19a135a76e95b8",
    "1a194e8623464edf",
    "1a18fc6328b668e2",
    "1a18a9d5e767548d",
    "1a185794e63c022c"
  ],
  "monthly_october_sent": "1a1a496a0bdc257d",
  "new_candidates": [
    {
      "family_key": "ipo_access:bitget:anthropic-rant",
      "event_key": "ipo_access:bitget:anthropic-rant:2026-11-03",
      "material_version": "bitget-official-2026-11-03-vip-nov05-public-nov10",
      "primary_section": 7,
      "decision": "INCLUDE_CANDIDATE_NEEDS_RIGHTS_QA",
      "source_url": "https://www.bitget.com/academy/what-is-anthropic-ipo-on-bitget-rant-benefits-fees-how-to-participate-2026-guide",
      "published_at": "2026-11-03",
      "checked_at": "2026-11-05T06:20+07:00",
      "facts": "Bitget official describes VIP1-7 2026-11-05 16:00 UTC+8 through Nov9, public Nov10, rANT tokens rather than direct shares, $100 minimum, 12% VIP / 5% public allocation fees; issuer IPO schedule provisional; Bitget disclaims Anthropic authorization/partnership. Bangkok VIP opening 07:00 Nov5. Check actual application page and regional eligibility before claiming executable access."
    },
    {
      "family_key": "cloud:railway:spoofed-ip-blocking",
      "event_key": "cloud:railway:spoofed-ip-blocking:2026-11-04",
      "material_version": "railway-status-2026-11-04T22:03Z",
      "primary_section": 9,
      "decision": "WATCH_OR_INCLUDE_IF_NEW_TO_LEDGER",
      "source_url": "https://status.railway.com/",
      "published_at": "2026-11-04T22:03Z",
      "checked_at": "2026-11-05T06:20+07:00",
      "facts": "Railway reports network blocks due to forged source IP scanning, explicitly no evidence of Railway customer infrastructure compromise; service access partially affected."
    },
    {
      "family_key": "runtime:node:2026-11-security",
      "event_key": "runtime:node:2026-11-security-planned",
      "material_version": "node-announcement-2026-11-03-planned-nov11",
      "primary_section": 9,
      "decision": "WATCH_NO_PATCH_YET",
      "source_url": "https://nodejs.org/en/blog",
      "published_at": "2026-11-03",
      "checked_at": "2026-11-05T06:20+07:00",
      "facts": "Node.js announces planned November 11 security releases, highest severity HIGH; no fixed version yet."
    }
  ],
  "source_receipts": [
    {
      "lane": "capital_flows",
      "url": "https://farside.co.uk/btc/",
      "status": "READ",
      "note": "IBIT missing must mean partial"
    },
    {
      "lane": "capital_flows",
      "url": "https://farside.co.uk/eth/",
      "status": "READ",
      "note": "ETHA missing must mean partial"
    },
    {
      "lane": "ai_package_supply_chain",
      "url": "https://docs.litellm.ai/blog",
      "status": "READ"
    },
    {
      "lane": "cloud_secrets_identity",
      "url": "https://status.railway.com/",
      "status": "READ"
    },
    {
      "lane": "cloud_secrets_identity",
      "url": "https://www.connectwise.com/company/trust/advisories",
      "status": "READ"
    },
    {
      "lane": "backend_framework_auth",
      "url": "https://github.com/laravel/framework/security/advisories",
      "status": "READ"
    },
    {
      "lane": "web_runtime_rce",
      "url": "https://www.php.net/archive/2026.php",
      "status": "READ"
    },
    {
      "lane": "web_runtime_rce",
      "url": "https://nodejs.org/en/blog",
      "status": "READ"
    },
    {
      "lane": "security",
      "url": "https://blog.btcpayserver.org/",
      "status": "READ"
    },
    {
      "lane": "early_nft",
      "url": "https://opensea.io/blog",
      "status": "READ"
    },
    {
      "lane": "early_nft",
      "url": "https://www.artblocks.io",
      "status": "READ"
    },
    {
      "lane": "third_party_ipo_access",
      "url": "https://www.bitget.com/academy/what-is-anthropic-ipo-on-bitget-rant-benefits-fees-how-to-participate-2026-guide",
      "status": "READ"
    },
    {
      "lane": "official_x",
      "url": "https://x.com",
      "status": "BROWSER_SESSION_UNAVAILABLE",
      "note": "No browser tab read attempted; public search and official Bitget page used"
    }
  ],
  "unverified_lanes": [
    "spot_live",
    "derivatives_live",
    "onchain_txid",
    "tge_registry",
    "macro_primary",
    "web_pki_tls_current",
    "official_x_authenticated"
  ],
  "delivery": "NO_SEND_COLLECTOR_WINDOW",
  "note": "Partial scan only; do not represent as complete CR32/CR33 coverage."
}