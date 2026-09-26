# Crypto Mission Monitor Health

Updated: 2026-09-26 07:59 Asia/Bangkok

- main_automation_id: 6ab46906a0cc8191880f1922dbef954a
- main_automation_enabled: true
- expected_schedule: hourly at minute 29 Asia/Bangkok
- previous_scheduler_run_seen: 2026-09-26 07:12 Asia/Bangkok
- current_manual_qa_time: 2026-09-26 07:59 Asia/Bangkok
- run_gap_status: healthy
- github_write_ok: true
- gmail_delivery_test: passed
- gmail_test_message_id: 1a0db38c1fe33130
- gmail_readback_verified: true
- separate_monster_daily_automation_enabled: false
- monster_lane_merged_into_main: true
- eth_lane_merged_into_main: true

## Mandatory lanes
- wallet/gas: configured
- PONS: configured
- XRP/Variational: configured
- ETH conditional: configured
- BTC regime: configured
- JUMP: configured
- launch/NFT radar: configured
- active-position security: configured
- monster squeeze V2.1: configured
- Robinhood/FOMO execution-flow: configured

## Current manual QA
ETH lane:
- fresh Binance market data successfully read;
- current conclusion: NO MARKET ENTRY around ~2685;
- conditional plan written to positions/eth-conditional.md.

Monster squeeze lane:
- Binance USDⓈ-M universe data successfully read;
- WLD smoke-test performed because of strong 24h move;
- WLD did not pass the frozen IGNITION gate at the check;
- watchlist/monster-squeeze-v2.1.md created.

Alert path:
- real Gmail test sent and read back successfully.
- ACTION/health triggers require Gmail + ChatGPT.
- WATCH is ChatGPT-only.
- 19:29 Bangkok 妖币 daily summary is mandatory.

## Known defect fixed
The Sep-25 ETH one-shot task completed in the scheduler but did not persist the promised conclusion into the Mission report. This is recorded as a persistence/QA defect. ETH is now handled by the main hourly monitor with mandatory GitHub writes.
