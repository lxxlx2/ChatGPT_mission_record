# BSC F0 adaptive HEAD one-use runner: offline preparation and consent gate

**Status:** `CODE_PREPARATION_ONLY / NOT_REVIEWED / ZERO_REAL_RPC / NO_PERMIT`.
**Base authority:** PR156 exact independently approved offline SHA `9326edc3b78bbd9e19f2d405668bf430432e853a`.
The approved PR156 branch and older PRs remain untouched. This is the next isolated development increment for **L1 free source viability**, not L2 quotes, ROI, a production monitoring service or F0 PASS.

## Implemented but not executed on a real network

The new `f0_l1_adaptive_live_once.py` is a concrete, strictly opt-in live wrapper around the already approved `collect_adaptive_injected` and the existing reviewed-style `live_https_post`. This wrapper can send public BSC RPC if deliberately executed; **importing or running offline tests cannot launch it**. No permit is supplied, generated or authorized by this PR.

Before invoking real HTTP, the CLI requires `--execute-live`, a separately user-approved JSON permit, a separate independent reviewer file `APPROVE_PERMIT <sha256(exact permit bytes)>`, a fixed Git HEAD and exact entrypoint SHA256 plus all transitive source/dependency bytes, a private fresh /tmp directory, and fsynced one-use nonce marker. It refuses old permit scope, missing permission flags, old SHAs, moved code, paid / proxy / redirected / retry / WS modes or reused nonce.

**Proposed hard maxima in source, not yet user approval:**
- Total `eth_chainId + initial HEAD + HEAD refresh + full blocks` requests: at most **32**, with a fixed `2 + max_head_polls + max_block_reads` equality.
- Max 24 full-block reads and max 6 HEAD refreshes. One request counter shared by all.
- Max 60-second core duration; HTTP timeout at most 5 seconds; request spacing at least 250 ms.
- Single existing official free endpoint `https://bsc-dataseed.bnbchain.org`, chain ID 56, no redirects, proxy, retries or auto-upgrade.
- Store raw public RPC responses privately at the user-authorized local /tmp directory. No wallet signing, alerts, trades, quote or background service.

These numbers are **candidate narrow-trial ceilings**, not permissions or proof of provider throughput. The actual runtime fields and private single-use permit must be independently reviewed against a **future fixed SHA** and the user's fresh explicit consent before one call is sent. Existing 4/24/62 grants are consumed and cannot be reused.

**Important limits:** the runner only measures local source-sampled HEAD-minus-consumer backlog (the initial 0 is a reference baseline), block acquisition and candidate-address hits; it does not measure global first-seen, prove causal BUY/SELL, certify E2/E3 or produce matched randomized BUY controls/real quotes. An interrupted or failed callback retains consumed attempts; persisted UNKNOWN may include presend expiry and is not independently proof of a billed call.

## Independent review checklist (pending)

1. Verify full checkout SHA and source/dependency bytes before any network; refuse code modifications or unexpected permit fields.
2. Verify nonce fsync before HTTP and no old permit or repeated nonce can execute.
3. Verify endpoint/proxy/redirect restrictions inherited from existing `live_https_post`.
4. Verify maximum shared HEAD+BLOCK request budget and no retries, no automatic long running service.
5. Run new offline tests and full suite without executing the CLI. Confirm no test uses a real `post`.
6. Verify all frozen cohort and Router blobs in the original injected core still check before the first callback.
7. Separate code review `APPROVE_OFFLINE_CODE` from an entirely new `APPROVE_PERMIT` for the user-approved private instance.

Stop at `REQUEST_CHANGES` for P0/P1, or `BLOCKED_INSUFFICIENT_EVIDENCE` for unavailable tests. Original #156 approval remains valid for its fixed SHA. No merge, live trial, WS, signature, spending, deployment or automation.
