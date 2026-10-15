# Frank existing-source F01 / C02 / F02 read-only HTTP connector — 2026-10-15

**Status: DEVELOPMENT / EXACT_SHA_CI_PENDING / OTHER_AI_REVIEW_PENDING / REAL_USER_MAC_NOT_RUN / PRODUCTION_NO_GO**.

This successor is stacked on [PR #69](https://github.com/lxxlx2/ChatGPT_mission_record/pull/69) external independent `APPROVE` only for the **data projection** at immutable `bd4698cd391174e3626b858e6db9ba8347517ff3`. It must not rewrite upstream approved Frank V1, C02 identity, F02 original source, or merge main. User has rejected UI prototypes; this change is **backend-only**, no new page or redesign.

## User-visible outcome and current limit

The new independent opt-in **loopback research-only** service can, for one **exact full 32-byte Base58 Solana Mint**, fetch these **three existing read-only live HTTP endpoints** from already-started local services:

- existing F01/C02 control Dashboard `GET /api/follow-opportunities`: returns frozen Frank-only current actionable eligibility (from F01). **No historical NO_BUY revival and no new BUY judgment**.
- same control Dashboard `GET /api/cluster-latest?mint=<exact Mint>`: reads **already saved** CA report if one exists. A missing report returns `NOT_QUERIED`, **not** "analysis complete". No automatic `POST /api/cluster-analysis`, no Solana RPC, no quoting or $30 generic CA quote. `ARCHIVED_REPORT_READ` explicitly means a historical stored report, not a newly completed full CA assessment.
- isolated research-only F02 `GET /api/research/positions`: every call reads source/TTL afresh from already imported separate research Sidecar and frozen A05 two-program source, no additional chain capture. F02 never claims full active portfolio; when source is expired/partial/mismatched, balances/Token Account counts are withheld.

Then calls the previously reviewed **pure exact-Mint projection** to return:
`GET http://127.0.0.1:<bridge port>/api/research/alignment?mint=<exact Mint>` with nested `alignment.f01`, `alignment.c02`, `alignment.f02`, per-source `upstream` and an honest top-level `status`.

The projection always returns `combined_trade_permission=false`; `F01_SOURCE_UNAVAILABLE` is **not** `F01_NOT_ELIGIBLE`; `CA_NOT_QUERIED` is **not** verified narrative; `SOURCE_UNAVAILABLE` is **not** ZERO/SELL. One zero account may format `0.000000` and remains zero, as fixed in #69. Do not cache a response as a live portfolio: the source TTL must still be checked again at browser display time in later UI acceptance.

**Crucial architectural limit:** The normal main/production Dashboard **does not yet contain the reviewed F01+C02+F02 combined branches**. The bridge only reads already-existing **GET API outputs** and is currently exercised with a disposable local integration setup; it does not install/merge/modify a production control server. It does not create missing C02 reports, validate full C02 narrative/holder/LP/funder completeness, or turn the frozen 32 Mint list into a whole-wallet view. A separate authorized integration and real Mac browser product acceptance is necessary.

## Execution safety and manual-only CLI

Running with no operation flags returns `PLAN_ONLY` without opening a listener or performing HTTP:

```zsh
cd crypto-300-profit-mission/local-agent
python3 -B -m scripts.frank_joint_readonly_http
```

Once the **upstream services have been separately authorized and started in a research-only isolated checkout**, their two local ports and this new unoccupied HTTP listener port can be supplied. Both source ports are literal loopback `127.0.0.1` only; no arbitrary hostname/URL, no redirects/proxy, HTTP GET only, bounded response size/timeout, and no production credentials:

```zsh
python3 -B -m scripts.frank_joint_readonly_http --serve --control-port 18766 --f02-port 18765 --listen-port 18777
```

Example ports above are **illustrative only**, not a claim that any service is running, that they are unoccupied, or that production services are currently compatible. The command does not start F01 or C02 or F02. Explicit research-only authorization, source startup and Mac acceptance remain separate.

For a one-time local read only against services already explicitly started, replace the placeholder CA and ports with grounded real values:

```zsh
python3 -B -m scripts.frank_joint_readonly_http --probe-once --mint SOLANA_MINT_HERE --control-port 18766 --f02-port 18765
```

`--probe-once` issues a maximum of three local read-only GETs; no new network RPC to Solana (the upstream endpoint should be read-only GET and must independently preserve its own safety contract). No scheduling, no logs containing Mint query strings; server bound only to `127.0.0.1`. It does not CORS-enable a remote site and does not serve an HTML page.

## Acceptance evidence and known limitations

Synthetic real localhost HTTP tests exercise source GET paths with an actual temporary F02 research SQLite and original dual-program **synthetic** RPC and no actual Solana RPC. Cases: current eligible F01, CA identity with exact Mint, F02 fresh nonzero/zero; same-name/different CA; `NO_BUY` is never generated from absent eligible; missing CA report; unavailable F01/older F01 `as_of_epoch`; F02 source stale, Host validation, invalid Base58 CA, POST refusal, no CORS, zero production writes or new query jobs. Separate disposable combined CI exercises reviewed F01, C02 and F02 implementations. The source is synthetic; no inference from user's prior private Mac archive to fresh positions.

- [PR #69 fixed reviewed projection SHA](https://github.com/lxxlx2/ChatGPT_mission_record/commit/bd4698cd391174e3626b858e6db9ba8347517ff3) stays immutable.
- [Independent reviewer P3](https://github.com/lxxlx2/ChatGPT_mission_record/pull/69#issuecomment-6187260196): the joint test's unused `datetime.timezone` import is cleaned **in this new child only** and CI now explicitly pyflakes-checks the integration test and the new HTTP bridge. No approved parent SHA changed.
- **Before release**: independently review pinned child SHA, run actual joint native API HTTP smoke in disposable checkout, then carry through user Mac isolated browser end-to-end real CA/positions operation, decide full current wallet scope, independent final system review and explicit deployment approval.

**Hard gates**: `NO_MERGE / NO_DEPLOY / NO_NEW_REAL_RPC / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_NEW_AUTOMATION`.
