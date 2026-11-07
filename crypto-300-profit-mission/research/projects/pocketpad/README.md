# Pocket Pad Chrome public mint: runbook and remaining gates

Date: 2026-11-08, Asia/Bangkok.
State: script committed; Chrome runtime untested; no user voucher; no user transaction.
This research aid does not authorize automatic trading, monitoring, wallet signing or changes to Mission production.

## 1. Confirmed inputs and known limitations

Official site: https://pocketpad.io/
Latest previously observed official timing message: https://x.com/pocketpad_io/status/2119112658209341874

That announcement stated public mint at 13:00 EST on Nov 7, 2026, equal to 01:00 in Bangkok on Nov 8. The issuer has changed its timetable several times; recheck the official announcement and the onchain phase. The timestamp is a planned opening, not a verified executed phase change.

Robinhood Chain: chain ID 4663 (hex 0x1237).
Pocket ERC-721 contract: 0x3a98DE41A0dF554F6b69Ca1b5A1Ad93a745AB1F2.
Public mint selector: 0x98dd0156; method: mintPublic(bytes32,uint256,uint256,uint256,bytes) payable.
Public mint: 0.03 ETH per item. Allowlist first mint: 0.015 ETH.
Two NFTs per user/identity in official rules, subject to actual smart-contract/identity checks.
Contract has signed vouchers, unique nonces and expiration timestamps.
White-listed users can mint their second NFT using mintPublic during allowlist phase, so PublicMinted events alone do not prove general public eligibility.

Verified historical public-price transaction:
https://explorer.robinhood.com/tx/0xa16f2d74f952fe925b57e173d091c4398f83569a9709678b5a0e6f15fea6f560

Its calldata reconstruction matched exactly, and a read-only simulation at its preceding block succeeded. This does not prove the present user's account has a voucher or that present-phase mint succeeds.

The user's Pocket page previously showed the error: We couldn't confirm your access.
Website showed 0.035 ETH in an embedded wallet. That was a dated page observation, not a refreshed onchain wallet balance, and is insufficient for two public-price NFTs.

## 2. Installation from Terminal on macOS

The command below copies the reviewed script from the mission Git branch into the clipboard and opens the official page in Chrome. It does not execute the script or create a transaction.

~~~bash
curl -fsSL 'https://raw.githubusercontent.com/lxxlx2/ChatGPT_mission_record/research/pocketpad-public-mint-chrome-20261108/crypto-300-profit-mission/research/projects/pocketpad/chrome_mint_preflight.js' | pbcopy && open -a 'Google Chrome' 'https://pocketpad.io/'
~~~

You should inspect the script in the GitHub file viewer before executing code inside a signed-in tab.

While already signed into Pocket Pad:

1. Open Chrome DevTools Console with Command+Option+J; alternatively DevTools > Sources > Snippets > New Snippet.
2. Paste the clipboard script and run once.
3. Confirm the console prints [PocketMint] Installed.
4. Click Check access again exactly once.
5. Execute the following safe diagnostics:

~~~javascript
PocketMint.status()
await PocketMint.snapshot()
await PocketMint.scanScripts()
~~~

The report lists sanitized endpoint paths, HTTP codes, durations, contract phase and counters. It does not print OTP, passwords, cookies, authorization headers, signed vouchers or complete responses. Never paste the full DevTools Network response or any bearer token into chat/Git. Only share sanitized paths, HTTP status and timing.

If snapshot fails because the public RPC blocks CORS or the user has no matching injected provider, mark RPC as UNAVAILABLE. Do not interpret that as sold out or successful eligibility.

## 3. How to interpret the access failure

- HTTP 500/502/503/504: server failure is plausible; retain login and wait rather than create a new Privy wallet.
- HTTP 429: throttled; do not retry quickly.
- HTTP 401/403: login, session or eligibility gate; verify authorization normally, without attempting authentication bypass.
- HTTP 200 but UI still fails: frontend or API business response needs further read-only inspection.
- No observed requests: may be a third-party host, different endpoint, service worker, or a request that already happened. Use DevTools Network > Fetch/XHR, recording only redacted metadata.

## 4. After a valid voucher has been legitimately issued

Do not assume the helper can produce a voucher by itself. It only detects certain signed responses from the Pocket origin after injection.

~~~javascript
PocketMint.hasVoucher()
~~~

Read the *actual* wallet address from Pocket/Privy wallet menu. Do not guess and do not export a private key. Only when hasVoucher is true:

