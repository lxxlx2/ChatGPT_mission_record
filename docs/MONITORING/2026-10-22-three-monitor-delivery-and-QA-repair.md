# 2026-10-22 — Three existing monitors: actual missed delivery, QA cardinality bug, TGE cache lag

Timezone: Asia/Bangkok.
Scope: the three original ChatGPT scheduled monitors ONLY; no new task, no user Mac deployment, no GitHub scheduled crawler, no paid API or additional monitored project.
Original tasks remain enabled with schedules unchanged.

## 1. Verified actual failures

- Gmail Sent list checked for target date 2026-10-22 before both sends: **no** normal/formal/repair Crypto or US-stock mail for Oct22. Both Git canonical paths missing.
- US Stock 2026-10-22 08:38 attempt terminal: `us-stock-daily/runs/2026-10-22/083826-final.md`. `status: BLOCKED_WITH_REASON`, stage `gmail_send`, literal provider error `This tool call was blocked by OpenAI's safety checks. Please double check what you are sending.`. This is a genuine platform rejection, not proven curable via prompt adjustments.
- Crypto prepared manifest `crypto-daily/delivery-pending/2026-10-22.json` and cloud CI `delivery-qa/2026-10-22.json` initially mismatched manifest SHA because the publisher later revised the report. Reject that stale CI PASS for any subsequent draft.
- Crypto machine editorial gate had a second concrete defect: `scripts/editorial_gate.mjs` required exactly one source receipt per lane while a legitimate multi-source check recorded two Farside funds, multiple security sources and Reuters market/macroeconomic sources under their proper lanes. The old code failed with `DISCOVERY_LANE_RECEIPT_MISSING` for capital_flows, early_nft, security, macro and forward_catalysts, despite real results. Deleting extra source evidence would be a bad workaround.

## 2. Actual code repair and fresh cloud QA

- Fixed `crypto-daily/scripts/editorial_gate.mjs` to accept ONE OR MORE independent source receipts per required lane, validating every receipt. A source_gap in one provider is retained as a warning even when another same-lane provider is readable; fake `checked` with missing result URLs still fails. Code commit `fb4a449aee0b307e19e2dd9a06e259e2f844c37e`.
- Added regression tests for multiple capital-flow/ETF sources and same-lane checked+source_gap security; malformed duplicate still fails. Commit `fd1d4ae8fb792e7c3bf9e1ddebcd0e6e0510cb95`.
- Ran actual current Git source in JavaScript with the Oct22 manifest: QA_PASS, **13 headings, 31 items, 2 global highlights, 29 event families, 17 actual source receipts, only security chapter blank with explanation**; actual 19/19 editorial regression tests passed in JS. This in-session JS verification is not misrepresented as GitHub Runner execution.
- Triggered GitHub push-only cloud QA on newest manifest via `958ed2559836083abe6f976518f55a3807b6fff1`. Cloud Git receipt `crypto-daily/delivery-qa/2026-10-22.json` now: `status: EDITORIAL_QA_PASS`, `validated_at: 2026-10-22T06:33:18.579Z`, `manifest_blob_sha=f21c940011de990a4c4874a183c322ecb0ecbfdc`, `rules_blob_sha=df26ea064cc6feae99e345f6efaf402485b0482c`, `editorial_gate_blob_sha=5761607601d0934bb87c33124e4a9c69676a127c`, each exact-match verified by fresh Git fetch immediately before delivery.
- Remaining Crypto actual source gaps: Arkham/onchain exhaustive labeled BTC scan, some Early/NFT dynamic and X pages, specialist real-time security X. These are PARTIAL source coverage, not claims of no events. Cloud editorial QA verifies structure/classification and declared receipts, NOT exhaustive external discovery.

## 3. Verified exact full formal Gmail resends

### US Stock
- Subject: `美股每日晨报｜2026-10-22｜正式补发`.
- To: `lxx.run688@gmail.com`.
- Gmail Sent ID: **`1a1624d4f0c25b08`**.
- Based on real 05:40 original `us-stock-daily/delivery-pending/2026-10-22.md`; 12 headings, 39 each-section numbered items, source-timed full Oct21 US stock close and earnings/macro. Actual Gmail Sent body readback EXACT, recipient/subject verified.
- Git actual Sent body canonical `us-stock-daily/reports/daily/2026/2026-10/2026-10-22.md`. Commit **`484dda78ccd818439398c6c7f05acb5ee538d0c0`**, Git fetch after commit EXACT.
- News checks include Reuters Oct21 US close, primary Meta quarterly IR, Tesla IR, New Mexico DOJ $25B Meta court penalty, France 10yr 5% development. Historical earnings and current stock-price reaction correctly separated.

