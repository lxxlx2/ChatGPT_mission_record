# Frank D2 — conditional permission repair + single import attempt: BLOCKED, safely restored

Authorization: [Issue165 full runbook](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6376739911), [PR178 executor handoff](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6376744705).

Fixed PR60 `e4529ba7069e5499d12323a7160ceac08c481fae`, PR174 `a14846f16e68fd0899ab5506d8c2f0c91272df48`, PR178 `ea9a7715beb4d2a55ae956bf993828cbddcb50e5`. Remote HEADs matched. Original PR60/178 detached source bytes matched their own Git archives; no product edits. Installed Dashboard verified PR168 `656ed2c96f4210d106d7b1129ec6cf8d7c4586f3`, 437-file installed manifest and approved runner unchanged. Existing Python framework provenance remains UNRESOLVED, explicitly accepted only for this offline import per authorization; not marked runtime PASS.

## Actual ordered gates

|Gate|Result|Evidence|
|---|---|---|
|A01_SOURCE_PIN|PASS|See aggregate assertions.json; criteria passed|
|A02_LIVE_SERVICE|PASS|See aggregate assertions.json; criteria passed|
|A03_EXACT_SHARED_DIRECTORY|PASS|See aggregate assertions.json; criteria passed|
|A04_OTHER_SERVICE_IMPACT|PASS|See aggregate assertions.json; criteria passed|
|A05_NO_OVERWRITE|PASS|See aggregate assertions.json; criteria passed|
|B01_SINGLE_DIRECTORY_MODE|PASS|See aggregate assertions.json; criteria passed|
|B02_POST_PERMISSION_ACCESS|FAIL|BLOCKED_SHARED_CONTROL_PERMISSION_IMPACT|
|C01_FINAL_PREWRITE|SKIPPED|Stopped before exporter; safety rollback performed separately|
|C02_EXPORT_ONCE|SKIPPED|Stopped before exporter; safety rollback performed separately|
|C03_PRIVATE_READER_ACCEPTANCE|SKIPPED|Stopped before exporter; safety rollback performed separately|
|C04_CLOSEOUT_AND_ROLLBACK|SKIPPED|Stopped before exporter; safety rollback performed separately|

A01 verified original Oct23 manifest/SPL/Token2022 wire hashes against frozen values (hash-only; no raw wallet document replay). A02 verified current Dashboard/Loop/V1 identities, effective UID, start/cwd/argv, runner/plist and unique local8766 listener using OS metadata; no production HTTP. A03 verified existing physical owner/device/inode, canonical no-symlink control root and explicit Git non-membership. A04 inspected effective UIDs for all three known services, process argv references, OS open-file metadata, and current user LaunchAgent references. Three recognized consumers shared directory-owner effective UID, two recognized configured references, no unknown/cross-UID consumers observed before mutation, no ACL entries or filesystem flags. This does not promise immunity for unobserved future consumers. A05 target absent by non-following existence check.

B01 opened the verified existing directory with no-follow/directory flags, rechecked same device/inode/owner/mode and used **one nonrecursive fchmod0755→0700**. No owner/group/ACL or other file mode changes.

## First failure and diagnostic limitation

**B02_POST_PERMISSION_ACCESS / BLOCKED_SHARED_CONTROL_PERMISSION_IMPACT / UNRECOGNIZED_OPEN_FILE_CONSUMER.** The post-mode service PID/start/effectiveUID/cwd/argv/runner/plist and listener comparison passed before the subsequent open-file inventory failed. No known-service access loss was demonstrated.

There is a relevant executor-check limitation: B01 retains a directory descriptor for race-safe identity/rollback, but B02's open-file-consumer allowlist contained only the three services, not the executor itself. Therefore the executor can be classified as an unknown consumer by its own inventory. The failing PID was not retained, so this report **does not conclusively identify that consumer**, does not assert another production service was harmed, and does not relabel the failed run PASS. No hidden retry/allowlist adjustment or second permission attempt was made. Minimal future executor correction would explicitly recognize only its own bound descriptor/process and safely record unknown-consumer identity classification locally; this run stops without that correction.

## Safe rollback and final readback

Exporter invocations **0**; no D2 file was generated, so no private file needed deletion. Rollback verified the bound directory identity and target absence, restored0755 on that same descriptor, then read back service identities and listener unchanged. Separate closeout readback confirmed **0755**, expected owner, no filesystem flags and exact target absent. No private file was exposed by restoring0755 because none existed. No service restart occurred.

Production changes in this run: **only the one existing directory mode0755→0700→0755**. Final directory mode equals original. No new production files, no other control-file changes, no DB reads/writes or notifications. Original bundle untouched except hash reads. Product/runner/plist/source unchanged. D2 remains uninstalled and no data import accepted.

`REAL_RPC=0 / PROD_HTTP_GET=0 / EXPORTER=0 / RESTARTS=0 / DEPLOYS=0 / MERGES=0 / NOTIFICATIONS=0 / TRADES=0 / SQLITE_READS=0 / SQLITE_WRITES=0 / PRODUCTION_DATA_FILES_CREATED=0`.

Only report and sanitized assertions are published, including source hashes/manifests and aggregate gate facts. No private source, balance/Mint/account data, absolute private paths, argv, UIDs, credentials, screenshots or raw receipts are uploaded. Temporary clean detached checkouts removed at closeout. Existing raw and production services left intact.

**BLOCKED / DIRECTORY_MODE_RESTORED_0755 / D2_FILE_ABSENT / EXPORTER_NOT_RUN / NO_DEPLOYMENT.** This one authorized bounded attempt is complete and stopped; no automatic continuation.
