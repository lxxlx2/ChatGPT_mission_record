# 2026-10-17 full daily corrections: chapter numbering and missed cross-CEX HTX restriction

User-requested defects:
A. Oct17 formal Crypto Daily and US Stock Daily used one global numbered-item counter instead of restarting at (1) in every fixed section; generated-body checks counted sections/items but did not enforce per-heading sequences.
B. Crypto Daily omitted high-impact Bitget Oct16 new enforcement involving HTX despite earlier Binance/Bybit/Bitget counterparty restrictions. Old HTX restriction alone is historical, but NEW venue enforcement/delta is a fresh major user-access safety event.

## Verified corrected email results

| Report | Superseded Gmail Sent | Corrected Gmail Sent + readback | Corrected canonical Git commit | Exact body |
| --- | --- | --- | --- | --- |
| US Stock Daily Oct17 | 1a148814cd66225b | 1a1488e038aa2ca6, subject 美股每日晨报｜2026-10-17｜修正版 | 174017451e025d1c812ba49d90f65c4a89602b7e | PASS, 12 chapters, all restart at 1, 55 total items; full original content preserved |
| Crypto Daily Oct17 | 1a14886106251842 | 1a1488f7e5801fe5, subject Crypto Daily Brief｜2026-10-17｜修正版 | 1dc2631c469037a6ddfd1c80a8d7d7d8a71fcc61 | PASS, 13 chapters, all restart at 1, 55 total items; material Bitget/HTX risk added in Top5 and Security section |

Recipient for both: lxx.run688@gmail.com. Gmail original body was read and verified byte-for-byte against pre-correction canonical Git body before any change. Gmail original corrected content readback exact; new Git canonical body readback exact after stripping YAML, including correction_of_gmail_message_id, official_corrected status. Git history retains earlier canonical versions. No unrelated report dates modified or duplicate generic daily sent.

## Actual permanent specification changes (verified via readback)
- crypto-daily/REPORT_ACCEPTANCE.md: CR-22 section-local numbering lint, CR-23 CEX counterparty risk cross-venue and policy delta hard gate. Commit 78e58d52c3d6b837e030ca623b23bbfeb2df4708.
- us-stock-daily/REPORT_ACCEPTANCE.md: STK-20 section-local numbering and corrected-email readback gate. Commit dd21c6dc373d503513a67142f92b20cfcf712e12.
- crypto-daily/COLLECTOR_SPEC.md: bounded English multi-venue legal/AML deposit-withdrawal discovery, event identity, original source timestamps. Commit 3faaad6002e166c48f755cf76f3a013600ff0c68.
- crypto-daily/SECURITY_SOURCE_POLICY.md: funds provenance, account access, frozen deposit/withdrawal security high materiality. Commit c55dc5742b12597e65e7f96bceabf382d165fc4b.

Source triage is in crypto-daily/research/2026-10-17/htx-three-cex-restricted-counterparty-20261016-triage.md, including current Bitget Oct16 English first-party SOURCE_GAP.

## Acceptance / residual problems
- Immediate interactive correction path: Gmail Sent, exact readback, section-local lint and Git archive were individually verified.
- Two EXISTING daily task prompts were explicitly updated after Git docs were written: Crypto task `6a8600b9d12481919bc43ebc800c9916` now requires latest CR-01..CR-23 and HTX cross-CEX material news discovery; US Stock task `6a8600c16e7081919566f170f58045a6` now requires latest STK-01..STK-20 and chapter-local numbering. `automations.update` success responses confirmed both original task IDs, unchanged titles, enabled state and original Asia/Bangkok schedules (:20 original ten slots and :40 original four slots respectively). TGE monitor untouched. No fallback or duplicate task, added email cadence, or expanded event watch. These prompt updates are implementation evidence; next true scheduled Gmail/Sent readback remains NOT YET VERIFIED.
- Original scheduled worker safety blocks, incomplete collector source receipts and TGE partial shard coverage remain NOT FIXED by this content/layout correction. Future normal reports need actual Sent/Git proof, and original first-party Bitget Oct16 full text is still a live verification gap.
