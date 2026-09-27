# Crypto Daily collector persistence repair

recorded_at: 2026-09-27T12:28:00+07:00
automation_id: 6a8600b9d12481919bc43ebc800c9916
status: repair_applied

## Observed
- 09:00 automatic research/final existed but Gmail delivery failed.
- 11:00 recovery research existed without a corresponding final audit.
- scheduler metadata advanced around 12:00, but no 12:00 research or final artifact was present when audited.

## Repair
- every scheduled run now writes attempt audit first;
- ordinary pre-final work is bounded to core market + one English discovery/shard pass + compact research;
- failures are isolated per lane;
- final/final-retry is persisted before deeper enrichment;
- formal delivery has a separate enabled 09:10/10:10/11:10 fallback.

The next 13:00 ordinary run must produce attempt + final/final-retry to validate collector recovery.
