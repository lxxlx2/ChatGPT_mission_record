# Ledger user-wallet drainage allegations — source and detection audit
report_date: 2026-10-09
timezone: Asia/Bangkok
event_key: ledger:multiuser_wallet_drain:2026-10-09
status: UNCONFIRMED_HIGH_IMPACT_WALLET_SECURITY_CANDIDATE
notification_type: none (research receipt only)
automations_created: false
monitoring_scope_changed: false
schedule_changed: false

## Evidence and limitations
1. FIRSTHAND RESEARCHER LEAD: Screenshot supplied by the user on 2026-10-09 quotes Specter (@SpecterAnalyst) saying multiple Ledger-user wallets were reportedly drained and that addresses across BTC/ETH/TRON received funds potentially sourced from hundreds of victims. Specter claims >$86M. The original complete post/wallet methodology was not independently retrieved during this audit; no audited whole-network total can be inferred from a screenshot or media repetitions.
2. REPEATED SECONDARY COVERAGE: English CoinNess Oct 9 [https://coinness.com/en/news/1171307] and PrimeXBT Oct 9 [https://primexbt.com/news/ledger-wallet-users-reportedly-drained-of-over-86-million-in-suspected-exploit/] repeat Specter's claims. Two publications repeating one investigator are not independent confirmation.
3. USER FIRSTHAND COMPLAINT: r/ledgerwallet 2026-10-09 [https://www.reddit.com/r/ledgerwallet/comments/1x1fz09/my_ledger_wallet_just_got_drained_out_of_almost/] alleges ~100k USDT missing, with a self-provided Tron wallet. Another thread [https://www.reddit.com/r/ledgerwallet/comments/1x1jxoo/whats_up_with_you_guys_and_being_drained/] notes a cluster of claims, but this does not independently verify mechanism or manufacturer-wide flaw.
4. CASE-SPECIFIC ISSUER SUPPORT: Ledger customer support in the first Reddit thread responds that simultaneous drains across multiple chains are consistent with a compromised recovery phrase or physical device+PIN access, requests support case/logs, and warns that remaining funds may be at risk. This reply addresses that individual customer, not the complete $86M allegation.
5. PRIMARY ISSUER CHANNELS: https://www.ledger.com/blog and https://status.ledger.com/ contain no independently located October 9 manufacturer-wide breach acknowledgement at the time of audit. Absence of such a statement is not proof that users were not stolen from.
6. DISTINCT RETAILER CLAIM, NOT CONFIRMED: English Lookonchain feed https://lookonchain.com/feeds/76136 claims Ledger is investigating CryptoBilis reseller-related compromises and issued a 90-day device advisory. This has not been corroborated with a fresh Ledger or CryptoBilis first-party incident statement, so it is UNVERIFIED and must NOT be communicated as an official order or fact. Ledger's reseller index https://www.ledger.com/reseller does list CryptoBilis as a reseller, but listing does not establish incident involvement.
7. DIRECT ETHEREUM EVIDENCE: Blockscout Blockchain Data MCP, Ethereum chain_id=1, retrieved Oct 9. The two addresses cited by indexed English incident reporting are live EOAs:
   - 0x69c8f401cfc6cd40ac94691d6d7c48e3b7a47841 ; first recorded tx 2026-10-09T05:09:23Z ; token transfers include transaction 0x01f25f90f68ed4a3b7c47e77aa8b83e23704f801d3770e4c747c06bd880ae177, 302922.353219 USDT leaving the address at 06:26:59Z, plus other genuine transfer/swap activity;
   - 0x033636e45d519bebb7b5c2520ca6ce56fbdb4f7a ; first recorded tx 2026-10-09T05:55:59Z ; outgoing 49990.00111 USDT (transaction 0xcfb9cb65511a67b89f044c3df34f16fa8c906375211de58f53d7a09e580c261b) and 100008.900873 USDC (transaction 0x64f6ad0dccc64ee6657324f809acff6140db12477998ffeacb173d3e2da0e7b5) at ~06:38-06:39Z.
   These are on-chain fund movements only. Ledger-user identity, lack of authorization, amount actually stolen, attacker control and whether all transactions relate to the same incident have NOT been established. This sample CANNOT validate $86M or hundreds of harmed individuals. BTC/TRON incident wallet tracing not independently completed.
8. FALSE POSITIVE CONTROL: Zilliqa's 2026 verified legacy Ledger signing-app nonce issue https://www.zilliqa.com/ledger-incident/post-mortem/ is an independent, earlier ZIL-specific incident. It does not prove a new October ETH/BTC/TRON Ledger signer exploit and must not be merged with these claims.

## Publication and delivery timeline
- Official Crypto Daily manual email for Oct 9 was sent around 19:20 Asia/Bangkok (Gmail ID 1a1209d4664105f9), before the public English news wave at roughly 19:30+; absence from that earlier edition is not itself a retrospective failure.
- The 19:10 existing collector slot has no durable run final/research in the 2026-10-09 runs/research directory when checked; this is an independent scheduler/persistence-health failure. There was no earlier receipt from that run to prove security coverage.
- Next existing collector is 23:10 Asia/Bangkok. Its runtime must read SECURITY_SOURCE_POLICY.md, run wallet_user_loss_fast_lane, ingest this unresolved lead, timestamp any first-party delta, and write a real final/final-retry. NO new task, scope or notification schedule.
- Future formal report Section 9: only include latest status as confirmed claim of user complaints + on-chain sample and clearly separate unverified aggregate loss and attack vector. CR-18/19 budget remains unchanged.

## Gate
Confirmed exists: social complaints + named researcher report + two active Ethereum sample address transactions.
Unconfirmed: manufacturer hardware/software vulnerability, cause(s), attribution of all addresses to Ledger users, affected-person count, global $86M tally, CryptoBilis remediation report.
Current action: avoid exposing recovery phrases; verify all recipient addresses/transactions on trusted device screens; contact Ledger via https://support.ledger.com/ if personally affected; do not use search ads, DM support or assumed 'urgent migration' links. Do not instruct all hardware-wallet users to reset/migrate seeds based only on an unverified rumor.

## Regression fixes
- SECURITY_SOURCE_POLICY.md: wallet-user multi-victim draining discovery within EXISTING wallet-security lane, honest X/Reddit source receipts, independent validation labels.
- AUTOMATION_RUNTIME.md: collector final preservation and next successful collector after fresh indexing, no backdated run claims.
- REPORT_ACCEPTANCE.md CR-04: wallet security receipts and unresolved major candidate manifest required, without downgrading source verification or widening tasks.
