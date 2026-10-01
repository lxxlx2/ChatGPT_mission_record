# Crypto Daily Acceptance Gate

Updated: 2026-10-01 Asia/Bangkok
Status: canonical pre-delivery QA

The official Crypto Daily can be sent only when all hard gates pass.

## CR-01 Fixed structure
Exactly the REPORT_SPEC 13 first-level sections in canonical order.

## CR-02 24h input manifest
Before drafting, build a delivery manifest covering the previous 24h:
- hourly research/final artifacts seen;
- missing scheduler hours;
- market/derivatives facts;
- security receipts/candidates;
- TGE/claim material state;
- institutional/ETF/whale flows;
- protocol/infrastructure/ecosystem candidates;
- Early/Meme/NFT discovery candidates;
- macro/cross-market inputs;
- active user private-market rights.

Missing hourly artifacts must be visible in the manifest. Missing data cannot be silently interpreted as no event.

## CR-03 Market core
BTC/ETH/SOL current 24h price/range/volume when available, plus material relative-strength outliers.

## CR-04 Security carry-forward
Every material security candidate from the prior 24h is either:
- included in Section 9 after fresh verification; or
- listed in the internal audit as omitted with concrete reason.
Major-CEX account-security receipts follow SECURITY_SOURCE_POLICY.md.

## CR-05 TGE/rights freshness
Section 7 consumes only current/actionable TGE/rights state. User-known/closed/refunded/expired events are not recycled as new information. When possible, use the canonical TGE monitor state rather than rediscovering stale events.

## CR-06 Early/Meme/NFT coverage
Section 8 may say no material candidate only if the relevant discovery lane actually ran or the manifest records its source gap. A lane that did not run cannot be rewritten as “no opportunities”.

## CR-07 Institutional/on-chain coverage
Material ETF/fund/exchange/whale/market-structure changes are checked and separated from stale historical context.

## CR-08 Macro/cross-market coverage
Material rates/oil/USD/equity/geopolitical drivers are checked when relevant.

## CR-09 Deduplication
Unchanged prior-day conclusions are not repeated as new. Carry-forward is allowed only when still decision-relevant and clearly identified as ongoing or when a material delta exists.

## CR-10 No recovery downgrade
09:00 primary, recovery, manual resend and correction all use the same full 13-section content contract. A short digest/patch can never silently become the official report.

## CR-11 Delivery integrity
- Gmail send + readback;
- canonical GitHub archive + readback;
- exact body equality after YAML metadata;
- prior incomplete/superseded same-day versions recorded.

## CR-12 Quality-collapse guard
Compare against trailing 5 latest complete formal reports:
- if body length < 70% of median OR numbered-item count < 70% of median, QA fails unless a genuine low-event reason is documented and CR-01 through CR-09 all still pass;
- provider failure, recovery mode or time pressure are never sufficient exceptions.

## CR-13 User-visible cleanliness
Monitoring-health details, run failures, “QA passed”, internal classification mechanics and persistence plumbing stay out of the report body.

The following belong only in the internal run audit, never in the user-visible report:
- why an item was omitted;
- why an old item is not repeated;
- why a closed/refunded item is no longer monitored;
- why a section was intentionally left sparse;
- source-coverage/process explanations;
- statements such as “不重复”“不填充”“不占用监控”“不写具体数字”“此前已提醒所以不再处理”“本报告其余类别不做填充”.

If there is genuinely no decision-relevant update for a section, use one short neutral line such as `无高置信新增。` and nothing more.

## CR-14 One logical event = one user-visible item
Before delivery, every numbered item must be assigned an internal `event_key`.

Rules:
- one logical event should normally appear as one numbered item;
- do not split one event into a factual bullet plus a second bullet whose only purpose is to qualify/caveat the first;
- status + caveat + next checkpoint for the same event must be merged into the same item;
- two adjacent items with the same `event_key` are an automatic QA failure unless they are truly independent actions for the user.

Example of a failure: `Bitget plans USDT recovery` as item 1 and `do not treat planned recovery as completed` as item 2. These are one event and must be one item.

## CR-15 Cross-section event dedupe
Build an internal pre-send event map: `event_key -> sections/items`.

A logical event gets one primary section. Repeating it in another section is allowed only when the second occurrence adds a distinct decision dimension that cannot be expressed in the primary item, for example:
- Section 9: the security incident itself and current remediation state;
- Section 11: a new future dated checkpoint that materially affects user action.

A repeat is forbidden when it merely restates the same status, disclaimer, or conclusion. If the same `event_key` appears more than once without a non-empty `distinct_dimension`, QA fails.

## CR-16 Item decision-value gate
Every numbered user-visible item must contain at least one of:
- a new or materially changed verified fact;
- a current quantitative market/state observation;
- a concrete user-relevant risk/opportunity/action;
- a specific future checkpoint with date/time/threshold.

An item fails if its primary meaning is only:
- “nothing changed”;
- “we chose not to repeat this”;
- “we do not have enough data so we will not write it”;
- “this item is closed and therefore not monitored”;
- “we intentionally did not fill this section”.

Those are audit facts, not report content.

## CR-17 Mandatory pre-send lint
Before Gmail send, create an internal lint result and require every check to PASS:

1. `structure_lint`: exact 13 headings/order.
2. `meta_prose_lint`: no user-visible process/no-op phrases from CR-13.
3. `same_event_item_lint`: no duplicate adjacent/same-section `event_key` items.
4. `cross_section_dedupe_lint`: repeated `event_key` requires a distinct decision dimension.
5. `decision_value_lint`: every numbered item passes CR-16.
6. `stale_rights_lint`: closed/refunded/expired/already-completed rights do not occupy user-visible bullets unless a new material change occurred.
7. `freshness_lint`: stale future tense / already-passed times are refreshed or removed.

Any FAIL means `QA_FAIL_NO_SEND`. The task must rewrite and re-run lint. It is forbidden to send first and explain the defect afterward.

The internal run audit must store only the PASS/FAIL result and offending item identifiers; the lint commentary itself must not appear in the email.

## State machine
DRAFT -> INPUT_MANIFEST_READY -> PRE_SEND_LINT_PASS -> QA_PASS -> GMAIL_SENT_READBACK -> GITHUB_ARCHIVED_READBACK -> DELIVERED

If Gmail succeeds but GitHub archive fails, repair GitHub only and do not resend.
