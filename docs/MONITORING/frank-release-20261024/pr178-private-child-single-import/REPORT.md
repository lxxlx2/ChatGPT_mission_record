# Frank D2 — MAC_D2_PRIVATE_CHILD_SINGLE_IMPORT_PASS

Authorization: [Issue165 complete new private-child runbook](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6382828296), [PR178 execution handoff](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6382838412).

## Fixed execution identities

- Candidate reader / executed original exporter checkout: `914e9e47fed2e60bc24690fcb083413a64d4e681`.
- Original PR178 reference: `ea9a7715beb4d2a55ae956bf993828cbddcb50e5`; unchanged exporter blob `7709dec5a749a10d75596b46b8afa818970e0f2b`.
- Candidate private-child reader blob: `eadfe0f765c400b4aa2e839c8604a6e4fa080b9b`.
- Original PR60 replay: `e4529ba7069e5499d12323a7160ceac08c481fae`; PR174 reference `a14846f16e68fd0899ab5506d8c2f0c91272df48`.
- Current installed Dashboard independently reverified: PR168 `656ed2c96f4210d106d7b1129ec6cf8d7c4586f3`, all437 manifest files and approved runner match. This release still has no D2 route or wallet_d2_ingress import.
- Candidate branch and original PR60/174/178 remote HEADs matched frozen pins before creation. Two clean detached checkouts matched all local-agent bytes in their own fixed Git archives. Main workspace not switched or modified. Product/candidate branches not changed.

## Actual one-time execution

|Named gate|Result|Actual evidence|
|---|---|---|
|A01_SOURCE_PIN|PASS|Frozen refs, exact original exporter/new reader blobs, clean detached archive bytes and three saved raw hashes match|
|A02_LIVE_SERVICE|PASS|Current Dashboard/Loop/V1 identified; real serve/script/cwd/flags match runner, exact8766 listener;437 installed files unchanged|
|A03_EXACT_SHARED_ROOT|PASS|Existing physical root from actual runner CONTROL_POINTER and live --control-root; prior pointer provenance matches;0755 owner/no-symlink/no-Git/no-ACL-or-flags|
|A04_CHILD_AND_SOURCE_ABSENT|PASS|Non-following checks: new child, source and legacy direct-root source absent; services unchanged|
|B01_SINGLE_PRIVATE_CHILD|PASS|Exactly one atomic single-level mkdir using bound parent descriptor, umask077, mode0700; shared parent untouched0755|
|C01_FINAL_PREWRITE|PASS|Original source hashes and clean fixed source rechecked; target absent, child0700, parent0755, services/8766 unchanged|
|C02_EXPORT_ONCE|PASS|Original exporter invoked exactly once under macOS process-level deny-network sandbox, parent and children; exit0; timeout100s|
|C03_PRIVATE_READER_ACCEPTANCE|PASS|Candidate private-child read_d2_source/query_d2 accepted actual new file; byte hash/size/provenance/count/page/lookup checks passed|
|D01_CLOSEOUT|PASS|Shared0755/child0700/source0600 retained; original raw/437 installed files and all protected service identities/8766 unchanged; no rollback|

The physical allowlisted location is the existing verified control_root plus **`frank-d2-private/frank-d2-owner-at-slot.json`**; no alternate root or staging destination used. Neither child nor source existed before this operation. Original exporter O_EXCL/no-symlink/Git guard created the new source. CLI's constant `production_imported:false` was not used to infer destination: post-write file metadata and candidate reader independently establish the actual new file at the allowlisted relative location.

Only **two production filesystem creations** occurred: one private child directory and one source JSON. Shared root owner/device/inode and0755 were preserved throughout; no shared-root chmod, owner/group/ACL modifications, overwrite, service install or runtime activation. New file identity verified at creation and closeout. File retained on success; no rollback performed.

## Dated source and exact bytes

