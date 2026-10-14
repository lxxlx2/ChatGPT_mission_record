# C02 exact mint identity research and engineering record

Date: 2026-10-14 Asia/Bangkok. State: IMPLEMENTING / BUSINESS_ACCEPTANCE_PENDING / NOT_DEPLOYED.

## Verified baseline and investigation

`gh pr view 46 --repo lxxlx2/ChatGPT_mission_record --json headRefName,headRefOid,baseRefName,title,body,state` confirmed OPEN head `e2fdb48e1e7d98a3f39d3153997b3b76f4d413ae`, branch `dev/frank-ca-c01-c08-unified-research-no-default-quote-20261013`. New branch `codex/frank-ca-c02-token-identity-20261014` was created from that exact SHA in an isolated worktree. Existing X-revenue dirty files were preserved. Main independently fetched: `656098f5bc845a234557b4cf6d14c57023f3b79b`.

Read `MISSION_SPEC.md`, `meme/ca-analysis-unified-accuracy-acceptance.md`, PR46 body/comments and actual cluster.py, market.py, server.py, app.js. The requested two design/TODO documents are absent from PR46 and current main; they were read from `origin/design/frank-ca-multiperson-completion-plan-20261013` (`002a9648dff95d18df916c40582101f12d977fd3`). These documents define C02 exact mint→metadata→pair, independent review, browser evidence and separate Mac release gates.

Old path: market.name/symbol are DexScreener labels; SPL Metaplex metadata not fetched; recursive updateAuthority lookup lacks exact metadata structure. Repeated labels appear in preview and summary. DEX accepted a self-quote pair. Exact quote-side rejection had no auditable direction reason.

## Frozen implementation design

Only generic CA research changes. Exact mint remains each RPC/market query and cache/job anchor. Chain mint owner/type/initialized state, Token-2022 self metadata pointer+embedded mint and Metaplex PDA owner/key/embedded mint/string bounds are checked. Metadata authorities are read from their precise record, never recursively guessed. External Token-2022 metadata interfaces are explicitly UNCONFIRMED (not implemented), and concurrent inaccessible metadata sources block full verification. Issuer supplied chain labels do not establish official affiliation.

Four independent statuses: identity_status, market_match_status, name_display_status, conflict_status. All eligible pair labels are reconciled, not only the highest-liquidity label. Any name/symbol or chain authority-source conflict gives TOKEN_IDENTITY_CONFLICT and no selected display name. UI shows source records and attempted metadata accounts. Metadata missing/failure cannot promote DEX/social names to chain identity. Display label deduplicates equal name/symbol, preserving both raw fields. Quote-side/base mismatch is excluded because priceUsd describes base, never silently inverted.

No changes to frozen Frank decisions, Gmail, notification, production SQLite, LaunchAgents, trading, strategy, or deployment. Shared server.py/app.js changes are confined to CA preview/report. No merge and no Mac service restart.

## Actual evidence

See `evidence/c02/official-rpc-attempts.json`: real finalized public official RPC getAccountInfo requests, responses, UTC epoch timestamps and slots. `raw-market-responses.json` captures exact DexScreener requests, response payloads and SHA256. `real-case-results.json` contains normalized/reconciled outputs. These captures are historical evidence, not live prices on later reopening.

- Actual Agency mint `7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump` recovered by verifying 20 base64 report chunks and hashes from `origin/evidence/frank-ca-local` SHA `b9fb6e6df9032a0e6f49c1274bb4ba61c9e4c2da`. Minimal identity projection saved in `agency-archived-identity.json`; no holder traces republished. Official RPC slot 456664257 confirms Token-2022 mint, self pointer, name=symbol=Agency, updateAuthority=null. DEX base matches exact mint; display now Agency once.
- Screenshot transcription at PR42 used `…VXPpump`. Official RPC returns null for that different address (slots 456664258/259). Never correct addresses by name. This is a documented transcription discrepancy, not a second valid token.
- Actual distinct same-name mint `4cdbUv2X2TUymvdBYSo4DrKXChMVwSnHHZjMyWhBpump` independently queried at slots 456664478/479. Another Agency `H4UH4ypR3nTqDHJPJurYL2GsDWzotKzzU1Kmj3XiqFkj` at slot 456664477. Discovery via DEX search only supplies candidates; official RPC metadata independently verifies labels.
- Ordinary SPL USDC `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`: finalized mint slot 456664257 and Metaplex account slot 456664259. Metadata name USD Coin, symbol USDC, authority `2wmVCSfPxGPjrnMMn7rchp4uaeoTqN39mXFC2zhPdri9`.
- WSOL queried as an additional ordinary SPL case. Missing Metaplex account for actual Agency is a real missing-source response; embedded Token-2022 metadata remains available.
- Fault/conflict/owner/mint/truncation tests use explicitly synthetic or counterfactual mutations of these saved responses. They are algorithm verification, not claims that a real issuer currently has a conflict/RPC outage. No fabricated live chain data.

## Commands and validation (update with exact final CI)

Environment: isolated `/tmp/mission-ca-c02-venv`, Python 3.12.14, pytest 8.3.5, numpy 2.3.3. System Python lacked pytest; that tooling failure was not counted as RED. Real RED: PYTHONPATH=crypto-300-profit-mission/local-agent python -m pytest tests/test_ca_market_c02_red.py against unchanged PR46 source: 2 assertion failures saved `red.txt`.

First full regression: 1 failed, 1412 passed, 3 skipped (numpy absent). Incomplete old metadata fixture expected null authority as verified; retained and changed to UNCONFIRMED because missing mint/name/symbol/pointer is not proof. Installed numpy for complete final regression. Saved `full.txt` preserves failure.

Current focused: 11 passed. Actual app.js Node renderer executes six official saved cases sequentially, preview, conflict and HTML escaping: PASS. PDA implementation independently compared against solders 0.27.1 Pubkey.find_program_address on 512 deterministic keys: all match (`pda-crosscheck.txt`). solders is development verification only, not runtime dependency.

Full regression command: `FRANK_EXPECT_REAL_GIT_REPLAY=1 PYTHONPATH=. /tmp/mission-ca-c02-venv/bin/python -m pytest -q -p no:cacheprovider tests` from local-agent. Final result and review/CI will be recorded after completion. CI workflow repeats exact PR46 baseline RED, focused GREEN, actual Node renderer, pyflakes/compileall/Node syntax, full real Git regression.

## Unfinished business acceptance and scope limits

Not deployed. Native production Dashboard, real operator input/readback, final current-main integration and user business acceptance remain NOT_PERFORMED. External metadataPointer interface parsing remains UNCONFIRMED. Chain labels do not verify official social/project affiliation. Actual malicious issuer conflict and unplanned public RPC outage were not found; fault injection is labeled. Holder/LP completeness, narrative, C03-C10 and full C01 completion semantics are outside C02. Draft PR and tests alone cannot mark overall CA acceptance complete.

References: Solana metadata extension https://solana.com/docs/tokens/extensions/metadata and Metaplex metadata https://solana.com/docs/tokens/metaplex .
