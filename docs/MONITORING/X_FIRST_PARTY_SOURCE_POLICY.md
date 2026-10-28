# X/Twitter first-party discovery — three EXISTING monitors (2026-10-28)

**Goal:** add original verified-account X announcements as *additional* evidence. Never reduce existing issuer websites/docs, SEC/IR, official CEX support, GitHub releases, onchain transaction proofs, Reuters/AP, business news, Arkham/Lookonchain, TGE source registry or historical user-rights intermediaries. Do not create a new timed automation, GitHub cron, paid X API or a local Mac/browser daemon. Do not take any actions on behalf of the user's X account.

## Reality of browser access

A connected read-only Browser tool offers `list_tabs({})` and `get_tab_context({tabId})` in supported *current interactive ChatGPT sessions*. The user often leaves an authenticated x.com tab open, but this **does NOT prove that the scheduled automation has access to the same session/browser/tabs**. Do not claim access or silently assume that the user desktop remains on and connected to scheduled runs. A separate browser tab shown by a prior conversation is NOT a binding for a future scheduled turn.

For EVERY actual scheduled source check:
1. At most once per relevant bounded slot, inspect whether the scheduled executor actually exposes the Browser tool and the required relevant x.com tab. If yes, read only the visible public post text and exact permanent post URL/account/time, record `browser_session=AVAILABLE`; do not rely on scrolling indefinitely or "home timeline" ranked recommendations. A visible personalized feed is NOT comprehensive coverage of target handles.
2. If Browser tool/tab cannot be accessed, record `browser_session=UNAVAILABLE` with actual tool outcome, then use bounded public `site:x.com/<official-handle>/status` search, direct public original permalinks where available, verified-account issuer announcements and official website/blog/docs/SEC/IR fallback. X HTTP403/429 or unreadable JavaScript -> `X_SOURCE_GAP`, NOT `NO_EVENTS`. A search result snippet/third-party repost cannot be represented as full firsthand X content.
3. Record each relevant source receipt in the EXISTING Git run manifest: `monitor,run_at,source_lane,issuer,verified_account,post_url,post_published_at,checked_at,browser_session,read_mode,read_status,source_tier,exact_claim,official_crosscheck_url,confidence,discovery_decision,event_key,material_version`. Do not invent a post ID or date if missing. No account login/cookies/tokens/password collection, no DM, repost, like, follow, wallet sign, transaction, payment or private browsing.
4. Only a newly verifiable event (eligibility, deadline, issuer filing, IPO offer, market-structure announcement, significant security exploit) can be escalated. Signal discovered on X must go through normal event family dedup, official origin validation, materiality and rights gates. X engagement/likes alone are sentiment evidence, not actionable rights.
5. Source failures affect only that lane. All other existing sources continue; no shortened report and no blanket abort for a failed X read.

## Existing Crypto Daily monitor — extra original posts

Conditional official X read for CEX exchanges (Kraken, Binance, Bitget, Bybit, Gate, OKX), Anthropic/other actual IPO issuer, Cambria @playcambria and existing relevant issuers and reliable onchain observers. During current collector windows, check at most a bounded set of event-centric official account posts and direct issuer links, not all followed accounts. Crypto `EDITORIAL_RULESET.json` requires an `official_x` receipt (checked or SOURCE_GAP) and a separate `third_party_ipo_access` receipt; never claim Anthropic allocation open from a Kraken/SpaceX precedent or a derivatives listing. The only appropriate high-urgency action is an issuer-backed NEW venue application deadline/eligibility or official security action, handled via original authorized Gmail policy.

## Existing US Stock Daily monitor — extra original posts

Official company/investor X/SEC/IR press distribution (Anthropic issuer, Nasdaq, underwriters, reliable exchange IPO-access announcements if equity relevant), plus market regulator/major earnings sources. SEC EDGAR, issuer IR and established market data **remain controlling**. Track issuer IPO stage changes `PUBLIC_S1/AMENDMENT/PRICING/TRADING` and third-party exchange allocation offers as separate event families. Classify crypto exchange **derivatives** as derivative, not share allocation. Use IPO mini-section under existing §5 only for verified material new progress. Record an X source receipt even when Browser unavailable; then primary SEC/IR fallback.

## Existing TGE hourly monitor — extra original posts, bounded

At HH:00 check actual available original X issuer posts for urgent known projects + **one** deep-shard set plus bounded cross-shard lifecycle leads; keep original shard fairness and all existing official docs and Tier-A/B rights sources. `@playcambria` is the existing Cambria Registry Shard 3 issuer and the Base $RSGP milestone is a *different family* from Abstract/Blast Duel Arena recovery and earlier RSGP Genesis opt-in. Do not suppress a newly issuer-verified cross-chain token/claim by destination chain; do not re-alert unchanged Oct29 milestone already mailed (Gmail ID `1a1812a1f6802ecb`). Direct X may discover a deadline, but a wallet CLAIM alert still requires TGE ACTION_GATE and official permission/status; no third-party-only alert.

## Compliance test / fail states

- `PASS`: actual relevant source read receipts or transparently bounded `X_SOURCE_GAP` with official fallback, exact source identity, correct routing and no false actionable claim.
- `FAIL`: asserting a logged-in X tab was scanned without a real scheduled-tool receipt; using a previous chat tab ID in scheduled run; one generic X timeline representing all specified official handles; third-party repost treated as original issuer; using old Abstract stake notice to suppress new Base issuer rights; treating ANTHROPICUSDT perps as IPO allocation; inventing product launch or sending duplicate alert.
- **Production acceptance remains pending** until a future real scheduled run leaves inspectable receipts. A Git policy file or successful interactive Browser read is not proof of unattended authenticated X scanning.