|Item|Actual verified value|
|---|---|
|Derived bytes|893189|
|Derived SHA256|`d24d73d13a5ab9740eed7d1f06a6226aa9650004ccd756458b579c9e2ee2e284`|
|Source manifest SHA256|`f06df53ccfb8b96e1b92f428620311cf62bd6bb44f9b83fd7e126f2ee5b1f88b`|
|SPL raw SHA256|`f77120c050a6d014dd53d41fd9d0e8392f34ab31b91155bfa30e18334ab3b682`|
|Token2022 raw SHA256|`a327bf34f0e5bf10994662e937704d74098464cc5fddeb2ab4ce77e9ac2c58c2`|
|Verified source capture digest|`016b99ff42c3b155316bd46bec5850ff9dbfb9437bbfd5c3c28414d58fef4f08`|
|Internal document checksum, **not signature/authentication**|`273058a9961d017fa170e86a593e3f621f5ddb31f322e40ce1846ccd66c1581b`|
|Observed UTC|2026-10-23T14:46:32.787921+00:00|
|Observed Bangkok|2026-10-23T21:46:32.787921+07:00|
|SPL finalized evidence|slot460482174 /1875 accounts|
|Token2022 finalized evidence|slot460482176 /2273 accounts|
|Total|4148 Token Accounts /4148 distinct Mints /3275 nonzero Mints|
|Pagination|42 pages, actual41×100+48|
|Pinned32 cross-check|32 present,8 nonzero/24zero|
|Exact observed-zero vs valid absent Mint|Distinct original reader states; not collapsed to zero|

Original PR60 raw-receipt replay ran inside the original exporter, not an unverified JSON substitute. All original raw hashes rechecked unchanged at closeout. No new chain request. No Mint identities, token-account keys, individual balances or raw payloads printed or uploaded. Candidate validator confirms unique Mint rows and unchanged schema; all source summary counts and derived byte digest matched.

**Historical, separate-slot, non-atomic snapshot only:** `same_slot_atomic=false`, `current_chain_balance_verified=false`, `usd_value_verified=false`, `pnl_verified=false`. This does not prove current wallet balances or ongoing live holdings.

## Protected runtime and limitations

Current known Dashboard/Loop/V1 PID/start/effectiveUID/cwd/argv and runner/plist hashes were compared locally before/after and remained identical; raw identities and private paths not published. Existing 127.0.0.1:8766 listener matches the same Dashboard process; no probing of8765/48721 or unrelated ports. No new listener or backend process started.

Existing `G03B_INTERPRETER_ORIGIN=UNRESOLVED` remains disclosed, accepted only for the authorized offline data import. It is not reclassified as binary-provenance PASS or release readiness. Actual script/cwd/serve/flags, installed source manifest, runner/plist and listener identities were verified without the rejected -m or canonical argv0-equality assumptions.

**D2_ENDPOINT_NOT_DEPLOYED / DASHBOARD_UI_NOT_ACTIVATED.** Installed PR168 still lacks the candidate private-child route; physical data import does not make it appear on the current Dashboard. No production HTTP/browser request was made. Candidate reader was invoked locally from isolated fixed source only; no production SQLite/backend/scanner/worker invocation.

## Safety and closeout

`SHARED_ROOT_CHMOD=0 / NEW_RPC=0 / PROD_HTTP_GET=0 / RESTARTS=0 / DEPLOYS=0 / MERGES=0 / NOTIFICATIONS=0 / TRADES=0 / SQLITE_READS=0 / SQLITE_WRITES=0 / NEW_LISTENERS=0 / PORT_CHANGES=0`.

Exporter calls **1**, no retry. Rollback **not executed**. Retain exact new child0700 and source0600, shared root0755 unchanged. Only temporary clean source/evidence checkouts removed after publication; original Oct23 raw and new authorized private file retained. No new PR, source modifications, dependency installation or production config changes. Report and scalar assertions only; no private executor/runner source, full paths, argv, PIDs/UIDs, raw receipt/JSON, Mint/account lists, private byte excerpts, credentials, screenshots or balances in Git.

Prior historical BLOCKED/REQUEST_CHANGES records remain unaltered. This is a distinct newly authorized successful one-time operation.

**MAC_D2_PRIVATE_CHILD_SINGLE_IMPORT_PASS / HISTORICAL_SOURCE_IMPORTED / CURRENT_BALANCE_NOT_VERIFIED / D2_ENDPOINT_NOT_DEPLOYED / PROD_SERVICES_AND_8766_UNCHANGED.** Stop after this report; Dashboard-only deployment remains a separate future owner decision.

Execution finished UTC: `2026-10-24T10:02:33.657151+00:00`.
