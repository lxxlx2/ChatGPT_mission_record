# Crypto Daily manual delivery recovery

run_time: 2026-09-27T12:09:22+07:00
automation_id: 6a8600b9d12481919bc43ebc800c9916
run_mode: daily_report_recovery
run_status: success
recovery_type: manual_interactive

## Failure chain
- 09:00 automatic publisher path completed research and critical-security verification.
- Gmail send was rejected twice by provider safety checks.
- 10:00/11:00 recovery logic still did not produce a sent message.
- Gmail Sent and GitHub official report were both absent before this recovery.

## Recovery
- fresh market values rechecked before delivery;
- exact subject: Crypto Daily Brief｜2026-09-27
- Gmail sent: true
- gmail_message_id: 1a0e14490ff201f6
- recipient verified: lxx.run688@gmail.com
- Gmail readback: success
- 13-section structure readback: success
- GitHub official report archive: attempted
- report_path: crypto-daily/reports/daily/2026/2026-09/2026-09-27.md

## Reliability action
A dedicated existing publisher/recovery scheduler is being restored as an idempotent fallback. It must dedupe Gmail Sent + GitHub before any send and may repair only the missing side.
