# BSC 前向地址跟单 F0 / D2-D3 A6：受信 macOS 账户威胁模型决策

Date: 2026-10-27 (Asia/Bangkok)
Status: `USER_ACCEPTED_NARROWED_THREAT_MODEL / INDEPENDENT_REVIEW_PENDING / DOCS_ONLY / NO_GO`
Parent ADR: `f0/F0_D2D3_PRODUCTION_RELEASE_THREAT_MODEL_ADR_20261026.md`, approved as **DOCS ONLY** in PR #219 at `1b35156710a860ae579c0e2ff1fd47d8f1052ad5`.
Approved implementation baseline: PR #217 at `8362b4048d45b0bd13be4a6e4b6be35ad737819b`, **only** for a PROPOSAL message format.

## Recorded user choice, limited to A6

On 2026-10-27 the user explicitly accepted the following alternative offered after reviewing PR #219:

> For this bounded BSC **read-only** F0 research experiment, assume the operator's macOS user account is trustworthy; do **not** claim protection from intentionally malicious processes running as that same UID. The user explicitly accepts the resulting residual risk **as a threat-model assumption**, subject to independent security review of the final implementation.

This is the user's conversational decision, **not** an authenticated signed D2/D3 approval, not an independently reviewed change, not consent to enroll keys, not authorization to start RPC, and not a decision that risk has been cryptographically eliminated. The broad hostile-same-UID threat model remains unsupported; if it becomes a requirement, this decision must be reopened.

A6 tracking state: `USER_ACCEPTED_NARROW_SCOPE / REVIEW_REQUIRED`. It is not `PRODUCTION_REPLAY_PROTECTION_PROVEN`.

## Scope, defenses, and explicitly accepted residual risk

1. Assumed trusted boundary: a user-controlled macOS account and a separately verified, fixed, read-only foreground launcher running reviewed source and dependency bytes. The owner does not intentionally delete, rename, reset, or patch the local grant registry and does not run malicious same-UID actors.
2. The existing 0700 owner-private registry, held directory FD, and O_EXCL/fsync marker can help detect **accidental or concurrent** reuse while the trusted directory remains stable; they do not guarantee replay prevention against an adversarial account owner across runs. The final production integration is **not yet implemented or validated**.
3. Explicitly out of claim: protection against a malicious same-UID process replacing directories/marker, monkeypatching Python or transport, corrupting local clock/storage, or manipulating the launch environment. The project must **never** advertise cryptographically independent replay protection or immutable local attestations under those assumptions.
4. Residual impact includes unauthorized/repeated read-only requests, missed or fabricated evidence, incorrect L1 coverage claims, upstream rate-limit consumption and leakage of raw public-chain metadata. The existing safeguards remain necessary: strict source/method/byte/attempt/UTC caps; exclusive pre-send durable RID; no retries/fallback; RAW-before-SETTLE; UNKNOWN/gap accounting; one original 3-slot coordinator.
5. This trust decision covers only **a future specifically approved** single foreground BSC F0 pilot. It cannot be inherited by production monitors, automated trading, other chains, unattended services, Frank/Monster, or a later experiment.
6. The pilot's actual machine/UID, owner attestation, private evidence root, signing authorities and final runtime SHA remain **unverified and undecided**. Never identify the account from a username or path in old logs.

## Gates still required

| ADR gate | Post-decision status | Required actual evidence |
| --- | --- | --- |
| A1 D2 user signer | `UNDECIDED` | Real accountable person, independently verified public key possession and custody; no private key in Git/chat |
| A2 D2 independent reviewer | `UNDECIDED` | Separate human or organizational reviewer and independent real-key authority; exact frozen-source review |
| A3 D3 one-shot operator | `UNDECIDED` | Distinct accountable operator authority and explicit one-run intent |
| A4 normative signature domain and revocation | `UNDECIDED` | New frozen normative specification; PR217 `PROPOSAL` domain must not be used for real signatures |
| A5 macOS UID, trusted launcher and evidence boundary | `UNDECIDED` | Identified and independently checked environment; explicitly carries this narrowed threat model |
| A6 replay threat model | `USER_ACCEPTED_NARROW_SCOPE / REVIEW_REQUIRED` | Independent threat-model review; residual same-UID risk must remain visible |
| A7 code SHA/manifest, one source and hard limits | `UNDECIDED` | Separate independently reviewed code, complete dependency hashes and final permit-bound scope |
| A8 one actual foreground read-only RPC trial | `NOT_AUTHORIZED` | NEW user approval after A1–A7, with exact SHA, machine, method and budget limits |

## Next work allowed without another user authorization

* Request **independent DOCS-ONLY review** of this exact decision record against the frozen PR #219 ADR: verify that A6 user acceptance has not been promoted to a security proof or real-run grant.
* In an isolated, subsequent code/spec PR, prepare a **normative-signature and trusted-launch design for review** that preserves independent A1/A2/A3 ownership, exact source freeze, the original single coordinator and the above residual risk. This may use synthetic tests only.
* Stop before gathering real signer identities/keys, pinning public production roots, touching actual OS registries, issuing/consuming grants, authenticating production software or calling RPC. Those actions require their own explicit applicable decisions and new fixed-SHA reviews.

The purpose of this F0 boundary is trustworthy BSC wallet BUY/SELL and real-time ordinary Router comparison data for later L1/L2/L3/L4 forward-follow research, never Monster D0/G1/G2 or live trading.

Immutable current operational state: `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`. `NO_DEPLOY / NO_RESTART / NO_RPC / NO_TRADES / NO_BACKGROUND / NO_MERGE / NO_GMAIL / NO_NEW_AUTOMATION`.
