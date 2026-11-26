# P0 — shared scheduled execution failure, 2026-11-26
Status: OPEN / PLATFORM_EXECUTION_ROOT_CAUSE_UNVERIFIED / PRODUCTION_NOT_ACCEPTED
Timezone: Asia/Bangkok. User asked for actual autonomous repair rather than daily manual recovery.

## Reproduced evidence (Nov26 morning)
| Original task | Task ID | Scheduled ICT | Actual started ICT | Completed ICT | Run ID |
|---|---|---|---|---|---|
| Crypto Daily | 6a8600b9d12481919bc43ebc800c9916 | 06:20 | 06:22:40.758 | 06:22:50.437 | 58cfc668-1ca4-8321-adb1-011ae9c228f5 |
| US stock | 6a8600c16e7081919566f170f58045a6 | 07:40 | 07:40:09.570 | 07:40:34.364 | 17deb3c4-9e8c-8321-b805-fc8736db9859 |
| TGE | 6a85fff710e0819190ffcf8c1145a170 | 08:00 | 07:58:08.174 | 07:58:17.096 | 1e707a59-d914-832d-b599-f9cc738d0d73 |

All three enabled, exact_schedule, environment_selection=inherited, environments=null (inherited environment details unavailable). Each last_run.recorded_status=completed, latest_result=null, chat_ref=null, delivery_status=unknown. None of these fields proves permission failure or actual runtime location. Task definition detail action returned HTTP 404 Action not found; no executor tool trace or underlying exception accessible through this action. Interactive browser list succeeds; this does not prove unattended browser access. No new task or scheduler.

Git evidence: Crypto 06:20 final absent; only 031507 collector final, partial source gaps. Nov25 09:20 had durable manual prebuild but no scheduled publish/Sent; later 10:20 and 11:20 archive-only recoveries successfully read prior manual Sent and Git, demonstrating at least some unattended connector operations worked. Stock Nov26 pending 404, 06:40 attempt 064300-attempt.md only, 07:40 final absent. TGE original automatic final last Nov25 08:00:30; Nov26 08:00 manual repair separately recorded, not automatic success. Crypto pending QA receipt for Nov26 absent; existing push-only CI workflow exists, workflow-specific run listing rejected by connector, no CI PASS proven.

## Controls / already executed
- Interactive Gmail and Git readbacks verified Nov25 both reports; Nov26 US stock manual recovery Sent 1a21565316947c35, canonical exact, audit us-stock-daily/runs/2026-11-26/080802-final-retry.md.
- Crypto Nov26 draft exists at crypto-daily/research/2026-11-26/0820-prebuild-13chapter.md, DRAFT_UNVERIFIED; as of initial Nov26 morning diagnosis formal 09:20 not yet due. Do not send merely because draft exists.
- TGE manual source recovery airdrop-tge-monitor/runs/2026-11-26/0800-manual-repair-final.md; current cache separates manual from autonomous. Actual TGE task prompt readback confirms scheduled-slot dispatch patch, Git runtime records same. Early-start wrong-shard risk corrected in instructions, actual prior wrong-shard not proven.
- Original prompts already require durable attempts, substantive work, Sent readback, Git exact-body and terminal finals. Repeated prompt additions have failed to establish production recovery. Do not further append incident history or relax hard gates to simulate success.
- OpenAI official incident Nov25: https://status.openai.com/incidents/01M898HVZGXFV2XC4775CG9GF8 (conversation errors affecting ChatGPT/Work/Codex Cloud; reported resolved). Correlation only, no causal proof for these three tasks. Failures predate that incident. Support procedure https://help.openai.com/en/articles/6614161-how-can-i-contact-support . No support case submitted.

## Required next evidence and acceptance
Obtain scheduler-side actual executor routing, connector authorization inheritance, tool invocation logs, early exit reason and final output persistence for the above run IDs. Distinguish recorded completion from verified delivery. If execution logs are inaccessible, mark blocked at platform diagnostic access, not repaired. Do not add fallback automations, local cron, or bypass editorial/rights gates.
- Crypto: original 08:20 real prebuild, 09:20 unattended complete source/novelty QA and actual daily Gmail Sent + exact Git body, original recovery windows correctly dedupe; monthly unchanged.
- Stock: original 05:40/06:40 substantive handoff, 07:40 unattended complete 12-section QA and real Gmail Sent/readback + Git exact body; recovery only on missed delivery.
- TGE: four consecutive original shard invocations with intended slots, real per-issuer source receipts, explicit identity/right gaps, no false no-news, durable terminal finals and current pointer, genuine material event only through existing gate; no heartbeat. Private rights not accessible remain unverified.
- Suggested acceptance window: three consecutive days of on-time autonomous daily deliveries and 24 consecutive hourly TGE finals, with source coverage separately evaluated. This is an acceptance recommendation, not a new schedule or monitoring task, and not a claim that such observation has taken place.
Production remains NO_GO for claims of recovery. Existing tasks remain enabled, same IDs, times, recipients, registry and exclusions.