### Crypto
- Subject: `Crypto Daily Brief｜2026-10-22｜正式补发`.
- To: `lxx.run688@gmail.com`.
- Gmail Sent ID: **`1a1625138e98951e`**.
- Delivered full existing current-Git 13-chapter editorial manifest, **31 items, 2 independently screened Top5 stories**, verified 3-boundary SHA current cloud QA and in-session re-QA before send. Market quotes clearly show 09:24 Bangkok-time rolling Binance sample, not falsely claimed current to second; Oct21 US ETF rows explicitly labeled as partial if issuer columns unavailable.
- Actual Gmail Sent readback full body EXACT after terminal whitespace normalization and recipient/subject match; canonical `crypto-daily/reports/daily/2026/2026-10/2026-10-22.md`, commit **`c6ae66d60ee1861f411bb86b82852225e0e3eb76`**, Git readback EXACT.
- Neither formal report is to be re-sent automatically again for Oct22. No fraudulent Git SUCCESS before a genuine Gmail Sent ID.

## 4. Third monitor: correct silent decision, but still incomplete source health

- Most recent VERIFIED durable terminal before remediation `airdrop-tge-monitor/runs/2026-10-22/120405-final.md`: 12:04 BKK, `PARTIAL`, shard0, 5 candidates, 0 ACTION_GATE passed, 6 source gaps. Original 13:01 `130143-attempt.md` is only an attempt, NOT a completed terminal. Do not convert it to source coverage success.
- Genuine coverage-complete success still `2026-10-10 07:52:16 BKK`. Some first-party entitlement notices unavailable (Concrete extra USDC, NeoSoul StandX beneficiary-specific, Cambria migration original, StandX X source, several issuer channels). Previously delivered Surf/StandX events still have no confirmed NEW Tier A/B entitlement delta.
- Existing user-facing event email remains SILENT because `ACTION_GATE=0`, not an automatic-email send failure. NeoSoul general eligibility checker cannot establish StandX community allocation. Research gaps MUST stay visible in Git without repeating unverified claim emails.
- Fixed stale `airdrop-tge-monitor/state/current.md` header from Oct22 05:58 to latest verified Oct22 12:04 PARTIAL, linking 13:01 unfinalized attempt separately, preserving all historical state text. Commit **`ed5711f07742fe505903aa2ee8527a6bc0f96bf1`**, exact readback verified.

## 5. Scheduled prompt fixes and production boundaries

- Updated each of the three original automation prompts IN PLACE, schedules and enabled status preserved; prompts are bootstrap instructions reading latest Git rules and run finals dynamically instead of hardcoded old daily states.
- Crypto: preserve multi-source receipts and warn on provider gaps; before Gmail require genuine current CI receipt SHA match for manifest+rules+editorial gate, plus actual content/source QA, and date-specific Gmail Sent dedupe.
- US Stock: on next scheduled 07:40, attempt normal authorized Gmail only after full QA and dedupe, then read back exact body+Git; when platform safety checks reject, record actual blocked stage, not false success, do not bypass.
- TGE: execute original HH:00 urgent+one shard and fairness from terminal record, not stale state header/attempt-only; after each durable final update `state/current.md`. No action no alert.
- **Not yet proven**: that the next actual AUTOMATIC scheduled send succeeds, that all relevant external security/whale sources are covered, or that provider-level Gmail safety filtering is fixed. Successful manual connected Gmail resends and GitHub cloud lint are not those proofs.

## 6. Acceptance of next normal scheduled delivery

For each US Stock/Crypto next regular date, independently verify Gmail Sent date and time, complete report content and real source timestamps, Git final canonical exact body match, and no stale CI bound to a different manifest. For TGE, verify post-run terminal final, timestamped source coverage by shard, actual Tier A/B action/no-action and state cache synchronization. Leave production state PARTIAL/UNPROVEN until then.