~~~javascript
var pocketTx = PocketMint.prepare('0xYOUR_ACTUAL_PRIVY_WALLET_ADDRESS')
await PocketMint.simulate(pocketTx)
~~~

Do not share pocketTx or its calldata. The calldata contains a signed mint authorization, which is time-sensitive and recipient-bound. A quantity of 2 can only be used if the issuer signed quantity 2. The helper never edits the quantity of the signed voucher.

A real transaction is not sent by any of the above. The following is an OPTIONAL real ETH spend, only when the user separately chooses it and confirms in an exact matching injected wallet:

~~~javascript
await PocketMint.send(pocketTx)
~~~

The Privy embedded wallet may not expose window.ethereum. The helper will refuse wallet-address mismatch and must not be made to export the wallet key. A live transaction always requires a separate user decision and wallet confirmation.

## 5. Remaining work and acceptance gates

1. Reconfirm official opening announcement and live mintPhase using a fresh block.
2. Determine exact HTTP root cause of Checking access through the user's Chrome Network panel.
3. Identify the actual backend voucher endpoint and whether it issues valid signed vouchers before the public phase.
4. Check Voucher binding: wallet, identity hash, quantity, nonce, expiry and current phase.
5. Determine the exact Privy mint wallet address and whether there is a safe wallet-provider integration.
6. Confirm signed quantity 2 only if the user funds 0.06 ETH plus gas and the service supports it.
7. Test eth_call for an unexpired user voucher, correct from wallet, intended amount and public phase.
8. If the user elects a live mint, confirm separately inside wallet, then inspect transaction receipt and PublicMinted event.
9. Preserve redacted evidence and failures; no auto-loop, repeated spam or wallet-key extraction.
10. Record only materially useful new evidence in the project research file under existing Mission policy.

| Gate | State |
| --- | --- |
| Contract and chain identity | VERIFIED |
| Historical mint function/call data | VERIFIED |
| Historical eth_call replay | VERIFIED |
| Script written to Git | DONE |
| Script run inside user's Chrome | NOT DONE |
| HTTP error root cause | UNRESOLVED |
| Voucher API mechanism | UNVERIFIED |
| Valid voucher for this user | NOT OBTAINED |
| Privy injected-provider match | UNVERIFIED |
| User-funded and signed mint transaction | NOT EXECUTED |
| Current user mint receipt | NOT VERIFIED |

No credentials, session identifiers, wallet secret material or personal account details should be committed into this public repository.

## 2026-11-08 00:30 Bangkok, live auth error evidence

The user's Chrome Network tab showed:
- `GET api.pocketpad.io/mint/pocket/state`: HTTP 200.
- `GET api.pocketpad.io/mint/pocket/eligibility`: HTTP 200. This alone does not confirm user eligibility.
- `GET api.pocketpad.io/me`: HTTP 401.
- `GET api.pocketpad.io/mint/pocket/allowance`: HTTP 401.

Account UI still appeared logged in. Exact backend root cause remains UNRESOLVED. In particular, authorization missing, expired, wrong audience, or mismatched account are hypotheses, not confirmations.

**Chrome-only procedure**: Open the *already logged-in* pocketpad.io DevTools Sources > Snippets. Paste `auth_401_diagnostic.js`, run it, then in Console run `await PocketAuth401.recheck()`. It clicks the official "Check access again" button **once**, records only redacted route, HTTP code, elapsed time, Authorization header **presence/absence** (not value), and credentials mode. For delayed calls, run `PocketAuth401.report()`. To uninstall hooks, run `PocketAuth401.restore()`.

If 401 requests lack authorization, confirm whether the site uses cookies or an unsupported session mechanism. If Authorization is present and HTTP 401 persists, it was rejected by the API; inspect the normal Privy-to-backend session flow. Do not invent bearer tokens or bypass the issuer signature gate.

Never publish credentials, cookies, identity hashes, signed vouchers, email, session values, or private keys. Because the issuer acknowledged historical Privy-wallet remapping, do not clear site storage or logout until the exact funded embedded-wallet address is verified.

Last checked chain: 2026-11-08 00:30:12 Bangkok, block 108580701, mintPhase=1, totalMinted=503, allowlistMinted=301, reserveMinted=100, paused=false. Snapshot is not an availability claim.

State: targeted diagnostic saved to Git, JS syntax validated; not yet run in the user's browser; no valid user voucher or live mint transaction confirmed.
