# Frank D2 — Dashboard private read-only at-slot ingress (code-only)

Owner authorization: 2026-10-23 to **develop, test and independently review only**. **No private import, deploy, merge, RPC, production modification, restart, signal, mail, or trade authorized.**

## Fixed ancestry / stacking

- Installed, approved Dashboard product: `656ed2c96f4210d106d7b1129ec6cf8d7c4586f3` (PR168, production).
- Approved PR174 adapter/CLI + Mac zero-RPC private preview: `a14846f16e68fd0899ab5506d8c2f0c91272df48`. This PR is **stacked on PR174**, which itself descends from the installed Dashboard source. No merge is implied.
- Approved raw source PR60 `e4529ba7069e5499d12323a7160ceac08c481fae`; frozen Oct23 private bundle SPL 460482174 / Token2022 460482176, capture ~2026-10-23 14:46Z. **Two independent finalized program reads, never a single atomic state or a permanently current wallet.**

## Contract

`mission_control/wallet_d2_ingress.py` adds a **separate** source contract, NOT the old legacy `frank-inventory-snapshot.json` schema. It never reads raw RPC receipts or a wallet secret. A separate manually authorized source export may be produced later with `scripts/frank_d2_export_ingress.py` using the **actual verified PR60 original replay**, then placed through an **entirely separate, explicitly authorized and audited private import** into `control_root/frank-d2-owner-at-slot.json`. **No current source file is bundled or installed by this PR.**

The private JSON contains only **full Mint-level** aggregated raw integer quantity, decimals, Token Account count, applicable programs and finalized slots; **no individual Token Account addresses, token holders, raw wire responses, API credentials, market value, PnL or transactions.** Each Mint may be found by exact CA even when not in the initial page. The producer verifies the actual full PR60 source through PR174's already approved child process; the document contains an accidental-change SHA256 **not** an authenticator or proof of origin by itself. The manual import procedure must independently verify pinned source, owner and private file hashes before enabling it.

The HTTP reader rejects missing, invalid, link-backed, world/group-readable, oversized, inconsistent, wrong-owner, wrong-program, conflicting or false-live documents. It reads *only the allowlisted basename* in an already configured private control directory, never arbitrary paths. It has **no fallback** to a fictitious zero, legacy Oct11 sample, or remote RPC.

API `GET /api/frank-d2-at-slot?page=0..999` returns metadata plus <=100 Mint rows. `GET /api/frank-d2-at-slot?mint=<exact valid Solana CA>` returns an exact Mint row, or an explicit `NO_ACTIVE_OWNER_TOKEN_ACCOUNT_OBSERVED_AT_SLOTS` with **no fake zero**, even if the target Mint lies outside the first 100. The JSON never returns all 4,148 rows at once. API is loopback-host-bound and requires `X-Frank-D2-Read: 1`; browser same-origin fetch is explicit; cross-site request headers/preflight are rejected. No CORS. Return `SOURCE_NOT_IMPORTED` if no authorized private projection exists.

**Data truth rules**: `NONZERO_AT_SLOT` only if source account raw>0; `ZERO_AT_SLOT` only if actual account row with raw=0; missing Mint means **no active owner Token Account observed in those two programs at these slots**, not never-held and not necessarily zero native SOL. Local historical model OPEN/CLOSED, signed BUY/SELL are displayed separately in UI and do not change token balance. Each response shows source UTC, Bangkok time, age calculated at GET time, two independently finalized slots, non-atomic status and `current_chain_balance_verified=false`. No price, cost, profit or active signal implied.

## UI

The existing `#signals` view has a separate "Frank 链上余额证据（D2，按采集时点）" panel. It does **not** auto-request private data on dashboard load, refresh or timer. The user must click "读取已导入快照" or submit a full Mint. It uses GET **only**, bounded pagination, stale-response request generations and exact raw integer quantity formatting (no JS floats). When source absent/invalid, presents UNKNOWN not zero. Existing watchlist and Frank V1/MC policies unchanged.

## Acceptance and further gates

1. Code-only PR CI: Python test synthetic replays, private mode and tamper cases, exact lookup outside page, local page bounds, absent vs zero, non-atomic slot date, bad import; Node actual D2 frontend handler GET-only/race checks. No real Solana endpoints or original private data in CI.
2. Independent source review of exact PR SHA and all changed files, then **bounded Mac isolated fixture browser verification** using only synthetic private source.
3. Separate owner authorization before *any* real Mac private projection export/import, and later **separate Dashboard-only production cutover approval**, each with rollback and proper source/permission validation. A realistic production acceptance cannot be claimed from offline CI or synthetic data alone.
4. Any future refresh scheduler or new RPC must receive new explicit authorization. Previous two RPC calls are already fully consumed.

**Never conflate this feature with CA Gate A–D, ongoing real-time balance observation, native SOL, full historical wallet PnL, actual buys/sells, or an authorized trade/notification.**
