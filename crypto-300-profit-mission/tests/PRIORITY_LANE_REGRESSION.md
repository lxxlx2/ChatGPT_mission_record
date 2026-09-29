# $300 Mission Priority-Lane Regression Cases

Updated: 2026-09-29
Scope: Frank + Monster/meme + NFT

## Frank
- FR-LIVE-01: source primary works -> scan cursor to finalized head and persist audit.
- FR-LIVE-02: primary Alchemy app returns 429/unavailable -> retry once on configured backup app; if both fail, preserve cursor and overall run is partial_failure.
- FR-LIVE-03: passive ATA/reward/claim/transfer/deposit -> never BUY.
- FR-LIVE-04: active DEX swap with wallet signer + opposing quote/token deltas -> BUY/SELL.
- FR-LIVE-05: ambiguous possible swap -> UNRESOLVED_TX; cursor cannot cross gap.
- FR-LIVE-06: PRECONFIRM/SUSPECTED/EXIT event persists before Gmail; Gmail readback required for delivery.
- FR-LIVE-07: quiet run after pending event cannot erase pending delivery.
- FR-LIVE-08: overall Mission cannot be healthy success without Frank audit.
- FR-HIST-01: full 30D pagination has no silent gap.
- FR-HIST-02: every active token ends in WATCH/PRECONFIRM/SUSPECTED/HFT/STALE/rejected bucket.
- FR-HIST-03: historical observer uses actual :29 cadence with no future information.
- FR-HIST-04: filtered token later >=3x appears in miss-controls report.

## Monster / meme
- MON-01: every due scan bulk-screens full eligible Binance USD-M universe.
- MON-02: every shortlist candidate is deep-checked or persisted DEFERRED_SHORTLIST.
- MON-03: each due scan reserves at least two deep-check slots for oldest deferred when two or more exist.
- MON-04: runtime budget is max 5 deep-checks; current top movers use remaining slots.
- MON-05: candidate cannot disappear without promote/reject/expire/data-gap terminal reason.
- MON-06: BTW historical starvation fixture must fail old behavior and pass new queue behavior.
- MON-07: every due scan persists coverage counts: universe, shortlist, deep_checked, deferred_added, deferred_remaining, state transitions, gaps.
- MON-08: 19:29 coverage summary exists even when no IGNITION fires.
- MON-09: model thresholds remain frozen V2.1; runtime coverage changes do not rewrite historical setup prices.

## NFT
- NFT-01: every hourly :29 Mission cycle executes one bounded NFT discovery lane.
- NFT-02: every cycle persists an NFT discovery receipt even when zero candidates qualify.
- NFT-03: lack of X/scanner access is explicit unavailable/partial, never “no opportunities”.
- NFT-04: candidate must pass canonical identity before actionable alert.
- NFT-05: copied/fake issuer/domain/contract/payment mismatch -> reject.
- NFT-06: official PREMINT within 24h can be candidate before collection contract is live.
- NFT-07: live mint needs identity + at least two opportunity signals before alert.
- NFT-08: ended/sold-out/stale mint -> no new ACTION.
- NFT-09: material contract/security issue after alert -> RISK_RETRACTION.
- NFT-10: one daily coverage report summarizes discovered/verified/rejected/alerted/source gaps.
- NFT-11: no new scheduler; lane stays inside existing $300 task.

## Overall completion
- CORE-01: core final remains early durable proof.
- CORE-02: authoritative overall health is a post-lane completion artifact.
- CORE-03: overall success requires Frank PASS + NFT PASS/PARTIAL_WITH_RECEIPT + Monster PASS when due or explicit NOT_DUE.
- CORE-04: missing priority-lane artifact => partial_failure, never success.
