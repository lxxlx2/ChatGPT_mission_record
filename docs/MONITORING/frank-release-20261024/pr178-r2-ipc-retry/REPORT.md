# Frank D2 R2 Offline Chrome IPC Retry — BLOCKED / R2_COVERAGE_LIMIT

Authority: [Owner Authorization Issue #165 #6383301194](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6383301194), [Mac Executor Handoff PR #178 #6383310809](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6383310809). Design: [R2 local-IPC plan 2e3ee20e](https://github.com/lxxlx2/ChatGPT_mission_record/blob/2e3ee20ee812477d4907c90e821389eddc3bc7b1/docs/MONITORING/frank-release-20261024/FRANK_D2_DASHBOARD_ONLY_RELEASE_READINESS_20261024.md).

**Outcome: GATE_P_PASS / R2_COVERAGE_LIMIT_BLOCKED / DEPLOYMENT_NOT_AUTHORIZED.**
The single authorized sandboxed offline Chrome IPC retry was executed under strict path-scoped AF_UNIX controls. Synthetic sandbox proofs (Gate P) verified that IP operations and out-of-root Unix sockets are kernel-denied. During Chrome launch (Gate B), Chromium on macOS resolved its temp directory to Darwin per-user system temp (`/var/folders/.../T/`) rather than the exported `TMPDIR`, causing `ProcessSingleton` socket bind to be denied by kernel policy with `Operation not permitted (1)` (exit 21). Per contract, testing stopped immediately at first failure. No product-source defect demonstrated; no second launch, no sandbox loosening, no TCP listening sockets, and production remains unchanged.

---

## 1. Frozen Pinned References & Candidate Package (R1 Preserved)

- Candidate Product SHA: `914e9e47fed2e60bc24690fcb083413a64d4e681` (branch `research/frank-d2-private-child-port-stable-20261024`).
- PR #178 HEAD: `ea9a7715beb4d2a55ae956bf993828cbddcb50e5` (OPEN / Draft).
- Candidate Package: Full 446-file local-agent tree verified byte-for-byte; normalized manifest SHA256 `9a06f5f29fce05ccade8caa2b90d6d6c0c4248d2e6ab4e45aa26fa9d3f401062` exactly matched preserved R1.
- Installed Dashboard: `656ed2c96f4210d106d7b1129ec6cf8d7c4586f3` (PR #168), PID 88897 on `127.0.0.1:8766`, runner hash `a7cf3df2308535a3de8f5b723a4a373eaece5f8ac54a2f7350db28e3adf3c4b0`.
- Imported Private Data: `control_root/frank-d2-private/frank-d2-owner-at-slot.json`, 893,189 bytes, modes `0755`/`0700`/`0600`, SHA256 `d24d73d13a5ab9740eed7d1f06a6226aa9650004ccd756458b579c9e2ee2e284` (read-only verified, untouched).

---

## 2. Gate P — Synthetic OS Sandbox Proof before Chrome (PASS)

Disposable owner-only 0700 temporary root created outside Git. macOS Seatbelt policy strictly denied all IPv4/IPv6 network operations and permitted AF_UNIX only inside the single disposable root:

```scheme
(version 1)
(allow default)
(deny network*)
(allow system-socket (socket-domain AF_UNIX))
(allow network-bind (local unix-socket (subpath "<TEMP_ROOT>")))
(allow network-outbound (remote unix-socket (subpath "<TEMP_ROOT>")))
(allow network-inbound (local unix-socket (subpath "<TEMP_ROOT>")))
```

All 7 synthetic policy assertions were verified prior to touching Chrome:

| Assertion | Policy Expectation | Actual OS Result | Verdict |
|---|---|---|---|
| In-root UDS bind/listen/connect/accept | Allowed | Success (ping/pong echo verified) | PASS |
| Out-of-root synthetic UDS bind | Denied by kernel | `[Errno 1] Operation not permitted` (EPERM) | PASS |
| Out-of-root synthetic UDS connect | Denied by kernel | `[Errno 1] Operation not permitted` (EPERM) | PASS |
| AF_INET bind (127.0.0.1:0) | Denied by kernel | `[Errno 1] Operation not permitted` (EPERM) | PASS |
| AF_INET connect (127.0.0.1:8766 loopback) | Denied by kernel | `[Errno 1] Operation not permitted` (EPERM) | PASS |
| AF_INET6 bind (::1:0) | Denied by kernel | `[Errno 1] Operation not permitted` (EPERM) | PASS |
| Child process inheritance | Inherited denial | Child AF_INET bind: `[Errno 1] Operation not permitted` | PASS |

Zero new TCP/UDP listening sockets created. Gate P: **PASS**.

---

## 3. Gate B — Single Real Chrome Launch Attempt (BLOCKED)

Chrome wrapper explicitly exported:
```sh
export TMPDIR="<TEMP_ROOT>/chrome-tmp"
export TMP="<TEMP_ROOT>/chrome-tmp"
export TEMP="<TEMP_ROOT>/chrome-tmp"
```
and invoked `/usr/bin/sandbox-exec -p '<SEATBELT_POLICY>' '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' "$@"` with `--remote-debugging-pipe` and `--user-data-dir="<TEMP_ROOT>/chrome-profile-..."`.

- **First failing gate**: `R2_BROWSER_LAUNCH: CHROME_UNIX_SINGLETON_BIND_DENIED_DARWIN_TEMP_DIR`
- **Literal error log**:
  ```
  [pid=41468][err] [41468:57306347:1024/180354.796481:ERROR:chrome/browser/process_singleton_posix.cc:1080] Failed to bind() /var/folders/5y/8cbpg10d2ns199gnp0fwj4n80000gn/T/com.google.Chrome.nsov6k/SingletonSocket: Operation not permitted (1)
  [pid=41468][err] [41468:57306347:1024/180354.796661:ERROR:chrome/app/chrome_main_delegate.cc:569] Failed to create a ProcessSingleton for your profile directory. This means that running multiple instances would start multiple browser processes rather than opening a new window in the existing process. Aborting now to avoid profile corruption.
  <process did exit: exitCode=21, signal=null>
  ```
- **Underlying reason**: On macOS, Chromium implements `base::GetTempDir` via Darwin system APIs (`confstr(_CS_DARWIN_USER_TEMP_DIR)` / `NSTemporaryDirectory()`), which ignores shell `TMPDIR` environment variables and returns `/var/folders/.../T/`. Under the Seatbelt policy confining AF_UNIX to `<TEMP_ROOT>`, binding `/var/folders/.../SingletonSocket` was correctly denied by the OS with `Operation not permitted (1)`.
- **Contract compliance**: As required by owner consent and handoff instructions (*"Fail first gate → STOP; no second Chrome launch or broader sandbox fallback"*), execution terminated immediately upon exit 21. No retry was attempted, no permissions were loosened, no HTTP test port was opened, and no synthetic bypass was used.

---

## 4. Test Case Execution Ledger

| Test Case | Execution Status | Reason |
|---|---|---|
| Manual click / initial D2 GET 0 | NOT_TESTED | Browser aborted at ProcessSingleton before page creation |
| Page 0 / Page 41 / Previous pagination | NOT_TESTED | Browser aborted at ProcessSingleton before page creation |
| Exact Mint (nonzero / observed-zero / absent) | NOT_TESTED | Browser aborted at ProcessSingleton before page creation |
| Oct 23 Bangkok timestamp & two finalized slots | NOT_TESTED | Browser aborted at ProcessSingleton before page creation |
| Late request race & original function overlap | NOT_TESTED | Browser aborted at ProcessSingleton before page creation |
| Missing & corrupt source error handling | NOT_TESTED | Browser aborted at ProcessSingleton before page creation |
| HTTP 503 & malformed JSON no-retry | NOT_TESTED | Browser aborted at ProcessSingleton before page creation |
| Existing signal / intelligence / CA controls | NOT_TESTED | Browser aborted at ProcessSingleton before page creation |
| In-memory pipe Handler bridge queries | 0 dispatched | Bridge initialized synthetic doc; closed cleanly |

---

## 5. Gate D — Closeout & Invariants Audit

- Cleanup: Isolated Chrome process exited; temporary profile directory removed; bridge process closed and exited; synthetic directories removed.
- Listener check: Exactly one Dashboard listener on `127.0.0.1:8766` (PID 88897). Existing observed ports `8765` and `48721` untouched (`UNKNOWN_NECESSITY_KEEP`).
- Installed files & runners: PR #168 installed files and launchd plist unchanged.
- Private data: `frank-d2-owner-at-slot.json` modes `0755`/`0700`/`0600`, 893,189 bytes, SHA256 `d24d73d13a5ab9740eed7d1f06a6226aa9650004ccd756458b579c9e2ee2e284` unchanged.
- Hard negatives:
  `PROD_WRITES=0 / NEW_TCP_LISTENERS=0 / NEW_HTTP_TEST_PORTS=0 / NEW_RPC=0 / PROD_HTTP_GET=0 / EXPORTER=0 / RESTARTS=0 / DEPLOYS=0 / MERGES=0 / NOTIFICATIONS=0 / TRADES=0 / PORT_CHANGES=0`.
- Release qualification `G03B_INTERPRETER_ORIGIN=UNRESOLVED` remains recorded.

**Status: MAC_D2_R2_OFFLINE_BROWSER_RETRY_BLOCKED / R1_PASS_PRESERVED / R2_COVERAGE_LIMIT / PROD_UNCHANGED / DEPLOYMENT_NOT_AUTHORIZED.**