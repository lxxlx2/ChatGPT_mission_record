# HTX / Huobi Global SA: Binance, Bybit, Bitget cross-CEX account-access restrictions

Event key: bitget:restricted-counterparty-htx-direct-enforcement:2026-10-16
Report date: 2026-10-17 Asia/Bangkok
Severity: HIGH user-funds-access / compliance-risk, NOT a confirmed hack or price-driven liquidation.
Scope: existing CEX security, policy and funds provenance; no new monitored project/automation.
Miss: Oct 17 manual Crypto Daily Gmail 1a14886106251842 omitted material Oct16 Bitget enforcement update despite broad CEX coverage; corrected full edition Gmail 1a1488f7e5801fe5.

## Chronology with first-party vs secondary separated

1. Binance first-party English notice published 2026-08-14 11:00, HTX (Huobi Global SA) effective 2026-08-23: no longer process direct/indirect transactions involving named crypto-asset providers; attempted transfers MAY be held for compliance review, impacted wallets MAY be restricted. https://www.binance.com/en/support/announcement/detail/af2be67dc03c4673b4f56c42db948253 . VERIFIED original English text.
2. Bitget first-party English notice published 2026-08-15 03:15, HTX included in effective 2026-08-23 group: direct/indirect transfers MAY be reviewed/rejected, accounts MAY face restrictions, terms breach MAY lead to closure. Explicit origin, destination and intermediaries. https://www.bitget.com/support/articles/12560603892077 . VERIFIED original English text.
3. Bybit original legal list page exists at https://www.bybit.com/en/legal/additional-terms-and-disclosures/Restricted-Counterparty-List , but only title was retrievable directly at investigation. Independent English review published 2026-09-27 and updated 2026-10-13 preserved Sep23 v2 and confirms HTX named; risks include holds, account closure and positions closed, with conditions tied to Bybit terms. https://digitalcompliance.pro/blog/en/bybit-restricted-counterparties . List content: PARTIAL_PRIMARY_READBACK + SECONDARY_VERIFIED, do not imply fresh Oct16 Bybit change.
4. Newly material Bitget delta: https://www.tokenpost.com/news/regulation/33530 English article published Oct16 18:21 EDT (Oct17 05:21 Asia/Bangkok), attributes a Bitget announcement Oct16 11:56 UTC; restricted list grows to about 20 entries, adding Tokenspot, Xeltox/cryptomus.com/heleket.com, BitBank3. Reports DIRECT listed counterparty transfers rejected and involved accounts terminated, versus INDIRECT possible review/rejection and restrictions, and may terminate account under terms, not automatic closure for all indirect links. Oct16 current Bitget original English full statement/official social text was not directly readable: SOURCE_GAP. Do not upgrade stricter modal to firsthand proof. Another English corroborating report: https://www.ababnews.com/en/news/b6aaa7fe-1d0e-4c2e-afd6-0d09500b9c85 .
5. Context underlying regulatory actions from Chainalysis' original research on UK's Oct8 added entities: https://www.chainalysis.com/blog/uk-sanctions-cryptomus-heleket-tokenspot/ . This explains some new entity names but does not prove that every HTX user is sanctioned or that all user coins are frozen.

## Material significance / user caution
- A sanctioned / restricted COUNTERPARTY and indirect SOURCE OF FUNDS differs from an individual token's listing. A person possessing BTC/USDT/coins formerly traded on HTX is not automatically banned solely because the asset is the same type.
- Rejection/frozen deposits, risk-control holds, trading restrictions and possible account termination affect usability of funds and may matter more immediately than token price. They can also affect practical rebalancing/withdrawals. Do not instruct circumventing AML/sanctions rules with fresh wallets, mixers or bridges.
- Users considering transfers involving these services should check latest official help center and official support BEFORE sending. Already held transfers should be documented by Tx hash, source proof and official ticket.
- Personal user balances, a pending transfer or a frozen account: NOT VERIFIED. No assertion of direct user exposure.
- Source gap (Bitget Oct16 primary) must persist for future retrieval; do not infer absence of news because 8/15 official page wasn't updated.
- Regression enforcement: CR-23/collector/security-source-policy, multi-CEX by counterparty, and CR-22 section-local numbering across complete daily/resend workflows.
